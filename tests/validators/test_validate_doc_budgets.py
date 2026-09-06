"""Tests for scripts/validate_doc_budgets.py.

The guard exists so that always-loaded instruction docs cannot grow unmeasured.
A budget gate proven only on the happy path is worthless: it would pass just as
happily if it never read the files at all. These tests therefore assert failure
in BOTH directions -- a compliant manifest passes, and each individual defect
(bad ceiling, duplicate key, missing file, over budget) exits non-zero with its
labeled class -- plus the collection property, that one failure does not mask
another.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "validate_doc_budgets.py"


def run(root: Path, manifest: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--manifest",
            str(manifest),
            *extra,
        ],
        capture_output=True,
        text=True,
    )


def build(tmp_path: Path, docs: dict[str, int], manifest: object) -> tuple[Path, Path]:
    """Create a fake repo root with `docs` (path -> word count) and a manifest.

    Returns (root, manifest_path). `manifest` is written as JSON when it is not
    already a string, so a test can inject deliberately malformed content.
    """
    root = tmp_path / "repo"
    root.mkdir(exist_ok=True)
    for rel, words in docs.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(" ".join(["word"] * words), encoding="utf-8")

    manifest_path = tmp_path / "doc-budgets.json"
    text = manifest if isinstance(manifest, str) else json.dumps(manifest)
    manifest_path.write_text(text, encoding="utf-8")
    return root, manifest_path


def test_all_within_ceiling_passes(tmp_path):
    root, manifest = build(
        tmp_path,
        {"AGENTS.md": 90, "CLAUDE.md": 40},
        {"AGENTS.md": 100, "CLAUDE.md": 50},
    )
    result = run(root, manifest)
    assert result.returncode == 0, result.stderr
    assert "2 budgeted doc(s) within ceiling" in result.stdout


def test_word_count_at_exactly_the_ceiling_passes(tmp_path):
    """The ceiling is inclusive: `words > ceiling` fails, `words == ceiling` does not."""
    root, manifest = build(tmp_path, {"AGENTS.md": 100}, {"AGENTS.md": 100})
    result = run(root, manifest)
    assert result.returncode == 0, result.stderr


def test_over_budget_fails_with_counts_and_no_raise_suggestion(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 130}, {"AGENTS.md": 100})
    result = run(root, manifest)
    assert result.returncode == 1
    assert "OVER AGENTS.md" in result.stderr
    assert "130 words exceeds the 100 ceiling by 30" in result.stderr
    # The cheap fix must stay the obvious one.
    assert "Relocate or condense" in result.stderr
    assert "requires justification in the PR" in result.stderr


def test_missing_budgeted_file_is_a_failure_not_a_silent_skip(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {"AGENTS.md": 100, "GONE.md": 100})
    result = run(root, manifest)
    assert result.returncode == 1
    assert "MISS GONE.md" in result.stderr
    assert "update the manifest in the same change" in result.stderr


def test_non_integer_ceiling_is_bad(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {"AGENTS.md": "lots"})
    result = run(root, manifest)
    assert result.returncode == 1
    assert "BAD  AGENTS.md" in result.stderr
    assert "positive integer" in result.stderr


def test_zero_and_negative_ceilings_are_bad(tmp_path):
    root, manifest = build(
        tmp_path, {"A.md": 10, "B.md": 10}, {"A.md": 0, "B.md": -5}
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "BAD  A.md" in result.stderr
    assert "BAD  B.md" in result.stderr


def test_boolean_ceiling_is_bad_despite_bool_subclassing_int(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {"AGENTS.md": True})
    result = run(root, manifest)
    assert result.returncode == 1
    assert "BAD  AGENTS.md" in result.stderr


def test_literal_duplicate_json_key_is_a_dupe(tmp_path):
    root, manifest = build(
        tmp_path,
        {"AGENTS.md": 10},
        '{"AGENTS.md": 100, "AGENTS.md": 999}',
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "DUPE AGENTS.md" in result.stderr


def test_paths_that_normalize_equal_are_a_dupe(tmp_path):
    root, manifest = build(
        tmp_path,
        {"AGENTS.md": 10},
        '{"AGENTS.md": 100, "./AGENTS.md": 200}',
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "DUPE AGENTS.md" in result.stderr
    assert "normalize to the same file" in result.stderr


def test_windows_separators_normalize_to_the_same_file(tmp_path):
    root, manifest = build(
        tmp_path,
        {"templates/base.md": 10},
        '{"templates/base.md": 100, "templates\\\\base.md": 200}',
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "DUPE templates/base.md" in result.stderr


def test_malformed_json_exits_one_without_a_traceback(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, "{not json")
    result = run(root, manifest)
    assert result.returncode == 1
    assert "not valid JSON" in result.stderr
    assert "Traceback" not in result.stderr


def test_absent_manifest_exits_one_without_a_traceback(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {"AGENTS.md": 100})
    manifest.unlink()
    result = run(root, manifest)
    assert result.returncode == 1
    assert "manifest not found" in result.stderr
    assert "Traceback" not in result.stderr


def test_non_object_manifest_is_bad(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, ["AGENTS.md"])
    result = run(root, manifest)
    assert result.returncode == 1
    assert "expected a JSON object" in result.stderr


def test_empty_manifest_is_bad(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {})
    result = run(root, manifest)
    assert result.returncode == 1
    assert "lists no budgeted docs" in result.stderr


def test_underscore_keys_are_comments_not_budgets(tmp_path):
    root, manifest = build(
        tmp_path,
        {"AGENTS.md": 10},
        {"_note": "policy lives in doc-budgets.md", "AGENTS.md": 100},
    )
    result = run(root, manifest)
    assert result.returncode == 0, result.stderr
    assert "1 budgeted doc(s) within ceiling" in result.stdout


def test_all_failures_are_collected_before_the_single_exit(tmp_path):
    """One bad entry must not mask another -- the whole point of collecting."""
    root, manifest = build(
        tmp_path,
        {"OVER.md": 130, "OK.md": 10},
        {"OVER.md": 100, "GONE.md": 100, "OK.md": 100},
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "OVER OVER.md" in result.stderr
    assert "MISS GONE.md" in result.stderr


def test_bad_entries_are_all_reported_together(tmp_path):
    root, manifest = build(
        tmp_path,
        {"A.md": 10, "B.md": 10},
        {"A.md": "nope", "B.md": -1},
    )
    result = run(root, manifest)
    assert result.returncode == 1
    assert "BAD  A.md" in result.stderr
    assert "BAD  B.md" in result.stderr


def test_list_prints_the_usage_table_and_exits_zero_even_when_over(tmp_path):
    """--list is a reporting mode, not a gate; it must not fail on an OVER doc."""
    root, manifest = build(tmp_path, {"AGENTS.md": 130}, {"AGENTS.md": 100})
    result = run(root, manifest, "--list")
    assert result.returncode == 0, result.stderr
    assert "PATH" in result.stdout
    assert "WORDS" in result.stdout
    assert "CEILING" in result.stdout
    assert "HEADROOM" in result.stdout
    assert "AGENTS.md" in result.stdout
    assert "-30" in result.stdout


def test_list_flags_a_budget_with_under_five_percent_headroom(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 98}, {"AGENTS.md": 100})
    result = run(root, manifest, "--list")
    assert result.returncode == 0, result.stderr
    assert "tight" in result.stdout


def test_list_does_not_flag_a_healthy_headroom(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 90}, {"AGENTS.md": 100})
    result = run(root, manifest, "--list")
    assert result.returncode == 0, result.stderr
    assert "tight" not in result.stdout


def test_list_reports_a_missing_file_without_failing(tmp_path):
    root, manifest = build(tmp_path, {"AGENTS.md": 10}, {"AGENTS.md": 100, "GONE.md": 50})
    result = run(root, manifest, "--list")
    assert result.returncode == 0, result.stderr
    assert "MISSING" in result.stdout


def test_shipped_manifest_passes(tmp_path):
    """The real repo manifest must be green, or the gate cannot be merged."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_shipped_manifest_budgets_the_always_loaded_docs(tmp_path):
    """Guard the seed set: dropping a doc from the budget must be deliberate."""
    manifest = json.loads(
        (REPO_ROOT / "docs" / "policy" / "doc-budgets.json").read_text(encoding="utf-8")
    )
    for required in (
        "AGENTS.md",
        "CLAUDE.md",
        "catalog/style-guides/markdown.md",
        "templates/ai-instructions/base-claude.md",
        "templates/ai-instructions/base-codex.md",
        "templates/ai-instructions/base-cursor.md",
        "templates/ai-instructions/base-gemini.md",
        "templates/ai-instructions/base-opencode.md",
    ):
        assert required in manifest, f"{required} lost its word budget"
