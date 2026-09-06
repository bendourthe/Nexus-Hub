"""Tests for v3.15.9 generic routing and provider-map helpers."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "catalog" / "skills" / "ai-development" / "model-routing"
SCRIPT = SKILL_DIR / "scripts" / "model-map.py"
SNAPSHOT = SKILL_DIR / "references" / "last-known-model-map.json"
FIXTURES = ROOT / "tests" / "fixtures" / "model-routing"


def _load_helper() -> ModuleType:
    spec = importlib.util.spec_from_file_location("model_map_helper", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODEL_MAP = _load_helper()


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


@pytest.mark.parametrize(
    ("signals", "extra", "expected"),
    (
        (["low"] * 5, [], {"tier": "fast", "effort": "low"}),
        (
            ["medium", "low", "low", "low", "low"],
            [],
            {"tier": "standard", "effort": "medium"},
        ),
        (
            ["medium", "medium", "medium", "low", "low"],
            [],
            {"tier": "strong", "effort": "high"},
        ),
        (
            ["high", "low", "low", "low", "low"],
            [],
            {"tier": "frontier", "effort": "high"},
        ),
        (["low"] * 5, ["--uncertain"], {"tier": "frontier", "effort": "max"}),
    ),
)
def test_rubric_maps_to_generic_tier_and_effort(
    signals: list[str], extra: list[str], expected: dict[str, str]
) -> None:
    result = _run("score", *signals, *extra)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected


def test_valid_fixture_has_four_by_four_schema() -> None:
    result = _run("validate", str(FIXTURES / "valid-map.json"))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "valid": True,
        "verified_as_of": "2026-08-01",
        "tiers": 4,
        "providers": 4,
    }


def test_empty_provider_column_is_rejected() -> None:
    result = _run("validate", str(FIXTURES / "empty-provider-column.json"))
    assert result.returncode == 1
    assert "empty model cell: frontier/Cursor" in result.stderr


def test_bundled_snapshot_parses_and_renders_dated_fallback() -> None:
    validate_result = _run("validate", str(SNAPSHOT))
    assert validate_result.returncode == 0, validate_result.stderr

    render_result = _run("fallback")
    assert render_result.returncode == 0, render_result.stderr
    rendered = render_result.stdout
    # Derive the date from the snapshot rather than hardcoding it. The contract
    # under test is that the fallback renders the snapshot's own `verified_as_of`
    # in that exact sentence, NOT that the snapshot holds any particular date.
    # A hardcoded date makes this a time bomb that fires on every legitimate map
    # refresh: v3.16.8 found it red because b29a0ffa moved the snapshot to
    # 2026-08-14 while the assertion still read 2026-08-03.
    verified_as_of = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["verified_as_of"]
    assert (
        f"**Model map status**: offline fallback; stale as of {verified_as_of}."
        in rendered
    )
    assert rendered.count("\n| frontier |") == 1
    assert rendered.count("\n| strong |") == 1
    assert rendered.count("\n| standard |") == 1
    assert rendered.count("\n| fast |") == 1
    for provider in ("Anthropic", "OpenAI", "Google", "Cursor"):
        assert f"- {provider}: http" in rendered


def test_fresh_render_uses_explicit_refresh_date() -> None:
    result = _run(
        "render",
        str(FIXTURES / "valid-map.json"),
        "--status",
        "fresh",
        "--as-of",
        "2026-08-03",
    )
    assert result.returncode == 0, result.stderr
    assert (
        "**Model map status**: fresh as of 2026-08-03; sources cited below."
        in result.stdout
    )


def test_unavailable_render_defers_all_sixteen_cells() -> None:
    result = _run("unavailable")
    assert result.returncode == 0, result.stderr
    assert "**Model map status**: unavailable; assess at implementation time." in (
        result.stdout
    )
    assert result.stdout.count("`assess at implementation time`") == 16


@pytest.mark.parametrize(
    "args",
    (
        ["score", "low", "low", "low", "low", "low"],
        ["validate", str(FIXTURES / "valid-map.json")],
        [
            "render",
            str(FIXTURES / "valid-map.json"),
            "--status",
            "fresh",
            "--as-of",
            "2026-08-03",
        ],
        ["fallback"],
        ["unavailable"],
    ),
)
def test_in_process_cli_commands_succeed(
    args: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert MODEL_MAP.main(args) == 0
    assert capsys.readouterr().out


def test_in_process_cli_reports_invalid_map(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        MODEL_MAP.main(["validate", str(FIXTURES / "empty-provider-column.json")]) == 1
    )
    assert "frontier/Cursor" in capsys.readouterr().err


def test_bundle_references_cross_platform_helpers_and_snapshot() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    bundled_files = (
        ("scripts", "model-map.py"),
        ("scripts", "model-map.sh"),
        ("scripts", "model-map.ps1"),
        ("references", "last-known-model-map.json"),
    )
    for directory, basename in bundled_files:
        assert basename in skill
        assert (SKILL_DIR / directory / basename).is_file()
