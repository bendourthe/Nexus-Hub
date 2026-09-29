"""Completeness and evidence tests for the completion levers matrix.

`docs/policy/completion-levers.json` records, for every registered integration
and for the named surfaces that share an integration, three completion levers:
a native goal command, a turn-end continuation hook or plugin, and a headless
CLI mode. The completion gate reads continuation formats from it and the
`run-plan` runner lists the platforms it marks headless-VERIFIED.

The roster comes from the integration registry, so a newly registered platform
fails here until it is classified. Every VERIFIED lever must carry a first-party
source URL and an ISO fetch date: the do-not-invent rule, applied the same way
as `test_platform_defaults_levers.py`.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import list_keys

MATRIX = REPO_ROOT / "docs" / "policy" / "completion-levers.json"
COMPANION = REPO_ROOT / "docs" / "policy" / "completion-levers.md"

LEVERS = ("native_goal", "continuation", "headless")
STATUSES = {"VERIFIED", "none documented"}
# The continuation shapes the completion gate knows how to emit. A new vendor
# format must be added here AND to scripts/completion_gate.py together.
FORMATS = {
    "top-level-block",
    "vscode-hook-specific-output",
    "cursor-followup-message",
    "antigravity-continue",
    "gemini-deny",
    "exit-2",
    "plugin",
}
SURFACE_ROWS = {
    "windsurf/devin-cli",
    "antigravity2/cli",
    "copilot/vscode",
    "copilot/cli",
}
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Whether a typed `/goal ...` line reaches the prompt-submit hook verbatim
# (v4.13.6 Phase 1.1). The approval page chooses its paste layout from this.
GOAL_CAPTURE_VALUES = {"verbatim", "not-captured", "no-goal", "unverified"}
# Values that assert a settled fact and therefore need a first-party source.
GOAL_CAPTURE_SETTLED = {"verbatim", "not-captured", "no-goal"}


@pytest.fixture(scope="module")
def matrix() -> dict:
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def _levers(matrix: dict):
    for row_id, row in matrix["rows"].items():
        for lever in LEVERS:
            yield row_id, lever, row[lever]


def test_every_registered_integration_is_classified(matrix: dict) -> None:
    missing = sorted(set(list_keys()) - set(matrix["rows"]))
    assert not missing, f"unclassified registered platforms: {missing}"


def test_named_surface_rows_are_present_and_owned(matrix: dict) -> None:
    keys = set(list_keys())
    for row_id in SURFACE_ROWS:
        assert row_id in matrix["rows"], f"missing surface row {row_id}"
        owner = matrix["rows"][row_id].get("owner")
        assert owner in keys, f"{row_id} names unregistered owner {owner!r}"


def test_no_row_is_unexplained(matrix: dict) -> None:
    extra = set(matrix["rows"]) - set(list_keys()) - SURFACE_ROWS
    assert not extra, (
        f"rows that are neither registered keys nor named surfaces: {sorted(extra)}"
    )


def test_every_lever_has_a_valid_status(matrix: dict) -> None:
    for row_id, lever, entry in _levers(matrix):
        assert entry.get("status") in STATUSES, (
            f"{row_id}.{lever}: bad status {entry.get('status')!r}"
        )


def test_verified_levers_carry_a_source_and_date(matrix: dict) -> None:
    for row_id, lever, entry in _levers(matrix):
        if entry["status"] != "VERIFIED":
            continue
        url = entry.get("source_url") or ""
        assert url.startswith("https://"), (
            f"{row_id}.{lever}: VERIFIED without an https source"
        )
        assert _ISO_DATE.match(entry.get("verified", "")), (
            f"{row_id}.{lever}: VERIFIED without an ISO date"
        )


def test_verified_continuation_names_a_known_format(matrix: dict) -> None:
    for row_id, lever, entry in _levers(matrix):
        if lever == "continuation" and entry["status"] == "VERIFIED":
            assert entry.get("format") in FORMATS, (
                f"{row_id}: unknown continuation format {entry.get('format')!r}"
            )
            assert entry.get("event"), (
                f"{row_id}: VERIFIED continuation without an event name"
            )


def test_verified_headless_names_launch_and_resume(matrix: dict) -> None:
    for row_id, lever, entry in _levers(matrix):
        if lever == "headless" and entry["status"] == "VERIFIED":
            assert entry.get("launch"), (
                f"{row_id}: headless VERIFIED without a launch form"
            )
            assert entry.get("resume"), (
                f"{row_id}: headless VERIFIED without a resume form"
            )


def test_companion_lists_every_row(matrix: dict) -> None:
    text = COMPANION.read_text(encoding="utf-8")
    for row_id in matrix["rows"]:
        assert f"`{row_id}`" in text, f"companion table omits {row_id}"


def _goal_captures(matrix: dict):
    for row_id, row in matrix["rows"].items():
        yield row_id, row.get("goal_capture")


def test_every_row_carries_goal_capture(matrix: dict) -> None:
    for row_id, entry in _goal_captures(matrix):
        assert isinstance(entry, dict), f"{row_id}: missing goal_capture object"
        assert entry.get("value") in GOAL_CAPTURE_VALUES, (
            f"{row_id}.goal_capture: bad value {entry.get('value')!r}"
        )
        assert _ISO_DATE.match(entry.get("verified", "")), (
            f"{row_id}.goal_capture: missing ISO verified date"
        )
        assert isinstance(entry.get("source_url"), str), (
            f"{row_id}.goal_capture: missing source_url"
        )
        assert entry.get("evidence"), f"{row_id}.goal_capture: missing evidence"


def test_settled_goal_capture_cites_a_source(matrix: dict) -> None:
    for row_id, entry in _goal_captures(matrix):
        if entry["value"] not in GOAL_CAPTURE_SETTLED:
            continue
        url = entry["source_url"]
        if entry.get("probe") is True:
            # A local probe cites its repository record instead of a vendor page.
            assert (REPO_ROOT / url).is_file(), (
                f"{row_id}.goal_capture: probe record {url!r} does not exist"
            )
        else:
            assert url.startswith("https://"), (
                f"{row_id}.goal_capture: {entry['value']} without an https source"
            )


def test_verbatim_goal_capture_requires_a_probe(matrix: dict) -> None:
    # Never verbatim by analogy: no vendor page states slash-command text
    # reaches the hook, so verbatim is only accepted from a recorded probe.
    for row_id, entry in _goal_captures(matrix):
        if entry["value"] == "verbatim":
            assert entry.get("probe") is True, (
                f"{row_id}.goal_capture: verbatim without a recorded probe"
            )
            # The approval is a typed paste, so a headless `-p` probe does not settle it.
            assert entry.get("probe_mode") == "interactive", (
                f"{row_id}.goal_capture: verbatim needs a typed (interactive) probe"
            )


def test_goal_capture_needs_a_goal_command(matrix: dict) -> None:
    for row_id, entry in _goal_captures(matrix):
        if entry["value"] in {"verbatim", "not-captured"}:
            assert matrix["rows"][row_id]["native_goal"]["status"] == "VERIFIED", (
                f"{row_id}.goal_capture: {entry['value']} but no VERIFIED native goal"
            )


def test_companion_documents_goal_capture_values(matrix: dict) -> None:
    text = COMPANION.read_text(encoding="utf-8")
    for value in GOAL_CAPTURE_VALUES:
        assert f"`{value}`" in text, f"companion omits goal_capture value {value}"
