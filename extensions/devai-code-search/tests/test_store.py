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
    (index_dir / "chunks.pickle").write_bytes(b"not a real pickle")
    (index_dir / "manifest.json").write_text("{not json}", encoding="utf-8")

    chunks, manifest = load_index(index_dir)
    assert chunks == []
    assert manifest is None


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
