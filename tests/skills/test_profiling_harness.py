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


def test_profile_run_emits_profile(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    target.write_text(
        "def work():\n"
        "    total = 0\n"
        "    for i in range(100000):\n"
        "        total += i\n"
        "    return total\n"
        "\n"
        "work()\n",
        encoding="utf-8",
    )
    out = tmp_path / "profile.json"
    result = _run(_RUN, str(target), "--out", str(out), "--top", "10")
    assert result.returncode == 0, result.stderr
    assert out.is_file()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["functions"], "expected at least one profiled function"
    assert any("work" in fn["name"] for fn in data["functions"])
    for fn in data["functions"]:
        assert {"name", "ncalls", "tottime", "cumtime"} <= set(fn)


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
