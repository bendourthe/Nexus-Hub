"""A scripted stand-in for a platform CLI in the end-to-end harness.

Each invocation performs the next phase of the fixture plan, one phase per
cycle, so the runner's resume path is exercised: cycle 1 records the upfront
approvals through the real checker and fixes the bug; cycle 2 adds the test and
resolves the known gap; cycle 3 writes the evidence, publishes through the gh
stand-in, merges, tags, releases, and cleans up. It makes no model call and
proves only that the fixture can reach PLAN COMPLETE, not that an agent will.

With E2E_SCENARIO=minor it drives `/implement v0.5` instead, following the
runbook's "Minor driver" one step per invocation: the first turn records the minor
approval through the exact paste; each runner cycle then runs one member (member
gate, `record member-start`, the phase work, the pull request, the merge, the tag
and release, and retiring the member's own branch); the last cycle is the minor
close (closing branch, gap migration, archive, one pull request, merge) and the
final `cleanup_merged.py --apply --receipt` pass. Every step's command and exit
code is appended to E2E_MINOR_LOG so the test can assert the order.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PLAN = os.environ.get("E2E_PLAN", "")
CHECKER = os.environ["E2E_CHECKER"]
STUB_SESSION = "e2e-stub-session"
REPO_SLUG = "acme/demo"
BRANCH = "feat/v0.2.0-demo"
SECTIONS = (
    "Architecture refactor",
    "Known-gaps reconciliation",
    "Living docs architecture",
    "Git-tree hygiene",
    "CI/CD coverage",
    "Tier 3 deep pass",
    "Goal-vs-codebase review",
    "Human/manual testing suggestions",
    "Publication and integration",
)


def git(*args: str) -> str:
    binary = shutil.which("git")
    if binary is None:
        raise SystemExit("git stand-in not on PATH")
    return subprocess.run(
        [binary, *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def gh(*args: str) -> None:
    # shutil.which searches PATH in order, so the harness's gh.exe stand-in wins on
    # Windows; a bare "gh" would let CreateProcess pick the real gh.exe.
    binary = shutil.which("gh")
    if binary is None:
        raise SystemExit("gh stand-in not on PATH")
    subprocess.run(
        [binary, *args, "--repo", REPO_SLUG], check=True, capture_output=True, text=True
    )


def tick(task: str) -> None:
    path = Path(PLAN)
    path.write_text(
        path.read_text(encoding="utf-8").replace(f"- [ ] {task} ", f"- [x] {task} "),
        encoding="utf-8",
    )


def write(rel: str, text: str) -> None:
    path = Path(rel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(message: str) -> None:
    git("add", "-A")
    git("commit", "-q", "-m", message)


def phase_1() -> None:
    approvals = Path("..") / "approvals.json"
    text = os.environ["E2E_APPROVAL"]
    approvals.write_text(
        json.dumps(
            {
                "repo": REPO_SLUG,
                "source_branch": BRANCH,
                "target_branch": "develop",
                "cleanup": {"branches": [BRANCH], "worktrees": []},
                "classes": [
                    {"class": "push-merge", "text": text},
                    {"class": "release", "bound": "v0.2.0", "text": text},
                ],
            }
        ),
        encoding="utf-8",
    )
    # The checker renders the page and generates the exact line; only the user's
    # whole-prompt paste of that line, captured by the real capture core as the
    # approval-capture hook would, lets `record create` record it (v4.13.2 WN-9).
    # The stub stands in for the user's typing, which is also the open WN-9
    # residual: a process piping into the capture core is not detectable.
    def submit(prompt: str) -> None:
        subprocess.run(
            [sys.executable, str(Path(CHECKER).with_name("completion_gate.py")), "capture"],
            input=json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": STUB_SESSION,
                              "prompt": prompt}),
            check=True,
            capture_output=True,
            text=True,
        )

    # The user's session already holds the /implement request before the page renders.
    submit(f"/implement {PLAN}")
    rendered = subprocess.run(
        [sys.executable, CHECKER, "record", "render", PLAN, "--session", "auto",
         "--approvals", str(approvals)],
        check=True,
        capture_output=True,
        text=True,
    )
    submit(rendered.stdout.splitlines()[0])
    subprocess.run(
        [
            sys.executable,
            CHECKER,
            "record",
            "create",
            PLAN,
            "--session",
            "auto",
            "--approvals",
            str(approvals),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    write("src/calc.py", "def add(a, b):\n    return a + b\n")
    tick("T001")
    commit("fix: add returns the sum")


def phase_2() -> None:
    write(
        "tests/test_calc.py",
        "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    )
    gaps = Path("docs/releases/v0/v0.2/known-gaps.md")
    gaps.write_text(
        gaps.read_text(encoding="utf-8").replace(
            "#### BG-1: add returns the difference",
            "#### BG-1: add returns the difference -- RESOLVED",
        ),
        encoding="utf-8",
    )
    tick("T002")
    commit("test: cover add")


def phase_3() -> None:
    body = "".join(f"## {name}\n\nDone.\n\n" for name in SECTIONS)
    body += "## Full-suite testing and stabilization\n\n`pytest -q`: 1 passed (tests/test_calc.py).\n"
    write(
        "docs/releases/v0/v0.2/development/v0.2.0-last-phase-evidence.md",
        "# Evidence\n\n" + body,
    )
    changelog = Path("CHANGELOG.md")
    changelog.write_text(
        changelog.read_text(encoding="utf-8") + "\n## [0.2.0] - 2026-09-25\n",
        encoding="utf-8",
    )
    tick("T003")
    commit("docs: last-phase evidence and v0.2.0 changelog")
    git("push", "-q", "origin", BRANCH)
    gh(
        "pr",
        "create",
        "--head",
        BRANCH,
        "--base",
        "develop",
        "--title",
        "v0.2.0",
        "--body",
        "Plan v0.2.0",
    )
    gh("pr", "merge", BRANCH, "--merge")
    git("checkout", "-q", "develop")
    git("merge", "-q", "--no-ff", BRANCH, "-m", "Merge v0.2.0")
    git("push", "-q", "origin", "develop")
    git("checkout", "-q", "main")
    git("merge", "-q", "--ff-only", "develop")
    git("tag", "v0.2.0")
    git("push", "-q", "origin", "main", "v0.2.0")
    gh("release", "create", "v0.2.0", "--title", "v0.2.0", "--notes", "Fix add.")
    git("branch", "-d", BRANCH)
    git("push", "-q", "origin", "--delete", BRANCH)


# --------------------------------------------------------------------------- minor scenario

MINOR = "v0.5"
MEMBERS = (("v0.5.2", "alpha"), ("v0.5.10", "omega"))
V05 = "docs/releases/v0/v0.5"
CLOSE_BRANCH = f"chore/close-{MINOR}"
MIGRATABLE = "v0.5#WN-3"
MINOR_APPROVALS = {
    "repo": REPO_SLUG,
    "target_branch": "develop",
    "classes": [
        {"class": "push-merge"},
        {"class": "release"},
        {"class": "cleanup-merged"},
        {"class": "gap-migration", "bound": [MIGRATABLE]},
        {"class": "archive-minor"},
        {"class": "minor-close-pr", "bound": 3},
    ],
}


def _log(step: str, proc: subprocess.CompletedProcess) -> None:
    with open(os.environ["E2E_MINOR_LOG"], "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"step": step, "rc": proc.returncode, "stdout": proc.stdout}) + "\n")


def _script(step: str, name: str, *args: str, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
    """Run an installed Nexus-Hub script (a sibling of the checker), log it, stop on failure."""
    proc = subprocess.run(
        [sys.executable, str(Path(CHECKER).with_name(name)), *args],
        capture_output=True, text=True, check=False, timeout=600,
    )
    _log(step, proc)
    if proc.returncode not in ok:
        raise SystemExit(f"{step} failed ({proc.returncode}): {proc.stdout}{proc.stderr}")
    return proc


def _capture(prompt: str) -> None:
    """The user's whole prompt reaching the approval-capture hook's core, as typed."""
    subprocess.run(
        [sys.executable, str(Path(CHECKER).with_name("completion_gate.py")), "capture"],
        input=json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": STUB_SESSION, "prompt": prompt}),
        check=True, capture_output=True, text=True,
    )


def minor_approve() -> None:
    """The upfront round: the page is rendered, and only the exact generated line records it."""
    spec = Path("..") / "minor-approvals.json"
    spec.write_text(json.dumps(MINOR_APPROVALS), encoding="utf-8")
    _capture(f"/implement {MINOR}")
    rendered = _script("render", "check_plan_completion.py", "record", "render", "--minor", MINOR,
                       "--session", STUB_SESSION, "--approvals", str(spec))
    _capture(rendered.stdout.splitlines()[0])
    _script("record-create", "check_plan_completion.py", "record", "create", "--minor", MINOR,
            "--session", STUB_SESSION, "--approvals", str(spec))


def _released(tag: str) -> bool:
    return bool(git("ls-remote", "--tags", "origin", f"refs/tags/{tag}"))


def _base() -> str:
    """Member gate steps 2-3: fetch, and confirm origin/develop already holds main."""
    git("fetch", "-q", "origin", "--tags")
    git("merge-base", "--is-ancestor", "origin/main", "origin/develop")
    return git("rev-parse", "origin/develop")


def _publish(branch: str, title: str) -> None:
    """Push once, open the pull request, merge it into develop, and record the host's merge."""
    git("push", "-q", "-u", "origin", branch)
    gh("pr", "create", "--head", branch, "--base", "develop", "--title", title, "--body", title)
    git("checkout", "-q", "develop")
    git("merge", "-q", "--no-ff", branch, "-m", f"Merge {branch}")
    git("push", "-q", "origin", "develop")
    gh("pr", "merge", branch, "--merge")


def minor_member(version: str, slug: str) -> None:
    base = _base()
    branch = f"feat/{version}-{slug}"
    git("checkout", "-q", "-b", branch, base)
    started = _script(f"member-start {version}", "check_plan_completion.py", "record", "member-start",
                      "--minor", MINOR, "--member", version, "--session", STUB_SESSION, "--head", base)
    if not started.stdout.startswith(f"STARTED {version}"):
        raise SystemExit(f"member gate refused {version}: {started.stdout}")
    plan = Path(f"{V05}/plans/{version}-{slug}.md")
    plan.write_text(plan.read_text(encoding="utf-8").replace("- [ ] T001 ", "- [x] T001 "), encoding="utf-8")
    write(f"src/{slug}.txt", f"{slug}\n")
    write(f"tests/test_{slug}.py", "def test_part():\n    assert True\n")
    body = "".join(f"## {name}\n\nDone.\n\n" for name in SECTIONS)
    body += f"## Full-suite testing and stabilization\n\n`pytest -q`: 2 passed, including tests/test_{slug}.py.\n"
    write(f"{V05}/development/{version}-last-phase-evidence.md", "# Evidence\n\n" + body)
    changelog = Path("CHANGELOG.md")
    changelog.write_text(
        changelog.read_text(encoding="utf-8") + f"\n## [{version.lstrip('v')}] - {dt.datetime.now(dt.timezone.utc).date().isoformat()}\n",
        encoding="utf-8",
    )
    commit(f"feat: {slug} ({version})")
    _publish(branch, version)
    git("checkout", "-q", "main")
    git("merge", "-q", "--ff-only", "develop")
    git("tag", version)
    git("push", "-q", "origin", "main", version)
    gh("release", "create", version, "--title", version, "--notes", f"{slug}.")
    git("checkout", "-q", "develop")
    # The run retires its own merged branch (run-owned cleanup); every other branch is
    # the cleanup executor's to decide.
    git("branch", "-d", branch)
    git("push", "-q", "origin", "--delete", branch)


def minor_close() -> None:
    """Runbook "Minor close" steps 2-11, after the last member's release and back-merge."""
    _base()
    git("checkout", "-q", "-b", CLOSE_BRANCH, "origin/develop")
    migrated = _script("migrate", "minor_close.py", "migrate", "--minor", MINOR, "--id", MIGRATABLE,
                       "--reason", "vendor-feature", "--evidence", "the vendor has not shipped the API",
                       "--session", STUB_SESSION, "--repo", ".")
    write(
        f"{V05}/development/{MINOR}-minor-close-evidence.md",
        f"# Minor close evidence - {MINOR}\n\n## Migrate\n\n`minor_close.py migrate --id {MIGRATABLE}`: "
        f"exit {migrated.returncode}\n\n## Local fast gate\n\nThe fixture has no fast profile; nothing to run.\n",
    )
    commit(f"docs(known-gaps): migrate {MIGRATABLE} to v0.6")
    _script("archive", "minor_close.py", "archive", "--minor", MINOR, "--apply", "--session", STUB_SESSION,
            "--link-checker", os.environ["E2E_LINK_CHECKER"], "--repo", ".")
    _publish(CLOSE_BRANCH, f"Close {MINOR}")
    git("fetch", "-q", "origin")
    git("merge-base", "--is-ancestor", "origin/main", "origin/develop")  # step 9: no back-merge needed
    _script("cleanup", "cleanup_merged.py", "--apply", "--receipt", "--minor", MINOR, "--session", STUB_SESSION,
            "--repo", ".", ok=(0, 1))
    _script("check-minor", "check_plan_completion.py", "check-minor", MINOR, ok=(0, 1, 3, 4))


def minor_main() -> int:
    if subprocess.run([sys.executable, CHECKER, "record", "path", "--minor", MINOR],
                      capture_output=True, text=True, check=False).returncode != 0:
        minor_approve()
        return 0
    for version, slug in MEMBERS:
        if not _released(version):
            minor_member(version, slug)
            return 0
    minor_close()
    return 0


def main() -> int:
    if os.environ.get("E2E_SCENARIO") == "minor":
        return minor_main()
    text = Path(PLAN).read_text(encoding="utf-8")
    if "- [ ] T001 " in text:
        phase_1()
    elif "- [ ] T002 " in text:
        phase_2()
    elif "- [ ] T003 " in text:
        phase_3()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
