"""Tests for scripts/check_american_spelling.py and the rule it backs.

The guard keeps the repository's living files in American English; the
Writing Discipline block carries the same rule to every installed platform.

Run from the repo root:

    python -m pytest tests/validators/test_check_american_spelling.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts import check_american_spelling as guard
from scripts.check_base_template_parity import instruction_section_body, template_roster

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_the_git_grep_prefilter_covers_every_british_form():
    """A form the prefilter misses is never read, so it would pass silently."""
    prefilter = re.compile(guard.PREFILTER_PATTERN, re.IGNORECASE)
    missed = sorted(word for word in guard.SPELLINGS if not prefilter.search(word))
    assert not missed, f"prefilter misses: {missed[:10]}"


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("The colour and behaviour.", "The color and behavior."),
        ("Colour is set. COLOUR too.", "Color is set. COLOR too."),
        ("We organise the catalogue at the centre.", "We organize the catalog at the center."),
        ("A labelled, normalised judgement.", "A labeled, normalized judgment."),
    ],
)
def test_british_forms_are_rewritten_with_case_preserved(line: str, expected: str):
    fixed, found = guard.fix_line(line)
    assert fixed == expected
    assert found


@pytest.mark.parametrize(
    "line",
    [
        "Use `colour_map` from the vendor API.",
        "See https://example.org/colour/centre for the source.",
        '<div aria-labelledby="title">',
        "The legend-colour-collision finding and the ship_colour field.",
        "Keep this: colour  # spelling: allow",
    ],
)
def test_literals_keep_their_published_spelling(line: str):
    assert guard.fix_line(line) == (line, [])


@pytest.mark.parametrize(
    "line",
    [
        "Raise the exercise; otherwise the enterprise promise breaks.",
        "Two analyses of the analysis.",
        "The run was cancelled and the job cancelled() check passed.",
        "A realistic specialist with characteristic precision.",
    ],
)
def test_american_words_and_accepted_variants_are_not_flagged(line: str):
    assert guard.fix_line(line) == (line, [])


@pytest.mark.parametrize(
    ("path", "frozen"),
    [
        ("docs/archives/v4/v4.13/plans/x.md", True),
        ("docs/releases/v4/v4.14/development/v4.14.0-phase-7-receipts/a.txt", True),
        ("docs/releases/v4/v4.14/development/fix.patch", True),
        ("scripts/check_american_spelling.py", True),
        ("docs/releases/v4/v4.14/plans/v4.14.2-plan.md", True),
        ("docs/releases/v4/v4.14/known-gaps.md", True),
        ("catalog/skills/workflow/x/SKILL.md", False),
        ("docs/decisions/implemented/policy/x.md", False),
    ],
)
def test_history_and_evidence_are_frozen(path: str, frozen: bool):
    assert guard.is_frozen(path) is frozen


def test_only_the_unreleased_changelog_section_is_checked():
    lines = ["# Changelog\n", "## [Unreleased]\n", "- colour\n", "## [1.0.0]\n", "- colour\n"]
    assert list(guard.checked_range("CHANGELOG.md", lines)) == [0, 1, 2]
    assert list(guard.checked_range("README.md", lines)) == [0, 1, 2, 3, 4]


_SUBSTANTIVE, _ = template_roster(_REPO_ROOT)


@pytest.mark.parametrize("path", _SUBSTANTIVE, ids=lambda p: p.name)
def test_every_installed_platform_is_told_to_write_american_english(path: Path):
    """The guard covers this repo; this sentence covers every user's agent."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    body = "\n".join(instruction_section_body(text, "## Writing Discipline"))
    assert "Spelling is American English" in body, path.name
