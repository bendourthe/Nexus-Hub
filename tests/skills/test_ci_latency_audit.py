"""Behavior tests for the cicd-architect latency audit script.

Every test uses the injectable runner or the offline ``--from-json`` fixtures,
so no ``gh`` process starts.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "catalog/skills/infrastructure/cicd-architect/scripts/ci_latency_audit.py"
FIXTURES = ROOT / "tests/fixtures/ci_latency"

spec = importlib.util.spec_from_file_location("ci_latency_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules["ci_latency_audit"] = audit
spec.loader.exec_module(audit)


def run_json(capsys: pytest.CaptureFixture[str], case: str, *extra: str) -> dict:
    code = audit.main(["--from-json", str(FIXTURES / case), "--gate", "ci-required", "--json", *extra])
    out = capsys.readouterr()
    assert code == 0, out.err
    return json.loads(out.out)


def test_normal_run_names_critical_path_and_gate_time(capsys: pytest.CaptureFixture[str]) -> None:
    data = run_json(capsys, "normal")
    assert data["critical_path"] == "tests"
    assert data["gate"]["mean"] == pytest.approx(30 * 60 + 25)
    tests = data["jobs"]["tests"]
    assert tests["queue"]["mean"] == pytest.approx(30)
    assert tests["work"]["mean"] == pytest.approx(28 * 60)
    assert tests["setup"]["mean"] == pytest.approx(60)


def test_aggregate_jobs_are_not_critical_path(capsys: pytest.CaptureFixture[str]) -> None:
    data = run_json(capsys, "normal")
    assert data["critical_path"] not in {"report", "ci-required"}
    assert data["critical_counts"] == {"tests": 1}


def test_retried_attempt_is_excluded_not_double_counted(capsys: pytest.CaptureFixture[str]) -> None:
    code = audit.main(["--from-json", str(FIXTURES / "retried"), "--gate", "ci-required"])
    err = capsys.readouterr().err
    assert code == 2
    assert "no runs matched" in err


def test_same_run_listed_twice_counts_once(capsys: pytest.CaptureFixture[str]) -> None:
    code = audit.main(["--from-json", str(FIXTURES / "normal"), "--run-ids", "1001,1001", "--json", "--gate", "ci-required"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["runs"] == 1


def test_skipped_cancelled_and_incomplete_jobs_are_reported_separately(capsys: pytest.CaptureFixture[str]) -> None:
    data = run_json(capsys, "skipped", "--conclusion", "any")
    assert set(data["skipped"]) == {"windows", "nightly"}
    assert data["incomplete"] == ["no-times"]
    assert "no-times" not in data["jobs"]
    assert "windows" not in data["jobs"]


def test_time_to_first_failure_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    data = run_json(capsys, "skipped", "--conclusion", "any")
    assert data["first_failure"]["median"] == pytest.approx(6 * 60)


def test_fork_run_excluded_by_default_and_included_on_request(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main(["--from-json", str(FIXTURES / "fork")]) == 2
    capsys.readouterr()
    data = run_json(capsys, "fork", "--include-forks")
    assert data["runs"] == 1


def test_hostile_job_name_is_escaped_in_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    code = audit.main(["--from-json", str(FIXTURES / "names"), "--gate", "ci-required"])
    out = capsys.readouterr().out
    assert code == 0
    row = next(line for line in out.splitlines() if "script" in line)
    assert "\\|" in row and "\\`" in row and "\\<script\\>" in row
    assert "\x1b" not in out and "\n  line2" not in out
    assert len(row.split("|")[1].strip()) <= audit.NAME_LIMIT + 8


@pytest.mark.parametrize("repo", ["no-slash", "a/b/c", "a b/c", "a/b;rm", "../x/y"])
def test_invalid_repo_refused_before_any_call(repo: str, capsys: pytest.CaptureFixture[str]) -> None:
    def runner(args: list[str]) -> tuple[int, str, str]:
        raise AssertionError("runner must not be called")

    assert audit.main(["--repo", repo, "--run-ids", "1"], runner=runner) == 2
    assert "owner/name" in capsys.readouterr().err


def test_non_github_repository_gets_clear_message(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main(["--repo", "https://gitlab.com/a/b", "--run-ids", "1"], runner=lambda a: (0, "", "")) == 2
    assert "only GitHub Actions is supported" in capsys.readouterr().err


@pytest.mark.parametrize("workflow", ["../ci.yml", "ci", "a/b.yml", "ci.yml;x"])
def test_invalid_workflow_refused(workflow: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main(["--repo", "o/r", "--workflow", workflow], runner=lambda a: (0, "", "")) == 2
    assert "--workflow" in capsys.readouterr().err


def test_non_numeric_run_id_refused(capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main(["--repo", "o/r", "--run-ids", "12,abc"], runner=lambda a: (0, "", "")) == 2
    assert "not numeric" in capsys.readouterr().err


def test_gh_failure_masks_token_and_caps_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    secret = "ghp_" + "A" * 36
    noisy = "\n".join(f"line {i} token {secret}" for i in range(12))

    code = audit.main(["--repo", "o/r", "--run-ids", "1"], runner=lambda a: (1, "", noisy))
    err = capsys.readouterr().err
    assert code == 2
    assert secret not in err and "***" in err
    assert "line 4" in err and "line 5" not in err
    assert "gh auth status" in err


def test_gh_calls_use_get_with_parameters_not_query_strings() -> None:
    seen: list[list[str]] = []

    def runner(args: list[str]) -> tuple[int, str, str]:
        seen.append(args)
        return 0, json.dumps({"workflow_runs": []}), ""

    audit.list_run_ids(runner, type("A", (), {"repo": "o/r", "workflow": "ci.yml", "runs": 5, "conclusion": "success"})())
    assert seen[0][:3] == ["api", "-X", "GET"]
    assert "?" not in seen[0][3] and "-f" in seen[0]


def test_gh_in_current_directory_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("gh.exe", "gh"):
        (tmp_path / name).write_text("", encoding="utf-8")
        os.chmod(tmp_path / name, 0o700)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(audit.AuditError, match="refusing gh inside the working tree"):
        audit.resolve_gh(None)


def test_missing_gh_gives_remedy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    with pytest.raises(audit.AuditError, match="gh auth login"):
        audit.resolve_gh("definitely-not-gh")


def test_json_runner_child_env_drops_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_run(argv: list[str], **kwargs: object) -> object:
        captured.update(kwargs)
        return type("R", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

    monkeypatch.setenv("GH_DEBUG", "api")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setattr(audit.subprocess, "run", fake_run)
    audit.make_runner("C:/x/gh.exe")(["api", "x"])
    assert "GH_DEBUG" not in captured["env"] and "DEBUG" not in captured["env"]
    assert captured["timeout"] == audit.TIMEOUT_SECONDS
    assert captured["creationflags"] == getattr(audit.subprocess, "CREATE_NO_WINDOW", 0)


@pytest.mark.parametrize("payload", [{"jobs": None}, {"jobs": "text"}, {"jobs": [None, 1, "x"]}, {"jobs": [{"steps": [None]}]}])
def test_adversarial_malformed_jobs_payload_is_tolerated(payload: dict, tmp_path: Path) -> None:
    (tmp_path / "run-7.json").write_text(json.dumps({"id": 7, "run_attempt": 1, "conclusion": "success"}), encoding="utf-8")
    (tmp_path / "jobs-7.json").write_text(json.dumps(payload), encoding="utf-8")
    assert audit.main(["--from-json", str(tmp_path)]) == 0  # an empty table, never a traceback


@pytest.mark.parametrize("stdout", ["[1, 2]", "[" * 5000 + "]" * 5000, "{" * 1000])
def test_adversarial_gh_output_that_is_not_an_object_is_refused(stdout: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert audit.main(["--repo", "o/r", "--run-ids", "1"], runner=lambda a: (0, stdout, "")) == 2
    assert "error:" in capsys.readouterr().err


def test_jobs_are_read_across_pages() -> None:
    def job(i: int) -> dict:
        return {"name": f"j{i}", "conclusion": "success", "created_at": "2026-01-05T10:00:00Z",
                "started_at": "2026-01-05T10:00:01Z", "completed_at": "2026-01-05T10:01:00Z",
                "steps": [{"name": "s", "conclusion": "success", "started_at": "2026-01-05T10:00:01Z",
                           "completed_at": "2026-01-05T10:01:00Z"}]}

    pages = {"1": [job(i) for i in range(100)], "2": [job(i) for i in range(100, 130)]}

    def runner(args: list[str]) -> tuple[int, str, str]:
        if args[3].endswith("/jobs"):
            page = next(a.split("=")[1] for a in args if a.startswith("page="))
            return 0, json.dumps({"jobs": pages[page]}), ""
        return 0, json.dumps({"id": 1, "run_attempt": 1, "conclusion": "success"}), ""

    _, jobs = audit.load_run(runner, "o/r", "1", None)
    assert len(jobs["jobs"]) == 130
