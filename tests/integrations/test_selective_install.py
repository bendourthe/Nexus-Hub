"""Focused-install distribution parity across platforms (v3.16.1 Phase 7.2).

Phase 6 proved the three install PATHS agree on what to install. This suite
proves the resulting install is correct at each platform's own documented read
path, under a selection rather than the full catalog.

Three properties are checked per platform, and the second is the one that
actually matters:

1. **Every resolved skill is present.** Weak on its own - a filter that did
   nothing would pass it.
2. **Every excluded skill is absent.** This is what proves filtering happened
   rather than being silently bypassed for a platform whose copy path differs
   (flattened vs nested vs command-as-skill).
3. **Policy infrastructure survives.** Rules and hooks install under every
   selection. A focused install that dropped the secret-scan hook would be less
   safe than the default one, which inverts the point of the feature.

Installs are rendered through the registry rather than the shell installers, so
the suite runs in seconds. Phase 6.5 already covers the shell paths end-to-end
in `tests/installer/test_selection_parity.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.installer.selection import (  # noqa: E402
    SelectionRequest,
    available_from_catalog,
    load_catalog,
    resolve,
)
from scripts.lib.integrations import get  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402

# Platforms that receive an actual skills file-tree. Instruction-only platforms
# (aider, windsurf, openclaw) carry no skills directory, so a skill-set
# assertion would be vacuous for them.
SKILL_BEARING = ["claude", "codex", "cursor", "opencode", "qwen"]

# Representative selections: the narrowest profile, a capability module, and a
# role bundle. `full` is covered by the byte-equivalence check in Phase 6.
SELECTIONS = {
    "minimal": {"profiles": ["minimal"]},
    "ai-engineering": {"modules": ["ai-engineering"]},
    "ai-engineer": {"bundles": ["ai-engineer"]},
}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(REPO_ROOT / "data" / "bundles.json")


@pytest.fixture(scope="module")
def available(catalog):
    return available_from_catalog(catalog, repo_root=REPO_ROOT)


def _plan(catalog, available, kwargs):
    return resolve(catalog, SelectionRequest.from_args(**kwargs), available)


def _install(key: str, target: Path, plan) -> None:
    integ = get(key)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=True,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "fixture"},
        selection=plan,
    )
    integ.install(ctx)


def _skill_dirs(target: Path) -> set:
    """Skill folder names discovered anywhere under the target.

    Deliberately layout-agnostic: platforms differ (flattened one level vs
    nested under a category), and this suite is asserting WHICH skills landed,
    not the shape - Phase 6 and the platform-contract tests own the shape.
    """
    return {p.parent.name for p in target.rglob("SKILL.md")}


@pytest.mark.parametrize("selection_name", sorted(SELECTIONS))
@pytest.mark.parametrize("key", SKILL_BEARING)
def test_focused_install_contains_every_resolved_skill(
    key: str, selection_name: str, catalog, available, tmp_path: Path
) -> None:
    plan = _plan(catalog, available, SELECTIONS[selection_name])
    target = tmp_path / f"{key}-{selection_name}"
    target.mkdir()
    _install(key, target, plan)

    installed = _skill_dirs(target)
    if not installed:
        pytest.skip(f"{key} installed no skills tree at workspace scope")
    missing = [s for s in plan.skills if s not in installed]
    assert not missing, (
        f"{key} / {selection_name}: resolved skills absent from the install: {missing}"
    )


@pytest.mark.parametrize("selection_name", sorted(SELECTIONS))
@pytest.mark.parametrize("key", SKILL_BEARING)
def test_focused_install_excludes_unselected_skills(
    key: str, selection_name: str, catalog, available, tmp_path: Path
) -> None:
    """The load-bearing assertion: filtering actually happened.

    A platform whose copy path differs (flattened, nested, or command-as-skill)
    could silently bypass the filter and still pass the presence test above.
    """
    plan = _plan(catalog, available, SELECTIONS[selection_name])
    target = tmp_path / f"{key}-{selection_name}-excl"
    target.mkdir()
    _install(key, target, plan)

    installed = _skill_dirs(target)
    if not installed:
        pytest.skip(f"{key} installed no skills tree at workspace scope")

    resolved = set(plan.skills)
    catalog_skills = set(available.skills)
    # Command-as-skill wrappers share the skills directory but are commands, not
    # catalog skills, so they are excluded from this comparison by construction.
    leaked = sorted((installed & catalog_skills) - resolved)
    assert not leaked, (
        f"{key} / {selection_name}: {len(leaked)} unselected catalog skills were "
        f"installed, so the filter was bypassed on this path: {leaked[:10]}"
    )


@pytest.mark.parametrize("key", SKILL_BEARING)
def test_policy_surfaces_survive_the_narrowest_selection(
    key: str, catalog, available, tmp_path: Path
) -> None:
    """Rules and hooks are never filtered, under any selection."""
    plan = _plan(catalog, available, SELECTIONS["minimal"])
    target = tmp_path / f"{key}-policy"
    target.mkdir()
    _install(key, target, plan)

    config = get(key).config
    for cfg_key, label in (("rules_subdir", "rules"), ("hooks_subdir", "hooks")):
        subdir = config.get(cfg_key)
        if not subdir:
            continue
        if cfg_key == "hooks_subdir" and not config.get("hooks_supported"):
            continue
        matches = list(target.rglob(f"{Path(subdir).name}/*"))
        assert matches, (
            f"{key}: {label} absent under a minimal selection. Policy "
            "infrastructure must install under EVERY selection; a focused "
            "install that drops a guardrail is less safe than the default one."
        )


@pytest.mark.parametrize("key", SKILL_BEARING)
def test_full_install_is_unfiltered(key: str, tmp_path: Path) -> None:
    """selection=None must leave the pre-v3.16.1 path completely untouched."""
    target = tmp_path / f"{key}-full"
    target.mkdir()
    _install(key, target, None)
    installed = _skill_dirs(target)
    if not installed:
        pytest.skip(f"{key} installed no skills tree at workspace scope")
    on_disk = {p.parent.name for p in (REPO_ROOT / "catalog" / "skills").glob("*/*/SKILL.md")}
    missing = sorted(on_disk - installed)
    assert not missing, (
        f"{key}: an unfiltered install is missing {len(missing)} catalog skills, "
        f"so the no-selector path is no longer equivalent to the old behavior: {missing[:10]}"
    )


# --------------------------------------------------------------------------- #
# Selection metadata correctness, independent of any platform
# --------------------------------------------------------------------------- #

def test_declared_command_requirements_reference_real_skills(catalog, available) -> None:
    reqs = (catalog.get("surface_requirements") or {}).get("commands") or {}
    bad = {c: [s for s in need if s not in available.skills] for c, need in reqs.items()}
    bad = {c: miss for c, miss in bad.items() if miss}
    assert not bad, f"surface_requirements name skills with no catalog directory: {bad}"


def test_declared_commands_exist(catalog, available) -> None:
    reqs = (catalog.get("surface_requirements") or {}).get("commands") or {}
    missing = [c for c in reqs if c not in available.commands]
    assert not missing, f"surface_requirements declare unknown commands: {missing}"


def test_every_catalog_skill_is_reachable_through_some_module(catalog, available) -> None:
    """Modules are category-complete as of schema 1.5.0.

    Before Phase 7.1 only 105 of 271 skills were reachable through any module or
    bundle; the rest existed solely under `full`, which made selective
    installation unable to reach 61% of the catalog. This asserts the property
    that fixed it, so a newly added skill that lands in no module is caught.
    """
    reachable = set()
    for collection in ("modules", "bundles"):
        for entry in catalog.get(collection, []):
            reachable |= set(entry.get("skills", []))
    unreachable = sorted(set(available.skills) - reachable)
    assert not unreachable, (
        f"{len(unreachable)} catalog skills are reachable only via `full`, so no "
        f"focused install can ever include them: {unreachable[:10]}"
    )


def test_a_focused_install_keeps_most_commands(catalog, available) -> None:
    """Sanity bound on the surface-requirement declarations.

    Declaring too aggressively would make focused installs lose commands
    wholesale. Six of twenty commands are declared, and each names exactly one
    delegate skill, so a selection that includes that skill keeps its command.
    """
    plan = resolve(catalog, SelectionRequest.from_args(modules=["workflow"]), available)
    assert len(plan.commands) >= len(available.commands) - 6, (
        f"a workflow selection kept only {len(plan.commands)} of "
        f"{len(available.commands)} commands; the declarations are too broad"
    )
    assert "implement" in plan.commands, (
        "the workflow module contains implement-phase, so /implement must survive"
    )
