"""The pull request gate retains one aggregate report package."""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
SOURCES = {
    "validate": "ci-validation-reports",
    "shellcheck": "ci-shell-reports",
    "tests": "ci-test-reports",
    "guide-render": "ci-guide-render-report",
    "tests-windows": "ci-windows-reports",
}


def test_report_job_aggregates_every_profile_receipt_after_failure() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    job = workflow["jobs"]["report"]
    assert set(job["needs"]) == set(SOURCES)
    assert job["if"] == "always()"
    steps = job["steps"]
    download = next(step for step in steps if step.get("uses", "").startswith("actions/download-artifact@"))
    assert download["continue-on-error"] is True
    assert download["with"]["path"] == "reports/inputs"
    assert download["with"]["pattern"] == "ci-*"
    assert download["with"]["merge-multiple"] is False
    aggregate = next(step for step in steps if step.get("name") == "Aggregate profile reports")
    assert "--profile report" in aggregate["run"]
    assert "--reports-dir reports" in aggregate["run"]
    for job_name, artifact in SOURCES.items():
        variable = "RESULT_" + job_name.upper().replace("-", "_")
        expression = f"needs.{job_name}.result" if "-" not in job_name else f"needs['{job_name}'].result"
        assert aggregate["env"][variable] == "${{ " + expression + " }}"
        assert f"--expect-artifact {artifact}=${variable}" in aggregate["run"]
    upload = next(step for step in steps if step.get("name") == "Retain aggregate reports")
    assert upload["if"] == "always()"
    assert upload["with"]["name"] == "ci-aggregate-reports"
    assert upload["with"]["path"] == "reports/"
    assert upload["with"]["retention-days"] == 7


def test_required_gate_includes_report_job() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    required = workflow["jobs"]["ci-required"]
    assert "report" in required["needs"]
    assert required["steps"][0]["env"]["R_report"] == "${{ needs.report.result }}"
