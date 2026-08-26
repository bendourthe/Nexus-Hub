"""Behavior and cross-platform parity tests for link-baseline helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "catalog" / "skills" / "code-cleanup" / "docs-layout-refactor" / "scripts" / "link-baseline.py"
POWERSHELL = SCRIPT.with_suffix(".ps1")


def _powershell() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


@pytest.fixture(params=["python", "powershell"])
def command(request: pytest.FixtureRequest) -> list[str]:
    if request.param == "python":
        return [sys.executable, str(SCRIPT)]
    executable = _powershell()
    if executable is None:
        pytest.skip("PowerShell is not available")
    return [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(POWERSHELL)]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "target.md").write_text("# Target\n", encoding="utf-8")
    (tmp_path / "docs" / "source.md").write_text(
        "[valid](target.md) [remote](https://example.com) [mail](mailto:a@example.com) [anchor](#top)\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "docs"], check=True)
    return tmp_path


def _run(command: list[str], *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*command, *map(str, args)], text=True, capture_output=True, check=False)


def _baseline(command: list[str], repo: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return _run(command, "baseline", "--root", repo, "--out", output)


def test_baseline_is_sorted_ndjson_and_skips_nonrelative_links(command: list[str], repo: Path) -> None:
    source = repo / "docs" / "source.md"
    source.write_text(
        "[z](z-missing.md) [a](a-missing.md) [remote](https://example.com) [anchor](#top) `fake](\\\\d+)`\n"
        "```text\n[fenced](ignored-missing.md)\n```\n",
        encoding="utf-8",
    )
    output = repo / "baseline.ndjson"

    result = _baseline(command, repo, output)

    assert result.returncode == 0, result.stderr
    lines = output.read_text(encoding="utf-8-sig").splitlines()
    records = [json.loads(line) for line in lines]
    assert [record["link"] for record in records] == ["a-missing.md", "z-missing.md"]
    assert all(record["source"] == "docs/source.md" for record in records)


def test_diff_fails_for_new_breakage_and_passes_for_unchanged(command: list[str], repo: Path) -> None:
    before = repo / "before.ndjson"
    after = repo / "after.ndjson"
    assert _baseline(command, repo, before).returncode == 0
    (repo / "docs" / "source.md").write_text("[broken](missing.md)\n", encoding="utf-8")
    assert _baseline(command, repo, after).returncode == 0

    broken = _run(command, "diff", "--before", before, "--after", after)
    unchanged = _run(command, "diff", "--before", after, "--after", after)

    assert broken.returncode == 1, broken.stderr
    assert json.loads(broken.stdout)["totals"]["newly_broken"] == 1
    assert unchanged.returncode == 0, unchanged.stderr
    assert json.loads(unchanged.stdout)["totals"]["newly_broken"] == 0


def test_diff_detects_one_fixed_and_one_new_when_total_holds_level(command: list[str], repo: Path) -> None:
    source = repo / "docs" / "source.md"
    before = repo / "before.ndjson"
    after = repo / "after.ndjson"
    source.write_text("[old](old-missing.md)\n", encoding="utf-8")
    assert _baseline(command, repo, before).returncode == 0
    source.write_text("[new](new-missing.md)\n", encoding="utf-8")
    assert _baseline(command, repo, after).returncode == 0

    result = _run(command, "diff", "--before", before, "--after", after)

    report = json.loads(result.stdout)
    assert result.returncode == 1
    assert report["totals"] == {"before": 1, "after": 1, "newly_broken": 1, "fixed": 1, "unchanged": 0}


@pytest.mark.skipif(_powershell() is None, reason="PowerShell is not available")
def test_powershell_script_ast_parses() -> None:
    executable = _powershell()
    assert executable is not None
    probe = f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('{POWERSHELL}',[ref]$t,[ref]$e)|Out-Null;if($e.Count){{exit 1}}"
    result = subprocess.run([executable, "-NoProfile", "-Command", probe], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
