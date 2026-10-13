"""Scorer: content_intent record, standalone phrasing, runtime accents (v4.13 AR-19).

Covers the mechanically decidable half of Gate A (the record exists, names every
field, and a `standalone` page's visible text carries no draft-reference
phrase) and the cheap partial guard for palette values a script assigns from a
`data-accent` attribute, which `check_contrast` cannot see.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCORER = (
    Path(__file__).resolve().parents[2]
    / "catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py"
)


@pytest.fixture(scope="module")
def scorer():
    spec = importlib.util.spec_from_file_location("visual_qa_score_ar19", _SCORER)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[spec.name] = module  # type: ignore[union-attr]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_CLEAN_INTENT = """
content_intent:
  source_relationship: standalone
  audience_familiarity: low
  decision_to_enable: choose commercial, agentic, or hybrid
  scope_class: decision-grade-pilot
  assumptions:
    - statement: the corpus is available
      status: accepted
  exclusions:
    - critique of the source draft
"""


def _page(record: str | None, body: str = "<p>A pilot plan for the team.</p>", accent: str = "") -> str:
    comment = f"<!--\n  DESIGN RECORD\n{record or ''}\n-->" if record is not None else ""
    section = f'<section data-accent="{accent}">' if accent else "<section>"
    return (
        "<!doctype html><html><head>" + comment
        + "<style>:root { --bg: #ffffff; --ink: #111111; }</style></head><body>"
        + section + body + "</section></body></html>"
    )


def _by_criterion(scorer, html: str) -> dict[str, dict]:
    return {f["criterion"]: f for f in scorer.score_html(html)["findings"]}


def test_complete_standalone_record_passes(scorer) -> None:
    found = _by_criterion(scorer, _page(_CLEAN_INTENT))

    assert found["content-intent"]["status"] == "pass"
    assert found["standalone-phrasing"]["status"] == "pass"


def test_design_record_without_content_intent_fails(scorer) -> None:
    found = _by_criterion(scorer, _page("  nav: scroll"))

    assert found["content-intent"]["status"] == "fail"
    assert "no content_intent block" in found["content-intent"]["evidence"]


@pytest.mark.parametrize("field", ["decision_to_enable", "scope_class", "exclusions"])
def test_missing_content_intent_field_fails(scorer, field: str) -> None:
    lines = _CLEAN_INTENT.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().startswith(field + ":"))
    end = start + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    record = "\n".join(lines[:start] + lines[end:])

    found = _by_criterion(scorer, _page(record))

    assert found["content-intent"]["status"] == "fail"
    assert field in found["content-intent"]["evidence"]


def test_standalone_page_naming_its_draft_fails(scorer) -> None:
    body = "<h2>What was wrong with the prior draft</h2><p>The original preserved it.</p>"
    found = _by_criterion(scorer, _page(_CLEAN_INTENT, body))

    assert found["standalone-phrasing"]["status"] == "fail"
    for phrase in ("what was wrong", "the prior draft", "original preserved"):
        assert phrase in found["standalone-phrasing"]["evidence"]


def test_phrase_only_in_hidden_markup_or_other_relationship_passes(scorer) -> None:
    hidden = "<script>var note = 'the original';</script><p>Plan.</p>"
    comparative = _CLEAN_INTENT.replace("standalone", "comparative")

    assert _by_criterion(scorer, _page(_CLEAN_INTENT, hidden))["standalone-phrasing"]["status"] == "pass"
    assert (
        _by_criterion(scorer, _page(comparative, "<p>The original said so.</p>"))[
            "standalone-phrasing"
        ]["status"]
        == "n/a"
    )


def test_page_without_design_record_is_not_graded(scorer) -> None:
    found = _by_criterion(scorer, _page(None))

    assert found["content-intent"]["status"] == "n/a"


def test_sub_aa_runtime_accent_is_flagged(scorer) -> None:
    found = _by_criterion(scorer, _page(None, accent="#9fe0d8"))

    assert found["contrast-runtime-accent"]["status"] == "fail"
    assert "#9fe0d8 on --bg" in found["contrast-runtime-accent"]["evidence"]
    # The declared tokens alone still pass: this is the blind spot the guard covers.
    assert found["contrast"]["status"] == "pass"


def test_aa_runtime_accent_passes(scorer) -> None:
    found = _by_criterion(scorer, _page(None, accent="#0b5d55"))

    assert found["contrast-runtime-accent"]["status"] == "pass"
