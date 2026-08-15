"""Tests for the shared cross-OS installer-smoke postcondition checker."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.check_installer_smoke import EXPECTED_SCRIPTS, collect_findings


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
    (settings_dir / "settings.local.json").write_text(json.dumps(settings), encoding="utf-8")


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
    assert any(EXPECTED_SCRIPTS[0] in finding for finding in collect_findings(home, workspace))


def test_template_metadata_leak_is_reported(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    _seed(home, workspace, metadata=True)
    assert any("template metadata" in finding for finding in collect_findings(home, workspace))
