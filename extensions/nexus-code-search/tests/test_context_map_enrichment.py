"""Phase 4 tests: hot-file ranking + git-scoped change map."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.contextmap import generate_context_map
from nexus_code_search.contextmap.changemap import compute_change_map
from nexus_code_search.contextmap.cli import main as map_cli_main
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph.affected import most_imported_files


def _cfg() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


def _index_dir(root: Path) -> Path:
    return index_dir_for(root, _cfg())


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )


@pytest.fixture
def import_repo(tmp_path: Path) -> Path:
    (tmp_path / "utils.py").write_text(
        "def helper():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "models.py").write_text("class Thing:\n    pass\n", encoding="utf-8")
    (tmp_path / "a.py").write_text(
        "from utils import helper\nfrom models import Thing\n", encoding="utf-8"
    )
    (tmp_path / "b.py").write_text("import utils\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("from utils import helper\n", encoding="utf-8")
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@e.st")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "utils.py").write_text(
        "def helper():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "service.py").write_text(
        "from utils import helper\n\ndef run():\n    return helper()\n",
        encoding="utf-8",
    )
    (tmp_path / "api.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n\n"
        "@app.get('/ping')\ndef ping():\n    return 'pong'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_service.py").write_text(
        "from service import run\n\ndef test_run():\n    assert run() == 1\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "baseline")
    # Modify utils.py (test_service transitively imports it) and api.py.
    (tmp_path / "utils.py").write_text(
        "def helper():\n    return 2\n", encoding="utf-8"
    )
    (tmp_path / "api.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n\n"
        "@app.get('/ping')\ndef ping():\n    return 'pong2'\n",
        encoding="utf-8",
    )
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    return tmp_path


# --- Hot files --------------------------------------------------------------


def test_most_imported_ranks_by_inbound(import_repo: Path) -> None:
    conn = open_database(_index_dir(import_repo))
    try:
        ranked = most_imported_files(conn)
    finally:
        conn.close()
    rank_map = dict(ranked)
    assert rank_map["utils.py"] == 3  # a, b, c import it
    assert rank_map["models.py"] == 1  # only a
    assert ranked[0][0] == "utils.py"  # highest count first
    assert "a.py" not in rank_map  # nobody imports a


def test_most_imported_limit(import_repo: Path) -> None:
    conn = open_database(_index_dir(import_repo))
    try:
        ranked = most_imported_files(conn, limit=1)
    finally:
        conn.close()
    assert len(ranked) == 1
    assert ranked[0][0] == "utils.py"


def test_map_fills_most_imported_section(import_repo: Path) -> None:
    generate_context_map(import_repo, _index_dir(import_repo))
    text = (import_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    assert "## Most-Imported Files" in text
    assert "| File | Imported by |" in text
    assert "`utils.py`" in text
    assert "code_impact" in text  # labeled distinct from the symbol-level view
    assert "Not yet available" not in text  # placeholder replaced


# --- Change map -------------------------------------------------------------


def test_compute_change_map(git_repo: Path) -> None:
    conn = open_database(_index_dir(git_repo))
    try:
        change = compute_change_map(conn, git_repo, "HEAD")
    finally:
        conn.close()
    assert change is not None
    assert set(change.changed_files) == {"utils.py", "api.py"}
    assert "test_service.py" in change.affected_tests  # transitive reverse-import
    assert "GET /ping" in change.affected_routes
    assert any("helper" in s for s in change.affected_symbols)


def test_change_map_bad_ref_returns_none(git_repo: Path) -> None:
    conn = open_database(_index_dir(git_repo))
    try:
        assert compute_change_map(conn, git_repo, "no-such-ref-xyz") is None
    finally:
        conn.close()


def test_change_map_non_git_returns_none(import_repo: Path) -> None:
    # import_repo is not a git repository.
    conn = open_database(_index_dir(import_repo))
    try:
        assert compute_change_map(conn, import_repo, "HEAD") is None
    finally:
        conn.close()


def test_cli_since_mode(git_repo: Path, capsys: pytest.CaptureFixture) -> None:
    rc = map_cli_main([str(git_repo), "--since", "HEAD", "--json"])
    assert rc == 0
    import json

    payload = json.loads(capsys.readouterr().out)
    assert payload["ref"] == "HEAD"
    assert "test_service.py" in payload["affected_tests"]


def test_cli_since_human_output(
    git_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    rc = map_cli_main([str(git_repo), "--since", "HEAD"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Change map since HEAD" in out
    assert "affected tests" in out
    assert "test_service.py" in out


def test_cli_since_bad_ref(git_repo: Path) -> None:
    assert map_cli_main([str(git_repo), "--since", "no-such-ref-xyz"]) == 1
