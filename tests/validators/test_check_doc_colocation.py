"""Tests for scripts/check_doc_colocation.py.

The three `test_defect_*` cases below each encode a fail-open the inline bash
implementation shipped with. Every one of them PASSED the old check while
checking nothing, so each test is written so that it would fail against the old
behavior and passes only against the current script.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_doc_colocation.py"

PLAN = """# Plan - Example

**Project**: Nexus-Hub
**Target version**: {target}
**Seeded from**: {seed}
"""

COMPARISON = """# Comparison - Example

**Adoption target**: {target}
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        cwd=str(root),
        check=False,  # the return code IS the assertion under test
    )


# --------------------------------------------------------------------------
# Baseline behavior
# --------------------------------------------------------------------------


def test_no_docs_tree_is_clean(tmp_path: Path) -> None:
    r = run(tmp_path)
    assert r.returncode == 0
    assert "nothing to check" in r.stdout


def test_colocated_pair_passes(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.19/plans/p.md",
          PLAN.format(target="v3.19.0", seed="docs/v3/v3.19/comparisons/c.md"))
    write(tmp_path / "docs/v3/v3.19/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout
    assert "OK:" in r.stdout


def test_plan_in_wrong_version_dir_fails(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.18/plans/p.md",
          PLAN.format(target="v3.19.0", seed="docs/v3/v3.19/comparisons/c.md"))
    write(tmp_path / "docs/v3/v3.19/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "MISMATCH (plan/comparison)" in r.stdout


def test_comparison_in_wrong_dir_for_its_target_fails(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.18/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "MISMATCH (comparison placement)" in r.stdout
    assert "docs/v3/v3.19" in r.stdout


# --------------------------------------------------------------------------
# Defect 1: only the highest major was scanned
# --------------------------------------------------------------------------


def test_defect_1_lower_major_still_scanned_when_higher_exists(tmp_path: Path) -> None:
    """A v3 violation must be caught even though a docs/v4 tree exists.

    Old behavior: CURRENT_MAJOR resolved to 4 via `sort -n | tail -1`, the find
    was scoped to docs/v4, and this violation reported CLEAN.
    """
    write(tmp_path / "docs/v3/v3.18/plans/p.md",
          PLAN.format(target="v3.19.0", seed="docs/v3/v3.19/comparisons/c.md"))
    write(tmp_path / "docs/v3/v3.19/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    write(tmp_path / "docs/v4/v4.0/plans/q.md",
          PLAN.format(target="v4.0.0", seed="docs/v4/v4.0/comparisons/d.md"))
    write(tmp_path / "docs/v4/v4.0/comparisons/d.md",
          COMPARISON.format(target="v4.0.0"))

    r = run(tmp_path)
    assert r.returncode == 1, r.stdout
    assert "MISMATCH (plan/comparison)" in r.stdout
    assert "docs/v3/v3.18/plans/p.md" in r.stdout


def test_defect_1_every_major_named_in_banner(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.19/plans/.keep", "")
    write(tmp_path / "docs/v4/v4.0/plans/.keep", "")
    r = run(tmp_path)
    assert r.returncode == 0
    assert "docs/v3" in r.stdout and "docs/v4" in r.stdout


# --------------------------------------------------------------------------
# Defect 2: a dangling `Seeded from` passed
# --------------------------------------------------------------------------


def test_defect_2_dangling_seed_fails(tmp_path: Path) -> None:
    """A cited comparison that does not exist must fail.

    Old behavior: the version directory was parsed out of the path STRING and
    compared, so a nonexistent file whose path sat in the right directory
    passed. Two real plans shipped in that state.
    """
    write(tmp_path / "docs/v3/v3.19/plans/p.md",
          PLAN.format(target="v3.19.0",
                      seed="docs/v3/v3.19/comparisons/does-not-exist.md"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "MISMATCH (dangling seed)" in r.stdout


def test_defect_2_dangling_seed_beats_matching_directory(tmp_path: Path) -> None:
    """The directory matching must not excuse a missing file."""
    write(tmp_path / "docs/v3/v3.19/plans/p.md",
          PLAN.format(target="v3.19.0", seed="docs/v3/v3.19/comparisons/ghost.md"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "dangling" in r.stdout
    assert "MISMATCH (plan/comparison)" not in r.stdout


# --------------------------------------------------------------------------
# Defect 3: relative `Seeded from` paths were skipped entirely
# --------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [
    "../comparisons/c.md",
    "[../comparisons/c.md](../comparisons/c.md)",
    "`../comparisons/c.md`",
])
def test_defect_3_relative_seed_is_resolved_and_checked(tmp_path: Path, seed: str) -> None:
    """A relative seed must be resolved against the plan's directory.

    Old behavior: the extraction regex required a literal `docs/v` prefix, so a
    relative reference produced an empty match and the plan was skipped. This
    plan sits in v3.18 and its comparison in v3.18, but the comparison declares
    a v3.19 target, so Direction 2 must fire.
    """
    write(tmp_path / "docs/v3/v3.18/plans/p.md",
          PLAN.format(target="v3.19.0", seed=seed))
    write(tmp_path / "docs/v3/v3.18/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    r = run(tmp_path)
    assert r.returncode == 1, r.stdout
    assert "MISMATCH (comparison placement)" in r.stdout


def test_defect_3_relative_dangling_seed_fails(tmp_path: Path) -> None:
    """The exact shape that shipped broken: a relative path to a missing file."""
    write(tmp_path / "docs/v3/v3.18/plans/p.md",
          PLAN.format(target="v3.19.0",
                      seed="[../comparisons/v3.18.0-comparison-oldslug.md]"
                           "(../comparisons/v3.18.0-comparison-oldslug.md)"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "MISMATCH (dangling seed)" in r.stdout
    assert "v3.18.0-comparison-oldslug.md" in r.stdout


def test_defect_3_relative_seed_crossing_versions_is_caught(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.18/plans/p.md",
          PLAN.format(target="v3.19.0", seed="../../v3.19/comparisons/c.md"))
    write(tmp_path / "docs/v3/v3.19/comparisons/c.md",
          COMPARISON.format(target="v3.19.0"))
    r = run(tmp_path)
    assert r.returncode == 1
    assert "MISMATCH (plan/comparison)" in r.stdout


# --------------------------------------------------------------------------
# Grandfathering that must be preserved
# --------------------------------------------------------------------------


def test_plan_without_seeded_from_is_skipped(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.18/plans/p.md", "# Plan\n\n**Target version**: v3.19.0\n")
    assert run(tmp_path).returncode == 0


def test_non_comparison_seed_is_not_a_violation(tmp_path: Path) -> None:
    """A plan seeded from a research doc or a release session has no duty."""
    for seed in ("`docs/v3/v3.19/research/notes.md`",
                 "the v3.17.5 release session, which produced seven instances",
                 "maintainer UX report against the shipped 0.1.0 build"):
        root = tmp_path / f"case{abs(hash(seed))}"
        write(root / "docs/v3/v3.18/plans/p.md",
              PLAN.format(target="v3.19.0", seed=seed))
        r = run(root)
        assert r.returncode == 0, f"{seed} -> {r.stdout}"


def test_legacy_comparison_without_adoption_target_is_a_note(tmp_path: Path) -> None:
    write(tmp_path / "docs/v3/v3.9/comparisons/legacy.md", "# Comparison\n\nNo target field.\n")
    r = run(tmp_path, "--verbose")
    assert r.returncode == 0
    assert "legacy comparison with no Adoption target" in r.stdout


def test_archive_tree_is_out_of_scope(tmp_path: Path) -> None:
    """docs/archive/** is grandfathered by not being under a docs/v<N> root."""
    write(tmp_path / "docs/archive/versions/v2/plans/old.md",
          PLAN.format(target="v2.0.0", seed="docs/v2/v2.0/comparisons/gone.md"))
    assert run(tmp_path).returncode == 0


# --------------------------------------------------------------------------
# The live repository must be clean
# --------------------------------------------------------------------------


def test_repository_is_colocated() -> None:
    r = run(REPO_ROOT)
    assert r.returncode == 0, r.stdout


def test_workflow_invokes_the_script_and_is_unfiltered() -> None:
    """The required `colocation` context must stay unconditionally produced."""
    wf = (REPO_ROOT / ".github/workflows/doc-colocation.yml").read_text(encoding="utf-8")
    assert "scripts/check_doc_colocation.py" in wf
    assert "paths:" not in wf, "workflow-level path filtering leaves the required check Pending forever"
