"""Regression tests for the temporary v3.17.2 provider-override migration."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).resolve().parent.parent / "retire-provider-override.py"


def _git_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def _run(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK), "--project", str(project), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_state(
    root: Path,
    *,
    platform: str = "claude",
    config: Path,
    backup: Path,
    original_exists: bool,
) -> Path:
    state = root / ".nexus-hub" / "autonomy-state.json"
    state.parent.mkdir()
    state.write_text(
        json.dumps(
            {
                "version": 1,
                "platforms": {
                    platform: {
                        "config_path": str(config),
                        "backup_path": str(backup),
                        "original_exists": original_exists,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return state


def test_no_legacy_state_is_a_quiet_noop(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    result = _run(root)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_existing_config_is_restored_byte_for_byte(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    config = root / ".claude" / "settings.local.json"
    config.parent.mkdir()
    config.write_bytes(b'{"permissions":{"defaultMode":"bypassPermissions"}}\r\n')
    backup = config.with_name("settings.local.json.bak.legacy")
    original = b'{"userSetting":true}\r\n'
    backup.write_bytes(original)
    state = _write_state(
        root, config=config, backup=backup, original_exists=True
    )

    result = _run(root)

    assert result.returncode == 0, result.stderr
    assert config.read_bytes() == original
    assert not backup.exists()
    assert not state.exists()
    assert "restored claude configuration" in result.stdout


def test_created_config_is_removed(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    config = root / ".codex" / "config.toml"
    config.parent.mkdir()
    config.write_text('approval_policy = "never"\n', encoding="utf-8")
    backup = config.with_name("config.toml.bak.legacy")
    backup.write_bytes(b"")
    state = _write_state(
        root, platform="codex", config=config, backup=backup, original_exists=False
    )

    result = _run(root)

    assert result.returncode == 0, result.stderr
    assert not config.exists()
    assert not backup.exists()
    assert not state.exists()


def test_missing_backup_preserves_config_and_state(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    config = root / "opencode.json"
    config.write_text('{"permission":"allow"}\n', encoding="utf-8")
    missing = root / "opencode.json.bak.missing"
    state = _write_state(
        root, platform="opencode", config=config, backup=missing, original_exists=True
    )

    result = _run(root)

    assert result.returncode == 1
    assert config.read_text(encoding="utf-8") == '{"permission":"allow"}\n'
    assert state.exists()
    assert "recorded backup is missing" in result.stderr


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    outside = tmp_path / "outside.json"
    outside.write_text("elevated", encoding="utf-8")
    backup = tmp_path / "outside.json.bak"
    backup.write_text("original", encoding="utf-8")
    state = _write_state(
        root, config=outside, backup=backup, original_exists=True
    )

    result = _run(root)

    assert result.returncode == 1
    assert outside.read_text(encoding="utf-8") == "elevated"
    assert backup.exists()
    assert state.exists()
    assert "escapes the project" in result.stderr


def test_settings_migration_removes_legacy_hooks_and_preserves_user_hooks(
    tmp_path: Path,
) -> None:
    root = _git_repo(tmp_path / "repo")
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps(
            {
                "userSetting": "keep",
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {"type": "command", "command": "bash .claude/hooks/session-start.sh"},
                                {"type": "command", "command": "bash .claude/hooks/autonomy-expiry.sh"},
                            ],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Write|Edit",
                            "hooks": [
                                {"type": "command", "command": "bash .claude/hooks/autonomy-guard.sh"}
                            ],
                        },
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "bash user-hook.sh"}],
                        },
                    ],
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    command = "python3 .claude/hooks/retire-provider-override.py"

    first = _run(root, "--settings", str(settings), "--hook-command", command)
    second = _run(root, "--settings", str(settings), "--hook-command", command)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    document = json.loads(settings.read_text(encoding="utf-8"))
    rendered = json.dumps(document)
    assert "autonomy-expiry" not in rendered
    assert "autonomy-guard" not in rendered
    assert "user-hook.sh" in rendered
    assert document["userSetting"] == "keep"
    assert rendered.count("retire-provider-override.py") == 1
    assert settings.with_name("settings.json.v3.17.2.bak").exists()


def test_malformed_settings_are_left_untouched(tmp_path: Path) -> None:
    root = _git_repo(tmp_path / "repo")
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir()
    original = b"{broken"
    settings.write_bytes(original)

    result = _run(
        root,
        "--settings",
        str(settings),
        "--hook-command",
        "python3 .claude/hooks/retire-provider-override.py",
    )

    assert result.returncode == 1
    assert settings.read_bytes() == original
    assert not settings.with_name("settings.json.v3.17.2.bak").exists()
