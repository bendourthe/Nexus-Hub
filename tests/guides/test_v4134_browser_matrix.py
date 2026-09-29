"""Keep the retained visual matrix aligned with seven-section Training."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MATRIX = Path(__file__).resolve().parent / "tools" / "browser_matrix.py"
SPEC = importlib.util.spec_from_file_location("browser_matrix", MATRIX)
assert SPEC and SPEC.loader
matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(matrix)


def test_matrix_routes_and_geometry_use_current_sections():
    expected = ("game", "describe-review", "plan", "implement", "fixed-game", "compare", "presentify")
    assert matrix.ROUTES == expected
    groups = matrix.declare_groups()
    for name in ("fullscreen", "narrow", "short", "zoom"):
        assert groups[name]
        assert all(case["section"] in expected for case in groups[name])
        assert all(case["geometry"] for case in groups[name])
    assert "game" in matrix.geometry_regions("game")
    assert "terminal" not in matrix.geometry_regions("game")
    assert "terminal" in matrix.geometry_regions("presentify")


def test_matrix_no_longer_targets_removed_presentation_ui():
    text = MATRIX.read_text(encoding="utf-8")
    assert "#nhtPresent" not in text
    assert "is-present" not in text
    assert all(case["url"].endswith("#training/game") for case in matrix.declare_groups()["pointer"])
    assert "[data-arcade-id=\"buggy\"] [data-arcade-start]" in text
