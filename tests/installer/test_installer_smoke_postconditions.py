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
