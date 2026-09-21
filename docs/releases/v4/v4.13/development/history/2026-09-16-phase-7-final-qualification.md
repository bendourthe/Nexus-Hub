# Session History -- Phase 7: architecture, reconciliation, CI/CD, and final qualification

**Date**: 2026-09-16
**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 7 of 7 (T025-T034), the final phase
**Branch**: `feat/v4.13.0-evidence-driven-agent-improvement`
**Evidence**: [last-phase-evidence.md](../last-phase-evidence.md)

## What this phase was for

Phase 7 is where a plan stops trusting its own checkboxes. Ten duties, each of which must quote the command or scan that produced it, and two of which are performed by reviewers who did not write the code.

The outcome that matters: the independent reviews found four real defects in work the previous six phases had already declared complete and evidenced, and one of them was a false confidence claim inside an evidence file.

## Steps taken

1. **Architecture refactor** (T025): empty-directory, orphan and docs-layout scans. No finding inside this plan's artifact set. The v4.7-v4.10 retention backlog was reported with its owner rather than archived opportunistically.
2. **Known-gaps reconciliation** (T026): 42 ledgers globbed, each open item given an explicit touched-or-not verdict.
3. **Living docs** (T027): handbook build receipts recomputed from disk.
4. **Git hygiene** (T028): branch and repository-settings report, nothing deleted.
5. **CI/CD reconciliation** (T029): thirteen canonical fields compared against the pipeline, plus cross-installer parity and platform-contract verification in the same pass. No pipeline change proposed.
6. **Tier 3 deep pass** (T030): the `functional-verification` runbook, including its adversarial and convergence steps.
7. **Goal-vs-codebase review** (T031): an independent reviewer against the Goal's six elements and three exclusions.
8. **Human testing suggestions** (T032), **full local gate** (T033), **publication** (T034).

## Troubleshooting

### A freshness check that compared nothing

The first handbook staleness check printed "0 stale" for both handbooks. It was reading receipt keys named `inputs` and `input_hashes`; the receipts actually use `sources` and `build`. Every lookup returned `None`, every comparison was skipped, and the result looked clean with zero evidence behind it.

Caught by asking how many hashes had actually been compared, which is a different question from how many were stale. The rewritten check prints the count of comparisons alongside the count of failures, because "0 stale" and "0 compared" are indistinguishable otherwise. Real result: 14 hashes per handbook, 0 stale, outputs matching their receipts.

### Controls that asserted a property of `str.replace`

Both independent reviewers found the same thing. Seven document guards followed this shape:

```python
mutated = document.replace(needle, "")
assert needle not in mutated
```

That assertion is true for every needle, present or absent. It tests `str.replace`, not the guard, so a guard whose needle had been silently reworded still passed. The module docstring and `phase-6-evidence.md` both claimed these controls proved a predicate "that could never match is itself caught".

Verified before fixing: the assertion passes identically for a needle that was never in the file. The fix asserts the needle IS present first, which is the load-bearing half, then that the mutation removes it. The false claim in the Phase 6 evidence file is corrected in place with the correction stated, not silently rewritten.

### A suggested security fix that would have broken macOS

The adversarial pass found a real defect: `trace-example.py` guarded its output directory with `parent.is_symlink()`, which is False for a Windows junction, and only ever checked the immediate parent. Reproduced with `mklink /J`.

The suggested fix was to resolve the parent and refuse any redirection. Implementing it produced an immediate false positive: an ordinary Windows path was refused because `resolve()` also expands 8.3 short names. Worse, a blanket ancestry ban would refuse `/tmp` and `$TMPDIR` on macOS, both symlinks, which is exactly the "caller-owned temporary directory" the script documents as its destination.

The shipped fix detects reparse points precisely and **discloses** redirection rather than refusing it, while the protection that actually matters moved to an `O_EXCL` write that cannot clobber a file or follow a symlink at the final component. A review finding can be correct about the defect and wrong about the remedy; both halves needed checking.

Measuring that fix then found something else: an exclusive create through a junction fails on Windows with `FileExistsError` even when nothing is there. That is now a clean refusal with an explanatory message instead of a traceback.

### A measurement tool that could report what it had not measured

Five defects in `run_trigger_pilot.py`, each reproduced before being fixed. The consequential one: selection was scored with `skill in json.dumps(tool_input)`, a substring test over the whole serialized call, so a different skill's invocation that merely mentioned the target would have counted.

That threatened the pilot's numbers, so the recorded run was audited before anything else. The `Skill` tool was invoked exactly five times across all 96 calls; those five are exactly the five rows scored as selected; each falls on a positive prompt for the skill under test; and no row shows a `Skill` call without a scored selection. The defect can only inflate a positive, never hide one, so every reported count is an upper bound and control arm A could only be equal or lower, which narrows rather than widens the gap criterion 1 failed on. Payloads were not retained, so this is a bounded argument rather than proof, and it is recorded as WN-5.

### A fixture that corrected its own oracle

`representation-cases.json` declared an expected rung per case that no code derived. Adding `derive_rung` immediately produced a disagreement: it placed a two-item, two-attribute comparison on `prose`, because the transcription used a row-count threshold. The ladder's actual rule is "one or two facts with no structure to show", and a two-by-two comparison has structure. The fixture was right and the oracle was wrong, which is the direction that demonstrates they are independent.

## Plan delta

**Disposition: Incomplete, non-blocking.**

The plan's task list had no line for a decision record, while the plan's own entry prerequisite demanded one: "Building an adapter or changing the two-model/cost/evidence contract requires a separately scoped decision; it is outside this plan." Phase 6 did both and no task instructed anyone to write that decision down. `AGENTS.md` independently requires a decision record for a new gate or script and a CHANGELOG entry for any change; neither existed.

**Evidence**: plan line 115; `git diff --name-only origin/develop...HEAD` contained no `docs/decisions/` or `CHANGELOG.md` path before this phase.

**Consequence for remaining phases**: none; this is the last phase and both are now written. Recorded because the omission was structural rather than careless: a plan that states a requirement in prose but creates no task for it will not produce the artifact, and the only thing that caught it here was a reviewer reading the Goal against the tree.

## Next steps

- T034 publication: push once, open the integration pull request against `develop`, wait for the required checks, merge only on green, then hand to `/update release`.
- WN-2 through WN-6 stay open with named owners and are inputs to the next plan.
