"""Tests for the non-blocking quality-heuristics pass in validate_skills.py.

The quality pass is warnings-only: it must flag a low-quality SKILL.md and
stay silent on a well-formed one, and it must NEVER change the validator's
exit code. These tests import the validator module directly (it lives under
scripts/, not on the default path) so the heuristics are exercised in
isolation, and one end-to-end subprocess test confirms `--quality` exits 0.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_skills.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_skills", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_skills = _load_validator()


GOOD_SKILL = dedent(
    """\
    ---
    name: good-skill
    description: A well-formed skill with trigger phrases. SKIP: nothing relevant.
    summary_l0: "A tight summary that stays well under the fifteen word limit"
    overview_l1: "A concise overview paragraph that comfortably stays under the one hundred and fifty word ceiling while still describing what the skill does and when to use it."
    ---

    # Good Skill

    ## When to Use This Skill

    Use when testing.

    ## Instructions

    1. Do the thing.

    ## Common Rationalizations

    | Rationalization | Reality |
    |---|---|
    | "Skip it" | Concrete failure mode here. |

    ## Verification

    - [ ] The artifact exists at the expected path.

    ## Related Skills

    - [[skill-create]] - the related skill.
    """
)


BAD_SKILL = dedent(
    """\
    ---
    name: bad-skill
    description: A skill missing several quality sections.
    summary_l0: "This summary is deliberately far too long and rambles on well past the fifteen word soft limit for sure"
    overview_l1: "Short overview."
    ---

    # Bad Skill

    ## When to Use This Skill

    Use when testing.

    ## Instructions

    1. Do the thing.

    ## Verification

    The implementation looks correct and the code reads well.
    """
)


def write_skill(skill_dir: Path, body: str) -> Path:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


def test_good_skill_has_no_quality_warnings(tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path / "good-skill", GOOD_SKILL)
    warnings = validate_skills.validate_skill_quality(skill_dir, GOOD_SKILL)
    assert warnings == [], warnings


def test_bad_skill_flags_every_heuristic(tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path / "bad-skill", BAD_SKILL)
    warnings = validate_skills.validate_skill_quality(skill_dir, BAD_SKILL)
    joined = "\n".join(warnings)
    # Missing Common Rationalizations section.
    assert "Common Rationalizations" in joined
    # Prose-only Verification (no '- [ ]' checklist).
    assert "prose-only" in joined
    # Over-long summary_l0.
    assert "summary_l0" in joined
    # Missing Related Skills section.
    assert "Related Skills" in joined


def test_quality_warnings_carry_the_quality_prefix(tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path / "bad-skill", BAD_SKILL)
    warnings = validate_skills.validate_skill_quality(skill_dir, BAD_SKILL)
    assert warnings
    assert all("quality:" in w for w in warnings)


def test_section_body_extraction_is_case_insensitive() -> None:
    content = "## verification\n- [ ] item\n\n## Next\n"
    body = validate_skills._section_body(content, "Verification")
    assert body is not None
    assert "- [ ]" in body


@pytest.mark.parametrize("flag", ["--quality", "--quality --verbose"])
def test_quality_cli_exits_zero_on_catalog(flag: str) -> None:
    """The --quality pass is warnings-only and must always exit 0."""
    cmd = [sys.executable, str(VALIDATOR), *flag.split()]
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=False, cwd=REPO_ROOT
    )
    assert result.returncode == 0, result.stderr
    assert "quality heuristics" in result.stdout


def test_quality_mode_does_not_invoke_secret_scan(tmp_path: Path) -> None:
    """`--quality` alone must not run the secret scanner.

    The quality pass is defined as a pure quality-heuristics pass; the
    secret scan belongs to the full structural validator (and is hard-error
    on a real hit). Putting a plausible OpenAI-style key in a fixture under
    the skill bundle proves that running `--quality` does not surface it as
    an error -- if it did, exit code would be 1 and the run would fail CI
    in non-blocking situations where that is exactly what `--quality` is
    designed to avoid.
    """
    skill_dir = tmp_path / "fixture-with-secret"
    write_skill(skill_dir, GOOD_SKILL)
    (skill_dir / "scripts").mkdir()
    # A 30-char alphanumeric key that matches SECRET_PATTERNS["OpenAI API key"].
    (skill_dir / "scripts" / "leaky.py").write_text(
        "OPENAI_KEY = 'sk-" + "A" * 30 + "'\n", encoding="utf-8"
    )
    cmd = [
        sys.executable,
        str(VALIDATOR),
        "--quality",
        "--verbose",
        "--path",
        str(tmp_path),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=False, cwd=REPO_ROOT
    )
    assert result.returncode == 0, result.stderr
    # The secret should not be surfaced as an error OR a quality warning.
    assert "OpenAI API key" not in result.stdout
    assert "OpenAI API key" not in result.stderr
