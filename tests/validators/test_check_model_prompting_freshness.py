"""Tests for scripts/check_model_prompting_freshness.py (v3.15.5 Phase 1).

The staleness checker is ADVISORY by contract: it detects roster drift and must
never block anything. These tests cover the three drift cases the plan calls for
(in sync, added model, removed model) and, just as importantly, pin the
non-blocking contract itself: in the default advisory mode EVERY path exits 0,
including drift, a missing bundle, a corrupt index, and an absent live roster.
Only the explicit `--strict` flag (local operator tooling, never CI) propagates a
non-zero exit.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SCRIPT = "check_model_prompting_freshness.py"
BUNDLE_REL = Path("catalog/skills/ai-development/model-prompting-research")
RECORDED = ["model-a", "model-b", "model-c"]


def _roster_hash(roster: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def _write_bundle(
    root: Path,
    roster: Iterable[str] = RECORDED,
    *,
    roster_hash: str | None = None,
    raw: str | None = None,
) -> Path:
    """Materialize a bundle whose index records `roster`."""
    roster = sorted(roster)
    bundle = root / BUNDLE_REL
    (bundle / "assets").mkdir(parents=True, exist_ok=True)
    (bundle / "references" / "models").mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": "1.0.0",
        "meta": {
            "last_verified": "2026-07-27",
            "platform": "claude-code",
            "roster_source": "picker",
            "roster": roster,
            "roster_hash": roster_hash if roster_hash is not None else _roster_hash(roster),
        },
        "models": {},
    }
    payload = raw if raw is not None else json.dumps(index, indent=2)
    (bundle / "assets" / "profiles-index.json").write_text(payload, encoding="utf-8")
    return bundle


# ---------------------------------------------------------------------------
# The three drift verdicts
# ---------------------------------------------------------------------------


def test_identical_roster_is_in_sync(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, list(RECORDED))

    assert result.returncode == 0
    assert "IN SYNC" in result.stdout
    assert "DRIFTED" not in result.stdout


def test_added_model_reports_drift_with_the_new_id(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, [*RECORDED, "model-d"])

    assert "DRIFTED" in result.stdout
    assert "added (live but unprofiled): model-d" in result.stdout
    assert "removed" not in result.stdout


def test_removed_model_reports_drift_with_the_dropped_id(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["model-a", "model-b"])

    assert "DRIFTED" in result.stdout
    assert "removed (recorded but no longer live): model-c" in result.stdout
    assert "added" not in result.stdout


def test_added_and_removed_are_reported_together(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["model-a", "model-b", "model-z"])

    assert "added (live but unprofiled): model-z" in result.stdout
    assert "removed (recorded but no longer live): model-c" in result.stdout


def test_stale_hash_with_matching_ids_reports_a_restamp(tmp_path: Path, runner) -> None:
    """A hand-edited roster whose hash was not re-stamped is still drift."""
    _write_bundle(tmp_path, roster_hash="0" * 64)

    result = runner(SCRIPT, tmp_path, list(RECORDED))

    assert "DRIFTED" in result.stdout
    assert "was not re-stamped" in result.stdout


def test_argv_roster_order_and_duplicates_do_not_matter(tmp_path: Path, runner) -> None:
    """The live roster is normalized (sorted, deduped) before comparison."""
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["model-c", "model-a", "model-b", "model-a"])

    assert "IN SYNC" in result.stdout


# ---------------------------------------------------------------------------
# The non-blocking contract: advisory mode never fails, whatever happens
# ---------------------------------------------------------------------------


def test_drift_exits_zero_in_default_advisory_mode(tmp_path: Path, runner) -> None:
    """The whole point of the script: drift is reported, never enforced."""
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["model-d"])

    assert result.returncode == 0, "advisory mode must never block on drift"
    assert "never blocks a release" in result.stdout


def test_explicit_advisory_flag_also_exits_zero_on_drift(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["--advisory", "model-d"])

    assert result.returncode == 0


@pytest.mark.parametrize(
    ("case", "extra_args"),
    [
        pytest.param("drift", ["model-d"], id="drift"),
        pytest.param("unknown_no_roster", [], id="unknown_no_roster"),
    ],
)
def test_strict_mode_propagates_failure(
    tmp_path: Path, runner, case: str, extra_args: list[str]
) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["--strict", *extra_args])

    assert result.returncode == 1, f"{case} should fail under --strict:\n{result.stdout}"


def test_advisory_and_strict_are_mutually_exclusive(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, ["--advisory", "--strict", "model-a"])

    assert result.returncode == 2, "argparse should reject both mode flags together"
    assert "not allowed with" in result.stderr


# ---------------------------------------------------------------------------
# UNKNOWN verdicts: no comparison possible, still never a blocker by default
# ---------------------------------------------------------------------------


def test_no_live_roster_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path)

    result = runner(SCRIPT, tmp_path, [])

    assert result.returncode == 0
    assert "UNKNOWN" in result.stdout
    assert "no live roster supplied" in result.stdout
    assert "enumerate-models" in result.stdout


def test_missing_bundle_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    """A non-catalog repo must be a silent no-op, which the release step relies on."""
    result = runner(SCRIPT, tmp_path, ["model-a"])

    assert result.returncode == 0
    assert "UNKNOWN" in result.stdout
    assert "no 'model-prompting-research' bundle found" in result.stdout


def test_corrupt_index_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    _write_bundle(tmp_path, raw="{broken")

    result = runner(SCRIPT, tmp_path, ["model-a"])

    assert result.returncode == 0
    assert "UNKNOWN" in result.stdout
    assert "not valid JSON" in result.stdout


def test_meta_that_is_not_an_object_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    raw = json.dumps({"schema_version": "1.0.0", "meta": "2026-07-27", "models": {}})
    _write_bundle(tmp_path, raw=raw)

    result = runner(SCRIPT, tmp_path, ["model-a"])

    assert result.returncode == 0
    assert "no usable meta block" in result.stdout


def test_absent_index_file_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    """The bundle dir exists but carries no index yet."""
    (tmp_path / BUNDLE_REL / "assets").mkdir(parents=True)

    result = runner(SCRIPT, tmp_path, ["model-a"])

    assert result.returncode == 0
    assert "missing profile index" in result.stdout


def test_malformed_roster_is_unknown_not_a_failure(tmp_path: Path, runner) -> None:
    raw = json.dumps({"schema_version": "1.0.0", "meta": {"roster": "model-a"}, "models": {}})
    _write_bundle(tmp_path, raw=raw)

    result = runner(SCRIPT, tmp_path, ["model-a"])

    assert result.returncode == 0
    assert "meta.roster is missing or malformed" in result.stdout


# ---------------------------------------------------------------------------
# The real shipped layer
# ---------------------------------------------------------------------------


def test_shipped_layer_reports_in_sync_against_its_own_recorded_roster(runner) -> None:
    """Sanity check on the seed: it agrees with itself, so drift means real drift."""
    index = json.loads(
        (REPO_ROOT / BUNDLE_REL / "assets" / "profiles-index.json").read_text(encoding="utf-8")
    )
    recorded = index["meta"]["roster"]

    result = runner(SCRIPT, REPO_ROOT, list(recorded))

    assert result.returncode == 0
    assert "IN SYNC" in result.stdout
