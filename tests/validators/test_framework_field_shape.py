"""Tests for optional framework-mapping list-shape and membership validation.

The seven fields (`mitre_attack`, `atlas_techniques`, `d3fend_techniques`,
`nist_csf`, `nist_ai_rmf`, `mitre_f3`, `owasp_agentic`) are optional: absence
is never an error. A present value must be a YAML list. A scalar is a hard
error naming the skill and the field. The check runs in `--bundles-only`, the
mode `make validate` and CI invoke.

`owasp_agentic` (v4.8.0) additionally validates MEMBERSHIP of the closed
ASI01-ASI10 set, so those cases live here alongside the shape cases rather
than in a second file with a duplicate harness. The other six draw on
catalogs that grow between releases, where a membership check would reject a
newly published identifier; here a shape-only check would accept `ASI99`, and
a plausible-looking identifier in a compliance-facing matrix reads as
verified coverage.
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


def write_skill(root: Path, name: str, extra_lines: str = "") -> Path:
    d = root / "cat" / name
    d.mkdir(parents=True, exist_ok=True)
    extra = f"\n{extra_lines}" if extra_lines else ""
    (d / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: A skill used for testing framework field list shape here.\n"
        f'summary_l0: "Tests the {name} case"\n'
        f'overview_l1: "A longer paragraph about the {name} case for testing."\n'
        f"{extra.strip()}\n"
        "---\n" + BODY.format(name=name),
        encoding="utf-8",
    )
    return d


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--bundles-only",
            "--path",
            str(root / "cat"),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_absent_mitre_f3_is_valid(tmp_path: Path) -> None:
    write_skill(tmp_path, "no-framework-tags")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "must be a YAML list" not in result.stdout


def test_mitre_f3_list_is_valid(tmp_path: Path) -> None:
    write_skill(tmp_path, "tagged-f3", "mitre_f3: [F1005.006, F1010]")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_mitre_f3_scalar_is_an_error_naming_skill_and_field(tmp_path: Path) -> None:
    write_skill(tmp_path, "scalar-f3", "mitre_f3: F1005.006")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "mitre_f3" in result.stdout
    assert "scalar-f3" in result.stdout
    assert "must be a YAML list" in result.stdout


def test_block_sequence_is_a_valid_list(tmp_path: Path) -> None:
    write_skill(tmp_path, "block-list", "mitre_attack:\n  - T1071\n  - T1003.001")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_list_fields_still_pass(tmp_path: Path) -> None:
    write_skill(
        tmp_path,
        "already-tagged",
        "mitre_attack: [T1003.001]\nd3fend_techniques: [D3-PA]",
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


# --- owasp_agentic: shape AND closed-set membership (v4.8.0) ----------------


def test_absent_owasp_agentic_is_valid(tmp_path: Path) -> None:
    """Absence is never an error. Asserted on the error text rather than on the
    field name, which the validator's own banner mentions on a clean run too."""
    write_skill(tmp_path, "no-owasp-tag")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 errors" in result.stdout
    assert "unknown identifier" not in result.stdout
    assert "must be a YAML list" not in result.stdout


def test_owasp_agentic_valid_flow_list(tmp_path: Path) -> None:
    write_skill(tmp_path, "owasp-flow", "owasp_agentic: [ASI01, ASI10]")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_owasp_agentic_valid_block_sequence(tmp_path: Path) -> None:
    write_skill(tmp_path, "owasp-block", "owasp_agentic:\n  - ASI02\n  - ASI05")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_owasp_agentic_scalar_is_an_error_naming_skill_and_field(
    tmp_path: Path,
) -> None:
    write_skill(tmp_path, "owasp-scalar", "owasp_agentic: ASI01")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "owasp-scalar" in result.stdout
    assert "owasp_agentic" in result.stdout
    assert "must be a YAML list" in result.stdout


def test_owasp_agentic_out_of_range_id_is_an_error(tmp_path: Path) -> None:
    """The case a shape-only check would have accepted."""
    write_skill(tmp_path, "owasp-asi99", "owasp_agentic: [ASI99]")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "owasp-asi99" in result.stdout
    assert "owasp_agentic" in result.stdout
    assert "ASI99" in result.stdout
    assert "ASI01 through ASI10" in result.stdout


def test_owasp_agentic_zero_index_is_an_error(tmp_path: Path) -> None:
    """ASI00 looks well-formed and is not a real identifier."""
    write_skill(tmp_path, "owasp-asi00", "owasp_agentic: [ASI00]")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI00" in result.stdout


def test_owasp_agentic_unpadded_id_is_an_error(tmp_path: Path) -> None:
    """ASI1 is the natural typo for ASI01 and must not pass."""
    write_skill(tmp_path, "owasp-asi1", "owasp_agentic: [ASI1]")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI1" in result.stdout


def test_owasp_agentic_bad_id_in_block_sequence_is_an_error(tmp_path: Path) -> None:
    """Membership must be checked in both YAML shapes, not just the flow list."""
    write_skill(tmp_path, "owasp-bad-block", "owasp_agentic:\n  - ASI04\n  - NOPE")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "NOPE" in result.stdout


def test_owasp_agentic_duplicate_id_is_an_error(tmp_path: Path) -> None:
    """A duplicate would double-count the skill in the coverage matrix."""
    write_skill(tmp_path, "owasp-dupe", "owasp_agentic: [ASI03, ASI03]")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "owasp-dupe" in result.stdout
    assert "more than once" in result.stdout


def test_every_owasp_identifier_in_the_closed_set_is_accepted(tmp_path: Path) -> None:
    """All ten, so an off-by-one in the pattern cannot pass unnoticed."""
    ids = ", ".join(f"ASI{n:02d}" for n in range(1, 11))
    write_skill(tmp_path, "owasp-all-ten", f"owasp_agentic: [{ids}]")
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


# --- Adversarial findings from the v4.8.0 Tier 3 deep pass ------------------
#
# The membership check is bypassable if the validator's parser is NARROWER than
# the coverage builder's. build_framework_coverage.py matches the key with
# `line.strip()` (so it reads an indented key) and keeps the LAST occurrence
# (so a duplicate wins). Both inputs below put ASI99 into
# docs/framework-coverage.md while the validator reported PASS. The validator
# now scans every occurrence, indented ones included, and fails closed.


def test_adversarial_nested_owasp_key_is_still_validated(tmp_path: Path) -> None:
    """AF-1: the coverage builder reads an indented key that YAML would treat
    as nested. Skipping it here let an unverified identifier reach a
    compliance-facing document."""
    write_skill(tmp_path, "owasp-nested", "something:\n  owasp_agentic: [ASI99]")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI99" in result.stdout


def test_adversarial_nested_bare_scalar_is_still_validated(tmp_path: Path) -> None:
    """AF-1b: the second bypass route. The shape check skips indented lines, so
    a nested bare scalar reached the builder unchecked by either gate."""
    write_skill(tmp_path, "owasp-nested-scalar", "something:\n  owasp_agentic: ASI99")
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI99" in result.stdout


def test_adversarial_duplicate_key_validates_the_union(tmp_path: Path) -> None:
    """AF-2: the validator read the first occurrence, the builder rendered the
    last. Validating the union closes it in both orderings."""
    write_skill(
        tmp_path, "owasp-dupe-key", "owasp_agentic: [ASI01]\nowasp_agentic: [ASI99]"
    )
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI99" in result.stdout


def test_adversarial_duplicate_key_bad_first_also_fails(tmp_path: Path) -> None:
    """The reverse ordering, so the fix cannot be an off-by-one that happens to
    catch only the common case."""
    write_skill(
        tmp_path, "owasp-dupe-first", "owasp_agentic: [ASI99]\nowasp_agentic: [ASI01]"
    )
    result = run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ASI99" in result.stdout


def test_block_sequence_followed_by_another_key_does_not_leak(tmp_path: Path) -> None:
    """Regression on the widened scan: a block sequence must stop at the next
    key at the same indent, not swallow the following field's values."""
    write_skill(
        tmp_path, "owasp-block-then-key", "owasp_agentic:\n  - ASI03\nnist_csf: [DE.CM]"
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
