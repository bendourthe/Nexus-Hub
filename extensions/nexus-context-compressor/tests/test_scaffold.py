"""Skeleton tests for the Phase 1 package scaffold.

These cover the no-op pipeline, the ``CompressResult`` metrics, and the
offline-safe token counter. The deterministic-strategy tests (SmartCrusher,
CCR round-trip) arrive with their phases.
"""

from __future__ import annotations

import nexus_context_compressor as ncc
from nexus_context_compressor import tokens
from nexus_context_compressor.types import CompressResult


def test_compress_is_identity_in_phase_1():
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "hi there, how can I help?"},
    ]
    result = ncc.compress(messages)
    assert isinstance(result, CompressResult)
    assert result.messages == messages
    assert result.transforms_applied == []
    assert result.tokens_after == result.tokens_before


def test_ratio_is_identity_for_noop():
    result = ncc.compress(["one fish", "two fish"])
    assert result.ratio == 1.0
    assert result.reduction == 0.0


def test_empty_input_does_not_divide_by_zero():
    result = ncc.compress([])
    assert result.tokens_before == 0
    assert result.tokens_after == 0
    assert result.ratio == 1.0


def test_compress_accepts_plain_strings_and_dicts():
    mixed = ["a plain string", {"role": "user", "content": "a mapping"}]
    result = ncc.compress(mixed)
    assert result.messages == mixed
    assert result.tokens_before > 0


def test_token_counter_is_deterministic():
    text = "the quick brown fox jumps over the lazy dog"
    assert tokens.count_tokens(text) == tokens.count_tokens(text)
    assert tokens.count_tokens("") == 0


def test_fallback_estimate_is_positive_and_stable():
    # Exercise the stdlib estimator directly so the test is meaningful even
    # when tiktoken is installed.
    est = tokens._estimate_tokens("hello, world! 123")
    assert est == tokens._estimate_tokens("hello, world! 123")
    assert est > 0
