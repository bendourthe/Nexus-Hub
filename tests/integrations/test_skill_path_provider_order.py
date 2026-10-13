"""Installer order derived from the skill read-path facts (DF-6-v4133, v4.13.11).

The installers call the runner once per platform, and a platform is eligible for
the Skill-Index Pointer only when one of its VERIFIED skill read paths already
holds installed Nexus-Hub skills (`skill_read_paths.enumerated_skill_dir`). A
platform that writes none of its own VERIFIED paths depends on another platform
having written one of them first; if every such provider ran later, it would keep
the full index until the next install.

This test replaces the hand-written Codex-before-Copilot pin. It derives the
provider of each VERIFIED path by dry-running every registered integration at
both scopes, then checks both installers' runner order, so a new shared path in
`docs/policy/platform-read-contracts.json` is covered without a new pin.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.lib.integrations import get, list_keys
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest
from scripts.lib.integrations.skill_read_paths import (
    _resolve,
    catalog_skill_names,
    load_facts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPES = ("global", "workspace")
INVOCATION = {
    ("installer.sh", "global"): r'"global" "" "([a-z0-9-]+)"',
    ("installer.sh", "workspace"): r'"workspace" "\$target_path" "([a-z0-9-]+)"',
    ("installer.ps1", "global"): r'-Scope "global" -IntegrationKey "([a-z0-9-]+)"',
    ("installer.ps1", "workspace"): r'-TargetPath \$targetPath -IntegrationKey "([a-z0-9-]+)"',
}


def _ctx(tmp: Path, scope: str) -> InstallContext:
    return InstallContext(repo_root=REPO_ROOT, target_root=tmp, scope=scope, overwrite=False,
                          dry_run=True, manifest=InstallManifest(),
                          template_vars={"PROJECT_NAME": "order-probe"}, explicit_target=True)


def _skill_dirs_written(tmp: Path, scope: str) -> dict[str, set[Path]]:
    """Dry-run each integration; return the skill directories each one writes."""
    names = catalog_skill_names(REPO_ROOT)
    written: dict[str, set[Path]] = {}
    for key in list_keys():
        integration = get(key)
        global_dir = integration.config.get("global_dir") or ""
        if global_dir.startswith("~/"):
            (tmp / global_dir[2:]).mkdir(parents=True, exist_ok=True)
        ctx = _ctx(tmp, scope)
        integration.install(ctx)
        written[key] = {Path(p).resolve().parent for p in ctx.manifest.files_for(key)
                        if Path(p).name in names}
    return written


def dependencies(tmp: Path, scope: str) -> dict[str, set[str]]:
    """{consumer: providers} for platforms that write none of their own VERIFIED paths."""
    written = _skill_dirs_written(tmp, scope)
    deps: dict[str, set[str]] = {}
    for key, by_scope in load_facts(REPO_ROOT).items():
        if key.startswith("_") or not isinstance(by_scope, dict):
            continue
        paths = {
            _resolve(entry["path"], _ctx(tmp, scope)).resolve()
            for entry in by_scope.get(scope, []) or []
            # Host-only facts never make the shared output pointer-eligible.
            if entry.get("status") == "VERIFIED" and "host" not in entry
        }
        if not paths or any(path in written.get(key, set()) for path in paths):
            continue
        providers = {other for other, dirs in written.items() if other != key and paths & dirs}
        if providers:
            deps[key] = providers
    return deps


def order(text: str, installer: str, scope: str) -> list[str]:
    return re.findall(INVOCATION[(installer, scope)], text)


def order_violations(deps: dict[str, set[str]], sequence: list[str]) -> list[str]:
    problems = []
    for consumer, providers in sorted(deps.items()):
        if consumer not in sequence:
            continue  # not installed by this installer at this scope
        ran_before = {p for p in providers if p in sequence
                      and sequence.index(p) < sequence.index(consumer)}
        if not ran_before:
            problems.append(f"{consumer} runs before every provider of its skill path {sorted(providers)}")
    return problems


@pytest.fixture(scope="module")
def derived(tmp_path_factory) -> dict[str, dict[str, set[str]]]:
    return {scope: dependencies(tmp_path_factory.mktemp(scope).resolve(), scope)
            for scope in SCOPES}


def test_derivation_finds_the_known_shared_path_dependency(derived) -> None:
    """Copilot's personal pointer eligibility comes only from Codex's ~/.agents/skills."""
    assert "codex" in derived["global"].get("copilot", set())
    assert derived["workspace"].get("copilot"), "workspace Copilot has no derived provider"


@pytest.mark.parametrize("installer", ["installer.sh", "installer.ps1"])
@pytest.mark.parametrize("scope", SCOPES)
def test_every_dependent_platform_runs_after_a_provider(derived, installer: str, scope: str) -> None:
    text = (REPO_ROOT / "scripts" / installer).read_text(encoding="utf-8-sig")
    sequence = order(text, installer, scope)
    assert len(sequence) == len(set(sequence)) and len(sequence) >= 10, sequence
    assert order_violations(derived[scope], sequence) == []
