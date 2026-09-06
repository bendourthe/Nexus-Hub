"""Real installer regression coverage for managed Claude hook upgrades."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import pytest

from scripts import check_installer_smoke as smoke
from scripts.check_installer_smoke import EXPECTED_WORKSPACE_ARTIFACTS, HTML_HOOK_STEM

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_STEM_PATTERN = re.compile(r"(?P<stem>[A-Za-z0-9_-]+)\.(?:sh|ps1|py)")


def _native_installer(workspace: Path) -> list[str]:
    if os.name == "nt":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if not powershell:
            raise RuntimeError("PowerShell is unavailable")
        return [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts" / "installer.ps1"),
            "-Workspace",
            str(workspace),
            "-Platforms",
            "claude",
            "-Yes",
        ]
    bash = shutil.which("bash")
    if not bash:
        raise RuntimeError("Bash is unavailable")
    return [
        bash,
        str(REPO_ROOT / "scripts" / "installer.sh"),
        "--workspace",
        str(workspace),
        "--platforms",
        "claude",
        "--yes",
    ]


def _managed_identities(settings: dict[str, object]) -> list[tuple[str, str, str, str]]:
    identities: list[tuple[str, str, str, str]] = []
    hooks = settings.get("hooks", {})
    assert isinstance(hooks, dict)
    for event, entries in hooks.items():
        assert isinstance(entries, list)
        for entry in entries:
            assert isinstance(entry, dict)
            matcher = str(entry.get("matcher", ""))
            for hook in entry.get("hooks", []):
                assert isinstance(hook, dict)
                command = str(hook.get("command", ""))
                matches = list(HOOK_STEM_PATTERN.finditer(command))
                if matches:
                    identities.append(
                        (
                            event,
                            matcher,
                            str(hook.get("type", "")),
                            matches[-1].group("stem"),
                        )
                    )
    return identities


def _run_installer(
    command: list[str], env: dict[str, str], run_number: int
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"installer run {run_number} failed:\n{result.stdout}\n{result.stderr}"
    )
    return result


def _write_parser_override_bash_env(path: Path) -> Path:
    path.write_text(
        """command() {
    if [ "${NEXUS_TEST_HIDE_MERGE_JQ:-1}" = "1" ] &&
       [ "${1:-}" = "-v" ] && [ "${2:-}" = "jq" ]; then
        return 1
    fi
    if [ "${NEXUS_TEST_HIDE_MERGE_PYTHON:-0}" = "1" ] &&
       [ "${1:-}" = "-v" ] &&
       { [ "${2:-}" = "python3" ] || [ "${2:-}" = "python" ]; } &&
       [ "${FUNCNAME[2]:-}" = "merge_managed_claude_hooks" ]; then
        return 1
    fi
    if [ "${NEXUS_TEST_HIDE_CONVERSION_PYTHON:-0}" = "1" ] &&
       [ "${1:-}" = "-v" ] &&
       { [ "${2:-}" = "python3" ] || [ "${2:-}" = "python" ]; } &&
       [ "${FUNCNAME[2]:-}" = "convert_claude_hook_commands_for_posix" ]; then
        return 1
    fi
    builtin command "$@"
}
""",
        encoding="utf-8",
    )
    return path


def _write_jq_passthrough(path: Path) -> Path:
    path.parent.mkdir(parents=True)
    path.write_text(
        """#!/usr/bin/env python3
import json
import sys

with open(sys.argv[-2], encoding="utf-8") as handle:
    existing = json.load(handle)
json.dump(existing, sys.stdout, ensure_ascii=False, indent=2)
sys.stdout.write("\\n")
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _existing_settings(existing_hooks: object = None) -> dict[str, object]:
    return {
        "customUserSetting": {"preserve": True},
        "customList": [1, {"nested": ["keep", None]}],
        "permissions": {"allow": ["Read"], "deny": ["Bash(rm:*)"]},
        "hooks": existing_hooks,
    }


def _verify_existing_settings_upgrade(
    home: Path,
    workspace: Path,
    *,
    existing_hooks: object = None,
    extra_env: dict[str, str] | None = None,
) -> None:
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    home.mkdir()
    host_suffix = ".ps1" if os.name == "nt" else ".sh"
    old_suffix = ".sh" if os.name == "nt" else ".ps1"
    settings_path = settings_dir / "settings.json"
    initial_settings = _existing_settings(existing_hooks)
    settings_path.write_text(json.dumps(initial_settings), encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
        }
    )
    if extra_env:
        env.update(extra_env)
    command = _native_installer(workspace)
    template = json.loads(
        (REPO_ROOT / "catalog" / "hooks" / "settings.json").read_text(encoding="utf-8")
    )
    expected_identities = Counter(_managed_identities(template))

    _run_installer(command, env, 1)
    first_run = json.loads(settings_path.read_text(encoding="utf-8"))
    assert Counter(_managed_identities(first_run)) == expected_identities
    for key, value in initial_settings.items():
        if key != "hooks":
            assert first_run[key] == value
    if isinstance(existing_hooks, dict):
        for event, entries in existing_hooks.items():
            assert first_run["hooks"][event][: len(entries)] == entries

    _run_installer(command, env, 2)
    second_run = json.loads(settings_path.read_text(encoding="utf-8"))
    assert second_run == first_run

    changed = False
    for entries in second_run["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command_text = str(hook.get("command", ""))
                host_name = f"git-guardrails{host_suffix}"
                if host_name in command_text:
                    hook["command"] = command_text.replace(
                        host_name, f"git-guardrails{old_suffix}"
                    )
                    changed = True
    assert changed, "first install did not materialize the git guardrail"
    settings_path.write_text(json.dumps(second_run), encoding="utf-8")

    _run_installer(command, env, 3)
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    for key, value in initial_settings.items():
        if key != "hooks":
            assert settings[key] == value
    identities = _managed_identities(settings)
    duplicate_identities = [
        identity for identity, count in Counter(identities).items() if count != 1
    ]
    assert duplicate_identities == []
    assert Counter(identities) == expected_identities
    assert ("PreToolUse", "Write", "command", HTML_HOOK_STEM) in identities
    assert ("PreToolUse", "Edit", "command", HTML_HOOK_STEM) in identities
    git_commands = [
        str(hook.get("command", ""))
        for entries in settings["hooks"].values()
        for entry in entries
        for hook in entry.get("hooks", [])
        if "git-guardrails" in str(hook.get("command", ""))
    ]
    assert len(git_commands) == 1
    assert f"git-guardrails{host_suffix}" in git_commands[0]
    for relative_path in EXPECTED_WORKSPACE_ARTIFACTS:
        assert (workspace / relative_path).is_file()
    assert smoke._html_hook_findings(workspace) == []


def test_existing_settings_receive_each_managed_hook_once(tmp_path: Path) -> None:
    _verify_existing_settings_upgrade(tmp_path / "home", tmp_path / "workspace")


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_existing_settings_upgrade_without_jq(tmp_path: Path) -> None:
    bash_env = _write_parser_override_bash_env(tmp_path / "no-jq.bash")
    custom_hooks = {
        "PreToolUse": [
            {
                "matcher": "CustomTool",
                "hooks": [{"type": "command", "command": "custom-user-hook --keep"}],
                "userMetadata": {"preserve": True},
            }
        ]
    }
    _verify_existing_settings_upgrade(
        tmp_path / "home",
        tmp_path / "workspace",
        existing_hooks=custom_hooks,
        extra_env={"BASH_ENV": str(bash_env)},
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_existing_settings_upgrade_fails_without_safe_parser(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    home.mkdir()
    settings_path = settings_dir / "settings.json"
    initial_settings = _existing_settings()
    original_text = json.dumps(initial_settings)
    settings_path.write_text(original_text, encoding="utf-8")
    bash_env = _write_parser_override_bash_env(tmp_path / "no-safe-parser.bash")
    env = os.environ.copy()
    env.update(
        {
            "BASH_ENV": str(bash_env),
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
            "NEXUS_TEST_HIDE_MERGE_PYTHON": "1",
        }
    )

    result = subprocess.run(
        _native_installer(workspace),
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Cannot safely upgrade" in output
    assert "without jq, python3, or python" in output
    assert settings_path.read_text(encoding="utf-8") == original_text


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_existing_settings_remain_unchanged_when_conversion_fails(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    home.mkdir()
    settings_path = settings_dir / "settings.json"
    original_text = json.dumps(_existing_settings())
    settings_path.write_text(original_text, encoding="utf-8")

    bin_dir = tmp_path / "bin"
    _write_jq_passthrough(bin_dir / "jq")
    bash_env = _write_parser_override_bash_env(tmp_path / "conversion-fails.bash")
    env = os.environ.copy()
    env.update(
        {
            "BASH_ENV": str(bash_env),
            "HOME": str(home),
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
            "NEXUS_TEST_HIDE_CONVERSION_PYTHON": "1",
            "NEXUS_TEST_HIDE_MERGE_JQ": "0",
        }
    )

    result = subprocess.run(
        _native_installer(workspace),
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )

    assert result.returncode != 0
    assert "Python is required to migrate Claude hook commands" in (
        result.stdout + result.stderr
    )
    assert settings_path.read_text(encoding="utf-8") == original_text


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_fresh_settings_are_not_created_when_conversion_fails(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    settings_path = workspace / ".claude" / "settings.json"
    bash_env = _write_parser_override_bash_env(tmp_path / "fresh-conversion-fails.bash")
    env = os.environ.copy()
    env.update(
        {
            "BASH_ENV": str(bash_env),
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
            "NEXUS_TEST_HIDE_CONVERSION_PYTHON": "1",
        }
    )

    result = subprocess.run(
        _native_installer(workspace),
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )

    assert result.returncode != 0
    assert "Python is required to migrate Claude hook commands" in (
        result.stdout + result.stderr
    )
    assert not settings_path.exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_existing_settings_symlink_is_preserved(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    settings_dir = workspace / ".claude"
    target_dir = tmp_path / "dotfiles"
    settings_dir.mkdir(parents=True)
    target_dir.mkdir()
    home.mkdir()

    target_path = target_dir / "claude-settings.json"
    target_path.write_text(json.dumps(_existing_settings()), encoding="utf-8")
    settings_path = settings_dir / "settings.json"
    settings_path.symlink_to(os.path.relpath(target_path, settings_dir))
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
        }
    )

    _run_installer(_native_installer(workspace), env, 1)

    assert settings_path.is_symlink()
    installed = json.loads(target_path.read_text(encoding="utf-8"))
    assert installed["customUserSetting"] == {"preserve": True}
    template = json.loads(
        (REPO_ROOT / "catalog" / "hooks" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    assert Counter(_managed_identities(installed)) == Counter(
        _managed_identities(template)
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX installer coverage")
def test_posix_python_fallback_accepts_utf8_bom_settings(tmp_path: Path) -> None:
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    home.mkdir()
    settings_path = settings_dir / "settings.json"
    original = json.dumps(_existing_settings()).encode("utf-8")
    settings_path.write_bytes(b"\xef\xbb\xbf" + original)
    bash_env = _write_parser_override_bash_env(tmp_path / "no-jq-bom.bash")
    env = os.environ.copy()
    env.update(
        {
            "BASH_ENV": str(bash_env),
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
        }
    )

    _run_installer(_native_installer(workspace), env, 1)

    installed = json.loads(settings_path.read_text(encoding="utf-8"))
    assert installed["customUserSetting"] == {"preserve": True}
    template = json.loads(
        (REPO_ROOT / "catalog" / "hooks" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    assert Counter(_managed_identities(installed)) == Counter(
        _managed_identities(template)
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nexus-hook-upgrade-") as temp_dir:
        root = Path(temp_dir)
        _verify_existing_settings_upgrade(root / "home", root / "workspace")
    print("managed hook upgrade: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
