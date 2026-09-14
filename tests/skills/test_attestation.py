"""The attestation gate checks that decisions were RECORDED, never that they are good.

Two properties, and the second is the one that keeps this honest:

1. A missing or empty record fails; a complete record passes.
2. The gate never scores content. `test_attestation_never_scores_content` gives
   it a record whose prose is deliberately terrible but structurally complete,
   and requires a pass. The moment that test fails, someone has added a quality
   heuristic and turned this into the beauty detector the plan forbids.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "catalog/skills/specialized-domains/document-to-interactive-html"
    / "scripts/check_attestation.py"
)
_spec = importlib.util.spec_from_file_location("check_attestation", SCRIPT)
att = importlib.util.module_from_spec(_spec)
sys.modules["check_attestation"] = att
_spec.loader.exec_module(att)


def complete_record() -> dict:
    return {
        "figures": [
            {
                "id": "fig-concept",
                "class": "illustrative",
                "labels_the_rule_not_the_number": "walk-stop threshold: 25% of this window's own peak",
            },
            {
                "id": "fig-measured",
                "class": "evidential",
                "series": [
                    {"name": "throughput", "source": "analysis/throughput.py::rolling_mean"}
                ],
            },
        ],
        "content_cuts": "Dropped the tooling history section and two worked examples; the draft ran 2.4x the useful length.",
        "code_claims": [
            {
                "claim": "the walk detector stops at 25% of peak",
                "file": "src/gait/detect.py",
                "function": "walk_stop_threshold",
            }
        ],
        "authorship": "Reviewed for uniform card grids and callout stripes; two three-card rows rewritten as prose.",
        "shared_numbers": [
            {"value": "4.7", "source": "analysis/throughput.py::rolling_mean"}
        ],
    }


def write(tmp_path: Path, record) -> Path:
    target = tmp_path / "attestation.json"
    target.write_text(json.dumps(record), encoding="utf-8")
    return target


def test_a_complete_record_passes(tmp_path: Path) -> None:
    assert att.check(complete_record()) == []
    record_path = write(tmp_path, complete_record())
    assert att.main([str(record_path)]) == att.EXIT_PASS


def test_an_absent_record_fails_rather_than_defaulting_to_pass(tmp_path: Path) -> None:
    """A build with no attestation has not made these decisions, or hid them."""
    assert att.main([str(tmp_path / "nothing.json")]) == att.EXIT_UNREADABLE


@pytest.mark.parametrize("section", sorted(att.REQUIRED_SECTIONS))
def test_removing_any_required_section_fails(tmp_path: Path, section: str) -> None:
    record = complete_record()
    del record[section]
    findings = att.check(record)
    assert any(section in f for f in findings), findings
    record_path = write(tmp_path, record)
    assert att.main([str(record_path)]) == att.EXIT_INCOMPLETE


@pytest.mark.parametrize("section", sorted(att.REQUIRED_SECTIONS))
def test_emptying_any_required_section_fails(tmp_path: Path, section: str) -> None:
    """Present-but-empty is the way a record gets filed without being made."""
    record = complete_record()
    record[section] = [] if isinstance(record[section], list) else ""
    assert any(section in f for f in att.check(record))


def test_an_unclassified_figure_fails() -> None:
    record = complete_record()
    record["figures"][0].pop("class")
    assert any("class must be one of" in f for f in att.check(record))


def test_an_evidential_series_with_no_computation_fails() -> None:
    """The hardcoded-list defect: points chosen because they looked right."""
    record = complete_record()
    record["figures"][1]["series"][0].pop("source")
    findings = att.check(record)
    assert any("names no source" in f for f in findings), findings


def test_an_illustrative_figure_must_attest_it_labels_the_rule() -> None:
    record = complete_record()
    record["figures"][0].pop("labels_the_rule_not_the_number")
    assert any("labels the rule" in f for f in att.check(record))


def test_a_code_claim_must_name_where_it_was_verified() -> None:
    record = complete_record()
    record["code_claims"][0].pop("function")
    findings = att.check(record)
    assert any("function" in f for f in findings), findings


def test_a_number_shared_between_figure_and_prose_names_one_source() -> None:
    """The 4.7-versus-27.8 defect: one number, two derivations, no shared source."""
    record = complete_record()
    record["shared_numbers"][0].pop("source")
    assert any("single source" in f for f in att.check(record))


def test_attestation_never_scores_content() -> None:
    """The boundary this gate must not cross.

    This record is structurally complete and its prose is deliberately awful:
    empty of specifics, full of filler, and self-evidently the kind of text the
    anti-slop rules exist to remove. It MUST pass, because judging it is the
    beauty detector the plan forbids.

    If this test ever fails, someone has added a quality heuristic here. Move it
    to a skill that owns authorship, or delete it.
    """
    record = complete_record()
    record["content_cuts"] = "stuff"
    record["authorship"] = "looked at it"
    record["code_claims"][0]["claim"] = "it works"
    assert att.check(record) == [], (
        "the gate judged content quality; it must only check that a decision "
        "was recorded"
    )


def test_a_malformed_record_is_unreadable_not_a_pass(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert att.main([str(broken)]) == att.EXIT_UNREADABLE

    listed = tmp_path / "listed.json"
    listed.write_text("[]", encoding="utf-8")
    assert att.main([str(listed)]) == att.EXIT_UNREADABLE
