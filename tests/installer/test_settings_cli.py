"""`nexus-hub settings show` and `explain` from an installed layout (v4.14.6 Phase 2, T014).

Each test copies the CLI core, the process policy, and `scripts/lib` into a scratch
`scripts/` folder, the way both installers lay them out, so nothing resolves
through the repository. HOME and PATH are scratch values: no real tool config is
read and no real tool is started.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
SCHEMA = json.loads((SCRIPTS / "lib" / "settings_control" / "schema" / "show.schema.json").read_text(encoding="utf-8"))
CLEAN_PREFIXES = ("CLAUDE", "ANTHROPIC", "CODEX", "COPILOT", "NEXUS")


@pytest.fixture()
def install(tmp_path: Path) -> Path:
    scripts = tmp_path / "install" / "scripts"
    scripts.mkdir(parents=True)
    for name in ("nexus_hub_cli.py", "nexus_process.py"):
        shutil.copy2(SCRIPTS / name, scripts / name)
    shutil.copytree(SCRIPTS / "lib", scripts / "lib", ignore=shutil.ignore_patterns("__pycache__", "integrations", "installer"))
    return scripts / "nexus_hub_cli.py"


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    (tmp_path / "home").mkdir()
    return tmp_path / "home"


@pytest.fixture()
def env(tmp_path: Path, home: Path) -> dict[str, str]:
    """A scrubbed environment whose only tool on PATH is a stub `claude` reporting the proven version."""
    stub = tmp_path / "bin"
    stub.mkdir()
    if os.name == "nt":
        (stub / "claude.cmd").write_text("@echo 2.1.283 (Claude Code)\r\n", encoding="utf-8")
    else:
        script = stub / "claude"
        script.write_text("#!/bin/sh\necho '2.1.283 (Claude Code)'\n", encoding="utf-8")
        script.chmod(0o755)
    kept = {k: v for k, v in os.environ.items() if not k.upper().startswith(CLEAN_PREFIXES)}
    return {**kept, "HOME": str(home), "USERPROFILE": str(home), "PATH": str(stub)}


def run(install: Path, env: dict[str, str], *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(install), "settings", *args], env=env, cwd=cwd, capture_output=True, text=True,
        timeout=120, stdin=subprocess.DEVNULL, check=False,
    )


def digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_show_json_validates_and_reports_an_override_with_exit_zero(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    env["ANTHROPIC_MODEL"] = "claude-haiku-5-5"

    done = run(install, env, "show", "--json", "--project", str(tmp_path))
    document = json.loads(done.stdout)

    assert done.returncode == 0, done.stderr
    jsonschema.validate(document, SCHEMA)
    record = next(r for r in document["records"] if (r["control"], r["tool"]) == ("model", "claude"))
    assert (record["state"], record["layer"]) == ("overridden-by", "env ANTHROPIC_MODEL (shell)")
    assert record["fix"] == "Unset ANTHROPIC_MODEL where it is set."
    assert document["tools"]["claude"]["installed"] is True and document["tools"]["claude"]["version"] == "2.1.283"
    assert document["tools"]["codex"]["installed"] is False
    assert document["tools"]["claude"]["cannot_remove"]


def test_show_table_lists_state_layer_and_fix(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    env["ANTHROPIC_MODEL"] = "claude-haiku-5-5"

    done = run(install, env, "show", "--project", str(tmp_path))

    assert done.returncode == 0, done.stderr
    assert done.stdout.splitlines()[0].split() == ["control", "tool", "state", "value", "layer"]
    assert "overridden-by" in done.stdout and "env ANTHROPIC_MODEL (shell) = claude-haiku-5-5" in done.stdout
    assert "fix: Unset ANTHROPIC_MODEL" in done.stdout
    assert done.stdout.isascii()


def test_show_is_read_only(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus", "env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}}), encoding="utf-8")
    before = digest(tmp_path / "home")

    done = run(install, env, "show", "--project", str(tmp_path))

    assert done.returncode == 0 and digest(tmp_path / "home") == before


def test_project_must_be_a_directory(install: Path, env: dict[str, str], tmp_path: Path) -> None:
    done = run(install, env, "show", "--project", str(tmp_path / "missing"))

    assert done.returncode == 2 and "--project is not a directory" in done.stderr and done.stdout == ""


def test_project_files_are_read_from_the_named_project(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    project = tmp_path / "proj"
    (project / ".claude").mkdir(parents=True)
    (project / ".claude" / "settings.json").write_text(json.dumps({"model": "sonnet"}), encoding="utf-8")
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus"}), encoding="utf-8")

    document = json.loads(run(install, env, "show", "--json", "--project", str(project)).stdout)

    record = next(r for r in document["records"] if (r["control"], r["tool"]) == ("model", "claude"))
    assert record["layer"] == "file .claude/settings.json (project)" and record["layer_value"] == "sonnet"


def test_explain_prints_sources_overrides_and_cannot_remove(install: Path, env: dict[str, str]) -> None:
    done = run(install, env, "explain", "posture")

    assert done.returncode == 0, done.stderr
    for needle in ("claude.posture", "codex.posture", "weakens safety for: full-auto", "override [project-file]", "Cannot remove (Claude Code):", "Cannot remove (Codex):"):
        assert needle in done.stdout
    assert done.stdout.isascii()


def test_explain_json_and_unknown_control(install: Path, env: dict[str, str]) -> None:
    data = json.loads(run(install, env, "explain", "model", "--json").stdout)
    assert data["control"]["id"] == "model" and {w["id"] for w in data["writes"]} >= {"claude.model", "codex.model"}

    bad = run(install, env, "explain", "nope")
    assert bad.returncode == 2 and "unknown control 'nope'" in bad.stderr and "known controls: effort, model" in bad.stderr


def test_settings_without_an_action_prints_help(install: Path, env: dict[str, str]) -> None:
    done = run(install, env)

    assert done.returncode == 0 and "show" in done.stdout and "explain" in done.stdout


def test_a_catalog_that_breaks_a_rule_is_refused_with_the_findings(install: Path, env: dict[str, str]) -> None:
    path = install.parent / "lib" / "settings_control" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    del catalog["writes"][0]["override_layers"][0]["detect"]
    path.write_text(json.dumps(catalog), encoding="utf-8")

    done = run(install, env, "show")

    assert done.returncode == 2 and done.stdout == ""
    assert "the settings catalog is not valid" in done.stderr and "has no detect spec" in done.stderr


@pytest.mark.parametrize("damage", ["missing", "garbage"])
def test_a_missing_or_unparseable_catalog_never_falls_back_to_guesses(install: Path, env: dict[str, str], damage: str) -> None:
    path = install.parent / "lib" / "settings_control" / "catalog.json"
    path.unlink() if damage == "missing" else path.write_text("{nope", encoding="utf-8")

    done = run(install, env, "show", "--json")

    assert done.returncode == 2 and done.stdout == "" and "settings catalog is not valid" in done.stderr


def test_a_missing_engine_says_to_reinstall(install: Path, env: dict[str, str]) -> None:
    shutil.rmtree(install.parent / "lib" / "settings_control")

    done = run(install, env, "show")

    assert done.returncode == 2 and "settings engine not found; re-run the Nexus-Hub installer" in done.stderr


def _record(**changes: object) -> dict:
    base = {
        "control": "model", "tool": "claude", "surface": "cli", "state": "in-effect", "value": "opus", "native": "opus", "layer": None,
        "layer_value": None, "fix": None, "detail": None, "caveats": [], "writes": ["claude.model"],
    }
    return {"schema_version": 1, "project": None, "platform": "linux", "tools": {}, "records": [{**base, **changes}]}


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "overridden-by"},  # needs a layer and a fix
        {"state": "overridden-by", "layer": "env X (shell)"},  # needs a fix
        {"state": "not-settable"},  # needs a reason
        {"state": "cannot-detect"},  # needs a reason
        {"state": "in-effect", "layer": "env X (shell)", "fix": "do it"},  # a layer only with overridden-by
        {"state": "maybe"},  # unknown state
        {"surface": "elsewhere"},
    ],
)
def test_the_schema_rejects_an_unexplained_or_unknown_state(changes: dict) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_record(**changes), SCHEMA)


def test_the_schema_accepts_a_well_formed_record() -> None:
    jsonschema.validate(_record(), SCHEMA)
    jsonschema.validate(_record(state="overridden-by", layer="env X (shell)", fix="Unset X."), SCHEMA)
    jsonschema.validate(_record(state="not-covered", detail="claude-opus-5-5"), SCHEMA)
