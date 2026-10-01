"""v4.13.9 Phase 4 (T421): draft review comments and the validated single-commit scope.

These are text checks because both behaviors are skill text; the functional exercise in
docs/releases/v4/v4.13/development/v4.13.9-review-drafts-exercise/ is the behavioral proof.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILL_DIR = _ROOT / "catalog" / "skills" / "code-review" / "multi-agent-code-review"
_SKILL = _SKILL_DIR / "SKILL.md"
_DRAFTS_REF = _SKILL_DIR / "references" / "draft-review-comments.md"
_REVIEW_CMD = _ROOT / "catalog" / "commands" / "review.md"
_EXERCISE = _ROOT / "docs" / "releases" / "v4" / "v4.13" / "development" / "v4.13.9-review-drafts-exercise" / "draft-review-comments-4f4681e.md"
# Commands or APIs that would write to a pull request, merge request, or issue. Read-only use
# (`gh pr diff`) and the prohibition text itself are not posting instructions.
_POSTING = [
    r"gh\s+(pr|issue)\s+(comment|review|edit|close|merge|create)",
    r"gh\s+api\b",
    r"\bcurl\b",
    r"api\.github\.com",
    r"\bgitlab\b",
    r"create_comment",
    r"submit_review",
    r"git\s+push",
]
_NO_POSTING = "never call any tool that writes to a pull request"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_skill_links_the_draft_format():
    assert "references/draft-review-comments.md" in _text(_SKILL)
    assert _DRAFTS_REF.is_file()


@pytest.mark.parametrize("path", [_SKILL, _DRAFTS_REF, _REVIEW_CMD], ids=["skill", "reference", "review-command"])
def test_no_posting_instruction(path):
    text = _text(path)
    hits = [p for p in _POSTING if re.search(p, text, re.I)]
    assert hits == [], (path.name, hits)


@pytest.mark.parametrize("path", [_SKILL, _REVIEW_CMD], ids=["skill", "review-command"])
def test_no_posting_statement_is_present(path):
    text = _text(path).lower()
    assert _NO_POSTING in text
    assert "mcp" in text and "connector" in text


def test_drafts_carry_confirmed_only_and_list_plausible_separately():
    skill, ref = _text(_SKILL), _text(_DRAFTS_REF)
    assert "Draft `CONFIRMED` findings only" in skill and "`PLAUSIBLE`" in skill
    for field in ("**Path**", "**Line**", "**Severity**", "**Verdict**", "**Body**", "**Evidence**"):
        assert field in ref, field
    for section in ("## Drafted (CONFIRMED)", "## Not drafted (PLAUSIBLE)", "## General notes"):
        assert section in ref, section
    assert "No CONFIRMED findings to draft." in ref
    assert "[[egress-redaction]]" in ref and "never overwritten without the user's confirmation" in ref


def test_commit_mode_names_the_pattern_and_all_three_cases():
    skill = _text(_SKILL)
    assert "**commit**" in skill
    assert "^[0-9a-fA-F]{7,40}$" in skill
    assert "git rev-parse --verify --end-of-options" in skill
    for case in ("Normal commit", "Root commit", "Merge commit"):
        assert case in skill, case
    assert "argument array, never a shell string" in skill


def test_hostile_argument_table_is_documented():
    skill = _text(_SKILL)
    for arg in ("`--output=x`", "`HEAD~100`", "`a..b`", "`abc1234 def`"):
        assert arg in skill, arg
    assert skill.count("rejected before any `git` call") >= 4
    assert "ambiguous" in skill


def test_review_command_stays_thin_and_names_the_commit_argument():
    text = _text(_REVIEW_CMD)
    assert "changes <sha>" in text
    assert len(text.splitlines()) < 120


def test_exercise_draft_has_the_documented_shape():
    text = _text(_EXERCISE)
    assert "**Status**: DRAFT. Nothing here has been posted." in text
    drafted = text.split("## Drafted (CONFIRMED)")[1].split("## Not drafted (PLAUSIBLE)")[0]
    entries = re.split(r"\n### \d+\. ", drafted)[1:]
    assert entries, "at least one drafted entry"
    for entry in entries:
        for field in ("**Path**", "**Line**", "**Severity**", "**Verdict**: CONFIRMED", "**Body**", "**Evidence**", "~~~text"):
            assert field in entry, field
    assert "## Not drafted (PLAUSIBLE)" in text
