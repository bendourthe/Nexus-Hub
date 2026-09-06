# Session History -- v3.1.0 adoption-dynamic-workflows Phase 2: Pilot on high-value read-only skills (skill-native)

**Date**: 2026-06-05
**Plan**: [docs/releases/v3/v3.1/plans/adoption-dynamic-workflows.md](../../plans/adoption-dynamic-workflows.md)
**Phase**: 2 of 3 -- Pilot on high-value read-only skills (skill-native)
**Branch**: `feat/adoption-dynamic-workflows`
**Outcome**: Complete. Both sub-tasks (T004-T005) closed plus stabilization (T006); catalog validators green and the skill-security scanner is clean on both pilot bundles.

## Goal

Apply the Phase 1 workflow-as-skill-bundle convention to two skills whose work is large-surface, read-only, and embarrassingly parallel -- the article's canonical fan-out use case. Each pilot skill gains an adapted, gracefully-degrading Dynamic-Workflow `.js` template referenced from its SKILL.md, with the scope-first token caution and a cross-link (not a copy) to `agent-orchestration-primitives`.

## Chronological Steps

1. **Resolved the plan, phase, and branch.** Located `docs/v3/v3.1/plans/adoption-dynamic-workflows.md` (legacy flat layout); confirmed the current branch is already `feat/adoption-dynamic-workflows` with Phase 1 committed at `b7c70c2`. Parsed the three sub-tasks; Phase 2 is non-final (2 of 3), so no release-readiness workflow runs.
2. **Cleared the shared-gate prerequisite empirically.** The v3-adoption-cycle memory flags a cross-branch gate: the claude-red `nexus-skill-scanner` producer-catalog allowlist should land on `develop` before the dynamic-workflows pilot, because the pilot `.js` bundles "also trip the scanner." Verified `feat/adoption-claude-red` has NOT merged to `develop` (tip is `d55c5c6`). Then tested the assumption directly: ran the scanner on the Phase 1 `.js` template -- 0 findings. Read the scanner's `text_patterns.py` (every prose pattern hard-capped at MEDIUM, fence-aware) and `signatures.py` (the only HIGH/CRITICAL source for non-Python files, opt-in via `--yara`, not passed by the CI gate). Conclusion: a read-only illustrative `.js` template can only ever yield MEDIUM-or-below findings, so the gate is moot for these bundles. `make validate` does not run the scanner at all.
3. **Studied the two host skills.** Read `multi-agent-code-review/SKILL.md` and its `references/findings-schema.md` + `references/validator-template.md` -- the skill is already a prose description of the dimensions -> find -> adversarially-verify shape (personas = dimensions, Stage 4 = find, Stage 6 refutation = verify) with two ready-made schemas. Read `deep-research-compilation/SKILL.md` and noted its core principle ("you are the generator; there is no persistent script") governs document EMISSION, so the upstream gathering harness is a categorically separate artifact.
4. **T004 -- authored the code-review template.** Wrote `catalog/skills/code-review/multi-agent-code-review/scripts/review-fanout-workflow.js`: a Review -> Verify -> Synthesize fan-out binding `FINDINGS_SCHEMA` to `references/findings-schema.md` and `VERDICT_SCHEMA` to `references/validator-template.md`. Used a deliberate `parallel()` barrier for the persona review (the cross-reviewer promotion in the merge genuinely needs the full finding set), a deterministic in-JS dedup/promotion/late-gate, and a per-finding adversarial refutation pass. Included the TEMPLATE-TO-ADAPT, graceful-degradation, scope-first, and skill-native banners.
5. **T004 -- referenced it.** Added a "Running the fanout as a Dynamic Workflow (optional)" subsection to the SKILL.md (after Stage 7) pointing at `scripts/review-fanout-workflow.js`, with graceful-degradation + scope-first framing and `[[agent-orchestration-primitives]]` / `[[ai-billing-safeguards]]` cross-links (no duplication). Satisfies the orphan-audit basename requirement.
6. **T005 -- authored the research template.** Wrote `catalog/skills/specialized-domains/deep-research-compilation/scripts/research-fanout-workflow.js`: a Search -> Fetch -> Verify -> Synthesize fan-out (multi-modal search sweep with a barrier dedup, a per-source fetch `pipeline`, per-claim adversarial refutation, then a cited synthesis whose canonical `[N]` list feeds the skill's Step 4 renumbering). The skill-native banner was adapted to state truthfully that the subagents use the harness's built-in `WebSearch` / `WebFetch` tools -- no NEW dependency, credential, or third-party MCP.
7. **T005 -- referenced it.** Added an "Upstream: gathering sources as a Dynamic Workflow (optional)" section before Step 1, explicitly reconciling it with the skill's "no persistent generator" rule (that rule is about document emission; this harness emits no document and gathers sources). Cross-linked `[[deep-research]]`, `[[agent-orchestration-primitives]]`, `[[ai-billing-safeguards]]`.
8. **T006 -- validated.** Emulated `make validate` by running each validator directly (orphan-bundle audit + quality heuristics + version-sync). Ran the skill-security scanner against both pilot skills. Ran the `tests/validators` pytest suite. All green.
9. **Post-phase sequence.** Checked off the Phase 2 boxes + exit checklist, updated `docs/v3/v3.1/known-gaps.md`, added a DEVLOG entry, wrote this session history, and prepared the commit message.

## Troubleshooting

- **No issues encountered.** The work is additive catalog content; no build/test breakage arose. The only investigative effort was the shared-gate verification (step 2), which resolved in favor of proceeding once the scanner architecture was understood.

## Assumptions

- The "appropriate feature branch" is `feat/adoption-dynamic-workflows` (matches the plan slug and the v3 adoption-cycle branching pattern); it was already checked out.
- The two `.js` templates are intentionally illustrative ("TEMPLATE TO ADAPT", per the plan), so their only automated gate is the orphan-bundle audit (plus the scanner, run for due diligence) -- they are not executed or unit-tested, and no coverage gate applies, mirroring the Phase 1 reference template.
- CHANGELOG is intentionally left untouched: the plan assigns the `## [Unreleased]` entry to Phase 3 (T009), not Phase 2.
- No `data/` registry edits are required because no new skill was added (bundled scripts on two existing skills plus prose).
- The shared-gate scanner allowlist from claude-red Phase 2 is NOT a blocker for these read-only templates (verified empirically); when claude-red eventually merges to `develop`, the allowlist will broaden the catalog scanner posture but does not change the clean result for these two bundles.

## Testing Results

`make validate` emulated directly (Windows host has no `make`):

- Orphan-bundle audit: PASS (0 errors, 1 pre-existing warning -- `demo-capture/scripts/__pycache__/*.pyc`, gitignored and untracked, unrelated to this phase). Both `review-fanout-workflow.js` and `research-fanout-workflow.js` recognized as referenced (not orphaned).
- Quality heuristics: PASS (0 errors, 1 warning).
- `check_version_sync.py`: exit 0 (green at 3.0.0 across all surfaces; no version surface touched).
- Skill-security scanner (`scan_skill_security.py ... --fail-on high`): 7 files scanned across both pilot skills, 0 findings, 0 HIGH/CRITICAL -- the shared-gate concern is moot for these bundles.
- `pytest tests/validators -q`: 134 passed (no regression in the bundle-audit logic).

No traditional test suite is affected (`make test` covers the MCP servers; this phase changes only catalog markdown + two illustrative `.js` templates).

## Files Changed

- `catalog/skills/code-review/multi-agent-code-review/scripts/review-fanout-workflow.js` -- new adapted template (T004).
- `catalog/skills/code-review/multi-agent-code-review/SKILL.md` -- new "Running the fanout as a Dynamic Workflow (optional)" subsection referencing the template.
- `catalog/skills/specialized-domains/deep-research-compilation/scripts/research-fanout-workflow.js` -- new adapted template (T005).
- `catalog/skills/specialized-domains/deep-research-compilation/SKILL.md` -- new "Upstream: gathering sources as a Dynamic Workflow (optional)" section referencing the template.
- `docs/v3/v3.1/plans/adoption-dynamic-workflows.md` -- Phase 2 boxes + exit checklist checked off.
- `docs/v3/v3.1/known-gaps.md` -- header refreshed; WN-v31-1 broadened to Phase 1-2.
- `docs/DEVLOG.md` -- Phase 2 entry.
- `docs/archive/v3/v3.1/development/history/2026-06-05_phase-2-pilot-read-only-skills.md` -- this file.

## Next Steps

- **Phase 3** (final phase of the plan): add the pairwise-tournament ranking-at-scale shape to `references/five-patterns.md` (distinct from `competitive-generation`'s best-of-N), cross-reference the `/loop` and `/goal` platform commands in `agent-orchestration-primitives/SKILL.md`, and add the CHANGELOG `## [Unreleased]` entry summarizing the convention + pilots + enrichments. Because Phase 3 is the final phase, `/implement-phase` will additionally run the release-readiness workflow (resolve known gaps, verify tests + CI/CD, refactor audits, `/update-*` checks, version-bump prep).
