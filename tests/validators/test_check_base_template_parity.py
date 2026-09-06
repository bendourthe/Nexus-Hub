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


def test_writing_discipline_divergence_fails(tmp_path: Path, runner) -> None:
    # v4.5.0: the Writing Discipline body is an invariant block. A one-word
    # reword in a single template must fail, naming the file and the section.
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-gemini.md",
        "Chatbot leftovers are defects, not style:",
        "Chatbot leftovers are quirks, not style:",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-gemini.md" in result.stderr
    assert "Writing Discipline" in result.stderr


def test_missing_writing_discipline_heading_fails(tmp_path: Path, runner) -> None:
    # v4.5.0: dropping the whole block from one lockstep file must fail on the
    # required-heading check, so a platform cannot silently lose the rule.
    seed_lockstep_tree(tmp_path)
    mutate(tmp_path, "base-codex.md", "## Writing Discipline", "## Writing Habits")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-codex.md" in result.stderr
    assert "Writing Discipline" in result.stderr


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


def test_autonomy_block_body_drift_fails(tmp_path: Path, runner) -> None:
    # v4.7.0: the Autonomous Operation body is an invariant block. Rewording one
    # lockstep file must fail the guard and name both the file and the block.
    seed_lockstep_tree(tmp_path)
    mutate(
        tmp_path,
        "base-cursor.md",
        "You are operating autonomously",
        "You are operating on your own",
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "base-cursor.md" in result.stderr
    assert "Autonomous Operation" in result.stderr
