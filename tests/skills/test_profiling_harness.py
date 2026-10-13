"""
Tests for the code-optimizer skill's bundled profiling harness
(scripts/profile_run.py + scripts/profile_compare.py).

Run from the repo root:
    python -m pytest tests/skills/test_profiling_harness.py -v

Pure Python (cProfile is stdlib), so these run on every platform including the
Windows dev host. profile_run captures a profile of a generated fixture target;
profile_compare is tested against crafted profile JSON so its deltas are
deterministic (cProfile times themselves are not).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "developer-experience"
    / "code-optimizer"
    / "scripts"
)
_RUN = _SCRIPTS / "profile_run.py"
_COMPARE = _SCRIPTS / "profile_compare.py"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
    )


def _write_json(path: Path, obj: object) -> str:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return str(path)


def test_scripts_exist() -> None:
    assert _RUN.is_file(), f"missing {_RUN}"
    assert _COMPARE.is_file(), f"missing {_COMPARE}"


# v4.13.11 T024 (closes v4.13.9 WN-25): ask for far more entries than the target can produce,
# so the fixture's functions are present whatever their timing rank under host load.
_COMPLETE = 100_000
_STEP_CALLS = 500
_TARGET_SOURCE = (
    "def step(i):\n"
    "    return i * 2\n"
    "\n"
    "\n"
    "def work():\n"
    "    total = 0\n"
    f"    for i in range({_STEP_CALLS}):\n"
    "        total += step(i)\n"
    "    return total\n"
    "\n"
    "\n"
    "work()\n"
)


def _assert_profiled_fixture(functions: list[dict], target: Path, top: int) -> None:
    """The profile is complete and records the fixture's own functions with their real call counts."""
    assert len(functions) < top, f"{len(functions)} entries at --top {top}: the list may be truncated"
    for fn in functions:
        assert {"name", "ncalls", "tottime", "cumtime"} <= set(fn)
    by_name = {fn["name"]: fn for fn in functions}
    work = by_name.get(f"{target}:5(work)")
    step = by_name.get(f"{target}:1(step)")
    assert work is not None, f"work() is not in the profile: {sorted(by_name)[:20]}"
    assert step is not None, f"step() is not in the profile: {sorted(by_name)[:20]}"
    assert work["ncalls"] == 1
    assert step["ncalls"] == _STEP_CALLS
    # work() calls step(), so its cumulative time includes all of step's.
    assert work["cumtime"] >= step["cumtime"]


def test_profile_run_emits_profile(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text(_TARGET_SOURCE, encoding="utf-8")
    out = tmp_path / "profile.json"
    result = _run(_RUN, str(target), "--out", str(out), "--top", str(_COMPLETE))
    assert result.returncode == 0, result.stderr
    assert out.is_file()

    data = json.loads(out.read_text(encoding="utf-8"))
    _assert_profiled_fixture(data["functions"], target, _COMPLETE)


def test_the_profile_assertion_rejects_a_profile_without_the_fixture(tmp_path: Path) -> None:
    """Negative control: a profile missing work(), or one cut at --top, must not pass."""
    target = tmp_path / "target.py"
    step = {"name": f"{target}:1(step)", "ncalls": _STEP_CALLS, "tottime": 0.1, "cumtime": 0.1}
    other = {"name": "<string>:1(<module>)", "ncalls": 1, "tottime": 0.0, "cumtime": 0.2}
    with pytest.raises(AssertionError, match="work"):
        _assert_profiled_fixture([other, step], target, _COMPLETE)
    work = {"name": f"{target}:5(work)", "ncalls": 1, "tottime": 0.0, "cumtime": 0.1}
    with pytest.raises(AssertionError, match="truncated"):
        _assert_profiled_fixture([other, work, step], target, 3)


def test_profile_run_missing_target_exits_2(tmp_path: Path) -> None:
    result = _run(_RUN, str(tmp_path / "nope.py"), "--out", str(tmp_path / "o.json"))
    assert result.returncode == 2


def test_profile_run_survives_target_sys_exit(tmp_path: Path) -> None:
    target = tmp_path / "exiter.py"
    target.write_text("import sys\nprint('hi')\nsys.exit(0)\n", encoding="utf-8")
    out = tmp_path / "p.json"
    result = _run(_RUN, str(target), "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert out.is_file()


def test_profile_compare_reports_slower_and_faster(tmp_path: Path) -> None:
    before = _write_json(
        tmp_path / "before.json",
        {
            "functions": [
                {"name": "a.py:1(hot)", "ncalls": 1, "tottime": 1.0, "cumtime": 1.0},
                {"name": "a.py:2(cold)", "ncalls": 1, "tottime": 0.5, "cumtime": 0.5},
            ]
        },
    )
    after = _write_json(
        tmp_path / "after.json",
        {
            "functions": [
                {
                    "name": "a.py:1(hot)",
                    "ncalls": 1,
                    "tottime": 0.2,
                    "cumtime": 0.2,
                },  # faster
                {
                    "name": "a.py:2(cold)",
                    "ncalls": 1,
                    "tottime": 0.9,
                    "cumtime": 0.9,
                },  # slower
            ]
        },
    )
    result = _run(_COMPARE, before, after, "--top", "10")
    assert result.returncode == 0, result.stderr
    assert "faster" in result.stdout
    assert "slower" in result.stdout


def test_profile_compare_reports_new_and_gone(tmp_path: Path) -> None:
    before = _write_json(
        tmp_path / "before.json",
        {
            "functions": [
                {"name": "a.py:1(retired)", "ncalls": 1, "tottime": 1.0, "cumtime": 1.0}
            ]
        },
    )
    after = _write_json(
        tmp_path / "after.json",
        {
            "functions": [
                {"name": "a.py:9(added)", "ncalls": 1, "tottime": 1.0, "cumtime": 1.0}
            ]
        },
    )
    result = _run(_COMPARE, before, after)
    assert result.returncode == 0
    assert "GONE" in result.stdout
    assert "NEW" in result.stdout


def test_profile_compare_bad_input_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    good = _write_json(tmp_path / "good.json", {"functions": []})
    result = _run(_COMPARE, str(bad), good)
    assert result.returncode == 2
