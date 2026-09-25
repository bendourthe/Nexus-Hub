"""Tests for the construction-discipline rule's template coverage (v4.1.2 Phase 1).

The pre-write ladder must reach every agent on every platform, which means it
lives in always-loaded instruction text rather than a skill (skills under-trigger
against an "always" requirement) or a hook.

`scripts/check_base_template_parity.py` already guards the five LOCKSTEP files.
It does not look at the other eight substantive templates at all. This file
closes that gap the same way `test_end_of_task_rule.py` does for End-of-Task
Summary.

Run from the repo root:

    python -m pytest tests/validators/test_construction_discipline_rule.py -v
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_base_template_parity import (
    LOCKSTEP_FILES,
    instruction_section_body,
    template_roster,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO_ROOT / "templates" / "ai-instructions"

_HEADING = "## Construction Discipline"

_LOCKSTEP = LOCKSTEP_FILES
_SUBSTANTIVE_PATHS, _INCLUDE_ONLY_PATHS = template_roster(_REPO_ROOT)
_SUBSTANTIVE = [path.name for path in _SUBSTANTIVE_PATHS]
_INCLUDE_ONLY = [path.name for path in _INCLUDE_ONLY_PATHS]


def _read(name: str) -> str:
    return (_TEMPLATES / name).read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("name", _SUBSTANTIVE)
def test_every_substantive_template_carries_the_rule(name: str):
    assert _HEADING in _read(name), (
        f"{name} is a substantive instruction template but has no {_HEADING!r} "
        "section; the rule must reach every platform that has an instruction surface"
    )


def test_the_rule_body_is_identical_across_every_substantive_template():
    """Not just the lockstep five.

    The parity guard pins the five; nothing pinned the other eight, so a reworded
    copy could drift into one platform's instructions unnoticed.
    """
    bodies = {name: instruction_section_body(_read(name), _HEADING) for name in _SUBSTANTIVE}
    reference = bodies[_LOCKSTEP[0]]

    assert reference, "the reference template has an empty rule body"
    for name, body in bodies.items():
        assert body == reference, (
            f"{name} diverges from {_LOCKSTEP[0]}:\n"
            f"  expected: {reference}\n  actual:   {body}"
        )


@pytest.mark.parametrize("name", _INCLUDE_ONLY)
def test_include_only_shims_do_not_duplicate_the_rule(name: str):
    """They inherit it, so a local copy would load the rule twice."""
    text = _read(name)

    assert "@base-" in text, (
        f"{name} was expected to be an include-only shim but has no @-include"
    )
    assert _HEADING not in text, (
        f"{name} inherits the rule through its @-include; a local copy duplicates it"
    )


def test_the_rule_stays_short_enough_to_always_load():
    """This text loads in every session on every platform, so it is budgeted.

    Three bullets was the authoring target. The cap here is eight non-empty
    body lines: tight enough to catch the section growing into a runbook,
    loose enough to allow a considered edit.
    """
    body = instruction_section_body(_read(_LOCKSTEP[0]), _HEADING)

    assert len(body) <= 8, (
        f"the rule has grown to {len(body)} lines; it is always-loaded on every "
        "platform, so push detail into a skill or a reference doc instead"
    )


def test_the_rule_is_not_nested_in_output_minimization():
    """Construction Discipline is its own heading, not an Output Minimization bullet."""
    text = _read(_LOCKSTEP[0])
    output_start = text.find("## Output Minimization")
    construction_start = text.find(_HEADING)
    next_after_output = text.find("\n## ", output_start + 1)

    assert construction_start != -1
    assert next_after_output != -1
    assert not (output_start < construction_start < next_after_output), (
        "Construction Discipline must not live inside Output Minimization"
    )


def _load_parity_guard():
    """Import the guard module so its real constants are asserted, not its source text."""
    import importlib.util

    path = _REPO_ROOT / "scripts" / "check_base_template_parity.py"
    spec = importlib.util.spec_from_file_location("check_base_template_parity", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parity_guard_enforces_the_rule_on_the_lockstep_five():
    """The heading must be in BOTH guard lists, not merely present in the files.

    Asserted against the imported constants rather than the file's text: a
    source-text search matches the module docstring, which mentions both list
    names, and would pass even with the heading absent from either list.
    """
    guard = _load_parity_guard()
    heading = _HEADING.removeprefix("## ")

    assert heading in guard.REQUIRED_HEADINGS, (
        f"{heading!r} missing from REQUIRED_HEADINGS: a lockstep file could drop "
        "the section entirely without failing validation"
    )
    assert heading in guard.INVARIANT_SECTIONS, (
        f"{heading!r} missing from INVARIANT_SECTIONS: the body could be reworded "
        "on one platform without failing validation"
    )
