"""Require full history wherever CI invokes the attribution-bearing hygiene group."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
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


def test_required_workflows_support_post_rewrite_dispatch() -> None:
    for name in ("ci.yml", "doc-colocation.yml", "presentify-extractor.yml"):
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
        )
        events = workflow.get("on", workflow.get(True))
        assert "workflow_dispatch" in events, name


def test_presentify_dispatch_exercises_full_check_without_pr_metadata(
    tmp_path: Path,
) -> None:
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("Bash is required to exercise the workflow detector")
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/presentify-extractor.yml").read_text(
            encoding="utf-8"
        )
    )
    detector = next(
        s for s in workflow["jobs"]["detect"]["steps"] if s.get("id") == "paths"
    )
    output = tmp_path / "output"
    proc = subprocess.run(
        [bash, "-c", detector["run"]],
        cwd=tmp_path,
        env={
            **os.environ,
            "EVENT_NAME": "workflow_dispatch",
            "GITHUB_OUTPUT": str(output),
            "PR_BASE_SHA": "",
            "PR_HEAD_SHA": "",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text().strip() == "presentify=true"
    assert (
        "github.event_name == 'workflow_dispatch'" in workflow["jobs"]["verify"]["if"]
    )
