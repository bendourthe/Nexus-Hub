# Known Gaps -- v3.10.0

**Status**: v3.10.0 (the ruflo adoption cycle) is complete on `develop`, pending release. The `adoption-ruflo` plan ([docs/releases/v3/v3.10/plans/adoption-ruflo.md](plans/adoption-ruflo.md)) operationalizes the reverse-engineerable subset of [comparison-ruflo.md](comparison-ruflo.md). Phase 1 (the `egress-redaction` skill), Phase 2 (the `prompt-injection-defense` skill), Phase 3 (the `competitive-generation` iterative-rounds enrichment plus the A6 decision recorded here), Phase 4 (the `nexus-hub verify` supply-chain command + release manifest), Phase 5 (the agent-setup grade + cross-snapshot regression diff in `harness_audit.py`, surfaced through `skill-stocktake`), and Phase 6 (two advisory worker-check hooks, the six runtime drops recorded in the reverse-engineering matrix, and the count/CHANGELOG/known-gaps consolidation) are all complete.

**Last updated**: 2026-06-30 (v3.10.0 adoption-ruflo Phase 6)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.10.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 3 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 0 | 0 |
| QG | 0 | 0 |
| **Total** | **3** | **0** |

## Open Items

| ID | Category | Source | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|
| DF-v310-ruflo-A6 | DF | adoption-ruflo Phase 3.2 (A6) | The optional, low-value quality-gate naming note was considered and skipped. A6 would add a short note (to `plan-before-code` or `quality-gate-definitions`) observing that a named, phased guided-development methodology with per-phase quality gates is functionally equivalent to Nexus-Hub's existing `/plan` -> `/implement` -> `/spec` flow plus `quality-gate-definitions`, so a user who arrives expecting that named methodology is already served. The comparison rated it low value because that function is already fully delivered and the note risks duplicating shipped material. | Add the short generic note only if users repeatedly arrive expecting the named methodology and do not find it. If built: add a 4-8 line note to the chosen planning skill mapping the named phases onto the existing flow, describe it as "a named phased guided-development methodology" with no branded token, and cross-link `quality-gate-definitions`. | Low (the phased-guided-development-with-gates function is already delivered by `/plan`, `/implement`, `/spec`, and `quality-gate-definitions`). |
| DF-v310-ruflo-P4-extensions | DF | adoption-ruflo Phase 4.1 (manifest scope) | The `nexus-hub verify` supply-chain manifest covers the core distributed catalog subtrees (`catalog/`, `templates/`, `scripts/`, `data/`) but intentionally excludes `extensions/` (the internal MCP-server sources: `nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`, `nexus-skill-scanner`, `nexus-context-compressor`). Those are pip-installed into a venv at install time rather than copied verbatim, and including their source trees would pull in build output / venv churn that destabilizes the deterministic manifest. So a tampered MCP-server source file is not currently caught by `verify`. | Extend `COVERED_ROOTS` in `scripts/generate_manifest.py` to include `extensions/` with robust exclusions (`node_modules`, `out`, `dist`, `*.vsix`, `.venv`, `__pycache__`, `*.egg-info`) if MCP-server source integrity coverage is wanted; re-confirm determinism and that `verify` stays clean on a fresh install. | Low (the MCP-server install path has its own pip integrity, and the highest-value tamper surface -- skills, commands, hooks, scripts -- is already covered). |
| DF-v310-ruflo-A10-rest | DF | adoption-ruflo Phase 6.1 (worker-check selection) | Phase 6.1 adopted the two highest-value, lowest-noise ruflo background-worker *check ideas* as advisory tool-event hooks (`test-gap-notice`, `dependency-staleness-notice`). The remaining worker-check ideas from the source catalog (a periodic audit / optimize pass, a docs-staleness check, a duplicate-code-elimination check, and a per-run cost check) were considered and not adopted, because each either lacks a clean Write/Edit tool-event trigger (it is a periodic-scan idea, not an event-driven one), is already covered by an existing skill or command (audit/optimize by `/review` + `code-optimizer`; docs by `/update docs` + `documentation-consistency`; duplicates by `dead-code-eliminator` + `code-simplification`), or would be redundant with the hard cost controls in `ai-billing-safeguards`. Adopting them as always-firing hooks would add noise without proportional value, and a periodic scanner would reintroduce the daemon model the cycle deliberately declined. | Adopt an additional check as an advisory hook only when a clean tool-event trigger and a low false-positive rate are both demonstrable (for example, a docs-staleness advisory keyed on edits to a source file whose sibling doc was not also touched). Otherwise leave the capability to the existing skills/commands. | Low (the two highest-value checks are shipped; the rest are either covered elsewhere or noise-prone as always-firing hooks). |

## Notes

- **A6 decision (adoption-ruflo Phase 3.2): skipped, recorded here.** The plan's default-skip recommendation was followed. The phased-guided-development-with-gates function that A6 would document is already covered by the existing `/plan` -> `/implement` -> `/spec` flow and `quality-gate-definitions`, so adding the note now would duplicate shipped material without adding capability, and it risks contradicting the existing planning guidance. Recorded as DF-v310-ruflo-A6 above so a future cycle picks it up if concrete demand for the named methodology appears.
- **The `MANIFEST.sha256` is a release-time artifact, not committed mid-cycle (adoption-ruflo Phase 4).** `scripts/generate_manifest.py` is wired into `/update release` (it regenerates the manifest after the version bump, before the commit), so the authoritative manifest is produced and committed at the release tag, where it rides inside the install tarball (`~/.nexus-hub/src/MANIFEST.sha256`). It is deliberately NOT committed during in-progress phase work on `develop`, because every subsequent phase edits covered files and would leave a stale manifest; `develop` checkouts therefore have no manifest and `nexus-hub verify` cleanly reports "no manifest" (exit 2) until a release produces one. This is intended behavior, not a missing artifact.
- **Declines are durable, not gaps.** The six v3.10.0 runtime drops (the runtime meta-harness + MCP-daemon model, the GPU vector DB, the multi-provider router runtime, cross-machine federation, the hosted web UIs, and the WASM sandbox runtime) are recorded as authoritative rows in [docs/policy/mcp-reverse-engineering-matrix.md](../../../policy/mcp-reverse-engineering-matrix.md) in Phase 6, referencing [comparison-ruflo.md](comparison-ruflo.md), so a future comparison recognizes them as already-adjudicated rather than re-surfacing them as fresh gaps.

## Resolved

_None resolved in v3.10.0 yet._
