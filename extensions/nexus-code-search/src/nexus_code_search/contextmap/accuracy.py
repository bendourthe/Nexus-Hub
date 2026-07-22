"""Extraction-accuracy harness for the context-map extractors.

Scores the route / env / middleware extractors against hand-counted ground
truth, reporting per-section recall and a false-positive count. The discipline
mirrors the extraction-accuracy checks the CodeSight comparison observed: a hard
zero-false-positive gate (a spurious detection is a hard failure) and a recall
figure per section (below the threshold is a soft warning to triage).

Reusable across phases: Phase 3 extends the same harness with schema / component
/ event sections. Pure scoring plus a thin evaluate() over a built graph; no I/O
beyond reading the fixture source the extractors already read.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from nexus_code_search.contextmap.env import audit_env_vars
from nexus_code_search.contextmap.middleware import detect_middleware
from nexus_code_search.contextmap.model import RouteInfo
from nexus_code_search.contextmap.routes import extract_routes

# Per-section recall below this is a soft warning to triage, not a hard failure.
RECALL_THRESHOLD = 0.8


@dataclass(frozen=True)
class SectionScore:
    """Recall / false-positive score for one extraction section."""

    section: str
    ground_truth: int
    detected: int
    true_positives: int
    false_positives: tuple[str, ...]
    missed: tuple[str, ...]

    @property
    def recall(self) -> float:
        if self.ground_truth == 0:
            return 1.0
        return self.true_positives / self.ground_truth

    @property
    def fp_count(self) -> int:
        return len(self.false_positives)


def route_key(route: RouteInfo) -> str:
    """Canonical `METHOD path` key for comparing a route to ground truth."""
    return f"{route.method} {route.path}"


def score_section(section: str, detected: set[str], truth: set[str]) -> SectionScore:
    """Compare a detected set to ground truth for one section."""
    tp = detected & truth
    return SectionScore(
        section=section,
        ground_truth=len(truth),
        detected=len(detected),
        true_positives=len(tp),
        false_positives=tuple(sorted(detected - truth)),
        missed=tuple(sorted(truth - detected)),
    )


def evaluate(
    conn: sqlite3.Connection, root: Path, truth: dict
) -> dict[str, SectionScore]:
    """Run every section extractor over the graph and score against ``truth``.

    ``truth`` maps "routes" / "env" / "middleware" to a list of expected keys
    (routes as "METHOD path", env as variable names, middleware as names).
    """
    code_files = [
        (path, language)
        for path, language in conn.execute("SELECT path, language FROM files")
    ]
    detected_routes = {route_key(r) for r in extract_routes(conn, root)}
    detected_env = {e.name for e in audit_env_vars(root, code_files)}
    detected_mw = {m.name for m in detect_middleware(root, code_files)}

    return {
        "routes": score_section(
            "routes", detected_routes, set(truth.get("routes", []))
        ),
        "env": score_section("env", detected_env, set(truth.get("env", []))),
        "middleware": score_section(
            "middleware", detected_mw, set(truth.get("middleware", []))
        ),
    }
