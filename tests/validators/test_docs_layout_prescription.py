"""Reject catalog prescriptions of the retired documentation layout."""

from __future__ import annotations

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[2]
OLD_SHAPE = re.compile(r"docs/v<MAJOR>|docs/archive/")
BT = chr(96)

ALLOWED_LEGACY_LINES = {
    (
        "catalog/hooks/session-summary.ps1",
        "    memory-persistence pattern (legacy migration source: docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md",
    ),
    (
        "catalog/hooks/session-summary.sh",
        "# memory-persistence pattern (legacy migration source: docs/archive/v2/v2.3/plans/adoption-ecc-cybersec-skills.md",
    ),
    (
        "catalog/hooks/tests/test_installer_smoke.py",
        "    # into the legacy migration source docs/archive/v0/ during v2.1.0 post-Phase-10 maintenance",
    ),
    (
        "catalog/hooks/tests/test_old_version_docs_guard.py",
        '        "docs/archive/v0/v0.8/history.md",  # Legacy detection fixture.',
    ),
    (
        "catalog/hooks/tests/test_old_version_docs_guard.py",
        '        "docs/archive/v0.8.1/history.md",  # Legacy detection fixture.',
    ),
    (
        "catalog/hooks/tests/test_old_version_docs_guard.py",
        '        "docs/archive/versions/v0/v0.8.1/history.md",  # Legacy detection fixture.',
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md",
        f"2. **Legacy exists**: if a legacy v-bucket {BT}docs/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}, singular archive {BT}docs/archive/{BT}, flat {BT}docs/<vSEMVER>/{BT}, or old three-level {BT}docs/versions/v<MAJOR>/<vSEMVER>/{BT} directory exists and is non-empty (and the canonical does not exist), use it in place and surface: {BT}Detected legacy docs layout at <path>. Continuing in place; run /update refactor to migrate to docs/releases/ and docs/archives/.{BT}",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md",
        f"Legacy archive sources {BT}docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}, {BT}docs/archive/<vSEMVER>/{BT}, and {BT}docs/archive/versions/v<MAJOR>/<vSEMVER>/{BT} are honored in place. An approved {BT}/refactor-docs --canonicalize-layout{BT} pass migrates them to {BT}docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}. Mixed layouts are reported from the helper's {BT}layout{BT} field rather than guessed.",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md",
        f"5. **Canonicalize layout** (only when {BT}--canonicalize-layout{BT} was set): run {BT}audit-docs.py canonicalize-layout --root ./docs{BT} after approval to migrate the legacy v-bucket {BT}docs/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}, flat {BT}docs/<vSEMVER>/{BT}, and {BT}docs/versions/v<MAJOR>/<vSEMVER>/{BT} sources into {BT}docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}. Migrate legacy singular {BT}docs/archive/{BT} sources to {BT}docs/archives/{BT} with the same minor bucketing. Refuse destination collisions, queue every rename for Step 9, and never merge silently.",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md",
        f"Version 2.0.0 renames the canonical active container from the legacy {BT}docs/v<MAJOR>/v<MAJOR>.<MINOR>/{BT} shape to {BT}docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/{BT} and the legacy singular {BT}docs/archive/{BT} container to {BT}docs/archives/{BT}. Run {BT}/refactor-docs --canonicalize-layout{BT} once, approve the proposed map, and let Step 9 repair references. The Phase 1 rename-map algorithm plus pre/post unresolved-link set diff is the proof: zero {BT}newly_broken{BT} is required before the migration completes.",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        "# Legacy v-bucket migration source: docs/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/...",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        f"    - {BT}{BT}v-bucket{BT}{BT}: legacy {BT}{BT}docs/v<MAJOR>/v<MAJOR>.<MINOR>/{BT}{BT}.",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        '        help="Move legacy active version directories into docs/releases/ and the legacy docs/archive/ container to docs/archives/.",',
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        "    migration-source container is the singular ``docs/archive/``. Bucketing below",
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        '    inv.add_argument("--include-archive", action="store_true", help="Include docs/archives/ and legacy docs/archive/ in the scan.")',
    ),
    (
        "catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py",
        '    ref.add_argument("--include-archive", action="store_true", help="Include docs/archives/ and legacy docs/archive/ in the scan targets.")',
    ),
    (
        "catalog/skills/workflow/skill-eval-loop/references/trigger-testing.md",
        f"These techniques are reverse-engineered (form, not verbatim) from the superpowers trigger harness ({BT}tests/skill-triggering/run-test.sh{BT}, {BT}tests/explicit-skill-requests/run-test.sh{BT}, and {BT}run-haiku-test.sh{BT}); see the legacy migration-source path {BT}docs/archive/v2/v2.3/comparison-superpowers.md{BT} Section 8 for provenance. They reuse the same CLI dispatcher as the rest of the loop: no new outbound calls, no new dependency, no new credential.",
    ),
    (
        "catalog/style-guides/markdownlint-cli2.jsonc",
        '    "docs/archive/**", // Legacy migration source until /update refactor canonicalizes the repository.',
    ),
    (
        "templates/ai-instructions/base-antigravity-cli.md",
        f"This file is a thin alias for {BT}base-antigravity-20.md{BT}. The Antigravity CLI and the Antigravity 2.0 desktop IDE share a backend and on-disk conventions per the 2026-05-21 Google Developers Blog announcement (legacy migration-source path {BT}docs/archive/v2/v2.2/antigravity-cli-probe.md{BT}), so the {BT}Antigravity20Integration{BT} in {BT}scripts/lib/integrations/antigravity.py{BT} covers both surfaces with a single class.",
    ),
}


def _matched_lines(root: Path) -> set[tuple[str, str]]:
    matches: set[tuple[str, str]] = set()
    for base_name in ("catalog", "templates"):
        base = root / base_name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line in lines:
                if OLD_SHAPE.search(line):
                    matches.add((path.relative_to(root).as_posix(), line))
    return matches


def _assert_exact_legacy_allowlist(root: Path, allowlist: set[tuple[str, str]]) -> None:
    matches = _matched_lines(root)
    unexpected = sorted(matches - allowlist)
    missing = sorted(allowlist - matches)
    details = []
    if unexpected:
        details.append(f"unexpected old-shape prescriptions or unclassified legacy lines: {unexpected}")
    if missing:
        details.append(f"stale exact-content allowlist entries: {missing}")
    assert not details, "\n".join(details)


def test_catalog_has_only_exactly_allowlisted_legacy_layout_lines() -> None:
    _assert_exact_legacy_allowlist(ROOT, ALLOWED_LEGACY_LINES)


def test_deliberate_old_shape_prescription_fails_the_guard(tmp_path: Path) -> None:
    artifact = tmp_path / "catalog/commands/example.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("Create each release under docs/v<MAJOR>/v<MAJOR>.<MINOR>/.\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="unexpected old-shape prescriptions"):
        _assert_exact_legacy_allowlist(tmp_path, set())
