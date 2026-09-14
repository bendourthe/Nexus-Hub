### Step 8: Optimize Cost and Latency

**Token Reduction Techniques**:

| Technique | Token Savings | Impact on Quality | When to Use |
|-----------|--------------|-------------------|-------------|
| **Concise instructions** | 20-40% | None if well-written | Always |
| **Remove redundancy** | 10-30% | None | Always |
| **Abbreviate examples** | 15-25% | Minor | Large few-shot sets |
| **Prompt caching** | 0% (cost savings) | None | Repeated system prompts |
| **Model routing** | N/A | Variable | Mixed-complexity workloads |

**Prompt Caching with Anthropic**:

Anthropic reports input tokens in three disjoint buckets, and `input_tokens` counts only the **uncached** portion. It is therefore never the denominator for a cache-share figure: dividing cache reads by it reports 900% for a request that read 900 cached and 100 uncached tokens. Sum all three buckets instead.

Cache share is a **token proportion**, not money saved and not the percentage of requests that hit cache. Cached input is billed at a reduced rate rather than free, and cache writes cost more than uncached input, so a share figure never converts directly into a saving.

```python
from math import isfinite
from typing import Any


def read_token_bucket(usage: Any, field: str, *, required: bool = False) -> int:
    """Read one non-negative whole-token input bucket from a usage object.

    Raises ValueError or TypeError when the field cannot be counted, so the
    caller can report "unknown" rather than a misleading number.
    """
    value = getattr(usage, field, None)
    if value is None:
        if required:
            raise ValueError(f"usage.{field} is required")
        # Documented default: the response carried no cache activity.
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"usage.{field} is not numeric")
    if not isfinite(value) or value < 0 or value != int(value):
        raise ValueError(f"usage.{field} is not a whole token count")
    return int(value)


def cache_read_share(usage: Any) -> float | None:
    """Fraction of input tokens served from cache, or None when unknowable.

    Returns a fraction in [0.0, 1.0]. Returns None when the telemetry object is
    missing or malformed, or when the request had no input tokens at all. None
    means "unknown"; it never means "no caching", and an all-zero request is
    not evidence that caching is ineffective.
    """
    if usage is None:
        return None
    try:
        uncached = read_token_bucket(usage, "input_tokens", required=True)
        cache_read = read_token_bucket(usage, "cache_read_input_tokens")
        cache_created = read_token_bucket(usage, "cache_creation_input_tokens")
    except (TypeError, ValueError):
        return None

    total_input = uncached + cache_read + cache_created
    if total_input == 0:
        return None  # No input, not a 0% cache rate.
    return cache_read / total_input


def describe_cache_share(usage: Any) -> str:
    """Render the share for a log line without asserting a cost saving."""
    share = cache_read_share(usage)
    if share is None:
        return "Cache share: unknown (missing, malformed, or empty input telemetry)"
    return f"Cache share: {share:.0%} of input tokens were read from cache"


def cached_system_prompt_call(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Use Anthropic's prompt caching for repeated system prompts."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    print(describe_cache_share(response.usage))
    return extract_text(response.content)
```

Worked outcomes for the three buckets, written as uncached / cache-read / cache-created:

| Uncached | Cache read | Cache created | Cache share | Reading |
|---|---|---|---|---|
| 100 | 900 | 0 | 90% | Warm prefix; most input came from cache. |
| 0 | 900 | 0 | 100% | Every input token was a cache read. |
| 100 | 0 | 0 | 0% | Cold or uncacheable request. |
| 100 | 900 | 200 | 75% | Warm read alongside a new cache write. |
| 0 | 0 | 0 | unknown | No input at all, so nothing to attribute. |

Missing telemetry, a negative or fractional count, and a non-numeric or non-finite value all report unknown. A number that cannot be trusted is worse than an absent one, because it survives into a cost review unchallenged.

**Cache stability checklist**:

Caching is a prefix match: any byte change anywhere in the prefix invalidates everything after it. Render order is `tools`, then `system`, then `messages`. Work the checklist in order; the first four items decide more than breakpoint placement does.

1. **Freeze the front of the prefix.** No `datetime.now()`, request ID, session ID, or conditional section in the system prompt. Anything dynamic moves after the last breakpoint.
2. **Serialize deterministically.** Sort JSON keys and tool lists by name. An unsorted `dict` or an iterated `set` changes the bytes without changing the meaning.
3. **Hold tools and model fixed for the conversation.** Tools render at position 0, and caches are model-scoped, so adding, removing, or reordering a tool, or switching model, rebuilds everything.
4. **Place the breakpoint at the end of the shared portion**, not the end of the whole prompt. A breakpoint after per-request content writes a new entry every time and never reads one.
5. **Make forks reuse the parent's exact prefix.** A summarizer or sub-agent that rebuilds `system`, `tools`, or `model` misses the parent's cache entirely.
6. **Check the minimum cacheable prefix for the model in use.** A prefix below it silently does not cache, with no error.

**TTL timing**: the default entry lives 5 minutes and the `ttl: "1h"` variant an hour, measured from the **start** of the request that writes or reads it, so generation time counts against the window. A read refreshes the timer at no extra cost, so requests sharing a prefix and starting less than 5 minutes apart keep the default entry warm indefinitely. Writes cost more than uncached input, and the 1-hour write costs more than the 5-minute one, so the longer TTL pays off only across gaps the default cannot bridge.

**Effort changes**: a change to top-level `effort` or thinking configuration invalidates the messages cache on every model, and on some models the tools and system caches as well. Pin them per route rather than varying per request. A per-message effort change that preserves the cache exists, but it is model-gated and beta-gated; confirm support for the exact model in use before relying on it, and treat an unsupported model's rejection as the expected outcome rather than a bug to work around.

**Prewarming is optional and has costs**: a `max_tokens: 0` request runs prefill and writes the cache without generating output. It earns its write charge only when first-request latency is user-visible, the shared prefix is large, and there is a quiet moment before traffic. Skip it when traffic is continuous, when the prefix is small or per-request, or when many distinct prefixes would be warmed speculatively. The request is rejected with `invalid_request_error` when combined with `stream: true`, `thinking.type: "enabled"`, structured outputs (`output_config.format`), a forced `tool_choice` of `{"type": "tool"}` or `{"type": "any"}`, or a Message Batches request, so do not prescribe it in those modes. Put the breakpoint on the last block shared with the real request, never on the placeholder message. Nothing here should be automated into a background warm loop, and none of it requires a credential or a provider request to reason about.

**Measured usage is not a prediction**: `usage.cache_read_input_tokens` is what the request actually read from cache. Cache diagnostics is a separate beta feature that compares consecutive requests and reports **where** the prefix diverged; it explains a miss, it does not measure a hit. When the two disagree, the usage fields are the ground truth and the diagnostic is the hypothesis. Verify usage after every change to prompt assembly, not only at setup: the costly failure mode is silent, because requests keep succeeding and only the bill moves.

**Currency of these claims**: the caching mechanics, TTL semantics, usage-field definitions, and prewarming restrictions above were verified on 2026-09-10 against the official [prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md) and [effort](https://platform.claude.com/docs/en/build-with-claude/effort.md) documentation. Model-specific minimums, per-message effort support, and beta header names change between releases and are deliberately not pinned here; read the current official page for the model you are targeting. Where support for a given model is unknown, say so rather than assuming a universal fallback.

**Worked cases**: each resolves through the checklist above. They are synthetic illustrations of the documented rules, not measurements of cache effectiveness on any real workload.

| Case | Observation | Checklist item | Expected decision |
|---|---|---|---|
| Stable prefix | A frozen system prompt is sent ahead of a varying question; `cache_read_input_tokens` grows across requests while `input_tokens` stays small. | 1, 4 | Healthy. The breakpoint sits at the end of the shared portion, so reads cover the prefix and only the tail is billed at full price. Change nothing. |
| Reordered tools | The tool list is built from a `set`, so its order differs between runs. Reads collapse to zero even though the system prompt is untouched. | 2, 3 | Not a breakpoint problem. Tools render at position 0, so a reordering invalidates everything. Sort the tool list by name; do not add breakpoints. |
| Changed top-level effort | A route raises top-level `effort` mid-conversation and the next request shows a large `cache_creation_input_tokens` with no read. | Effort changes | Expected, not a defect. An effort change invalidates the messages cache on every model. Pin effort per route instead of varying it per request. |
| Unsupported per-message control | The same route tries the cache-preserving per-message effort message and the request is rejected. | Effort changes | The model or beta is not supported. Record it as unsupported for that model and fall back to a pinned per-route effort. Do not assume a universal fallback exists, and do not retry against a different model to make the symptom disappear. |
| Diagnostics disagrees with usage | Cache diagnostics reports the prefix as unchanged, but `cache_read_input_tokens` is zero. | Measured usage is not a prediction | Trust the usage fields. Diagnostics explains where a prefix diverged; it does not measure what was read. Treat the disagreement as an unresolved finding and diff the rendered payloads rather than reporting a hit that did not occur. |

None of these cases claims a measured saving, a hit rate, or an improvement in agent behaviour. Any such claim needs a qualified live evaluation, which is out of scope for this reference.

**Model Routing by Complexity**:

```python
def route_to_model(task_description: str, input_length: int) -> str:
    """Select the appropriate model based on task complexity."""
    # Simple heuristics for model routing
    complex_indicators = [
        "analyze", "compare", "evaluate", "design", "architect",
        "debug", "optimize", "refactor",
    ]

    is_complex = any(ind in task_description.lower() for ind in complex_indicators)
    is_long = input_length > 5000

    if is_complex or is_long:
        return "claude-sonnet-4-20250514"   # Higher capability
    else:
        return "claude-haiku-4-20250514"    # Lower cost, faster
```
