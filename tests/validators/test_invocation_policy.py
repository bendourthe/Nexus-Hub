"""Tests for the optional invocation-policy frontmatter fields (v3.17.5 Phase 6).

Two properties matter and pull in opposite directions. The fields are OPTIONAL,
so 273 existing skills that declare neither must pass untouched -- an optional
field that breaks the catalog on absence is a required field with a friendlier
name. And a declared field must be a real boolean, because `user-invocable:
"true"` is a string that reads as correct and behaves as unset.

The invalid-combination rule is a Nexus-Hub addition, not a vendor rule: Claude
documents each field independently, and nothing upstream forbids setting both.
Setting both leaves a skill nobody can invoke, so the catalog refuses it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "validate_skills.py"

BODY = """
# {name}

## When to Use This Skill

Use it when testing.

## Instructions

Do the thing.

## Verification

- [ ] It worked.
"""


def write_skill(root: Path, name: str, policy_lines: str = "") -> Path:
    d = root / "cat" / name
    d.mkdir(parents=True, exist_ok=True)
    extra = f"\n{policy_lines}" if policy_lines else ""
    (d / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: A skill used for testing the invocation policy fields here.\n"
        f'summary_l0: "Tests the {name} case"\n'
        f'overview_l1: "A longer paragraph about the {name} case for testing."\n'
        f"{extra.strip()}\n"
        "---\n" + BODY.format(name=name),
        encoding="utf-8",
    )
    return d


def run(root: Path, *, verbose: bool = False) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--bundles-only",
        "--path",
        str(root / "cat"),
    ]
    if verbose:
        cmd.append("--verbose")
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_absent_fields_are_the_valid_default(tmp_path):
    """The 273-skill property: declaring neither field must pass silently."""
    write_skill(tmp_path, "no-policy")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "invocable" not in result.stdout


def test_model_invocation_disabled_alone_is_valid(tmp_path):
    write_skill(tmp_path, "manual-only", "disable-model-invocation: true")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_user_invocable_false_alone_is_valid(tmp_path):
    """Background knowledge the model loads but users should not invoke."""
    write_skill(tmp_path, "background", "user-invocable: false")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_both_false_defaults_are_valid(tmp_path):
    write_skill(
        tmp_path,
        "explicit-defaults",
        "disable-model-invocation: false\nuser-invocable: true",
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_manual_only_but_still_user_invocable_is_valid(tmp_path):
    write_skill(
        tmp_path,
        "slash-only",
        "disable-model-invocation: true\nuser-invocable: true",
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_quoted_true_is_a_type_error(tmp_path):
    """A string that reads as correct and behaves as unset."""
    write_skill(tmp_path, "quoted", 'user-invocable: "true"')
    result = run(tmp_path)
    assert result.returncode == 1
    assert "must be a boolean" in result.stdout
    # The check is a literal scan (no PyYAML), so it reports the raw
    # right-hand side rather than a YAML type name.
    assert "true" in result.stdout


def test_integer_is_a_type_error(tmp_path):
    write_skill(tmp_path, "numeric", "disable-model-invocation: 1")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "must be a boolean" in result.stdout
    assert "1" in result.stdout


def test_yes_string_is_a_type_error(tmp_path):
    """YAML 1.1 would coerce bare yes to True; the strict parser must not."""
    write_skill(tmp_path, "yesno", 'disable-model-invocation: "yes"')
    result = run(tmp_path)
    assert result.returncode == 1
    assert "must be a boolean" in result.stdout


def test_the_field_name_is_reported_so_the_author_knows_which_one(tmp_path):
    write_skill(tmp_path, "which", 'disable-model-invocation: "true"')
    result = run(tmp_path)
    assert result.returncode == 1
    assert "'disable-model-invocation'" in result.stdout


def test_invocable_by_nobody_is_a_hard_error(tmp_path):
    write_skill(
        tmp_path,
        "invisible",
        "disable-model-invocation: true\nuser-invocable: false",
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "invocable by nobody" in result.stdout
    assert "must remain user-invocable" in result.stdout


def test_both_violations_are_reported_together(tmp_path):
    write_skill(tmp_path, "bad-type", 'user-invocable: "true"')
    write_skill(
        tmp_path,
        "bad-combo",
        "disable-model-invocation: true\nuser-invocable: false",
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "must be a boolean" in result.stdout
    assert "invocable by nobody" in result.stdout


def test_the_shipped_catalog_passes_untouched():
    """No existing skill declares these fields; all 273 must still validate."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--bundles-only"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_slash_dispatcher_description_without_flag_is_a_warning(tmp_path):
    """A hand-authored 'Run the /X command' skill without the flag is suspicious."""
    d = tmp_path / "cat" / "plan-wrapper"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\n"
        "name: plan-wrapper\n"
        "description: Run the /plan command. Thin dispatcher for the plan skill.\n"
        'summary_l0: "Wraps the plan command"\n'
        'overview_l1: "A longer paragraph about wrapping the plan command for tests."\n'
        "---\n" + BODY.format(name="plan-wrapper"),
        encoding="utf-8",
    )
    result = run(tmp_path, verbose=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Run the /X command" in result.stdout
    assert "user-invoked only" in result.stdout


def test_slash_dispatcher_description_with_flag_is_silent(tmp_path):
    d = tmp_path / "cat" / "plan-wrapper"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\n"
        "name: plan-wrapper\n"
        "description: Run the /plan command. Thin dispatcher for the plan skill.\n"
        "disable-model-invocation: true\n"
        'summary_l0: "Wraps the plan command"\n'
        'overview_l1: "A longer paragraph about wrapping the plan command for tests."\n'
        "---\n" + BODY.format(name="plan-wrapper"),
        encoding="utf-8",
    )
    result = run(tmp_path, verbose=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Run the /X command" not in result.stdout
