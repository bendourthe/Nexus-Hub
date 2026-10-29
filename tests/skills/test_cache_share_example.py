"""Regression tests for the distributed cache-accounting example.

The example in the prompt-engineering cost reference once divided
``cache_read_input_tokens`` by ``usage.input_tokens``. Because ``input_tokens``
counts only the UNCACHED portion of the input, that expression reported 900%
for a request that read 900 cached and 100 uncached tokens -- the metric looked
best exactly when it was most wrong.

These tests execute the ACTUAL fenced snippet from the shipped Markdown rather
than a copy of the formula, so reverting the documentation fails the suite.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REFERENCE = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "ai-development"
    / "prompt-engineering"
    / "references"
    / "step-8-optimize-cost-and-latency.md"
)

FENCE = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


def _load_snippet() -> dict[str, Any]:
    """Execute the fenced block that defines the cache-accounting helpers.

    The block also defines ``cached_system_prompt_call``, which references a
    module-level ``client``. Defining the function does not call it, so no
    network access or SDK install is required.
    """
    text = REFERENCE.read_text(encoding="utf-8")
    blocks = [b for b in FENCE.findall(text) if "def cache_read_share" in b]
    assert len(blocks) == 1, (
        f"expected exactly one cache-accounting snippet in {REFERENCE.name}, "
        f"found {len(blocks)}"
    )
    namespace: dict[str, Any] = {}
    exec(compile(blocks[0], str(REFERENCE), "exec"), namespace)  # noqa: S102
    return namespace


SNIPPET = _load_snippet()
cache_read_share = SNIPPET["cache_read_share"]
describe_cache_share = SNIPPET["describe_cache_share"]


def usage(
    uncached: Any, cache_read: Any = 0, cache_created: Any = 0
) -> SimpleNamespace:
    """Build a synthetic usage object shaped like the Anthropic response field."""
    return SimpleNamespace(
        input_tokens=uncached,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_created,
    )


@pytest.mark.parametrize(
    ("uncached", "cache_read", "cache_created", "expected"),
    [
        # The four D1 cases from the v4.10.0 plan.
        (100, 900, 0, 0.90),
        (0, 900, 0, 1.00),
        (100, 0, 0, 0.00),
        (100, 900, 200, 0.75),
    ],
)
def test_documented_cases_report_the_token_share(
    uncached: int, cache_read: int, cache_created: int, expected: float
) -> None:
    share = cache_read_share(usage(uncached, cache_read, cache_created))
    assert share == pytest.approx(expected)


def test_the_regressed_case_is_no_longer_over_one_hundred_percent() -> None:
    # The exact defect: 900 read over 100 uncached must not report 9.0 (900%).
    assert cache_read_share(usage(100, 900)) <= 1.0


def test_all_zero_request_is_unknown_not_zero_percent() -> None:
    # No input at all is not evidence that caching is ineffective.
    assert cache_read_share(usage(0, 0, 0)) is None


def test_missing_telemetry_object_is_unknown() -> None:
    assert cache_read_share(None) is None


def test_missing_required_input_field_is_unknown() -> None:
    assert cache_read_share(SimpleNamespace(cache_read_input_tokens=900)) is None


def test_absent_cache_fields_default_to_zero() -> None:
    # A supported no-cache response omits the optional buckets; that is a real
    # 0% share, distinct from unknown telemetry.
    assert cache_read_share(SimpleNamespace(input_tokens=100)) == 0.0


@pytest.mark.parametrize(
    "bad",
    [-1, 0.5, float("nan"), float("inf"), "900", True],
    ids=["negative", "fractional", "nan", "inf", "string", "bool"],
)
def test_untrustworthy_counts_report_unknown(bad: Any) -> None:
    assert cache_read_share(usage(100, bad)) is None


def test_description_never_claims_money_saved() -> None:
    rendered = describe_cache_share(usage(100, 900))
    assert "90%" in rendered
    assert "input tokens" in rendered
    for forbidden in ("saved", "saving", "cost", "$"):
        assert forbidden not in rendered.lower()


def test_description_reports_unknown_for_empty_input() -> None:
    assert "unknown" in describe_cache_share(usage(0, 0, 0))


def openai_usage(input_tokens: Any, cached: Any = None, writes: Any = 0, *, details: bool = True) -> SimpleNamespace:
    """A usage object shaped like OpenAI's: `input_tokens` is the total, details hold its subsets."""
    if not details:
        return SimpleNamespace(input_tokens=input_tokens)
    return SimpleNamespace(input_tokens=input_tokens,
                           input_tokens_details={"cached_tokens": cached, "cache_write_tokens": writes})


@pytest.mark.parametrize(
    ("value", "kwargs", "expected"),
    [
        # The six v4.14.2 Phase 3 fixtures.
        pytest.param(usage(100, 900, 0), {}, 0.90, id="anthropic-default-provider"),
        pytest.param(openai_usage(1000, 900), {"provider": "openai"}, 0.90, id="openai-full"),
        pytest.param(openai_usage(12000, 4000, 7000), {"provider": "openai"}, 4000 / 12000, id="openai-reads-and-writes"),
        pytest.param(openai_usage(0, 0), {"provider": "openai"}, None, id="openai-zero-input"),
        pytest.param(openai_usage(1000, details=False), {"provider": "openai"}, None, id="openai-no-details"),
        pytest.param(openai_usage("1000", 900), {"provider": "openai"}, None, id="malformed"),
        pytest.param(usage(100, 900, 0), {"provider": "other"}, None, id="unknown-provider"),
    ],
)
def test_two_provider_fixtures(value: Any, kwargs: dict, expected: float | None) -> None:
    share = cache_read_share(value, **kwargs)
    assert share == (None if expected is None else pytest.approx(expected))
    rendered = describe_cache_share(value, **kwargs)
    if expected is None:
        # Unknown telemetry never reads as a 0% cache rate.
        assert "unknown" in rendered and "0%" not in rendered
    else:
        assert f"{expected:.0%}" in rendered


def test_openai_reads_beyond_the_total_are_malformed() -> None:
    assert cache_read_share(openai_usage(100, 900), provider="openai") is None


def test_openai_reads_plus_writes_beyond_the_total_are_malformed() -> None:
    assert cache_read_share(openai_usage(10, 8, 8), provider="openai") is None
    assert cache_read_share(openai_usage(12000, 4000, 7000), provider="openai") == pytest.approx(4000 / 12000)


def test_an_unrepresentable_count_reports_unknown_not_an_exception() -> None:
    assert cache_read_share(openai_usage(10**400, 900), provider="openai") is None


def test_anthropic_dict_shaped_usage_is_read() -> None:
    # A usage dumped to a dict (for example with model_dump()) reads like the object.
    as_dict = {"input_tokens": 100, "cache_read_input_tokens": 900, "cache_creation_input_tokens": 0}
    assert cache_read_share(as_dict) == pytest.approx(0.90)


def test_openai_usage_with_the_default_provider_is_unknown_not_zero() -> None:
    # Its input_tokens is the total; read as Anthropic's uncached count it would report a confident 0%.
    assert cache_read_share(openai_usage(1000, 900)) is None
    assert cache_read_share({"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 900}}) is None


def test_openai_attribute_shaped_details_are_read() -> None:
    usage_obj = SimpleNamespace(input_tokens=1000, input_tokens_details=SimpleNamespace(cached_tokens=250))
    assert cache_read_share(usage_obj, provider="openai") == pytest.approx(0.25)


def test_provider_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        cache_read_share(usage(100, 900), "openai")  # type: ignore[misc]


def test_reference_does_not_reintroduce_the_uncached_denominator() -> None:
    # Guard the specific regression shape, not the prose around it.
    text = REFERENCE.read_text(encoding="utf-8")
    assert "total_input = usage.input_tokens" not in text
