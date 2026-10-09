"""Keep browser-required guide contracts explicit and profile-owned."""

from pathlib import Path

import pytest

from scripts.ci.profiles import groups_for
from scripts.ci.run import select_groups

yaml = pytest.importorskip("yaml")

CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def test_browser_group_is_explicit_only() -> None:
    browser = next(group for group in groups_for("full") if group.name == "guide-browser")
    assert browser not in select_groups("full", None)
    assert select_groups("full", ["guide-browser"]) == (browser,)
    assert len(browser.commands) == 1
    command = browser.commands[0]
    assert set(command.argv) >= {
        "tests/guides/",
        "tests/verification/test_visual_defect_detector.py",
        "--junitxml=reports/junit/guide-render.xml",
    }
    assert command.env["NEXUS_REQUIRE_RENDER"] == "1"


SHARDS = ("guide-browser-engine", "guide-browser-game", "guide-browser-rest")


def test_guide_job_runs_one_browser_shard_per_leg() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    job = workflow["jobs"]["guide-render"]
    legs = job["strategy"]["matrix"]["include"]
    assert [leg["group"] for leg in legs] == list(SHARDS)
    assert job["strategy"]["fail-fast"] is False, "one slow shard must not cancel the others"
    run = next(step for step in job["steps"] if step.get("name") == "Run guide and visual detector browser contracts")
    assert run["run"] == (
        "python scripts/ci/run.py --profile full --only ${{ matrix.group }} --reports-dir reports"
    )
    assert "env" not in run


def _shard_files(argv: list[str]) -> set[str]:
    """The test files a shard's pytest arguments select, at file level."""
    root = CI.parents[2]
    ignore = {a.split("=", 1)[1] for a in argv if a.startswith("--ignore=")}
    globs = [a.split("=", 1)[1] for a in argv if a.startswith("--ignore-glob=")]
    files: set[str] = set()
    for arg in argv:
        if arg.startswith("-") or not arg.startswith("tests/"):
            continue
        path = root / arg
        found = sorted(path.glob("**/test_*.py")) if path.is_dir() else [path]
        files.update(p.relative_to(root).as_posix() for p in found)
    skipped = {f for f in files if f in ignore or any(Path(f).match(g) for g in globs)}
    return files - skipped


def test_the_browser_shards_partition_the_whole_suite() -> None:
    """Every guide test file runs in exactly one CI shard, so none is dropped or run twice."""
    groups = {group.name: group for group in groups_for("full")}
    whole = _shard_files(groups["guide-browser"].commands[0].argv)
    parts = [_shard_files(groups[name].commands[0].argv) for name in SHARDS]
    assert all(parts), "every shard selects at least one file"
    assert set().union(*parts) == whole, "the shards together cover the whole suite"
    assert sum(len(p) for p in parts) == len(whole), "no file runs in two shards"
    for name in SHARDS:
        command = groups[name].commands[0]
        assert command.env["NEXUS_REQUIRE_RENDER"] == "1", name
        assert f"--junitxml=reports/junit/{name}.xml" in command.argv, name
