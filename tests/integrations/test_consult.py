"""Tests for v2.3.0 / Phase 4 / T011 consult advisor."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import nexus_hub_consult  # noqa: E402


def test_tokenize_drops_stopwords_and_short_tokens() -> None:
    tokens = nexus_hub_consult.tokenize(
        "I want to use TDD for my new Python project"
    )
    # "i", "want", "to", "use", "for", "my" should all be dropped.
    assert "tdd" in tokens
    assert "python" in tokens
    assert "want" not in tokens
    assert "to" not in tokens


def test_tokenize_handles_empty_input() -> None:
    assert nexus_hub_consult.tokenize("") == []
    assert nexus_hub_consult.tokenize("   ") == []


def test_load_candidates_returns_all_kinds() -> None:
    candidates = nexus_hub_consult.load_candidates(
        {"skill", "bundle", "profile", "module"}
    )
    kinds = {c.kind for c in candidates}
    # Profiles and modules were introduced in this same phase, so they MUST
    # be in the catalog now -- not just optionally present.
    assert kinds == {"skill", "bundle", "profile", "module"}


def test_load_candidates_respects_kind_filter() -> None:
    profiles = nexus_hub_consult.load_candidates({"profile"})
    assert {c.kind for c in profiles} == {"profile"}
    # The three named profiles (minimal / core / full) must all be present.
    profile_ids = {c.id for c in profiles}
    assert {"minimal", "core", "full"} <= profile_ids


def test_score_candidate_returns_zero_when_no_overlap() -> None:
    candidate = nexus_hub_consult.Candidate(
        kind="skill",
        id="unrelated-skill",
        name="unrelated",
        description="something completely different",
        tags=[],
    )
    scored = nexus_hub_consult.score_candidate(
        ["dashboard", "metrics"], candidate
    )
    assert scored.score == 0.0
    assert scored.matched_tokens == []


def test_score_candidate_boosts_id_match() -> None:
    candidate = nexus_hub_consult.Candidate(
        kind="skill",
        id="testing",
        name="Testing",
        description="Generic description.",
        tags=[],
    )
    scored = nexus_hub_consult.score_candidate(["testing"], candidate)
    # The baseline gives +1 for the token match plus +2 for the id-exact
    # match.
    assert scored.score >= 3.0
    assert "testing" in scored.matched_tokens


def test_score_candidate_boosts_tag_match() -> None:
    candidate = nexus_hub_consult.Candidate(
        kind="module",
        id="testing-module",
        name="Testing",
        description="...",
        tags=["testing", "qa"],
    )
    scored = nexus_hub_consult.score_candidate(["testing"], candidate)
    assert scored.score >= 2.0


def test_consult_returns_sorted_results_with_install_hint() -> None:
    results = nexus_hub_consult.consult(
        "I need testing skills for my project", top=5
    )
    assert results
    # Sorted descending by score.
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    for r in results:
        assert r.candidate.install_hint  # every candidate must offer a hint


def test_consult_empty_need_returns_empty_list() -> None:
    assert nexus_hub_consult.consult("") == []


def test_consult_respects_top_argument() -> None:
    results = nexus_hub_consult.consult("api design rest", top=2)
    assert len(results) <= 2


def test_main_exits_zero_on_match(capsys: pytest.CaptureFixture[str]) -> None:
    code = nexus_hub_consult.main(["testing", "--top", "3"])
    captured = capsys.readouterr().out
    assert code == 0
    assert "install:" in captured


def test_main_exits_one_on_no_match(capsys: pytest.CaptureFixture[str]) -> None:
    code = nexus_hub_consult.main(["zzzunmatchablequeryxyzzy"])
    assert code == 1


def test_main_json_emits_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    code = nexus_hub_consult.main(["--json", "testing"])
    captured = capsys.readouterr().out
    assert code == 0
    parsed = json.loads(captured)
    assert isinstance(parsed, list)
    assert parsed and "score" in parsed[0]
