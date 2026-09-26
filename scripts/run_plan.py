#!/usr/bin/env python3
"""Relaunch a platform's headless CLI until a full /implement run reaches a terminal verdict.

    nexus-hub run-plan <plan> --platform <row> [--max-cycles N]

The completion gate keeps a live session going; this runner is the layer that
continues past a session that ended anyway (a platform's consecutive-block cap,
a crash, a closed terminal). After each cycle it asks
`check_plan_completion.py` for the verdict: a terminal verdict ends the loop, an
INCOMPLETE verdict with a higher progress score relaunches with the platform's
documented resume flag, and three cycles without progress record a
`no-progress` blocker and stop.

What this runner never does:
  - create approvals (the run record must already exist from /implement's
    upfront round),
  - add a permission-bypass, auto-approve, or config-override flag (a denylist
    is asserted per platform in tests), or launch when the platform's own
    configuration already bypasses approvals, unless the user approved the
    `unattended-with-bypass` class upfront,
  - invoke a shell: every launch is an argument list.

Launch and resume flags are hard-coded here from each vendor's CLI reference
(`docs/policy/completion-levers.json` documents the levers but is never read for
flags). The levers matrix decides which rows are offered: exactly the rows whose
headless lever is VERIFIED.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
NO_PROGRESS_CYCLES = 3
DEFAULT_MAX_CYCLES = 20
LOCK_STALE_SECONDS = 6 * 3600
SAFE_PLAN = re.compile(r"^[A-Za-z0-9._/\\:-]+$")
CMD_METACHARACTERS = set('&|<>^%!"')

# Flags that bypass approvals or override configuration. Never emitted by any
# template; the tests assert it for every row.
DENYLIST = (
    "--dangerously-skip-permissions",
    "--permission-mode",
    "bypassPermissions",
    "--dangerously-bypass-approvals-and-sandbox",
    "--full-auto",
    "danger-full-access",
    "approval_policy=never",
    "--approval-mode",
    "yolo",
    "--yolo",
    "--allow-all-tools",
    "--allow-all",
    "--force",
    "--yes-always",
)


# row id -> (launch(prompt), resume(prompt), supports a headless goal entry point)
TEMPLATES: dict[str, tuple] = {
    "claude": (
        lambda p: ["claude", "-p", p],
        lambda p: ["claude", "-p", p, "--continue"],
        True,
    ),
    "codex": (
        lambda p: ["codex", "exec", p],
        lambda p: ["codex", "exec", "resume", "--last", p],
        False,
    ),
    "cursor": (
        lambda p: ["agent", "-p", p],
        lambda p: ["agent", "--continue", "-p", p],
        False,
    ),
    "copilot": (
        lambda p: ["copilot", "-p", p],
        lambda p: ["copilot", "--continue", "-p", p],
        False,
    ),
    "copilot/cli": (
        lambda p: ["copilot", "-p", p],
        lambda p: ["copilot", "--continue", "-p", p],
        False,
    ),
    "gemini-cli": (
        lambda p: ["gemini", "-p", p],
        lambda p: ["gemini", "--resume", "latest", "-p", p],
        False,
    ),
    "antigravity2/cli": (
        lambda p: ["agy", "-p", p],
        lambda p: ["agy", "--continue", "-p", p],
        False,
    ),
    "qwen": (
        lambda p: ["qwen", "-p", p],
        lambda p: ["qwen", "--continue", "-p", p],
        True,
    ),
    "kimi": (
        lambda p: ["kimi", "-p", p],
        lambda p: ["kimi", "--continue", "-p", p],
        True,
    ),
    "opencode": (
        lambda p: ["opencode", "run", p],
        lambda p: ["opencode", "run", "-c", p],
        False,
    ),
    "windsurf/devin-cli": (
        lambda p: ["devin", "-p", p],
        lambda p: ["devin", "-c", "-p", p],
        False,
    ),
    "hermes": (
        lambda p: ["hermes", "chat", "-q", p],
        lambda p: ["hermes", "chat", "-c", "-q", p],
        False,
    ),
    "aider": (
        lambda p: ["aider", "--message", p],
        lambda p: ["aider", "--restore-chat-history", "--message", p],
        False,
    ),
    "pi": (lambda p: ["pi", "-p", p], lambda p: ["pi", "--continue", "-p", p], False),
    # OpenClaw needs a session selector on every call; SESSION is replaced with
    # the run nonce so launch and resume address the same session.
    "openclaw": (
        lambda p: ["openclaw", "agent", "--message", p, "--session-id", "SESSION"],
        lambda p: ["openclaw", "agent", "--message", p, "--session-id", "SESSION"],
        False,
    ),
}


class RunnerError(Exception):
    """Exit 2 with this message."""


def _checker() -> Path:
    override = os.environ.get("NEXUS_RUNNER_CHECKER")
    return Path(override) if override else SCRIPT_DIR / "check_plan_completion.py"


def _checker_run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(_checker()), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    return proc.returncode, proc.stdout


def validate_plan(plan: str) -> Path:
    if not SAFE_PLAN.match(plan):
        raise RunnerError(
            "plan path contains characters outside [A-Za-z0-9._/-]; refusing"
        )
    path = Path(plan)
    parts = path.as_posix().split("/")
    if path.suffix != ".md" or "plans" not in parts[:-1] or "docs" not in parts:
        raise RunnerError("plan must be a docs/**/plans/*.md file")
    if not path.is_file():
        raise RunnerError(f"plan not found: {plan}")
    return path


def resolve_binary(argv0: str) -> str:
    found = shutil.which(argv0)
    if not found:
        raise RunnerError(
            f"{argv0} is not installed or not on PATH; install the platform CLI first"
        )
    return found


def check_argv(argv: list[str]) -> None:
    """Refuse cmd metacharacters when the binary is a Windows .cmd/.bat shim.

    CreateProcess routes .cmd files through cmd.exe, which re-parses arguments,
    so an argument array is no longer shell-free there.
    """
    lowered = argv[0].lower()
    if lowered.endswith((".cmd", ".bat")):
        bad = [a for a in argv[1:] if CMD_METACHARACTERS & set(a)]
        if bad:
            raise RunnerError("refusing to pass cmd metacharacters through a .cmd shim")
    for arg in argv:
        if any(flag == arg or flag in arg.split("=") for flag in DENYLIST):
            raise RunnerError(f"refusing denylisted argument: {arg}")


def bypass_configured(row: str) -> str | None:
    """Return a reason when the platform's own configuration bypasses approvals."""
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    checks = {
        "claude": (
            home / ".claude" / "settings.json",
            r'"defaultMode"\s*:\s*"bypassPermissions"',
        ),
        "codex": (
            home / ".codex" / "config.toml",
            r'approval_policy\s*=\s*"never"|sandbox_mode\s*=\s*"danger-full-access"',
        ),
        "gemini-cli": (
            home / ".gemini" / "settings.json",
            r'"approvalMode"\s*:\s*"yolo"',
        ),
        "qwen": (home / ".qwen" / "settings.json", r'"approvalMode"\s*:\s*"yolo"'),
    }
    if row in checks:
        path, pattern = checks[row]
        try:
            if re.search(pattern, path.read_text(encoding="utf-8")):
                return f"{path} bypasses approvals"
        except OSError:
            pass
    return None


def goal_prompt(plan: str, nonce: str) -> str:
    return (
        f"/goal Complete /implement {plan}. The goal is met only when "
        f"check_plan_completion.py check {plan} prints a first line starting with "
        f"PLAN COMPLETE and ending with the run nonce {nonce}."
    )


class Lock:
    def __init__(self, record: Path) -> None:
        self.path = record.with_name(record.stem + ".runner.lock")
        self.held = False

    def __enter__(self) -> Lock:  # noqa: PYI034 - typing.Self needs 3.11; installers support 3.10
        try:
            if (
                self.path.exists()
                and time.time() - self.path.stat().st_mtime > LOCK_STALE_SECONDS
            ):
                self.path.unlink()
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RunnerError("another runner already holds this run record") from exc
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        self.held = True
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.held:
            self.path.unlink(missing_ok=True)


def _launch(argv: list[str], backoff: float) -> int:
    for attempt in (1, 2):
        try:
            code = subprocess.run(argv, check=False).returncode
        except OSError:
            code = -1
        if code == 0 or attempt == 2:
            return code
        time.sleep(backoff)
    return -1


def run(plan_arg: str, row: str, max_cycles: int) -> int:
    if row not in TEMPLATES:
        raise RunnerError(
            f"unknown platform {row!r}; choose one of: {', '.join(sorted(TEMPLATES))}"
        )
    plan = validate_plan(plan_arg)
    launch, resume, headless_goal = TEMPLATES[row]
    rc, out = _checker_run(["record", "path", str(plan)])
    if rc != 0:
        raise RunnerError(
            f"no run record for {plan}; run /implement {plan} first to record the upfront approvals"
        )
    record_path = Path(out.strip())
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunnerError(f"run record unreadable: {record_path}") from exc
    approved = {c.get("class") for c in record.get("approvals", {}).get("classes", [])}
    reason = bypass_configured(row)
    if reason and "unattended-with-bypass" not in approved:
        raise RunnerError(
            f"{reason}; approve the unattended-with-bypass class upfront or remove the setting"
        )
    binary = resolve_binary(launch("x")[0])
    backoff = float(os.environ.get("NEXUS_RUNNER_BACKOFF", "5"))
    with Lock(record_path):
        best = -1
        stalled = 0
        for cycle in range(1, max_cycles + 1):
            if cycle == 1:
                prompt = (
                    goal_prompt(plan.as_posix(), str(record.get("nonce", "-")))
                    if headless_goal
                    else f"/implement {plan.as_posix()}"
                )
                argv = launch(prompt)
            else:
                argv = resume(
                    f"Continue /implement {plan.as_posix()}. The completion checker still reports it incomplete."
                )
            argv = [
                binary,
                *(
                    str(record.get("nonce", "run")) if a == "SESSION" else a
                    for a in argv[1:]
                ),
            ]
            check_argv(argv)
            if _launch(argv, backoff) != 0 and cycle == 1:
                _checker_run(
                    [
                        "record",
                        "block",
                        str(plan),
                        "--category",
                        "platform-unavailable",
                        "--evidence",
                        f"{row} CLI failed twice on the first cycle",
                    ]
                )
                print("BLOCKED: platform-unavailable")
                return 3
            rc, out = _checker_run(["check", str(plan)])
            verdict = out.splitlines()[0] if out else ""
            if rc in (0, 3, 4):
                print(verdict)
                return rc
            if rc != 1:
                raise RunnerError(f"checker exited {rc}")
            _, score_out = _checker_run(["score", str(plan)])
            met = int(score_out.split()[0]) if score_out.split() else -1
            stalled = 0 if met > best else stalled + 1
            best = max(best, met)
            print(f"cycle {cycle}: {verdict}", file=sys.stderr)
            if stalled >= NO_PROGRESS_CYCLES:
                _checker_run(
                    [
                        "record",
                        "block",
                        str(plan),
                        "--category",
                        "no-progress",
                        "--evidence",
                        f"score {best} unchanged over {stalled} runner cycles",
                    ]
                )
                print("BLOCKED: no-progress")
                return 3
        print(f"INCOMPLETE after {max_cycles} cycles")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub run-plan",
        description="Relaunch a platform's headless CLI until the plan's completion verdict is terminal.",
        epilog="Platforms: " + ", ".join(sorted(TEMPLATES)),
    )
    parser.add_argument("plan", help="docs/**/plans/<plan>.md")
    parser.add_argument("--platform", required=True, choices=sorted(TEMPLATES))
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args.plan, args.platform, max(1, args.max_cycles))
    except RunnerError as exc:
        print(f"run-plan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
