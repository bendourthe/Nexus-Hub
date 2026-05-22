"""nexus_hub_affected.py CLI dispatcher tests (T032)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_SCRIPT = REPO_ROOT / "scripts" / "nexus_hub_affected.py"


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_utils.py").write_text(
        "from src.utils import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    config = CodeSearchConfig(hub_root=None)
    index_dir = tmp_path / ".nexus" / "code-index"
    with ExtractionOrchestrator(tmp_path, config, index_dir) as orch:
        orch.run(force=True)
    return tmp_path


def _load_cli_main():
    """Import the script module by absolute path (it's not in any package)."""
    spec = importlib.util.spec_from_file_location("nexus_hub_affected", CLI_SCRIPT)
    assert spec and spec.loader, "CLI script must be importable"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def test_cli_returns_affected_tests_for_changed_source(fixture_repo, capsys) -> None:
    main = _load_cli_main()
    exit_code = main(["--root", str(fixture_repo), "src/utils.py"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "tests/test_utils.py" in captured.out


def test_cli_json_mode(fixture_repo, capsys) -> None:
    main = _load_cli_main()
    exit_code = main(["--root", str(fixture_repo), "--json", "src/utils.py"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["affected_tests"] == ["tests/test_utils.py"]
    assert payload["root"] == str(fixture_repo)


def test_cli_errors_when_no_index_present(tmp_path, capsys) -> None:
    main = _load_cli_main()
    exit_code = main(["--root", str(tmp_path), "src/utils.py"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "no graph index found" in captured.err


def test_cli_errors_when_no_input_files(fixture_repo, capsys) -> None:
    main = _load_cli_main()
    exit_code = main(["--root", str(fixture_repo)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no input files" in captured.err
