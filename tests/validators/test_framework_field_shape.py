"""Tests for optional framework-mapping list-shape validation.

The six fields (`mitre_attack`, `atlas_techniques`, `d3fend_techniques`,
`nist_csf`, `nist_ai_rmf`, `mitre_f3`) are optional: absence is never an
error. A present value must be a YAML list. A scalar is a hard error naming
the skill and the field. The check runs in `--bundles-only`, the mode
`make validate` and CI invoke.
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
