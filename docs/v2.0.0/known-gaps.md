# Known Gaps -- v2.0.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.0.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md)
**Status**: open
**Last updated**: 2026-05-20 (Phase 4 close; extension dirs and Python packages renamed, MCP registry updated, Install-DevAI-Permissions.ps1 renamed)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 2 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 2 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **3** | **2** |

> Phase 4 closed with all stability gates green: 37 + 36+1s + 23 extension tests passing, 370 + 3s hook tests, `python scripts/nexus_mcp_benchmark.py --help` runs end-to-end against the renamed extension packages, and `python scripts/validate_skills.py --bundles-only` returns PASS (0 errors, 4 WN-001 carry-over warnings). DF-002 and DF-003 are resolved by the Phase 4.1 extension rename and the Phase 4.3 closeout. DF-001 remains open (deferred to Phase 5 catalog sweep). WN-001 and WN-002 remain as documented v1.3.0 carry-overs scheduled for closeout in Phase 8 sub-task 8.3.

## Open Items

### DF-001 -- `data/skills.json` and `data/SKILL_INDEX.md` regeneration deferred until after Phase 5

**Source phase**: Phase 2, sub-task 2.2.
**Plan reference**: [docs/v2.0.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md) sub-task 2.2 step 4 ("If `make build-catalog` works in this environment, run it and diff the output against the manually-edited files; any drift indicates the source-of-truth is `catalog/`, not `data/`, and the manual edits must be re-applied AFTER the Phase 5 catalog sweep. In that case, defer this sub-task to after Phase 5 and document the deferral here.").
**Reason**: `infrastructure/tools/build_skills_catalog.py` regenerates `data/skills.json` and `data/SKILL_INDEX.md` from `catalog/skills/**/SKILL.md`. The catalog SKILL.md bodies still carry DevAI strings until Phase 5's bulk textual rename. Running `make build-catalog` now would overwrite Phase 2's manual data/ edits with DevAI-named content. The Phase 2 textual edits keep validators and downstream consumers reading the new name during Phases 3-4.
**Suggested next step**: After Phase 5 sub-task 5.1 catalog sweep completes, run `make build-catalog` (or invoke the two build scripts directly under `infrastructure/tools/`) and diff the output against the Phase 2 manual edits. Re-commit the regenerated `data/skills.json` and `data/SKILL_INDEX.md` if they differ. Track as part of Phase 5 stability gate.

### WN-001 -- Pre-existing orphan-bundle warnings carried from v1.1.5 / v1.3.0

**Source phase**: Phase 2, sub-task 2.5 stability gate (re-observed during validator run).
**Plan reference**: [docs/v1.3.0/known-gaps.md](../v1.3.0/known-gaps.md) WN-001 (carry-over). Phase 2.2 step 5 explicitly allows "4 known orphan warnings allowed per WN-001".
**Reason**: `python scripts/validate_skills.py --bundles-only` continues to emit 4 warnings on the framework-specialist bundle: `fastapi-expert/references/dependency-injection-patterns.md`, `nextjs-expert/references/data-fetching-patterns.md`, `react-expert/references/performance-patterns.md`, `react-expert/references/testing-recipes.md`. None of these references are linked from their parent SKILL.md. Carried forward across v1.1.5, v1.2.x, v1.3.0, v1.4.0.
**Suggested next step**: Per the v2.0.0 plan Phase 8 sub-task 8.3, decide at version close whether to close out or re-defer. Tracking options per v1.3.0 WN-001: (a) link each orphan from its parent SKILL.md, (b) inline-and-delete, or (c) leave as documented carry-over.

### WN-002 -- `make` and `shellcheck` unavailable on Windows dev machine; UTF-8 codec workaround

**Source phase**: Phase 2, sub-task 2.5 stability gate (carry-over from v1.3.0 Phase 1 baseline conditions).
**Plan reference**: [docs/v1.3.0/known-gaps.md](../v1.3.0/known-gaps.md) WN-002. The v2.0.0 plan Phase 1 baseline ([docs/v2.0.0/baselines/](baselines/)) documents the same workaround.
**Reason**: `make validate` / `make lint` / `make test` cannot run directly on the Windows 11 + Git Bash environment (`make` and `shellcheck` not on PATH). All validators were invoked via direct Python (`python scripts/validate_skills.py --bundles-only`). Result during Phase 2 close: PASS, 0 errors, 4 warnings (the WN-001 orphans).
**Suggested next step**: Same as v1.3.0 WN-002 -- either patch Makefile inline `python -c` calls to pass `encoding='utf-8'`, or document Windows dev-environment prerequisites. Owner: future hygiene phase.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-002 | End-to-end installer smoke deferred to Phase 4 close | Phase 4 sub-task 4.1 | The three `extensions/nexus-*` directories now exist on disk, so the installer's MCP-server install branch is no longer skipped. The cross-platform installer dry-run prescribed by plan sub-task 8.2 is still owed and will be captured to `docs/v2.0.0/installer-smoke-post.txt` during Phase 8.2; the *Phase 4* deferral specifically is closed. |
| DF-003 | `scripts/devai_mcp_benchmark.py` rename pulled into Phase 3 ahead of plan | Phase 4 sub-task 4.1 + 4.3 | The extension package rename in Phase 4.1 unblocks `python scripts/nexus_mcp_benchmark.py --help`, which now runs end-to-end (verified at Phase 4.3 close). The `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1` rename in 4.3 closes the rest of the Phase 4.3 scope. |

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.0.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
