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


def _verify_existing_settings_upgrade(home: Path, workspace: Path) -> None:
    settings_dir = workspace / ".claude"
    settings_dir.mkdir(parents=True)
    home.mkdir()
    host_suffix = ".ps1" if os.name == "nt" else ".sh"
    old_suffix = ".sh" if os.name == "nt" else ".ps1"
    settings_path = settings_dir / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "customUserSetting": {"preserve": True},
                "hooks": None,
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "NEXUS_HUB_NO_AUTOSEED": "1",
        }
    )
    command = _native_installer(workspace)
    template = json.loads(
        (REPO_ROOT / "catalog" / "hooks" / "settings.json").read_text(
            encoding="utf-8"
        )
    )
    expected_identities = Counter(_managed_identities(template))

    _run_installer(command, env, 1)
    first_run = json.loads(settings_path.read_text(encoding="utf-8"))
    assert Counter(_managed_identities(first_run)) == expected_identities
    assert first_run["customUserSetting"] == {"preserve": True}

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
    assert settings["customUserSetting"] == {"preserve": True}
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


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nexus-hook-upgrade-") as temp_dir:
        root = Path(temp_dir)
        _verify_existing_settings_upgrade(root / "home", root / "workspace")
    print("managed hook upgrade: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
