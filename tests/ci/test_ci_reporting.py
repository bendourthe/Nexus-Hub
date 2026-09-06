"""Report schema and failure-path tests for the CI engine (v4.0.0 Phase 6).

The requirement carrying the most weight here is contract section 6's failure
clause: **a failing command must still produce a readable summary and valid
partial metadata.** A run that fails and reports nothing is indistinguishable
from a run that never started, and the second is what people assume.

So most of this file exercises the FAILING path, not the happy one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ci import reporting  # noqa: E402
from scripts.ci.reporting import CommandResult, GroupResult, RunResult  # noqa: E402

#: Assembled rather than written as a literal; see tests/ci/test_ci_engine.py.
FAKE_TOKEN = "gh" + "p_" + ("B" * 30)


def _result(*groups: GroupResult, profile: str = "full") -> RunResult:
    return RunResult(
        profile=profile,
        platform="linux",
        groups=list(groups),
        started_at="2026-08-25T10:00:00Z",
        finished_at="2026-08-25T10:06:12Z",
        duration_s=372.0,
        scope_reason="classified 3 changed path(s)",
    )


def _passing_group(name: str = "hygiene") -> GroupResult:
    return GroupResult(
        name=name,
        status="pass",
        commands=[CommandResult(name="a-check", group=name, status="pass", duration_s=1.5, exit_code=0)],
    )


def _failing_group(name: str = "catalog") -> GroupResult:
    return GroupResult(
        name=name,
        status="fail",
        commands=[
            CommandResult(name="ok-check", group=name, status="pass", duration_s=0.5, exit_code=0),
            CommandResult(
                name="broken-check",
                group=name,
                status="fail",
                duration_s=2.0,
                exit_code=2,
                output="traceback line one\ntraceback line two",
                reason="exit 2",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------


def test_a_clean_run_is_pass():
    assert _result(_passing_group()).status == "PASS"


def test_any_failure_makes_the_run_fail():
    assert _result(_passing_group(), _failing_group()).status == "FAIL"


def test_a_skip_makes_the_run_partial_not_pass():
    """PARTIAL is a distinct signal: something did not run, and that is visible."""
    group = GroupResult(
        name="platform",
        commands=[CommandResult(name="win-only", group="platform", status="skip", reason="host is linux")],
    )
    assert _result(group).status == "PARTIAL"


def test_an_advisory_failure_does_not_fail_the_run():
    group = GroupResult(
        name="docs",
        commands=[CommandResult(name="retention", group="docs", status="advisory-fail", exit_code=1)],
    )
    assert _result(group).status == "PARTIAL"


def test_a_timeout_fails_the_run():
    group = GroupResult(
        name="tests",
        commands=[CommandResult(name="hung", group="tests", status="timeout", reason="exceeded 60s")],
    )
    assert _result(group).status == "FAIL"


def test_a_missing_tool_fails_the_run():
    group = GroupResult(
        name="shell-lint",
        commands=[CommandResult(name="shellcheck", group="shell-lint", status="missing")],
    )
    assert _result(group).status == "FAIL"


def test_an_empty_run_is_pass_not_fail():
    """The report profile runs nothing; that is success, not an error."""
    assert _result(profile="report").status == "PASS"


def test_tally_counts_every_status():
    result = _result(_passing_group(), _failing_group())
    counts = result.tally()
    assert counts["pass"] == 2
    assert counts["fail"] == 1


# ---------------------------------------------------------------------------
# Artifacts on the FAILING path
# ---------------------------------------------------------------------------


def test_a_failed_run_still_writes_every_artifact(tmp_path: Path):
    result = _result(_passing_group(), _failing_group())
    reporting.write_reports(result, tmp_path, REPO_ROOT)

    assert (tmp_path / "summary.md").is_file()
    assert (tmp_path / "summary.json").is_file()
    assert (tmp_path / "metadata" / "environment.json").is_file()
    assert (tmp_path / "junit" / "catalog.xml").is_file()


def test_metadata_after_a_failure_is_valid_json_with_the_required_keys(tmp_path: Path):
    reporting.write_reports(_result(_failing_group()), tmp_path, REPO_ROOT)
    meta = json.loads((tmp_path / "metadata" / "environment.json").read_text(encoding="utf-8"))
    for key in ("profile", "platform", "os", "python", "started_at", "finished_at", "status", "tools"):
        assert key in meta, f"environment.json is missing {key}"
    assert meta["status"] == "FAIL"


def test_the_summary_names_the_failing_command_and_shows_its_output(tmp_path: Path):
    reporting.write_reports(_result(_failing_group()), tmp_path, REPO_ROOT)
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "broken-check" in summary
    assert "traceback line two" in summary
    assert "## Failures" in summary


def test_a_clean_run_says_so_rather_than_omitting_the_failures_section(tmp_path: Path):
    """An absent section reads as truncated output; an explicit None does not."""
    reporting.write_reports(_result(_passing_group()), tmp_path, REPO_ROOT)
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "## Failures" in summary
    assert "None." in summary


def test_junit_is_wellformed_and_marks_the_failure(tmp_path: Path):
    reporting.write_reports(_result(_failing_group()), tmp_path, REPO_ROOT)
    root = ET.parse(tmp_path / "junit" / "catalog.xml").getroot()
    assert root.tag == "testsuite"
    assert root.attrib["failures"] == "1"
    assert root.attrib["tests"] == "2"
    failures = root.findall("./testcase/failure")
    assert len(failures) == 1
    assert "traceback" in (failures[0].text or "")


def test_junit_marks_a_skip_as_skipped_not_as_a_pass(tmp_path: Path):
    group = GroupResult(
        name="platform",
        commands=[CommandResult(name="win-only", group="platform", status="skip", reason="host is linux")],
    )
    reporting.write_reports(_result(group), tmp_path, REPO_ROOT)
    root = ET.parse(tmp_path / "junit" / "platform.xml").getroot()
    assert root.attrib["skipped"] == "1"
    assert root.find("./testcase/skipped") is not None


def test_one_junit_file_per_group(tmp_path: Path):
    reporting.write_reports(_result(_passing_group(), _failing_group()), tmp_path, REPO_ROOT)
    names = sorted(p.name for p in (tmp_path / "junit").glob("*.xml"))
    assert names == ["catalog.xml", "hygiene.xml"]


def test_summary_json_round_trips(tmp_path: Path):
    result = _result(_passing_group(), _failing_group())
    reporting.write_reports(result, tmp_path, REPO_ROOT)
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert data["profile"] == "full"
    assert len(data["groups"]) == 2


def test_reports_dir_is_created_if_absent(tmp_path: Path):
    target = tmp_path / "does" / "not" / "exist"
    reporting.write_reports(_result(_passing_group()), target, REPO_ROOT)
    assert (target / "summary.md").is_file()


# ---------------------------------------------------------------------------
# Determinism and safety
# ---------------------------------------------------------------------------


def test_the_same_run_renders_byte_identically_twice(tmp_path: Path):
    """Two identical runs must produce comparable reports, or diffing is useless."""
    result = _result(_passing_group(), _failing_group())
    first = reporting.render_summary(result, tmp_path, REPO_ROOT)
    second = reporting.render_summary(result, tmp_path, REPO_ROOT)
    assert first == second


def test_artifact_paths_in_the_summary_are_repository_relative(tmp_path: Path):
    """An absolute path leaks a user name and means nothing on another machine."""
    result = _result(_passing_group())
    summary = reporting.render_summary(result, REPO_ROOT / "reports", REPO_ROOT)
    assert "reports/summary.md" in summary
    assert "C:\\" not in summary
    assert str(REPO_ROOT) not in summary


def test_the_summary_is_ascii_safe(tmp_path: Path):
    summary = reporting.render_summary(_result(_failing_group()), tmp_path, REPO_ROOT)
    summary.encode("ascii")


def test_written_files_use_lf_endings(tmp_path: Path):
    """A CRLF Windows leg would make two identical runs differ byte for byte."""
    reporting.write_reports(_result(_passing_group()), tmp_path, REPO_ROOT)
    raw = (tmp_path / "summary.md").read_bytes()
    assert b"\r\n" not in raw


def test_redaction_removes_a_known_value():
    assert reporting.redact(f"value={FAKE_TOKEN}", [FAKE_TOKEN]) == "value=[REDACTED]"


def test_redaction_catches_an_unknown_token_shape():
    """A backstop for a value that was never an environment variable."""
    assert FAKE_TOKEN not in reporting.redact(f"leaked {FAKE_TOKEN} here", [])


def test_redaction_prefers_the_longest_value_first():
    """A short value redacted first would leave a fragment of the longer one."""
    short = "abcd1234"
    long = short + "-extended-tail"
    out = reporting.redact(f"see {long}", [short, long])
    assert "extended-tail" not in out


def test_redaction_is_a_noop_on_empty_input():
    assert reporting.redact("", ["x"]) == ""


def test_secret_values_reads_names_not_shapes(monkeypatch):
    """Matching on the NAME survives a token format change; matching a shape does not."""
    monkeypatch.setenv("NEXUS_TEST_API_TOKEN", "a-long-enough-value-here")
    monkeypatch.setenv("NEXUS_TEST_PLAIN", "also-a-long-enough-value")
    values = reporting.secret_values()
    assert "a-long-enough-value-here" in values
    assert "also-a-long-enough-value" not in values


def test_short_environment_values_are_not_treated_as_secrets(monkeypatch):
    """Redacting a 3-character value would blank unrelated text everywhere."""
    monkeypatch.setenv("NEXUS_TEST_TOKEN", "ab")
    assert "ab" not in reporting.secret_values()


# ---------------------------------------------------------------------------
# Reporting never masks the run
# ---------------------------------------------------------------------------


def test_a_failing_artifact_writer_does_not_raise(tmp_path: Path, monkeypatch):
    """The artifact most likely to fail is the least important of the four."""
    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(reporting, "write_junit", boom)
    written = reporting.write_reports(_result(_failing_group()), tmp_path, REPO_ROOT)
    assert "summary.md" in written
    assert "junit" not in written


def test_environment_metadata_is_stable_for_the_same_run():
    result = _result(_passing_group())
    first = reporting.environment_metadata(result, {"git": "2.52"})
    second = reporting.environment_metadata(result, {"git": "2.52"})
    assert first == second


def test_environment_metadata_records_the_change_scope_reason():
    """A skip with no recorded reason is the shape of every fail-open defect."""
    meta = reporting.environment_metadata(_result(_passing_group()))
    assert meta["scope_reason"] == "classified 3 changed path(s)"
