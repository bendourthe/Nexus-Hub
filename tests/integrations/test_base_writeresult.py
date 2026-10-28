"""Tests asserting each integration's lifecycle methods return WriteResult (T002).

Also covers the unchanged-on-byte-match optimization for instruction-file writes
and tree mirrors.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.integrations import get, list_keys
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.result import FileAction, WriteResult


@pytest.fixture(autouse=True)
def _isolated_nexus_state(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the instruction-merge lock and backup state out of the real profile.

    A reinstall finds an existing instruction file and takes a per-target lock under
    the Nexus state root, which falls back to the real home unless NEXUS_HUB_HOME is
    set. The directory sits outside tmp_path so tests that snapshot tmp_path see no
    extra entries.
    """
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path_factory.mktemp("nexus-home")))



@pytest.mark.parametrize("key", sorted(list_keys()))
def test_install_workspace_returns_write_result(install_ctx: InstallContext, key: str) -> None:
    integ = get(key)
    result = integ.install_workspace(install_ctx)
    assert isinstance(result, WriteResult), (
        f"{key}.install_workspace must return WriteResult, got {type(result).__name__}"
    )
    for fa in result.files:
        assert isinstance(fa, FileAction)


@pytest.mark.parametrize("key", sorted(list_keys()))
def test_install_dispatch_returns_write_result(install_ctx: InstallContext, key: str) -> None:
    integ = get(key)
    result = integ.install(install_ctx)
    assert isinstance(result, WriteResult), (
        f"{key}.install must return WriteResult, got {type(result).__name__}"
    )


@pytest.mark.parametrize(
    "key,expected_first_actions",
    [
        ("claude", {"created"}),
        ("codex", {"created"}),
        ("gemini", {"created"}),
        ("opencode", {"created"}),
        ("antigravity", {"created"}),
        ("antigravity2", {"created"}),
        ("nexus-ai", {"created"}),
    ],
)
def test_fresh_install_surfaces_created_actions(
    install_ctx: InstallContext, key: str, expected_first_actions: set[str]
) -> None:
    integ = get(key)
    result = integ.install(install_ctx)
    actions_seen = {fa.action for fa in result.files}
    assert actions_seen & expected_first_actions, (
        f"{key}: expected at least one of {expected_first_actions} "
        f"on fresh install, saw {actions_seen}"
    )


def test_unchanged_surfaces_on_byte_identical_reinstall(install_ctx: InstallContext) -> None:
    """A second install over an unchanged target reports `unchanged`, not `created`/`updated`.

    The fixture install_ctx has overwrite=False; on the second pass every file
    on disk is byte-identical to what would be rendered. The instruction file
    short-circuits to `unchanged`; tree mirrors detect byte-equality and also
    return `unchanged`.
    """
    integ = get("opencode")
    first = integ.install(install_ctx)
    # First pass: at least one created action expected.
    assert any(fa.action == "created" for fa in first.files), (
        f"first install should report created actions, got {[fa.action for fa in first.files]}"
    )

    # Same context, second invocation: dst paths exist with identical bytes.
    second = integ.install(install_ctx)
    instruction_actions = [
        fa for fa in second.files if fa.path.endswith("AGENTS.md")
    ]
    assert instruction_actions, "second install should surface an action for the instruction file"
    assert instruction_actions[0].action == "unchanged", (
        f"byte-identical reinstall must surface 'unchanged' for the instruction file, "
        f"got {instruction_actions[0].action}"
    )


def test_teardown_returns_write_result_with_removed_actions(
    install_ctx: InstallContext,
) -> None:
    integ = get("opencode")
    integ.install(install_ctx)
    result = integ.teardown(install_ctx)
    assert isinstance(result, WriteResult)
    assert result.files, "teardown should report at least one removed FileAction"
    assert all(fa.action in {"removed", "not-found"} for fa in result.files)


def test_copilot_marker_block_settles_after_two_installs(install_ctx: InstallContext) -> None:
    """Copilot now uses the canonical merge_marker_section primitive (v2.3.0 /
    MT-1): pass 1 creates the marker-wrapped block; every subsequent install is
    a byte-identical no-op reported as ``unchanged`` (the shared-mode vocabulary
    used by cursor/codex/gemini), not the bespoke ``kept`` of the old flow.
    """
    integ = get("copilot")
    first = integ.install(install_ctx)
    assert "created" in [fa.action for fa in first.files]
    integ.install(install_ctx)
    third = integ.install(install_ctx)
    actions = [fa.action for fa in third.files]
    assert "unchanged" in actions, (
        f"copilot re-install should settle to a no-op (unchanged) once the marker "
        f"block is present, got {actions}"
    )


@pytest.fixture(scope="module")
def legacy_callbacks_during_module_setup():
    from scripts.lib.integrations import legacy

    # This ordinary module fixture must run after the module-autouse boundary.
    return tuple(legacy.LEGACY_CLEANUPS["claude"])


def test_host_callbacks_are_isolated_before_module_setup(legacy_callbacks_during_module_setup) -> None:
    from scripts.lib.integrations import legacy

    callbacks = legacy_callbacks_during_module_setup
    assert legacy._cleanup_claude_legacy_vscode_extension not in callbacks
    assert legacy._cleanup_windows_auth_monitor_task not in callbacks
    assert legacy._cleanup_claude_legacy_skill_registry in callbacks
    assert legacy._cleanup_devai_hub_legacy_global_dir in callbacks
    assert legacy._cleanup_devai_hub_auth_monitor_vbs in callbacks
    assert legacy._cleanup_devai_hub_auth_monitor_ps1 in callbacks


def test_private_home_keeps_real_filesystem_cleanup(tmp_path: Path, tmp_path_factory: pytest.TempPathFactory, install_ctx: InstallContext) -> None:
    from scripts.lib.integrations import legacy

    callbacks = legacy.LEGACY_CLEANUPS["claude"]
    # Missing isolation must fail here, before any real callback can reach the host.
    assert legacy._cleanup_claude_legacy_vscode_extension not in callbacks
    assert legacy._cleanup_windows_auth_monitor_task not in callbacks
    home = Path.home()
    assert home.is_relative_to(tmp_path_factory.getbasetemp())
    assert not home.is_relative_to(tmp_path)
    artifact = home / ".claude" / "devai-hub-skills.json"
    artifact.parent.mkdir()
    artifact.write_text("legacy fixture", encoding="utf-8")
    actions = legacy.run_cleanups("claude", install_ctx)
    assert not artifact.exists()
    assert any(action.path == str(artifact) and action.action == "removed" for action in actions)
