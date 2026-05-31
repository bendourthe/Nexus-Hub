"""Tests for catalog/skills/workflow/demo-capture/scripts/capture-demo.py.

Covers probe-mode plan shape, project-type detection, and graceful
degradation when a capture tool is absent (exit 0, no hard failure).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "catalog" / "skills" / "workflow" / "demo-capture" / "scripts" / "capture-demo.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("capture_demo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


cd = _load_module()


# --- project-type detection --------------------------------------------------


def test_detects_web_from_package_json(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "18"}}', encoding="utf-8")
    assert cd.detect_project_type(tmp_path) == "web"


def test_detects_web_from_index_html(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    assert cd.detect_project_type(tmp_path) == "web"


def test_detects_cli_from_pyproject_scripts(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project.scripts]\nmytool = 'm:main'\n", encoding="utf-8")
    assert cd.detect_project_type(tmp_path) == "cli"


def test_detects_api_from_fastapi(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = ['fastapi']\n", encoding="utf-8")
    assert cd.detect_project_type(tmp_path) == "api"


def test_unknown_project_is_generic(tmp_path: Path):
    assert cd.detect_project_type(tmp_path) == "generic"


# --- tier recommendation -----------------------------------------------------


def test_web_recommends_browser_tier():
    tier, needed = cd.recommend_tier("web")
    assert tier == "browser-screenshots"
    assert needed == "browser"


def test_cli_recommends_terminal_tier():
    tier, needed = cd.recommend_tier("cli")
    assert tier == "terminal-recording"
    assert needed == "recorder"


# --- probe plan shape --------------------------------------------------------


def test_build_plan_has_required_keys(tmp_path: Path):
    plan = cd.build_plan(tmp_path, tmp_path / "docs" / "demos", "web")
    for key in (
        "project_type",
        "recommended_tier",
        "needed_capability",
        "available_tools",
        "missing_capabilities",
        "blocking_capabilities",
        "install_hints",
        "out_dir",
        "upload",
    ):
        assert key in plan, f"missing plan key: {key}"
    assert "disabled" in plan["upload"]  # local-only assertion present


# --- CLI: probe + graceful degradation ---------------------------------------


def test_cli_probe_emits_json(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "probe", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["project_type"] == "generic"
    assert plan["recommended_tier"] == "terminal-recording"


def test_capture_degrades_gracefully_when_browser_missing(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mode",
            "capture",
            "--type",
            "web",
            "--root",
            str(tmp_path),
            "--browser",
            "/definitely/not/a/real/browser",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # Must NOT fail hard: exit 0, report the missing capability with a hint.
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["captured"] == []
    assert payload["skipped"], "expected a skipped entry for the missing browser"
    assert any("browser" == s.get("capability") for s in payload["skipped"])
    assert any("Install" in (s.get("hint") or "") for s in payload["skipped"])


def test_capture_degrades_gracefully_when_recorder_missing(tmp_path: Path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--mode",
            "capture",
            "--type",
            "cli",
            "--root",
            str(tmp_path),
            "--recorder",
            "/definitely/not/a/real/recorder",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["captured"] == []
    assert any(s.get("capability") == "recorder" for s in payload["skipped"])
