# Session History - adoption-t3mp3st Phases 2-4: receipt discipline, approval gate, declines

**Date**: 2026-07-08
**Plan**: `docs/v3/v3.11/plans/adoption-t3mp3st.md`
**Phases**: 2, 3, 4 of 4 (completed in one continuous pass after Phase 1)
**Status**: Complete. Plan fully implemented. All edits body-only, defensive, zero registry drift. Part of the open v3.11.0 release; `/update release` ships it.

## Goal

Complete the T3MP3ST defensive adoption: fold a reproducible-benchmark-receipt discipline into the evaluation skills (C2), add a dangerous-action human-approval-gate pattern to `agent-access-policy` (C3), and record the declined offensive components plus the CHANGELOG entry (Phase 4).

## What changed (all body-only; no frontmatter, no `data/` edit)

- **Phase 2.1 - `skill-eval-loop`** (`catalog/skills/workflow/skill-eval-loop/SKILL.md`): new `## Reproducible receipts` section (after Persistence discipline). Rule: no headline number ships without (1) a committed artifact it recomputes from (the iteration's `benchmark.json` + per-run `grading.json`), (2) a single documented recompute step (`scripts/aggregate_benchmark.py <workspace>/iteration-N/`), and (3) a confidence interval (Wilson for pass@1) or an honest small-sample label. Maps the discipline onto the skill's existing benchmark machinery rather than adding infrastructure. Cross-links `[[ai-output-evaluation]]`.
- **Phase 2.2 - `ai-output-evaluation`** (`catalog/skills/developer-experience/ai-output-evaluation/SKILL.md`): concise `## Reproducible Receipts` note (shorter than the skill-eval-loop version, to avoid duplication) applying the same committed-artifact + recompute-step + interval-or-honest-label rule to LLM-as-judge / rubric scores. Cross-links `[[skill-eval-loop]]` as the fuller treatment.
- **Phase 3.1 - `agent-access-policy`** (`catalog/skills/orchestration/agent-access-policy/SKILL.md`): new `## Dangerous-Action Approval Gates` section, DISTINCT from the Phase 1.2 containment section. Defines the gated class by effect (destructive FS ops outside the working tree, actions reaching systems beyond the local project, tools with external side effects, anything not cleanly undoable), states the default-deny-on-uncertainty stance, and distinguishes the gate from containment (what is reachable) and from spend caps (`[[ai-billing-safeguards]]`).
- **Phase 4.1 - declines** (`docs/v3/v3.11/known-gaps.md`): new `## Comparison Declines` section recording the six declined offensive component classes (exploitation runtime / meta-harness; attacker swarm + C2; offensive arsenal; detection-evasion engine; keyless local-agent-hijack credential proxy; runtime service surfaces) each described generically by function with the grounds cited by name (MCP Registry Policy + the v3.10.0 ruflo precedent; the defensive safety posture), plus the deferred optional C5 report-type taxonomy.
- **Phase 4.2 - CHANGELOG** (`CHANGELOG.md`): one bullet under `## [3.11.0] ### Changed` (not `[Unreleased]` - that was already promoted to `[3.11.0]` in workflow-governance Phase 8) describing all three adopted items (C1/C2/C3) with unchanged counts (263 skills, not the plan's stale 260), the no-new-outbound assurance, and the offensive-component declines. Cites the plan, comparison, and known-gaps.

## Verification (2.3 / 3.2 / 4.3)

- Validators green (`make validate` gate mode): `validate_skills.py --bundles-only` and `--quality` exit 0; `validate_unicode_safety.py` exit 0; `check_version_sync.py` clean at 3.11.0.
- Skill count unchanged at 263 across `data/skills.json`, `data/SKILL_INDEX.md` (263 rows + "Total: 263 skills"), and `data/marketplace.json` (category counts sum to 263) - confirming the body-only, no-new-skill guarantee.
- Registry-drift guard: `git diff` shows zero frontmatter-line changes in all four edited skills across the cycle (Phases 1-3 touched five skills; none changed frontmatter).
- Line counts under the 500-line norm: skill-eval-loop 272, ai-output-evaluation 305, agent-access-policy 304.
- Attribution: the five distributed skill artifacts contain zero matches for `T3MP3ST` / `TEMPEST` / `verify-claims` / `Metasploit` / `Hydra` / `Sqlmap` / `elder-plinius` / `Pliny`. The only diff matches are internal file-path references to `comparison-t3mp3st.md` and `adoption-t3mp3st.md` in `known-gaps.md` / `CHANGELOG.md` (the slug in filenames), which the plan's 4.1/4.2 explicitly instruct - not prose attribution.
- ASCII-only: no non-ASCII characters introduced in the CHANGELOG or known-gaps edits.
- `make lint` (ShellCheck) and the full `make test` pytest suite: not run locally (this cycle edits no shell script and no test; `make` is unavailable on the Windows host). Covered by CI on Linux on the release push.

## Notes

- The plan predates the current v3.11.0 count and CHANGELOG state, so two documented adaptations were made: the CHANGELOG entry folds into the already-open `## [3.11.0]` rather than `## [Unreleased]`, and it states 263 skills rather than the plan's 260. Both are noted in the Phase 4 Exit Checklist.
- Nothing auto-committed here beyond the planned develop commit; no tag/push. `/update release` ships v3.11.0 (workflow-governance + all adoptions) when the version DoD is met.

## Next steps

- adoption-t3mp3st is complete (all four phases). Remaining v3.11.0 work, if any (e.g. adoption-spec-kit third cycle), then `/update release`.
