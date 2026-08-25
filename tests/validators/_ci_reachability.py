"""Is a repository guard actually reachable from CI? (v4.0.0 Phase 8)

Several validator tests assert that their guard is wired into `make validate`
AND into `.github/workflows/ci.yml`. That assertion is exactly right and must
survive, because a guard that exists and never runs is worse than no guard: it
reads as coverage.

What changed in v4.0.0 is only WHERE the wiring lives. `ci.yml` used to name
each guard in its own `run:` step; it now calls
`python scripts/ci/run.py --profile full --only <groups>`, and the command list
lives in `scripts/ci/profiles.py`. A test that greps the YAML for a script name
therefore reports a wired guard as MISSING.

The tempting fix is the wrong one. Re-adding literal `run: python scripts/x.py`
lines to the workflow would make those greps pass and would reintroduce the
duplicated command list the engine exists to remove -- the same list that had
already diverged in production, silently dropping a security validator from CI
while the local list still ran it.

So this helper resolves the question through the indirection instead, reading
the live profile definitions rather than a copy of them. A guard added to a
group is visible here immediately, with no test edit.

Usage in a validator test:

    from tests.validators._ci_reachability import assert_wired_into_ci

    def test_makefile_and_ci_invoke_the_guard():
        assert "scripts/check_thing.py" in MAKEFILE.read_text(encoding="utf-8")
        assert_wired_into_ci("check_thing.py")
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"


def _groups_selected_by_workflows() -> set[str]:
    """Every profile group named by an `--only` flag in any workflow."""
    groups: set[str] = set()
    for path in WORKFLOW_DIR.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        if "scripts/ci/run.py" not in text:
            continue
        if "--only" not in text:
            # A call with no --only runs the WHOLE profile, so every group in it
            # is selected. Recorded as the sentinel below.
            groups.add("*")
            continue
        for match in re.finditer(r"--only\s+([\w,-]+)", text):
            groups.update(g for g in match.group(1).split(",") if g)
    return groups


def scripts_reachable_from_ci() -> set[str]:
    """Basenames of every `scripts/*.py` a CI job would execute.

    Covers both routes: a literal invocation in the workflow YAML, and a command
    inside a profile group that a workflow selects.
    """
    from scripts.ci.profiles import PROFILES  # noqa: PLC0415 - deliberate late import

    reachable: set[str] = set()

    # Route 1: named directly in any workflow.
    for path in WORKFLOW_DIR.glob("*.yml"):
        for match in re.finditer(r"scripts/([\w-]+\.py)", path.read_text(encoding="utf-8")):
            reachable.add(match.group(1))

    # Route 2: inside a profile group a workflow selects.
    selected = _groups_selected_by_workflows()
    for groups in PROFILES.values():
        for group in groups:
            if "*" not in selected and group.name not in selected:
                continue
            for cmd in group.commands:
                for token in cmd.argv:
                    match = re.fullmatch(r"scripts/([\w-]+\.py)", str(token))
                    if match:
                        reachable.add(match.group(1))
    return reachable


def is_wired_into_ci(script_basename: str) -> bool:
    """True when a CI job would run `scripts/<script_basename>`."""
    return script_basename in scripts_reachable_from_ci()


def assert_wired_into_ci(script_basename: str) -> None:
    """Fail with a message that names the correct remedy.

    The remedy matters as much as the assertion here: the obvious way to make a
    failure go away is the one that reintroduces the defect.
    """
    assert is_wired_into_ci(script_basename), (
        f"scripts/{script_basename} is not reachable from any CI job, so it "
        "guards nothing in CI. Add it to the right Group in "
        "scripts/ci/profiles.py -- do NOT add a literal `run: python "
        f"scripts/{script_basename}` step to a workflow, which would recreate "
        "the duplicated command list the engine exists to remove."
    )
