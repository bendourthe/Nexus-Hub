"""Keep the retained visual matrix aligned with the two-page guide (v4.13.10)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MATRIX = Path(__file__).resolve().parent / "tools" / "browser_matrix.py"
STORY = Path(__file__).resolve().parents[2] / "guides" / "website" / "src" / "training-story.json"
SPEC = importlib.util.spec_from_file_location("browser_matrix", MATRIX)
assert SPEC and SPEC.loader
matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matrix)


def test_matrix_stages_exist_in_the_story():
    stage_ids = {s["id"] for s in json.loads(STORY.read_text(encoding="utf-8"))["stages"]}
    assert set(matrix.ROUTES) <= stage_ids
    for cases in matrix.declare_groups().values():
        for case in cases:
            if "stage" in case:
                assert case["stage"] in stage_ids, case["label"]
                assert case["url"].startswith(matrix.TRAINING.as_uri()), case["label"]


def test_matrix_geometry_uses_stage_owned_regions():
    groups = matrix.declare_groups()
    for name in ("fullscreen", "narrow", "short", "zoom"):
        assert groups[name] and all(case["geometry"] for case in groups[name])
    assert "game" in matrix.geometry_regions("play-buggy")
    assert "session" not in matrix.geometry_regions("play-buggy")
    assert {"session", "files", "activity"} <= set(matrix.geometry_regions("review"))
    assert set(matrix.geometry_regions("intro")) == {"banner"}


def test_matrix_no_longer_targets_the_retired_in_guide_training():
    text = MATRIX.read_text(encoding="utf-8")
    for retired in ("#training/", "NexusShooter", "NexusTraining ", "data-nht-section", "data-arcade-"):
        assert retired not in text, retired
    assert "training" not in matrix.PAGES
