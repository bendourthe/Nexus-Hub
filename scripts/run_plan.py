#!/usr/bin/env python3
"""Relaunch a platform's headless CLI until a full /implement run reaches a terminal verdict.

    nexus-hub run-plan <plan> --platform <row> [--max-cycles N]
    nexus-hub run-plan vX.Y --platform <row> [--max-cycles N]     (a whole minor)

The completion gate keeps a live session going; this runner is the layer that
continues past a session that ended anyway (a platform's consecutive-block cap,
a crash, a closed terminal). After each cycle it asks
`check_plan_completion.py` for the verdict: a terminal verdict ends the loop, an
INCOMPLETE verdict with a higher progress score relaunches with the platform's
documented resume flag, and three cycles without progress record a
`no-progress` blocker and stop. A `vX.Y` scope drives the schema-2 minor record
the same way through `check-minor` and `score-minor`, so `no-progress` applies to
the minor score; the per-plan path is unchanged.

What this runner never does:
  - create approvals (the run record must already exist from /implement's
    upfront round); every session it launches carries NEXUS_RUNNER_LAUNCH=1,
    so the capture hook skips its prompts and `record create` refuses there,
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
from contextlib import contextmanager
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import approval_page  # installed as a sibling in ~/.nexus-hub/scripts/

NO_PROGRESS_CYCLES = 3
DEFAULT_MAX_CYCLES = 20
LOCK_STALE_SECONDS = 6 * 3600
SAFE_PLAN = re.compile(r"^[A-Za-z0-9._/\\:-]+$")
MINOR_TOKEN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)$")
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


# row id -> (launch(prompt), resume(prompt), supports a headless goal entry point).
# A headless goal is set only where the vendor documents `<cli> -p "/goal ..."`
# (docs/policy/completion-levers.json `native_goal.headless_entry`): Claude Code,
# Qwen Code, and Kimi Code CLI. Copilot CLI's documented headless path is
# `copilot --autopilot -p` with a bypass flag, not /goal, so it stays interactive.
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

# Extra flags on the goal-setting launch. Claude Code documents stream-json with
# --verbose so a long goal loop shows progress instead of looking stuck.
GOAL_FLAGS: dict[str, list[str]] = {"claude": ["--output-format", "stream-json", "--verbose"]}
# Kimi's prompt-mode goal exits 3 when the goal is blocked and 6 when it is paused
# (completion-levers.json `kimi.native_goal.goal_exit_codes`). Such an exit counts as
# a run, not a launch failure, only when the checker then reports BLOCKED or PAUSED;
# otherwise it is retried and, on the first cycle, recorded as platform-unavailable.
GOAL_EXITS: dict[str, set[int]] = {"kimi": {3, 6}}
# Rows whose goal command is documented for interactive use only: the runner cannot
# set it, so it prints the line for the user to type in that session.
INTERACTIVE_GOAL_ROWS = {"codex", "cursor", "copilot", "copilot/cli", "antigravity2/cli", "hermes", "openclaw"}
PLAN_VERSION = re.compile(r"^(v\d+\.\d+\.\d+)(?:-|\.md$)")


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


def _which_on_path(name: str) -> str | None:
    """Find `name` on PATH's absolute entries only, never in the current directory.

    `shutil.which` on Windows searches the current directory first, so a `claude.cmd`
    planted at the repository root would be launched as the platform CLI. Same rule
    as `repo_host._which_on_path`; kept local so the runner has no import
    dependency on the checker it invokes as a subprocess.
    """
    exts = [""]
    if os.name == "nt":
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        base = Path(entry)
        if not entry or not base.is_absolute():
            continue
        for ext in exts:
            candidate = base / (name + ext)
            if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return str(candidate)
    return None


def resolve_binary(argv0: str) -> str:
    found = _which_on_path(argv0)
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


# row -> (format, user-scope files under home, project-scope files under the launch
# directory, {key: values that remove approval}). Scopes are the documented ones in
# docs/policy/platform-defaults-levers.md: Claude `.claude/settings.json` and
# `.claude/settings.local.json`; Codex `.codex/config.toml` (trusted projects may
# override approval_policy and sandbox_mode since 2026-10-01); Gemini CLI and Qwen
# `.gemini/settings.json` / `.qwen/settings.json`; Cursor CLI's project file holds
# permissions only, so only its global `cli-config.json` is read. Copilot, OpenCode,
# and Kimi document no approval key a file can set, so they have no row here.
BYPASS_SETTINGS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...], dict[str, set[str]]]] = {
    "claude": (
        "json",
        (".claude/settings.json",),
        (".claude/settings.json", ".claude/settings.local.json"),
        {"defaultMode": {"bypassPermissions"}},
    ),
    "codex": (
        "toml",
        (".codex/config.toml",),
        (".codex/config.toml",),
        {"approval_policy": {"never"}, "sandbox_mode": {"danger-full-access"}},
    ),
    "gemini-cli": (
        "json",
        (".gemini/settings.json",),
        (".gemini/settings.json",),
        {"approvalMode": {"yolo"}, "defaultApprovalMode": {"yolo"}},
    ),
    "qwen": ("json", (".qwen/settings.json",), (".qwen/settings.json",), {"approvalMode": {"yolo"}}),
    "cursor": ("json", (".cursor/cli-config.json",), (), {"approvalMode": {"unrestricted"}}),
}


def _load_toml(text: str) -> object:
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover - installers still support 3.10
        import tomli as tomllib  # type: ignore[no-redef]  # ImportError falls through to the text scan
    return tomllib.loads(text)


def _has_bypass(node: object, keys: dict[str, set[str]]) -> bool:
    """True when any nested mapping sets one of `keys` to a bypassing value.
    Nested keys count everywhere (a Codex profile table, Claude's `permissions`):
    reporting a bypass that might not be active only asks for the approval."""
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and value in keys.get(key, ()):
                return True
            if _has_bypass(value, keys):
                return True
    elif isinstance(node, list):
        return any(_has_bypass(item, keys) for item in node)
    return False


def _text_has_bypass(text: str, keys: dict[str, set[str]]) -> bool:
    """Fallback for a file that does not parse: match either quote style, so an
    unparseable file can never hide a bypass the parser would have found."""
    return any(
        re.search(rf"""["']?{re.escape(key)}["']?\s*[:=]\s*["']{re.escape(value)}["']""", text)
        for key, values in keys.items()
        for value in values
    )


def bypass_configured(row: str, launch_dir: Path | None = None) -> str | None:
    """Return a reason when the platform's own configuration, at user scope or in
    the project the runner launches from, bypasses approvals."""
    if row not in BYPASS_SETTINGS:
        return None
    fmt, user_files, project_files, keys = BYPASS_SETTINGS[row]
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    project = launch_dir or Path.cwd()
    candidates = [home / rel for rel in user_files] + [project / rel for rel in project_files]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            # An unreadable config cannot declare a bypass; the next candidate is checked.
            continue
        try:
            found = _has_bypass(_load_toml(text) if fmt == "toml" else json.loads(text), keys)
        except (ImportError, ValueError):
            # ValueError covers JSONDecodeError and TOMLDecodeError.
            found = _text_has_bypass(text, keys)
        if found:
            return f"{path} bypasses approvals"
    return None


def goal_prompt(scope: str) -> str | None:
    """The approval page's goal line without an approval code, or None when the
    scope is not a version token. Runner-launched sessions are never captured, so
    the line sets only the goal; the checker stays the authority on done."""
    try:
        return approval_page.goal_line(scope)
    except approval_page.PageError:
        return None


class Scope:
    """The checker arguments for one plan or one minor; everything else in the loop is shared."""

    def __init__(self, target: str) -> None:
        self.minor = bool(MINOR_TOKEN.match(target))
        self.repo_root = Path.cwd().resolve()
        self.label = target if self.minor else validate_plan(target).as_posix()
        found = PLAN_VERSION.match(Path(self.label).name)
        self.version = target if self.minor else (found.group(1) if found else "")

    def path(self) -> list[str]:
        return ["record", "path", "--minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["record", "path", self.label]

    def check(self) -> list[str]:
        return ["check-minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["check", self.label]

    def score(self) -> list[str]:
        return ["score-minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["score", self.label]

    def block(self, category: str, evidence: str) -> list[str]:
        scope = ["--minor", self.label, "--repo", str(self.repo_root)] if self.minor else [self.label]
        return ["record", "block", *scope, "--category", category, "--evidence", evidence]


class Lock:
    def __init__(self, record: Path) -> None:
        self.path = record.with_name(record.stem + ".runner.lock")
        self.held = False
        self.identity: tuple[int, int] | None = None
        self.pid_written = False

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
        try:
            info = os.fstat(fd)
            self.identity = (info.st_dev, info.st_ino)
            self.held = True
            payload = str(os.getpid()).encode('ascii')
            if os.write(fd, payload) != len(payload):
                raise OSError('incomplete runner lock write')
            self.pid_written = True
        finally:
            os.close(fd)
        return self

    def refresh(self) -> None:
        """Mark the lock live; called every cycle so a long run never looks stale."""
        if self.held:
            try:
                os.utime(self.path)
            except OSError:
                # Best effort: a lock that cannot be touched only risks looking stale later.
                pass

    def __exit__(self, *_exc: object) -> None:
        # PID text alone cannot distinguish a replaced file from the one we created.
        if not self.held or self.identity is None:
            return
        try:
            entry = self.path.lstat()
            if (entry.st_dev, entry.st_ino) != self.identity:
                self.held = False
                return
            with self.path.open('r', encoding='ascii') as handle:
                opened = os.fstat(handle.fileno())
                if (opened.st_dev, opened.st_ino) != self.identity:
                    return
                owner = handle.read().strip()
            current = self.path.lstat()
            if (current.st_dev, current.st_ino) != self.identity:
                self.held = False
                return
            if self.pid_written and owner != str(os.getpid()):
                return
            self.path.unlink()
            self.held = False
        except (OSError, UnicodeError):
            # Uncertain filesystem ownership must never remove another entry.
            return


def record_blocker(scope: Scope, category: str, evidence: str) -> int:
    """Write a blocker and report it only when the checker confirms it was written.

    `record block` prints `BLOCKED: <category>` and exits 3 once the blocker is in the
    record. Any other answer (a tampered record, no record, a refusal) means nothing
    was written: that verdict is printed instead, never the blocker this runner meant.
    """
    rc, out = _checker_run(scope.block(category, evidence))
    first = out.splitlines()[0] if out else ""
    if rc == 3 and first == f"BLOCKED: {category}":
        print(first)
        return 3
    print(
        f"run-plan: the {category} blocker was not recorded (checker exit {rc}: {first or 'no output'})",
        file=sys.stderr,
    )
    if rc in (3, 4) and first:
        print(first)
        return rc
    return 2


def _launch(argv: list[str], backoff: float, settled: Callable[[int], bool] | None = None) -> int:
    """Run one session, retrying once. `settled(code)` may accept a non-zero exit
    (returning 0 for it) when the checker confirms what that exit claims."""
    # Every session this runner launches is marked, so its prompts are never
    # captured, and never recorded, as the user's approval (v4.13.2 WN-9).
    env = {**os.environ, "NEXUS_RUNNER_LAUNCH": "1"}
    for attempt in (1, 2):
        try:
            code = subprocess.run(argv, check=False, env=env).returncode
        except OSError:
            code = -1
        if code != 0 and settled is not None and settled(code):
            return 0
        if code == 0 or attempt == 2:
            return code
        time.sleep(backoff)
    return -1



def _verified_runner_minor(record_path: Path, record: dict):
    import check_plan_completion as ck
    try:
        ctx, verified = ck.resolve_minor_controller(record_path, str(record.get('session_id') or ''))
    except (OSError, ValueError, ck.Malformed) as exc:
        raise RunnerError('minor controller could not be verified') from exc
    if Path.cwd().resolve() != ctx.root:
        raise RunnerError('restart run-plan from the verified operational controller')
    return ctx, verified


@contextmanager
def controller_runner_lock(scope, record_path: Path, record: dict):
    if not scope.minor:
        with Lock(record_path) as lock:
            yield lock
        return
    import check_plan_completion as ck
    lock = Lock(record_path)
    try:
        try:
            with ck.minor_transaction(record):
                lock.__enter__()
        except (ck.Malformed, OSError) as exc:
            raise RunnerError(f'minor runner acquisition failed: {exc}') from exc
        yield lock
    finally:
        # Covers lease-exit, CAS and I/O failures after exclusive lock creation.
        lock.__exit__(None, None, None)


def run(plan_arg: str, row: str, max_cycles: int) -> int:
    if row not in TEMPLATES:
        raise RunnerError(
            f"unknown platform {row!r}; choose one of: {', '.join(sorted(TEMPLATES))}"
        )
    scope = Scope(plan_arg)
    label = scope.label
    launch, resume, headless_goal = TEMPLATES[row]
    rc, out = _checker_run(scope.path())
    if rc != 0:
        raise RunnerError(
            f"no run record for {label}; run /implement {label} first to record the upfront approvals"
        )
    record_path = Path(out.strip())
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunnerError(f"run record unreadable: {record_path}") from exc
    minor_ctx = None
    if scope.minor:
        minor_ctx, record = _verified_runner_minor(record_path, record)
        scope.repo_root = minor_ctx.root
    approved = {c.get("class") for c in record.get("approvals", {}).get("classes", [])}
    reason = bypass_configured(row)
    full_access = False
    context = record.get('approvals', {}).get('authorization_context') or {}
    if (context.get('origin') in {'host-hook-capture', 'codex-host-transcript'}
            and context.get('permission_mode') == 'bypassPermissions'
            and context.get('session_id') == record.get('session_id')):
        # record path only locates a file. A terminal check must authenticate it before this mode is trusted.
        verified_rc, verified_out = _checker_run(scope.check())
        if verified_rc not in (0, 1, 3, 4) or verified_out.startswith('BLOCKED: record-tampered'):
            raise RunnerError('run record authorization could not be verified')
        import approval_binding
        try:
            import check_plan_completion as ck
            roots = ck._host_cwds(minor_ctx) if minor_ctx is not None else {str(Path.cwd().resolve())}
            current = approval_binding.current_host_context(record_path.parent, record, roots,
                historical_cwds=ck.historical_host_cwds(record) if scope.minor else set())
            full_access = approval_binding.full_access_authorization(record, current)
        except ValueError:
            full_access = False
    if reason and "unattended-with-bypass" not in approved and not full_access:
        raise RunnerError(
            f"{reason}; approve the unattended-with-bypass class upfront or remove the setting"
        )
    binary = resolve_binary(launch("x")[0])
    backoff = float(os.environ.get("NEXUS_RUNNER_BACKOFF", "5"))
    with controller_runner_lock(scope, record_path, record) as lock:
        # A run whose verdict is already terminal (the first turn completed it, a
        # blocker was recorded, or the user paused it) has nothing to resume, and a
        # resumed session there only spends money restating the stop.
        rc, out = _checker_run(scope.check())
        if rc in (0, 3, 4):
            print(out.splitlines()[0] if out else "")
            return rc
        if rc != 1:
            raise RunnerError(f"checker exited {rc}")
        best = -1
        stalled = 0
        goal = goal_prompt(scope.version)
        if goal and row in INTERACTIVE_GOAL_ROWS:
            print(f"run-plan: {row} sets its goal only when you type it; to add it, type: {goal}", file=sys.stderr)
        for cycle in range(1, max_cycles + 1):
            lock.refresh()
            # Every cycle RESUMES: the run record exists only because /implement's
            # upfront round ran in a session, and a fresh session would carry a
            # different session id, so the turn-end gate bound to the record would
            # never fire in it. The first cycle also sets the goal where a platform
            # documents a headless goal entry point.
            goal_cycle = cycle == 1 and headless_goal and goal is not None
            if goal_cycle:
                argv = [*resume(goal), *GOAL_FLAGS.get(row, [])]
            else:
                argv = resume(
                    f"Continue /implement {label}. The completion checker still reports it incomplete."
                )
            argv = [
                binary,
                *(
                    str(record.get("nonce", "run")) if a == "SESSION" else a
                    for a in argv[1:]
                ),
            ]
            check_argv(argv)
            documented = GOAL_EXITS.get(row, set()) if goal_cycle else set()

            def settled(code: int) -> bool:
                return code in documented and _checker_run(scope.check())[0] in (3, 4)

            if _launch(argv, backoff, settled) != 0 and cycle == 1:
                return record_blocker(scope, "platform-unavailable", f"{row} CLI failed twice on the first cycle")
            rc, out = _checker_run(scope.check())
            verdict = out.splitlines()[0] if out else ""
            if rc in (0, 3, 4):
                print(verdict)
                return rc
            if rc != 1:
                raise RunnerError(f"checker exited {rc}")
            _, score_out = _checker_run(scope.score())
            met = int(score_out.split()[0]) if score_out.split() else -1
            stalled = 0 if met > best else stalled + 1
            best = max(best, met)
            print(f"cycle {cycle}: {verdict}", file=sys.stderr)
            if stalled >= NO_PROGRESS_CYCLES:
                return record_blocker(scope, "no-progress", f"score {best} unchanged over {stalled} runner cycles")
        print(f"INCOMPLETE after {max_cycles} cycles")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub run-plan",
        description="Relaunch a platform's headless CLI until the plan's completion verdict is terminal.",
        epilog="Platforms: " + ", ".join(sorted(TEMPLATES)),
    )
    parser.add_argument("plan", help="docs/**/plans/<plan>.md, or a minor scope such as v0.5")
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
