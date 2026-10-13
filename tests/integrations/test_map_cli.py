"""Exercise map dispatch through the real nexus-hub script entry point."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.extraction import ExtractionOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SCRIPT = REPO_ROOT / "scripts" / "nexus_hub_cli.py"
EXTENSION_SOURCE = REPO_ROOT / "extensions" / "nexus-code-search" / "src"


@pytest.fixture
def indexed_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repository with spaces"
    source = root / "src"
    source.mkdir(parents=True)
    (source / "sample.py").write_text(
        "def sample_function(value):\n    return value + 1\n", encoding="utf-8"
    )
    config = CodeSearchConfig(hub_root=None)
    with ExtractionOrchestrator(root, config, index_dir_for(root, config)) as orch:
        orch.run(force=True)
    return root


def _run_map(root: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(EXTENSION_SOURCE) + os.pathsep + env.get("PYTHONPATH", "")
    env["NEXUS_HUB_HOME"] = str(root.parent / "unused install")
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), "map", str(root), *argv],
        cwd=root.parent,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )


def test_map_dispatch_forwards_root_json_and_force(indexed_repo: Path) -> None:
    generated = _run_map(indexed_repo, "--json")
    assert generated.returncode == 0, generated.stderr
    payload = json.loads(generated.stdout)
    map_path = indexed_repo / ".nexus" / "CONTEXT-MAP.md"
    assert Path(payload["root"]) == indexed_repo
    assert Path(payload["map_path"]) == map_path
    assert payload["files_indexed"] == 1
    assert payload["skipped"] is False
    original = map_path.read_text(encoding="utf-8")
    assert "[`src`](context/src.md)" in original
    article = indexed_repo / ".nexus" / "context" / "src.md"
    assert "src/sample.py" in article.read_text(encoding="utf-8")

    unchanged = _run_map(indexed_repo, "--json")
    assert unchanged.returncode == 0, unchanged.stderr
    assert json.loads(unchanged.stdout)["skipped"] is True

    map_path.write_text(original + "stale artifact sentinel\n", encoding="utf-8")
    forced = _run_map(indexed_repo, "--force", "--json")
    assert forced.returncode == 0, forced.stderr
    assert json.loads(forced.stdout)["skipped"] is False
    assert map_path.read_text(encoding="utf-8") == original


def test_map_dispatch_preserves_lint_failure(indexed_repo: Path) -> None:
    generated = _run_map(indexed_repo, "--force")
    assert generated.returncode == 0, generated.stderr
    orphan = indexed_repo / ".nexus" / "context" / "orphan.md"
    orphan.write_text("# Orphan\n", encoding="utf-8")

    linted = _run_map(indexed_repo, "--lint", "--json")

    assert linted.returncode == 1, linted.stderr
    payload = json.loads(linted.stdout)
    assert payload["map_present"] is True
    assert payload["healthy"] is False
    assert payload["orphans"] == ["orphan.md"]
    assert orphan.read_text(encoding="utf-8") == "# Orphan\n"


def test_map_dispatch_preserves_malformed_argument_diagnostic(indexed_repo: Path) -> None:
    malformed = _run_map(indexed_repo, "--not-a-map-option")

    assert malformed.returncode == 2
    assert malformed.stdout == ""
    assert "usage: nexus-hub map" in malformed.stderr
    assert "unrecognized arguments: --not-a-map-option" in malformed.stderr


def test_map_dispatch_preserves_missing_index_diagnostic(tmp_path: Path) -> None:
    root = tmp_path / "unindexed repository with spaces"
    root.mkdir()

    missing = _run_map(root, "--json")

    assert missing.returncode == 2
    assert missing.stdout == ""
    assert "no graph index found" in missing.stderr
    assert str(root / ".nexus" / "code-index" / "codegraph.db") in missing.stderr
