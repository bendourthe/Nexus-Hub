# Session History - v3.16.7 Phase 4: Terminal refactor, reconciliation, CI/CD, release readiness

**Date**: 2026-08-13
**Plan**: [plans/v3.16.7-presentify-first-shot-hardening.md](../../plans/v3.16.7-presentify-first-shot-hardening.md)
**Phase**: 4 of 4 (the terminal phase, so the mandatory 9.0 gate and the release-readiness workflow ran)
**Branch**: `feat/v3.16.7-presentify-first-shot-hardening`
**Status**: COMPLETE. Release-ready, awaiting `/update release`.

## 4.1 Terminal refactor and audit

The plan required three things be VERIFIED and recorded rather than assumed. All three were checked against the code, not against the rule as written.

**Orphan-bundle rule**: all 21 files under the presentify skill's `scripts/` / `references/` / `assets/` are referenced from `SKILL.md`, the new `content-intent.md` included. `validate_skills.py --bundles-only` PASS across 271 skills with 0 warnings.

**Installer registration is genuinely not required.** Rather than trusting the AGENTS.md rule, the code path was read. Neither installer names any per-skill bundled file (grep for `fit_map_projection` / `content-intent` / `visual_qa_score` returns 0 in both `installer.sh` and `installer.ps1`). Distribution runs through the integration registry: `scripts/lib/integrations/base.py` line 804 calls `_copy_tree(catalog/skills, ...)`, which is `shutil.copytree(src, dst, dirs_exist_ok=True)`. The whole tree ships; only a repo-level `scripts/<name>.py` needs the explicit-name copy step. `test_installer_smoke.py`: 33 passed.

**Refactor detectors**: no tracked `__pycache__`; every root file is a legitimate governance artifact or the documented `install.sh` bootstrap. Four empty directories exist; the two under `docs/` (`v3.17/development/history`, `v3.20/comparisons`) are other versions' scaffolding and were deliberately left alone as outside this release's scope.

**WN-2 closed here.** The two pre-existing `PLW1510` ruff findings in the Phase 1 test module were fixed (`check=False`), which is in scope for a terminal cleanliness pass in a way it was not during Phase 3. That module now reports 0 findings.

## 4.2 The WN-1 manifest defect, root-caused

This item had been carried since v3.16.5 and had already caused a shipped defect, so it got a real diagnosis rather than a third re-carry.

**Confirmed empirically.** This repo sets `core.autocrlf=true`, and `.gitattributes` sets `* text=auto` plus `*.md text=auto`. A byte probe of `references/visual-qa-rubric.md` showed 141 CRLF and 0 bare LF on disk. `generate_manifest.py` hashed those working-tree bytes, so a manifest generated here disagreed with the released tarball on essentially every text file. v3.16.5 shipped exactly that (`nexus-hub verify` would have reported ~520 spurious mismatches); v3.16.6 regenerated the data from a clean tree but left the generator, leaving the defect one Windows release away from returning.

**Three options were put to the maintainer**, because the choice changes a user-facing verification contract and `AGENTS.md` puts release tooling under "ask first". The decision was to hash git blob bytes.

**Implemented**: `compute_manifest()` now reads the index via `git ls-files -s -z` and one batched `git cat-file --batch`, sha256ing each blob payload. A single batch was used deliberately; a process per file would be ~1200 spawns on this catalog. Untracked covered files and any non-git tree (an installed tree, an exported tarball) fall back to file bytes exactly as before.

**Why the blob rather than newline normalization**: the tarball IS the committed blobs, so hashing them makes the manifest correct by construction instead of correct by a text-detection heuristic, and it leaves `sha256sum -c` semantics and `verify_install.py` untouched.

**Proven, not asserted.** A direct probe showed the manifest entry for `visual-qa-rubric.md` equals `sha256(git show :<path>)` (what a tarball install has) and differs from `sha256(disk bytes)` (what the old generator produced). Both halves matter: matching the blob is the fix, and differing from disk is the proof the old path was wrong.

**Residual boundary, stated rather than left to be discovered.** Because the index is the source, a tracked file with unstaged edits is hashed as its staged form, so `main()` now warns and names the dirty covered paths. Separately, a user installing from a Windows git clone with autocrlf would still see mismatches; the supported install path is the tarball.

**Tests**: 4 regression tests in `tests/validators/test_verify_install.py` build a real repo with `core.autocrlf=true`, commit LF content, rewrite the working tree as CRLF, and assert the manifest matches the LF blob and NOT the CRLF disk bytes, plus untracked fallback, non-git-tree fallback, and the dirty-path warning.

## CI/CD verification

Every one of the 16 files changed across `develop..HEAD` is covered, checked file by file rather than by assumption. `catalog/**`, `tests/skills/**`, `scripts/**`, and `CHANGELOG.md` reach `ci.yml` (whose `paths` is `**` minus `docs/**`, with documented re-inclusions); the presentify surfaces additionally reach `presentify-extractor.yml`; `docs/**` reaches `doc-colocation.yml`. The session-history files sit deliberately outside `ci.yml`'s re-included docs patterns, which is the documented intent. No workflow edit was needed. The presentify workflow already carries path filters, concurrency cancel-in-progress, pip caching, and a merge-gated render job, so the optimization pass was a no-op.

## Results and one instructive test failure

**Full battery: 3383 passed, 53 skipped, 0 failed** (37m27s), run natively.

Getting there was itself worth recording. Run through the Bash tool, `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` failed with `/usr/bin/tar: Child returned status 128`. Stashing showed it failed identically on the baseline, so it was not this phase's doing. The cause is that Git Bash puts GNU `tar` on PATH ahead of Windows `bsdtar`, and PowerShell inherits that environment; the same module passes 5/4-skipped when pytest is launched natively. Classified ENV, no repo defect, and CI runs on clean runners. The lesson is that a Windows-targeting installer test must be run in the shell it targets, or the harness invents a failure.

**Validators** (all native): bundle audit PASS (271 skills, 0 warnings); unicode-safety 0 errors with no finding in any changed file; trigger-eval gate PASS; version sync matches 3.16.6 across every surface; platform read-contract OK for v3.16.6.

**Lint**: the presentify test module went 2 findings to 0. `generate_manifest.py` and `test_verify_install.py` carry `UP006` / `UP035` advisories because the new code uses the modules' existing `typing.List` / `Dict` / `Tuple` convention. Ruff is not a CI gate here and no `[tool.ruff]` config exists, so these are advisory; recorded as `WN-3` rather than fixed, because modernizing only the new functions would leave one module written two ways and modernizing the whole module is an out-of-scope refactor of release-critical tooling during a release phase.

## Known-gaps reconciliation

Final state: **3 open, 6 closed.** Open are `NI-2` (Gates A/B/E are agent behavior, deliberately with no deterministic checker, by the same reasoning the maintainer applied to rubric criterion 10), `NI-3` (composition probes specified inline like the existing probes, extract the whole set at once if ever found skipped), and `WN-3` (accepted style consistency). Closed are `BG-1`, `DF-1`, `DF-2`, `NI-1`, `WN-1`, and `WN-2`. **No release blocker remains.**

## Release readiness and the handoff

Definition of Done: all six items met. Every phase shipped, the full suites and validator battery are green, and the gap log is reconciled with a recomputed summary.

**Capability-usage gate**: satisfied with an explicit no-change declaration. This release introduces no new opt-in capability, installer flag, env-var-gated surface, or managed skill. The content-intent layer, the composition rules, and the QA gates are all authoring doctrine inside an existing skill, reached by the existing `/presentify` command with no new activation mechanism, no new authority, and nothing to disable. The `generate_manifest.py` change alters no interface: same CLI, same output format, same `nexus-hub verify` contract.

**Left for `/update release`** (this phase created no tag and pushed nothing):

1. The version bump 3.16.6 -> 3.16.7 across every version-carrying surface, gated by `check_version_sync.py`.
2. The changelog finalize.
3. **Re-verify and re-stamp the platform read-contract for v3.16.7.** It currently reads OK for v3.16.6 and hard-gates on the version being cut, so this is a real gate, not a formality.
4. Regenerate `MANIFEST.sha256`. Worth doing deliberately this cycle: it is the first regeneration under the new blob-hashing generator, so it is also the end-to-end proof of the WN-1 fix. Stage the release changes BEFORE generating, or the new dirty-path warning will (correctly) fire.
5. The `develop` -> `main` merge, the tag, and the GitHub Release.

## Next steps

Run `/update release`. Note that a concurrent session has untracked v3.16.8 artifacts in this working tree (`docs/v3/v3.16/comparisons/v3.16.8-comparison-watermark-hygiene-and-harness-engineering.md` and `docs/v3/v3.16/plans/v3.16.8-adoption-watermark-hygiene.md`); they were deliberately left unstaged throughout both phases, and the release flow must not sweep them in. That is the `DF-2` hazard this same plan already recorded once.
