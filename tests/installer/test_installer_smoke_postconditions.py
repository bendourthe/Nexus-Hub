"""Tests for the shared cross-OS installer-smoke postcondition checker."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import check_installer_smoke as smoke
from scripts.check_installer_smoke import EXPECTED_SCRIPTS, collect_findings

NEXUS_START_MARKER = "<!-- NEXUS_HUB_START -->"
NEXUS_END_MARKER = "<!-- NEXUS_HUB_END -->"
ORG_START_MARKER = "<!-- NEXUS_HUB_ORG_START -->"
ORG_END_MARKER = "<!-- NEXUS_HUB_ORG_END -->"
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
