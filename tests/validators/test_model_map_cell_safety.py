"""WN-29: model-map.py refuses a cell or source that would corrupt the rendered Markdown.

`render` writes each model cell into a table row that plans embed verbatim, so a pipe starts a
new column, a backtick ends the code span, and a line break starts a new row. `validate` is the
gate in front of `render`; these tests prove it refuses each hazard with a clear message and a
non-zero exit, and that `render` never reaches the table for such a map.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HELPER = (
    REPO / "catalog" / "skills" / "ai-development" / "model-routing" / "scripts" / "model-map.py"
)
SNAPSHOT = HELPER.parent.parent / "references" / "last-known-model-map.json"
VALID = REPO / "tests" / "fixtures" / "model-routing" / "valid-map.json"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _map_with(tmp_path: Path, mutate) -> Path:
    data = json.loads(VALID.read_text(encoding="utf-8"))
    mutate(data)
    path = tmp_path / "map.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


HOSTILE_CELLS = [
    pytest.param("gemini-4-argon|x", id="pipe"),
    pytest.param("gemini-4-argon\nx", id="newline"),
    pytest.param("gemini-4-argon\r\nx", id="crlf"),
    pytest.param("gemini-4-argon\n", id="trailing-newline"),
    pytest.param("gemini-4-argon\x00", id="nul"),
    pytest.param("gemini-4-argon\x1b[31m", id="escape-sequence"),
    pytest.param("gemini-4-argon x", id="line-separator"),
    pytest.param("gemini‮4-argon", id="bidi-override"),
    pytest.param("gemini-4-argon`x", id="backtick"),
    pytest.param("m" * 101, id="over-length"),
]


@pytest.mark.parametrize("cell", HOSTILE_CELLS)
def test_validate_rejects_a_hostile_cell(tmp_path: Path, cell: str) -> None:
    path = _map_with(tmp_path, lambda d: d["tiers"]["frontier"].update({"Google": cell}))

    result = _run("validate", str(path))

    assert result.returncode == 1, result.stdout
    assert "frontier/Google" in result.stderr
    assert "Error:" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("cell", HOSTILE_CELLS)
def test_render_never_emits_a_hostile_cell(tmp_path: Path, cell: str) -> None:
    path = _map_with(tmp_path, lambda d: d["tiers"]["strong"].update({"OpenAI": cell}))

    result = _run("render", str(path), "--status", "offline")

    assert result.returncode == 1
    assert result.stdout == "", "no Markdown may be produced for an unsafe map"
    assert "strong/OpenAI" in result.stderr


@pytest.mark.parametrize("url", ["https://example.com/a b", "https://example.com/a\nb", "https://example.com/\x00"])
def test_validate_rejects_a_source_url_that_would_split_the_list_line(
    tmp_path: Path, url: str
) -> None:
    path = _map_with(tmp_path, lambda d: d["sources"]["Anthropic"].append(url))

    result = _run("validate", str(path))

    assert result.returncode == 1
    assert "sources for Anthropic" in result.stderr


def test_a_normal_map_still_validates_and_renders_one_row_per_tier(tmp_path: Path) -> None:
    assert _run("validate", str(VALID)).returncode == 0

    rendered = _run("render", str(VALID), "--status", "offline").stdout

    rows = [line for line in rendered.splitlines() if line.startswith("| ") and "`" in line]
    assert len(rows) == 4
    assert all(line.count("|") == 6 for line in rows)


def test_the_bundled_snapshot_passes_the_stricter_rules() -> None:
    result = _run("validate", str(SNAPSHOT))

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["valid"] is True
