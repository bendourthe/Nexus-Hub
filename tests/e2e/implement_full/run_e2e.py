"""End-to-end evaluation harness for the v4.13.2 full-by-default /implement run.

One run = one fixture repository (two phases, one known gap, a minimal final
phase, a local bare remote) driven by `run_plan.py` on one platform until the
completion checker's verdict is terminal. Measures: runner cycles, the final
verdict, unplanned stops, and spend where the platform reports it.

    python tests/e2e/implement_full/run_e2e.py --agent stub --out <dir>
    python tests/e2e/implement_full/run_e2e.py --agent claude --out <dir>   # paid

`--agent stub` replaces the platform CLI with `stub_agent.py`, which performs the
plan's steps deterministically (one phase per cycle), so the fixture, the gh
stand-in, the checker, and the runner are proven completable with no model call.
The real agents (claude, codex, opencode) need their own credentials in the
environment; the harness never copies a user's credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "gh_stub"))
from launcher import make_stub
PLAN_REL = "docs/releases/v0/v0.2/plans/v0.2.0-demo.md"
# The approval names the remote the push really goes to: origin is a local bare mirror, and
# an approval naming only acme/demo leaves a careful agent unable to push anywhere it names.
APPROVAL = (
    "Approve the full run of v0.2.0 for acme/demo, whose git remote origin is its local mirror: "
    "push to origin, merge, release v0.2.0, and clean up."
)
STUB_APPROVAL = (
    "Approve the full run of v0.2.0 for acme/demo at https://github.com/acme/demo.git: "
    "push to origin, merge, release v0.2.0, and clean up."
)

PLAN = """# Plan -- Demo calculator

**Version**: v0.2.0
**Slug**: demo
**Status**: queued

**Goal**: `add` returns the sum, is tested, and v0.2.0 is released.

## Phase 1: Fix add

- [ ] T001 Make add return a + b src/calc.py

## Phase 2: Test add

- [ ] T002 Add a unit test for add tests/test_calc.py

## Phase 3: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

- [ ] T003 Write the last-phase evidence and publish docs/releases/v0/v0.2/development/v0.2.0-last-phase-evidence.md
"""

GAPS = """# Known gaps - v0.2

## v0.2.0

### Open Items

#### BG-1: add returns the difference

**Source phase**: pre-existing. **Reason**: `add` subtracts. **Suggested next step**: fix in Phase 1.
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def build_fixture(root: Path, *, stub: bool = False) -> Path:
    remote = root / "remote.git"
    work = root / "work"
    _git(root, "init", "--bare", "-q", "-b", "main", str(remote))
    work.mkdir()
    _git(work, "init", "-q", "-b", "main")
    _git(work, "config", "user.email", "e2e@example.invalid")
    _git(work, "config", "user.name", "E2E")
    _git(work, "remote", "add", "origin", str(remote))
    files = {
        PLAN_REL: PLAN,
        "docs/releases/v0/v0.2/known-gaps.md": GAPS,
        "src/calc.py": "def add(a, b):\n    return a - b\n",
        "CHANGELOG.md": "# Changelog\n\n## [Unreleased]\n",
        "README.md": "# Demo calculator\n",
    }
    for rel, text in files.items():
        path = work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "start")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "branch", "develop")
    _git(work, "push", "-q", "origin", "develop")
    _git(work, "checkout", "-q", "-b", "feat/v0.2.0-demo")
    if stub:
        # The stub advertises the approved URL; its Git transport is redirected
        # only for pushes and remote reads, so the checker still sees that origin.
        _git(work, "remote", "set-url", "origin", "https://github.com/acme/demo.git")
    return work


def _stub_bin(bin_dir: Path, name: str, target: Path, python: str) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    # Run a copy inside the run root: an agent's sandbox (Codex on Linux) sees only the
    # paths the run grants, and the harness source tree is not one of them.
    copy = bin_dir / f"_{target.name}"
    shutil.copyfile(target, copy)
    # A real executable (an .exe on Windows, plus an extensionless sh script for Git
    # Bash): the checker's resolver never runs a .cmd or .bat, whose arguments cmd.exe
    # would re-parse.
    make_stub(bin_dir, name, copy, python)


def install_into(home: Path, platform: str, env: dict) -> int:
    """Install Nexus-Hub for one platform into a throwaway home (never the real one).

    E2E_INSTALL_FROM names another Nexus-Hub tree to install (a baseline checkout);
    the completion checker that scores the run is always this tree's.
    """
    source = Path(os.environ.get("E2E_INSTALL_FROM") or REPO)
    (
        home
        / {"claude": ".claude", "codex": ".codex", "opencode": ".config/opencode"}[
            platform
        ]
    ).mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        argv = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(source / "scripts" / "installer.ps1"),
            "-Yes",
            "-Platforms",
            platform,
        ]
    else:
        argv = [
            "bash",
            str(source / "scripts" / "installer.sh"),
            "--yes",
            "--platforms",
            platform,
        ]
    # Run from outside any repository: an install run inside a checkout writes
    # project surfaces into it.
    # The installer finds VS Code and Cursor through LOCALAPPDATA and would install the
    # usage-monitor extensions into the user's real editors, so it gets the throwaway one.
    install_env = {**env, "LOCALAPPDATA": str(home / "AppData" / "Local")}
    proc = subprocess.run(
        argv,
        cwd=home.parent,
        env=install_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
        check=False,
    )
    # Kept per run: an installer step that skips a platform still exits 0, so the log
    # is the only record of what the run's agent was actually given.
    (home.parent / "install.log").write_text(
        f"exit {proc.returncode}\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8"
    )
    if proc.returncode != 0:
        return proc.returncode
    # Pre-flight before any paid call: the platform must have THIS tree's implement-phase
    # skill. Without it a CLI can fall back to the user's real, older install (Codex
    # resolves ~/.agents from the Windows profile, not HOME) and the run measures that.
    skill_root = {"claude": ".claude/skills", "codex": ".agents/skills",
                  "opencode": ".config/opencode/skills"}[platform]
    skill = home / skill_root / "implement-phase" / "SKILL.md"
    expected = source / "catalog" / "skills" / "workflow" / "implement-phase" / "SKILL.md"
    if not skill.is_file() or skill.read_bytes() != expected.read_bytes():
        (home.parent / "install.log").open("a", encoding="utf-8").write(
            f"\npre-flight: {skill} is missing or differs from {expected}\n"
        )
        return 90
    return 0


CRED_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_PROFILE",
             "ANTHROPIC_BASE_URL", "OPENAI_API_KEY", "CODEX_API_KEY", "NEXUS_PILOT_ANTHROPIC_API_KEY",
             "NEXUS_PILOT_OPENAI_API_KEY")


UNATTENDED_ALLOW = ["Edit", "Write", "MultiEdit", "Bash(git *)", "Bash(gh *)", "Bash(python *)",
                    "Bash(python3 *)", "Bash(pytest *)", "Bash(nexus-hub *)"]


def unattended_profile(home: Path, agent: str, remote: Path) -> str:
    """The permission setup a user chooses for an unattended run, WITHOUT a bypass mode.

    `run_plan.py` passes no bypass flag and refuses a platform whose own config bypasses
    approvals (`bypassPermissions`, `approval_policy = "never"`, `danger-full-access`), so an
    unattended run can only edit files and run git where the platform's settings allow it.
    A default install allows read-only commands only; this grants edits and the fixture's
    commands inside the throwaway home and records exactly what was granted.
    """
    if agent == "claude":
        settings = home / ".claude" / "settings.json"
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.is_file() else {}
        permissions = data.setdefault("permissions", {})
        permissions["defaultMode"] = "acceptEdits"
        allow = permissions.setdefault("allow", [])
        allow.extend(rule for rule in UNATTENDED_ALLOW if rule not in allow)
        settings.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return "claude: permissions.defaultMode=acceptEdits; allow += " + ", ".join(UNATTENDED_ALLOW)
    if agent == "codex":
        # The installed config selects a `default_permissions` profile, which overrides
        # `sandbox_mode` entirely, so writes are granted in that profile's filesystem table:
        # the fixture's work tree and its remote, by absolute path (documented key form).
        config = home / ".codex" / "config.toml"
        text = config.read_text(encoding="utf-8")
        header = "[permissions.default.filesystem]\n"
        assert text.count(header) == 1, "installed Codex config lacks its default permissions profile"
        # The run root covers `work` and any worktree created beside it; Codex keeps `.git`
        # read-only inside a writable root unless it is granted explicitly (measured: no
        # commit without the `work/.git` entry).
        # `work` is also named explicitly: it is the workspace, and the shipped profile's
        # `":workspace_roots" = "read"` is more specific than the run-root grant, so without
        # its own entry the original checkout stayed read-only (measured: `git switch` there
        # failed to unlink tracked files while the sibling worktree was writable).
        run_root = remote.parent.resolve()
        grants = [(run_root.as_posix(), "write"), ((run_root / "work").as_posix(), "write"),
                  ((run_root / "work" / ".git").as_posix(), "write"), (remote.resolve().as_posix(), "write")]
        # A user-local npm prefix (no sudo) sits outside `:minimal`, and Codex's Linux
        # sandbox re-executes its own vendored binary from there, so the prefix is readable.
        real = os.environ.get("E2E_REAL_BIN") or shutil.which("codex")
        if real and os.name != "nt":
            grants.append((Path(real).resolve().parents[1].as_posix(), "read"))
        lines = "".join(f'"{path}" = "{mode}"\n' for path, mode in grants)
        config.write_text(text.replace(header, header + lines), encoding="utf-8")
        return "codex: permissions.default.filesystem += " + ", ".join(f'"{p}" = "{m}"' for p, m in grants)
    if agent == "opencode":
        config = home / ".config" / "opencode" / "opencode.json"
        data = json.loads(config.read_text(encoding="utf-8")) if config.is_file() else {}
        data["permission"] = {**data.get("permission", {}), "edit": "allow", "bash": "allow"}
        config.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return 'opencode: permission.edit="allow", permission.bash="allow"'
    return "none"


def isolated(env: dict, home: Path, agent: str) -> dict:
    """Point every home-like location into the throwaway home and map only the pilot key.

    The user's own credentials never reach the child: every credential variable is dropped,
    then the dedicated pilot key is given to the child under the name its CLI reads.
    """
    source = dict(env)
    env = {k: v for k, v in env.items() if k not in CRED_VARS and not k.startswith("CLAUDE_CODE_")}
    for sub in (".claude", ".codex", ".config", "AppData/Roaming", "AppData/Local"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    gitconfig = home / ".gitconfig"
    if not gitconfig.exists():
        gitconfig.write_text("[user]\n\tname = E2E User\n\temail = e2e@example.invalid\n", encoding="utf-8")
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(home / "AppData" / "Roaming"),
        # LOCALAPPDATA stays real: a Microsoft Store Python derives sys.executable from it, so
        # redirecting it breaks every child that re-launches Python (git hooks, the checker).
        GIT_CONFIG_GLOBAL=str(gitconfig),
        GIT_CONFIG_NOSYSTEM="1",
        CLAUDE_CONFIG_DIR=str(home / ".claude"),
        CODEX_HOME=str(home / ".codex"),
        XDG_CONFIG_HOME=str(home / ".config"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    # A Microsoft Store Python derives sys.executable from USERPROFILE, so with USERPROFILE redirected
    # every relaunch of Python (the checker, git hooks) would fail. Run the harness from a venv and put
    # its Scripts folder first: a venv interpreter is an ordinary file that records its base by path.
    if sys.prefix != sys.base_prefix:
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    # The installer probes editor CLIs to retire old extensions; keep it off the real editors.
    env["PATH"] = os.pathsep.join(p for p in env.get("PATH", "").split(os.pathsep)
                                  if p and not any((Path(p) / n).exists() for n in ("code.cmd", "cursor.cmd")))
    # The installer puts the `nexus-hub` CLI in ~/.nexus-hub/bin and adds it to the user's
    # shell profile PATH; the harness never sources a profile, so it does that step here.
    env["PATH"] = str(home / ".nexus-hub" / "bin") + os.pathsep + env["PATH"]
    if agent == "claude":
        env["ANTHROPIC_API_KEY"] = source.get("NEXUS_PILOT_ANTHROPIC_API_KEY", "")
    elif agent == "codex":
        env["CODEX_API_KEY"] = source.get("NEXUS_PILOT_OPENAI_API_KEY", "")
        # Codex skips every hook the user has not trusted through `/hooks` (hash-pinned),
        # and a fresh install has trusted none, so approval capture and the completion gate
        # never ran. This flag stands in for that one-time interactive trust; it relaxes
        # neither approvals nor the sandbox (https://learn.chatgpt.com/docs/hooks).
        env["E2E_CODEX_TRUST_HOOKS"] = "1"
    elif agent == "opencode":
        env["ANTHROPIC_API_KEY"] = source.get("NEXUS_PILOT_ANTHROPIC_API_KEY", "")
    return env


def run_condition(
    agent: str, out: Path, max_cycles: int, runner: bool = True, hooks: bool = True
) -> dict:
    root = out / f"{agent}-{time.strftime('%Y%m%d-%H%M%S')}"
    root.mkdir(parents=True)
    work = build_fixture(root, stub=agent == "stub")
    approval = STUB_APPROVAL if agent == "stub" else APPROVAL
    home = root / "home"
    bin_dir = root / "bin"
    runs = home / ".nexus-hub" / "runs"
    runs.mkdir(parents=True)
    _stub_bin(bin_dir, "gh", HERE / "gh_e2e.py", sys.executable)
    platform = {
        "stub": "claude",
        "claude": "claude",
        "codex": "codex",
        "opencode": "opencode",
    }[agent]
    real_git = shutil.which("git")
    assert real_git is not None, "git is required by the fixture"
    if agent == "stub":
        _stub_bin(bin_dir, "git", HERE / "git_e2e.py", sys.executable)
        _stub_bin(bin_dir, "claude", HERE / "stub_agent.py", sys.executable)
    env = dict(os.environ)
    env.update(
        PATH=str(bin_dir) + os.pathsep + env.get("PATH", ""),
        GH_E2E_STATE=str(root / "gh-state.json"),
        GH_E2E_LOG=str(root / "gh.log"),
        NEXUS_HUB_RUNS_DIR=str(runs),
        E2E_APPROVAL=approval,
        E2E_PLAN=PLAN_REL,
        E2E_CHECKER=str(REPO / "scripts" / "check_plan_completion.py"),
        NEXUS_RUNNER_BACKOFF="0",
        GH_PROMPT_DISABLED="1",
    )
    spend_log = root / "spend.jsonl"
    profile = "stub"
    if agent != "stub":
        env = isolated(env, home, agent)
        # Git Bash exports PWD, and OpenCode trusts PWD over the process working
        # directory: with the harness's PWD inherited it resolved its project to the
        # directory the harness ran from, not the fixture. Every child runs in `work`.
        env["PWD"] = str(work)
        env["E2E_SPEND_LOG"] = str(spend_log)
        env["E2E_RUN_LABEL"] = root.name
        if install_into(home, platform, env) != 0:
            return {
                "agent": agent,
                "root": str(root),
                "complete": False,
                "verdict": "install failed",
            }
        profile = unattended_profile(home, platform, root / "remote.git")
        if not hooks:
            env["NEXUS_DISABLED_HOOKS"] = "completion-gate,approval-capture"
        # Every paid CLI runs behind the spend shim, so each call is metered into the ledger.
        cli = platform
        env["E2E_SHIM_AGENT"] = cli
        env["E2E_REAL_BIN"] = shutil.which(cli) or cli
        _stub_bin(bin_dir, cli, HERE / "spend_shim.py", sys.executable)
    if agent == "stub":
        env["E2E_REAL_GIT"] = real_git
        env["E2E_STUB_REMOTE_MIRROR"] = str(root / "remote.git")
        # The stub renders the approval page itself and stands in for the user
        # pasting the generated line (stub_agent.phase_1); a digest planted here
        # in advance could never match, because the line carries a fresh code.
    started = time.monotonic()
    # The scripted first turn: /implement with the upfront approvals answered in
    # the same prompt, never mid-run. It creates the run record; the runner then
    # resumes that session until the verdict is terminal.
    sys.path.insert(0, str(REPO / "scripts"))
    import run_plan

    launch = run_plan.TEMPLATES[platform][0]
    first = launch(f"/implement {PLAN_REL} -- upfront approvals, verbatim: {approval}")
    first[0] = shutil.which(first[0], path=env["PATH"]) or first[0]
    first_proc = subprocess.run(
        first,
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=3600,
        check=False,
    )
    (root / "first-turn.out").write_text(first_proc.stdout + "\n--- stderr ---\n" + first_proc.stderr,
                                         encoding="utf-8")
    proc = (
        subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "run_plan.py"),
                PLAN_REL,
                "--platform",
                platform,
                "--max-cycles",
                str(max_cycles if runner else 0),
            ],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
        if runner
        else subprocess.CompletedProcess([], 0, "", "")
    )
    (root / "runner.out").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    check = subprocess.run(
        [sys.executable, env["E2E_CHECKER"], "check", PLAN_REL],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    cycles = sum(1 for line in proc.stderr.splitlines() if line.startswith("cycle "))
    verdict = check.stdout.splitlines()[0] if check.stdout else ""
    return {
        "agent": agent,
        "platform": platform,
        "root": str(root),
        "runner_exit": proc.returncode,
        "runner_stdout": proc.stdout.strip()[-400:],
        "incomplete_cycles": cycles,
        "verdict": verdict,
        "complete": verdict.startswith("PLAN COMPLETE"),
        "seconds": round(time.monotonic() - started, 1),
        "runner": runner,
        "hooks": hooks,
        "spend_usd": _spend(spend_log),
        "permission_profile": profile if agent != "stub" else "stub",
        "runner_stderr_tail": proc.stderr.strip()[-600:],
    }


def _spend(path: Path) -> float:
    if not path.exists():
        return 0.0
    return round(
        sum(
            json.loads(line).get("cost_usd", 0.0)
            for line in path.read_text(encoding="utf-8").splitlines()
        ),
        4,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--agent", choices=["stub", "claude", "codex", "opencode"], required=True
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-cycles", type=int, default=6)
    parser.add_argument(
        "--no-runner",
        action="store_true",
        help="instruction-only condition: first turn only",
    )
    parser.add_argument(
        "--no-hooks",
        action="store_true",
        help="disable the completion gate and capture hooks",
    )
    parser.add_argument("--ledger", default="C:/tmp/v4132e2e/ledger.jsonl",
                        help="plan-wide spend ledger shared by every paid run")
    parser.add_argument("--cap", type=float, default=50.0, help="USD cap for the ledger (first pass)")
    parser.add_argument("--install-from", help="install Nexus-Hub from this tree (a baseline checkout)")
    args = parser.parse_args()
    Path(args.ledger).parent.mkdir(parents=True, exist_ok=True)
    pilot = {"claude": "NEXUS_PILOT_ANTHROPIC_API_KEY", "opencode": "NEXUS_PILOT_ANTHROPIC_API_KEY",
             "codex": "NEXUS_PILOT_OPENAI_API_KEY"}.get(args.agent)
    if pilot and not os.environ.get(pilot):
        print(f"{pilot} is not set; the paid run is blocked (the user's own credentials are never used)",
              file=sys.stderr)
        return 2
    os.environ["E2E_LEDGER"] = str(Path(args.ledger).resolve())
    os.environ["E2E_LEDGER_CAP"] = str(args.cap)
    if args.install_from:
        os.environ["E2E_INSTALL_FROM"] = str(Path(args.install_from).resolve())
    if args.agent != "stub" and shutil.which(args.agent) is None:
        print(f"{args.agent} CLI is not installed", file=sys.stderr)
        return 2
    result = run_condition(
        args.agent,
        Path(args.out).resolve(),
        args.max_cycles,
        runner=not args.no_runner,
        hooks=not args.no_hooks,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
