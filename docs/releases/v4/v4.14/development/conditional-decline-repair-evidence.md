# Conditional Decline Repair Evidence

## Scope

The owner approved a separate scoped Nexus-Hub repair on 2026-10-29 so the original Nexus-AI v2.16 run can represent its frozen full-decline outcome. The implementation lives in isolated worktree `C:/nh-decline`, branch `fix/conditional-decline-closeout`, based on `4fabd664a`. The existing dirty checker checkout and original product checkout are preserved. This record proves a tooling repair, not completion of the consumer run.

## Baseline

The [baseline receipt](conditional-decline-baseline.json) records the original installed bytes. Those bytes yielded 13 failures and 17 passes in the relevant newer consumer regression set. The repair was forward-ported onto committed source `4fabd664a`, preserving its consumer fixes; two merge conflicts were reviewed explicitly. No dirty work from the separate checker checkout was imported. The installed scripts and real signed run record remained unchanged throughout source qualification.

## Verification

Final focused qualification passed all 56 cases in 277.07 seconds, including the new decline suite, consumer handoff/workflow, contract ownership and schema projection compatibility. The separate compatibility run passed 298 cases with one skip in 566.98 seconds. It covered approval capture/binding/continuation, ordinary completion predicates, schema compatibility, replay refusal, member ordering and the actual two-member closing flow. That run preceded the final successor refinement; the final 56-case run requalified the affected projection and decline paths. These are split qualification, not a single full repository run. Raw reports and the exact source digests are retained under `evidence/conditional-decline/`.

The successor regression first failed on legitimate later admission, then exposed uncommitted restoration masking. The corrected validator selects the applicable verified successor independently of current file contents and always checks the final baseline against the worktree. Negative cases cover no approved successor, wrong target, red checks and uncommitted restoration. Independent source review approved the corrected delta; it did not rerun suites.

Python 3.11 grammar validation passed for 1032 tracked files. Installer parity passed. The bundle audit passed with zero errors and 66 existing warnings. All 89 decision records validated, and release documentation conventions passed. All five runtime files compiled. The narrow Ruff comparison has 28 diagnostics at both the committed base and current source, with zero introduced diagnostics. The other three local runtime dependencies (`cleanup_merged`, `repo_host`, `run_plan`) match installed text exactly; only line endings differ. `make` is unavailable on this machine; these underlying checks do not imply all Makefile targets ran.

## Preservation

All changes used the official edit guard. An earlier acceptance of this session's own test additions corrected a recording-order mistake after the official diff was inspected; this was not new human consent or a native baseline-adoption receipt. No user edit was overwritten. Existing product checkout edits and the other Hub worktree remain preserved. Historical product guard deviations remain recorded in the consumer evidence.

## Adoption

Source qualification is complete. Pending: local commit, exact backed-up installation of the five existing runtime scripts, fresh installed native verification and genuine capture of the concrete conditional disposition. No runtime installation, disposition capture, consumer archive or final completion is claimed by this record yet. Additional gap migration needs its separate authority.
