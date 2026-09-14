# Phase 2 evidence - Cache stability guidance

Renumber note, 2026-09-14: this historical cache-track evidence was authored under v4.11.0; its current plan is v4.11.1. Historical test results and phase dates remain unchanged.

Evidence for Phase 2 (T004-T006) of the [v4.11.0 adoption plan](../plans/v4.11.1-adoption-cache-and-diagram-quality.md). Records the source refresh with fetch dates and supported boundaries, the checklist and worked cases added to the cache owner, the two ownership handoffs, and the validation run. Read this to confirm D2 before Phase 3 adds the prompt-audit worksheet.

## T004 - Cache-stability checklist

### Source refresh

Every behavioural claim was checked against official documentation fetched on **2026-09-10**.

| Claim | Source | Supported boundary as documented |
|---|---|---|
| TTL options are a 5-minute default and a `ttl: "1h"` variant | [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md) | All caching-capable models |
| Lifetime is measured from request **start**, so generation time counts against it | Prompt caching | All |
| A cache read refreshes the entry at no additional cost | Prompt caching | All |
| `input_tokens` is the uncached remainder after the last breakpoint; total input is the sum of the three buckets | Prompt caching | All |
| Cache writes cost more than uncached input, and the 1-hour write costs more than the 5-minute write | Prompt caching | All; exact multipliers deliberately not pinned in the reference |
| `max_tokens: 0` prewarming is rejected with `invalid_request_error` alongside `stream: true`, `thinking.type: "enabled"`, `output_config.format`, forced `tool_choice` of `tool` or `any`, and Message Batches | Prompt caching | All |
| An `effort` or thinking change invalidates the messages cache, and on some models tools and system too | [Effort](https://platform.claude.com/docs/en/build-with-claude/effort.md), prompt caching | Model-specific; not pinned |
| A cache-preserving per-message effort change exists but is model- and beta-gated | Prompt caching, model migration reference | Model-specific; the reference instructs the reader to confirm per model rather than naming one |
| Cache diagnostics is a separate beta that reports **where** a prefix diverged | Prompt caching | Beta; the official page marks it beta without naming the header, so the reference does not name one |

### Deliberate non-pinning

Minimum cacheable prefix per model, exact price multipliers, per-message effort support, and beta header names were all read and deliberately **not** written into the reference. They change between releases, and a stale number in a distributed skill is worse than an instruction to check the current page. The reference states this explicitly and tells the reader to say so when support is unknown rather than assuming a universal fallback.

### What was added

A six-item ordered checklist covering prefix freezing, deterministic serialization, fixed tools and model, breakpoint placement at the end of the shared portion, fork prefix reuse, and the model-dependent minimum. Four short paragraphs then cover TTL timing, effort changes, optional prewarming with its costs and rejected combinations, and the distinction between measured usage and diagnostic prediction. A closing paragraph dates the claims.

The reference does not prescribe `max_tokens: 0` in any unsupported mode, does not describe an automatic prewarm loop, and requires no credential or provider request to act on.

## T005 - Ownership and worked cases

### Handoffs added

Cache accounting stays owned by `catalog/skills/ai-development/prompt-engineering/references/step-8-optimize-cost-and-latency.md`. Two one-line pointers were added where a reader is already thinking about caching, each naming the owner and saying not to restate the rule:

- `catalog/skills/ai-development/claude-agent-sdk/SKILL.md` - at the existing append-only-history guidance, which already mentions the prompt cache.
- `catalog/skills/orchestration/prompt-token-optimization/SKILL.md` - at the existing lossless-levers paragraph, which already names prompt caching as a lever.

Token and tool-loading rules were left with their existing owners. No shared model-profile schema was changed.

### Worked cases

Five synthetic cases were added as a table, each resolved through a named checklist item with an expected decision: stable prefix (healthy, change nothing), reordered tools (sort the list, not a breakpoint problem), changed top-level effort (expected invalidation, pin per route), unsupported per-message control (record as unsupported, do not retry against another model to hide the symptom), and diagnostics disagreeing with usage (trust usage, treat as unresolved and diff payloads).

The table closes by stating that none of the cases claims a measured saving, hit rate, or behavioural improvement, and that such a claim needs a qualified live evaluation outside this reference's scope.

## T006 - Testing and stabilization

### Documentary review versus API execution

This phase performed **documentary case review only**. Every case above is a synthetic walk-through of documented rules. No API request was executed, no credential was used, and no cache behaviour was measured. That boundary is stated in the reference itself so a later reader cannot mistake the table for evidence.

### Checks run

```text
$ python -m pytest tests/skills/test_cache_share_example.py -q
..................
18 passed in 0.14s

$ python scripts/validate_skills.py --bundles-only
Scanned 336 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 64 warnings)

$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 7.7s
```

The Phase 1 regression was re-run deliberately: the Phase 2 insertions sit in the same file the test extracts its snippet from, and the test asserts exactly one matching fenced block. Its continued pass proves the additions did not introduce a second cache-accounting snippet or displace the first. The 64 bundle warnings are pre-existing and none names an edited skill.

### Limitations

- No live provider call was made, so nothing here demonstrates that the checklist improves a real cache hit rate. That claim belongs to the separate qualified v4.11 evaluation path.
- Model-specific values that were read but not pinned are recorded above rather than in the distributed reference. A reader wanting a current number must fetch the official page; this is intentional, not an omission.

### CI impact

No new command, dependency, environment variable, test path, or artifact. Documentation and bundle validation only, already covered by the existing `hygiene` and `catalog-parse` groups. Nothing is carried forward to the Phase 6 reconciliation.
