"""Static regression guards for Windows Claude hooks imported by Cursor."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_INSTALLER = _ROOT / "scripts" / "installer.ps1"
_POSIX_INSTALLER = _ROOT / "scripts" / "installer.sh"


def _function_body(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"function {next_name}", start)
    return source[start:end]


def test_powershell_installer_materializes_windows_hook_siblings() -> None:
    source = _INSTALLER.read_text(encoding="utf-8")
    assert re.search(r"^function Install-ClaudeHookFiles\b", source, re.M)
    body = _function_body(source, "Install-ClaudeHookFiles", "Install-GitGuardrails")
    assert "catalog\\hooks" in body
    assert "*.ps1" in body and "*.py" in body
    assert "Safe-Copy" in body


def test_powershell_installer_rewrites_stale_bash_hook_commands() -> None:
    source = _INSTALLER.read_text(encoding="utf-8")
    assert re.search(r"^function Convert-ClaudeHookCommandsForWindows\b", source, re.M)
    body = _function_body(
        source, "Convert-ClaudeHookCommandsForWindows", "Install-ClaudeHookFiles"
    )
    assert "cursor-hook-compat.py" in body
    assert "--rewrite-settings" in body
    assert "--host windows" in body
    assert "--scope" in body
    install_body = _function_body(source, "Install-GitGuardrails", "Install-UsageDisplay")
    assert "Convert-ClaudeHookCommandsForWindows" in install_body
    assert "Write-JsonFile" in install_body


def test_powershell_installer_no_longer_copies_raw_hook_template() -> None:
    source = _INSTALLER.read_text(encoding="utf-8")
    body = _function_body(source, "Install-GitGuardrails", "Install-UsageDisplay")
    assert "Copy-Item -Path $templateFile -Destination $settingsFile" not in body


def test_posix_installer_materializes_and_migrates_all_hook_files() -> None:
    source = _POSIX_INSTALLER.read_text(encoding="utf-8")
    assert re.search(r"^install_claude_hook_files\(\)", source, re.M)
    copy_body = source[
        source.index("install_claude_hook_files()") : source.index(
            "convert_claude_hook_commands_for_posix()"
        )
    ]
    assert "catalog/hooks/*.sh" in copy_body
    assert "catalog/hooks/*.py" in copy_body
    assert "safe_copy" in copy_body

    migrate_body = source[
        source.index("convert_claude_hook_commands_for_posix()") : source.index(
            "install_git_guardrails()"
        )
    ]
    assert "cursor-hook-compat.py" in migrate_body
    assert "--host posix" in migrate_body
    assert "--scope" in migrate_body

    install_body = source[
        source.index("install_git_guardrails()") : source.index(
            "install_usage_display()"
        )
    ]
    assert "install_claude_hook_files" in install_body
    assert 'merge_managed_claude_hooks "$settings_file" "$template_file"' in install_body
    assert install_body.count("convert_claude_hook_commands_for_posix") >= 2
