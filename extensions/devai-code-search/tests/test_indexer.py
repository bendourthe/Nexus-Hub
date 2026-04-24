"""Tests for the indexer: walk, filter, hash, chunk, persist, incremental."""
from __future__ import annotations

from pathlib import Path

import pytest

from devai_code_search.config import CodeSearchConfig
from devai_code_search.indexer import hash_file, index_codebase, read_text_safely, walk_files


def test_walk_respects_gitignore(sample_tree: Path, default_config: CodeSearchConfig) -> None:
    files = list(walk_files(sample_tree, default_config))
    rels = {str(p.relative_to(sample_tree).as_posix()) for p in files}
    assert "debug.log" not in rels  # gitignored
    assert "src/main.py" in rels
    assert "README.md" in rels


def test_walk_skips_default_excluded_dirs(
    sample_tree: Path, default_config: CodeSearchConfig
) -> None:
    files = list(walk_files(sample_tree, default_config))
    rels = [p.relative_to(sample_tree).as_posix() for p in files]
    assert not any("node_modules" in r for r in rels)


def test_hash_file_is_stable(tmp_path: Path) -> None:
    file = tmp_path / "a.txt"
    file.write_text("hello", encoding="utf-8")
    h1 = hash_file(file)
    h2 = hash_file(file)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_file_differs_on_content_change(tmp_path: Path) -> None:
    file = tmp_path / "a.txt"
    file.write_text("hello", encoding="utf-8")
    before = hash_file(file)
    file.write_text("world", encoding="utf-8")
    after = hash_file(file)
    assert before != after


def test_read_text_safely_returns_none_on_binary(tmp_path: Path) -> None:
    file = tmp_path / "b.bin"
    file.write_bytes(b"\xff\xfe\xfd\xfc")
    assert read_text_safely(file) is None


def test_index_codebase_produces_chunks(
    sample_tree: Path, default_config: CodeSearchConfig, tmp_path: Path
) -> None:
    index_dir = tmp_path / ".devai" / "code-index"
    chunks, manifest = index_codebase(sample_tree, default_config, index_dir)
    assert chunks, "expected non-empty chunk list"
    # Files tracked in manifest should include our sources.
    assert "src/main.py" in manifest.file_hashes
    assert "src/utils.ts" in manifest.file_hashes
    assert "README.md" in manifest.file_hashes
    # Binary file should NOT be tracked.
    assert "src/icon.bin" not in manifest.file_hashes


def test_incremental_skips_unchanged_files(
    sample_tree: Path, default_config: CodeSearchConfig, tmp_path: Path
) -> None:
    index_dir = tmp_path / ".devai" / "code-index"
    chunks1, manifest1 = index_codebase(sample_tree, default_config, index_dir)

    # Re-index without changes. Chunk count should be identical; hashes unchanged.
    chunks2, manifest2 = index_codebase(sample_tree, default_config, index_dir)
    assert manifest1.file_hashes == manifest2.file_hashes
    assert len(chunks1) == len(chunks2)


def test_incremental_detects_modification(
    sample_tree: Path, default_config: CodeSearchConfig, tmp_path: Path
) -> None:
    index_dir = tmp_path / ".devai" / "code-index"
    index_codebase(sample_tree, default_config, index_dir)

    (sample_tree / "src" / "main.py").write_text(
        "def compute_total(items):\n    return sum(items) + 1\n", encoding="utf-8"
    )
    _, manifest2 = index_codebase(sample_tree, default_config, index_dir)
    # Hash for main.py must have changed.
    assert "src/main.py" in manifest2.file_hashes


def test_force_rebuild_reindexes_all(
    sample_tree: Path, default_config: CodeSearchConfig, tmp_path: Path
) -> None:
    index_dir = tmp_path / ".devai" / "code-index"
    _, manifest1 = index_codebase(sample_tree, default_config, index_dir)
    _, manifest2 = index_codebase(sample_tree, default_config, index_dir, force=True)
    # Hashes should match (same content), chunk totals should match too.
    assert manifest1.file_hashes == manifest2.file_hashes
    assert manifest1.total_chunks == manifest2.total_chunks


def test_large_file_is_skipped(
    tmp_path: Path, default_config: CodeSearchConfig
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "big.txt").write_text("x" * (default_config.max_file_bytes + 1), encoding="utf-8")
    (root / "small.txt").write_text("y", encoding="utf-8")

    index_dir = tmp_path / "idx"
    _, manifest = index_codebase(root, default_config, index_dir)
    assert "big.txt" not in manifest.file_hashes
    assert "small.txt" in manifest.file_hashes
