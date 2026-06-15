"""Parameterized contract test suite for every registered integration.

For each of the 13 integrations, this suite asserts five invariants:

  1. install_idempotent       - a second install is all `unchanged` / `kept`.
  2. uninstall_reverses_install - install followed by uninstall leaves no
                                  Nexus-Hub managed bytes behind.
  3. sibling_preservation     - install does not clobber unrelated user
                                  content already present in the instruction
                                  file.
  4. partial_state_recovery   - deleting one installed file then re-installing
                                  recreates it.
  5. dry_run_matches_install  - the histogram of actions returned by dry_run
                                  against a fresh tmp_path matches the
                                  histogram from install against a separately
                                  cloned fresh tmp_path.

Total cases: 13 integrations * 5 invariants = 65 (with documented skips for
the rare cases that legitimately do not apply).
"""

from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Set

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY, list_keys  # noqa: E402
from scripts.lib.integrations.base import InstallContext, IntegrationBase  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.result import FileAction, WriteResult  # noqa: E402

ALL_KEYS = sorted(INTEGRATION_REGISTRY)
# Dedicated-mode integrations: they refuse to overwrite the instruction file
# without --overwrite, so the sibling test is satisfied trivially (the file is
# kept verbatim). Listed here so the test reports the skip explicitly rather
# than getting an unexpected outcome.
DEDICATED_KEYS = {"nexus-ai"}


def _make_ctx(target: Path, overwrite: bool = False) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=overwrite,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


def _files_in(root: Path) -> Set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def fresh_target(tmp_path: Path) -> Path:
    target = tmp_path / "workspace"
    target.mkdir()
    return target


# ---------------------------------------------------------------------------
# Invariant 1 - install_idempotent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_install_idempotent(key: str, fake_home: Path, fresh_target: Path) -> None:
    integ = INTEGRATION_REGISTRY[key]
    ctx1 = _make_ctx(fresh_target)
    integ.install(ctx1)
    # Second install reuses the same target but a fresh manifest (we want to
    # measure what install would report cold, not just based on tracked files).
    ctx2 = _make_ctx(fresh_target)
    result2 = integ.install(ctx2)
    bad = [
        fa
        for fa in result2.files
        if fa.action not in ("unchanged", "kept", "not-found")
    ]
    assert not bad, (
        f"{key}: second install reported non-idempotent actions: "
        f"{[(fa.action, fa.path) for fa in bad]}"
    )


# ---------------------------------------------------------------------------
# Invariant 2 - uninstall_reverses_install
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_uninstall_reverses_install(
    key: str, fake_home: Path, fresh_target: Path
) -> None:
    integ = INTEGRATION_REGISTRY[key]
    snapshot_before = _files_in(fresh_target)

    manifest = InstallManifest()
    ctx_install = InstallContext(
        repo_root=REPO_ROOT,
        target_root=fresh_target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    integ.install(ctx_install)

    ctx_uninstall = InstallContext(
        repo_root=REPO_ROOT,
        target_root=fresh_target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    integ.uninstall(ctx_uninstall)

    snapshot_after = _files_in(fresh_target)
    leftover = snapshot_after - snapshot_before
    # The .nexus-hub/install-manifest.json is written by runner.cmd_install,
    # not by integ.install(). Confirm none of our other paths leaked through.
    real_leaks = {p for p in leftover if ".nexus-hub" not in p.parts}
    assert not real_leaks, (
        f"{key}: uninstall left files behind: {sorted(real_leaks)}"
    )


# ---------------------------------------------------------------------------
# Invariant 3 - sibling_preservation
# ---------------------------------------------------------------------------


def _instruction_file_for(integ: IntegrationBase, target: Path) -> Path | None:
    """Return the path to the integration's instruction file under target, if any."""
    instr_file = integ.config.get("instruction_file")
    if not instr_file:
        return None
    # Cursor writes AGENTS.md at the project root via a bespoke override.
    if integ.key == "cursor":
        return target / instr_file
    # v2.3.0 / DF-001: the instruction file lives under instruction_workspace_dir
    # (claude/codex set it to "" -> project root); it defaults to workspace_dir
    # for everyone else (gemini/opencode/copilot/...).
    iwd = integ.config.get("instruction_workspace_dir", integ.config.get("workspace_dir"))
    if iwd is None:
        return None
    return target / iwd / instr_file


@pytest.mark.parametrize("key", ALL_KEYS)
def test_sibling_preservation(
    key: str, fake_home: Path, fresh_target: Path
) -> None:
    """User content adjacent to the Nexus-Hub block must survive a re-install."""
    integ = INTEGRATION_REGISTRY[key]
    instr_path = _instruction_file_for(integ, fresh_target)
    if instr_path is None:
        pytest.skip(f"{key} has no instruction file in workspace scope")

    # Pre-populate the instruction file with unique user content.
    instr_path.parent.mkdir(parents=True, exist_ok=True)
    unique_marker = "USER_CONTENT_DO_NOT_TOUCH_42"
    user_body = f"# My own notes\n\n{unique_marker}\n"
    instr_path.write_text(user_body, encoding="utf-8")

    integ.install(_make_ctx(fresh_target))

    if key in DEDICATED_KEYS:
        # Dedicated-mode: file is "kept" verbatim because Nexus-Hub does not
        # overwrite without --overwrite. User content remains unchanged.
        assert instr_path.read_text(encoding="utf-8") == user_body
        return

    survived = instr_path.read_text(encoding="utf-8")
    assert unique_marker in survived, (
        f"{key}: install clobbered user content; instruction file no longer "
        f"contains the unique marker."
    )


# ---------------------------------------------------------------------------
# Invariant 4 - partial_state_recovery
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_partial_state_recovery(
    key: str, fake_home: Path, fresh_target: Path
) -> None:
    integ = INTEGRATION_REGISTRY[key]
    manifest = InstallManifest()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=fresh_target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=manifest,
        template_vars={"PROJECT_NAME": "test-project"},
    )
    integ.install(ctx)

    # Find one tracked file to delete.
    tracked = manifest.files_for(key) + manifest.shared_for(key)
    file_paths = [Path(p) for p in tracked if Path(p).is_file()]
    if not file_paths:
        pytest.skip(f"{key} installed no files to delete in workspace scope")
    victim = file_paths[0]
    if victim.is_dir():
        shutil.rmtree(victim, ignore_errors=True)
    else:
        victim.unlink(missing_ok=True)
    assert not victim.exists()

    # Re-install. The victim must come back.
    integ.install(_make_ctx(fresh_target))
    assert victim.exists(), (
        f"{key}: partial state was not recovered; {victim} is still missing"
    )


# ---------------------------------------------------------------------------
# Invariant 5 - dry_run_matches_install
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ALL_KEYS)
def test_dry_run_matches_install(
    key: str, fake_home: Path, tmp_path: Path
) -> None:
    """The action histogram from dry_run on a fresh state matches the
    histogram from install against a separately-cloned fresh state.
    """
    integ = INTEGRATION_REGISTRY[key]
    dry_target = tmp_path / "dry"
    install_target = tmp_path / "install"
    dry_target.mkdir()
    install_target.mkdir()

    dry_result = integ.dry_run(_make_ctx(dry_target))
    install_result = integ.install(_make_ctx(install_target))

    dry_hist = Counter(fa.action for fa in dry_result.files)
    install_hist = Counter(fa.action for fa in install_result.files)
    assert dry_hist == install_hist, (
        f"{key}: dry_run histogram {dict(dry_hist)} != install histogram {dict(install_hist)}"
    )
