"""Tests for scripts/validate_decision_records.py.

The guard's whole value is that `rejected/` can be grepped before someone
re-proposes a declined design, and that every record says what its choice beat.
Both properties fail silently: a misfiled record still looks filed, and a
record with no alternatives still looks complete. So these tests assert failure
in both directions -- a well-formed record in each lifecycle passes, and each
individual defect exits non-zero with a message naming the offending path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "validate_decision_records.py"

PROPOSED = """# Decision: Do the thing

Status: proposed - awaiting a call

## Problem

The thing is not done.

## Proposal

Do the thing.

## Alternatives considered

- Not doing the thing. Rejected because the thing needs doing.

## Acceptance criteria

The thing is done.

## Risks

The thing might not work.
"""

IMPLEMENTED = """# Decision: Do the thing

Status: implemented - the thing is done

## Problem

The thing was not done.

## Decision

We do the thing.

## Alternatives considered

- Not doing the thing. Rejected because the thing needed doing.

## Consequences

The thing is now done, and undoing it would cost a migration.
"""

REJECTED = """# Decision: Do the other thing

Status: rejected - it presupposed a runtime we declined

## Problem

The other thing was not done.

## Proposal

Do the other thing.

## Alternatives considered

- Doing the first thing instead. This is what won.

## Acceptance criteria

The other thing is done.
"""

BODIES = {"proposed": PROPOSED, "implemented": IMPLEMENTED, "rejected": REJECTED}


def run(decisions_dir: Path, root: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT), "--decisions-dir", str(decisions_dir)]
    if root is not None:
        cmd += ["--root", str(root)]
    return subprocess.run(cmd, capture_output=True, text=True)


def write(base: Path, rel: str, body: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_a_valid_record_in_each_lifecycle_passes(tmp_path):
    for lifecycle, body in BODIES.items():
        write(tmp_path, f"{lifecycle}/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "3 decision record(s) OK" in result.stdout


def test_readme_at_the_root_is_not_treated_as_a_record(tmp_path):
    write(tmp_path, "README.md", "# Decision Records\n\nNot a record.\n")
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "1 decision record(s) OK" in result.stdout


def test_absent_tree_is_a_no_op(tmp_path):
    result = run(tmp_path / "nope", root=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "nothing to check" in result.stdout


def test_wrong_depth_fails(tmp_path):
    write(tmp_path, "implemented/2026-01-01-no-class.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "expected exactly" in result.stderr
    assert "2 path segment(s)" in result.stderr


def test_too_deep_fails(tmp_path):
    write(tmp_path, "implemented/policy/sub/2026-01-01-too-deep.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "4 path segment(s)" in result.stderr


def test_unknown_lifecycle_fails(tmp_path):
    write(tmp_path, "accepted/policy/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "unknown lifecycle 'accepted'" in result.stderr


def test_unknown_class_fails_and_explains_the_missing_feature_class(tmp_path):
    write(tmp_path, "implemented/feature/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "unknown class 'feature'" in result.stderr
    assert "feature intent lives in plans" in result.stderr


def test_bad_filename_date_fails(tmp_path):
    write(tmp_path, "implemented/policy/jan-1-2026-a-decision.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "YYYY-MM-DD-<kebab-slug>.md" in result.stderr


def test_uppercase_slug_fails(tmp_path):
    write(tmp_path, "implemented/policy/2026-01-01-A-Decision.md", IMPLEMENTED)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "YYYY-MM-DD-<kebab-slug>.md" in result.stderr


def test_status_folder_mismatch_fails(tmp_path):
    body = IMPLEMENTED.replace(
        "Status: implemented - the thing is done",
        "Status: proposed - the thing is done",
    )
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "Status says 'proposed' but the file sits in 'implemented'" in result.stderr


def test_missing_alternatives_fails_in_every_lifecycle(tmp_path):
    for lifecycle, body in BODIES.items():
        stripped = body.replace("## Alternatives considered", "## Something else")
        write(tmp_path, f"{lifecycle}/policy/2026-01-01-a-decision.md", stripped)
    result = run(tmp_path)
    assert result.returncode == 1
    for lifecycle in BODIES:
        assert f"{lifecycle}/policy/2026-01-01-a-decision.md" in result.stderr
    assert result.stderr.count("Alternatives considered") >= 3


def test_missing_consequences_fails_in_implemented(tmp_path):
    body = IMPLEMENTED.replace("## Consequences", "## Outcome")
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "'## Consequences'" in result.stderr


def test_proposal_headings_are_rejected_inside_implemented(tmp_path):
    body = IMPLEMENTED + "\n## Proposal\n\nWe should do the thing.\n"
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "'## Proposal' describes work that has not happened yet" in result.stderr
    assert "becomes '## Decision' in the present tense" in result.stderr


def test_proposal_headings_are_allowed_in_rejected(tmp_path):
    """A rejected record is the FROZEN proposal; its pitch headings must survive."""
    write(tmp_path, "rejected/policy/2026-01-01-a-decision.md", REJECTED)
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_malformed_header_lines_fail(tmp_path):
    body = IMPLEMENTED.replace("# Decision: Do the thing", "# Do the thing")
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "line 1 must be" in result.stderr


def test_non_blank_second_line_fails(tmp_path):
    body = IMPLEMENTED.replace(
        "# Decision: Do the thing\n\nStatus:",
        "# Decision: Do the thing\nStatus:",
    )
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "must be blank" in result.stderr or "line 3 must be" in result.stderr


def test_status_without_a_summary_fails(tmp_path):
    body = IMPLEMENTED.replace(
        "Status: implemented - the thing is done", "Status: implemented"
    )
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "line 3 must be" in result.stderr


def test_file_shorter_than_the_header_fails_without_a_traceback(tmp_path):
    write(tmp_path, "implemented/policy/2026-01-01-a-decision.md", "# Decision: x\n")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "shorter than the required 3-line header" in result.stderr
    assert "Traceback" not in result.stderr


def test_all_failures_are_collected_before_the_single_exit(tmp_path):
    """One bad record must not mask another -- the point of collecting."""
    write(tmp_path, "implemented/feature/2026-01-01-bad-class.md", IMPLEMENTED)
    write(tmp_path, "implemented/policy/nope.md", IMPLEMENTED)
    write(
        tmp_path,
        "implemented/policy/2026-01-01-no-alts.md",
        IMPLEMENTED.replace("## Alternatives considered", "## Nope"),
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "unknown class 'feature'" in result.stderr
    assert "YYYY-MM-DD-<kebab-slug>.md" in result.stderr
    assert "Alternatives considered" in result.stderr


def test_a_legacy_location_holding_records_fails_with_a_relocation_hint(tmp_path):
    legacy = tmp_path / "docs" / "rfc"
    legacy.mkdir(parents=True)
    (legacy / "0001-something.md").write_text("# Decision: old\n", encoding="utf-8")
    decisions = tmp_path / "docs" / "decisions"
    write(decisions, "implemented/policy/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(decisions, root=tmp_path)
    assert result.returncode == 1
    assert "docs/rfc/" in result.stderr
    assert "relocate" in result.stderr


def test_a_resurrected_memory_decisions_file_fails(tmp_path):
    memory = tmp_path / ".claude" / "memory"
    memory.mkdir(parents=True)
    (memory / "decisions.md").write_text(
        "# Decision: snuck back in\n\nStatus: implemented - nope\n", encoding="utf-8"
    )
    decisions = tmp_path / "docs" / "decisions"
    write(decisions, "implemented/policy/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(decisions, root=tmp_path)
    assert result.returncode == 1
    assert ".claude/memory/decisions.md" in result.stderr


def test_a_memory_file_without_a_record_is_left_alone(tmp_path):
    """The distributed ADR template is not a record; it must not trip the guard."""
    memory = tmp_path / ".claude" / "memory"
    memory.mkdir(parents=True)
    (memory / "decisions.md").write_text(
        "# Architecture Decision Records\n\n### ADR-XXX: [Decision Title]\n",
        encoding="utf-8",
    )
    decisions = tmp_path / "docs" / "decisions"
    write(decisions, "implemented/policy/2026-01-01-a-decision.md", IMPLEMENTED)
    result = run(decisions, root=tmp_path)
    assert result.returncode == 0, result.stderr


def test_the_shipped_tree_passes():
    """The real repo tree must be green, or the gate cannot be merged."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_the_shipped_tree_seeds_the_rejected_lifecycle():
    """`rejected/` is the highest-value folder; an empty one defeats the purpose."""
    rejected = REPO_ROOT / "docs" / "decisions" / "rejected"
    records = list(rejected.rglob("*.md"))
    assert len(records) >= 2, (
        "the rejected lifecycle must ship seeded with real declined designs, "
        "or nobody will think to grep it before re-proposing one"
    )
