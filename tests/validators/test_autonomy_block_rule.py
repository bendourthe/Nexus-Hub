"""Tests for the autonomous-operation block's template coverage (v4.7.0 Phase 2).

The block is always-loaded guidance on every platform. `scripts/check_base_template_parity.py`
byte-locks it across the five LOCKSTEP files; this module covers all thirteen substantive
templates, derives the roster from the templates directory (so a newly added template fails
until it carries the block), and asserts on stable markers rather than the full prose, so
a considered per-platform reduction passes while an absent block fails.

Run from the repo root:

    python -m pytest tests/validators/test_autonomy_block_rule.py -v
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from scripts.check_base_template_parity import (
    LOCKSTEP_FILES,
    instruction_section_body,
    template_roster,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO_ROOT / "templates" / "ai-instructions"

_HEADING = "## Autonomous Operation"
# Stable markers: the load-bearing opening clause, and the amendment's precedence sentence.
_OPENING_MARKER = "You are operating autonomously"
_PRECEDENCE_MARKER = (
    "The user's instructions take precedence over guidelines in a skill."
)
_DISCLOSURE_MARKER = (
    "name the skill, link its `SKILL.md`, and quote the line you set aside"
)
_CD_REFERENCE = "The boundary itself is stated once, in `## Autonomous Operation`"
_SD_ORIGINAL = "Do not mention the skill lookup to the user."
_SD_CROSS_REFERENCE = "is governed by `## Autonomous Operation`"

_LOCKSTEP = LOCKSTEP_FILES


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_template(path: Path) -> list[str]:
    """Return the block defects in one template, naming the file in each finding."""
    text = _read(path)
    findings: list[str] = []
    body = instruction_section_body(text, _HEADING)
    if not body:
        findings.append(f"{path.name}: missing `{_HEADING}` section")
        return findings
    joined = "\n".join(body)
    if _OPENING_MARKER not in joined:
        findings.append(
            f"{path.name}: block lacks its opening clause {_OPENING_MARKER!r}"
        )
    if _PRECEDENCE_MARKER not in joined:
        findings.append(
            f"{path.name}: block lacks the user-over-skill precedence paragraph"
        )
    if _DISCLOSURE_MARKER not in joined:
        findings.append(f"{path.name}: block lacks the disclosed-deviation instruction")
    return findings


SUBSTANTIVE, SHIMS = template_roster(_REPO_ROOT)


def test_roster_is_the_expected_shape():
    assert len(SUBSTANTIVE) == 13 and len(SHIMS) == 4, (
        [p.name for p in SUBSTANTIVE],
        [p.name for p in SHIMS],
    )


@pytest.mark.parametrize("path", SUBSTANTIVE, ids=lambda p: p.name)
def test_every_substantive_template_carries_the_block(path: Path):
    assert check_template(path) == []


@pytest.mark.parametrize("path", SHIMS, ids=lambda p: p.name)
def test_include_only_shims_do_not_duplicate_the_block(path: Path):
    assert _HEADING not in _read(path), (
        f"{path.name} is an include-only shim and must not carry its own copy"
    )


def test_the_block_body_is_identical_across_every_substantive_template():
    bodies = {p.name: instruction_section_body(_read(p), _HEADING) for p in SUBSTANTIVE}
    reference = bodies["base-claude.md"]
    drifted = [name for name, body in bodies.items() if body != reference]
    assert drifted == [], f"block body differs from base-claude.md in: {drifted}"


def test_consequential_decisions_references_the_block(tmp_path: Path):
    missing = [p.name for p in SUBSTANTIVE if _CD_REFERENCE not in _read(p)]
    assert missing == [], missing


def test_skill_discovery_keeps_its_silent_lookup_sentence_and_cross_references_the_block():
    missing_original = [p.name for p in SUBSTANTIVE if _SD_ORIGINAL not in _read(p)]
    missing_xref = [p.name for p in SUBSTANTIVE if _SD_CROSS_REFERENCE not in _read(p)]
    assert missing_original == [], (
        f"silent-lookup sentence softened in: {missing_original}"
    )
    assert missing_xref == [], f"cross-reference missing in: {missing_xref}"


def test_the_block_stays_short_enough_to_always_load():
    body = instruction_section_body(_read(_TEMPLATES / _LOCKSTEP[0]), _HEADING)
    words = sum(len(line.split()) for line in body)
    assert len(body) <= 4 and words <= 260, (len(body), words)


def test_a_template_carrying_the_block_without_the_precedence_paragraph_fails(
    tmp_path: Path,
):
    """Negative fixture (amendment sub-task 2.3): the paragraph is part of the checked block."""
    source = _read(_TEMPLATES / "base-qwen.md")
    body = instruction_section_body(source, _HEADING)
    stripped = "\n".join(line for line in body if _PRECEDENCE_MARKER not in line)
    start = source.index("\n" + _HEADING + "\n") + 1
    end = source.find("\n## ", start + 1)
    mutated = source[:start] + _HEADING + "\n\n" + stripped + "\n" + source[end:]
    fixture = tmp_path / "base-qwen.md"
    fixture.write_text(mutated, encoding="utf-8")
    findings = check_template(fixture)
    assert findings and all("base-qwen.md" in f for f in findings)
    assert any("precedence" in f for f in findings)


def test_a_template_without_the_block_fails_naming_the_file(tmp_path: Path):
    source = _read(_TEMPLATES / "base-qwen.md")
    start = source.index("\n" + _HEADING + "\n") + 1
    end = source.find("\n## ", start + 1)
    fixture = tmp_path / "base-qwen.md"
    fixture.write_text(source[:start] + source[end + 1 :], encoding="utf-8")
    findings = check_template(fixture)
    assert findings == [f"base-qwen.md: missing `{_HEADING}` section"]


def _load_parity_guard():
    path = _REPO_ROOT / "scripts" / "check_base_template_parity.py"
    spec = importlib.util.spec_from_file_location("check_base_template_parity", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parity_guard_enforces_the_block_on_the_lockstep_five():
    guard = _load_parity_guard()
    heading = _HEADING.removeprefix("## ")
    assert heading in guard.REQUIRED_HEADINGS
    assert heading in guard.INVARIANT_SECTIONS
