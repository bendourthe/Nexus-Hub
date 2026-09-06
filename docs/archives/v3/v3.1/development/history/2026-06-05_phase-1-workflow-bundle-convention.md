# Session History -- v3.1.0 adoption-dynamic-workflows Phase 1: Workflow-bundle convention (skill-native)

**Date**: 2026-06-05
**Plan**: [docs/releases/v3/v3.1/plans/adoption-dynamic-workflows.md](../../plans/adoption-dynamic-workflows.md)
**Phase**: 1 of 3 -- Workflow-bundle convention (skill-native)
**Branch**: `feat/adoption-dynamic-workflows`
**Outcome**: Complete. All three sub-tasks (T001-T003) closed; catalog validators green.

## Goal

Define and document how a skill ships a Dynamic-Workflow `.js` template as a Tier-3 bundled resource (referenced from SKILL.md as a template to adapt, not a verbatim script to run), and author one canonical reference template. This is the genuine residual from the source comparison `comparison-a-harness-for-every-task-dynamic-workflows-in-claude-code.md`: the orchestration theory was already adopted in v3.0.0 (`agent-orchestration-primitives` + `references/five-patterns.md`), so Phase 1 covers only the distribution-pattern gap.

## Chronological Steps

1. **Resolved the plan and phase.** Located `docs/v3/v3.1/plans/adoption-dynamic-workflows.md` (legacy flat layout). Parsed the three sub-tasks and confirmed Phase 1 is non-final (1 of 3), so no release-readiness workflow runs.
2. **Prepared the branch.** Confirmed `feat/adoption-dynamic-workflows` existed locally but was two commits behind `develop` (the branching-governance merge) with zero unique commits. Checked it out and fast-forwarded it to `develop` (`be071f8..d55c5c6`), a clean fast-forward with no merge commit.
3. **Reviewed the target skill.** Read `agent-orchestration-primitives/SKILL.md` and confirmed the bundle structure (`SKILL.md` + `references/five-patterns.md`; no `assets/` directory yet). Read the AGENTS.md "Per-skill Bundled Resources" subsection to find the insertion point for T001.
4. **Verified the toolchain.** `make` is absent on the Windows host but `python` 3.12.10 is present. Read the Makefile `validate` target to enumerate the validators T003 must run directly. Read `validate_workflow_security.py` and confirmed it scans only `.github/workflows/*.yml` (not the new `.js`), so the template would not trip it.
5. **T002 -- authored the reference template.** Wrote `catalog/skills/orchestration/agent-orchestration-primitives/assets/example-fanout-workflow.js`: a Discover -> Audit -> Synthesize read-only fan-out with the required `export const meta` literal, TEMPLATE-TO-ADAPT markers, a graceful-degradation banner, the scope-first token caution, schema-validated per-file findings, and `pipeline()` null-filtering.
6. **Referenced the template.** Added a paragraph to SKILL.md Step 7 pointing at `assets/example-fanout-workflow.js` as a copy-adaptable starting point (this also satisfies the orphan-bundle audit's basename-in-SKILL.md requirement).
7. **T001 -- documented the convention.** Added a "Workflow templates (Dynamic Workflows)" block to the AGENTS.md "Per-skill Bundled Resources" subsection with the three mandatory rules (graceful degradation, scope-first token caution + `[[ai-billing-safeguards]]` cross-link, skill-native).
8. **T003 -- validated.** Emulated `make validate` by running each validator directly. Confirmed the orphan audit recognizes the template, all JSON catalogs load, and the ASCII / personal-path / supply-chain / version-sync validators exit 0.
9. **Post-phase sequence.** Checked off the plan boxes, created `docs/v3/v3.1/known-gaps.md`, added a DEVLOG entry, wrote this session history, and prepared the commit message.

## Troubleshooting

- **ASCII-verification script crash.** A one-off Python check that printed found non-ASCII characters crashed with a `UnicodeEncodeError` (cp1252 console) on AGENTS.md's box-drawing char `U+251C`. This was a console-encoding limitation in the throwaway check, not a content problem: the char is pre-existing in AGENTS.md's directory-tree diagram. Re-ran the check printing codepoints only (never the raw glyph) and confirmed: the JS template and SKILL.md edits are 100% ASCII-clean, and my inserted AGENTS.md block (lines 216-223) added zero non-ASCII characters. The 143 non-ASCII chars in AGENTS.md are all pre-existing (em-dashes, `<=` glyphs, tree-diagram box-drawing).

## Assumptions

- The "appropriate feature branch" is `feat/adoption-dynamic-workflows` (matches the plan slug and the v3 adoption-cycle branching pattern).
- The `.js` template is intentionally illustrative (a "TEMPLATE TO ADAPT", per the plan), so its only automated gate is the orphan-bundle audit -- it is not executed or unit-tested, and no coverage gate applies to it.
- CHANGELOG is intentionally left untouched: the plan assigns the `## [Unreleased]` entry to Phase 3 (T009), not Phase 1.
- No `data/` registry edits are required because no new skill was added (only an asset on an existing skill plus prose).

## Testing Results

`make validate` emulated directly (Windows host has no `make`):

- Orphan-bundle audit: PASS (0 errors, 1 pre-existing warning -- `demo-capture/scripts/__pycache__/*.pyc`, gitignored-but-on-disk, unrelated to this phase). `example-fanout-workflow.js` recognized as referenced.
- JSON catalogs: `skills.json` (247 skills), `bundles.json`, `workflows.json`, `templates.json` all load.
- `validate_no_personal_paths.py`: exit 0.
- `validate_unicode_safety.py`: exit 0 (pre-existing warnings only; my changes ASCII-clean).
- `scan_supply_chain_iocs.py`: exit 0.
- `check_version_sync.py`: exit 0 (green at 3.0.0 across all surfaces; no version surface touched).

No traditional test suite is affected (`make test` covers the MCP servers; this phase changes only catalog markdown + one asset).

## Files Changed

- `AGENTS.md` -- new "Workflow templates (Dynamic Workflows)" convention block (T001).
- `catalog/skills/orchestration/agent-orchestration-primitives/assets/example-fanout-workflow.js` -- new reference template (T002).
- `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` -- Step 7 reference to the template.
- `docs/v3/v3.1/plans/adoption-dynamic-workflows.md` -- Phase 1 boxes + exit checklist checked off.
- `docs/v3/v3.1/known-gaps.md` -- created (WN-v31-1).
- `docs/DEVLOG.md` -- Phase 1 entry.
- `docs/archive/v3/v3.1/development/history/2026-06-05_phase-1-workflow-bundle-convention.md` -- this file.

## Next Steps

- **Phase 2**: pilot the convention on two high-value read-only skills -- add an adapted `dimensions -> find -> adversarially-verify` template to `multi-agent-code-review`, and a `fan-out -> fetch -> verify -> synthesize` template to `deep-research-compilation`.
- **Phase 3**: add the pairwise-tournament ranking-at-scale shape to `references/five-patterns.md`, cross-reference the `/loop` and `/goal` platform commands in the skill, and add the CHANGELOG `## [Unreleased]` entry.
