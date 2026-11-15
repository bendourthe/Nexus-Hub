#!/usr/bin/env python3
"""Read-only GitHub Actions latency audit.

Splits every job of a workflow into queue, setup and work time, names the
critical-path job, and reports the time to the gate job and to the first failed
job. Only GitHub Actions is supported. All data comes from the user's own
authenticated ``gh`` (never unauthenticated HTTP) or from ``--from-json``
fixtures; nothing is written and no repository helper is imported.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW_RE = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")
RUN_ID_RE = re.compile(r"^[0-9]{1,20}$")
TOKEN_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}|Bearer\s+\S+|\b[A-Fa-f0-9]{32,}\b)"
)
CONTROL_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|[\x00-\x1f\x7f]")
TIMEOUT_SECONDS = 60
NAME_LIMIT = 80

Runner = Callable[[list[str]], "tuple[int, str, str]"]


class AuditError(Exception):
    """A refusal or failure that is reported as one short message."""


def mask(text: str) -> str:
    """Hide token-shaped strings."""
    return TOKEN_RE.sub("***", text)


def clean_name(value: object) -> str:
    """Make a job or step name safe for a Markdown table cell."""
    text = CONTROL_RE.sub(" ", str(value))
    text = " ".join(text.split())
    for char in "|`<>[]":
        text = text.replace(char, "\\" + char)
    return text if len(text) <= NAME_LIMIT else text[: NAME_LIMIT - 3] + "..."


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def seconds(start: datetime, end: datetime) -> float:
    return max(0.0, (end - start).total_seconds())


def repo_root_or_cwd() -> Path:
    here = Path.cwd().resolve()
    for parent in (here, *here.parents):
        if (parent / ".git").exists():
            return parent
    return here


def resolve_gh(explicit: str | None) -> str:
    found = shutil.which(explicit or "gh")
    if not found:
        raise AuditError("gh was not found. Install the GitHub CLI and run: gh auth login")
    resolved = Path(found).resolve()
    for base in {Path.cwd().resolve(), repo_root_or_cwd()}:
        if resolved == base or base in resolved.parents:
            raise AuditError(f"refusing gh inside the working tree: {resolved}")
    return str(resolved)


def make_runner(gh: str) -> Runner:
    env = {k: v for k, v in os.environ.items() if k not in ("GH_DEBUG", "DEBUG")}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # hidden console on Windows

    def run(args: list[str]) -> tuple[int, str, str]:
        try:
            done = subprocess.run(
                [gh, *args], capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
                env=env, stdin=subprocess.DEVNULL, creationflags=flags, check=False,
            )
        except subprocess.TimeoutExpired:
            return 124, "", f"gh timed out after {TIMEOUT_SECONDS} s"
        return done.returncode, done.stdout, done.stderr

    return run


def gh_json(runner: Runner, path: str, params: dict[str, str]) -> Any:
    args = ["api", "-X", "GET", path]
    for key, value in params.items():
        args += ["-f", f"{key}={value}"]
    code, out, err = runner(args)
    if code != 0:
        lines = mask(err).strip().splitlines()[:5]
        raise AuditError(
            f"gh failed (exit {code}): {' | '.join(lines) or 'no message'}. "
            "Remedy: run `gh auth status`, then retry or lower --runs."
        )
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise AuditError(f"gh returned invalid JSON: {exc.msg}") from exc


def load_run(runner: Runner | None, repo: str, run_id: str, fixtures: Path | None) -> tuple[dict, dict]:
    if fixtures is not None:
        try:
            run = json.loads((fixtures / f"run-{run_id}.json").read_text(encoding="utf-8"))
            jobs = json.loads((fixtures / f"jobs-{run_id}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise AuditError(f"fixture for run {run_id} unreadable: {exc}") from exc
        return run, jobs
    assert runner is not None
    run = gh_json(runner, f"repos/{repo}/actions/runs/{run_id}", {})
    jobs = gh_json(runner, f"repos/{repo}/actions/runs/{run_id}/jobs", {"filter": "latest", "per_page": "100"})
    return run, jobs


def split_job(job: dict) -> dict:
    """Return queue, setup, work and total seconds, or an incomplete marker."""
    created, started = parse_time(job.get("created_at")), parse_time(job.get("started_at"))
    done = parse_time(job.get("completed_at"))
    row = {"name": clean_name(job.get("name", "?")), "conclusion": job.get("conclusion"),
           "created": created, "started": started, "completed": done}
    if job.get("conclusion") in ("skipped", "cancelled"):
        row["status"] = str(job["conclusion"])
        return row
    steps = []
    for step in job.get("steps") or []:
        s0, s1 = parse_time(step.get("started_at")), parse_time(step.get("completed_at"))
        if s0 and s1 and step.get("conclusion") != "skipped":
            steps.append(seconds(s0, s1))
    if not (created and started and done) or not steps:
        row["status"] = "incomplete"
        return row
    total, work = seconds(started, done), max(steps)
    row.update(status="ok", queue=seconds(created, started), total=total, work=work,
               setup=max(0.0, total - work))
    return row


def analyze_run(run: dict, jobs_payload: dict, gate: str | None) -> dict:
    jobs = [split_job(j) for j in jobs_payload.get("jobs", []) if isinstance(j, dict)]
    ok = [j for j in jobs if j["status"] == "ok"]
    start = parse_time(run.get("run_started_at")) or parse_time(run.get("created_at")) or min((j["created"] for j in ok if j["created"]), default=None)
    gate_job = next((j for j in ok if gate and j["name"] == clean_name(gate)), None)
    others = [j for j in ok if j is not gate_job]

    def aggregate(job: dict) -> bool:
        rest = [o for o in others if o is not job]
        if len(rest) < 2:
            return False
        running = [o for o in rest if o["completed"] and job["started"] and o["completed"] > job["started"]]
        return len(running) <= 1

    pool = [j for j in others if not aggregate(j)] or others
    critical = max(pool, key=lambda j: j["completed"], default=None)
    failed = [j for j in jobs if j.get("conclusion") == "failure" and j["completed"]]
    first_fail = min((j["completed"] for j in failed), default=None)
    return {
        "run_id": run.get("id"), "attempt": run.get("run_attempt", 1), "jobs": jobs,
        "gate_seconds": seconds(start, gate_job["completed"]) if start and gate_job else None,
        "first_failure_seconds": seconds(start, first_fail) if start and first_fail else None,
        "critical": critical["name"] if critical else None,
        "skipped": [j["name"] for j in jobs if j["status"] in ("skipped", "cancelled")],
        "incomplete": [j["name"] for j in jobs if j["status"] == "incomplete"],
    }


def stat(values: list[float]) -> dict:
    return {"mean": statistics.fmean(values), "median": statistics.median(values), "max": max(values)}


def summarize(analyses: list[dict]) -> dict:
    per_job: dict[str, dict[str, list[float]]] = {}
    for a in analyses:
        for j in a["jobs"]:
            if j["status"] == "ok":
                bucket = per_job.setdefault(j["name"], {"total": [], "queue": [], "setup": [], "work": []})
                for key in bucket:
                    bucket[key].append(j[key])
    rows = {n: {k: stat(v) for k, v in b.items()} | {"runs": len(b["total"])} for n, b in per_job.items()}
    gates = [a["gate_seconds"] for a in analyses if a["gate_seconds"] is not None]
    fails = [a["first_failure_seconds"] for a in analyses if a["first_failure_seconds"] is not None]
    crit: dict[str, int] = {}
    for a in analyses:
        if a["critical"]:
            crit[a["critical"]] = crit.get(a["critical"], 0) + 1
    return {
        "runs": len(analyses), "jobs": rows, "gate": stat(gates) if gates else None,
        "first_failure": stat(fails) if fails else None,
        "critical_path": max(crit, key=lambda k: crit[k]) if crit else None,
        "critical_counts": crit,
        "skipped": sorted({n for a in analyses for n in a["skipped"]}),
        "incomplete": sorted({n for a in analyses for n in a["incomplete"]}),
        "excluded_runs": analyses[0].get("excluded_runs", []),
    }


def minutes(value: float) -> str:
    return f"{value / 60:.1f}"


def render(summary: dict, gate: str | None) -> str:
    lines = [f"CI latency audit over {summary['runs']} run(s). Times in minutes except queue and work (seconds).", "",
             "| Job | Runs | Mean total | Median total | Max total | Mean queue (s) | Mean setup | Mean work (s) |",
             "|---|---|---|---|---|---|---|---|"]
    for name, row in sorted(summary["jobs"].items(), key=lambda kv: -kv[1]["total"]["mean"]):
        lines.append(f"| {name} | {row['runs']} | {minutes(row['total']['mean'])} | {minutes(row['total']['median'])} "
                     f"| {minutes(row['total']['max'])} | {row['queue']['mean']:.0f} | {minutes(row['setup']['mean'])} "
                     f"| {row['work']['mean']:.0f} |")
    lines.append("")
    lines.append(f"Critical-path job: {summary['critical_path'] or 'none found'}")
    if summary["gate"]:
        g = summary["gate"]
        lines.append(f"Time to gate `{clean_name(gate or '')}`: mean {minutes(g['mean'])}, median {minutes(g['median'])}, "
                     f"max {minutes(g['max'])}")
    elif gate:
        lines.append(f"Time to gate `{clean_name(gate)}`: not found in any run")
    if summary["first_failure"]:
        lines.append(f"Time to first failed job: median {minutes(summary['first_failure']['median'])}")
    if summary["skipped"]:
        lines.append("Skipped or cancelled (excluded): " + ", ".join(summary["skipped"]))
    if summary["incomplete"]:
        lines.append("Incomplete (excluded, never counted as zero): " + ", ".join(summary["incomplete"]))
    return "\n".join(lines)


def validate_args(args: argparse.Namespace) -> list[str]:
    repo = args.repo or ""
    if not args.from_json and ("://" in repo or repo.startswith("git@")):
        raise AuditError("only GitHub Actions is supported; pass --repo owner/name for a GitHub repository")
    if not args.from_json and not REPO_RE.match(repo):
        raise AuditError("--repo must look like owner/name (letters, digits, dot, dash, underscore)")
    if args.workflow and not WORKFLOW_RE.match(args.workflow):
        raise AuditError("--workflow must be a workflow file name such as ci.yml")
    ids = [x for x in (args.run_ids or "").split(",") if x]
    for item in ids:
        if not RUN_ID_RE.match(item):
            raise AuditError(f"run id is not numeric: {clean_name(item)}")
    if not ids and not args.workflow and not args.from_json:
        raise AuditError("give --run-ids, or --workflow with --runs")
    return ids


def list_run_ids(runner: Runner, args: argparse.Namespace) -> list[str]:
    status = "completed" if args.conclusion == "any" else args.conclusion
    data = gh_json(runner, f"repos/{args.repo}/actions/workflows/{args.workflow}/runs",
                   {"status": status, "per_page": str(max(1, min(args.runs, 100)))})
    return [str(r["id"]) for r in data.get("workflow_runs", []) if isinstance(r, dict) and "id" in r]


def collect(args: argparse.Namespace, runner: Runner | None, ids: list[str]) -> list[dict]:
    fixtures = Path(args.from_json) if args.from_json else None
    if fixtures and not ids:
        ids = sorted(p.stem[4:] for p in fixtures.glob("run-*.json"))
    elif not ids and runner:
        ids = list_run_ids(runner, args)
    seen: set[tuple[str, object]] = set()
    analyses: list[dict] = []
    excluded: list[str] = []
    for run_id in ids:
        run, jobs = load_run(runner, args.repo, run_id, fixtures)
        key = (run_id, run.get("run_attempt", 1))
        if key in seen:
            continue
        seen.add(key)
        head = (run.get("head_repository") or {}).get("full_name")
        base = (run.get("repository") or {}).get("full_name")
        if (run.get("run_attempt") or 1) > 1:
            excluded.append(f"run {run_id} attempt {run['run_attempt']} (re-run: jobs mix attempts)")
            continue
        if not args.include_forks and (run.get("event") == "pull_request_target" or (head and base and head != base)):
            continue
        if args.conclusion != "any" and run.get("conclusion") != args.conclusion:
            continue
        analyses.append(analyze_run(run, jobs, args.gate))
    if analyses:
        analyses[0]["excluded_runs"] = excluded
    return analyses


def main(argv: Sequence[str] | None = None, runner: Runner | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only GitHub Actions CI latency audit (GitHub Actions only).")
    parser.add_argument("--repo")
    parser.add_argument("--workflow")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--run-ids")
    parser.add_argument("--from-json")
    parser.add_argument("--conclusion", choices=("success", "failure", "any"), default="success")
    parser.add_argument("--gate")
    parser.add_argument("--include-forks", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--gh")
    args = parser.parse_args(argv)
    try:
        ids = validate_args(args)
        if not args.from_json and runner is None:
            runner = make_runner(resolve_gh(args.gh))
        analyses = collect(args, runner, ids)
        if not analyses:
            raise AuditError("no runs matched; check --conclusion, --include-forks and the run selection")
        summary = summarize(analyses)
    except AuditError as exc:
        print(f"error: {mask(str(exc))}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=1) if args.json else render(summary, args.gate))
    return 0


if __name__ == "__main__":
    sys.exit(main())
