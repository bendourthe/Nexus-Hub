# Portable Status Contract

Summary: implementation and qualification of shared compact/full implementation reporting across supported Nexus-Hub platforms. Maintainers use this record to review layout, cadence, resource delivery, stale-install diagnostics and the remaining native-client qualification boundary.

## Scope

The maintainer authorized implementation on 2026-11-16 and additionally required a larger compact Status title, heading-style Goals, Decisions and Running sections, and blank lines around each heading. Work is isolated in `fix/portable-status-contract`, initially based on `origin/develop` at `cf6db64f5`, then fast-forwarded to `a71f4901e` after checking that its two release-evidence changes do not overlap this work. Unrelated primary-checkout changes and active worktrees are preserved. This maintenance change does not complete a signed release-plan task or authorize publication, release or broad installed-harness replacement.

## Implementation

1. Use the existing `implement-phase` bundle as the single reporting owner. `progress-reporting.md` owns cadence and evidence; `status-formats.md` owns layout. Remove the conflicting legacy phase-table requirement.
2. Add a standard-library renderer and illustrative input snapshot. Validate required observations, derive aggregate counts, escape evidence text and render portable Markdown in the maintainer-approved layout (an H2 Status Update heading, H2 emoji sections with H3 decision headings, and `&nbsp;` plus rule separators). Text escaping uses HTML entities and never backslash escapes, so Codex does not read parentheses or `$` as math. Keep empty sections visible. Full reports retain every scoped plan/phase row, goals, decision explanations/options, observed running work, timestamps and evidence sources.
3. Separate narration from reports. Emit full status at start/resume, explicit status requests and new decisions. Emit compact status at changed material checkpoints or after five minutes at the next reporting boundary. Ordinary commentary never emits status. Coalesce triggers, retain a receipt only after delivery and recover missing/invalid history with a full report. Explicit status remains read-only.
4. Carry the same concise instruction through every substantive platform template and inherited Google shim. Extend both session-start siblings with the same reminder. Use the existing common catalog for platforms without a native reporting skill. No additional Stop retry loop or workflow is introduced.
5. Add post-install diagnostics for missing/stale reporting resources and legacy Codex copies. Preserve legacy files and expose the mismatch; do not silently overwrite unowned content. A CLI audit exits nonzero for incomplete or stale reporting copies.
6. Verify deterministic behavior, actual temporary installations, installed CLI output, damaged-install repair, hook siblings and the affected repository validators. Record native-client limitations separately.

## Authority and CI

This is one local maintenance phase with one final local commit. No pipeline files are changed. New tests use the existing pytest discovery; no remote validation is started during implementation. No push, pull request, merge, release, worktree retirement or installation into the live user profile is part of this checkpoint.

## Qualification

The latest focused run passed 63 tests covering the renderer, routing contract and all platform delivery checks. The broader adapter regression run passed 204 tests with one skip: Hermes has no workspace instruction file, so the sibling-instruction preservation case does not apply. The session-start sibling parity selection passed 10 tests; the combined template, communication and session-start qualification also passed 124 tests before the final link/receipt refinements, which were then rechecked in the focused run. Counts from overlapping runs are not summed.

All 17 registered integration instruction paths are covered. Actual native skill installation, identical installed CLI output and missing-resource repair are covered for the 15 integrations that deliver native skill bundles. Aider and Copilot use the common catalog and their instruction/wrapper path; this checkpoint does not claim a full outer-installer or live model session for either.

The independent installed-Codex CLI exercise returned `full, none, none, compact, none, compact, full` for start, routine narration, early turn-end, changed material checkpoint, duplicate checkpoint, elapsed interval and explicit status request. The reporting audit returned exit codes `0, 1, 0` for healthy, missing layout and repaired installation. The CLI wrote no run state. [Observations](portable-status-cli-proof.json), [compact example](portable-status-compact-example.md) and [full example](portable-status-full-example.md) are illustrative fixtures, not live run evidence.

Ruff, the Python grammar-floor check, registry integrity, agentskills conformance, bundled-resource audit, installer parity, documentation conventions, standing instruction budgets, base-template parity and whitespace checks passed. Instruction budgets were retained. Attribution verified Ben Dourthe's configured identity and active Git hooks.

## Remaining Qualification

The source change is local. Publication, installation into the live user profile and end-to-end native model/client sessions remain unperformed. Recommend the normal reviewed integration and backed-up installation, followed by fresh compact/full status requests and a narration/checkpoint sequence in each supported client. Keeping the current installation preserves the reported behavior and version drift. Legacy user-owned duplicates require preservation-aware repair; diagnostics do not overwrite them.

 Temporary-install and CLI proof establishes delivered bytes and deterministic behavior. It does not establish that every model invokes the renderer or that every chat client displays identical pixel sizes. Native hook availability/trust and model adherence must be observed in each actual client before claiming native platform parity.

## Review

Considered but rejected: separate per-platform layouts would recreate drift; another Stop retry loop could repeatedly interrupt work; rewriting or deleting legacy Codex skills could lose user edits; raising standing instruction budgets would charge every session for detailed reporting rules. The change reuses the catalog bundle, adapters, session-start event and existing preservation behavior.

construction-debt: one bundled renderer, one small installation-diagnostic module, existing platform templates/hooks and focused regression tests. No scheduler, new runtime package, parallel task ledger or CI workflow.
