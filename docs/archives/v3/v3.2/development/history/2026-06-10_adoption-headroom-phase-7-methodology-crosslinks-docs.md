# Session History -- v3.2.0 adoption-headroom Phase 7: Methodology cross-links + docs

**Date**: 2026-06-10
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 7 of 7 -- Methodology cross-links + docs (re-partial); the final phase of the plan
**Branch**: `feat/adoption-headroom` (continuing from Phase 6)
**Outcome**: complete; all three sub-tasks (T021-T023) closed, all quality gates green (GO). adoption-headroom is now complete end-to-end. DF-v32hr-11 resolved; no new Phase 7 deferrals.

## Goal

Close the adoption by connecting the new engine to the existing methodology skills and documenting the architecture, with no new code. The deterministic + reversible + optional-ML engine already exists end-to-end (Phases 1-6); Phase 7 makes it discoverable from the human-facing context skills (so the agent reaches for the engine when output is mechanical) and writes the architecture down so a future maintainer understands the pipeline + CCR without reading the source.

## Subtasks completed

1. **T021 -- cross-link the engine from the three context skills** (`catalog/skills/orchestration/context-compression/SKILL.md`, `catalog/skills/orchestration/prompt-token-optimization/SKILL.md`, `catalog/skills/developer-experience/context-optimization/SKILL.md`). Each skill now carries a "Programmatic counterpart -- the `nexus-context-compressor` engine" note plus `[[ ]]` cross-links, framed as *when to reach for the engine* (mechanical tool output) versus *when to apply the skill's methodology* (judgment-bearing conversation history), with no engine internals duplicated into the bodies. `context-compression` and `prompt-token-optimization` each gained the note + a Related-Skills entry to `context-optimization` (the skill that configures the engine). `context-optimization` got the heaviest change (this is what DF-v32hr-11 tracked): its verbatim `cargo install --git rtk` proxy-setup section was replaced with the internal-engine setup (a single `NEXUS_CONTEXT_COMPRESS=1` env var, the Windows CLAUDE.md path, the what-it-compresses scope, reversibility, and a "Migrating from rtk" subsection), and its frontmatter `description`/`overview_l1`, the "What This Skill Does" bullet, two Common Rationalizations, and two Verification items were all updated off rtk and onto the engine. The now-false rtk `description`/`overview_l1` were also surgically synced in `data/skills.json` so the machine-readable catalog is truthful.
2. **T022 -- architecture documentation** (`extensions/nexus-context-compressor/README.md`, `docs/v3/v3.2/context-compressor-architecture.md`). The README's stale Status section (it still called Phase 4 "this phase" and listed Phases 5-7 as future) was brought current, and a new `Architecture` section was added covering: the two-entry-point -> one-router pipeline (an ASCII diagram of `compress_output`/`compress` -> `route` -> per-type strategy -> CCR store), a module map table, CCR reversibility (the persist-then-mark invariant, the single-source-of-truth marker grammar, the SQLite store), the local-first/zero-outbound guarantee, the optional ML module's offline-first design, and the rtk migration. A project-level `docs/v3/v3.2/context-compressor-architecture.md` was added as the map (why it exists, design principles, how it fits together, runtime-integration table, rtk migration, open items), pointing to the README for implementation detail.
3. **T023 -- final validation + CHANGELOG** (`CHANGELOG.md`). Ran the full validator suite, the compressor test suite, the compression accuracy gate, and the skill-security scan (all green; see Test results). Added three `## [Unreleased]` CHANGELOG entries (Phases 5, 6, 7 of the compressor -- Phases 5/6 had deferred their entries to the adoption-wide T023 per the phase boundary, and Phase 7 is its own entry), each in the established per-phase style, summarizing the accuracy harness, the optional ML dropper, and the cross-links + docs + rtk retirement.

## Key decisions

- **Cross-link, do not duplicate.** The plan's T021 is explicit that the methodology skills point to the engine without copying its internals. Each note is a few sentences of "reach for the engine when the bloat is mechanical tool output; apply this skill when it is judgment-bearing conversation history", plus a `[[context-optimization]]` link to the skill that owns setup. This keeps the skills within the 500-line norm (all three remain well under) and keeps the engine's deep detail in one place (the README + guide).
- **`context-optimization` is the engine's "setup" skill.** Rather than spread setup across all three skills, the two orchestration skills link to `context-optimization` for the one-env-var setup, and `context-optimization` carries the full internal-engine section + rtk migration. This matches the existing guide, which already cross-links the `context-optimization` skill as the AI-assisted companion.
- **Surgical `skills.json` sync, not a full `build-catalog` regen.** `data/skills.json` is a generated mirror, but its `overview_l1` for `context-optimization` already differed in wording from the SKILL.md frontmatter before this phase (proof the catalog is regenerated in bulk at build/release time, not per-edit). A full regen would have churned every drifted skill into this phase's diff, so only the now-false rtk clauses in this one entry were corrected; the broader frontmatter-to-`skills.json` reconciliation is left to the release-time `build-catalog`, the same disposition WN-v32-3 takes for count prose. Logged on the resolved DF-v32hr-11 row.
- **Documentation-only; no installer change.** Phase 7 added no script, hook, command, or MCP config -- the three SKILL.md edits live under `catalog/skills/` and the README under `extensions/`, both already recursively copied by the installer, and the new `docs/v3/v3.2/` note is a repo doc (intentionally not distributed, like the plan and known-gaps). Both installers still reference the compressor package (5 occurrences each, intact from Phases 1/4); no copy step was needed.
- **Release routing deferred.** As the plan's final phase, Phase 7 triggers release-readiness, but the v3.2.0 develop->main version bump / CHANGELOG finalization / count-prose reconciliation / tag are a `/update release` action owned at the merge, not a feature-branch action (as known-gaps states). Phase 7 leaves the branch release-ready, not released.

## Test results

- `make validate` validators run directly (WN-v32* host has no `make`): JSON catalogs OK (251 skills, 15 bundles, 17 workflows, templates), bundle orphan audit **PASS (0 errors, 1 pre-existing warning)**, no-personal-paths clean, unicode-safety **0 errors** (1051 pre-existing legacy WARNs in AGENTS.md/templates, none from this phase's files -- the new Markdown + the JSON edit are ASCII-only), supply-chain-iocs clean, workflow-security clean, solution-frontmatter clean, version-sync all-match (canonical 3.1.1; the 3.2.0 bump is the release's job).
- Compressor package suite (`cd extensions/nexus-context-compressor && python -m pytest -q`): **215 passed** (unchanged -- Phase 7 touched no Python).
- Compression accuracy gate, verbatim (`python -m evals --check`): **exit 0** -- CCR round-trip 100%, signature preservation 100%, mean char reduction 45.8% (unchanged).
- Skill-security scan (`python scripts/scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0** (no HIGH/CRITICAL; the MEDIUM/LOW findings are pre-existing in security skills / configs, none in this phase's three edited skills).
- `make lint` (ShellCheck): N/A -- Phase 7 added no shell surface.

## CI/CD edits

- None required. The compressor suite, the compression eval gate, and the catalog skill-security gate were CI-wired in Phases 4-5 (`.github/workflows/ci.yml`); the doc/SKILL.md/JSON edits are picked up automatically and add no new CI surface.

## Deviations

- **`data/skills.json` edited by hand (in scope).** The "never edit data/ manually" convention has an explicit registry-maintenance exception; a surgical fix of a now-false `description` after an in-scope SKILL.md change is exactly that. The full regen is deferred to the release bump (see Key decisions / DF-v32hr-11).
- **CHANGELOG carries Phase 5 + Phase 6 entries too.** Phases 5 and 6 deliberately deferred their `## [Unreleased]` entries to the adoption-wide T023 (the phase-boundary stance their session histories recorded); Phase 7 adds all three (5, 6, 7) so the changelog reflects the whole engine.
- **No DEVLOG entry.** Matching the established adoption-headroom precedent (every prior phase recorded itself in this `development/history/` directory + known-gaps rather than a root DEVLOG, which does not exist); this file is the per-phase record.

## Troubleshooting / environment notes

- `make` is not on PATH (WN-v32* class, same as every prior phase): every target was emulated by invoking the underlying validator / pytest / eval / scanner directly. The installer dry-run was likewise emulated -- since Phase 7 registered no new installer artifact, verification was confirming the existing compressor registration is intact in both installers and that the edited folders are already on the recursive-copy path.
- `tiktoken` / `onnxruntime` absent locally, so the engine ran in stdlib-token-fallback mode -- the intended default/CI posture; irrelevant to a docs-only phase.

## Known gaps

Logged in [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md): **DF-v32hr-11 moved to Resolved** (the verbatim rtk setup is gone from `context-optimization`; the engine is cross-linked in all three context skills). No new Phase 7 deferrals. Open total 20, resolved 3. The remaining open items are all prior-phase enhancements (CCR auto-eviction DF-v32hr-4, CacheAligner runtime wiring DF-v32hr-9, ML auto-wiring DF-v32hr-14, the live-ONNX CI lane MT-v32hr-1, and the Windows-verification WN class), none of which affect the local-first / reversible / zero-outbound guarantees.

## Next steps

- **adoption-headroom is complete.** All 7 phases are closed; the branch is release-ready. The remaining step is the v3.2.0 `develop` -> `main` release (merge `adoption-teach` + `adoption-headroom`, then `/update release`: docs + devlog + gitignore + version bump via `check_version_sync.py` + CHANGELOG finalization + count-prose reconciliation + `build-catalog` regen + tag + push), with its own confirmation gates. Never tag/push automatically.
- **Separately requested**: explore removing the deprecated v3.x command shims to reduce slash-menu noise (the user's follow-up to this implementation) -- a cross-platform decision presented for sign-off rather than executed inline, because the shims are documented "removed in v4.0.0".
