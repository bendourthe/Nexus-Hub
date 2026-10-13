"""The guide browser suite runs as three serial shards, never under pytest-xdist.

The maintainer requirement from v4.13.10: parallel workers on one runner starve each
other (Chromium renders WebGL in software there), so the suite is split across three
runners instead, each bounded at 45 minutes. This pins that shape so a later speed-up
cannot quietly reintroduce workers or a fourth leg.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import pytest

from scripts.ci.profiles import PROFILES

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
SHARDS = ("guide-browser-engine", "guide-browser-game", "guide-browser-rest")
LEG_MINUTES = 45
XDIST_TEXT = re.compile(r"xdist|numprocesses", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    try:
        return shlex.split(text, comments=True)
    except ValueError:  # an unbalanced quote in a YAML line; plain words still show a flag
        return text.split()


def _parallel_flags(argv: list[str]) -> list[str]:
    """The pytest arguments that would start xdist workers."""
    found = []
    for index, arg in enumerate(argv):
        if arg == "-n" or re.fullmatch(r"-n(?:\d+|auto|logical)", arg) or arg.startswith("--numprocesses"):
            found.append(arg)
        elif arg == "-p" and index + 1 < len(argv) and "xdist" in argv[index + 1]:
            found.append(f"-p {argv[index + 1]}")
        elif arg.startswith("-p") and "xdist" in arg:
            found.append(arg)
    return found


def test_guide_render_is_three_serial_shards_of_45_minutes() -> None:
    job = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))["jobs"]["guide-render"]
    legs = job["strategy"]["matrix"]["include"]
    assert len(legs) == 3, "the guide suite runs as exactly three shards"
    assert sorted(leg["group"] for leg in legs) == sorted(SHARDS)
    assert set(job["strategy"]["matrix"]) == {"include"}, "no extra matrix axis multiplies the legs"
    assert job["timeout-minutes"] == LEG_MINUTES, "each leg is bounded at 45 minutes"
    assert all("timeout-minutes" not in leg for leg in legs)
    groups = {group.name: group for group in PROFILES["full"]}
    for name in SHARDS:
        (command,) = groups[name].commands
        assert command.timeout == LEG_MINUTES * 60, name
        assert not command.platform_timeouts, name


def test_no_workflow_or_profile_step_runs_pytest_in_parallel() -> None:
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        assert not XDIST_TEXT.search(text), f"{path.name} mentions pytest-xdist"
        for line in text.splitlines():
            if "pytest" in line:
                assert not _parallel_flags(_tokens(line)), f"{path.name}: {line.strip()}"
    for profile, groups in PROFILES.items():
        for group in groups:
            for command in group.commands:
                where = f"{profile}/{group.name}/{command.name}"
                assert not _parallel_flags(list(command.argv)), where
                assert not any(XDIST_TEXT.search(a) for a in command.argv), where
                assert not any(XDIST_TEXT.search(v) or _parallel_flags(_tokens(v))
                               for v in command.env.values()), where


def test_no_dependency_file_pins_pytest_xdist() -> None:
    candidates = [
        *(ROOT / "scripts" / "ci").glob("requirements*"),
        *ROOT.glob("requirements*"),
        *ROOT.glob("constraints*"),
        *ROOT.glob("pyproject.toml"),
        *(ROOT / "extensions").glob("*/pyproject.toml"),
        *(ROOT / "extensions").glob("*/requirements*"),
    ]
    assert any(p.name == "requirements-py311.txt" for p in candidates), "the constraints file moved"
    for path in candidates:
        assert not re.search(r"pytest[-_.]xdist", path.read_text(encoding="utf-8"), re.IGNORECASE), path
