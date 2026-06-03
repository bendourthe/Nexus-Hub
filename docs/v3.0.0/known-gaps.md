# Known Gaps -- v3.0.0

**Status**: in progress (accumulating across phases; finalized at the v3.0.0 release in Phase 10)
**Last updated**: 2026-06-03 (Phase 6)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for the v3.0.0 `command-consolidation-skill-security` plan. The next version's `/generate-plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 2 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 3 | 0 |
| QG | 0 | 0 |
| **Total** | **5** | **0** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v30-1 | WN | Phase 1 | T004 (stabilization) | Local lint verification was partial on the Windows dev host: `make` and `shellcheck` are not installed, so `make validate` was emulated by invoking each validator directly (all green, including `check_version_sync.py`) and the ShellCheck pass on the new `installer.sh` copy block was deferred to CI. The new block reuses the exact `safe_copy ... true "..."` pattern of its 15 sibling validator-copy blocks, so it is ShellCheck-clean by construction. | Confirm the CI `shellcheck` job is green for this commit on the ubuntu runner; no code change expected. | Low (covered by CI) |
| WN-v30-2 | WN | Phase 2 | T008 (register both skills) | The T008 prompt prescribed regenerating `data/skills.json` + `data/SKILL_INDEX.md` via `infrastructure/tools/build_skills_catalog.py`. Running the generator produced a ~5,500-line diff that materially rewrote existing entries: it splits categories by raw frontmatter casing (e.g. `Developer Experience` vs `developer-experience`, `Research`, `Workflow`), recomputes `long_description`/`size` differently, and reorders entries -- indicating the committed `data/` files are maintained by a newer/different process than this generator. To keep the diff traceable, registration was done by hand (2 skill entries + recomputed `statistics` + 2 `SKILL_INDEX.md` rows + the `orchestration`/`security` `marketplace.json` counts), and the regeneration was reverted. Net effect: `make build-catalog` is currently unsafe to run -- it would clobber curated catalog data. | Reconcile `build_skills_catalog.py` with the committed `data/skills.json` (normalize category casing in source SKILL.md frontmatter, align `long_description`/`size`/ordering, and category counting) so `make build-catalog` reproduces the committed catalog with a no-op diff; OR document that `data/` is hand-maintained and retire/replace the generator. Verify with a no-op regen diff. | Medium (a future `make build-catalog` or `/update` run could corrupt the catalog) |
| DF-v30-1 | DF | Phase 6 | T027 (static analyzers) | The `nexus-skill-scanner` ships the highest-signal patterns for each of the 15 static classes (1-13, 15-16), not the full ~64-pattern surface described in the comparison. This is the deliberate "start with the highest-signal classes and grow the pattern set per release" approach from `comparison-skillspector.md` Section 13. Coverage is sufficient to score the planted-malicious fixture CRITICAL and pass the clean catalog, but individual classes (e.g. memory poisoning, tool misuse, output handling) have a thin pattern set. | Grow the per-class pattern set in subsequent releases, adding eval fixtures per new pattern; prioritize classes by observed catalog/third-party false-negative rate. Class 14 (YARA) and the live OSV.dev lookup are scheduled for Phase 7, not gaps. | Low (by-design incremental coverage; gate + semantic skill compensate) |
| DF-v30-2 | DF | Phase 6 | T027 (taint tracking) | Class 13 taint tracking is a module-scoped over-approximating heuristic: it marks names assigned from a tainted source (os.environ / os.getenv / input / sys.stdin) and flags them reaching a code-exec sink (HIGH) or process-exec sink (MEDIUM). It is flat (not intra-procedural / flow-sensitive), so it can over- or under-approximate across function boundaries. Severities are capped so the heuristic cannot trip the HIGH gate except on the genuinely dangerous input->exec/eval flow (which the catalog has none of). | If false positives/negatives emerge in practice, replace with a flow-sensitive intra-procedural dataflow pass (per-function def-use chains). Add adversarial taint fixtures. | Low (conservative severities; bounded blast radius) |
| WN-v30-3 | WN | Phase 6 | T032 (stabilization) | Local verification on the Windows dev host was partial: `make` and `ruff` are not installed, so `make validate`/`make scan`/`make test` were emulated by invoking each validator and the scanner directly (all green: 38 package tests + 134 repo validator tests, version-sync, supply-chain, workflow-security, bundle audit, and the new catalog scan gate at exit 0), `py_compile` was used in place of `ruff`, and the ShellCheck pass on the two new installer copy blocks was deferred to CI. The new installer blocks reuse the exact `safe_copy ... true "..."` / `Safe-Copy ... -Confirm:$true` pattern of their sibling validator-copy blocks, so they are ShellCheck-clean by construction. | Confirm the CI `validate`, `tests`, and `shellcheck` jobs are green for this commit on the ubuntu runner (which runs `ruff`/`make` equivalents and the editable install + pytest); no code change expected. | Low (covered by CI) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| (none yet) | -- | -- | -- | -- |
