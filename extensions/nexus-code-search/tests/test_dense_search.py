"""Optional offline-only dense and hybrid retrieval contracts."""

from __future__ import annotations

import builtins
import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.search_dense import (
    DenseSearchConfig,
    _onnx_backend_factory,
    build_local_encoder,
    hybrid_search,
)
from nexus_code_search.server import _handle_index, _handle_search
from nexus_code_search.types import Chunk


def _chunk(text: str, path: str) -> Chunk:
    return Chunk(path, 1, 1, text)


def _payload(contents: list) -> dict:
    return json.loads(contents[0].text)


def test_dense_extra_is_off_by_default() -> None:
    assert DenseSearchConfig().enabled is False
    assert CodeSearchConfig(hub_root=None).dense_enabled is False


def test_keyword_path_never_imports_optional_dense_dependencies(
    sample_tree: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object):
        if name.split(".")[0] in {"onnxruntime", "numpy", "tokenizers"}:
            raise AssertionError(f"keyword path imported optional dependency {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    config = CodeSearchConfig(hub_root=None)
    _handle_index({"root": str(sample_tree)}, config)
    payload = _payload(
        _handle_search({"root": str(sample_tree), "query": "compute_total"}, config)
    )
    assert payload["mode"] == "keyword"
    assert payload["results"]

    hybrid_payload = _payload(
        _handle_search(
            {"root": str(sample_tree), "query": "compute_total", "mode": "hybrid"},
            config,
        )
    )
    assert hybrid_payload["mode"] == "keyword"
    assert hybrid_payload["degraded"] is False


def test_enabled_missing_weights_degrades_without_import_or_network(
    sample_tree: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object):
        if name.split(".")[0] in {"onnxruntime", "numpy", "tokenizers"}:
            raise AssertionError(f"missing-weights path imported {name}")
        return original_import(name, *args, **kwargs)

    def reject_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dense path attempted a network connection")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    model_dir = tmp_path / "missing-weights"
    config = CodeSearchConfig(
        hub_root=None,
        dense_enabled=True,
        dense_model_dir=str(model_dir),
    )
    _handle_index({"root": str(sample_tree)}, config)
    payload = _payload(
        _handle_search(
            {"root": str(sample_tree), "query": "compute_total", "mode": "hybrid"},
            config,
        )
    )

    assert payload["requested_mode"] == "hybrid"
    assert payload["mode"] == "keyword"
    assert payload["degraded"] is True
    assert payload["results"]
    assert "nexus-code-search[dense]" in payload["hint"]
    assert str(model_dir) in payload["hint"]
    assert "never downloads" in payload["hint"]


def test_preplaced_weights_build_injected_local_encoder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_dir = tmp_path / "weights"
    model_dir.mkdir()
    model_path = model_dir / "model.onnx"
    tokenizer_path = model_dir / "tokenizer.json"
    model_path.write_bytes(b"local-model")
    tokenizer_path.write_text("{}", encoding="utf-8")
    captured: list[tuple[Path, Path]] = []

    def reject_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("pre-placed local encoder attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", reject_connection)

    def factory(model: Path, tokenizer: Path):
        captured.append((model, tokenizer))
        return lambda texts: [[float(index), 1.0] for index, _ in enumerate(texts)]

    encoder, hint = build_local_encoder(
        DenseSearchConfig(enabled=True, model_dir=str(model_dir)),
        backend_factory=factory,
    )
    assert hint is None
    assert encoder is not None
    assert encoder(["query", "document"]) == [[0.0, 1.0], [1.0, 1.0]]
    assert captured == [(model_path, tokenizer_path)]


def test_preplaced_weights_with_missing_dependency_degrade_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_dir = tmp_path / "weights"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"local-model")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

    def reject_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("missing-dependency path attempted a network connection")

    def missing_dependency(_model: Path, _tokenizer: Path):
        raise ImportError("onnxruntime")

    monkeypatch.setattr(socket.socket, "connect", reject_connection)
    encoder, hint = build_local_encoder(
        DenseSearchConfig(enabled=True, model_dir=str(model_dir)),
        backend_factory=missing_dependency,
    )
    assert encoder is None
    assert hint and "optional dependency not installed" in hint
    assert str(model_dir) in hint
    assert "never downloads" in hint


def test_local_onnx_adapter_uses_preplaced_files_and_cpu_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = tmp_path / "model.onnx"
    tokenizer_path = tmp_path / "tokenizer.json"
    model_path.write_bytes(b"local-model")
    tokenizer_path.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    class FakeArray:
        def __init__(self, values: list) -> None:
            self.values = values
            self.ndim = 2 if values and isinstance(values[0], list) else 1

        def tolist(self) -> list:
            return self.values

    class FakeSession:
        output: ClassVar[list] = [[0.1, 0.2], [0.3, 0.4]]

        def __init__(self, path: str, *, providers: list[str]) -> None:
            captured["model_path"] = path
            captured["providers"] = providers

        def get_inputs(self) -> list[SimpleNamespace]:
            return [SimpleNamespace(name="input_ids"), SimpleNamespace(name="attention_mask")]

        def run(self, _outputs: object, feeds: dict[str, FakeArray]) -> list[list]:
            captured["feeds"] = feeds
            return [self.output]

    class FakeTokenizer:
        @classmethod
        def from_file(cls, path: str) -> FakeTokenizer:
            captured["tokenizer_path"] = path
            return cls()

        def encode_batch(self, texts: list[str]) -> list[SimpleNamespace]:
            return [SimpleNamespace(ids=list(range(len(text.split())))) for text in texts]

    fake_numpy = SimpleNamespace(asarray=lambda values, dtype: FakeArray(values))
    fake_onnx = SimpleNamespace(InferenceSession=FakeSession)
    fake_tokenizers = SimpleNamespace(Tokenizer=FakeTokenizer)
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_onnx)
    monkeypatch.setitem(sys.modules, "tokenizers", fake_tokenizers)

    encoder = _onnx_backend_factory(model_path, tokenizer_path)
    assert encoder(["two tokens", "one"]) == [[0.1, 0.2], [0.3, 0.4]]
    assert encoder([""]) == [[]]
    assert captured["model_path"] == str(model_path)
    assert captured["tokenizer_path"] == str(tokenizer_path)
    assert captured["providers"] == ["CPUExecutionProvider"]
    assert set(captured["feeds"]) == {"input_ids", "attention_mask"}

    FakeSession.output = [1.0]
    with pytest.raises(ValueError, match="rank 2 or 3"):
        encoder(["invalid output"])


def test_preplaced_weights_with_broken_backend_degrade_locally(tmp_path: Path) -> None:
    model_dir = tmp_path / "weights"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"local-model")
    (model_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

    def broken_backend(_model: Path, _tokenizer: Path):
        raise RuntimeError("invalid local model")

    encoder, hint = build_local_encoder(
        DenseSearchConfig(enabled=True, model_dir=str(model_dir)),
        backend_factory=broken_backend,
    )
    assert encoder is None
    assert hint and "failed to load local weights" in hint


def test_hybrid_ranking_combines_keyword_and_injected_dense_scores() -> None:
    chunks = [
        _chunk("parse structured payload", "keyword.py"),
        _chunk("unrelated words", "semantic.py"),
    ]

    def encoder(texts: list[str]) -> list[list[float]]:
        assert len(texts) == 3
        return [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]

    outcome = hybrid_search(
        chunks,
        "parse payload",
        limit=2,
        config=DenseSearchConfig(enabled=True, dense_weight=0.8),
        encoder=encoder,
    )
    assert outcome.mode == "hybrid"
    assert outcome.results[0].chunk.file_path == "semantic.py"
    assert outcome.hint is None


def test_failing_encoder_degrades_to_keyword_results() -> None:
    chunks = [_chunk("payment processor", "pay.py")]

    def fail(_texts: list[str]) -> list[list[float]]:
        raise RuntimeError("bad local model")

    outcome = hybrid_search(
        chunks,
        "payment",
        limit=10,
        config=DenseSearchConfig(enabled=True),
        encoder=fail,
    )
    assert outcome.mode == "keyword"
    assert outcome.degraded is True
    assert outcome.results[0].chunk.file_path == "pay.py"
    assert outcome.hint and "encoder failed" in outcome.hint


def test_dense_module_contains_no_download_surface() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "nexus_code_search"
        / "search_dense.py"
    ).read_text(encoding="utf-8").lower()
    forbidden = (
        "requests",
        "httpx",
        "urllib",
        "huggingface",
        "snapshot_download",
        "from_pretrained",
        "http://",
        "https://",
    )
    assert not any(token in source for token in forbidden)


def test_readme_keeps_zero_download_claim_and_documents_local_weights() -> None:
    readme = (
        Path(__file__).resolve().parents[1] / "README.md"
    ).read_text(encoding="utf-8")
    assert "zero outbound calls, zero API keys, zero model downloads" in readme
    assert "pip install -e '.[dense]'" in readme
    assert "model.onnx" in readme
    assert "tokenizer.json" in readme
    assert "never downloads" in readme
