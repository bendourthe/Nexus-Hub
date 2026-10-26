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

import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Set

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY, legacy, list_keys  # noqa: E402
from scripts.lib.integrations.base import InstallContext, IntegrationBase  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.result import FileAction, WriteResult  # noqa: E402

ALL_KEYS = sorted(INTEGRATION_REGISTRY)
# Dedicated-mode integrations: they refuse to overwrite the instruction file
# without --overwrite, so the sibling test is satisfied trivially (the file is
# kept verbatim). Listed here so the test reports the skip explicitly rather
# than getting an unexpected outcome.
DEDICATED_KEYS = {"nexus-ai"}


_CONTRACT_SKILL_NAMES = ("code-commit-workflow", "unit-tests")


@pytest.fixture(scope="session")
def contract_source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build one representative source; full-catalog delivery has dedicated tests."""
    source = tmp_path_factory.mktemp("contract-source")
    for relative in (
        "catalog/agents", "catalog/commands", "catalog/rules", "catalog/hooks",
        "catalog/mcp-configs", "catalog/style-guides", "catalog/plugins",
        "configs", "templates", ".claude-plugin",
    ):
        shutil.copytree(REPO_ROOT / relative, source / relative)
    compat = Path("scripts/lib/integrations/_cascade_hook_compat.py")
    (source / compat).parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / compat, source / compat)

    registry = json.loads((REPO_ROOT / "data/skills.json").read_text(encoding="utf-8"))
    selected = [skill for skill in registry["skills"] if skill["name"] in _CONTRACT_SKILL_NAMES]
    assert {skill["name"] for skill in selected} == set(_CONTRACT_SKILL_NAMES)
    for skill in selected:
        relative = Path(skill["path"])
        shutil.copytree(REPO_ROOT / relative, source / relative)
    data = source / "data"
    data.mkdir()
    fixture_registry = {
        "metadata": registry["metadata"],
        "statistics": {
            "total_skills": len(selected),
            "categories": dict(Counter(skill["category"] for skill in selected)),
        },
        "skills": selected,
    }
    (data / "skills.json").write_text(json.dumps(fixture_registry), encoding="utf-8")
    bundles = json.loads((REPO_ROOT / "data/bundles.json").read_text(encoding="utf-8"))
    for section in ("bundles", "modules"):
        for group in bundles[section]:
            group["skills"] = [name for name in group["skills"] if name in _CONTRACT_SKILL_NAMES]
    for profile in bundles["profiles"]:
        profile["extra_skills"] = [name for name in profile.get("extra_skills", []) if name in _CONTRACT_SKILL_NAMES]
    (data / "bundles.json").write_text(json.dumps(bundles), encoding="utf-8")
    rows = [f"| {skill['name']} | {skill['category']} | {skill['file']} |" for skill in selected]
    index = "# Contract Fixture Skills\n\n| Skill | Category | File |\n|---|---|---|\n" + "\n".join(rows) + "\n"
    (data / "SKILL_INDEX.md").write_text(index, encoding="utf-8")
    return source


@pytest.fixture(autouse=True)
def isolated_contract_environment(contract_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise install invariants without reaching editor or scheduled-task state."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", contract_source)
    # Legacy migration is covered with fake CLI/task responses in test_legacy_cleanups.py.
    monkeypatch.setattr(legacy, "run_cleanups", lambda _key, _ctx: [])


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
    # Native Aider YAML is shared user configuration, seeded append-only and
    # deliberately retained. Uninstall must preserve its exact bytes.
    retained_config = fresh_target / ".aider.conf.yml"
    retained_bytes = retained_config.read_bytes() if key == "aider" else None

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
    if key == "aider":
        assert retained_config.read_bytes() == retained_bytes
        real_leaks.discard(retained_config.relative_to(fresh_target))
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


@pytest.mark.parametrize("explicit_override", [False, True])
def test_workspace_instruction_state_is_per_test(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit_override: bool) -> None:
    from scripts.lib.installer.instruction_merge import merge_instruction, state_root

    fake_home = tmp_path / "user-home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    if explicit_override:
        monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "explicit-nexus-home"))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "AGENTS.md"
    original = b"# User instructions\n"
    target.write_bytes(original)
    ctx = _make_ctx(workspace)
    assert merge_instruction(target, "managed instructions", ctx=ctx).action == "updated"
    root = state_root(ctx)
    assert b"managed instructions" in target.read_bytes()
    assert len(list((root / "locks").glob("*.lock"))) == 1
    backups = [p for p in (root / "backups").rglob("*") if p.is_file()]
    assert len(backups) == 1
    assert backups[0].read_bytes() == original
    assert root.is_relative_to(tmp_path), "workspace state escaped the per-test temporary directory"
    if explicit_override:
        assert root == tmp_path / "explicit-nexus-home" / "state"


def test_explicit_global_target_keeps_instruction_state(tmp_path: Path) -> None:
    from scripts.lib.installer.instruction_merge import merge_instruction, state_root

    target_home = tmp_path / "global-home"
    target_home.mkdir()
    target = target_home / "AGENTS.md"
    target.write_text("# User instructions\n", encoding="utf-8")
    ctx = InstallContext(repo_root=REPO_ROOT, target_root=target_home, scope="global", explicit_target=True)
    assert merge_instruction(target, "managed instructions", ctx=ctx).action == "updated"
    root = target_home / ".nexus-hub" / "state"
    assert state_root(ctx) == root
    assert len(list((root / "locks").glob("*.lock"))) == 1
    assert any(p.is_file() for p in (root / "backups").rglob("*"))


def test_contract_source_copies_bundled_resources_without_host_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fake_home: Path) -> None:
    skills = sorted((REPO_ROOT / "catalog/skills").glob("*/*/SKILL.md"))
    assert {path.parent.name for path in skills} == set(_CONTRACT_SKILL_NAMES)
    reference = REPO_ROOT / "catalog/skills/workflow/code-commit-workflow/references/commit-message-examples.md"
    assert reference.is_file()
    bundle = json.loads((REPO_ROOT / "data/bundles.json").read_text(encoding="utf-8"))
    core = next(group for group in bundle["bundles"] if group["id"] == "core-developer")
    assert set(core["skills"]) == set(_CONTRACT_SKILL_NAMES)

    def unexpected_host_cleanup(_ctx: InstallContext) -> None:
        raise AssertionError("generic contract reached host legacy cleanup")

    # If the module's boundary is removed, a real install reaches this sentinel.
    monkeypatch.setitem(legacy.LEGACY_CLEANUPS, "claude", [unexpected_host_cleanup])
    target = tmp_path / "workspace"
    INTEGRATION_REGISTRY["claude"].install(_make_ctx(target))
    installed = target / ".claude/skills/code-commit-workflow/references/commit-message-examples.md"
    assert installed.read_bytes() == reference.read_bytes()
