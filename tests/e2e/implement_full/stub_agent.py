"""A scripted stand-in for a platform CLI in the end-to-end harness.

Each invocation performs the next phase of the fixture plan, one phase per
cycle, so the runner's resume path is exercised: cycle 1 records the upfront
approvals through the real checker and fixes the bug; cycle 2 adds the test and
resolves the known gap; cycle 3 writes the evidence, publishes through the gh
stand-in, merges, tags, releases, and cleans up. It makes no model call and
proves only that the fixture can reach PLAN COMPLETE, not that an agent will.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PLAN = os.environ["E2E_PLAN"]
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
    # shutil.which honors PATHEXT, so the harness's gh.cmd stand-in wins on
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


def main() -> int:
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
