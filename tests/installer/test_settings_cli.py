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


def schema_checker():
    """The `jsonschema` module, or a skip of only the calling test when this job does not install it.

    The Windows installer shards install a small requirements set without `jsonschema`, so a
    module-level import would stop every test in this file from being collected there. The
    schema checks still run in the Linux `tests` job, which gets `jsonschema` through `mcp`.
    """
    return pytest.importorskip("jsonschema")


def digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_show_json_validates_against_the_schema(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    jsonschema = schema_checker()
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    env["ANTHROPIC_MODEL"] = "claude-haiku-5-5"

    done = run(install, env, "show", "--json", "--project", str(tmp_path))

    assert done.returncode == 0, done.stderr
    jsonschema.validate(json.loads(done.stdout), SCHEMA)


def test_show_json_reports_an_override_with_exit_zero(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"model": "opus"}), encoding="utf-8")
    env["ANTHROPIC_MODEL"] = "claude-haiku-5-5"

    done = run(install, env, "show", "--json", "--project", str(tmp_path))
    document = json.loads(done.stdout)

    assert done.returncode == 0, done.stderr
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


def test_installed_cli_applies_shared_effort_and_restores_existing_override(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    user = home / ".claude" / "settings.json"
    user.parent.mkdir()
    original = '{\n  "env": {"CLAUDE_CODE_EFFORT_LEVEL": "low", "KEEP": "yes"}\n}\n'
    user.write_text(original, encoding="utf-8")

    changed = run(install, env, "set", "effort", "high", "--json", "--project", str(tmp_path))
    assert changed.returncode == 0, changed.stderr
    assert json.loads((home / ".nexus-hub" / "preferences.json").read_text()) == {"default_effort": "high"}
    assert json.loads(user.read_text())["env"] == {"CLAUDE_CODE_EFFORT_LEVEL": "high", "KEEP": "yes"}
    shown = run(install, env, "show", "--json", "--project", str(tmp_path))
    rows = {(r["control"], r["tool"]): r for r in json.loads(shown.stdout)["records"]}
    assert rows["effort", "internal"]["value"] == "high"
    assert rows["effort", "claude"]["state"] == "in-effect"

    reset = run(install, env, "reset", "effort", "--json", "--project", str(tmp_path))

    assert reset.returncode == 0, reset.stderr
    assert user.read_text(encoding="utf-8") == original
    assert not (home / ".nexus-hub" / "preferences.json").exists()


def test_installed_cli_reports_default_guards_and_enforces_off_confirmation(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    shown = run(install, env, "show", "--json", "--project", str(tmp_path))
    rows = {r["control"]: r for r in json.loads(shown.stdout)["records"] if r["tool"] == "internal"}
    assert all(rows[control]["value"] == "on" for control in ("git_safety", "secret_scan", "edit_preservation", "large_file_warning"))

    refused = run(install, env, "set", "secret_scan", "off", "--json", "--project", str(tmp_path))

    assert refused.returncode == 3 and not (home / ".nexus-hub" / "guardrails.json").exists()
    warning = run(install, env, "set", "large_file_warning", "off", "--json", "--project", str(tmp_path))
    assert warning.returncode == 0, warning.stderr
    assert json.loads((home / ".nexus-hub" / "guardrails.json").read_text()) == {"warn_large_files": False}


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
    assert data["control"]["per_tool"] is True and data["control"]["never_written"] == []
    assert data["claude_model_ids"] and all(isinstance(i, str) and i for i in data["claude_model_ids"])
    effort = json.loads(run(install, env, "explain", "effort", "--json").stdout)
    assert effort["control"]["per_tool"] is False and effort["control"]["never_written"] == []

    bad = run(install, env, "explain", "nope")
    assert bad.returncode == 2 and "unknown control 'nope'" in bad.stderr and "known controls: effort, model" in bad.stderr


def test_settings_without_an_action_prints_help(install: Path, env: dict[str, str]) -> None:
    done = run(install, env)

    assert done.returncode == 0 and "show" in done.stdout and "explain" in done.stdout


def test_a_catalog_that_breaks_a_rule_is_refused_with_the_findings(install: Path, env: dict[str, str]) -> None:
    path = install.parent / "lib" / "settings_control" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    write = next(w for w in catalog["writes"] if w["id"] == "claude.effort.model_settings")
    del write["override_layers"][0]["detect"]
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
        "layer_value": None, "fix": None, "detail": None, "caveats": [], "writes": ["claude.model"], "removable_override": None,
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
        {"removable_override": {"id": "x"}},  # an incomplete removable-override object
        {"removable_override": {"id": "x", "weakens_safety": "no", "reason": "r"}},
    ],
)
def test_the_schema_rejects_an_unexplained_or_unknown_state(changes: dict) -> None:
    jsonschema = schema_checker()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_record(**changes), SCHEMA)


def test_the_schema_accepts_a_well_formed_record() -> None:
    jsonschema = schema_checker()
    jsonschema.validate(_record(), SCHEMA)
    jsonschema.validate(_record(state="overridden-by", layer="env X (shell)", fix="Unset X."), SCHEMA)
    jsonschema.validate(_record(state="not-covered", detail="claude-opus-5-5"), SCHEMA)
    jsonschema.validate(_record(removable_override={"id": "claude.effort_env", "weakens_safety": False, "reason": "Outranks /effort."}), SCHEMA)


# --- Write side (v4.14.6 Phase 3) -------------------------------------------------


def test_set_dry_run_json_then_set_and_reset_round_trip_with_exit_codes(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    settings = home / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text('{\n  "model": "sonnet",\n  "env": {"KEEP": "1"}\n}\n', encoding="utf-8")
    before = digest(home)

    dry = run(install, env, "set", "model", "claude-opus-5-5", "--tool", "claude", "--dry-run", "--json", "--project", str(tmp_path))
    assert dry.returncode == 0, dry.stderr
    assert json.loads(dry.stdout)["results"][0]["status"] == "would-write" and digest(home) == before

    done = run(install, env, "set", "model", "claude-opus-5-5", "--tool", "claude", "--project", str(tmp_path))
    assert done.returncode == 0, done.stderr
    assert json.loads(settings.read_text(encoding="utf-8"))["model"] == "claude-opus-5-5"
    owned = json.loads(run(install, env, "owned-keys", "--json").stdout)
    assert owned["dotted"] == {"~/.claude/settings.json": ["model"]}

    reset = run(install, env, "reset", "model", "--tool", "claude", "--project", str(tmp_path))
    assert reset.returncode == 0, reset.stderr
    assert digest(home) == {**before, **{k: v for k, v in digest(home).items() if k.startswith(".nexus-hub")}}
    assert settings.read_text(encoding="utf-8") == '{\n  "model": "sonnet",\n  "env": {"KEEP": "1"}\n}\n'


def test_a_safety_weakening_set_without_a_terminal_exits_three_and_writes_nothing(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".claude").mkdir()
    before = digest(home)

    done = run(install, env, "set", "posture", "full-auto", "--tool", "claude", "--project", str(tmp_path))

    assert done.returncode == 3 and "needs a person" in done.stderr
    assert digest(home) == before


def test_usage_errors_exit_two_and_nothing_to_write_exits_four(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    assert run(install, env, "set", "posture", "yolo").returncode == 2
    assert run(install, env, "set", "model", "x").returncode == 2  # model is chosen per tool
    assert run(install, env, "remove-override", "effort").returncode == 2  # --tool is required
    nothing = run(install, env, "set", "attribution", "off", "--tool", "codex", "--project", str(tmp_path))
    assert nothing.returncode == 4 and "not-settable" in nothing.stdout


def test_an_unreadable_record_stops_set_and_owned_keys_with_exit_two(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    (home / ".nexus-hub").mkdir()
    (home / ".nexus-hub" / "settings-control.json").write_text("{nope", encoding="utf-8")
    (home / ".claude").mkdir()

    assert run(install, env, "set", "model", "x", "--tool", "claude", "--project", str(tmp_path)).returncode == 2
    owned = run(install, env, "owned-keys", "--json")
    assert owned.returncode == 2 and "repair or delete" in owned.stderr


def test_owned_keys_takes_its_home_from_the_option(install: Path, home: Path, env: dict[str, str], tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / ".nexus-hub").mkdir(parents=True)
    entry = {"kind": "file", "tool": "claude", "file": "~/.claude/settings.json", "key_path": ["model"],
             "previous": {"present": False}, "new": {"present": True, "value": "x"}}
    (elsewhere / ".nexus-hub" / "settings-control.json").write_text(json.dumps({"schema_version": 1, "entries": [entry]}), encoding="utf-8")

    done = run(install, env, "owned-keys", "--json", "--home", str(elsewhere))

    assert done.returncode == 0 and json.loads(done.stdout)["dotted"] == {"~/.claude/settings.json": ["model"]}
    assert json.loads(run(install, env, "owned-keys", "--json").stdout)["dotted"] == {}
