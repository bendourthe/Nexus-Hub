"""Contracts for the OWASP Agentic Top 10 mapping (v4.8.0, seventh framework).

Two invariants here are worth more than the rest. The Navigator layer must stay
free of `ASI` identifiers, because the ATT&CK Navigator resolves identifiers
against the ATT&CK catalog and would either drop an ASI entry or render it
unresolvable. And a tagged skill must explain each of its identifiers, because
the failure mode this mapping carries is not a crash: it is a fabricated or
mistranscribed identifier sitting in a compliance-facing matrix, reading as
verified coverage.

Field shape and closed-set membership live in `test_framework_field_shape.py`,
which already owns the validator harness.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_SKILLS = REPO_ROOT / "catalog" / "skills"
COVERAGE_MD = REPO_ROOT / "docs" / "framework-coverage.md"
NAVIGATOR_LAYER = REPO_ROOT / "docs" / "attack-navigator-layer.json"
MAPPING_SKILL = CATALOG_SKILLS / "security" / "security-framework-mapping"
DECISION_RECORD = (
    REPO_ROOT
    / "docs"
    / "decisions"
    / "implemented"
    / "policy"
    / "2026-09-07-owasp-agentic-top-10-as-seventh-framework-field.md"
)

# Verified 2026-09-07 against the fetched OWASP sources. The ampersands in
# ASI03 and ASI06 are part of the official titles; an earlier transcription
# wrote "and" and was corrected against the source.
OFFICIAL_TITLES = {
    "ASI01": "Agent Goal Hijack",
    "ASI02": "Tool Misuse",
    "ASI03": "Identity & Privilege Abuse",
    "ASI04": "Agentic Supply Chain Vulnerabilities",
    "ASI05": "Unexpected Code Execution",
    "ASI06": "Memory & Context Poisoning",
    "ASI07": "Insecure Inter-Agent Communication",
    "ASI08": "Cascading Failures",
    "ASI09": "Human-Agent Trust Exploitation",
    "ASI10": "Rogue Agents",
}

ASI_PATTERN = re.compile(r"\bASI\d{2}\b")


def _tagged_skills() -> dict[Path, list[str]]:
    """Every SKILL.md carrying owasp_agentic, mapped to its identifiers."""
    found: dict[Path, list[str]] = {}
    for skill in sorted(CATALOG_SKILLS.rglob("SKILL.md")):
        text = skill.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end == -1:
            continue
        block = text[:end]
        match = re.search(r"^owasp_agentic:\s*(.*)$", block, flags=re.MULTILINE)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.startswith("[") and raw.endswith("]"):
            ids = [v.strip() for v in raw[1:-1].split(",") if v.strip()]
        else:
            ids = re.findall(r"^\s*-\s*(\S+)", block[match.end():], flags=re.MULTILINE)
        found[skill] = ids
    return found


TAGGED = _tagged_skills()


def test_the_catalog_actually_carries_tags() -> None:
    """Guards the rest of this file: a parser regression that found zero tagged
    skills would make every data-driven test below vacuously pass."""
    assert len(TAGGED) >= 15, f"expected at least 15 tagged skills, found {len(TAGGED)}"


def test_navigator_layer_contains_no_owasp_identifiers() -> None:
    """The load-bearing isolation invariant."""
    raw = NAVIGATOR_LAYER.read_text(encoding="utf-8")
    assert not ASI_PATTERN.search(raw), (
        "an ASI identifier reached docs/attack-navigator-layer.json; the Navigator "
        "resolves identifiers against the ATT&CK catalog and cannot render one"
    )
    layer = json.loads(raw)
    for technique in layer.get("techniques", []):
        assert not technique["techniqueID"].startswith("ASI")


def test_coverage_matrix_has_a_non_empty_owasp_column() -> None:
    text = COVERAGE_MD.read_text(encoding="utf-8")
    assert "## OWASP Agentic" in text, "the matrix has no OWASP Agentic section"
    section = text.split("## OWASP Agentic", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| `(ASI\d{2})` \| (.+?) \|$", section, flags=re.MULTILINE)
    assert rows, "the OWASP Agentic section lists no control rows"
    for ident, skills in rows:
        assert ident in OFFICIAL_TITLES, f"matrix lists unknown identifier {ident}"
        assert skills.strip(), f"{ident} row names no skill"


@pytest.mark.parametrize("identifier", sorted(OFFICIAL_TITLES))
def test_every_identifier_is_covered_by_at_least_one_skill(identifier: str) -> None:
    """Not required by the framework, but a gap here is worth seeing: an
    uncovered identifier is a risk the catalog teaches nothing about."""
    covered = {i for ids in TAGGED.values() for i in ids}
    assert identifier in covered, (
        f"{identifier} ({OFFICIAL_TITLES[identifier]}) is not covered by any skill"
    )


@pytest.mark.parametrize(
    "skill", sorted(TAGGED, key=str), ids=lambda p: p.parent.name
)
def test_tagged_skill_explains_each_identifier_in_standards(skill: Path) -> None:
    standards = skill.parent / "references" / "standards.md"
    assert standards.is_file(), (
        f"{skill.parent.name} declares owasp_agentic but ships no "
        "references/standards.md to explain it"
    )
    text = standards.read_text(encoding="utf-8")
    for identifier in TAGGED[skill]:
        assert identifier in text, (
            f"{skill.parent.name} is tagged {identifier} but standards.md never "
            "explains it; a tag with no stated rationale is a mistranscription "
            "presented as coverage"
        )


@pytest.mark.parametrize(
    "skill", sorted(TAGGED, key=str), ids=lambda p: p.parent.name
)
def test_tagged_skill_references_its_standards_file(skill: Path) -> None:
    """AGENTS.md orphan rule: a bundled file nothing links is never loaded."""
    assert "references/standards.md" in skill.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "skill", sorted(TAGGED, key=str), ids=lambda p: p.parent.name
)
def test_tagged_identifiers_are_in_the_closed_set_and_unique(skill: Path) -> None:
    ids = TAGGED[skill]
    assert ids, f"{skill.parent.name} has an empty owasp_agentic list"
    for identifier in ids:
        assert identifier in OFFICIAL_TITLES, (
            f"{skill.parent.name} declares unknown identifier {identifier}"
        )
    assert len(ids) == len(set(ids)), f"{skill.parent.name} repeats an identifier"


def test_mapping_skill_documents_seven_frameworks() -> None:
    body = (MAPPING_SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "## The Seven Frameworks" in body
    assert "seven public taxonomies" in body
    assert "owasp_agentic" in body
    assert "## The Six Frameworks" not in body


def test_mapping_skill_standards_lists_all_ten_official_titles() -> None:
    """The one place the full set is recorded, so a retitled entry is caught here."""
    text = (MAPPING_SKILL / "references" / "standards.md").read_text(encoding="utf-8")
    for identifier, title in OFFICIAL_TITLES.items():
        assert identifier in text, f"{identifier} missing from the mapping standards"
        assert title in text, (
            f"the official title for {identifier} ({title!r}) is not recorded "
            "verbatim; check it against the fetched source before changing this"
        )


def test_mapping_skill_records_both_fetched_sources() -> None:
    """The resource page does not enumerate the ten, so the announcement that
    does is recorded alongside it."""
    text = (MAPPING_SKILL / "references" / "standards.md").read_text(encoding="utf-8")
    assert "genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026" in text
    assert "genai.owasp.org/2025/12/09/" in text
    assert "2026-09-07" in text, "the verification date must be recorded"


def test_decision_record_exists_with_alternatives_and_the_watch_item() -> None:
    assert DECISION_RECORD.is_file(), "the decision record for this mapping is missing"
    text = DECISION_RECORD.read_text(encoding="utf-8")
    assert "Status: implemented" in text
    assert "## Alternatives considered" in text
    assert "## Consequences" in text
    assert "Agent Control Standard" in text, (
        "the deferred-standard watch item must be recorded, or the next proposer "
        "re-litigates whether to wait for it"
    )


def test_worked_example_shows_a_deliberately_empty_owasp_tag() -> None:
    """The mapping skill's example is where a reader learns that not tagging is a
    valid outcome; without it the example teaches tagging everything."""
    body = (MAPPING_SKILL / "SKILL.md").read_text(encoding="utf-8")
    example = body.split("### 4. Worked example", 1)[1].split("\n### ", 1)[0]
    assert "owasp_agentic" in example
    assert "EMPTY" in example or "(none)" in example
