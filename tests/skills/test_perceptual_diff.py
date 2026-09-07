"""
Tests for the visual-regression-testing skill's bundled scripts/perceptual_diff.py.

Run from the repo root:
    python -m pytest tests/skills/test_perceptual_diff.py -v

Pure Python; fixtures are generated at runtime with Pillow (no committed binary
images). If Pillow is not installed the whole module skips, mirroring the
lazy-import degradation of the script itself.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "testing"
    / "visual-regression-testing"
    / "scripts"
    / "perceptual_diff.py"
)


def _solid(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> str:
    Image.new("RGB", size, color).save(path)
    return str(path)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_script_exists() -> None:
    assert _SCRIPT.is_file(), f"bundled script missing at {_SCRIPT}"


def test_identical_images_pass(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (40, 40), (10, 20, 30))
    b = _solid(tmp_path / "b.png", (40, 40), (10, 20, 30))
    result = _run(a, b)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_near_identical_within_threshold_pass(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (100, 100), (100, 100, 100))
    # Flip a handful of pixels: mean normalized diff stays well under 1%.
    img = Image.new("RGB", (100, 100), (100, 100, 100))
    for x in range(3):
        img.putpixel((x, 0), (255, 255, 255))
    b = str(tmp_path / "b.png")
    img.save(b)
    result = _run(a, b, "--threshold", "0.01")
    assert result.returncode == 0, result.stdout + result.stderr


def test_clearly_different_fails(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (40, 40), (0, 0, 0))
    b = _solid(tmp_path / "b.png", (40, 40), (255, 255, 255))
    result = _run(a, b, "--threshold", "0.01")
    assert result.returncode == 1
    assert "REGRESSED" in result.stdout


def test_size_mismatch_fails(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (40, 40), (10, 10, 10))
    b = _solid(tmp_path / "b.png", (50, 40), (10, 10, 10))
    result = _run(a, b)
    assert result.returncode == 1
    assert "SIZE MISMATCH" in result.stderr


def test_diff_image_is_written(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (40, 40), (0, 0, 0))
    b = _solid(tmp_path / "b.png", (40, 40), (255, 255, 255))
    diff = tmp_path / "diff.png"
    _run(a, b, "--diff", str(diff), "--threshold", "0.01")
    assert diff.is_file()


def test_bad_input_exits_2(tmp_path: Path) -> None:
    a = _solid(tmp_path / "a.png", (40, 40), (0, 0, 0))
    not_an_image = tmp_path / "nope.png"
    not_an_image.write_text("this is not an image", encoding="utf-8")
    result = _run(a, str(not_an_image))
    assert result.returncode == 2
