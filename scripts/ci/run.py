#!/usr/bin/env python3
"""Run a repository-native CI profile.

    python scripts/ci/run.py --profile fast
    python scripts/ci/run.py --profile full --reports-dir reports
    python scripts/ci/run.py --profile platform --platform windows
    python scripts/ci/run.py --profile full --list          # print, run nothing
    python scripts/ci/run.py --profile full --base origin/develop

No CI provider is required or consulted. Nothing here reads a GitHub
environment variable, and `--base` takes an ordinary git revision.

Exit status is 0 only when every required command passed. An advisory command
that fails is reported and does not change the status; a command that times out,
crashes, or cannot be found DOES, because "the tool is missing" and "the tool
passed" must never look the same.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ci import PROFILE_NAMES  # noqa: E402
from scripts.ci import change_scope, reporting  # noqa: E402
from scripts.ci.profiles import Command, Group, detect_platform, groups_for  # noqa: E402
from scripts.ci.reporting import CommandResult, GroupResult, RunResult  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tool_versions() -> dict[str, str]:
    """Best-effort versions for the report. Never fails the run."""
    tools: dict[str, str] = {"python": sys.version.split()[0]}
    for name, argv in (("git", ["git", "--version"]), ("shellcheck", ["shellcheck", "--version"])):
        if not shutil.which(argv[0]):
            continue
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            first = next((ln for ln in proc.stdout.splitlines() if ln.strip()), "")
            tools[name] = first.strip()
        except (OSError, subprocess.SubprocessError):
            continue
    return tools


def run_command(cmd: Command, repo_root: Path, secrets: list[str], quiet: bool) -> CommandResult:
    """Execute one command, capturing output and never raising."""
    cwd = (repo_root / cmd.cwd).resolve()
    started = time.monotonic()

    if not cwd.is_dir():
        return CommandResult(
            name=cmd.name, group="", status="missing", reason=f"working directory not found: {cmd.cwd}"
        )

    # An executable that is not on PATH is MISSING, not passing. The engine
    # deliberately does not fall back to a shell lookup: `shell=True` would let
    # a path containing a space (this repository lives under one) re-split.
    if not Path(cmd.argv[0]).is_absolute() and shutil.which(cmd.argv[0]) is None:
        return CommandResult(
            name=cmd.name,
            group="",
            status="missing",
            reason=f"executable not found on PATH: {cmd.argv[0]}",
            duration_s=time.monotonic() - started,
        )

    env = os.environ.copy()
    env.update(cmd.env)
    # Deterministic output across hosts: an unset locale changes sort order and
    # number formatting, which would make two identical runs produce different
    # reports.
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    try:
        proc = subprocess.run(
            list(cmd.argv),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=cmd.timeout,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            name=cmd.name,
            group="",
            status="timeout",
            duration_s=time.monotonic() - started,
            reason=f"exceeded {cmd.timeout}s",
        )
    except OSError as exc:
        return CommandResult(
            name=cmd.name,
            group="",
            status="missing",
            duration_s=time.monotonic() - started,
            reason=f"{type(exc).__name__}: {exc}",
        )

    duration = time.monotonic() - started
    output = reporting.redact((proc.stdout or "") + (proc.stderr or ""), secrets)
    passed = proc.returncode == 0
    status = "pass" if passed else ("advisory-fail" if cmd.advisory else "fail")

    if not quiet or not passed:
        mark = "ok  " if passed else "FAIL"
        print(f"  [{mark}] {cmd.name} ({duration:.1f}s)")
        if not passed:
            tail = output.rstrip().splitlines()[-12:]
            for line in tail:
                print(f"         {line}")

    return CommandResult(
        name=cmd.name,
        group="",
        status=status,
        duration_s=duration,
        exit_code=proc.returncode,
        output=output,
        reason="" if passed else f"exit {proc.returncode}",
    )


def run_group(
    group: Group,
    platform: str,
    decision: change_scope.ScopeDecision,
    repo_root: Path,
    secrets: list[str],
    quiet: bool,
) -> GroupResult:
    result = GroupResult(name=group.name)

    if not decision.is_required(group.scope_key):
        result.status = "skip"
        result.skipped_reason = decision.skipped.get(
            group.scope_key or "", "not required by the change scope"
        )
        print(f"- {group.name}: SKIP ({result.skipped_reason})")
        return result

    applicable = [c for c in group.commands if c.runs_on(platform)]
    off_platform = [c for c in group.commands if not c.runs_on(platform)]

    if not applicable:
        result.status = "skip"
        result.skipped_reason = f"no command in this group runs on {platform}"
        print(f"- {group.name}: SKIP ({result.skipped_reason})")
        return result

    print(f"- {group.name}")
    for cmd in off_platform:
        result.commands.append(
            CommandResult(
                name=cmd.name,
                group=group.name,
                status="skip",
                reason=f"scoped to {', '.join(cmd.platforms)}; host is {platform}",
            )
        )

    for cmd in applicable:
        outcome = run_command(cmd, repo_root, secrets, quiet)
        outcome.group = group.name
        result.commands.append(outcome)
        if outcome.counts_as_failure:
            result.status = "fail"

    return result


def select_groups(profile: str, only: list[str] | None) -> tuple[Group, ...]:
    """Resolve `--only` against a profile, failing loudly on an unknown name.

    A typo must be an ERROR, not an empty selection. Silently running nothing is
    the worst outcome available: the job goes green having proved nothing, which
    is the same fail-open shape the change classifier is built to avoid.
    """
    groups = groups_for(profile)
    if not only:
        return groups
    available = {g.name for g in groups}
    unknown = [name for name in only if name not in available]
    if unknown:
        raise KeyError(
            f"unknown group(s) {unknown} for profile {profile!r}; "
            f"available: {sorted(available)}"
        )
    wanted = set(only)
    return tuple(g for g in groups if g.name in wanted)


def run_profile(
    profile: str,
    platform: str | None = None,
    reports_dir: Path | None = None,
    base: str | None = None,
    quiet: bool = False,
    only: list[str] | None = None,
    repo_root: Path = REPO_ROOT,
) -> RunResult:
    host = platform or detect_platform()
    decision = change_scope.classify(base, repo_root=repo_root) if base else change_scope._all_required(
        "no --base supplied; running every group"
    )
    secrets = reporting.secret_values()

    started_wall = _now()
    started = time.monotonic()
    result = RunResult(
        profile=profile,
        platform=host,
        started_at=started_wall,
        scope_reason=decision.reason,
        scope_conservative=decision.conservative,
    )

    print(f"profile: {profile}   platform: {host}")
    if decision.reason:
        print(f"scope:   {decision.reason}")

    for group in select_groups(profile, only):
        group_result = run_group(group, host, decision, repo_root, secrets, quiet)
        result.groups.append(group_result)
        if group.blocking and group_result.status == "fail":
            print(f"! blocking group {group.name} failed; stopping before later groups")
            break

    result.duration_s = time.monotonic() - started
    result.finished_at = _now()

    if reports_dir is not None:
        written = reporting.write_reports(result, reports_dir, repo_root, _tool_versions())
        if written and not quiet:
            print(f"reports: {reports_dir}")

    return result


def _print_listing(profile: str, host: str, only: list[str] | None = None) -> None:
    # Resolve BEFORE printing the header, so an unknown group name produces an
    # error and nothing else. A header followed by an error reads as a partial
    # listing rather than a rejected request.
    selected = select_groups(profile, only)
    print(f"profile: {profile}   platform: {host}")
    for group in selected:
        scope = group.scope_key or "always"
        flags = " (blocking)" if group.blocking else ""
        print(f"  {group.name}  [scope: {scope}]{flags}")
        for cmd in group.commands:
            applies = "" if cmd.runs_on(host) else f"  -- skipped on {host}"
            advisory = " (advisory)" if cmd.advisory else ""
            print(f"    - {cmd.name}{advisory}{applies}")
    if not selected:
        print("  (aggregation only; runs no commands)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/ci/run.py",
        description="Run a repository-native CI profile. Requires no CI provider.",
    )
    parser.add_argument("--profile", required=True, choices=PROFILE_NAMES)
    parser.add_argument("--platform", choices=("linux", "macos", "windows"), default=None)
    parser.add_argument("--reports-dir", default=None, help="where to write reports (default: none)")
    parser.add_argument("--base", default=None, help="git revision to scope the run against")
    parser.add_argument("--quiet", action="store_true", help="suppress per-command output on success")
    parser.add_argument(
        "--only",
        default=None,
        help="comma-separated group names to run from the profile. An unknown "
             "name is an error, never an empty selection.",
    )
    parser.add_argument("--list", action="store_true", help="print the resolved commands and exit 0")
    parser.add_argument("--json", action="store_true", help="print the machine-readable summary")
    args = parser.parse_args(argv)

    host = args.platform or detect_platform()
    only = [g.strip() for g in args.only.split(",") if g.strip()] if args.only else None

    try:
        if args.list:
            _print_listing(args.profile, host, only)
            return 0
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    reports_dir = Path(args.reports_dir).resolve() if args.reports_dir else None
    try:
        result = run_profile(
            profile=args.profile,
            platform=args.platform,
            reports_dir=reports_dir,
            base=args.base,
            quiet=args.quiet,
            only=only,
        )
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        import json

        from dataclasses import asdict

        print(json.dumps(asdict(result), indent=2, sort_keys=True))

    counts = result.tally()
    print(
        f"\n{result.status}: {counts['pass']} passed, "
        f"{counts['fail'] + counts['timeout'] + counts['missing']} failed, "
        f"{counts['skip']} skipped, {counts['advisory-fail']} advisory "
        f"in {result.duration_s:.1f}s"
    )
    return 0 if result.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
