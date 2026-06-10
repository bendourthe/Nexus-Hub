"""Tests for the optional, default-off ML token-dropper (Phase 6 T019/T020).

Covers the stability-gate assertions from the plan:

* the module is **off by default** (identity, never loads a model);
* when enabled with a scorer it drops low-importance words at the target ratio;
* the absent-dependency path returns the original text plus an install hint and
  never crashes;
* no network call occurs (the module never downloads weights -- it only loads
  pre-placed local ones), proven by running the enabled path with the socket
  layer poisoned;

plus the pure selection/reconstruction/pooling helpers, determinism, every
``build_onnx_scorer`` degradation branch (via stubbed ``sys.modules``, mirroring
the CacheAligner spaCy-stub tests), and a re-run of the Phase 5 accuracy gate to
confirm the lossy module did not regress the deterministic engine.

The heavy ONNX backend (``onnxruntime``/``numpy``/``tokenizers``) is never required
to run this suite: the drop logic is exercised through an injected scorer, the
numeric reduction is guarded by ``importorskip``, and the backend's guard branches
are driven with lightweight module stubs.
"""

from __future__ import annotations

import sys
import types

import pytest

from nexus_context_compressor.transforms.ml_token_dropper import (
    DropResult,
    MLTokenDropperConfig,
    _pool_subword_scores,
    _reconstruct,
    _reduce_logits_to_importance,
    _resolve_model_dir,
    _safe_scores,
    _select_keepers,
    _word_spans,
    build_onnx_scorer,
    drop_tokens,
)
from nexus_context_compressor.transforms.ml_token_dropper import (
    _WORD_RE,
)

# A long-enough sample (>= the default min_words of 20) so enabling the dropper
# actually drops rather than short-circuiting. Keywords are the high-value words a
# scorer should keep; the rest is droppable filler.
KEYWORDS = ["ERROR", "database", "connection", "timeout", "retry", "failed", "host", "port"]
FILLER = ["the", "a", "very", "really", "just", "so", "then", "and", "but", "also",
          "quite", "rather", "somewhat", "perhaps", "maybe", "indeed", "thus", "hence"]
SAMPLE_WORDS = KEYWORDS + FILLER
SAMPLE_TEXT = " ".join(SAMPLE_WORDS)


def keyword_scorer(words: list[str]) -> list[float]:
    """Deterministic scorer: keywords are important (1.0), everything else 0.0."""
    keep = {w.lower() for w in KEYWORDS}
    return [1.0 if w.lower() in keep else 0.0 for w in words]


# --- Off by default -----------------------------------------------------------


def test_disabled_by_default_is_identity():
    result = drop_tokens(SAMPLE_TEXT)
    assert result.text == SAMPLE_TEXT
    assert not result.ran
    assert not result.degraded
    assert result.hint is None
    assert result.words_before == result.words_after == len(SAMPLE_WORDS)
    assert result.tokens_after == result.tokens_before


def test_disabled_never_touches_the_scorer():
    """A disabled dropper must not call the scorer (it loads no model)."""

    def boom(_words: list[str]) -> list[float]:
        raise AssertionError("scorer must not be called when disabled")

    result = drop_tokens(SAMPLE_TEXT, scorer=boom)  # default config: disabled
    assert result.text == SAMPLE_TEXT
    assert not result.ran


def test_enabled_below_min_words_is_identity():
    short = "ERROR database connection failed"  # 4 words < default min_words (20)
    result = drop_tokens(
        short, config=MLTokenDropperConfig(enabled=True), scorer=keyword_scorer
    )
    assert result.text == short
    assert not result.ran


# --- Enabled: drops low-importance words at the target ratio -------------------


def test_enabled_drops_low_importance_words_to_target_ratio():
    config = MLTokenDropperConfig(enabled=True, target_ratio=0.4)
    result = drop_tokens(SAMPLE_TEXT, config=config, scorer=keyword_scorer)

    assert result.ran
    assert not result.degraded
    n = len(SAMPLE_WORDS)
    import math

    expected_keep = max(1, math.ceil(n * 0.4))
    assert result.words_after == expected_keep
    assert result.words_before == n
    # Every keyword (score 1.0) outranks all filler (0.0), so all keywords survive
    # whenever the keep budget covers them.
    assert expected_keep >= len(KEYWORDS)
    for keyword in KEYWORDS:
        assert keyword in result.text.split()
    # It actually compressed.
    assert result.tokens_after < result.tokens_before
    assert result.dropped_words == n - expected_keep


def test_target_ratio_one_keeps_everything_verbatim():
    config = MLTokenDropperConfig(enabled=True, target_ratio=1.0)
    result = drop_tokens(SAMPLE_TEXT, config=config, scorer=keyword_scorer)
    assert result.ran
    assert result.words_after == len(SAMPLE_WORDS)
    assert result.text == SAMPLE_TEXT  # nothing dropped -> spacing fully preserved


def test_target_ratio_zero_keeps_at_least_one_word():
    config = MLTokenDropperConfig(enabled=True, target_ratio=0.0)
    result = drop_tokens(SAMPLE_TEXT, config=config, scorer=keyword_scorer)
    assert result.ran
    assert result.words_after == 1
    # The single survivor is a keyword (highest score, earliest on ties).
    assert result.text.strip() in KEYWORDS


def test_enabled_is_deterministic():
    config = MLTokenDropperConfig(enabled=True, target_ratio=0.5)
    a = drop_tokens(SAMPLE_TEXT, config=config, scorer=keyword_scorer)
    b = drop_tokens(SAMPLE_TEXT, config=config, scorer=keyword_scorer)
    assert a.text == b.text
    assert a.words_after == b.words_after


# --- Graceful degradation (no backend, no crash, install hint) ----------------


def test_enabled_without_backend_degrades_with_hint():
    """Real default path in CI: onnxruntime absent -> identity + hint, no crash."""
    config = MLTokenDropperConfig(enabled=True)
    result = drop_tokens(SAMPLE_TEXT, config=config)  # no injected scorer
    assert result.text == SAMPLE_TEXT  # unchanged
    assert result.degraded
    assert not result.ran
    assert result.hint and "ML token-dropper unavailable" in result.hint
    assert "pip install" in result.hint


def test_failing_scorer_degrades_rather_than_raises():
    def boom(_words: list[str]) -> list[float]:
        raise RuntimeError("model exploded")

    config = MLTokenDropperConfig(enabled=True)
    result = drop_tokens(SAMPLE_TEXT, config=config, scorer=boom)
    assert result.text == SAMPLE_TEXT
    assert result.degraded
    assert result.hint is not None


def test_scorer_wrong_length_degrades():
    config = MLTokenDropperConfig(enabled=True)
    result = drop_tokens(SAMPLE_TEXT, config=config, scorer=lambda w: [1.0])
    assert result.text == SAMPLE_TEXT
    assert result.degraded


# --- No network (the module never downloads weights) --------------------------


def test_enabled_makes_no_network_call(monkeypatch):
    """Poison the socket layer; the enabled dropper must still not reach the net.

    The module only *loads* pre-placed local weights and never fetches them, so
    even with the backend nominally requested it degrades (weights absent) without
    opening a socket. Any accidental network use would raise here.
    """
    import socket

    def no_network(*_args, **_kwargs):
        raise AssertionError("ML token-dropper must make no network call")

    monkeypatch.setattr(socket, "socket", no_network)
    config = MLTokenDropperConfig(enabled=True)
    result = drop_tokens(SAMPLE_TEXT, config=config)  # default backend, absent here
    assert isinstance(result, DropResult)
    assert result.text == SAMPLE_TEXT  # degraded, no fetch attempted


# --- build_onnx_scorer: every degradation branch via sys.modules stubs --------


def test_build_scorer_onnxruntime_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", None)  # import -> ImportError
    scorer, hint = build_onnx_scorer(MLTokenDropperConfig(enabled=True))
    assert scorer is None
    assert hint and "onnxruntime not installed" in hint


def test_build_scorer_numpy_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", types.ModuleType("onnxruntime"))
    monkeypatch.setitem(sys.modules, "numpy", None)
    scorer, hint = build_onnx_scorer(MLTokenDropperConfig(enabled=True))
    assert scorer is None
    assert hint and "numpy not installed" in hint


def test_build_scorer_tokenizers_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "onnxruntime", types.ModuleType("onnxruntime"))
    monkeypatch.setitem(sys.modules, "numpy", types.ModuleType("numpy"))
    monkeypatch.setitem(sys.modules, "tokenizers", None)
    scorer, hint = build_onnx_scorer(MLTokenDropperConfig(enabled=True))
    assert scorer is None
    assert hint and "tokenizers not installed" in hint


def _stub_ml_modules(monkeypatch, *, session_factory=None):
    """Inject importable fake onnxruntime/numpy/tokenizers modules."""
    monkeypatch.setitem(sys.modules, "onnxruntime", types.ModuleType("onnxruntime"))
    monkeypatch.setitem(sys.modules, "numpy", types.ModuleType("numpy"))
    tok_mod = types.ModuleType("tokenizers")

    class _Tokenizer:
        @staticmethod
        def from_file(_path):
            return object()

    tok_mod.Tokenizer = _Tokenizer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tokenizers", tok_mod)

    ort = sys.modules["onnxruntime"]
    if session_factory is None:
        def session_factory(*_args, **_kwargs):
            return object()
    ort.InferenceSession = session_factory  # type: ignore[attr-defined]


def test_build_scorer_weights_absent(monkeypatch, tmp_path):
    _stub_ml_modules(monkeypatch)
    config = MLTokenDropperConfig(enabled=True, model_dir=str(tmp_path))
    scorer, hint = build_onnx_scorer(config)
    assert scorer is None
    assert hint and "weights not found" in hint
    assert str(tmp_path) in hint  # the hint names where it looked


def test_build_scorer_load_failure_degrades(monkeypatch, tmp_path):
    (tmp_path / "model.onnx").write_bytes(b"not a real model")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")

    def exploding_session(*_args, **_kwargs):
        raise RuntimeError("corrupt model")

    _stub_ml_modules(monkeypatch, session_factory=exploding_session)
    config = MLTokenDropperConfig(enabled=True, model_dir=str(tmp_path))
    scorer, hint = build_onnx_scorer(config)
    assert scorer is None
    assert hint and "failed to load weights" in hint


def test_build_scorer_all_present_returns_callable(monkeypatch, tmp_path):
    """With every piece present, a callable scorer is built (calling it is the
    numpy path, exercised separately under importorskip)."""
    (tmp_path / "model.onnx").write_bytes(b"stub")
    (tmp_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    _stub_ml_modules(monkeypatch)
    config = MLTokenDropperConfig(enabled=True, model_dir=str(tmp_path))
    scorer, hint = build_onnx_scorer(config)
    assert hint is None
    assert callable(scorer)


# --- Pure helpers: selection, reconstruction, pooling, spans ------------------


def test_select_keepers_top_by_score():
    keep = _select_keepers([0.1, 0.9, 0.5, 0.2], 0.5)  # keep_n = 2
    assert keep == {1, 2}


def test_select_keepers_ties_break_by_earliest_index():
    keep = _select_keepers([1.0, 1.0, 1.0], 0.34)  # keep_n = ceil(1.02) = 2
    assert keep == {0, 1}


def test_select_keepers_clamps_ratio():
    assert _select_keepers([0.1, 0.2, 0.3], 5.0) == {0, 1, 2}  # >1 -> keep all
    assert _select_keepers([0.1, 0.2, 0.3], -1.0) == {2}       # <0 -> keep best (1)


def test_select_keepers_empty():
    assert _select_keepers([], 0.5) == set()


def test_reconstruct_single_space_across_a_drop():
    text = "alpha beta gamma"
    matches = list(_WORD_RE.finditer(text))
    out = _reconstruct(text, matches, {0, 2})  # drop "beta"
    assert out == "alpha gamma"


def test_reconstruct_preserves_original_spacing_between_survivors():
    text = "alpha   beta gamma"  # 3 spaces between alpha and beta
    matches = list(_WORD_RE.finditer(text))
    out = _reconstruct(text, matches, {0, 1})  # keep alpha+beta, drop gamma
    assert out == "alpha   beta"


def test_reconstruct_preserves_newlines_between_survivors():
    text = "line1\nline2 dropme"
    matches = list(_WORD_RE.finditer(text))
    out = _reconstruct(text, matches, {0, 1})  # keep line1+line2, drop dropme
    assert out == "line1\nline2"


def test_word_spans_round_trip():
    words = ["a", "bb", "ccc"]
    joined, spans = _word_spans(words)
    assert joined == "a bb ccc"
    for word, (start, end) in zip(words, spans):
        assert joined[start:end] == word


def test_pool_subword_scores_mean_pools_to_words():
    # "hello world" -> word spans [(0,5),(6,11)].
    word_spans = [(0, 5), (6, 11)]
    sub_offsets = [(0, 2), (2, 5), (6, 11)]  # two sub-words for "hello", one for "world"
    sub_scores = [1.0, 3.0, 5.0]
    pooled = _pool_subword_scores(word_spans, sub_offsets, sub_scores)
    assert pooled == [2.0, 5.0]  # mean(1,3)=2.0 ; 5.0


def test_pool_subword_scores_word_with_no_subword_is_zero():
    word_spans = [(0, 5), (6, 11)]
    sub_offsets = [(0, 5)]  # only the first word is covered
    sub_scores = [4.0]
    pooled = _pool_subword_scores(word_spans, sub_offsets, sub_scores)
    assert pooled == [4.0, 0.0]


def test_safe_scores_good_path():
    assert _safe_scores(lambda w: [0.1 for _ in w], ["a", "b"]) == [0.1, 0.1]


def test_safe_scores_guards():
    assert _safe_scores(lambda w: (_ for _ in ()).throw(ValueError()), ["a"]) is None
    assert _safe_scores(lambda w: [1.0, 2.0], ["a"]) is None  # wrong length
    assert _safe_scores(lambda w: ["nan-ish"], ["a"]) is None  # non-numeric


# --- Numeric reduction (real numpy only; skipped when numpy is absent) --------


def test_reduce_logits_classifier_shape():
    np = pytest.importorskip("numpy")
    # (1, seq=2, classes=2): positive class is index -1.
    logits = np.array([[[2.0, 0.0], [0.0, 2.0]]])
    scores = _reduce_logits_to_importance(logits, np)
    assert len(scores) == 2
    assert scores[0] < scores[1]  # second sub-word favors the positive class


def test_reduce_logits_regressor_shape():
    np = pytest.importorskip("numpy")
    logits = np.array([[0.3, 0.9, 0.1]])  # (1, seq=3): scalar per sub-word
    scores = _reduce_logits_to_importance(logits, np)
    assert scores == [0.3, 0.9, 0.1]


# --- Misc ---------------------------------------------------------------------


def test_non_string_input_is_coerced():
    result = drop_tokens(12345)
    assert isinstance(result.text, str)
    assert not result.ran


def test_none_input_is_empty():
    result = drop_tokens(None)
    assert result.text == ""


def test_drop_result_ratio_and_dropped_words():
    r = DropResult(text="x", tokens_before=10, tokens_after=4, words_before=8, words_after=3)
    assert r.ratio == 0.4
    assert r.dropped_words == 5
    empty = DropResult(text="", tokens_before=0, tokens_after=0)
    assert empty.ratio == 1.0  # no division by zero


def test_resolve_model_dir_precedence(monkeypatch, tmp_path):
    # Explicit config wins over env.
    monkeypatch.setenv("NEXUS_COMPRESS_MODEL_DIR", str(tmp_path / "env"))
    explicit = _resolve_model_dir(MLTokenDropperConfig(model_dir=str(tmp_path / "cfg")))
    assert explicit == (tmp_path / "cfg")
    # Env wins when no explicit config.
    from_env = _resolve_model_dir(MLTokenDropperConfig())
    assert from_env == (tmp_path / "env")


def test_resolve_model_dir_default_under_hub_root(monkeypatch, tmp_path):
    monkeypatch.delenv("NEXUS_COMPRESS_MODEL_DIR", raising=False)
    monkeypatch.setenv("NEXUS_HUB_ROOT", str(tmp_path))
    resolved = _resolve_model_dir(MLTokenDropperConfig())
    assert resolved == tmp_path / "cache" / "models" / "importance-scorer"


# --- Phase 5 accuracy gate still passes with the lossy module present ----------


def test_phase5_accuracy_gate_still_passes_with_ml_module_present():
    """T020: re-run the Phase 5 gate; the lossy ML module is off the deterministic
    pipeline, so the gate (CCR round-trip + signature preservation + effectiveness)
    must still PASS -- exactly the guarantee the gate exists to protect."""
    from evals.runner import check_baseline, load_baseline, run_eval

    report = run_eval()
    failures = check_baseline(report, load_baseline())
    assert failures == [], f"Phase 5 accuracy gate regressed: {failures}"
