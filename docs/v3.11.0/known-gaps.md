# Known Gaps -- v3.11.0

**Status**: v3.11.0 is in progress on `develop`, pending release. This file currently tracks the `adoption-pxpipe` cycle ([docs/v3.11.0/plans/adoption-pxpipe.md](plans/adoption-pxpipe.md)), which operationalizes the skill-native subset of [comparison-pxpipe.md](comparison-pxpipe.md). Phase 1 (the `prompt-token-optimization` optical / image-token compression doctrine) and Phase 2 (the `model-routing` model-specificity note, the `drop-outright` matrix row, the CHANGELOG entry, and this file) are complete. Other v3.11.0 adoption cycles may append their own items below.

**Last updated**: 2026-07-07 (v3.11.0 adoption-pxpipe Phase 2)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.11.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

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
| DF-v311-pxpipe-C3 | DF | adoption-pxpipe Phase 2.2 (C3 decline) | The optical / image-token compression proxy mechanism (an always-on transport-layer reverse-proxy that lossily re-renders bulky static context as images in the API critical path) was deliberately declined this cycle and recorded as `drop-outright` in [docs/policy/mcp-reverse-engineering-matrix.md](../policy/mcp-reverse-engineering-matrix.md). It is declined under the MCP Registry Policy (a lossy, credential-handling, request-mutating runtime in the API path), on correctness grounds (its errors are silent confabulations, 0% hex recall on strong models), and on economics grounds (the savings invert on the strong-model high-resolution image tier). This is a durable decline, not an unfinished task. | Keep declined. Revisit ONLY if one of two conditions changes: (1) Anthropic changes image-token billing so that legible renders become cheaper than the equivalent text on strong models (removing the economics disqualifier), or (2) a lossless-fidelity variant becomes proven -- specifically a verified anchor sidecar that passes byte-exact strings (IDs, hashes, secrets) as text beside the image with a runtime read-back check (removing the correctness disqualifier). Absent both, do not re-surface as a gap. | Low (the mechanism is architecturally out of scope for a local-first, correctness-first catalog; the adoptable doctrine was already imported as the skill-native items). |

## Notes

- **Declines are durable, not gaps.** The optical / image-token compression proxy mechanism is recorded as an authoritative `drop-outright` row in [docs/policy/mcp-reverse-engineering-matrix.md](../policy/mcp-reverse-engineering-matrix.md), referencing [comparison-pxpipe.md](comparison-pxpipe.md), so a future comparison recognizes it as already-adjudicated rather than re-surfacing it as a fresh gap. The revisit trigger above states the exact conditions under which the decision would be reopened.
- **The adoptable substance shipped.** The skill-native doctrine (the `prompt-token-optimization` optical-compression subsection with the silent-confabulation caution and the byte-exact-stays-text rule, plus the `model-routing` model-specificity note) was imported this cycle. No new outbound call, dependency, credential, or runtime was introduced.

## Resolved

_None resolved in v3.11.0 yet._
