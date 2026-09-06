# Session History - v2.3.0 (adoption-superpowers) Phase 5: Flaky-test tooling cluster

**Date**: 2026-05-30
**Plan**: [docs/archives/v2/v2.3/plans/adoption-superpowers.md](../../plans/adoption-superpowers.md)
**Phase**: 5 of 6 - Flaky-test tooling cluster (`re-full`)
**Sub-tasks**: T018 (find-polluter.sh + find-polluter.ps1 bisector), T019 (condition-based-waiting-example.ts waitFor helper), T020 (validate + parity + stabilization)
**Outcome**: Two per-skill bundled resources shipped under `flaky-test-detector` (auto-copied by both installers; no installer edit, no `data/` edit). Orphan-bundle audit PASS 0/0 across 237 skills; `.sh`/`.ps1` parity confirmed by live cross-OS smoke (5 cases each, identical). A `nullglob` literal-pattern bug in the `.sh` was caught by the smoke test and fixed in-phase. No new open gap. Ready to advance to Phase 6.

---

## Goal

Ship the two flaky-test tooling items the comparison's Section 5a identified as superpowers tooling Nexus-Hub's `flaky-test-detector` describes but does not bundle: a test-pollution bisector script (`find-polluter`) and a reusable `waitFor` condition-based-waiting helper. Both are `re-full` per the MCP Registry Policy: local code reverse-engineered into a project-agnostic form, no new runtime dependency, no outbound call, no credential. The Phase 3 T011 `references/condition-based-waiting.md` already forward-references both, so this phase fills in the bundled artifacts it points at.

## Steps taken

1. **Pre-implementation review**: read the target `flaky-test-detector/SKILL.md`, the Phase-3 `references/condition-based-waiting.md` (which forward-references both new artifacts), the comparison Section 5a source-pattern descriptions for `find-polluter.sh` and `condition-based-waiting-example.ts`, the bash code-style + security rules under `catalog/rules/bash/`, a representative recent `.sh`/`.ps1` pair (`security-operations/log-threat-hunting/scripts/ioc-log-scan.*`) to match house style, the `validate_skills.py` orphan-bundle audit logic (it searches the basename across SKILL.md + every `references/*.md`), and the Makefile `validate`/`lint` targets. Confirmed Phase 5 is not the final phase (5 of 6), so no release-readiness workflow runs.

2. **T018 - find-polluter bisector** (`catalog/skills/tests-generation/flaky-test-detector/scripts/find-polluter.sh` + `find-polluter.ps1`): a project-agnostic bisector that runs each test file in isolation, removes a watched pollution artifact before each run, and reports the first file whose isolated run re-creates it. Bash interface: `--watch <artifact>` / `--tests <glob>` / `-- <test-cmd...>` with a `{}` per-file placeholder (appended if absent); the command after `--` is run as an argv array (no `eval`, no injection surface). PowerShell sibling: `-Watch` / `-Tests` / `-TestCommand "<cmd>"` (single string split on whitespace into exe + args, with `{}` substituted as one token so a file path with spaces survives). Both: an unsafe-path guard refusing `/`, `.`, `..`, `~`, `$HOME`, `$PWD`, `*` as the watched pattern; a failing test does not abort the bisection (only pollution matters); exit 0 on a successful scan, 2 on a usage/IO error; the polluter path goes to stdout for scriptability while logs go to stderr.

3. **T019 - condition-based-waiting helper** (`catalog/skills/tests-generation/flaky-test-detector/assets/condition-based-waiting-example.ts`): a copy-in `waitFor(probe, description, timeoutMs = 5000, intervalMs = 25)` polling helper (matching the signature the Phase-3 reference shows) plus three domain helpers - `waitForEvent`, `waitForCount`, `waitForState`. Zero runtime dependencies (only `setTimeout`); explicit return types; heavy WHY comments encoding the flakiness footguns it avoids (always an outer deadline, small non-zero interval, swallow probe errors during polling and surface them only in the timeout message, assert AFTER `waitFor` returns not inside the probe). Ends with the flaky-then-stable usage contrast from the reference.

4. **SKILL.md wiring (orphan-bundle rule)**: added a bisector block to `flaky-test-detector/SKILL.md` Step 3 (Diagnose Test Ordering Dependencies) that names both `scripts/find-polluter.sh` and `scripts/find-polluter.ps1` with a bash and a PowerShell invocation example. The `condition-based-waiting-example.ts` basename was already present in SKILL.md (Step 2) and in the Phase-3 reference, so the asset needed no new reference.

5. **T020 - validate + parity + stabilization**: ran the `make validate` equivalent directly (make unavailable on the Windows host), `bash -n` on the script, and live cross-OS smoke tests of both bisector siblings against a throwaway fixture; fixed the bug the smoke test surfaced; updated the plan checkboxes + Phase 5 exit checklist; ran the post-phase documentation sequence.

## Troubleshooting

- **`nullglob` literal-pattern bug in find-polluter.sh (found by the smoke test, fixed in-phase)**: the first smoke run reported the FIRST test file as the polluter regardless of which file actually polluted, and still reported a polluter when none existed. Root cause: with `shopt -s nullglob`, a `--watch` value with no glob metacharacters (e.g. `leaked.lock`) is NOT a filename pattern subject to globbing, so `for p in $watch` always yields the literal whether or not the file exists - making `artifact_exists` always true. Fix: `artifact_exists`, `remove_artifact`, and the test-glob expansion now test real on-disk existence with `[ -e "$p" ]` rather than trusting glob expansion. The `.ps1` was unaffected because it uses existence-based `Test-Path`, which returns false for a non-existent literal or wildcard. Re-ran: all 5 bash cases pass.

- **Harness sandbox blocked a `Remove-Item ... "/"` guard test**: the PowerShell smoke initially passed `-Watch "/"` to exercise the unsafe-path guard, and the harness statically refused the whole command for containing a `Remove-Item` on a protected path (even though the script's guard exits 2 before any removal). Re-ran the guard case with `-Watch $tmp` (which equals `$PWD` after `Push-Location`, also rejected by the guard) - exit 2 with no removal, as intended. The literal-`/` guard is already verified in the bash smoke.

## Assumptions

- `find-polluter` watches a single artifact path/glob without embedded spaces (the bash side word-splits the unquoted `$watch` to allow globbing); a diagnostic-tool limitation, documented in the header.
- The `.ps1` `-TestCommand` is split on whitespace into exe + args, so the command template's own arguments must be whitespace-separable; the `{}` token is substituted as a single argument so the per-file path (which may contain spaces) stays intact. The bash `-- <cmd...>` form takes real shell words and has no such constraint - functional parity, not identical CLI syntax (documented in each header).
- `condition-based-waiting-example.ts` is a copy-in example, not runtime code, so it ships without an automated test (consistent with the plan's "a copy-in example, not a runtime dependency" framing). It is not compiled by this repo.
- `make validate` / `make lint` were invoked as direct `python` / `bash -n` calls because `make` and `shellcheck` are unavailable on this Windows host (same as prior phases).

## Testing results

- **Orphan-bundle audit**: PASS 0 errors / 0 warnings across 237 skills (`--bundles-only`); the scoped run on `flaky-test-detector` also PASS - all three new files (`find-polluter.sh`, `find-polluter.ps1`, `condition-based-waiting-example.ts`) are referenced from SKILL.md / the Phase-3 reference.
- **JSON catalogs**: skills.json OK (231 skills, untouched - no `data/` edit), bundles.json OK (15).
- **CI validators**: no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security all exit 0; the four new/edited files (two scripts, one asset, SKILL.md) are ASCII-clean (verified directly).
- **`bash -n`** on find-polluter.sh: syntax OK.
- **`.sh`/`.ps1` parity (live cross-OS)**: both run against a throwaway 4-file fixture with identical results across 5 cases each - (1) polluter present -> correct file on stdout; (2) no polluter -> empty stdout, exit 0; (3) append mode (no `{}`) -> correct file; (4) unsafe `--watch` guard -> exit 2; (5) no matching test files -> exit 2.
- **Lint**: ShellCheck unavailable on host; covered by `bash -n` + the live runs. Per-skill-script ShellCheck coverage in CI is already tracked under QG-v23-1 (transferred to the v2.4.0 plan), so no new gap.

## Next steps

- Phase 6 (FINAL): deferral record + polish - record the P3 visual-brainstorm-server deferral as a tracked known-gap (T021), update AGENTS.md catalog counts + CHANGELOG `[Unreleased]` (T022), and run the final validation sweep (T023). Phase 6 being the final phase, `/implement-phase` will additionally run the release-readiness workflow (resolve known gaps, verify tests + CI/CD, refactor-docs/project audits, `/update-*` checks, version-bump prep).
- No Phase 5 carryover gap: the bisector bug was fixed in-phase, parity is confirmed, and the `.ts` example needs no test by design.
