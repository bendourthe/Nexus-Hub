"""The shared notify helper ships with the completion hook (AR-45, v4.13.11).

``notify-on-complete`` loads ``_notify_common`` from its own directory and exits
silently when that file is absent. Codex hit this in v3.15.11; Qwen Code, Gemini
CLI and Kimi Code CLI kept the same defect until v4.13.11 because their hook
builders never resolved sourced modules. These tests install each platform's hooks
into a temporary home, assert the helper pair lands beside the hook, and run the
installed hook in dry-run mode to prove it reaches its notification step.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._kimi_native import build_kimi_hooks
from scripts.lib.integrations._settings_hooks import (
    GEMINI_CLI_SPEC,
    QWEN_SPEC,
    build_settings_hooks,
)
from scripts.lib.integrations.base import InstallContext

HELPERS = ("_notify_common.sh", "_notify_common.ps1")

_GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)


def _catalog_settings(repo_root: Path) -> dict:
    path = repo_root / "catalog" / "hooks" / "settings.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _install(key: str, ctx: InstallContext) -> Path:
    """Install one platform's hooks into the temp home; return the hooks dir."""
    integration = get(key)
    if key == "kimi":
        root = (ctx.target_root / ".kimi-code").resolve()
        integration._install_hooks(root, ctx)
    else:
        config_dir = ".gemini" if key == "gemini-cli" else ".qwen"
        root = (ctx.target_root / config_dir).resolve()
        integration._install_settings_hooks(root, ctx, scope="workspace")
    return root / "hooks"


def _working_bash() -> str | None:
    candidates = [c for c in (shutil.which("bash"),) if c]
    candidates += [c for c in _GIT_BASH_CANDIDATES if Path(c).is_file()]
    for candidate in candidates:
        try:
            probe = subprocess.run(
                [candidate, "-c", "exit 0"], capture_output=True, timeout=30, check=False
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            return candidate
    return None


def _dry_run_env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["NEXUS_NOTIFY_DRY_RUN"] = "1"
    env["NEXUS_NOTIFY_DISABLED_FILE"] = str(home / "no-such-switch")
    env.pop("NEXUS_DISABLED_HOOKS", None)
    env.pop("NEXUS_HOOK_PROFILE", None)
    return env


@pytest.mark.parametrize(
    ("key", "builder"),
    [
        ("qwen", lambda s, d: build_settings_hooks(QWEN_SPEC, s, d, "/h", False)),
        (
            "gemini-cli",
            lambda s, d: build_settings_hooks(GEMINI_CLI_SPEC, s, d, "/h", False),
        ),
        ("kimi", lambda s, d: build_kimi_hooks(s, d, "/h", False)),
    ],
)
def test_builder_returns_the_helper_with_the_completion_hook(repo_root, key, builder):
    src = repo_root / "catalog" / "hooks"
    _, scripts, _ = builder(_catalog_settings(repo_root), src)
    assert "notify-on-complete.sh" in scripts, f"{key}: completion hook not delivered"
    for helper in HELPERS:
        assert helper in scripts, f"{key}: {helper} not shipped with its hook"


@pytest.mark.parametrize("key", ["qwen", "gemini-cli", "kimi"])
def test_install_lands_helper_beside_the_hook(install_ctx, key):
    hooks_dir = _install(key, install_ctx)
    assert (hooks_dir / "notify-on-complete.sh").is_file()
    for helper in HELPERS:
        assert (hooks_dir / helper).is_file(), f"{key}: {helper} missing after install"


@pytest.mark.parametrize("key", ["qwen", "gemini-cli", "kimi"])
def test_installed_completion_hook_reaches_its_notification(install_ctx, key):
    """Run the INSTALLED copy: without the helper it exits 0 and prints nothing."""
    bash = _working_bash()
    if bash is None:
        pytest.skip("no working bash interpreter on this host")
    hooks_dir = _install(key, install_ctx)
    proc = subprocess.run(
        [bash, (hooks_dir / "notify-on-complete.sh").as_posix()],
        input="{}",
        text=True,
        capture_output=True,
        timeout=60,
        env=_dry_run_env(install_ctx.target_root),
        check=False,
    )
    assert proc.returncode == 0
    assert "Task complete" in proc.stdout, (
        f"{key}: installed hook never reached its notification step; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# ----- Kimi trigger A (AR-45 Kimi event verdict) ---------------------------
#
# Fetched 2026-10-10 from kimi.com/code/docs/.../customization/hooks.html: Kimi's
# `Notification` is "Triggered when a background task status changes", while
# `PermissionRequest` is "Triggered just before waiting for user approval". The
# attention notifier therefore belongs on PermissionRequest; on Notification it
# would toast on every background-task transition.


def test_kimi_attention_notifier_rides_permission_request(repo_root):
    src = repo_root / "catalog" / "hooks"
    entries, _, skipped = build_kimi_hooks(_catalog_settings(repo_root), src, "/h", False)
    by_event: dict[str, list[str]] = {}
    for entry in entries:
        by_event.setdefault(entry["event"], []).append(entry["command"])
    assert any(
        "notify-attention-required" in c for c in by_event.get("PermissionRequest", [])
    ), f"attention notifier not on PermissionRequest; skipped={skipped}"
    assert not any(
        "notify-attention-required" in c for c in by_event.get("Notification", [])
    ), "attention notifier wired to Kimi Notification (background-task changes)"
    assert any("notify-on-complete" in c for c in by_event.get("Stop", []))
    for event in ("SubagentStop", "SubagentStart"):
        assert not any("notify-" in c for c in by_event.get(event, []))
