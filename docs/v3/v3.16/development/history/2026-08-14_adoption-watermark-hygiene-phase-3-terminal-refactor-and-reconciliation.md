# Session History - v3.16.8 Phase 3: Terminal refactor, reconciliation, CI/CD, release readiness

**Date**: 2026-08-14
**Plan**: [plans/v3.16.8-adoption-watermark-hygiene.md](../../plans/v3.16.8-adoption-watermark-hygiene.md)
**Phase**: 3 of 3 (the terminal phase, so the mandatory 9.0 gate and the release-readiness workflow ran)
**Branch**: `feat/v3.16.8-adoption-watermark-hygiene`
**Status**: COMPLETE. Release-ready, awaiting `/update release`.

## 3.1 Architecture refactor

A genuine no-op, executed rather than skipped, which is what the plan predicted ("expected to be a light pass; it is still executed, not skipped"). Every detector was run and its result recorded rather than assumed.

**Layout**: `docs/v3/v3.16/` is canonical (`comparisons/`, `development/`, `plans/`, plus the two governance files `known-gaps.md` and `docs-cleanup-report.md`). The v3.16.8 plan and its seeding comparison are co-located, satisfying the co-location rule that exists because a plan separated from the comparison that seeded it loses its provenance.

**Caches**: no tracked `__pycache__` or `.pyc`.

**Empty directories**: four exist, all four deliberately left. `.antigravitycli` and `.claude/worktrees` are gitignored local runtime dirs. `docs/v3/v3.17/development/history` and `docs/v3/v3.20/comparisons` are other versions' scaffolding, and v3.17 has ACTIVE work from a parallel session in this same tree, so touching it would be both out of scope and disruptive.

**Stray root artifact**: `pytest-out.log` is gitignored (`*.log`), untracked, dated 2026-05-22, and absent from `MANIFEST.sha256`, so it never ships. Left rather than deleted: it is a local scratch file in the user's working tree, not a repository artifact, and removing someone's local file is not a refactor.

**Deferred-work markers**: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` across every code and instruction file this version changed.

## 3.2 Known-gaps reconciliation

Six items, all dispositioned. 4 closed, 2 carried, **0 release blockers**.

| Item | Verdict | Basis |
|---|---|---|
| `NI-1` VS16 deviation | CLOSED (by design) | Deliberate, measured, maintainer-approved, documented in four places. No outstanding work. |
| `WN-1` CJK ideographic variation | CARRIED (accepted) | Zero instances; warning-only unless `--strict`; named revisit trigger (extend to `Lo` bases if CJK content enters the tree). |
| `MT-1` Windows-skipped mode test | CLOSED | CI coverage VERIFIED, not assumed: `ci.yml` line 497 runs `tests/validators` on Linux, line 576 on Windows. The mode assertion executes where file modes exist. |
| `BG-1` bootstrap `tar` failure | CARRIED | Pre-existing and environmental; already root-caused as v3.16.0 `BG-1` (Git Bash MSYS `tar` ahead of the system binary). |
| `BG-2` stale model-map date | CLOSED | Fixed by deriving the expectation from the snapshot's `verified_as_of`. |
| `QG-1` combined Phases 1+2 commit | CLOSED | Historical fact, recorded so the combined commit reads as deliberate. Nothing corrective. |

### The advisory model-prompting staleness check

Verdict **DRIFTED**, which is an acceptable terminal outcome. UNKNOWN would not have been, and getting a real verdict required enumerating the roster first: the check takes model ids as arguments and answers UNKNOWN when given none, so running it bare "passes" while verifying nothing.

The roster came from `last-known-model-map.json` as refreshed from live first-party documentation earlier today (commit `b29a0ffa`, sources cited in the plan), passed as 15 explicit ids. The layer was last verified 2026-07-27 against a roster that no longer matches: 12 live-but-unprofiled ids, 1 recorded-but-not-live.

That single removal is an artifact worth naming rather than acting on: `claude-haiku-4-5-20251001` and the map's `claude-haiku-4-5` are the same model, the dated id versus its alias. Comparing two artifacts that spell the id differently will report this removal on every future run until one side adopts the other's form. The 12 additions are real.

Per the step's contract this is ADVISORY. It did not block, the freshness marker was NOT re-stamped (only a real research run may write it, and re-stamping here would fake currency), and the follow-up is `/tune-prompting` on its own schedule.

## 3.3 CI/CD

Verified, no change required, and the verification was against the workflow rather than against the rule.

**Already optimized**: `concurrency` with `cancel-in-progress` (line 81), pip caching on both Python jobs (97, 475), and a `paths` filter of `**` minus `docs/**` carrying deliberate re-inclusions for validator-input docs.

**Coverage of this plan's surfaces**: `tests/validators` on the Linux (497) and Windows (576) legs covers the validator and its 31 new tests; `tests/skills` (500) covers the edited command and skill prose; `tests/plans` (507) covers the model-map fix. The repo-wide detect step calls the validator with no arguments and is untouched by every change in this plan.

**Deliberately NOT added**: a repo-wide `--strict` CI gate. It would fail on the 1042 grandfathered warnings, and strictness belongs to the pre-commit release gate over release-cycle artifacts, which is exactly where Phase 2 put it. Recording the non-addition so a later reader does not "complete" the work by adding it.

## 3.4 Verification

| Gate | Result |
|---|---|
| Validate battery (14 gates, run directly since `make` is unavailable) | all green |
| `validate_unicode_safety` (repo-wide detect) | 0 errors, 1042 warnings |
| Release hygiene gate (artifacts, detect) | exit 0 |
| Compression accuracy-regression gate | PASSED (CCR 100.0%, signatures 100.0%, reduction 45.8%) |
| `tests/integrations` + `tests/installer` | 947 passed, 17 skipped, 1 failed (`BG-1`) |
| `tests/plans` + `tests/validators` | 698 passed, 1 skipped |
| Full `tests/` + `catalog/hooks/tests/` | see the closing run recorded in the phase report |

The `tests/integrations` + `tests/installer` result closes the one evidence gap Phase 2 left open: that leg had never reported before the Phase 2 commit, and it is now confirmed green apart from the known pre-existing `BG-1`.

## Release readiness

- **9A known gaps**: reconciled above. 0 release blockers.
- **9B tests and CI/CD**: verified above.
- **9C-9E**: handed off to `/update release`. No tag or push was created here, by design.

**Hold conditions**: none active. The one failing test in the whole suite is `BG-1`, pre-existing, environmental, confined to a Windows host whose PATH resolves `tar` to the Git Bash binary, and unaffected by CI.

**Version note for `/update release`**: this branch's work is currently under `## [Unreleased]` in `CHANGELOG.md`. The release step owns the bump to 3.16.8 across every version-carrying surface via `check_version_sync.py`, the manifest regeneration, and the tag.
