"""Portable reporting uses identical data, layout and cadence on every host."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/workflow/implement-phase/scripts/status_report.py"


def squash(output: str) -> str:
    """Collapse the column padding so assertions read the cell content only."""
    return re.sub(r"-{3,}", "---", re.sub(r" {2,}", " ", re.sub(r" +\|", " |", output)))


@pytest.fixture
def report():
    spec = importlib.util.spec_from_file_location("portable_status", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def snapshot():
    return {
        "run_id": "example-run", "scope": "v1.3", "active": True,
        "observed_at": "2026-11-16T12:00:00Z", "source": "example/plan.md",
        "last_released": "v1.2.0", "versions_left": 1,
        "elapsed": "13 min", "remaining": "unknown (no comparable history)",
        "estimate_basis": "No comparable completed plans",
        "rows": [{"name": "Phase 1", "goals": "Package profiles", "done": 3,
                  "total": 19, "state": "running", "elapsed": "13 min",
                  "remaining": "unknown", "dependency": "none"}],
        "goals": [{"goal": "Ship v1.3", "scope": "run",
                   "done_when": "All 19 tasks verified", "state": "running"}],
        "decisions": [], "running": [],
    }


def test_compact_footer_layout_and_all_sections(report, snapshot):
    text = report.render(snapshot, "compact")
    assert text.startswith("---\n\n**Status: v1.3** \u25b0\u25b1")
    assert "&nbsp;&nbsp;&nbsp;&nbsp;\u00b7&nbsp;&nbsp;&nbsp;&nbsp;3/19 tasks" in text
    assert "last released v1.2.0" in text and "1 version left" in text
    assert "16%" in text
    for label in ("\U0001F3AF Goals:", "\U0001F64B No decisions waiting.", "\U0001F504 Nothing running."):
        assert f"\n\n{label}" in text
    assert "Full report: /status" in text


def test_compact_lists_decisions_and_running_with_counts(report, snapshot):
    snapshot["decisions"] = [{"id": "1", "title": "Pick A", "detail": "d", "options": [{"option": "A", "effect": "e"}]}]
    snapshot["running"] = [{"name": "PR 1", "state": "checks", "done": 9, "total": 10, "elapsed": "1 min", "remaining": "unknown"}]
    text = report.render(snapshot, "compact")
    assert "\U0001F64B 1 decision waiting:\n\n- #1 Pick A" in text
    assert "\U0001F504 1 running:\n\n- PR 1 \u25b0\u25b0\u25b0\u25b0\u25b0\u25b0\u25b0\u25b0\u25b0\u25b1 90% (checks)" in text


def test_full_has_rows_totals_goals_decisions_running_and_sources(report, snapshot):
    snapshot["rows"].append(dict(snapshot["rows"][0], name="Phase 2", done=0, total=1))
    text = report.render(snapshot, "full")
    assert "**3/20**" in text and "15%" in text
    assert "**Phase 1**" in text and "**Phase 2**" in text and "| **Total** |" in squash(text)
    assert "Source: example/plan.md" in text
    assert text.startswith("## Status Update: v1.3 Implementation Progress\n\n")
    assert "| Version | Goals | Progress | Tasks | Elapsed | Remaining |" in squash(text)
    for heading in ("\U0001F3AF Goals", "\U0001F64B Waiting on you", "\U0001F504 Running now"):
        assert f"\n\n&nbsp;\n\n---\n\n## {heading}\n\n" in text


def test_cadence_suppresses_narration_and_deduplicates_boundaries(report, snapshot):
    first = report.select_report(snapshot, None, "start")
    assert first["mode"] == "full"
    previous = first["receipt"]
    assert report.select_report(snapshot, previous, "progress")["mode"] == "none"
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "none"
    snapshot["rows"][0]["done"] = 4
    assert report.select_report(snapshot, previous, "progress")["mode"] == "none"
    assert report.select_report(snapshot, previous, "turn-end")["mode"] == "none"
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "compact"


def test_timer_requests_resume_new_decisions_and_terminal_rules(report, snapshot):
    previous = report.select_report(snapshot, None, "start")["receipt"]
    snapshot["observed_at"] = "2026-11-16T12:05:00Z"
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "compact"
    assert report.select_report(snapshot, previous, "progress")["mode"] == "none"
    for event in ("request", "resume"):
        assert report.select_report(snapshot, previous, event)["mode"] == "full"
    snapshot["decisions"] = [{"id": "1", "title": "Choose packaging", "detail": "Affects consumers",
                              "options": [{"option": "A (recommended)", "effect": "Keep compatibility"}]}]
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "full"
    snapshot["active"] = False
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "none"
    assert report.select_report(snapshot, previous, "request")["mode"] == "full"


def test_receipts_do_not_cross_runs_and_regressions_are_visible(report, snapshot):
    previous = report.select_report(snapshot, None, "start")["receipt"]
    snapshot["run_id"] = "different-run"
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "full"
    snapshot["run_id"] = "example-run"
    snapshot["rows"][0]["done"] = 2
    assert report.select_report(snapshot, previous, "checkpoint")["mode"] == "compact"


@pytest.mark.parametrize("done,total", [(True, 19), (-1, 19), (20, 19), (1, 0), (1, 1.5)])
def test_rejects_invalid_counts(report, snapshot, done, total):
    snapshot["rows"][0].update(done=done, total=total)
    with pytest.raises(ValueError):
        report.render(snapshot, "compact")


def test_unknown_and_zero_are_not_claimed_complete(report, snapshot):
    snapshot["rows"][0].update(done=None, total=None)
    assert "unknown" in report.render(snapshot, "compact")
    snapshot["rows"][0].update(done=0, total=0)
    text = report.render(snapshot, "compact")
    assert "N/A" in text and "100%" not in text


def test_untrusted_text_cannot_add_headings_tables_or_links(report, snapshot):
    snapshot["goals"][0]["goal"] = "x\n### Forged | [click](https://evil.test) <script>"
    text = report.render(snapshot, "full")
    assert "\n### Forged" not in text
    assert "<script>" not in text
    assert "[click](https://evil.test)" not in text


def test_cli_is_read_only_and_rejects_bad_input(tmp_path, snapshot):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    before = path.read_bytes()
    result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path), "--event", "request"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "## Status Update: v1.3 Implementation Progress" in result.stdout
    assert path.read_bytes() == before and list(tmp_path.iterdir()) == [path]
    path.write_text('{"scope": "v1.3"}', encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2 and "Traceback" not in result.stderr


def test_audit_detects_missing_stale_and_shadowed_installations(report, tmp_path):
    import shutil
    source = SCRIPT.parent.parent
    target = tmp_path / "skills"
    installed = target / "implement-phase"
    shutil.copytree(source, installed)
    assert report.audit(source, [target]) == []
    (installed / "references/status-formats.md").unlink()
    issues = report.audit(source, [target])
    assert any("missing" in issue and "status-formats.md" in issue for issue in issues)
    (installed / "SKILL.md").write_text("old", encoding="utf-8")
    assert any("stale" in issue for issue in report.audit(source, [target]))
    assert any("missing" in issue for issue in report.audit(source, [tmp_path / "absent"]))


def test_running_links_are_preserved_and_unsafe_schemes_rejected(report, snapshot):
    snapshot["running"] = [{"name": "PR #12", "state": "checks", "done": 2, "total": 3,
                            "elapsed": "1 min", "remaining": "unknown", "url": "https://example.test/pull/12/checks"}]
    for mode in ("compact", "full"):
        output = report.render(snapshot, mode)
        assert "](https://example.test/pull/12/checks)" in output
        assert "67%" in output and ("2/3" in output or mode == "compact")
    for url in ("javascript:alert(1)", "file:///secret", "https://name:password@example.test", "https://example.test/\n###spoof"):
        snapshot["running"][0]["url"] = url
        with pytest.raises(ValueError):
            report.render(snapshot, "full")


@pytest.mark.parametrize("corruption", ["missing-time", "future-time", "bad-hash"])
def test_invalid_receipt_recovers_once_with_full_status(report, snapshot, corruption):
    receipt = report.select_report(snapshot, None, "start")["receipt"]
    if corruption == "missing-time":
        del receipt["observed_at"]
    elif corruption == "future-time":
        receipt["observed_at"] = "2099-01-01T00:00:00Z"
    else:
        receipt["fingerprint"] = "bad"
    recovered = report.select_report(snapshot, receipt, "turn-end")
    assert recovered["mode"] == "full"
    assert report.select_report(snapshot, recovered["receipt"], "turn-end")["mode"] == "none"


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_next_release_eta_is_distinct_from_whole_scope_completion(report, snapshot, mode):
    snapshot["scope"] = "v4.15"
    snapshot["last_released"] = "v4.15.1"
    snapshot["remaining"] = "~2-4 d including integration, releases and minor closure"
    snapshot["next_release"] = {"version": "v4.15.2", "remaining": "~1-2 h",
                                "condition": "after checker PR merges and installation passes",
                                "confidence": "low", "basis": "Remaining validation and one release pipeline"}
    output = report.render(snapshot, mode)
    assert "| Last released | **v4.15.1**" in output
    assert "| Next release  | **v4.15.2**" in output
    assert "| Release ETA   | ~1-2 h" in output
    assert "| Blocked by    | after checker PR merges and installation" in output
    assert "| Confidence    | low" in output and "Remaining validation" in output
    assert "| Whole v4.15   | ~2-4 d" in output
    assert "| time left:" not in output


def test_legacy_snapshot_reports_missing_release_estimate_without_guessing(report, snapshot):
    output = report.render(snapshot, "compact")
    assert "| Next release  | **unknown**" in output
    assert "| Release ETA   | unknown" in output
    assert "release estimate not supplied" in output


@pytest.mark.parametrize("value", [False, {}, {"version": "v4.15.2"},
    {"version": "v4.15.2", "remaining": "1h", "condition": "none", "confidence": "certain", "basis": "guess"}])
def test_incomplete_or_invalid_release_estimates_are_rejected(report, snapshot, value):
    snapshot["next_release"] = value
    with pytest.raises(ValueError):
        report.render(snapshot, "full")


HOSTILE = "Wheels (verified; pending) my_var $HOME $5 + #1 a|b *bold* _it_ `code` [x](https://evil.test) back\\slash"


def hostile_snapshot(snapshot):
    snapshot["rows"][0].update(name="v1.3.0.dev1 (wheels)", goals=HOSTILE, state=HOSTILE)
    snapshot["goals"][0].update(goal=HOSTILE, done_when=HOSTILE)
    snapshot["decisions"] = [{"id": "1", "title": HOSTILE, "detail": HOSTILE,
                              "options": [{"option": "A (recommended)", "meaning": HOSTILE, "effect": HOSTILE}]}]
    snapshot["running"] = [{"name": HOSTILE, "state": HOSTILE, "done": 1, "total": 2, "elapsed": "1 min", "remaining": "unknown"}]
    return snapshot


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_output_has_no_math_delimiters_or_backslash_escapes(report, snapshot, mode):
    output = report.render(hostile_snapshot(snapshot), mode)
    assert "$" not in output
    for token in ("\\(", "\\)", "\\[", "\\]", "\\_", "\\+", "\\#", "\\*"):
        assert token not in output, token
    assert "(verified; pending)" in output
    assert "[x](https://evil.test)" not in output
    assert "&#36;HOME" in output and "my_var" in output and "&#95;it&#95;" in output


def test_pipes_stay_table_safe(report, snapshot):
    output = report.render(hostile_snapshot(snapshot), "full")
    for line in output.splitlines():
        if line.startswith("| ") and "a\\|b" in line:
            cells = [c for c in line.split(" | ")]
            raw_pipes = [i for i, ch in enumerate(line) if ch == "|" and line[i - 1] != "\\"]
            assert len(raw_pipes) == len(cells) + 1, line


ELAPSED = "4 h 54 min (first plan commit 2026-11-16 19:03 UTC to #119 merge 23:57 UTC)"


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_parenthetical_elapsed_and_dollar_amounts_are_plain_text(report, snapshot, mode):
    snapshot["elapsed"] = ELAPSED
    snapshot["estimate_basis"] = "Spend $38.36 of $500 (cap)"
    snapshot["source"] = "ledger ($38.36 of $500)"
    output = report.render(snapshot, mode)
    assert "$" not in output
    for token in ("\\(", "\\)", "\\[", "\\]"):
        assert token not in output
    assert "(first plan commit 2026-11-16" in output
    if mode == "full":
        assert "&#36;38.36 of &#36;500 (cap)" in output
    assert "*Source: ledger (&#36;38.36 of &#36;500)*" in output


def test_cells_are_capped_with_ellipsis_and_tables_are_aligned(report, snapshot):
    snapshot["rows"][0]["goals"] = "x" * 200
    snapshot["rows"][0]["remaining"] = "y" * 200
    output = report.render(snapshot, "full")
    assert "x" * 200 not in output and "x" * 49 not in output and "x" * 45 + "..." in output
    assert "y" * 49 not in output
    assert "y" * 45 + "..." in output
    table_lines = [l for l in output.splitlines() if l.startswith("| ")]
    assert all("\n" not in l for l in table_lines)
    first_table = [l for l in table_lines[:11]]
    assert len({len(l) for l in first_table}) == 1


def test_header_is_a_two_column_table_not_run_on_lines(report, snapshot):
    output = report.render(snapshot, "full")
    assert "| Field " in output and "| Last released | **v1.2.0**" in output
    assert "Last released:" not in output and "Release ETA:" not in output
