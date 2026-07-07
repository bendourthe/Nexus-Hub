# Known Gaps -- v3.11.0

**Status**: v3.11.0 is in progress on `develop`, pending release. This file tracks two v3.11.0 adoption cycles. The `adoption-pxpipe` cycle ([docs/v3.11.0/plans/adoption-pxpipe.md](plans/adoption-pxpipe.md)) operationalizes the skill-native subset of [comparison-pxpipe.md](comparison-pxpipe.md): Phase 1 (the `prompt-token-optimization` optical / image-token compression doctrine) and Phase 2 (the `model-routing` model-specificity note, the `drop-outright` matrix row, the CHANGELOG entry, and this file) are complete. The `adoption-davidondrej-skills` cycle ([docs/v3.11.0/plans/adoption-davidondrej-skills.md](plans/adoption-davidondrej-skills.md), operationalizing [comparison-davidondrej-skills.md](comparison-davidondrej-skills.md)) shipped three adopted items (Phases 1-3) and records its declines below (Phase 4). Other v3.11.0 adoption cycles may append their own items below.

**Last updated**: 2026-07-07 (v3.11.0 adoption-davidondrej-skills Phase 4)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.11.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 6 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 0 | 0 |
| QG | 0 | 0 |
| **Total** | **6** | **0** |

## Open Items

| ID | Category | Source | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|
| DF-v311-pxpipe-C3 | DF | adoption-pxpipe Phase 2.2 (C3 decline) | The optical / image-token compression proxy mechanism (an always-on transport-layer reverse-proxy that lossily re-renders bulky static context as images in the API critical path) was deliberately declined this cycle and recorded as `drop-outright` in [docs/policy/mcp-reverse-engineering-matrix.md](../policy/mcp-reverse-engineering-matrix.md). It is declined under the MCP Registry Policy (a lossy, credential-handling, request-mutating runtime in the API path), on correctness grounds (its errors are silent confabulations, 0% hex recall on strong models), and on economics grounds (the savings invert on the strong-model high-resolution image tier). This is a durable decline, not an unfinished task. | Keep declined. Revisit ONLY if one of two conditions changes: (1) Anthropic changes image-token billing so that legible renders become cheaper than the equivalent text on strong models (removing the economics disqualifier), or (2) a lossless-fidelity variant becomes proven -- specifically a verified anchor sidecar that passes byte-exact strings (IDs, hashes, secrets) as text beside the image with a runtime read-back check (removing the correctness disqualifier). Absent both, do not re-surface as a gap. | Low (the mechanism is architecturally out of scope for a local-first, correctness-first catalog; the adoptable doctrine was already imported as the skill-native items). |
| DF-v311-ddj-paid-api | DF | adoption-davidondrej-skills Phase 4.1 | A paid scraping-and-email API skill and a paid deep-research API skill declined under the MCP Registry Policy hard-no on scraping-as-service and research-as-service (each sends query text or target URLs to a paid third party and requires a new commercial account). The research workflow is already delivered by `/research` and the `deep-research` harness with no paid dependency; the local transcript capability shipped separately as the `youtube-transcript` skill (local `yt-dlp` path only). Durable decline, not a task. | Keep declined. Revisit only if a path exists with no third-party processor and no new credential. | Low |
| DF-v311-ddj-benchmark-router | DF | adoption-davidondrej-skills Phase 4.1 | A model-benchmarking skill bound to a specific third-party model router declined as vendor-bound and niche (it sends prompts to a third party). Covered in spirit by `ai-output-evaluation` and `skill-eval-loop`. Durable decline. | Keep declined. | Low |
| DF-v311-ddj-prompt-rewrite | DF | adoption-davidondrej-skills Phase 4.1 | A prompt-rewriting skill whose purpose is to weaken server-side safety classifiers on dual-use topics declined on policy and ethics grounds; it is contrary to Nexus-Hub's defensive security posture. Durable decline. | Keep declined; do not re-surface. | Low |
| DF-v311-ddj-tool-bound | DF | adoption-davidondrej-skills Phase 4.1 | A terminal-multiplexer integration skill (with a render-workaround companion), two personal-agent skills, and a vendor goal-loop feature document declined because they target external stacks Nexus-Hub does not support; the transferable agent-loop pattern already exists in `loop-engineering`. Durable decline. | Keep declined. | Low |
| DF-v311-ddj-deferred | DF | adoption-davidondrej-skills Phase 4.1 | A guided setup walkthrough, a folder-scoped context-file helper, and a read-all-ADRs loader deferred as low-value skill-native interaction patterns. | Optional future items; adopt only on explicit request. | Low |

## Notes

- **Declines are durable, not gaps.** The optical / image-token compression proxy mechanism is recorded as an authoritative `drop-outright` row in [docs/policy/mcp-reverse-engineering-matrix.md](../policy/mcp-reverse-engineering-matrix.md), referencing [comparison-pxpipe.md](comparison-pxpipe.md), so a future comparison recognizes it as already-adjudicated rather than re-surfacing it as a fresh gap. The revisit trigger above states the exact conditions under which the decision would be reopened.
- **The adoptable substance shipped.** The skill-native doctrine (the `prompt-token-optimization` optical-compression subsection with the silent-confabulation caution and the byte-exact-stays-text rule, plus the `model-routing` model-specificity note) was imported this cycle. No new outbound call, dependency, credential, or runtime was introduced.
- **The adoption-davidondrej-skills declines are durable, policy-grounded, not pending work.** The paid scraping and research API skills, the vendor-bound benchmark skill, the safety-classifier-weakening prompt-rewriting skill, and the tool-bound set are all declined outright under the MCP Registry Policy (scraping-as-service and research-as-service hard-no, defensive-posture, and unsupported-stack grounds respectively), recorded so a future comparison recognizes them as already-adjudicated rather than re-surfacing them as fresh gaps. See [comparison-davidondrej-skills.md](comparison-davidondrej-skills.md).
- **The adoption-davidondrej-skills adoptable substance shipped.** The three recommended items were adopted this cycle: the `prompt-engineering` research-brief authoring technique (Phase 1, referenced from `/research`), the opt-in grill-me interactive mode in `idea-refine` (Phase 2), and the new `youtube-transcript` research skill via local `yt-dlp` (Phase 3, catalog 259 -> 260). No new outbound call, dependency, or credential was introduced (the `yt-dlp` invocation is a user-run local tool, lazy-checked, not a Nexus-Hub dependency).

## Resolved

_None resolved in v3.11.0 yet._
