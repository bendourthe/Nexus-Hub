"""MLTokenDropper: optional, default-off ML token-importance dropper.

Every other strategy in this engine is *deterministic* and *reversible*: it
either reorders content (CacheAligner) or drops a span behind a content-hashed
CCR marker that resolves back to the exact original (SmartCrusher,
CodeCompressor). This module is the one exception, and the trade-offs that come
with it are the reason it sits behind an explicit opt-in flag and is off by
default.

It ports headroom's Kompress strategy: a pre-trained ModernBERT token-importance
classifier scores each unit of free text, and the lowest-importance units are
*dropped* to hit a target compression ratio. That is genuinely lossy -- a dropped
word cannot be reconstructed from an importance score, so there is no CCR store
and no retrieval. Free prose is exactly the content the deterministic strategies
leave untouched (the ContentRouter passes ``text`` through verbatim), so this is
the only path that compresses it, at the cost of fidelity. The Phase 5
accuracy-regression gate exists precisely to keep a lossy default off the shipping
pipeline; this module honors that by staying opt-in.

Granularity. The upstream classifier scores sub-word tokens; this port scores and
drops at the **whitespace-word** granularity instead. A word is the unit a human
(or an agent) reads, it reconstructs to readable text without sub-word detokenizer
gymnastics, and the inter-word spacing of surviving runs is preserved, so the
output stays legible. The model's sub-word scores are mean-pooled up to their
covering word (see :func:`_pool_subword_scores`).

Local-first, offline-first, zero-outbound -- the non-negotiables:

* **The module never downloads anything.** It *loads* public pre-trained weights
  that the user has placed once in a local cache, exactly as ``tiktoken`` loads a
  cached vocab and the v3.0.0 OSV.dev DB ships offline-first. The one-time public
  weight download is the user's step (documented in the install hint and the
  README); it carries no user data, and this code path makes no network call.
* **No user data leaves the machine.** Scoring runs entirely in-process via a
  local ``onnxruntime`` session. The text being compressed is never transmitted.
* **Graceful degradation.** When the optional ``ml`` extra (``onnxruntime`` and
  its numeric companions) or the local weights are absent, the dropper returns the
  original text unchanged together with a clear install hint -- it never raises and
  never blocks the engine.

The importance scorer is a pluggable seam (``scorer``): the drop logic is fully
exercisable with an injected scorer (and so is testable without the heavy ONNX
backend), and a consumer may supply its own. The shipped default backend
(:func:`build_onnx_scorer`) is built against the documented ``onnxruntime`` /
``tokenizers`` / ``numpy`` APIs and is selected only when every piece is present.

Deterministic given a fixed scorer: no clock, no randomness. Keeper selection
breaks score ties by original position, so the same text and scores always yield
the same survivors. Reference behavior: ``docs/v3.2.0/comparison-headroom.md``
Section 5a (Kompress ML token-dropping).
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..tokens import count_tokens

# The importance-scorer contract. Given the ordered words of a text, return one
# score per word (higher = more important = more likely to be kept). Pluggable so
# the drop logic never depends on the ONNX backend.
Scorer = Callable[[list[str]], "list[float]"]

# Whitespace-delimited word: a maximal run of non-whitespace. ``finditer`` over
# this yields each word plus its char span, which the reconstructor uses to keep
# the original spacing between surviving neighbors.
_WORD_RE = re.compile(r"\S+")

# Default sub-directory (under the Nexus-Hub cache) where the user places the
# public pre-trained weights. The bundle is a directory holding the ONNX model
# and its tokenizer; the module reads it but never writes or fetches it.
_MODEL_SUBDIR = ("cache", "models", "importance-scorer")
_MODEL_FILENAME = "model.onnx"
_TOKENIZER_FILENAME = "tokenizer.json"


def _install_hint(reason: str, model_dir: Path | None = None) -> str:
    """Build the user-facing degradation hint, naming the precise missing piece."""
    where = f" Expected weights bundle: {model_dir}." if model_dir is not None else ""
    return (
        f"ML token-dropper unavailable ({reason}); returning text unchanged. "
        "Install the optional extra (pip install 'nexus-context-compressor[ml]') "
        f"and place the public pre-trained importance-scorer weights "
        f"({_MODEL_FILENAME} + {_TOKENIZER_FILENAME}) in the local cache."
        f"{where} The module never downloads weights and sends no data anywhere; "
        "obtain them once from the public model card."
    )


@dataclass(frozen=True)
class MLTokenDropperConfig:
    """Tunables for the optional ML token-dropper.

    Attributes:
        enabled: master opt-in switch. **Off by default** -- with ``enabled`` false
            the dropper is a pure identity and never touches the scorer or the
            ONNX backend. The deterministic strategies remain the default pipeline.
        target_ratio: fraction of words to **keep** (token-retention target, the
            same direction as ``CompressResult.ratio``). ``0.5`` keeps the top
            ~50% of words by importance and drops the rest. Clamped to ``[0, 1]``;
            at least one word is always kept.
        min_words: texts with fewer words than this are returned unchanged (too
            short for a meaningful, safe drop).
        model_dir: explicit path to the weights bundle directory. ``None`` resolves
            the default cache location (see :func:`_resolve_model_dir`).
    """

    enabled: bool = False
    target_ratio: float = 0.5
    min_words: int = 20
    model_dir: str | None = None


@dataclass
class DropResult:
    """The outcome of running the ML token-dropper over one text.

    Attributes:
        text: the (possibly) compressed text. Equal to the input whenever the
            dropper did not run (disabled, too short, or degraded).
        tokens_before / tokens_after: whole-text token accounting via
            ``tokens.count_tokens``.
        words_before / words_after: whitespace-word counts before/after the drop.
        ran: ``True`` only when a scorer actually scored and words were dropped (or
            could have been). ``False`` for the identity paths (disabled / short).
        degraded: ``True`` when the dropper was enabled but the backend was
            unavailable, so it fell back to the original text plus ``hint``.
        hint: the user-facing install/obtain-weights hint when ``degraded``.
    """

    text: str
    tokens_before: int
    tokens_after: int
    words_before: int = 0
    words_after: int = 0
    ran: bool = False
    degraded: bool = False
    hint: str | None = None

    @property
    def ratio(self) -> float:
        """Fraction of tokens retained (``tokens_after / tokens_before``)."""
        if self.tokens_before <= 0:
            return 1.0
        return self.tokens_after / self.tokens_before

    @property
    def dropped_words(self) -> int:
        """Number of words removed (never negative)."""
        return max(0, self.words_before - self.words_after)


# --- Pure selection + reconstruction (no ML, fully testable) ----------------


def _select_keepers(scores: list[float], target_ratio: float) -> set[int]:
    """Indices of the words to keep: the top ``target_ratio`` by score.

    Keeps ``ceil(n * ratio)`` words (at least one), chosen by highest score and,
    on a tie, by earliest position -- so selection is deterministic for a fixed
    score vector. Returns a set of kept indices into the original word list.
    """
    n = len(scores)
    if n == 0:
        return set()
    ratio = min(1.0, max(0.0, target_ratio))
    keep_n = max(1, math.ceil(n * ratio))
    if keep_n >= n:
        return set(range(n))
    # Rank by descending score, ascending index on ties; take the top keep_n.
    order = sorted(range(n), key=lambda i: (-scores[i], i))
    return set(order[:keep_n])


def _reconstruct(text: str, matches: list[re.Match[str]], keep: set[int]) -> str:
    """Rejoin the kept words, preserving original spacing between survivors.

    For two kept words that were adjacent in the input (no dropped word between
    them), the original inter-word whitespace -- including newlines and
    indentation -- is preserved verbatim. When a drop occurred between two
    survivors, they are joined with a single space (the gap is gone with the
    dropped words). The result therefore keeps the shape of untouched runs while
    collapsing the holes left by drops.
    """
    out: list[str] = []
    prev_end: int | None = None
    prev_kept = False
    for i, match in enumerate(matches):
        if i not in keep:
            prev_kept = False
            continue
        if out:
            if prev_kept and prev_end is not None:
                out.append(text[prev_end : match.start()])
            else:
                out.append(" ")
        out.append(match.group())
        prev_end = match.end()
        prev_kept = True
    return "".join(out)


def _safe_scores(scorer: Scorer, words: list[str]) -> list[float] | None:
    """Call ``scorer`` defensively; return per-word floats or ``None`` on any fault.

    A scorer is external (an ONNX session, or a caller-supplied callable), so it
    may raise, return the wrong length, or return non-numeric values. Any of these
    yields ``None`` so the caller degrades to the original text rather than
    crashing the engine on its hot path.
    """
    try:
        raw = list(scorer(words))
    except Exception:
        return None
    if len(raw) != len(words):
        return None
    try:
        return [float(s) for s in raw]
    except (TypeError, ValueError):
        return None


# --- ONNX backend (optional; loaded only when enabled and present) ----------


def _resolve_model_dir(config: MLTokenDropperConfig) -> Path:
    """Resolve the weights-bundle directory (explicit, env, or default cache).

    Order: ``config.model_dir`` -> ``NEXUS_COMPRESS_MODEL_DIR`` -> ``NEXUS_HUB_ROOT``
    (or ``~/.nexus-hub``) ``/cache/models/importance-scorer``. Mirrors the CCR
    store's cache-path convention. The directory is read-only here -- never created
    or written, because the module does not produce weights.
    """
    if config.model_dir:
        return Path(config.model_dir).expanduser()
    explicit = os.environ.get("NEXUS_COMPRESS_MODEL_DIR")
    if explicit:
        return Path(explicit).expanduser()
    hub_root = os.environ.get("NEXUS_HUB_ROOT")
    base = Path(hub_root).expanduser() if hub_root else Path.home() / ".nexus-hub"
    return base.joinpath(*_MODEL_SUBDIR)


def _word_spans(words: list[str]) -> tuple[str, list[tuple[int, int]]]:
    """Join words with single spaces and return that text plus each word's span.

    The joined string is what the tokenizer encodes; the per-word ``(start, end)``
    char spans let :func:`_pool_subword_scores` map a sub-word offset back to its
    covering word.
    """
    spans: list[tuple[int, int]] = []
    cursor = 0
    for index, word in enumerate(words):
        if index:
            cursor += 1  # the single joining space
        start = cursor
        cursor += len(word)
        spans.append((start, cursor))
    return " ".join(words), spans


def _pool_subword_scores(
    word_spans: list[tuple[int, int]],
    sub_offsets: list[tuple[int, int]],
    sub_scores: list[float],
) -> list[float]:
    """Mean-pool sub-word importance scores up to their covering word.

    Each sub-word carries a ``(start, end)`` char offset into the joined text and
    a scalar importance. A sub-word belongs to the word whose span contains its
    start offset. A word's score is the mean of its sub-words' scores; a word with
    no overlapping sub-word (e.g. a special token region, or an offset gap) scores
    ``0.0`` so it ranks lowest and is dropped first. Pure and deterministic.
    """
    totals = [0.0] * len(word_spans)
    counts = [0] * len(word_spans)
    for (sub_start, _sub_end), score in zip(sub_offsets, sub_scores):
        word_index = _word_at(word_spans, sub_start)
        if word_index is not None:
            totals[word_index] += score
            counts[word_index] += 1
    return [totals[i] / counts[i] if counts[i] else 0.0 for i in range(len(word_spans))]


def _word_at(word_spans: list[tuple[int, int]], offset: int) -> int | None:
    """Index of the word whose ``[start, end)`` span contains ``offset``, or ``None``."""
    for index, (start, end) in enumerate(word_spans):
        if start <= offset < end:
            return index
    return None


def build_onnx_scorer(config: MLTokenDropperConfig) -> tuple[Scorer | None, str | None]:
    """Build the default ONNX-backed importance scorer, or report why it can't.

    Returns ``(scorer, None)`` when the optional ``ml`` extra and the local weights
    bundle are all present, otherwise ``(None, hint)`` where ``hint`` names the
    missing piece. Every probe is guarded so a missing dependency or unreadable
    weights degrades to a hint rather than an exception -- the module makes no
    network call and never auto-downloads weights.

    The scorer encodes the joined words with the bundled tokenizer, runs the local
    ONNX session, reduces the per-sub-word logits to an importance scalar, and
    mean-pools those up to each word via :func:`_pool_subword_scores`.
    """
    try:
        import onnxruntime  # type: ignore
    except ImportError:
        return None, _install_hint("onnxruntime not installed")
    try:
        import numpy  # type: ignore
    except ImportError:
        return None, _install_hint("numpy not installed")
    try:
        from tokenizers import Tokenizer  # type: ignore
    except ImportError:
        return None, _install_hint("tokenizers not installed")

    model_dir = _resolve_model_dir(config)
    model_path = model_dir / _MODEL_FILENAME
    tokenizer_path = model_dir / _TOKENIZER_FILENAME
    if not model_path.is_file() or not tokenizer_path.is_file():
        return None, _install_hint("weights not found", model_dir)

    try:
        session = onnxruntime.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        tokenizer = Tokenizer.from_file(str(tokenizer_path))
    except Exception as exc:  # corrupt model, bad tokenizer, provider error
        return None, _install_hint(f"failed to load weights ({exc})", model_dir)

    def scorer(words: list[str]) -> list[float]:
        return _onnx_word_scores(session, tokenizer, words, numpy)

    return scorer, None


def _onnx_word_scores(session: object, tokenizer: object, words: list[str], numpy: object) -> list[float]:
    """Run the local ONNX importance model and return one score per word.

    Encodes the joined words (with offsets), feeds ``input_ids`` (and
    ``attention_mask`` when the model declares it) to the session, reduces each
    sub-word's output to an importance scalar (positive-class probability for a
    classifier, or the raw scalar for a regressor), and mean-pools to words. Any
    structural surprise propagates to :func:`_safe_scores`, which degrades.
    """
    joined, word_spans = _word_spans(words)
    encoding = tokenizer.encode(joined)  # type: ignore[attr-defined]
    ids = list(encoding.ids)
    offsets = list(encoding.offsets)

    input_ids = numpy.array([ids], dtype=numpy.int64)  # type: ignore[attr-defined]
    feeds: dict[str, object] = {}
    for spec in session.get_inputs():  # type: ignore[attr-defined]
        if spec.name == "attention_mask":
            feeds[spec.name] = numpy.ones_like(input_ids)  # type: ignore[attr-defined]
        else:  # input_ids (or the model's sole input, whatever it is named)
            feeds[spec.name] = input_ids

    outputs = session.run(None, feeds)  # type: ignore[attr-defined]
    logits = numpy.asarray(outputs[0])  # type: ignore[attr-defined]
    sub_scores = _reduce_logits_to_importance(logits, numpy)
    return _pool_subword_scores(word_spans, offsets, sub_scores)


def _reduce_logits_to_importance(logits: object, numpy: object) -> list[float]:
    """Collapse a model's per-sub-word output to one importance scalar each.

    Handles the common shapes: ``(1, seq, classes)`` -> softmax over the last
    dimension, positive (last) class probability; ``(1, seq)`` -> the raw scalar.
    Returns a plain Python list so downstream pooling is numpy-free.
    """
    array = numpy.asarray(logits, dtype=numpy.float64)  # type: ignore[attr-defined]
    array = array[0]  # drop the batch dimension
    if array.ndim == 2:  # (seq, classes): softmax, take the positive class
        shifted = array - array.max(axis=-1, keepdims=True)
        exp = numpy.exp(shifted)  # type: ignore[attr-defined]
        probs = exp / exp.sum(axis=-1, keepdims=True)
        return [float(row[-1]) for row in probs]
    return [float(value) for value in array]  # (seq,): scalar per sub-word


# --- Public entry point -----------------------------------------------------


def drop_tokens(
    text: object,
    *,
    config: MLTokenDropperConfig | None = None,
    scorer: Scorer | None = None,
) -> DropResult:
    """Drop low-importance words from free text using the optional ML scorer.

    Default-off and safe: with the default config (``enabled=False``) this is a
    pure identity that never loads a model. When enabled, it scores each word,
    keeps the top ``target_ratio`` by importance, and rebuilds readable text;
    if the backend (or the local weights) is unavailable it returns the original
    text plus an install hint rather than raising or fetching anything.

    Args:
        text: the free text to compress. A non-string is stringified.
        config: tunables; defaults to a disabled :class:`MLTokenDropperConfig`.
        scorer: an importance scorer to use instead of the default ONNX backend.
            Mainly for testing and for a consumer supplying its own model. When
            ``None`` and the dropper is enabled, :func:`build_onnx_scorer` provides
            the default (or degrades).

    Returns:
        A :class:`DropResult`. The text is unchanged on every non-running path
        (disabled, too short, or degraded), and ``degraded``/``hint`` explain a
        backend-unavailable fallback.
    """
    config = config or MLTokenDropperConfig()
    text = text if isinstance(text, str) else ("" if text is None else str(text))
    tokens_before = count_tokens(text)
    matches = list(_WORD_RE.finditer(text))
    word_count = len(matches)

    def identity(*, ran: bool, degraded: bool = False, hint: str | None = None) -> DropResult:
        return DropResult(
            text=text,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
            words_before=word_count,
            words_after=word_count,
            ran=ran,
            degraded=degraded,
            hint=hint,
        )

    # Off by default: never touch a scorer or the ONNX backend.
    if not config.enabled:
        return identity(ran=False)
    # Too short to drop safely.
    if word_count < config.min_words:
        return identity(ran=False)

    # Resolve a scorer: an injected one wins; otherwise build the ONNX default.
    hint: str | None = None
    if scorer is None:
        scorer, hint = build_onnx_scorer(config)
    if scorer is None:
        return identity(ran=False, degraded=True, hint=hint)

    words = [match.group() for match in matches]
    scores = _safe_scores(scorer, words)
    if scores is None:
        return identity(ran=False, degraded=True, hint=_install_hint("scorer failed"))

    keep = _select_keepers(scores, config.target_ratio)
    out_text = _reconstruct(text, matches, keep)
    return DropResult(
        text=out_text,
        tokens_before=tokens_before,
        tokens_after=count_tokens(out_text),
        words_before=word_count,
        words_after=len(keep),
        ran=True,
    )
