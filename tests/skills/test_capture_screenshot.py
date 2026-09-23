"""Contract tests for the visual-regression screenshot capture helper."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "testing"
    / "visual-regression-testing"
    / "scripts"
    / "capture_screenshot.py"
)


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("capture_screenshot", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_browser_selection_uses_first_available_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    capture = _load_script()
    names: list[str] = []

    def find(name: str) -> str | None:
        names.append(name)
        return "C:/Browser/chromium.exe" if name == "chromium" else None

    monkeypatch.setattr(capture.shutil, "which", find)

    assert capture._find_browser() == "C:/Browser/chromium.exe"
    assert names == ["chrome", "google-chrome", "chromium"]


@pytest.mark.parametrize("target", ["https://example.test/view", "http://example.test", "file:///tmp/a.html"])
def test_url_target_is_preserved(target: str) -> None:
    assert _load_script()._to_target(target) == target


def test_local_target_becomes_absolute_file_uri(tmp_path: Path) -> None:
    target = tmp_path / "local page.html"
    assert _load_script()._to_target(str(target)) == target.as_uri()


def test_no_browser_returns_documented_exit_code(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    capture = _load_script()
    monkeypatch.setattr(capture, "_find_browser", lambda: None)

    assert capture.main(["index.html", "--out", str(tmp_path / "shot.png")]) == 3
    assert "no headless Chromium-family browser found" in capsys.readouterr().err


def test_cli_no_browser_fallback_runs_end_to_end(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "index.html", "--out", str(tmp_path / "shot.png")],
        capture_output=True,
        text=True,
        env={"PATH": str(tmp_path)},
        check=False,
    )

    assert result.returncode == 3
    assert "Install one" in result.stderr
    assert not (tmp_path / "shot.png").exists()


def test_success_writes_capture_and_reports_browser(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    capture = _load_script()
    output = tmp_path / "shot.png"
    target = tmp_path / "page.html"
    monkeypatch.setattr(capture, "_find_browser", lambda: "C:/Browser/chrome.exe")
    observed: list[str] = []

    def run(command: list[str], *, check: bool, capture_output: bool, timeout: int) -> None:
        assert check and capture_output and timeout == 120
        observed.extend(command)
        output.write_bytes(b"PNG")

    monkeypatch.setattr(capture.subprocess, "run", run)

    assert capture.main([str(target), "--out", str(output), "--width", "480", "--height", "320"]) == 0
    assert observed == [
        "C:/Browser/chrome.exe",
        "--headless=new",
        "--disable-gpu",
        "--window-size=480,320",
        f"--screenshot={output}",
        target.as_uri(),
    ]
    assert "captured" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, "chrome"),
        subprocess.TimeoutExpired("chrome", 120),
        OSError("launch failed"),
    ],
)
def test_browser_failure_returns_two(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path, error: Exception) -> None:
    capture = _load_script()
    monkeypatch.setattr(capture, "_find_browser", lambda: "chrome")

    def fail(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(capture.subprocess, "run", fail)

    assert capture.main(["index.html", "--out", str(tmp_path / "shot.png")]) == 2
    assert "browser capture failed" in capsys.readouterr().err


def test_missing_screenshot_returns_two(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    capture = _load_script()
    output = tmp_path / "shot.png"
    monkeypatch.setattr(capture, "_find_browser", lambda: "chrome")
    monkeypatch.setattr(capture.subprocess, "run", lambda *args, **kwargs: None)

    assert capture.main(["index.html", "--out", str(output)]) == 2
    assert f"screenshot not produced at {output}" in capsys.readouterr().err
