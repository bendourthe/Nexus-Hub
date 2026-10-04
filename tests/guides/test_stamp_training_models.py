"""v4.13.10 Phase 5: scripts/stamp_training_models.py keeps the Training page's model ids equal to the map.

Each test builds a throwaway repository root under tmp_path, so the real page is never written.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "stamp_training_models.py"
MAP_REL = Path("catalog/skills/ai-development/model-routing/references/last-known-model-map.json")
PAGE = '<body>\n<!-- models:nh-training-models -->\n<!-- /models:nh-training-models -->\n</body>\n'
MAP = {
    "schema_version": 1,
    "verified_as_of": "2026-10-01",
    "tiers": {
        "frontier": {"Anthropic": "model-a1", "OpenAI": "model-o1"},
        "fast": {"Anthropic": "model-a4", "OpenAI": "model-o4"},
    },
}
STORY = {"providers": ["Anthropic", "OpenAI"], "stages": [{"id": "loop1/review", "badge": {"tier": "frontier"}}]}


def _root(tmp_path: Path, model_map: dict | None = MAP, story: dict = STORY, page: str = PAGE) -> Path:
    (tmp_path / MAP_REL).parent.mkdir(parents=True)
    if model_map is not None:
        (tmp_path / MAP_REL).write_text(json.dumps(model_map), encoding="utf-8")
    (tmp_path / "guides" / "website" / "src").mkdir(parents=True)
    (tmp_path / "guides" / "website" / "src" / "training-story.json").write_text(json.dumps(story), encoding="utf-8")
    (tmp_path / "guides" / "website" / "training.html").write_text(page, encoding="utf-8", newline="\n")
    return tmp_path


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args], capture_output=True, text=True, check=False)


def _page(root: Path) -> str:
    return (root / "guides" / "website" / "training.html").read_text(encoding="utf-8")


def test_stamp_copies_the_map_and_check_then_passes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    assert _run(root).returncode == 0
    page = _page(root)
    assert '<script type="application/json" id="nh-training-models">' in page
    assert '"model-a1"' in page and '"verified_as_of": "2026-10-01"' in page
    assert _run(root, "--check").returncode == 0


def test_check_reports_a_changed_map_cell(tmp_path: Path) -> None:
    root = _root(tmp_path)
    assert _run(root).returncode == 0
    changed = json.loads(json.dumps(MAP))
    changed["tiers"]["frontier"]["OpenAI"] = "model-o1-new"
    other = tmp_path / "changed-map.json"
    other.write_text(json.dumps(changed), encoding="utf-8")
    result = _run(root, "--check", "--map", str(other))
    assert result.returncode == 1 and "drift" in result.stderr


def test_a_missing_map_is_an_error_and_writes_nothing(tmp_path: Path) -> None:
    root = _root(tmp_path, model_map=None)
    result = _run(root)
    assert result.returncode == 2 and "model map" in result.stderr
    assert _page(root) == PAGE


def test_a_badge_tier_missing_from_the_map_is_an_error(tmp_path: Path) -> None:
    story = {"providers": ["Anthropic"], "stages": [{"id": "loop1/plan", "badge": {"tier": "strong"}}]}
    result = _run(_root(tmp_path, story=story))
    assert result.returncode == 2 and "loop1/plan" in result.stderr and "'strong'" in result.stderr


@pytest.mark.parametrize("provider", ["openai", "Mistral"])
def test_a_provider_that_is_not_an_exact_map_column_is_an_error(tmp_path: Path, provider: str) -> None:
    story = {"providers": ["Anthropic", provider], "stages": []}
    result = _run(_root(tmp_path, story=story))
    assert result.returncode == 2 and provider in result.stderr


def test_a_page_without_one_marker_pair_is_an_error(tmp_path: Path) -> None:
    root = _root(tmp_path, page="<body></body>\n")
    result = _run(root)
    assert result.returncode == 2 and "found 0" in result.stderr


def test_the_real_page_matches_the_bundled_map() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
