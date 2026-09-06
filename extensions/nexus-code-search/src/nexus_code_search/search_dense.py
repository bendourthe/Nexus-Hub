"""Optional offline-only dense and hybrid chunk retrieval."""

from __future__ import annotations

import math
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from nexus_code_search.search_keyword import KeywordIndex
from nexus_code_search.types import Chunk, SearchResult

DenseEncoder = Callable[[list[str]], list[list[float]]]
BackendFactory = Callable[[Path, Path], DenseEncoder]

_MODEL_SUBDIR = ("cache", "models", "code-search-encoder")
_MODEL_FILENAME = "model.onnx"
_TOKENIZER_FILENAME = "tokenizer.json"


@dataclass(frozen=True)
class DenseSearchConfig:
    """Configuration for the opt-in local dense path."""

    enabled: bool = False
    model_dir: str | None = None
    dense_weight: float = 0.35


@dataclass(frozen=True)
class HybridSearchOutcome:
    """Ranked results plus explicit fallback state."""

    results: list[SearchResult]
    mode: str
    degraded: bool = False
    hint: str | None = None


def resolve_model_dir(config: DenseSearchConfig) -> Path:
    """Resolve the read-only local weights directory without creating it."""

    if config.model_dir:
        return Path(config.model_dir).expanduser()
    explicit = os.environ.get("NEXUS_CODE_SEARCH_MODEL_DIR")
    if explicit:
        return Path(explicit).expanduser()
    hub_root = os.environ.get("NEXUS_HUB_ROOT")
    base = Path(hub_root).expanduser() if hub_root else Path.home() / ".nexus-hub"
    return base.joinpath(*_MODEL_SUBDIR)


def _install_hint(reason: str, model_dir: Path) -> str:
    return (
        f"Dense retrieval unavailable ({reason}); using keyword-only search. "
        "Install the optional extra with pip install 'nexus-code-search[dense]' "
        f"and place {_MODEL_FILENAME} plus {_TOKENIZER_FILENAME} in {model_dir}. "
        "The extension only loads pre-placed local weights and never downloads them."
    )


def _onnx_backend_factory(model_path: Path, tokenizer_path: Path) -> DenseEncoder:
    import numpy  # type: ignore
    import onnxruntime  # type: ignore
    from tokenizers import Tokenizer  # type: ignore

    session = onnxruntime.InferenceSession(
        str(model_path), providers=["CPUExecutionProvider"]
    )
    tokenizer = Tokenizer.from_file(str(tokenizer_path))

    def encode(texts: list[str]) -> list[list[float]]:
        encoded = tokenizer.encode_batch(texts)
        max_length = max((len(item.ids) for item in encoded), default=0)
        if max_length == 0:
            return [[] for _ in texts]
        input_ids = numpy.asarray(
            [item.ids + [0] * (max_length - len(item.ids)) for item in encoded],
            dtype="int64",
        )
        attention = numpy.asarray(
            [
                [1] * len(item.ids) + [0] * (max_length - len(item.ids))
                for item in encoded
            ],
            dtype="int64",
        )
        input_names = {item.name for item in session.get_inputs()}
        feeds = {"input_ids": input_ids}
        if "attention_mask" in input_names:
            feeds["attention_mask"] = attention
        output = numpy.asarray(session.run(None, feeds)[0], dtype="float32")
        if output.ndim == 2:
            return output.tolist()
        if output.ndim != 3:
            raise ValueError("local encoder output must be rank 2 or 3")
        mask = attention[..., None]
        totals = (output * mask).sum(axis=1)
        counts = mask.sum(axis=1).clip(min=1)
        return (totals / counts).tolist()

    return encode


def build_local_encoder(
    config: DenseSearchConfig,
    *,
    backend_factory: BackendFactory | None = None,
) -> tuple[DenseEncoder | None, str | None]:
    """Load an encoder only from pre-placed files, otherwise return a hint."""

    model_dir = resolve_model_dir(config)
    model_path = model_dir / _MODEL_FILENAME
    tokenizer_path = model_dir / _TOKENIZER_FILENAME
    if not model_path.is_file() or not tokenizer_path.is_file():
        return None, _install_hint("weights not found", model_dir)
    factory = backend_factory or _onnx_backend_factory
    try:
        return factory(model_path, tokenizer_path), None
    except ImportError as exc:
        return None, _install_hint(
            f"optional dependency not installed: {exc}", model_dir
        )
    except Exception as exc:  # noqa: BLE001 - local backend failures degrade
        return None, _install_hint(f"failed to load local weights: {exc}", model_dir)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )


def hybrid_search(
    chunks: list[Chunk],
    query: str,
    *,
    limit: int,
    config: DenseSearchConfig,
    encoder: DenseEncoder | None = None,
) -> HybridSearchOutcome:
    """Combine normalized keyword and local dense scores, failing soft."""

    keyword_results = KeywordIndex.build(chunks).search(query, limit=len(chunks))
    keyword_fallback = keyword_results[:limit]
    if not config.enabled:
        return HybridSearchOutcome(keyword_fallback, mode="keyword")
    hint: str | None = None
    if encoder is None:
        encoder, hint = build_local_encoder(config)
    if encoder is None:
        return HybridSearchOutcome(
            keyword_fallback, mode="keyword", degraded=True, hint=hint
        )
    try:
        vectors = encoder([query, *(chunk.text for chunk in chunks)])
        if len(vectors) != len(chunks) + 1:
            raise ValueError("encoder returned the wrong vector count")
        query_vector, document_vectors = vectors[0], vectors[1:]
        if not query_vector or any(
            len(vector) != len(query_vector) for vector in document_vectors
        ):
            raise ValueError("encoder returned inconsistent vector dimensions")
        keyword_scores = {result.chunk: result.score for result in keyword_results}
        keyword_max = max(keyword_scores.values(), default=1.0)
        dense_weight = min(1.0, max(0.0, config.dense_weight))
        scored: list[tuple[Chunk, float]] = []
        for chunk, vector in zip(chunks, document_vectors, strict=True):
            keyword_score = keyword_scores.get(chunk, 0.0) / keyword_max
            dense_score = (_cosine(query_vector, vector) + 1.0) / 2.0
            score = (1.0 - dense_weight) * keyword_score + dense_weight * dense_score
            scored.append((chunk, score))
        scored.sort(key=lambda item: (-item[1], item[0].file_path, item[0].start_line))
        results = [
            SearchResult(chunk=chunk, score=round(score, 4), rank=index)
            for index, (chunk, score) in enumerate(scored[:limit], start=1)
        ]
        return HybridSearchOutcome(results, mode="hybrid")
    except Exception as exc:  # noqa: BLE001 - encoder failures degrade
        model_dir = resolve_model_dir(config)
        return HybridSearchOutcome(
            keyword_fallback,
            mode="keyword",
            degraded=True,
            hint=_install_hint(f"encoder failed: {exc}", model_dir),
        )
