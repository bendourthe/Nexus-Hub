# Known Gaps -- v3.0.0

**Status**: in progress (accumulating across phases; finalized at the v3.0.0 release in Phase 10)
**Last updated**: 2026-06-03 (Phase 3)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.0.0 `command-consolidation-skill-security` plan. The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 2 | 0 |
| QG | 0 | 0 |
| **Total** | **2** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v30-1 | WN | Phase 1 | T004 (stabilization) | Local lint verification was partial on the Windows dev host: `make` and `shellcheck` are not installed, so `make validate` was emulated by invoking each validator directly (all green, including `check_version_sync.py`) and the ShellCheck pass on the new `installer.sh` copy block was deferred to CI. The new block reuses the exact `safe_copy ... true "..."` pattern of its 15 sibling validator-copy blocks, so it is ShellCheck-clean by construction. | Confirm the CI `shellcheck` job is green for this commit on the ubuntu runner; no code change expected. | Low (covered by CI) |
| WN-v30-2 | WN | Phase 2 | T008 (register both skills) | The T008 prompt prescribed regenerating `data/skills.json` + `data/SKILL_INDEX.md` via `infrastructure/tools/build_skills_catalog.py`. Running the generator produced a ~5,500-line diff that materially rewrote existing entries: it splits categories by raw frontmatter casing (e.g. `Developer Experience` vs `developer-experience`, `Research`, `Workflow`), recomputes `long_description`/`size` differently, and reorders entries -- indicating the committed `data/` files are maintained by a newer/different process than this generator. To keep the diff traceable, registration was done by hand (2 skill entries + recomputed `statistics` + 2 `SKILL_INDEX.md` rows + the `orchestration`/`security` `marketplace.json` counts), and the regeneration was reverted. Net effect: `make build-catalog` is currently unsafe to run -- it would clobber curated catalog data. | Reconcile `build_skills_catalog.py` with the committed `data/skills.json` (normalize category casing in source SKILL.md frontmatter, align `long_description`/`size`/ordering, and category counting) so `make build-catalog` reproduces the committed catalog with a no-op diff; OR document that `data/` is hand-maintained and retire/replace the generator. Verify with a no-op regen diff. | Medium (a future `make build-catalog` or `/update` run could corrupt the catalog) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | -- | -- | -- | -- |
