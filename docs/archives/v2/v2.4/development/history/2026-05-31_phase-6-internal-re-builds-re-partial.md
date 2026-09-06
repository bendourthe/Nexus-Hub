# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 6: Internal RE Builds (re-partial)

**Date**: 2026-05-31
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 6 of 8 - Internal RE builds, re-partial (A12 local demo-capture, A13 conventional-commit release/changelog)
**Sub-tasks**: T023 (demo-capture skill + capture scripts), T024 (release/changelog script + installer + command wiring + pytest), T025 (testing + stabilization)
**Outcome**: Added a local-only `demo-capture` skill (terminal-recording / GIF / headless-screenshot PR evidence into `docs/demos/`, upload step dropped) with `capture-demo.{py,ps1}`, and a `generate_release_changelog.{py,ps1}` conventional-commit helper (next-semver-bump + Keep-a-Changelog section) wired as an optional accelerator into update-version / generate-changelog and registered in both installers - no release-please Action added. 31 new tests pass; the new skill is registered (245 skills / workflow 36). Live demo-capture eval deferred (DF-v24-6). 1 pre-existing installer test failure surfaced and recorded (BG-v24-1), unrelated to Phase 6.

---

## Goal

Build the two re-partial internal artifacts: keep the local capability and drop the externally-vendored surface. For A12 (demo reel), keep the local capture (terminal recording / GIF / screenshots) and drop the upstream upload/approval/hosting step. For A13 (release automation), build a LOCAL conventional-commit-driven version-bump + changelog script instead of adopting the third-party release-please GitHub Action. Both are fully local; no new outbound call, no new credential, no new runtime dependency.

## Steps taken

1. **Phase 0 - resolve plan / phase**: parsed `6 of v2.4.0 adoption-compound-engineering-plugin.md`; legacy flat layout (`docs/archive/v2/v2.4/plans/`). Phase 6's prerequisite is "None". Phases 1-5 closed. Final-phase detection: false (6 of 8; Phases 7-8 open) - so the Phase-9 release-readiness workflow does NOT run.

2. **Phase 1 - pre-implementation review**: read the closest precedents - the Phase-3 `session-query` skill (script-first skill with `.sh`/`.py`/`.ps1` bundled scripts) and its `extract-session.ps1` (repo PowerShell idioms), the installer `validate_solution_frontmatter` copy blocks in both `installer.sh`/`installer.ps1` (explicit-name copy-step pattern), the `tests/validators/conftest.py` runner fixture, and the `generate-changelog` / `update-version` command bodies (where to wire the helper). Confirmed `make validate` runs only `--bundles-only` + `--quality` + the four CI validators + solution-frontmatter (NOT the default description-length check).

3. **T023 - demo-capture skill**: wrote `catalog/skills/workflow/demo-capture/scripts/capture-demo.py` (stdlib-only: probe/capture modes, tool detection via `shutil.which`, project-type detection, tier selection, graceful degradation) and the `.ps1` sibling (same behavior, `Get-Command` detection, `ConvertTo-Json` output). Wrote `SKILL.md` (118 lines, all six required sections, pushy description with trigger phrases + SKIP clause, local-only/no-upload asserted in body + Common Rationalizations). Registered in all three data files (workflow 35 -> 36; total 244 -> 245). Verified both siblings run (probe + missing-tool capture degradation, exit 0).

4. **T024 - release/changelog helper (lockstep)**: wrote `scripts/generate_release_changelog.py` with importable pure functions (`parse_commit`, `determine_bump`, `bump_version`, `categorize`, `render_changelog_section`) and the git-reading isolated behind `--commits-from` for fixture testing; mirrored it in `generate_release_changelog.ps1`. Registered BOTH siblings as explicit-name copy steps in `installer.sh` AND `installer.ps1`. Wired the helper as an optional accelerator into `catalog/commands/update-version.md` (Step A3) and `catalog/commands/generate-changelog.md` (Phase 2), referenced not replacing the manual flow, with an explicit "NOT a release Action" note. Added `tests/validators/test_generate_release_changelog.py` (20 cases). Did NOT add a release-please GitHub Action.

5. **T025 - stabilization**: ran the validators directly (make unavailable on host), `ruff check` on the new Python, both installer parse checks, and the full pytest suites; added `tests/validators/test_capture_demo.py` (11 cases) so the new `capture-demo.py` is covered; recorded DF-v24-6 (live eval deferred) and BG-v24-1 (pre-existing installer test failure); ran the post-phase documentation sequence.

## Troubleshooting

- **1 pre-existing test failure surfaced**: `catalog/hooks/tests/test_installer_smoke.py::test_installer_ps1_fallback_literal_matches_template` fails because it asserts a hardcoded ``"effortLevel`": `"xhigh`"`` literal in `installer.ps1`, but commit `a6475d8` refactored the installer to seed `effortLevel`/`model` dynamically from the template (the fallback hint now says "Manually copy effortLevel/model/env from $templateFile"). Root-caused as pre-existing (`git show HEAD:scripts/installer.ps1` has no such literal; the Phase-6 diff to `installer.ps1` only adds a copy block). Left unfixed per the in-scope rule; recorded as BG-v24-1.
- **`ruff check` unused variable**: `parse_commit` extracted a `body` local it never used (the BREAKING-CHANGE check scans the full message); removed it. `ruff format` is not repo-enforced (committed scripts also "would reformat"; absent from CI/Makefile) so formatting was left matching the surrounding style.
- **PowerShell `/tmp` invisibility**: the bash tool's `/tmp` fixture path is not visible to Windows PowerShell; re-ran the PS parity smoke against `$env:TEMP`. No functional bug - the `.ps1` output matched the `.py` output exactly (release helper) and behaviorally (capture degradation).

## Assumptions

- A12's upload/approval/hosting surface is the dropped vendor piece (stated in the skill body + the `upload: disabled` field in the script's JSON plan); the skill is local-capture-only and reminds the user to attach the artifact to the PR by hand.
- `docs/demos/` is a consuming-project output dir, not a Nexus-Hub repo artifact, so it is NOT added to `.gitignore` (consistent with the Phase-4 `product-pulse` -> `docs/pulse-reports/` precedent, which was likewise not gitignored).
- The `.ps1` sibling parity for both new scripts is verified by empirical smokes (probe + degradation for capture-demo; fixture output match for the release helper), matching the session-query DF-v24-4 precedent; no dedicated PowerShell test harness exists in the repo.
- `demo-capture`'s pushy >250-char description follows the AGENTS.md combat-undertriggering guidance and matches its five v2.4.0 sibling skills; the `--allow-existing` allowlist reconciliation is deferred to the version bump (folded into WN-v24-1). `make validate` does not run the description-length check, so this is not a gate failure.
- `make` / shellcheck are unavailable on the Windows host, so validators ran directly and shellcheck is N/A (the new scripts are `.py`/`.ps1`, no `.sh`, so the CI shellcheck scope is unaffected); `bash -n` and PowerShell `PSParser` both pass.

## Testing results

- `make validate` equivalent (direct): JSON catalogs OK with all three registries reconciled at **245 skills across 21 categories** (workflow 36 everywhere; marketplace category sum 245; SKILL_INDEX rows + footer 245), orphan-bundle PASS 0/0 across 245 skills (both demo-capture scripts referenced), quality pass 0 errors (neither new skill flagged), four CI validators + solution-frontmatter all exit 0, no-personal-paths exit 0, unicode-safety 0 errors / 1085 warnings (pre-existing compliance-template debt; no Phase-6 file flagged).
- `make lint`: `ruff check` clean on all four new Python files (one unused-variable fix applied); `bash -n scripts/installer.sh` OK; PowerShell `PSParser` clean on `installer.ps1`, `generate_release_changelog.ps1`, `capture-demo.ps1`; shellcheck N/A on host.
- New pytest: `test_generate_release_changelog.py` 20 passed, `test_capture_demo.py` 11 passed.
- Full suites: `tests/validators` + `tests/skills` 115 passed; MCP skill-server 43 passed (consumes the new entry); `catalog/hooks/tests` + `tests/integrations` + `tests/installer` 681 passed / 3 skipped / **1 failed** (BG-v24-1, pre-existing, unrelated to Phase 6).
- **Release-helper dry-run (PASS)**: against real repo history (last tag -> HEAD) with `--current-version 2.3.0` it proposed minor -> 2.4.0 and rendered a scope-bolded Keep-a-Changelog section; a `feat!`/`fix`/`docs`/`chore` fixture correctly resolved to major.
- **Capture-demo degradation (PASS, py + ps1)**: capture mode with a missing browser/recorder returns `captured=[]`, a `skipped` entry with the install hint, and exit 0.

## Deviations

- **BG-v24-1**: a pre-existing installer test (`test_installer_ps1_fallback_literal_matches_template`) fails after commit `a6475d8`'s dynamic-template-seed refactor; left unfixed (out of Phase-6 scope), recorded for Phase 7 / the version bump.
- **DF-v24-6**: the live `skill-eval-loop` trigger run for `demo-capture` was deferred (no model CLI on PATH); a static trigger-surface check was substituted, and the graceful-degradation requirement was verified directly (not deferred).
- No release-please GitHub Action was added (the vendor piece stays unadopted per the comparison Section 9.4); the local helper is referenced, not substituted, into the existing manual flows.
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written.

## Next steps

- Phase 7 (catalog-quality + hygiene remediation) follows: the nine ingested v2.3.0 known-gaps (stocktake remediation, BOM/punctuation/personal-path cleanup, CI shellcheck broadening, code-search extractors).
- Phase 8 T037 should fold in the live `skill-eval-loop` run for `demo-capture` (DF-v24-6) alongside the other deferred live evals (DF-v24-1 through DF-v24-4).
- Phase 7 or the version bump should resolve BG-v24-1 (update the stale installer test to match the dynamic-seed behavior) and the WN-v24-1 count-prose / pushy-description-allowlist reconciliation.
