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
