# Session History - v3.4.0 adoption-nessie-and-agency-agents Phase 5: selective agent-body enrichment

**Date**: 2026-06-15
**Plan**: [`../../plans/adoption-nessie-and-agency-agents.md`](../../plans/adoption-nessie-and-agency-agents.md) Phase 5 (A2, skill-native)
**Branch**: `develop`
**Outcome**: Implementation complete; quality gate GO. This is the plan's final phase (5 of 5), so release readiness via `/update release` follows (gated on user confirmation; no tag or push made automatically).

## Goal

Where a Nexus-Hub agent definition genuinely benefits, add concise "Success Metrics" and/or "Deliverable Template" sections in the repo's terse, verification-first style, importing none of the comparison source's persona/vibe narration. Opportunistic and scoped: no agent edited "just because".

## Selection (sub-task 5.1)

Surveyed all 23 agents under `catalog/agents/`. The 13 single-lens reviewers (`coherence-reviewer`, `adversarial-reviewer`, `maintainability-reviewer`, etc.) already carry a strict JSON "Output contract" section; `architect`, `planner`, `code-reviewer`, `security-reviewer`, `refactor-cleaner`, and `loop-operator` already have an "Output"/"Output Format(s)"/"After Completion" section; `tdd-guide` already has an observable "Coverage Gate". Per the plan ("if an agent's existing structure already conveys success criteria, leave it alone"), none of those earned an edit.

The justified set is the three deliverable-producing agents that produce a concrete artifact but lacked any success-criteria or output-contract section:

| Agent | Gap | Added |
|---|---|---|
| `build-error-resolver` | Process-only (collect/triage/fix/verify); description promises "Report the root cause and fix" but no output contract or pass/fail bar | Success Metrics + Deliverable Template |
| `harness-optimizer` | Description promises "a concrete improvement plan"; has a phased process + Phase-4 deltas but no consolidated deliverable shape or pass/fail bar | Success Metrics + Deliverable Template |
| `doc-updater` | Produces scattered doc edits with per-doc format snippets but no observable "done/correct" criteria | Success Metrics only (a single template does not fit scattered edits) |

## What shipped (sub-task 5.2)

- **`catalog/agents/build-error-resolver.md`**: a "Success Metrics" section (build exits 0 with zero errors; existing tests still pass; no suppression without a justifying comment; fix targets the first error in dependency order) and a "Deliverable Template" (Root Cause -> Fix -> Cascade Resolved -> Verification report shape).
- **`catalog/agents/harness-optimizer.md`**: a "Success Metrics" section (suite time below baseline, measured; flakiness fixed not masked; coverage at or above baseline; full suite green after every change) and a "Deliverable Template" (Inventory -> Prioritized Improvements table -> Quick Wins Applied with before -> after deltas).
- **`catalog/agents/doc-updater.md`**: a "Success Metrics" section (only changed-behavior sections updated; dated DEVLOG entry under 200 words; no claim contradicts the code; nothing deleted without confirming removal).
- **`CHANGELOG.md`**: `## [Unreleased]` "Changed" entry recording the enrichment as skill-native, zero new outbound call / dependency / credential, with the scope rationale.

All added content is ASCII-only (hyphens, `->`, straight quotes), follows the Markdown style guide (blank line before/after every list, heading, and code fence), and introduces no persona/vibe narration.

## Key decisions

- **Scope discipline over coverage.** The phase goal is opportunistic enrichment, so the test was "does this agent lack an output contract that a section would supply?" not "could any agent take a section?". That filtered 23 agents down to 3 and left the reviewers (already JSON-contracted) and the Output-Format-bearing working agents untouched.
- **ASCII-only for new content, leave legacy em-dashes alone.** The existing agent bodies use em-dashes throughout. `validate_unicode_safety.py` flags em-dashes only as warnings under `make validate` (non-strict); converting the pre-existing ones would violate the "every changed line must trace to the request" rule, so new sections are ASCII and the legacy punctuation is left in place. A `--strict` run confirmed all 14 flagged em-dashes are pre-existing lines, none in the added sections.
- **`doc-updater` gets metrics but no template.** Its deliverable is scattered edits across several docs, so a single fenced template would misrepresent the shape; Success Metrics alone supplies the observable bar.

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so gates were run via direct equivalents:

- **Unicode-safety**: non-strict run exit 0 (only pre-existing em-dash warnings; the three edited files are ASCII-clean in all added content, confirmed by reading lines 60-82 / 50-70 / 69-74 and a `--strict` line-by-line check).
- **No-personal-paths / supply-chain-iocs / workflow-security**: all exit 0; no findings reference the three edited files.
- **JSON integrity**: `data/skills.json` 256 skills, `data/bundles.json` 15 bundles (unchanged; no skill or registry edit needed for agent definitions).
- **Bundle orphan audit**: PASS (0 errors, 1 pre-existing WN-v33-2 warning).
- **Solution frontmatter**: exit 0. **Version-sync**: all surfaces match 3.3.4 (the in-development state; the bump to 3.4.0 happens at release).
- The compression accuracy eval (`extensions/nexus-context-compressor`) was not run: this phase does not touch the compressor, so it is out of scope; CI runs it on the ubuntu runner.

No regressions: agents are auto-distributed by both installers via folder copy, so no installer or registry edit was required, and no data/ file changed.

## Files changed

- `catalog/agents/build-error-resolver.md`
- `catalog/agents/harness-optimizer.md`
- `catalog/agents/doc-updater.md`
- `CHANGELOG.md`
- `docs/v3/v3.4/plans/adoption-nessie-and-agency-agents.md` (Phase 5 exit checklist)
- `docs/archive/v3/v3.4/development/history/2026-06-15_adoption-nessie-and-agency-agents-phase-5-agent-body-enrichment.md` (this file)

## Next

Final phase complete. Release readiness via `/update release`: bump 3.3.4 -> 3.4.0 across the version-carrying surfaces, finalize the `[Unreleased]` CHANGELOG block as `[3.4.0]`, merge `develop` -> `main`, tag `v3.4.0`, and push - each gated by `/update release`'s own confirmation prompts. No tag or push is made automatically.
