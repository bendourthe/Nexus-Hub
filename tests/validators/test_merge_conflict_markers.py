"""The conflict-marker gate must catch a widened rename-conflict run.

A rename/modify merge committed without resolution writes `<<<<<<<< HEAD:path`
with EIGHT characters, not the familiar seven. The first version of this gate
anchored on exactly seven, so eleven such conflicts sat in a release plan while
the fast profile reported fourteen of fourteen green. Every assertion below is
negative-controlled: each fixture that must fail carries the defect, and each
fixture that must pass carries the nearest look-alike.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "check_merge_conflict_markers", ROOT / "scripts" / "check_merge_conflict_markers.py"
)
gate = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = gate
_spec.loader.exec_module(gate)


def scan(tmp_path: Path, text: str) -> list[tuple[int, str]]:
    target = tmp_path / "sample.md"
    target.write_text(text, encoding="utf-8")
    return gate.conflicts_in(target)


CONFLICTING = {
    "classic seven": "a\n<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n",
    "widened eight, the rename case": (
        "a\n<<<<<<<< HEAD:docs/old.md\nours\n========\ntheirs\n"
        ">>>>>>>> origin/develop:docs/new.md\n"
    ),
    "start marker with no label": "<<<<<<<\nours\n",
    "end marker alone": "text\n>>>>>>> origin/main\n",
}

CLEAN = {
    "setext rule": "Heading\n=======\n\nbody\n",
    "prose naming the markers": "Resolve the `<<<<<<<` block by hand.\n",
    "marker not at line start": "  <<<<<<< HEAD\n",
    "horizontal rule of dashes": "body\n\n-------\n",
    "short run": "<<<<<< HEAD\n",
}


@pytest.mark.parametrize("name", sorted(CONFLICTING))
def test_conflict_is_reported(tmp_path: Path, name: str) -> None:
    assert scan(tmp_path, CONFLICTING[name]), f"{name} should be reported"


@pytest.mark.parametrize("name", sorted(CLEAN))
def test_clean_text_is_not_reported(tmp_path: Path, name: str) -> None:
    assert scan(tmp_path, CLEAN[name]) == [], f"{name} should not be reported"


def test_reported_line_numbers_are_one_indexed(tmp_path: Path) -> None:
    findings = scan(tmp_path, "one\ntwo\n<<<<<<<< HEAD:a\nours\n")
    assert [number for number, _ in findings] == [3]


def test_the_gate_allowlists_only_its_own_subject_matter() -> None:
    # An allowlist that grows silently is how a real conflict gets excused.
    assert gate.ALLOWLIST == {
        "catalog/skills/workflow/conflict-analyzer/SKILL.md",
        "scripts/check_merge_conflict_markers.py",
    }
