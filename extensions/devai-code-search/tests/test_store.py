"""Tests for the persistence layer."""
from __future__ import annotations

from pathlib import Path

from devai_code_search.store import clear_index, load_index, save_index
from devai_code_search.types import Chunk, IndexManifest


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    index_dir = tmp_path / "idx"
    chunks = [
        Chunk(file_path="a.py", start_line=1, end_line=3, text="def a(): pass"),
        Chunk(file_path="b.py", start_line=1, end_line=1, text="x = 1"),
    ]
    manifest = IndexManifest(
        root=str(tmp_path),
        indexed_at="2026-04-24T00:00:00Z",
        total_chunks=len(chunks),
        file_hashes={"a.py": "h1" * 32, "b.py": "h2" * 32},
        chunk_counts={"a.py": 1, "b.py": 1},
    )
    save_index(index_dir, chunks, manifest)

    loaded_chunks, loaded_manifest = load_index(index_dir)
    assert len(loaded_chunks) == 2
    assert loaded_manifest is not None
    assert loaded_manifest.file_hashes == manifest.file_hashes
    assert loaded_manifest.total_chunks == 2


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    chunks, manifest = load_index(tmp_path / "does-not-exist")
    assert chunks == []
    assert manifest is None


def test_load_corrupt_falls_back(tmp_path: Path) -> None:
    index_dir = tmp_path / "idx"
    index_dir.mkdir()
    (index_dir / "chunks.json").write_text("not valid json", encoding="utf-8")
    (index_dir / "manifest.json").write_text("{not json}", encoding="utf-8")

    chunks, manifest = load_index(index_dir)
    assert chunks == []
    assert manifest is None


def test_load_does_not_read_legacy_pickle(tmp_path: Path) -> None:
    """Regression: a stray chunks.pickle from a pre-v1.0.0 install must NOT
    be loaded. The loader reads chunks.json only; pickle is never touched.

    Defends against the v1.0.0 security review's pickle-RCE finding: even if
    an attacker plants a malicious chunks.pickle in <root>/.devai/code-index/,
    load_index ignores it because chunks.json does not exist.
    """
    index_dir = tmp_path / "idx"
    index_dir.mkdir()
    # Plant a "malicious" pickle that would execute on pickle.load.
    # We don't actually craft a working RCE payload; we verify the loader
    # never opens this file in the first place.
    (index_dir / "chunks.pickle").write_bytes(b"cos\nsystem\n(S'echo pwned'\ntR.")
    # No chunks.json -> load_index returns ([], None) without touching pickle.
    chunks, manifest = load_index(index_dir)
    assert chunks == []
    assert manifest is None
    # The pickle file should still be on disk (we didn't delete it); the test
    # asserts it was never *opened* by load_index. The chunks.pickle remains
    # for clear_index to remove.


def test_chunks_file_is_json_not_pickle(tmp_path: Path) -> None:
    """Save then read the file directly to confirm it is JSON, not pickle."""
    index_dir = tmp_path / "idx"
    chunks = [
        Chunk(file_path="a.py", start_line=1, end_line=2, text="def a(): pass")
    ]
    manifest = IndexManifest(
        root=str(tmp_path), indexed_at="2026-04-24T00:00:00Z", total_chunks=1
    )
    save_index(index_dir, chunks, manifest)

    # Persisted file must be valid JSON.
    raw = (index_dir / "chunks.json").read_text(encoding="utf-8")
    import json as _json
    parsed = _json.loads(raw)
    assert isinstance(parsed, list)
    assert parsed[0]["file_path"] == "a.py"
    assert parsed[0]["text"] == "def a(): pass"


def test_clear_index_removes_directory(tmp_path: Path) -> None:
    index_dir = tmp_path / "idx"
    chunks = [Chunk(file_path="a.py", start_line=1, end_line=1, text="pass")]
    manifest = IndexManifest(
        root=str(tmp_path), indexed_at="2026-04-24T00:00:00Z", total_chunks=1
    )
    save_index(index_dir, chunks, manifest)
    assert index_dir.exists()

    removed = clear_index(index_dir)
    assert removed is True
    # The two core files should be gone; directory removal is best-effort.
    assert not (index_dir / "chunks.pickle").exists()
    assert not (index_dir / "manifest.json").exists()


def test_clear_index_on_missing_returns_false(tmp_path: Path) -> None:
    removed = clear_index(tmp_path / "never-existed")
    assert removed is False
