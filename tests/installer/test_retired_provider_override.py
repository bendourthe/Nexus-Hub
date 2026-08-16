"""Installer parity for the temporary v3.17.2 provider-override migration."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_both_installers_copy_and_invoke_the_shared_migration() -> None:
    bash = (ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    powershell = (ROOT / "scripts" / "installer.ps1").read_text(encoding="utf-8")

    assert "install_retired_override_cleanup()" in bash
    assert "function Install-RetiredOverrideCleanup" in powershell
    for body in (bash, powershell):
        assert "catalog/hooks/retire-provider-override.py" in body.replace("\\", "/")
        assert body.count("retire-provider-override.py") >= 4
        assert '"Global"' in body
        assert '"Workspace"' in body


def test_session_start_registers_only_the_retirement_migration() -> None:
    settings = json.loads((ROOT / "catalog" / "hooks" / "settings.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"]
        for group in settings["hooks"]["SessionStart"]
        for hook in group["hooks"]
    ]

    assert any("retire-provider-override.py" in command for command in commands)
    assert not any("autonomy-expiry" in command for command in commands)
    assert not any("autonomy-guard" in command for command in commands)
