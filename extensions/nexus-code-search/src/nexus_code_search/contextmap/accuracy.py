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

from nexus_code_search.contextmap.components import extract_components
from nexus_code_search.contextmap.env import audit_env_vars
from nexus_code_search.contextmap.events import detect_events
from nexus_code_search.contextmap.middleware import detect_middleware
from nexus_code_search.contextmap.model import RouteInfo
from nexus_code_search.contextmap.routes import extract_routes
from nexus_code_search.contextmap.schema import extract_schema

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


def relation_key(model_name: str, rel) -> str:
    """Canonical `Model.rel->Target` key for comparing a relation to truth."""
    return f"{model_name}.{rel.name}->{rel.target}"


def event_key(event) -> str:
    """Canonical `kind:name` key for comparing an event to ground truth."""
    return f"{event.kind}:{event.name}"


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
    """Run the relevant extractors over the graph and score against ``truth``.

    Only sections declared in ``truth`` are scored, so a fixture opts into the
    sections it exercises. Keys: routes ("METHOD path"), env (names), middleware
    (names), models (names), relations ("Model.rel->Target"), components (names),
    events ("kind:name").
    """
    code_files = [
        (path, language)
        for path, language in conn.execute("SELECT path, language FROM files")
    ]
    detected: dict[str, set[str]] = {}
    if "routes" in truth:
        detected["routes"] = {route_key(r) for r in extract_routes(conn, root)}
    if "env" in truth:
        detected["env"] = {e.name for e in audit_env_vars(root, code_files)}
    if "middleware" in truth:
        detected["middleware"] = {m.name for m in detect_middleware(root, code_files)}
    if "models" in truth or "relations" in truth:
        models = extract_schema(conn, root)
        if "models" in truth:
            detected["models"] = {m.name for m in models}
        if "relations" in truth:
            detected["relations"] = {
                relation_key(m.name, r) for m in models for r in m.relations
            }
    if "components" in truth:
        detected["components"] = {c.name for c in extract_components(root, code_files)}
    if "events" in truth:
        detected["events"] = {event_key(e) for e in detect_events(root, code_files)}

    return {
        section: score_section(section, found, set(truth.get(section, [])))
        for section, found in detected.items()
    }
