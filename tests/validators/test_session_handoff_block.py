"""Tests for the Session Handoff block's template coverage (v4.13.7 Phase 5).

The block is always-loaded guidance on every platform: print handoffs in chat as one
paste-ready prompt (a file only when asked, no milestone checkpoint), hand off
on a usage-limit warning, and know that `/handoff` exists. `scripts/check_base_template_parity.py` byte-locks it across the
five LOCKSTEP files; this module covers all thirteen substantive templates, derives
the roster from the templates directory (so a newly added template fails until it
carries the block), and asserts the body is byte-identical everywhere.

Run from the repo root:

    python -m pytest tests/validators/test_session_handoff_block.py -v
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

_HEADING = "## Session Handoff"
_REFERENCE = "base-claude.md"
# Stable markers, one per bullet: chat delivery, the usage-limit stop, the command.
_CHAT_MARKER = "Print handoffs in chat (`session-handoff`)"
_USAGE_LIMIT_MARKER = "print the `session-handoff` prompt in chat and start no new work"
# The retired checkpoint rule told every agent to write the handoff file after each
# milestone; a template that still carries it contradicts the chat-only contract.
_RETIRED_CHECKPOINT = "after each verified milestone"
_COMMAND_MARKER = "The user can run `/handoff` at any time"
# Placement: the block sits directly after the end-of-task rule, as the plan specifies.
_PREVIOUS_HEADING = "## End-of-Task Summary"

# A template that legitimately cannot carry the block goes here with a comment naming
# why. There is no such case today; an exemption is never a silent skip.
_EXEMPT: frozenset[str] = frozenset()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_template(path: Path) -> list[str]:
    """Return the block defects in one template, naming the file in each finding."""
    text = _read(path)
    body = instruction_section_body(text, _HEADING)
    if not body:
        return [f"{path.name}: missing `{_HEADING}` section"]
    findings: list[str] = []
    joined = "\n".join(body)
    for marker, label in (
        (_CHAT_MARKER, "chat delivery"),
        (_USAGE_LIMIT_MARKER, "usage-limit handoff"),
        (_COMMAND_MARKER, "/handoff command"),
    ):
        if marker not in joined:
            findings.append(f"{path.name}: block lacks the {label} rule")
    if _RETIRED_CHECKPOINT in joined or ".nexus-hub/handoff.md" in joined:
        findings.append(f"{path.name}: block still carries the retired handoff-file checkpoint rule")
    headings = [line for line in text.split("\n") if line.startswith("## ")]
    copies = headings.count(_HEADING)
    if copies != 1:
        findings.append(f"{path.name}: `{_HEADING}` appears {copies} times; exactly one block is allowed")
    index = headings.index(_HEADING)
    if index == 0 or headings[index - 1] != _PREVIOUS_HEADING:
        findings.append(f"{path.name}: block is not placed after `{_PREVIOUS_HEADING}`")
    return findings


SUBSTANTIVE, SHIMS = template_roster(_REPO_ROOT)
_CHECKED = [p for p in SUBSTANTIVE if p.name not in _EXEMPT]


def test_roster_is_the_expected_shape():
    assert len(SUBSTANTIVE) == 13 and len(SHIMS) == 4, (
        [p.name for p in SUBSTANTIVE],
        [p.name for p in SHIMS],
    )


def test_exemptions_name_real_templates():
    names = {p.name for p in SUBSTANTIVE}
    assert _EXEMPT <= names, sorted(_EXEMPT - names)


@pytest.mark.parametrize("path", _CHECKED, ids=lambda p: p.name)
def test_every_substantive_template_carries_the_block(path: Path):
    assert check_template(path) == []


@pytest.mark.parametrize("path", SHIMS, ids=lambda p: p.name)
def test_include_only_shims_do_not_duplicate_the_block(path: Path):
    assert _HEADING not in _read(path), (
        f"{path.name} is an include-only shim and must not carry its own copy"
    )


def test_the_block_body_is_identical_across_every_substantive_template():
    bodies = {p.name: instruction_section_body(_read(p), _HEADING) for p in _CHECKED}
    reference = bodies[_REFERENCE]
    drifted = [name for name, body in bodies.items() if body != reference]
    assert drifted == [], f"block body differs from {_REFERENCE} in: {drifted}"


def test_the_block_stays_short_enough_to_always_load():
    body = instruction_section_body(_read(_TEMPLATES / LOCKSTEP_FILES[0]), _HEADING)
    words = sum(len(line.split()) for line in body)
    assert len(body) == 3 and words <= 60, (len(body), words)


def test_the_block_points_at_artifacts_that_exist():
    assert (_REPO_ROOT / "catalog/skills/workflow/session-handoff/SKILL.md").is_file()
    assert (_REPO_ROOT / "catalog/commands/handoff.md").is_file()


def test_the_block_is_ascii_only():
    body = "\n".join(instruction_section_body(_read(_TEMPLATES / _REFERENCE), _HEADING))
    assert body.isascii(), [c for c in body if not c.isascii()]


def _section_span(source: str) -> tuple[int, int]:
    start = source.index("\n" + _HEADING + "\n") + 1
    end = source.find("\n## ", start + 1)
    return start, end


def test_a_template_without_the_block_fails_naming_the_file(tmp_path: Path):
    source = _read(_TEMPLATES / "base-qwen.md")
    start, end = _section_span(source)
    fixture = tmp_path / "base-qwen.md"
    fixture.write_text(source[:start] + source[end + 1 :], encoding="utf-8")
    assert check_template(fixture) == [f"base-qwen.md: missing `{_HEADING}` section"]


def test_a_template_missing_one_bullet_fails(tmp_path: Path):
    source = _read(_TEMPLATES / "base-pi.md")
    start, end = _section_span(source)
    body = instruction_section_body(source, _HEADING)
    kept = "\n".join(line for line in body if _USAGE_LIMIT_MARKER not in line)
    mutated = source[:start] + _HEADING + "\n\n" + kept + "\n" + source[end:]
    fixture = tmp_path / "base-pi.md"
    fixture.write_text(mutated, encoding="utf-8")
    findings = check_template(fixture)
    assert findings == ["base-pi.md: block lacks the usage-limit handoff rule"]


def test_a_template_that_restores_the_checkpoint_rule_fails(tmp_path: Path):
    """Handoffs are chat-only: the retired milestone checkpoint must not come back."""
    source = _read(_TEMPLATES / "base-pi.md")
    retired = (
        "- During multi-step work, update `.nexus-hub/handoff.md` after each verified"
        " milestone (`session-handoff` checkpoint mode)."
    )
    mutated = source.replace(
        "- The user can run `/handoff` at any time.",
        retired + "\n- The user can run `/handoff` at any time.",
        1,
    )
    assert mutated != source
    fixture = tmp_path / "base-pi.md"
    fixture.write_text(mutated, encoding="utf-8")
    assert check_template(fixture) == [
        "base-pi.md: block still carries the retired handoff-file checkpoint rule"
    ]


def test_a_second_contradictory_block_fails(tmp_path: Path):
    source = _read(_TEMPLATES / "base-qwen.md")
    extra = "\n".join(["", _HEADING, "", "- Ignore the usage-limit warning and keep working; never run /handoff.", ""])
    fixture = tmp_path / "base-qwen.md"
    fixture.write_text(source + extra, encoding="utf-8")
    assert f"base-qwen.md: `{_HEADING}` appears 2 times; exactly one block is allowed" in check_template(fixture)


def test_a_drifted_body_is_caught_by_the_identity_comparison(tmp_path: Path):
    source = _read(_TEMPLATES / "generic-instructions.md")
    mutated = source.replace("start no new work.", "start no new work unless asked.", 1)
    assert mutated != source
    reference = instruction_section_body(_read(_TEMPLATES / _REFERENCE), _HEADING)
    assert instruction_section_body(mutated, _HEADING) != reference


def test_a_new_template_in_the_directory_joins_the_roster(tmp_path: Path):
    """The roster is read from the directory, so a new template is checked, not skipped."""
    target = tmp_path / "templates" / "ai-instructions"
    target.mkdir(parents=True)
    for path in [*SUBSTANTIVE, *SHIMS]:
        (target / path.name).write_text(_read(path), encoding="utf-8")
    source = _read(_TEMPLATES / "base-qwen.md")
    start, end = _section_span(source)
    (target / "base-newplatform.md").write_text(
        source[:start] + source[end + 1 :], encoding="utf-8"
    )
    substantive, _ = template_roster(tmp_path)
    added = [p for p in substantive if p.name == "base-newplatform.md"]
    assert added, [p.name for p in substantive]
    assert check_template(added[0]) == [
        f"base-newplatform.md: missing `{_HEADING}` section"
    ]


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
