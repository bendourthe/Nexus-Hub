"""Hook installation is gated on the `hooks_supported` capability flag (v3.15.0 Phase 1.1).

Before v3.15.0 the flag was declared on every integration config but never read;
hook delivery was implicitly gated on whether an integration declared
`hooks_subdir`. Phase 1.1 made `hooks_supported` the single load-bearing capability
signal, in both the base `SkillsIntegration._mirror_catalog` copy path and the
bespoke `Antigravity20Integration` hooks.json writer. Because every integration
that declares `hooks_subdir` today also sets `hooks_supported: True`, the change is
byte-identical for the live registry; these tests lock in both the gate and that
byte-identical invariant.
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.integrations import get
from scripts.lib.integrations.antigravity import Antigravity20Integration
from scripts.lib.integrations.base import InstallContext, SkillsIntegration
from scripts.lib.integrations.manifest import InstallManifest


def _ctx(repo_root: Path, target_root: Path) -> InstallContext:
    return InstallContext(
        repo_root=repo_root,
        target_root=target_root,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
    )


class _HooksSupportedTrue(SkillsIntegration):
    """Minimal skills integration that declares hook support."""

    key = "test-hooks-supported-true"
    config = {
        "workspace_dir": "cfg",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }


class _HooksSupportedFalse(SkillsIntegration):
    """Identical to _HooksSupportedTrue except it does NOT support hooks.

    It still declares `hooks_subdir`; the gate must suppress the hook copy purely
    on the `hooks_supported: False` signal.
    """

    key = "test-hooks-supported-false"
    config = {
        "workspace_dir": "cfg",
        "hooks_subdir": "hooks",
        "hooks_supported": False,
    }


def test_base_mirror_writes_hooks_when_supported(repo_root: Path, tmp_path: Path) -> None:
    result = _HooksSupportedTrue().install_workspace(_ctx(repo_root, tmp_path))
    hooks_dir = tmp_path / "cfg" / "hooks"
    assert hooks_dir.is_dir(), "hooks_supported=True must write the hooks tree"
    assert any(hooks_dir.iterdir()), "the mirrored hooks tree must be non-empty"
    assert any(
        Path(fa.path).name == "hooks" and fa.action in {"created", "updated", "unchanged"}
        for fa in result.files
    ), f"expected a hooks FileAction, got {[(fa.path, fa.action) for fa in result.files]}"


def test_base_mirror_skips_hooks_when_unsupported(repo_root: Path, tmp_path: Path) -> None:
    result = _HooksSupportedFalse().install_workspace(_ctx(repo_root, tmp_path))
    assert not (tmp_path / "cfg" / "hooks").exists(), (
        "hooks_supported=False must write no hook surface even when hooks_subdir is declared"
    )
    assert not any(Path(fa.path).name == "hooks" for fa in result.files), (
        "no hooks FileAction should be emitted when hooks_supported is False"
    )


def test_antigravity2_writes_hooks_json_when_supported(repo_root: Path, tmp_path: Path) -> None:
    result = get("antigravity2").install_workspace(_ctx(repo_root, tmp_path))
    assert any(Path(fa.path).name == "hooks.json" for fa in result.files), (
        "antigravity2 (hooks_supported=True) must write a hooks.json"
    )


def test_antigravity2_skips_hooks_json_when_unsupported(repo_root: Path, tmp_path: Path) -> None:
    class _AntigravityNoHooks(Antigravity20Integration):
        key = "test-antigravity-nohooks"
        config = {**Antigravity20Integration.config, "hooks_supported": False}

    result = _AntigravityNoHooks().install_workspace(_ctx(repo_root, tmp_path))
    assert not any(Path(fa.path).name == "hooks.json" for fa in result.files), (
        "the bespoke antigravity2 hooks.json writer must be gated on hooks_supported"
    )
    assert not (tmp_path / ".agents" / "hooks.json").exists()


def test_live_hook_integrations_still_write_hooks(repo_root: Path, tmp_path: Path) -> None:
    """Byte-identical invariant: every live integration that declares hooks_subdir
    also sets hooks_supported=True, so the gate must not have dropped their hooks.
    """
    for key in ("claude", "nexus-ai"):
        integ = get(key)
        assert integ.config.get("hooks_supported") is True
        result = integ.install_workspace(_ctx(repo_root, tmp_path / key))
        assert any(Path(fa.path).name == "hooks" for fa in result.files), (
            f"{key} must still mirror its hooks tree after the hooks_supported gate"
        )
