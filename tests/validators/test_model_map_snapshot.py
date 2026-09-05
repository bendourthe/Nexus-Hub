"""v4.7.0 Phase 1: the bundled model-map snapshot is valid, current, and names no legacy frontier id.

Three durable contracts, none pinned to a specific model id beyond the one legacy
name the phase retired:

1. The snapshot validates through the skill's own ``model-map.py validate`` and
   carries a ``verified_as_of`` no older than the v4.7.0 Phase 1 refresh.
2. No live routing surface (the snapshot's tier cells, the platform-defaults
   source, the templates, and the skill bodies) names ``claude-fable-5`` as a
   tier value. Historical plans under ``docs/releases/`` keep their maps as
   written and are deliberately outside this check.
3. ``sync_platform_defaults.py --check`` exits 0, so the corrected Claude lever
   statement left every derived artifact in sync.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = (
    REPO
    / "catalog"
    / "skills"
    / "ai-development"
    / "model-routing"
    / "references"
    / "last-known-model-map.json"
)
HELPER = (
    REPO
    / "catalog"
    / "skills"
    / "ai-development"
    / "model-routing"
    / "scripts"
    / "model-map.py"
)
REFRESH_FLOOR = "2026-09-05"
LEGACY_FRONTIER = "claude-fable-5"
LIVE_SURFACES = [
    REPO / "configs" / "platform-defaults.json",
    REPO / "templates" / "ai-instructions",
    REPO / "catalog" / "skills" / "ai-development" / "model-routing" / "SKILL.md",
]


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_snapshot_validates_through_the_skill_helper():
    result = subprocess.run(
        [sys.executable, str(HELPER), "validate", str(SNAPSHOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report["valid"] is True
    assert report["tiers"] == 4 and report["providers"] == 4


def test_snapshot_is_no_older_than_the_phase_refresh():
    assert _snapshot()["verified_as_of"] >= REFRESH_FLOOR


def test_no_tier_cell_names_the_legacy_frontier_id():
    for tier, cells in _snapshot()["tiers"].items():
        for provider, model in cells.items():
            assert model != LEGACY_FRONTIER, (
                f"{tier}/{provider} still names {LEGACY_FRONTIER}"
            )


def test_no_live_surface_names_the_legacy_frontier_id_as_a_value():
    pattern = re.compile(rf"(?<![\w-]){re.escape(LEGACY_FRONTIER)}(?![\w-])")
    offenders: list[str] = []
    for surface in LIVE_SURFACES:
        files = (
            [surface]
            if surface.is_file()
            else sorted(surface.rglob("*.md")) + sorted(surface.rglob("*.json"))
        )
        for f in files:
            if pattern.search(f.read_text(encoding="utf-8")):
                offenders.append(str(f.relative_to(REPO)))
    assert offenders == [], offenders


def test_platform_defaults_derived_artifacts_are_in_sync():
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "sync_platform_defaults.py"),
            "--check",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
