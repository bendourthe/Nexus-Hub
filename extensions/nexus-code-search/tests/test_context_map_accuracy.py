"""Extraction-accuracy tests (Phase 2 sub-task 2.3).

Runs the route / env / middleware extractors against per-framework fixtures with
hand-counted ground truth. Enforces a HARD zero-false-positive gate and a recall
threshold per section (routes, env, middleware).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.contextmap.accuracy import (
    RECALL_THRESHOLD,
    SectionScore,
    evaluate,
    route_key,
    score_section,
)
from nexus_code_search.contextmap.model import RouteInfo
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator

FIXTURES = Path(__file__).parent / "fixtures" / "contextmap"
FIXTURE_APPS = [
    "fastapi_app",
    "express_app",
    "django_app",
    "schema_app",
    "frontend_app",
]


def _evaluate_fixture(app: str, tmp_path: Path) -> dict[str, SectionScore]:
    fixture_dir = FIXTURES / app
    truth = json.loads((fixture_dir / "truth.json").read_text(encoding="utf-8"))
    cfg = CodeSearchConfig(hub_root=None)
    index_dir = tmp_path / "idx"
    with ExtractionOrchestrator(fixture_dir, cfg, index_dir) as orch:
        orch.run()
    conn = open_database(index_dir)
    try:
        return evaluate(conn, fixture_dir, truth)
    finally:
        conn.close()


@pytest.mark.parametrize("app", FIXTURE_APPS)
def test_zero_false_positives(app: str, tmp_path: Path) -> None:
    scores = _evaluate_fixture(app, tmp_path)
    for section, score in scores.items():
        assert score.fp_count == 0, (
            f"{app}/{section} false positives: {score.false_positives}"
        )


@pytest.mark.parametrize("app", FIXTURE_APPS)
def test_recall_meets_threshold(app: str, tmp_path: Path) -> None:
    scores = _evaluate_fixture(app, tmp_path)
    for section, score in scores.items():
        assert score.recall >= RECALL_THRESHOLD, (
            f"{app}/{section} recall {score.recall:.2f} below "
            f"{RECALL_THRESHOLD} (missed: {score.missed})"
        )


@pytest.mark.parametrize("app", FIXTURE_APPS)
def test_each_section_detects_something(app: str, tmp_path: Path) -> None:
    # The fixtures are designed so every section has ground truth; a section that
    # detects nothing would signal an extractor regression.
    scores = _evaluate_fixture(app, tmp_path)
    for section, score in scores.items():
        assert score.detected >= 1, f"{app}/{section} detected nothing"


def test_relation_resolution(tmp_path: Path) -> None:
    # The plan calls ORM relation resolution the hardest extraction; assert it
    # explicitly across Django, SQLAlchemy, and Prisma via the schema fixture.
    scores = _evaluate_fixture("schema_app", tmp_path)
    relations = scores["relations"]
    assert relations.fp_count == 0, relations.false_positives
    assert relations.missed == (), f"unresolved relations: {relations.missed}"
    assert relations.recall == 1.0


# --- Unit tests for the scoring math ----------------------------------------


def test_score_section_perfect() -> None:
    score = score_section("routes", {"GET /a", "POST /b"}, {"GET /a", "POST /b"})
    assert score.recall == 1.0
    assert score.fp_count == 0
    assert score.missed == ()


def test_score_section_false_positive_and_miss() -> None:
    score = score_section("env", {"A", "B"}, {"A", "C"})
    assert score.false_positives == ("B",)
    assert score.missed == ("C",)
    assert score.recall == 0.5


def test_score_section_empty_truth_is_full_recall() -> None:
    score = score_section("middleware", set(), set())
    assert score.recall == 1.0
    assert score.fp_count == 0


def test_route_key_format() -> None:
    route = RouteInfo(
        framework="fastapi",
        method="GET",
        path="/x",
        params=(),
        handler="",
        handler_file="",
        behavior_tags=(),
        source_file="a.py",
    )
    assert route_key(route) == "GET /x"
