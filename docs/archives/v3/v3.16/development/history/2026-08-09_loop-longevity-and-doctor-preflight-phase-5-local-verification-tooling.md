# Session History - v3.16.2 Phase 5: Local verification tooling

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 5 of 6 (not the final phase; Phase 6 is the terminal refactor phase)
**Branch**: `develop`
**Prerequisite**: Phase 2 (satisfied, committed as `b64f29c2`)
**Outcome**: Complete. Quality gate GO.

## Goal

Add the preflight Nexus-Hub has never had, so a user finds out that an install did not land where the contract promised before they discover it as silent non-coverage.

## What already existed (checked before building)

The plan's premise needed correcting against the codebase. `scripts/lib/integrations/runner.py` already had:

- `cmd_verify` - reads the SAME `install_verify` block, detects platforms, checks each surface, prints PASS / NEEDS-ACTION with remediation. **Deliberately always exits 0**, with a comment warning future editors not to "fix" that, because it must never fail an install.
- `cmd_doctor` - manifest-based content-drift detection (missing / drifted hashes against a recorded install manifest). Unrelated to the read-contract.

So roughly 90% of the surface-checking logic existed, and the genuine gap was narrow: no installer-level `doctor` subcommand (which is why the `update.md` reference was NI-1), and nothing combining contract checks with a failing exit code.

This was surfaced as an explicit choice rather than resolved unilaterally. **The user chose full logic in both shells**, over a thin dispatch to shared Python. Parity is therefore asserted by test rather than guaranteed by construction, which raised the bar on the tests - and is where the phase's main finding came from.

## Sub-tasks completed

### 5.1 - `nexus-hub doctor` (bash)

`run_doctor()` and four helpers in `scripts/installer.sh`, plus the `doctor)` argument case, a self-contained dispatch, and usage text.

Three states kept distinct, because collapsing them is what makes a doctor untrustworthy: **SKIP** (platform absent, not a failure), **PASS** (present, every surface there), **FAIL** (present, a promised surface missing or empty). An existing-but-empty directory is a FAILED surface: an empty skills dir surfaces nothing to the platform that reads it.

Exit codes: 0 all complete, 1 any FAIL, **2 the contract could not be read or parsed**. That last one is the deliberate divergence from `runner.py`'s fail-soft helper. Fail-soft suits an advisory post-install note; for a preflight, reporting CLEAR because the contract was unreadable is the worst possible output. An unknown surface `kind` also fails rather than passing, so a contract addition cannot silently widen the set of things reported CLEAR on an older installer.

Two hard constraints, both stated in comments so a later edit does not quietly break them: **no network call of any kind** (what keeps it `re-full` under the MCP Registry Policy), and **read-only** - `--repair` prints the remediation commands and explicitly does not execute them.

Only the JSON tokenization is delegated (jq when present, else Python, which the `init` / `--check` / `--print-config` subcommands already require). Every decision - path resolution, surface evaluation, state classification, exit code - is made in the shell. When NEITHER tokenizer is available it exits 2 rather than skipping: silently allowing is how `secret-scan.sh` became inert on a jq-less host (BG-2, found in Phase 3), and a preflight repeating that defect would be worse than no preflight.

`NEXUS_DOCTOR_CONTRACT` was added as an explicit override. Without it the unreadable-contract path is untestable, because `REPO_ROOT` is derived from the script location and a test cannot steer the lookup. It is honored even when the file is absent, deliberately - an override that fell back to the repo copy would make the fail-loud path unreachable.

### 5.2 - The PowerShell sibling

`Invoke-NexusDoctor` and three helpers in `scripts/installer.ps1`, dispatched before the existing read-only subcommand block.

Native equivalents rather than emulated shell mechanics, per the guidance the hook-sibling work established: `ConvertFrom-Json` instead of a jq dependency, `[System.IO.File]::ReadAllText` for the contains-check, `[Console]::Error.WriteLine` for stderr. The UTF8Encoding/BOM hazard behind the v3.15.6 divergence cannot arise here, and the note says why: a read-only command has no encoding surface.

Both backfilled incident notes were read first, as sub-task 5.2 requires, and their durable fixes treated as requirements: the file must parse under Windows PowerShell 5.1 (verified locally on 5.1.26100.8875), and exit-code parity must be asserted by test rather than assumed.

### 5.3 - Release-capability documentation validator

`scripts/check_release_capability_docs.py`, stdlib only, modeled on the repo's other internal guards. Asserts the five elements per `--surface`, supports `--expect-no-optional-capability-changes`, and treats silence as a failure for that mode - "checked and none applied" must be distinguishable from "never checked".

**Ships ADVISORY** (reports and exits 0), per the comparison's sequencing recommendation; `--strict` is the flip a future promotion turns on. Detection is marker-based rather than prose-inferring, and the docstring says why: a checker that guessed at free text would produce confident false passes, and a false CLEAR is the exact failure the gate exists to prevent.

Classified into `DEV_ONLY_SCRIPTS` with a justification following the five existing precedents - a repo-internal guard, no installer copy step in either installer. It is NOT added to `make validate`, because it requires a release-notes file argument; `/update release` is its caller, and governance step 6 now names the real invocation (closing DF-1).

### 5.4 - Tests and stabilization

`tests/installer/test_doctor_parity.py` - a `doctor` fixture parametrized over both implementations, so every behavioral assertion doubles as a parity assertion. Covers the four minimum cases the plan names (absent, complete, missing surface, malformed contract) plus missing contract, empty `install_verify`, unknown argument, unknown surface kind, `--repair` read-only-ness, remediation text, an unconditional AST-parse backstop, and one explicit cross-implementation exit-code comparison.

`tests/validators/test_check_release_capability_docs.py` - 15 tests including a parametrized case per missing element and both advisory / strict postures.

**CI collection was verified, not assumed** (v3.15.8 QG-2): `ci.yml` enumerates test directories by name, and both `tests/installer` and `tests/validators` are already listed, so no new directory was created and no `ci.yml` collection edit was needed. Confirmed by reading the `tests` job.

## Test results

| Suite | Result |
|-------|--------|
| `tests/installer` | **305 passed** (was 283), 16 skipped, 1 failed (inherited BG-1) |
| `tests/installer/test_doctor_parity.py` | 22 passed (11 assertions x 2 implementations) |
| `tests/validators` | **569 passed** (was 554) |
| `tests/skills` | 509 passed, 3 skipped |
| `catalog/hooks/tests/test_installer_smoke.py` | 33 passed |
| ShellCheck (`installer.sh`, `install.sh`) | **Clean** |
| `installer.ps1` AST parse, Windows PowerShell 5.1 | OK |
| `validate` guards (7, run individually) | All pass |

Live verification on this machine: both implementations exit 1 and produce **byte-identical verdict lines**, confirmed by diff.

## The two findings

### BG-3: the parity requirement paid for itself on first use

The first cross-implementation run produced **disagreeing verdicts with matching exit codes** - Bash 5 complete / 5 incomplete, PowerShell 9 / 1, same machine. Matching exit codes are what makes this insidious: an exit-code-only parity test would have passed.

Cause: the Bash flattener's Python fallback emits CRLF on a Windows host, so the last tab-separated field arrived carrying a trailing `\r`. Only `file_contains` surfaces read that final `needle` column, so only they broke.

This is shape S-1 failure mode 2 (runs but disagrees) from `docs/incidents/shapes.md`, reproduced within hours of the notes describing it being written, and caught on the first application of the durable fixes those notes name. Fixed by stripping the CR, with the reasoning recorded inline.

### QG-2: the v3.11.0 gate did not cover the file most exposed to it

While deciding where to add the AST assertion, I found `scripts/installer.ps1` had **never been AST-parsed in CI**. The unconditional gate globs `catalog/hooks` only; the `bootstrap` job parses only the root `install.ps1`. The largest PowerShell file in the repo, and the one this phase modifies, was covered by neither. Extended the gate to `catalog/hooks/*.ps1`, `scripts/*.ps1`, and `install.ps1`.

## Deviations

1. **`NEXUS_DOCTOR_CONTRACT` is a test seam not named in the plan.** Added because the plan requires proving the malformed-contract path and `REPO_ROOT` is script-derived, making that path otherwise unreachable from a test.
2. **`--repair` prints rather than executes.** Recorded as NI-3 with the bound stated.
3. **The validator is not in `make validate`.** It needs a release-notes argument; `/update release` is its caller.
4. **CI's AST gate was widened beyond the new code.** Sub-task 5.4 asked for an assertion covering the new `.ps1` code; covering only the new lines while leaving the file unparsed would have satisfied the words and missed the point.
5. **SC2088 was designed out rather than suppressed.** ShellCheck flagged the tilde-in-quotes case pattern (a false positive - the tilde is contract data). The resolver was rewritten with prefix-stripping, since CI runs ShellCheck at `--severity=warning` over this file.

## Post-phase steps

| Step | Result |
|------|--------|
| 8.1 gitignore | 0 patterns added |
| 8.2 Test review | Both new scripts have dedicated suites; both installers are covered by the parity fixture and the smoke tests |
| 8.3 CI/CD | Changed: AST-parse gate widened to `scripts/*.ps1` + `install.ps1`. Collection verified: both test dirs already enumerated, no new directory created |
| 8.4 Known gaps | BG-3, QG-2, NI-3 raised; BG-3, QG-2, NI-1, DF-1, WN-2 closed; summary and Last-updated refreshed |
| 8.5 Docs cleanup audit | No-op. No documentation file added, moved, or renamed |
| 8.6 Devlog | Entry added |
| 8.7 Docs | `catalog/commands/update.md` governance step 6 now names the validator's real invocation |
| 8.8 Session history | This file |

## Next steps

Phase 6, the terminal phase: architecture refactor, known-gaps reconciliation, and CI/CD. It inherits MT-1 (the only substantive open item), NI-2 (the `observability-setup` size decision), NI-3 and BG-2 (both bounded), and its own 6.2 instruction to record the six declined candidates and the incident-archive residual risk. Its 6.4 note that `nexus-hub doctor` is the capability gate's first real test case is now literally true: the subcommand exists, and it is an opt-in surface the release notes must teach.
