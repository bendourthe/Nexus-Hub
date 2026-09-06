"""Cross-platform wrapper tests for the model-routing map helper."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = ROOT / "catalog" / "skills" / "ai-development" / "model-routing"
SCRIPTS = SKILL_DIR / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "model-routing"
Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture(params=("sh", "ps1"))
def run(request: pytest.FixtureRequest) -> Runner:
    implementation = request.param
    interpreter = request.getfixturevalue(
        "bash_bin" if implementation == "sh" else "powershell_bin"
    )
    script = SCRIPTS / f"model-map.{implementation}"

    def invoke(*args: str) -> subprocess.CompletedProcess[str]:
        command = [interpreter]
        if implementation == "ps1":
            command.extend(("-NoProfile", "-File"))
        command.extend((str(script), *args))
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    return invoke


def test_wrapper_scores_all_low_as_fast(
    run: Runner,
) -> None:
    result = run("score", "low", "low", "low", "low", "low")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"tier": "fast", "effort": "low"}


def test_wrapper_validates_four_by_four_fixture(
    run: Runner,
) -> None:
    result = run("validate", str(FIXTURES / "valid-map.json"))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"] is True


def test_wrapper_rejects_empty_provider_column(
    run: Runner,
) -> None:
    result = run("validate", str(FIXTURES / "empty-provider-column.json"))
    assert result.returncode == 1
    assert "frontier/Cursor" in result.stderr
