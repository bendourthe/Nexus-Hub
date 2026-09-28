"""v4.7.0 amendment Phase 1 (T040): the Astra routing decision is recorded where the plan said it would be.

- The snapshot's newest note names GPT-6 Astra and its OpenAI sources cite both pages.
- The main plan's sub-task 2.2 and 5.3 prompts cite the GPT-6 Astra guide as a second vendor source.
- The decision note exists and carries both quoted pages.
"""

from __future__ import annotations

import json
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
MAIN_PLAN = (
    REPO
    / "docs"
    / "archives"
    / "v4"
    / "v4.7"
    / "plans"
    / "v4.7.0-adoption-model-behavior-and-distribution-integrity.md"
)
DECISION = (
    REPO
    / "docs"
    / "archives"
    / "v4"
    / "v4.7"
    / "development"
    / "astra-routing-decision.md"
)
CATALOG_URL = "https://developers.openai.com/api/docs/models"
GUIDE_URL = (
    "https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra"
)


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_newest_note_and_sources_record_the_astra_decision():
    snapshot = _snapshot()
    assert "GPT-6 Astra" in snapshot["notes"][-1]
    assert CATALOG_URL in snapshot["sources"]["OpenAI"]
    assert GUIDE_URL in snapshot["sources"]["OpenAI"]


def test_main_plan_prompts_cite_the_astra_guide_twice():
    text = MAIN_PLAN.read_text(encoding="utf-8")
    body_22 = text[text.index("#### 2.2") : text.index("#### 2.3")]
    body_53 = text[text.index("#### 5.3") : text.index("#### 5.4")]
    assert GUIDE_URL in body_22 and "can you" in body_22
    assert GUIDE_URL in body_53 and "Do not write tests for reversible" in body_53


def test_decision_note_exists_with_both_quoted_pages():
    text = DECISION.read_text(encoding="utf-8")
    assert CATALOG_URL in text and GUIDE_URL in text
    assert "Mapped at `frontier`" in text
