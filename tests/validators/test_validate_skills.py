"""Tests for the single-line name/description rules in validate_skills.py.

These rules (insight I-03 from the Nexus adoption-skill-cleaner track) are
hard-errors at PR time: `name` must be single-line kebab-case, `description`
must be single-line and at most 250 characters, and an absent `name` defaults
to the parent directory name (which must itself be kebab-case). A transitional
`--allow-existing` flag, backed by scripts/validate_skills.allowlist.json,
demotes known pre-existing violations to warnings while the catalog drains.

The tests import the validator module directly (it lives under scripts/, not on
the default path) and add one end-to-end subprocess test that the new check
fires through the CLI surface.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_skills.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_skills", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_skills = _load_validator()


def _skill_content(name: str, description: str) -> str:
    """A structurally-complete SKILL.md whose only variable is name/description."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "summary_l0: A short summary well under the limit.\n"
        "overview_l1: A short overview paragraph.\n"
        "---\n\n"
        f"# {name}\n\nBody.\n"
    )


# ---------------------------------------------------------------------------
# validate_frontmatter_format -- the three rules in isolation
# ---------------------------------------------------------------------------

def test_conformant_frontmatter_has_no_format_errors(tmp_path: Path) -> None:
    d = tmp_path / "good-skill"
    fm = {"name": "good-skill", "description": "A concise single-line description."}
    assert validate_skills.validate_frontmatter_format(d / "SKILL.md", d, fm) == []


def test_overlong_description_is_error(tmp_path: Path) -> None:
    d = tmp_path / "wordy-skill"
    fm = {"name": "wordy-skill", "description": "x" * 251}
    errs = validate_skills.validate_frontmatter_format(d / "SKILL.md", d, fm)
    assert any("251 characters" in e and "max 250" in e for e in errs)


def test_description_at_the_limit_is_ok(tmp_path: Path) -> None:
    d = tmp_path / "edge-skill"
    fm = {"name": "edge-skill", "description": "x" * 250}
    assert validate_skills.validate_frontmatter_format(d / "SKILL.md", d, fm) == []


def test_non_kebab_name_is_error(tmp_path: Path) -> None:
    d = tmp_path / "bad-name"
    fm = {"name": "Bad_Name", "description": "ok"}
    errs = validate_skills.validate_frontmatter_format(d / "SKILL.md", d, fm)
    assert any("kebab-case" in e and "frontmatter name" in e for e in errs)


def test_absent_name_defaults_to_directory_name(tmp_path: Path) -> None:
    # A kebab-case directory name satisfies the default-name rule.
    good = tmp_path / "fine-dir"
    assert validate_skills.validate_frontmatter_format(good / "SKILL.md", good, {"description": "ok"}) == []
    # A non-kebab directory name fails, and the message names the directory default.
    bad = tmp_path / "Bad_Dir"
    errs = validate_skills.validate_frontmatter_format(bad / "SKILL.md", bad, {"description": "ok"})
    assert any("directory name" in e and "kebab-case" in e for e in errs)


def test_description_with_newline_is_error(tmp_path: Path) -> None:
    d = tmp_path / "multi-line"
    fm = {"name": "multi-line", "description": "line one\nline two"}
    errs = validate_skills.validate_frontmatter_format(d / "SKILL.md", d, fm)
    assert any("single line" in e for e in errs)


# ---------------------------------------------------------------------------
# Allowlist loading + grandfathering
# ---------------------------------------------------------------------------

def test_load_allowlist_reads_the_allow_array(tmp_path: Path) -> None:
    p = tmp_path / "allow.json"
    p.write_text(json.dumps({"allow": ["catalog/skills/foo/SKILL.md"]}), encoding="utf-8")
    assert validate_skills.load_allowlist(p) == {"catalog/skills/foo/SKILL.md"}


def test_load_allowlist_missing_file_is_empty(tmp_path: Path) -> None:
    assert validate_skills.load_allowlist(tmp_path / "nope.json") == set()


def test_load_allowlist_malformed_file_is_empty(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert validate_skills.load_allowlist(p) == set()


def test_grandfathered_violation_is_demoted_to_warning(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wordy-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(_skill_content("wordy-skill", "x" * 300), encoding="utf-8")

    # Not grandfathered -> the over-long description is a hard error.
    errs, _warns = validate_skills.validate_skill_dir(skill_dir)
    assert any("max 250" in e for e in errs)

    # Grandfathered -> demoted to a warning, no error.
    key = skill_file.as_posix()
    errs2, warns2 = validate_skills.validate_skill_dir(skill_dir, {key})
    assert not any("max 250" in e for e in errs2)
    assert any("grandfathered" in w for w in warns2)


# ---------------------------------------------------------------------------
# End-to-end CLI surface
# ---------------------------------------------------------------------------

def test_overlong_description_fails_full_validator_via_cli(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wordy-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(_skill_content("wordy-skill", "x" * 300), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--path", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1, result.stdout
    assert "max 250" in result.stdout


# ---------------------------------------------------------------------------
# Fenced-code-aware secret scan (BG-v23-1)
# ---------------------------------------------------------------------------

_FENCED = (
    "# Example\n\n"
    "Here is how NOT to store a secret:\n\n"
    "```python\n"
    'password = "hunter2pass"\n'
    "```\n\n"
    "Done.\n"
)

_UNFENCED = (
    "# Example\n\n"
    'A bare assignment in prose: password = "hunter2pass" should be flagged.\n'
)


def test_fenced_generic_secret_is_ignored() -> None:
    errs = validate_skills.scan_text_for_secrets(_FENCED, Path("doc.md"))
    assert errs == [], errs


def test_unfenced_generic_secret_is_flagged() -> None:
    errs = validate_skills.scan_text_for_secrets(_UNFENCED, Path("doc.md"))
    assert any("Generic secret assignment" in e for e in errs), errs


def test_high_confidence_secret_flagged_even_in_fence() -> None:
    # A real-format AWS key inside a fence must still be flagged.
    text = "```\nAKIAIOSFODNN7EXAMPLE\n```\n"
    errs = validate_skills.scan_text_for_secrets(text, Path("doc.md"))
    assert any("AWS Access Key" in e for e in errs), errs


def test_generic_secret_in_non_markdown_is_flagged_inside_backticks() -> None:
    # Non-Markdown files do not get fence treatment: the assignment is flagged
    # regardless of surrounding triple-backtick lines.
    text = '```\npassword = "hunter2pass"\n```\n'
    errs = validate_skills.scan_text_for_secrets(text, Path("script.py"))
    assert any("Generic secret assignment" in e for e in errs), errs


def test_nested_example_fence_does_not_invert_state() -> None:
    # Mirrors the user-documentation skill: a ```markdown block that itself
    # shows ```bash examples must not invert fence state. The generic secret in
    # the later ```python block stays suppressed; the one in prose is flagged.
    text = (
        "# Doc\n\n"
        "```markdown\n"
        "Inside the markdown example, here is a shell block:\n"
        "```bash\n"
        'export TOKEN_VALUE="example-inside-md"\n'
        "```\n"
        "End of markdown example.\n"
        "```\n\n"
        "Now a real python usage block:\n\n"
        "```python\n"
        'client = Client(api_key="your-key-here")\n'
        "```\n\n"
        'And in prose: password = "leakedvalue123" should be flagged.\n'
    )
    errs = validate_skills.scan_text_for_secrets(text, Path("doc.md"))
    # exactly one finding: the prose assignment, not the two fenced examples.
    assert len(errs) == 1, errs
    assert "leakedvalue123" not in " ".join(errs)  # message names pattern, not value
    assert any("Generic secret assignment" in e for e in errs)
