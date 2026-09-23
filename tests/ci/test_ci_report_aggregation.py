"""The report profile aggregates existing receipts without rerunning validation."""

import json
from pathlib import Path

from scripts.ci.run import main, run_profile


def _summary(path: Path, status: str = "pass") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"profile": "full", "groups": [{"commands": [{"status": status}]}]}),
        encoding="utf-8",
    )


def test_report_without_inputs_fails_instead_of_passing_empty(tmp_path: Path) -> None:
    result = run_profile("report", reports_dir=tmp_path)
    assert result.status == "FAIL"
    assert result.groups[0].commands[0].status == "missing"


def test_report_aggregates_job_receipts_and_indexes_files(tmp_path: Path) -> None:
    artifact = tmp_path / "inputs" / "ci-test-reports"
    _summary(artifact / "summary.json")
    (artifact / "junit").mkdir()
    (artifact / "junit" / "tests.xml").write_text("<testsuite/>", encoding="utf-8")

    result = run_profile(
        "report", reports_dir=tmp_path, expected_artifacts={"ci-test-reports": "success"}
    )

    assert result.status == "PASS"
    index = json.loads((tmp_path / "aggregate-index.json").read_text(encoding="utf-8"))
    assert index["schema_version"] == 1
    assert index["artifacts"][0]["name"] == "ci-test-reports"
    assert {entry["path"] for entry in index["artifacts"][0]["files"]} == {
        "inputs/ci-test-reports/summary.json",
        "inputs/ci-test-reports/junit/tests.xml",
    }
    assert all(len(entry["sha256"]) == 64 for entry in index["artifacts"][0]["files"])


def test_report_accepts_an_expected_skipped_job(tmp_path: Path) -> None:
    result = run_profile(
        "report", reports_dir=tmp_path, expected_artifacts={"ci-guide-render-report": "skipped"}
    )
    assert result.status == "PARTIAL"
    assert result.groups[0].commands[0].status == "skip"


def test_report_fails_if_a_required_job_has_no_receipt(tmp_path: Path) -> None:
    result = run_profile(
        "report", reports_dir=tmp_path, expected_artifacts={"ci-test-reports": "success"}
    )
    assert result.status == "FAIL"
    assert result.groups[0].commands[0].status == "missing"


def test_report_preserves_an_upstream_failure_even_with_a_passing_receipt(tmp_path: Path) -> None:
    _summary(tmp_path / "inputs" / "ci-test-reports" / "summary.json")
    result = run_profile(
        "report", reports_dir=tmp_path, expected_artifacts={"ci-test-reports": "failure"}
    )
    assert result.status == "FAIL"
    assert result.groups[0].commands[0].status == "fail"


def test_report_rejects_an_artifact_name_that_escapes_its_root(tmp_path: Path) -> None:
    result = run_profile(
        "report", reports_dir=tmp_path, expected_artifacts={"../outside": "success"}
    )
    assert result.status == "FAIL"
    assert result.groups[0].commands[0].reason == "invalid artifact name"


def test_report_preserves_the_existing_local_summary_entrypoint(tmp_path: Path) -> None:
    _summary(tmp_path / "summary.json")
    result = run_profile("report", reports_dir=tmp_path)
    assert result.status == "PASS"
    assert result.groups[0].commands[0].status == "pass"
    assert (tmp_path / "inputs" / "local" / "summary.json").is_file()
    assert run_profile("report", reports_dir=tmp_path).status == "PASS"


def test_report_rejects_a_malformed_source_receipt(tmp_path: Path) -> None:
    _summary(tmp_path / "inputs" / "ci-test-reports" / "summary.json", "unknown")
    result = run_profile("report", reports_dir=tmp_path)
    assert result.status == "FAIL"


def test_report_cli_accepts_expected_job_result(tmp_path: Path) -> None:
    _summary(tmp_path / "inputs" / "ci-test-reports" / "summary.json")
    assert main([
        "--profile", "report", "--reports-dir", str(tmp_path),
        "--expect-artifact", "ci-test-reports=success", "--quiet",
    ]) == 0


def test_report_expectation_cannot_be_used_on_validation_profile(tmp_path: Path) -> None:
    assert main([
        "--profile", "full", "--reports-dir", str(tmp_path),
        "--expect-artifact", "ci-test-reports=success",
    ]) == 2
