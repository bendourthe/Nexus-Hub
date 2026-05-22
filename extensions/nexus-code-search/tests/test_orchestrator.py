"""ExtractionOrchestrator end-to-end tests (T025 / T028)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "def helper():\n"
        "    return 1\n"
        "\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return helper()\n"
        "\n"
        "def main():\n"
        "    s = Service()\n"
        "    return s.run()\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "web.ts").write_text(
        "export class Api {\n"
        "  send(x: number) { return x; }\n"
        "}\n"
        "export function go() {\n"
        "  const a = new Api();\n"
        "  return a.send(1);\n"
        "}\n",
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    return tmp_path


def _config() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


def test_orchestrator_indexes_python_and_typescript(sample_repo: Path) -> None:
    idx_dir = sample_repo / ".nexus" / "code-index"
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        stats = orch.run()
    assert stats.files_indexed == 2
    assert stats.nodes_inserted > 0
    assert stats.edges_inserted > 0


def test_orchestrator_is_idempotent(sample_repo: Path) -> None:
    idx_dir = sample_repo / ".nexus" / "code-index"
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        stats1 = orch.run()
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        stats2 = orch.run()
    # Second run skips unchanged files.
    assert stats2.files_indexed == 0
    assert stats1.nodes_inserted > 0


def test_orchestrator_reindexes_changed_file(sample_repo: Path) -> None:
    idx_dir = sample_repo / ".nexus" / "code-index"
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        orch.run()
    # Modify a file.
    (sample_repo / "src" / "app.py").write_text(
        "def renamed_helper():\n    return 2\n", encoding="utf-8"
    )
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        stats = orch.run()
    assert stats.files_indexed == 1
    # New node should be present.
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        rows = orch.conn.execute(
            "SELECT name FROM nodes WHERE name = 'renamed_helper'"
        ).fetchall()
    assert rows


def test_orchestrator_force_rebuild(sample_repo: Path) -> None:
    idx_dir = sample_repo / ".nexus" / "code-index"
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        orch.run()
    with ExtractionOrchestrator(sample_repo, _config(), idx_dir) as orch:
        stats = orch.run(force=True)
    # Force run reprocesses both files.
    assert stats.files_indexed == 2
