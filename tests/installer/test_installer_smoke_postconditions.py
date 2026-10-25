"""Tests for the shared cross-OS installer-smoke postcondition checker."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_installer_smoke as smoke
from scripts.check_installer_smoke import EXPECTED_SCRIPTS, collect_findings

NEXUS_START_MARKER = "<!-- NEXUS_HUB_START -->"
NEXUS_END_MARKER = "<!-- NEXUS_HUB_END -->"
ORG_START_MARKER = "<!-- NEXUS_HUB_ORG_START -->"
ORG_END_MARKER = "<!-- NEXUS_HUB_ORG_END -->"
EVAL_AND_REPORT_SCRIPTS = (
    "package_skill.py",
    "aggregate_benchmark.py",
    "skill_eval_viewer.py",
    "optimize_skill_description.py",
    "generate_report.py",
)
FUNCTIONAL_VERIFICATION_ARTIFACTS = (
    Path(".claude") / "skills" / "functional-verification" / "SKILL.md",
    Path(".claude")
    / "skills"
    / "functional-verification"
    / "scripts"
    / "detect_visual_defects.py",
    Path(".claude")
    / "skills"
    / "functional-verification"
    / "references"
    / "deep-pass.md",
    Path(".claude") / "rules" / "html" / "responsive-layout.md",
)


def _host_hook_suffix() -> str:
    return ".ps1" if smoke.os.name == "nt" else ".sh"


def _seed(home: Path, workspace: Path, *, metadata: bool = False) -> None:
    scripts = home / ".nexus-hub" / "scripts"
    scripts.mkdir(parents=True)
    for name in EXPECTED_SCRIPTS:
        (scripts / name).write_text("# fixture\n", encoding="utf-8")
    (home / ".nexus-hub" / "VERSION").write_text("3.17.0", encoding="ascii")
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    settings = {"permissions": {"allow": ["Read"]}}
    if metadata:
        settings["_description"] = "must not leak"
    (settings_dir / "settings.local.json").write_text(
        json.dumps(settings), encoding="utf-8"
    )
    (workspace / "CLAUDE.md").write_text(
        f"{NEXUS_START_MARKER}\n# Nexus-Hub\n{NEXUS_END_MARKER}\n"
        f"{ORG_START_MARKER}\n# Organization Standards\n{ORG_END_MARKER}\n",
        encoding="utf-8",
    )
    org_rule = workspace / ".claude" / "rules" / "org" / "python" / "code-style.md"
    org_rule.parent.mkdir(parents=True)
    org_rule.write_text("# Organization Python Style\n", encoding="utf-8")
    for relative_path in FUNCTIONAL_VERIFICATION_ARTIFACTS:
        artifact = workspace / relative_path
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("# fixture\n", encoding="utf-8")
    hook_name = f"html-responsive-guard{_host_hook_suffix()}"
    installed_hook = workspace / ".claude" / "hooks" / hook_name
    installed_hook.parent.mkdir(parents=True, exist_ok=True)
    installed_hook.write_text("# fixture\n", encoding="utf-8")
    settings = {
        "customUserSetting": {"preserve": True},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": matcher,
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"run .claude/hooks/{hook_name}",
                        }
                    ],
                }
                for matcher in ("Write", "Edit")
            ]
        },
    }
    (workspace / ".claude" / "settings.json").write_text(
        json.dumps(settings), encoding="utf-8"
    )


def test_complete_install_has_no_findings(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    assert collect_findings(home, workspace) == []


@pytest.fixture
def installed_copy(tmp_path: Path) -> tuple[Path, Path]:
    """Copy the distributed scripts and launcher into a disposable home."""
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    repo = Path(smoke.__file__).resolve().parents[1]
    install_root = home / ".nexus-hub"
    for name in set(EXPECTED_SCRIPTS) | set(EVAL_AND_REPORT_SCRIPTS):
        source = repo / "scripts" / name
        target = install_root / "scripts" / name
        shutil.copyfile(source, target)
        assert target.read_bytes() == source.read_bytes()
    bin_dir = install_root / "bin"
    bin_dir.mkdir()
    launcher = "nexus-hub.cmd" if smoke.os.name == "nt" else "nexus-hub"
    shutil.copy2(repo / "scripts" / launcher, bin_dir / launcher)
    (bin_dir / launcher).chmod(0o755)
    return home, workspace


def test_eval_and_report_scripts_are_literal_smoke_requirements() -> None:
    assert set(EVAL_AND_REPORT_SCRIPTS) <= set(EXPECTED_SCRIPTS)


@pytest.mark.parametrize("name", (*EVAL_AND_REPORT_SCRIPTS, "completion_budget.py"))
def test_cli_rejects_a_missing_distributed_script(
    installed_copy: tuple[Path, Path], name: str
) -> None:
    assert name in EXPECTED_SCRIPTS
    home, workspace = installed_copy
    command = [
        sys.executable, str(Path(smoke.__file__).resolve()),
        "--home", str(home), "--workspace", str(workspace),
    ]
    complete = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
    assert complete.returncode == 0, complete.stderr
    assert complete.stdout.strip() == "installer smoke: PASS"

    (home / ".nexus-hub" / "scripts" / name).unlink()
    incomplete = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
    assert incomplete.returncode == 1
    assert incomplete.stdout == ""
    assert incomplete.stderr.strip() == f"installer smoke: FAIL: expected installed script is missing: {name}"


@pytest.mark.parametrize("problem", ["missing", "unreadable"])
def test_cli_refuses_an_unreadable_or_missing_permission_artifact(
    installed_copy: tuple[Path, Path], problem: str
) -> None:
    home, workspace = installed_copy
    settings = workspace / ".claude" / "settings.local.json"
    settings.unlink()
    if problem == "unreadable":
        settings.mkdir()
    result = subprocess.run(
        [sys.executable, str(Path(smoke.__file__).resolve()),
         "--home", str(home), "--workspace", str(workspace)],
        capture_output=True, text=True, timeout=45, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "permission baseline is missing or invalid" in result.stderr
    assert str(settings) in result.stderr


def test_missing_script_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (home / ".nexus-hub" / "scripts" / EXPECTED_SCRIPTS[0]).unlink()
    assert any(
        EXPECTED_SCRIPTS[0] in finding for finding in collect_findings(home, workspace)
    )


@pytest.mark.parametrize("relative_path", FUNCTIONAL_VERIFICATION_ARTIFACTS)
def test_missing_functional_verification_artifact_is_reported(
    tmp_path: Path, relative_path: Path
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (workspace / relative_path).unlink()

    assert any(str(relative_path) in finding for finding in collect_findings(home, workspace))


def test_missing_host_hook_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    relative_path = Path(".claude") / "hooks" / f"html-responsive-guard{_host_hook_suffix()}"
    (workspace / relative_path).unlink()

    assert any(str(relative_path) in finding for finding in collect_findings(home, workspace))


def test_duplicate_html_hook_registration_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    settings_path = workspace / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["hooks"]["PreToolUse"].append(settings["hooks"]["PreToolUse"][0])
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    assert any("exactly one Write registration" in finding for finding in collect_findings(home, workspace))


def test_wrong_host_html_hook_registration_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    settings_path = workspace / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    wrong_suffix = ".sh" if _host_hook_suffix() == ".ps1" else ".ps1"
    for entry in settings["hooks"]["PreToolUse"]:
        entry["hooks"][0]["command"] = (
            f"run .claude/hooks/html-responsive-guard{wrong_suffix}"
        )
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    assert any("host-correct registration" in finding for finding in collect_findings(home, workspace))


@pytest.mark.parametrize("invalid_hooks", [None, []])
def test_non_object_hooks_are_reported_without_crashing(
    tmp_path: Path, invalid_hooks: object
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    settings_path = workspace / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    settings["hooks"] = invalid_hooks
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    assert any(
        "hooks to be an object" in finding for finding in collect_findings(home, workspace)
    )


def test_template_metadata_leak_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace, metadata=True)
    assert any(
        "template metadata" in finding for finding in collect_findings(home, workspace)
    )


def test_org_block_before_nexus_block_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (workspace / "CLAUDE.md").write_text(
        f"{ORG_START_MARKER}\n# Organization Standards\n{ORG_END_MARKER}\n"
        f"{NEXUS_START_MARKER}\n# Nexus-Hub\n{NEXUS_END_MARKER}\n",
        encoding="utf-8",
    )

    assert any(
        "must follow the Nexus-Hub block" in finding
        for finding in collect_findings(home, workspace)
    )


def test_missing_org_rule_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (workspace / ".claude" / "rules" / "org" / "python" / "code-style.md").unlink()

    assert any(
        "organization rule is missing" in finding
        for finding in collect_findings(home, workspace)
    )


def test_duplicate_org_marker_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    instruction = workspace / "CLAUDE.md"
    instruction.write_text(
        instruction.read_text(encoding="utf-8") + f"{ORG_START_MARKER}\n",
        encoding="utf-8",
    )

    assert any("found 2" in finding for finding in collect_findings(home, workspace))


def test_missing_instruction_surface_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (workspace / "CLAUDE.md").unlink()

    assert any(
        "instruction surface is missing or unreadable" in finding
        for finding in collect_findings(home, workspace)
    )


def test_invalid_settings_are_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    (workspace / ".claude" / "settings.local.json").write_text("{", encoding="utf-8")

    assert any("permission baseline is missing or invalid" in finding for finding in collect_findings(home, workspace))


def test_main_runs_installed_launcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *args, **kwargs: smoke.subprocess.CompletedProcess(
            args[0], 0, "nexus-hub 3.17.4\n", ""
        ),
    )

    assert smoke.main(["--home", str(home), "--workspace", str(workspace)]) == 0
    assert "installer smoke: PASS" in capsys.readouterr().out


def test_main_reports_launcher_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace)
    monkeypatch.setattr(
        smoke.subprocess,
        "run",
        lambda *args, **kwargs: smoke.subprocess.CompletedProcess(
            args[0], 1, "", "launcher failed"
        ),
    )

    assert smoke.main(["--home", str(home), "--workspace", str(workspace)]) == 1
    assert "nexus-hub --version failed" in capsys.readouterr().err


@pytest.mark.parametrize("problem", [None, "missing-reference", "changed-eval", "changed-command", "missing-source"])
def test_source_payload_requires_exact_nested_files_and_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], problem: str | None
) -> None:
    home, workspace, source = (tmp_path / name for name in ("home", "workspace", "source"))
    _seed(home, workspace)
    files = (
        "skills/category/example/SKILL.md",
        "skills/category/example/references/detail.md",
        "skills/category/example/evals/cases.json",
        "commands/example.md",
    )
    for relative in files:
        original = source / "catalog" / relative
        parts = Path(relative).parts
        installed = workspace / ".claude" / (Path("skills", *parts[2:]) if parts[0] == "skills" else Path(relative))
        original.parent.mkdir(parents=True, exist_ok=True)
        installed.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(b"exact payload\r\n")
        installed.write_bytes(original.read_bytes())
    if problem == "missing-reference":
        (workspace / ".claude/skills/example/references/detail.md").unlink()
    elif problem == "changed-eval":
        (workspace / ".claude/skills/example/evals/cases.json").write_bytes(b"different")
    elif problem == "changed-command":
        (workspace / ".claude/commands/example.md").write_bytes(b"different")
    elif problem == "missing-source":
        source = source / "absent"
    monkeypatch.setattr(smoke.subprocess, "run", lambda *args, **kwargs: smoke.subprocess.CompletedProcess(args[0], 0, "nexus-hub 4.14.2\n", ""))
    code = smoke.main(["--home", str(home), "--workspace", str(workspace), "--source", str(source)])
    assert code == (0 if problem is None else 1)
    output = capsys.readouterr()
    assert ("installer smoke: PASS" in output.out) == (problem is None)
    if problem is not None:
        assert "catalog" in output.err
