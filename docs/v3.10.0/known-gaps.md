# Known Gaps -- v3.10.0

**Status**: v3.10.0 (the ruflo adoption cycle) is in progress on `develop`. The `adoption-ruflo` plan ([docs/v3.10.0/plans/adoption-ruflo.md](plans/adoption-ruflo.md)) operationalizes the reverse-engineerable subset of [comparison-ruflo.md](comparison-ruflo.md). Phase 1 (the `egress-redaction` skill) and Phase 2 (the `prompt-injection-defense` skill) are complete; Phase 3 (the `competitive-generation` iterative-rounds enrichment plus the A6 decision recorded here) is in progress. Phases 4-6 (the `nexus-hub verify` supply-chain command, the agent-setup grade + regression diff, and the advisory worker-check hooks + consolidation) are pending.

**Last updated**: 2026-06-30 (v3.10.0 adoption-ruflo Phase 3)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.10.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 1 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 0 | 0 |
| QG | 0 | 0 |
| **Total** | **1** | **0** |

## Open Items

| ID | Category | Source | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|
| DF-v310-ruflo-A6 | DF | adoption-ruflo Phase 3.2 (A6) | The optional, low-value quality-gate naming note was considered and skipped. A6 would add a short note (to `plan-before-code` or `quality-gate-definitions`) observing that a named, phased guided-development methodology with per-phase quality gates is functionally equivalent to Nexus-Hub's existing `/plan` -> `/implement` -> `/spec` flow plus `quality-gate-definitions`, so a user who arrives expecting that named methodology is already served. The comparison rated it low value because that function is already fully delivered and the note risks duplicating shipped material. | Add the short generic note only if users repeatedly arrive expecting the named methodology and do not find it. If built: add a 4-8 line note to the chosen planning skill mapping the named phases onto the existing flow, describe it as "a named phased guided-development methodology" with no branded token, and cross-link `quality-gate-definitions`. | Low (the phased-guided-development-with-gates function is already delivered by `/plan`, `/implement`, `/spec`, and `quality-gate-definitions`). |

## Notes

- **A6 decision (adoption-ruflo Phase 3.2): skipped, recorded here.** The plan's default-skip recommendation was followed. The phased-guided-development-with-gates function that A6 would document is already covered by the existing `/plan` -> `/implement` -> `/spec` flow and `quality-gate-definitions`, so adding the note now would duplicate shipped material without adding capability, and it risks contradicting the existing planning guidance. Recorded as DF-v310-ruflo-A6 above so a future cycle picks it up if concrete demand for the named methodology appears.
- **Declines are durable, not gaps.** The six v3.10.0 runtime drops (the runtime meta-harness + MCP-daemon model, the GPU vector DB, the multi-provider router runtime, cross-machine federation, the hosted web UIs, and the WASM sandbox runtime) are recorded as authoritative rows in [docs/policy/mcp-reverse-engineering-matrix.md](../policy/mcp-reverse-engineering-matrix.md) in Phase 6, referencing [comparison-ruflo.md](comparison-ruflo.md), so a future comparison recognizes them as already-adjudicated rather than re-surfacing them as fresh gaps.

## Resolved

_None resolved in v3.10.0 yet._
