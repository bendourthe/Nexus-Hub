"""Require full history wherever CI invokes the attribution-bearing hygiene group."""

import re
from pathlib import Path

import yaml

from scripts.ci.profiles import HYGIENE

ROOT = Path(__file__).resolve().parents[2]


def test_hygiene_and_make_validate_invoke_live_checker() -> None:
    commands = [
        c.argv
        for c in HYGIENE.commands
        if "scripts/check_commit_attribution.py" in c.argv
    ]
    assert len(commands) == 1
    assert commands[0][1:] == [
        "scripts/check_commit_attribution.py",
        "--all-refs",
        "--root",
        ".",
    ]
    assert (
        "\t@python scripts/check_commit_attribution.py --all-refs --root ."
        in (ROOT / "Makefile").read_text()
    )


def test_every_hygiene_profile_caller_fetches_full_history() -> None:
    found = set()
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, job in workflow.get("jobs", {}).items():
            for step in job.get("steps", []):
                run = step.get("run", "").replace("\\\n", " ")
                if not re.search(
                    r"scripts/ci/run\.py\s+--profile\s+(?:fast|full)\b", run
                ):
                    continue
                only = re.search(r"--only\s+(\S+)", run)
                if only and "hygiene" not in only.group(1).split(","):
                    continue
                checkouts = [
                    s
                    for s in job["steps"]
                    if s.get("uses", "").startswith("actions/checkout@")
                ]
                assert checkouts and all(
                    s.get("with", {}).get("fetch-depth") == 0 for s in checkouts
                ), (path.name, name)
                found.add((path.name, name))
    assert ("ci.yml", "validate") in found
    assert ("post-merge.yml", "smoke") in found


def test_validate_stays_unconditional_and_uses_hygiene_profile() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    )
    validate = workflow["jobs"]["validate"]
    assert "if" not in validate
    assert any(
        "hygiene" in s.get("run", "") and "scripts/ci/run.py" in s["run"]
        for s in validate["steps"]
    )
