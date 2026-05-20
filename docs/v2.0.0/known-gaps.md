# Known Gaps -- v2.0.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.0.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md)
**Status**: open
**Last updated**: 2026-05-20 (Phase 5 close; catalog bulk rename complete, using-devai-hub skill renamed, .cursor/rules/devai-hub.mdc renamed, build-catalog source-of-truth defect discovered)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 3 |
| BG -- Bug or unresolved test failure | 1 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 2 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **4** | **3** |

> Phase 5 closed with all stability gates green: `grep -rn "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" catalog/ templates/ .cursor/` returns NOTHING; `python scripts/validate_skills.py --bundles-only` returns PASS (0 errors, 4 WN-001 carry-over warnings); `python -m pytest catalog/hooks/tests -q` returns 370 passed, 3 skipped (above the 366 baseline because Phase 3.3 added installer-migration smoke tests and Phase 4 added MCP-rename guards). The single new gap opened this phase is BG-001 (build-catalog regression). DF-001 from Phase 2 is resolved by the Phase 5.1 catalog sweep but its follow-up rerun is parked behind BG-001 -- see DF-001 in the Resolved table and BG-001 below. WN-001 and WN-002 remain as documented v1.3.0 carry-overs scheduled for closeout in Phase 8 sub-task 8.3.

## Open Items

### BG-001 -- `infrastructure/tools/build_skills_catalog.py` has hardcoded DevAI strings that regress data/ on regeneration

**Source phase**: Phase 5, post-sweep DF-001 follow-up.
**Plan reference**: [docs/v2.0.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md) sub-task 2.2 step 4 and DF-001 (the deferred re-run of `make build-catalog` after the Phase 5 catalog sweep).
**Reason**: When the Phase 5.1 sweep completed, DF-001 prescribed running the catalog builder to confirm `data/skills.json` and `data/SKILL_INDEX.md` agree with the regenerated source-of-truth. Running `python infrastructure/tools/build_skills_catalog.py` produced 1149 insertions / 1156 deletions across `data/skills.json` and `data/SKILL_INDEX.md` -- including reverting `# Nexus-Hub Skill Index` back to `# DevAI-Hub Skill Index`. Root cause: the builder script itself carries four hardcoded DevAI strings (lines 292, 300, 339, 340 of `infrastructure/tools/build_skills_catalog.py`: two GitHub URLs, the SKILL_INDEX title literal, and the catalog `description` field). The regeneration was reverted via `git checkout -- data/SKILL_INDEX.md data/skills.json` so Phase 2's manual edits remain intact. Until the builder is renamed, `make build-catalog` is unsafe to run.
**Suggested next step**: In Phase 7 (`/update-documentation` + `/update-config` sweep) extend the rename surface to `infrastructure/tools/build_skills_catalog.py`. The fix is a four-line edit -- two GitHub URL strings, one Markdown H1, one description string. After the builder is renamed, re-run `python infrastructure/tools/build_skills_catalog.py` and diff against the manually-edited `data/` files; resolve any drift in the same commit.

### WN-001 -- Pre-existing orphan-bundle warnings carried from v1.1.5 / v1.3.0

**Source phase**: Phase 2, sub-task 2.5 stability gate (re-observed during validator runs at Phase 5 close).
**Plan reference**: [docs/v1.3.0/known-gaps.md](../v1.3.0/known-gaps.md) WN-001 (carry-over). Phase 2.2 step 5 and Phase 5.5 step 2 both explicitly allow "4 known orphan warnings allowed per WN-001".
**Reason**: `python scripts/validate_skills.py --bundles-only` continues to emit 4 warnings on the framework-specialist bundle: `fastapi-expert/references/dependency-injection-patterns.md`, `nextjs-expert/references/data-fetching-patterns.md`, `react-expert/references/performance-patterns.md`, `react-expert/references/testing-recipes.md`. None of these references are linked from their parent SKILL.md. Carried forward across v1.1.5, v1.2.x, v1.3.0, v1.4.0.
**Suggested next step**: Per the v2.0.0 plan Phase 8 sub-task 8.3, decide at version close whether to close out or re-defer. Tracking options per v1.3.0 WN-001: (a) link each orphan from its parent SKILL.md, (b) inline-and-delete, or (c) leave as documented carry-over.

### WN-002 -- `make` and `shellcheck` unavailable on Windows dev machine; UTF-8 codec workaround

**Source phase**: Phase 2, sub-task 2.5 stability gate (carry-over from v1.3.0 Phase 1 baseline conditions).
**Plan reference**: [docs/v1.3.0/known-gaps.md](../v1.3.0/known-gaps.md) WN-002. The v2.0.0 plan Phase 1 baseline ([docs/v2.0.0/baselines/](baselines/)) documents the same workaround.
**Reason**: `make validate` / `make lint` / `make test` cannot run directly on the Windows 11 + Git Bash environment (`make` and `shellcheck` not on PATH). All validators were invoked via direct Python (`python scripts/validate_skills.py --bundles-only`). Bash hook syntax was checked via the `for f in catalog/hooks/*.sh; do bash -n "$f"; done` loop at Phase 5.5. Result during Phase 5 close: PASS, 0 errors, 4 warnings (the WN-001 orphans), 370 hook tests passed.
**Suggested next step**: Same as v1.3.0 WN-002 -- either patch Makefile inline `python -c` calls to pass `encoding='utf-8'`, or document Windows dev-environment prerequisites. Owner: future hygiene phase.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-001 | `data/skills.json` and `data/SKILL_INDEX.md` regeneration deferred until after Phase 5 | Phase 5 sub-task 5.1 (sweep) + BG-001 (parked follow-up) | The Phase 5.1 catalog sweep removed every DevAI string from `catalog/`, which was the precondition DF-001 named. The downstream re-run of `make build-catalog` is parked behind BG-001 because the builder source itself still carries DevAI literals; the data/ files manually edited in Phase 2 remain the source-of-truth until the builder is renamed in Phase 7. |
| DF-002 | End-to-end installer smoke deferred to Phase 4 close | Phase 4 sub-task 4.1 | The three `extensions/nexus-*` directories now exist on disk, so the installer's MCP-server install branch is no longer skipped. The cross-platform installer dry-run prescribed by plan sub-task 8.2 is still owed and will be captured to `docs/v2.0.0/installer-smoke-post.txt` during Phase 8.2; the *Phase 4* deferral specifically is closed. |
| DF-003 | `scripts/devai_mcp_benchmark.py` rename pulled into Phase 3 ahead of plan | Phase 4 sub-task 4.1 + 4.3 | The extension package rename in Phase 4.1 unblocks `python scripts/nexus_mcp_benchmark.py --help`, which now runs end-to-end (verified at Phase 4.3 close). The `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1` rename in 4.3 closes the rest of the Phase 4.3 scope. |

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.0.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
