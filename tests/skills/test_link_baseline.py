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


def _seed_move(repo, files, body):
    """Create docs/old/<files> with `body`, stage, then move them to docs/new/."""
    docs = repo / "docs"
    (docs / "old").mkdir()
    for name in files:
        (docs / "old" / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)


def _apply_move(repo, files):
    docs = repo / "docs"
    (docs / "new").mkdir()
    for name in files:
        (docs / "old" / name).rename(docs / "new" / name)
    (docs / "old").rmdir()
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)


def _rename_map(repo, files, prefix=""):
    path = repo / "renames.tsv"
    path.write_text(
        "".join(f"{prefix}docs/old/{n}\tdocs/new/{n}\n" for n in files), encoding="utf-8"
    )
    return path


def test_diff_without_a_rename_map_miscounts_a_moved_file(command: list[str], repo: Path) -> None:
    """A pure move must not read as breakage -- but without a map it does.

    This is the BG-3 symptom, asserted so the reason --rename-map exists stays
    visible: identity keys on `source`, so moving a file that already held a
    broken link re-keys it and it reports as newly broken.
    """
    files = ["page.md"]
    _seed_move(repo, files, "[dead](nowhere.md)\n")
    before = repo / "before.ndjson"
    assert _baseline(command, repo, before).returncode == 0
    _apply_move(repo, files)
    after = repo / "after.ndjson"
    assert _baseline(command, repo, after).returncode == 0

    result = _run(command, "diff", "--before", before, "--after", after)

    assert result.returncode == 1
    assert json.loads(result.stdout)["totals"]["newly_broken"] == 1


def test_diff_with_a_rename_map_reports_a_pure_move_as_clean(command: list[str], repo: Path) -> None:
    """The same move, with the map supplied, is correctly zero newly broken."""
    files = ["page.md", "other.md"]
    _seed_move(repo, files, "[dead](nowhere.md)\n")
    before = repo / "before.ndjson"
    assert _baseline(command, repo, before).returncode == 0
    _apply_move(repo, files)
    after = repo / "after.ndjson"
    assert _baseline(command, repo, after).returncode == 0

    result = _run(
        command, "diff", "--before", before, "--after", after,
        "--rename-map", _rename_map(repo, files),
    )

    assert result.returncode == 0, result.stderr
    totals = json.loads(result.stdout)["totals"]
    assert totals["newly_broken"] == 0
    assert totals["unchanged"] == 2


def test_rename_map_still_reports_a_genuine_break_across_a_move(
    command: list[str], repo: Path
) -> None:
    """The map must not launder real breakage introduced during the move."""
    files = ["page.md", "other.md"]
    _seed_move(repo, files, "[ok](../target.md)\n")
    before = repo / "before.ndjson"
    assert _baseline(command, repo, before).returncode == 0
    _apply_move(repo, files)
    # One link is left pointing somewhere that does not exist after the move.
    (repo / "docs" / "new" / "page.md").write_text("[broken](../../gone.md)\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    after = repo / "after.ndjson"
    assert _baseline(command, repo, after).returncode == 0

    result = _run(
        command, "diff", "--before", before, "--after", after,
        "--rename-map", _rename_map(repo, files),
    )

    assert result.returncode == 1, result.stdout
    assert json.loads(result.stdout)["totals"]["newly_broken"] == 1


def test_rename_map_accepts_git_name_status_rows(command: list[str], repo: Path) -> None:
    """`git diff --name-status -M` output is usable verbatim, no reformatting."""
    files = ["page.md", "other.md"]
    _seed_move(repo, files, "[dead](nowhere.md)\n")
    before = repo / "before.ndjson"
    assert _baseline(command, repo, before).returncode == 0
    _apply_move(repo, files)
    after = repo / "after.ndjson"
    assert _baseline(command, repo, after).returncode == 0

    result = _run(
        command, "diff", "--before", before, "--after", after,
        "--rename-map", _rename_map(repo, files, prefix="R100\t"),
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["totals"]["newly_broken"] == 0


@pytest.mark.skipif(_powershell() is None, reason="PowerShell is not available")
def test_powershell_script_ast_parses() -> None:
    executable = _powershell()
    assert executable is not None
    probe = f"$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile('{POWERSHELL}',[ref]$t,[ref]$e)|Out-Null;if($e.Count){{exit 1}}"
    result = subprocess.run([executable, "-NoProfile", "-Command", probe], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
