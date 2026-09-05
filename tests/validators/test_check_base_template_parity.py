"""Tests for scripts/check_base_template_parity.py.

The guard enforces the AGENTS.md "edit all five base-*.md in lockstep" rule by
comparing the five platform-agnostic instruction templates structurally:
required shared headings + placeholder tokens must be present in each, and the
bodies of the invariant sections (Tech Stack / Key Commands / Branching / MCP
Registry Policy) must stay identical across the set.

These tests run the guard against the real repo (the must-pass baseline) and
against temporary trees seeded by copying the real templates and mutating one
thing: a removed heading, a reworded invariant block, a dropped placeholder
(each a FINDING), and an allowed per-platform install-path change (still a
PASS, proving the contract tolerates legitimate divergence).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_REL = "templates/ai-instructions"
LOCKSTEP_FILES = [
    "base-claude.md",
    "base-codex.md",
    "base-cursor.md",
    "base-gemini.md",
    "base-opencode.md",
]

SCRIPT = "check_base_template_parity.py"


def _real_template(name: str) -> str:
    return (REPO_ROOT / TEMPLATES_REL / name).read_text(encoding="utf-8")


def seed_lockstep_tree(root: Path, only: list[str] | None = None) -> Path:
    """Copy the real lockstep templates into `root/templates/ai-instructions`.

    `only` restricts the copy to a subset (used by the partial-tree test).
    """
    dst_dir = root / TEMPLATES_REL
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in only or LOCKSTEP_FILES:
        (dst_dir / name).write_text(_real_template(name), encoding="utf-8")
    return root


def mutate(root: Path, name: str, old: str, new: str) -> None:
    """Replace `old` with `new` in one seeded template, asserting it changed."""
    path = root / TEMPLATES_REL / name
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture precondition: {old!r} not found in {name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_real_repo_templates_are_in_parity(runner) -> None:
    # The must-pass baseline: the five current templates satisfy the contract.
    result = runner(SCRIPT, REPO_ROOT)
    assert result.returncode == 0, result.stderr


def test_missing_shared_heading_fails(tmp_path: Path, runner) -> None:
    # Drop the shared `## Branching` heading from one file -> required-heading
    # finding. (Proves the structural floor catches a removed shared section.)
    seed_lockstep_tree(tmp_path)
    mutate(tmp_path, "base-gemini.md", "## Branching\n", "")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-gemini.md" in result.stderr
    assert "Branching" in result.stderr


def test_missing_placeholder_fails(tmp_path: Path, runner) -> None:
    # Remove the {{SKILL_INDEX}} token from one file -> placeholder finding.
    seed_lockstep_tree(tmp_path)
    mutate(tmp_path, "base-codex.md", "{{SKILL_INDEX}}", "")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-codex.md" in result.stderr
    assert "SKILL_INDEX" in result.stderr


def test_invariant_block_divergence_fails(tmp_path: Path, runner) -> None:
    # Reword the MCP Registry Policy body in one file -> block-divergence
    # finding. This is the core lockstep enforcer: a policy edit applied to
    # four of five must fail.
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-opencode.md",
        "Hard no: search-as-service",
        "Hard no: nothing-at-all",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-opencode.md" in result.stderr
    assert "MCP Registry Policy" in result.stderr


def test_communication_contract_divergence_fails(tmp_path: Path, runner) -> None:
    # v4.0.0: the Communication Contract body is an invariant block. A one-word
    # reword in a single template must fail, naming the file and the section.
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-cursor.md",
        "- Close tasks with Completed / Verified / Open / Next.",
        "- Close tasks with Completed / Verified / Open / Later.",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-cursor.md" in result.stderr
    assert "Communication Contract" in result.stderr


def test_documentation_layout_divergence_fails(tmp_path: Path, runner) -> None:
    # The Documentation Layout body is an invariant block. A one-word change
    # in one template must fail and name both the file and section.
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-gemini.md",
        "Use lifespan as the single placement axis for project documentation.",
        "Use topic as the single placement axis for project documentation.",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-gemini.md" in result.stderr
    assert "Documentation Layout" in result.stderr


def test_missing_communication_contract_heading_fails(tmp_path: Path, runner) -> None:
    # The heading is also in REQUIRED_HEADINGS, so dropping the section
    # entirely from one template is a distinct, separately-reported failure.
    seed_lockstep_tree(tmp_path)
    mutate(tmp_path, "base-codex.md", "## Communication Contract\n", "")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-codex.md" in result.stderr


def test_allowed_per_platform_line_still_passes(tmp_path: Path, runner) -> None:
    # Change only an allowed per-platform install path (Context References is
    # neither a required heading/placeholder nor an invariant block) -> the
    # guard must NOT flag it. This proves the contract tolerates legitimate
    # per-platform divergence (no false positive).
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-cursor.md",
        "- Skills: `.cursor/skills/`",
        "- Skills: `.cursor/agents/skills/`",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_partial_tree_is_a_noop(tmp_path: Path, runner) -> None:
    # Only one lockstep file present: nothing to compare -> clean exit 0.
    seed_lockstep_tree(tmp_path, only=["base-claude.md"])
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_no_templates_dir_is_a_noop(tmp_path: Path, runner) -> None:
    # An empty tree (no templates at all) is tolerated, not a crash.
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_json_output_in_parity(runner) -> None:
    import json

    result = runner(SCRIPT, REPO_ROOT, ["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["in_parity"] is True
    assert len(payload["present"]) == 5
    assert payload["findings"] == []


def test_json_output_reports_findings(tmp_path: Path, runner) -> None:
    import json

    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-opencode.md",
        "Hard no: search-as-service",
        "Hard no: nothing-at-all",
    )
    result = runner(SCRIPT, tmp_path, ["--json"])
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["in_parity"] is False
    assert any(f["file"] == "base-opencode.md" for f in payload["findings"])
    assert any(f["category"] == "block-divergence" for f in payload["findings"])


# --- v4.5.0 phase 1: the always-on Writing Discipline block ---------------------
# Temporary home. Phase 2 promotes "Writing Discipline" into the guard's
# INVARIANT_SECTIONS (covering the lockstep five) and moves the twelve-template
# assertion into its own companion validator; when that lands, this block of
# tests is relocated rather than duplicated.

SUBSTANTIVE_UNGUARDED = [
    "base-google-shared.md",
    "base-aider.md",
    "base-kimi.md",
    "base-openclaw.md",
    "base-qwen.md",
    "base-windsurf.md",
    "generic-instructions.md",
]
SURFACE_NOTES = [
    "base-antigravity-10.md",
    "base-antigravity-20.md",
    "base-antigravity-cli.md",
    "base-gemini-cli.md",
]
WRITING_DISCIPLINE_HEADING = "## Writing Discipline"


def _section_body(text: str, heading: str) -> str | None:
    """Return the normalized body under `heading`, or None when the heading is absent."""
    lines = text.replace("\r\n", "\n").split("\n")
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return None
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        body.append(line.rstrip())
    return "\n".join(body).strip("\n")


def test_writing_discipline_present_in_all_twelve_substantive_templates() -> None:
    missing = [
        name
        for name in LOCKSTEP_FILES + SUBSTANTIVE_UNGUARDED
        if _section_body(_real_template(name), WRITING_DISCIPLINE_HEADING) is None
    ]
    assert not missing, f"Writing Discipline block missing from: {missing}"


def test_writing_discipline_absent_from_surface_note_files() -> None:
    present = [
        name
        for name in SURFACE_NOTES
        if WRITING_DISCIPLINE_HEADING in _real_template(name)
    ]
    assert not present, (
        f"surface-note pointer files must not carry the block: {present}"
    )


def test_writing_discipline_body_identical_across_all_twelve() -> None:
    bodies = {
        name: _section_body(_real_template(name), WRITING_DISCIPLINE_HEADING)
        for name in LOCKSTEP_FILES + SUBSTANTIVE_UNGUARDED
    }
    distinct = {body for body in bodies.values() if body is not None}
    assert len(distinct) == 1, (
        "Writing Discipline body differs across templates: "
        + ", ".join(sorted(n for n, b in bodies.items() if b != next(iter(distinct))))
    )


def test_writing_discipline_block_stays_within_budget_and_ascii() -> None:
    body = _section_body(_real_template("base-claude.md"), WRITING_DISCIPLINE_HEADING)
    assert body is not None
    non_ascii = sorted({c for c in body if ord(c) > 127})
    assert not non_ascii, f"block must be ASCII only, found {non_ascii!r}"
    # heading + body lines, counting separators, must not exceed the plan's 14-line budget
    assert body.count("\n") + 2 <= 14, (
        "Writing Discipline block exceeds its 14-line budget"
    )
