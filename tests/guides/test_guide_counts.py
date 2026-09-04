"""v4.4.2 Phase 1: catalog-derived counts in the guide can never drift.

`scripts/stamp_guide_counts.py` rewrites `<span data-count="...">` markers from the catalog
and `--check` fails when any marker disagrees. These tests prove the tool against a fixture,
prove the real guide is clean, and prove that no count-bearing phrase in the page's visible
text escapes the marker discipline.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
SCRIPT = _ROOT / "scripts" / "stamp_guide_counts.py"


@pytest.fixture(scope="module")
def stamper():
    spec = importlib.util.spec_from_file_location("stamp_guide_counts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_counts_come_from_the_catalog(stamper) -> None:
    counts = stamper.compute_counts(_ROOT)
    assert set(counts) == {"skills", "hooks", "pretooluse", "commands"}
    assert all(isinstance(v, int) and v > 0 for v in counts.values())
    assert counts["pretooluse"] <= counts["hooks"], "PreToolUse hooks are a subset of all hooks"
    # The alias exclusion must be real: at least one command file declares itself an alias.
    assert counts["commands"] < len(list((_ROOT / "catalog" / "commands").glob("*.md")))


def test_stamp_rewrites_only_stale_markers(stamper) -> None:
    text = (
        '<p><span data-count="skills">1</span> skills and '
        '<span class="x" data-count="hooks">2</span> hooks and '
        '<span data-count="commands">7</span> commands.</p>'
    )
    new, changes = stamper.stamp(text, {"skills": 5, "hooks": 2, "pretooluse": 1, "commands": 7})
    assert '<span data-count="skills">5</span>' in new
    assert '<span class="x" data-count="hooks">2</span>' in new
    assert [c[0] for c in changes] == ["skills"], changes


def test_check_mode_fails_on_a_stale_marker(stamper, tmp_path: Path) -> None:
    counts = stamper.compute_counts(_ROOT)
    fixture = tmp_path / "guide.html"
    fixture.write_text(
        f'<span data-count="skills">{counts["skills"] + 1}</span> skills', encoding="utf-8"
    )
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--root", str(_ROOT), "--guide", str(fixture)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert 'STALE data-count="skills"' in proc.stdout


def test_missing_source_exits_two_and_writes_nothing(stamper, tmp_path: Path) -> None:
    fixture = tmp_path / "guide.html"
    fixture.write_text('<span data-count="skills">0</span>', encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--guide", str(fixture)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert fixture.read_text(encoding="utf-8") == '<span data-count="skills">0</span>'


def test_real_guide_markers_match_the_catalog() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--root", str(_ROOT)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_every_visible_count_phrase_uses_a_marker() -> None:
    """A bare '329 skills' in prose is the drift the stamper exists to prevent."""
    html = GUIDE.read_text(encoding="utf-8")
    # Drop code-like carriers where a number is data, not a claim.
    visible = re.sub(r"<(script|style|code|pre|kbd)\b.*?</\1>", " ", html, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+data-count=\"[a-z]+\"[^>]*>[^<]*</span>", " MARKED ", visible)
    visible = re.sub(r"<[^>]+>", " ", visible)
    bare = re.findall(r"\b\d{2,4}\+?\s+(?:skills|hooks|commands)\b", visible, flags=re.I)
    assert not bare, f"count-bearing phrases without a data-count marker: {bare}"
