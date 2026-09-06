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


# ---------------------------------------------------------------------------
# Unfilled-placeholder lint (v3.15.2 Phase 2)
# ---------------------------------------------------------------------------

_FAKE_SKILL_FILE = Path("catalog/skills/x/some-skill/SKILL.md")


def _skill_with_body(name: str, description: str, body: str) -> str:
    """A structurally-complete SKILL.md with a caller-controlled body."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "summary_l0: A short summary.\n"
        "overview_l1: A short overview.\n"
        "---\n\n"
        f"{body}\n"
    )


def _placeholders(description: str = "A clean, filled-in description.", body: str = "Body.") -> list[str]:
    content = _skill_with_body("some-skill", description, body)
    fm = validate_skills.parse_frontmatter(content) or {}
    return validate_skills.validate_placeholders(_FAKE_SKILL_FILE, content, fm)


def test_placeholder_in_description_is_flagged() -> None:
    errs = _placeholders(description="<one sentence describing this skill>")
    assert any("description contains an unfilled template placeholder" in e for e in errs)


def test_placeholder_in_body_is_flagged() -> None:
    errs = _placeholders(body="This skill does <what this skill does> for you.")
    assert any("body contains an unfilled template placeholder" in e for e in errs)


def test_cli_notation_single_word_not_flagged() -> None:
    assert _placeholders(description="Save output to <path> for <name>.", body="Reads <category> input.") == []


def test_html_tags_not_flagged() -> None:
    body = 'Use <div> and <br/> and <a href="x"> and <img src="y" alt="z"> here.'
    assert _placeholders(body=body) == []


def test_uppercase_template_var_not_flagged() -> None:
    # docs/v<MAJOR>/ style version tokens are uppercase and single-token.
    assert _placeholders(description="Reorganize docs into a docs/v<MAJOR>/ layout.", body="See <MAJOR> here.") == []


def test_comparison_operators_not_flagged() -> None:
    assert _placeholders(body="Fire the check when x < y and y > z in the pipeline.") == []


def test_placeholder_in_fenced_code_not_flagged() -> None:
    body = "Example scaffold:\n\n```\n<what this does>\n```\n\nDone."
    assert _placeholders(body=body) == []


def test_placeholder_in_inline_code_not_flagged() -> None:
    assert _placeholders(body="Write a description like `<one sentence here>` in the file.") == []


def test_description_placeholder_in_backticks_is_exempt() -> None:
    assert _placeholders(description="Author a form such as `<multi word example>` inline.") == []


def test_nested_fence_does_not_leak_placeholder() -> None:
    # Mirrors the secret-scan nested-fence guard. A markdown code block that
    # itself shows a ```bash example must use a LONGER outer fence (CommonMark:
    # fences do not nest; a shorter inner fence cannot close a longer outer one),
    # so the inner ``` markers stay content and only the prose placeholder
    # outside every fence is flagged.
    body = (
        "````markdown\n"
        "Inside the md example:\n"
        "```bash\n"
        "echo <do a thing>\n"
        "```\n"
        "end of example.\n"
        "````\n\n"
        "Now in prose: fill in <the actual placeholder here> please.\n"
    )
    errs = _placeholders(body=body)
    assert len(errs) == 1, errs
    assert "the actual placeholder here" in errs[0]


def test_body_after_frontmatter_excludes_frontmatter() -> None:
    content = _skill_with_body("some-skill", "desc", "# Title\n\nHello body.")
    body = validate_skills._body_after_frontmatter(content)
    assert "Hello body." in body
    assert "name: some-skill" not in body


def test_body_after_frontmatter_without_frontmatter_returns_all() -> None:
    # No leading `---`: the whole content is treated as body (defensive fallback).
    assert validate_skills._body_after_frontmatter("no frontmatter here") == "no frontmatter here"


def test_bundles_only_flags_placeholder_via_cli(tmp_path: Path) -> None:
    skill_dir = tmp_path / "scaffold-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        _skill_with_body("scaffold-skill", "A clean description.", "It does <what it does> now."),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--bundles-only", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1, result.stdout
    assert "unfilled template placeholder" in result.stdout


def test_bundles_only_clean_skill_passes_via_cli(tmp_path: Path) -> None:
    skill_dir = tmp_path / "clean-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        _skill_with_body("clean-skill", "A clean, filled-in description.", "Reads <path> and writes output."),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--bundles-only", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout


# ---------------------------------------------------------------------------
# Malformed skill directories (v3.15.9 Phase 7)
#
# `find_skill_dirs` locates skills BY their SKILL.md, so a `<category>/<name>/`
# folder without one is invisible to every per-skill check -- silently skipped
# here while the installers used to silently ship it. The two gates disagreed
# about what a skill directory is. These tests pin the agreement: the validator
# reports it, and it stays a WARNING so a work-in-progress branch still passes.
# ---------------------------------------------------------------------------


def _catalog_with_scaffold(root: Path) -> Path:
    """One valid skill plus one scaffold that never got a SKILL.md."""
    skills = root / "skills"
    good = skills / "workflow" / "good-skill"
    good.mkdir(parents=True)
    (good / "SKILL.md").write_text(
        _skill_with_body(
            "good-skill", "A clean, filled-in description.", "Reads <path>."
        ),
        encoding="utf-8",
    )
    (skills / "workflow" / "abandoned-scaffold").mkdir(parents=True)
    return skills


def test_find_malformed_skill_dirs_flags_missing_skill_md(tmp_path: Path):
    validator = _load_validator()
    skills = _catalog_with_scaffold(tmp_path)

    found = [p.name for p in validator.find_malformed_skill_dirs(skills)]

    assert found == ["abandoned-scaffold"]


def test_find_malformed_skill_dirs_ignores_bundle_subdirs_of_a_single_skill(
    tmp_path: Path,
):
    """Pointing --path at one skill folder must not flag its bundled subdirs.

    `scripts/`, `references/`, `assets/`, and `evals/` are bundle directories,
    not skills; treating them as skills would emit noise for every skill that
    ships resources.
    """
    validator = _load_validator()
    skill = tmp_path / "solo-skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text(
        _skill_with_body(
            "solo-skill", "A clean, filled-in description.", "Reads <path>."
        ),
        encoding="utf-8",
    )

    assert validator.find_malformed_skill_dirs(skill) == []


def test_malformed_skill_dir_warns_but_does_not_fail_the_gate(tmp_path: Path):
    """The CLI surface reports it and still exits 0 (WIP branches must pass)."""
    skills = _catalog_with_scaffold(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--bundles-only",
            "--verbose",
            "--path",
            str(skills),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stdout
    assert "abandoned-scaffold" in result.stdout
    assert "has no SKILL.md" in result.stdout


def _padded_skill(name: str, body_lines: int) -> str:
    """SKILL.md whose body (after frontmatter) is exactly `body_lines` lines."""
    lines = [f"# {name}", "", "Body."]
    while len(lines) < body_lines:
        lines.append("padding")
    lines = lines[:body_lines]
    return (
        "---\n"
        f"name: {name}\n"
        "description: A concise single-line description.\n"
        'summary_l0: "short summary"\n'
        'overview_l1: "short overview"\n'
        "---\n"
        + "\n".join(lines)
        + "\n"
    )


def test_count_body_lines_excludes_frontmatter() -> None:
    content = _padded_skill("size-skill", 10)
    # Frontmatter is 6 lines plus fences; body must still report 10.
    assert validate_skills.count_body_lines(content) == 10


def test_body_at_hard_cap_is_ok(tmp_path: Path) -> None:
    skill = tmp_path / "cap-skill"
    skill.mkdir()
    content = _padded_skill("cap-skill", 800)
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    errors, warnings = validate_skills.validate_body_size(skill / "SKILL.md", content)
    assert errors == []
    # 800 is still over the 500 warning tier; that is a grandfathered warning, not an error.
    assert any("800 lines" in w for w in warnings)


def test_body_over_soft_cap_warns(tmp_path: Path) -> None:
    skill = tmp_path / "warn-skill"
    skill.mkdir()
    content = _padded_skill("warn-skill", 501)
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    errors, warnings = validate_skills.validate_body_size(skill / "SKILL.md", content)
    assert errors == []
    assert any("501 lines" in w and "soft cap 500" in w for w in warnings)


def test_body_over_hard_cap_is_error(tmp_path: Path) -> None:
    skill = tmp_path / "over-skill"
    skill.mkdir()
    content = _padded_skill("over-skill", 801)
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    errors, warnings = validate_skills.validate_body_size(skill / "SKILL.md", content)
    assert any("801 lines" in e and "hard cap 800" in e for e in errors)


def test_bundles_only_fails_when_body_exceeds_hard_cap(tmp_path: Path) -> None:
    skills = tmp_path / "catalog"
    skill = skills / "over-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(_padded_skill("over-skill", 801), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--bundles-only",
            "--path",
            str(skills),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 1, result.stdout
    assert "hard cap 800" in result.stdout
