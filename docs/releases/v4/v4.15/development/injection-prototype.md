# Profile Injection Experiment

**Date**: 2026-10-31
**Base**: `ff69aff882f5cc825939507d326edce904ce65eb`
**Disposition**: UNEVALUATED for model benefit and cache behavior; local byte-size estimates and resolver latency are measured.
**Criterion**: [The decision record](../../../../decisions/rejected/policy/2026-10-31-model-adaptive-runtime-platform-scope.md) fixed a ceiling of 512 estimated tokens per turn before this experiment.

## Method

Five fixed public synthetic prompts were counted without model calls. The baseline is the prompt text only, not a complete host system prompt. The candidate appends one newline, a 70-byte advisory reference-data prefix, and every claim in the selected profile separated by newlines. Tokens are estimated as the ceiling of UTF-8 bytes divided by four. This estimator is reproducible but is not the model's tokenizer or a provider bill. The delta is computed from the complete before/after strings, so rounding can make it one token below the separately rounded injection size.

The plan's historical case is claude-fable-5-1, still 18 claims. The current largest profile is claude-sonnet-5-5, with 36 claims. Both cases use the same prompt set. No claim ranking or runtime filter is invented, and the full payload is not injected into any real model session.

| ID | Fixed prompt |
|---|---|
| 1 | Explain why this unit test fails and identify the smallest correction. |
| 2 | Add a keyboard-accessible settings dialog while preserving the existing layout. |
| 3 | Review this API change for authorization errors and malformed request handling. |
| 4 | Document the command-line installation flow and its expected success output. |
| 5 | Compare two local evaluation variants without making provider API calls. |

## Cost observations

| ID | Baseline estimate | Fable 5.1 with injection | Fable delta | Sonnet 5.5 with injection | Sonnet delta |
|---|---|---|---|---|---|
| 1 | 18 | 1103 | 1085 | 2530 | 2512 |
| 2 | 20 | 1106 | 1086 | 2532 | 2512 |
| 3 | 20 | 1106 | 1086 | 2532 | 2512 |
| 4 | 19 | 1105 | 1086 | 2531 | 2512 |
| 5 | 18 | 1104 | 1086 | 2530 | 2512 |

The 18-claim payload is 4,341 UTF-8 bytes, approximately 1,086 tokens. The 36-claim payload is 10,047 bytes, approximately 2,512 tokens. Both exceed the predeclared 512-token ceiling. These estimates concern a particular full-profile text shape; they do not prove that every hypothetical bounded selection would exceed it. The current schema supplies no priority field from which to justify such a selection.

The candidate Sonnet payload contains 10,047 characters, above the current Claude hook documentation's 10,000-character inline threshold. That documentation predicts file-and-preview delivery above the threshold. No installed delivery test was run, so this is not a measured delivery failure.

## Latency and benefit

The [metadata resolver experiment](detection-evidence.md) returned the real transcript model with p50 0.6470 ms and p95 1.0941 ms across 101 local calls. It did not time a provider or an installed hook.

The paired evaluation owner is skill-eval-loop, with ai-output-evaluation owning the benefit rubric. A meaningful pair would pin one model and host version, apply the same five prompts with and without the candidate, hold permissions and corpus constant, grade task correctness and policy compliance independently, and retain token, latency, cost, and cache observations. The archived v4.13 skill-trigger pilot concerns a different intervention and cannot supply this result.

No paired model run was started: zero extra provider API spend is authorized, and no safe zero-spend live benefit instrument was established. The benefit figure is therefore **UNEVALUATED**, not zero benefit and not measured no change. No fixture, reviewer judgment, or payload-size result is substituted for model quality. No runtime is recommended on this basis.

## Cache accounting

The archived v4.11.1 cache work has landed. Its distinction between observed input, cache creation, and cache reads remains binding; input size alone is not a cache-hit measurement. The current [Claude API caching reference](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) describes reuse of unchanged prefixes. Appending new context does not by itself demonstrate mutation of an existing prefix. The old comparison's assertion that per-prompt text necessarily sits before and defeats the cached prefix is unsupported by the current hook placement documentation.

Actual cache preservation is **UNEVALUATED** because no paired provider responses or cache usage counters were collected. No savings, price, or latency benefit is claimed.


## Candidate Refresh (2026-11-08)

**Integration input:** `1dc21b92db664347d18ff591e02e1e73c0d8c867`. **Current source:** 70 models and 610 claims; LF SHA-256 `8e4e39de9c2cba3d2ee1baa076705af9eedafcfcf7e14edee47aaa5a9afd70c9`. The earlier sections above are the dated 2026-10-31 snapshot and remain historical evidence.

The predeclared 512-estimated-token ceiling and the five fixed prompts above are unchanged. The current Fable 5.1 profile has 12 claims: 4,586 UTF-8 bytes joined with newlines plus the documented 70-byte advisory prefix is 4,656 payload bytes, or 1,164 estimated tokens. The original prefix wording is not retained; only its documented length is used, and that length independently reconstructs both old payload totals exactly. No exact prefix string or whole-payload-content hash is invented. The byte arithmetic is reproducible without executing profile instructions.

The ordered 36 Sonnet 5.5 claim texts are unchanged, with joined-text SHA-256 `1a58be6f349eb6ad6ea396d07ea740f0523a04a6a66fc6afd1b7233fdf86972d`. Its 10,047-byte payload and five old rows reproduce exactly. It remains the largest current complete profile by claim count and joined-text size. Current Fable joined-text SHA-256 is `7cd4c96e361ed98bde01bd47d3da60e8b33f307b048a8fe390c26f289ebe4511`.

| Prompt | Baseline | Fable after | Fable delta | Sonnet after | Sonnet delta |
|---|---|---|---|---|---|
| 1 | 18 | 1182 | 1164 | 2530 | 2512 |
| 2 | 20 | 1184 | 1164 | 2532 | 2512 |
| 3 | 20 | 1184 | 1164 | 2532 | 2512 |
| 4 | 19 | 1184 | 1165 | 2531 | 2512 |
| 5 | 18 | 1183 | 1165 | 2530 | 2512 |

The estimate remains ceiling(UTF-8 bytes / 4), with one newline after the baseline prompt. It is not a tokenizer count, provider bill, model-quality result or installed delivery measurement. Both full-profile shapes exceed the original ceiling; this does not prove every hypothetical bounded selection does. The source defines no priority field. Historical character-threshold observations remain historical because the exact prefix wording and installed delivery were not re-exercised. Benefit and cache behavior remain UNEVALUATED, with zero provider calls and no transcript reread.
