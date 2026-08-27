# Session History - v3.16.2 Phase 6: Architecture refactor, known-gaps reconciliation, and CI/CD

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 6 of 6 - **TERMINAL PHASE**
**Branch**: `develop` (not pushed)
**Outcome**: Complete. Quality gate GO. Release readiness handed to `/update release`; **nothing tagged, nothing pushed**.

## Final-phase detection

`is_final_phase = true`, from all five signals rather than the invocation alone: Phase 6 is numerically last AND last by document order; its title matches the v3.11.0 terminal-phase heuristic exactly ("Architecture Refactor, Known-Gaps Reconciliation, and CI/CD"); all five prior phases have session-history files and commits (`4746bdcc`, `b64f29c2`, `5c8344cb`, `53866205`, `8b092bf2`); no `Final-Phase:` marker contradicts it; and its own exit checklist ends in the release handoff.

## Sub-tasks completed

### 6.1 - Architecture refactor

Audited; **nothing needed to move**. Recording what was checked matters as much as the verdict, because "the layout is fine" is otherwise indistinguishable from "the layout was not looked at".

| Check | Result |
|---|---|
| Legacy `docs/versions/v*/v*/` tree | Absent |
| Flat `docs/<vSEMVER>/plans/` duplicates | None; every plan is canonical |
| Stray comparison reports outside `comparisons/` | None. Three filename matches inspected and confirmed false positives |
| Empty directories | Five, **all gitignored**. Nothing tracked to clean |
| Session histories | All five prior phases present |

**`docs/incidents/` placement ratified and the reasoning recorded**, as 6.1 explicitly required. It sits at the docs ROOT because an incident is cross-version by nature: both backfilled notes span multiple releases, and filing either under one version directory would bury a lesson that applies to all of them. It also matches the existing docs-root convention for cross-version concerns (`policy/`, `security/`, `specs/`, `git/`). Only per-release artifacts belong under a version directory.

**One reference repaired.** The plan's own header declared `**Slug**: adoption-loopx` and `**Filename**: v3.16.2-adoption-loopx.md`, naming a file that does not exist. Corrected. This is the plan-metadata half of the drift class the v3.14.2 comparison-versioning work addressed, found by reading the artifact being executed rather than by a validator.

### 6.2 - Known-gaps reconciliation

Every item across six phases dispositioned: **6 closed, 5 carried, 0 release blockers.**

Closed: QG-1 (incidents path filter), QG-2 (installer.ps1 AST gate), BG-3 (doctor CR divergence), NI-1 (doctor now exists), DF-1 (capability validator built), WN-2 (shellcheck-availability correction).

Carried, each with a stated reason: MT-1 (loop-schema concepts still lack mechanical assertion; the duplicated `gates` block is the concrete drift risk), NI-2 (two skills over the 500-line target, under the 800 cap), NI-3 (`--repair` prints rather than executes, deliberate), BG-2 (`secret-scan.sh` fails open without `jq`, pre-existing and bounded), and the environmental WN-1 / BG-1.

Also recorded, per 6.2's explicit instruction: **the six declined candidates** with their reasons (control-plane runtime, benchmark adapters, dashboard SPA, Lark extension, per-skill agent sidecars, single-sentence descriptions), plus the one candidate that was verified-and-dropped rather than declined on principle (LoopX's CI hardening, already complete across all nine workflows).

**The residual risk was assessed rather than restated.** The comparison warned the incident archive could become a directory nobody reads. The Durable-fix control held mechanically (a guard that fails an unlinked fix, wired into `make validate` and CI, 12 tests in both directions), but the stronger evidence is behavioral: within the same cycle, shape S-1 from those two notes **caught two live defects** (BG-3 and QG-2). An archive whose shapes are catching defects days after being written is not a graveyard. Re-assess after a cycle in which nobody adds a note.

### 6.3 - CI/CD create/update/optimize

Reviewed; already at the optimized contract, and this cycle's additions were made in the phases that earned them rather than deferred here.

- **Coverage**: skill and schema edits reach CI via the `'**'` path filter (catalog is outside `docs/`); both new scripts are covered by test suites in enumerated directories; `docs/incidents/**` was re-included in Phase 3 behind the guard that justifies it; the AST-parse gate was widened in Phase 5 to `scripts/*.ps1` and the root bootstrap.
- **Optimization**: path filters, workflow-level `concurrency` cancel-in-progress, pip caching, least-privilege `permissions`, and `timeout-minutes` on all seven jobs (verified programmatically). Expensive Windows legs already gated.
- **Both standing constraints respected and unchanged**: the skill gate stays on `--bundles-only` (v3.14.2 WN-1), and **QG-2 was verified empirically** - both Phase 5 test files live in `tests/installer` and `tests/validators`, both explicitly enumerated in `ci.yml`, so collection actually happens. No new test directory was created, which is the cheapest way to satisfy that constraint.

### 6.4 - Testing and stabilization

## Test results

| Check | Result |
|---|---|
| `make validate` guards (15, run individually) | **All pass** |
| `tests/skills` | 509 passed, 3 skipped |
| `tests/validators` | 569 passed |
| `tests/workflows` | 91 passed |
| `tests/plans` | 91 passed |
| `tests/installer` + `tests/integrations` | see run below |
| ShellCheck: both installers | Clean |
| ShellCheck: every `catalog/**/*.sh` | Clean |
| AST parse: every `.ps1` in `scripts/` + `catalog/hooks/` | OK on Windows PowerShell 5.1 |
| Compression accuracy-regression evals | Pass |

**Catalog unchanged**: 271 skills in `data/skills.json` and 271 on-disk `SKILL.md` files - consistent with each other and with the pre-cycle count. `data/` is untouched across the entire six-phase range, which is the mechanical proof that no frontmatter changed anywhere and therefore that no `skills.json` sync was required. `check_base_template_parity.py` passes, as required after the `AGENTS.md` edits in Phases 2 and 4.

## Release readiness (Phase 9)

- **9.0 gate**: refactor (6.1), known-gaps reconciliation (6.2), and CI/CD (6.3) all run. The advisory model-prompting-profile staleness step was run via its structural sibling; `verify_model_prompting_profiles.py` passes and `check_model_prompting_freshness.py` is deliberately NOT wired into `make validate` or CI, which is the documented advisory/blocking split.
- **9A**: known gaps resolved and dispositioned; no release blocker remains.
- **9B**: test and CI surfaces verified above; both new scripts have dedicated suites in CI-enumerated directories.
- **9C-9E**: **handed to `/update release`, not performed here.** No version bump, no changelog finalization, no tag, no push, no GitHub Release. This skill never creates a tag or pushes automatically.

**The capability usage gate now applies to this very release.** `nexus-hub doctor` is an opt-in surface this plan adds, making it the gate's first real test case exactly as sub-task 6.4 predicted. When `/update release` runs, its notes must carry all five elements for `doctor`: activation (`bash scripts/installer.sh doctor` / `pwsh scripts/installer.ps1 doctor`), validation (the command is its own readback; exit 0/1/2 is the signal), rollback (read-only, so there is nothing to undo - and saying that IS the rollback statement), the authority boundary (it verifies surfaces and **changes nothing**; `--repair` prints and does not execute; it grants no new access and makes no network call), and a documentation link. `python scripts/check_release_capability_docs.py <notes> --surface doctor` can assert that mechanically, advisory-first.

## Deviations

1. **NI-2 was carried rather than fixed.** Splitting `observability-setup` is the right next-touch action but the wrong terminal-phase action; restructuring a skill nothing in this plan required changing, under a release gate, trades a real risk for a cosmetic number.
2. **The plan file itself was edited.** Only its stale `Slug` / `Filename` metadata, which named a nonexistent file. Repairing a broken self-reference is inside 6.1's "repair every reference" mandate.

## Next steps

Run `/update release` when ready. It owns the version bump (via `check_version_sync.py`), changelog, refactor pass, manifest regeneration, commit, `develop` -> `main` merge, tag, push, and GitHub Release publish, each behind its own confirmation gate. Note that a release merge tip means `--no-ff` rather than `--ff-only`.

Highest-value follow-on work, in order: **BG-2** (a security guard that fails open deserves a dedicated fix), **MT-1** (assert the loop-schema concepts, starting with the duplicated `gates` block), then **NI-2** (split `observability-setup` into `references/`).
