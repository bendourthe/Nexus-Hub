# Last-Phase Evidence - v4.11.2 Document and Deck Quality

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Branch**: `feat/v4.11.2-document-deck-quality`, from `develop` at `8ac5e325`
**Date**: 2026-09-13
**Status**: local GO. Publication and integration require explicit approval.

Each duty below quotes the command that proves it, or records a gap naming what
was not done.

## Architecture refactor

### One owner per check, verified

```
for each check name, count the scripts that define it
(no output = one owner each)
```

No check is defined in two scripts. `functional-verification` does not claim
`label-overlap`, which is this skill's; the WN-5 contradiction closed in v4.11.0
has not reopened.

### A one-owner violation this plan created, and fixed

The rule-ownership table said `[[hallmark-design]]` owns "the looks-AI-generated
visual tells". This plan then put the document-tell LIST in `[[anti-slop-editing]]`
and MEASURED two of them in `geometric_audit.py` - three owners for one concern,
which is exactly what that table exists to prevent.

Resolved with the tie-break `AGENTS.md` specifies: one skill decides when a
constraint applies and how severe it is, another owns measuring it.
`hallmark-design` judges, `anti-slop-editing` holds the named list, this skill
counts the two countable members. Seven rows added and the split stated in prose
above the table, because a table alone does not explain why three entries touch
one subject.

### Bundled resources

Both new scripts are referenced from `SKILL.md`, so the orphan audit is clean.
`SKILL.md` is 429 lines, inside the 500-line target.

## Known-gaps reconciliation

Recorded in [the v4.11 ledger](../../known-gaps.md) under
`v4.11.2 - adoption-document-and-deck-quality`.

- **MT-5 - PARTIALLY closed, and said so.** It was transferred into this plan expecting Phase 5's provenance record to close it. It closes one half: an unsourced series now fails. The other half - a value existing only in an intermediate animation frame - is untouched, because the attestation covers what a series IS, not what a chart displays mid-transition. Next step recorded: sample inside the animation window, which Phase 4's per-slide walk already makes possible.
- **Four tells attested rather than gated**, deliberately: emoji markers, em-dash rhythm, structure-announcing sentences, three-bullet sections. Each needs a judgement about what the document is for, and a check that guessed would be the beauty detector this plan forbids.
- **SEC-1 and MT-9** carried unchanged; neither belongs to this plan.

## Living documentation and the self-hosted handbook check

```
geometric_audit   docs/handbooks/overview.html       exit=0
geometric_audit   docs/handbooks/distribution.html   exit=0
check_handbooks                                      exit=0
check_attestation (round-trip record)                exit=0  complete
```

Zero findings across both handbooks. This is the result the source project's
audit could not reach: its first version produced roughly 220 findings on real
output and was abandoned for it.

## Git-tree hygiene

Six phase commits plus this one, each scoped to its phase. No unrelated guide
work, private data, or transient artifact entered any of them. Line endings were
checked against the committed blob at every phase boundary after the v4.11.0
release found seventeen drifted files.

## Terminal CI/CD reconciliation and distribution parity

**No pipeline change was required**, recorded explicitly because "no change" and
"not checked" are indistinguishable afterwards.

```
new scripts under scripts/ (needing installer registration):  0
new skill-bundled scripts (auto-copied by both installers):   3
new test files (already inside the repo-tests glob):          5
check_installer_parity.py                                     PASS
```

## Tier 3 deep pass

The full profile on final bytes, after two corrections:

```
run 1:  FAIL  45 passed, 1 failed   (repo-tests: 2 failed, 5394 passed)
run 2:  PASS  5396 passed, 98 skipped, 0 failed in 3756.54s
```

Both failures were mine and both were caught by repository guards rather than by
review:

- `check_attestation.py` was git mode `100644` with a shebang, which fails `ruff EXE001` on Linux. Both new scripts are now `100755`.
- **`test_update_md_stays_a_thin_dispatcher`** - Phase 6 inlined a numbered procedure with sub-bullets into `update.md`, which is a dispatcher. The test said it plainly: the procedure belongs in the skill's runbook. The substance already lived in the skill, so the dispatcher now carries one line naming the gate and its owner.

The second is worth keeping in view: a repository guard caught this plan
violating the repository's own architecture, in the phase whose job is to check
exactly that.

## Goal-vs-codebase review

**The Goal**: make the first generated draft survive inspection without a human
acting as the rendering engine, by converting field lessons into gates that fail
a build rather than advice a build can rationalise past.

**Against the tree:**

| Claim | Evidence |
|---|---|
| Gates, not advice | 11 checks in `geometric_audit.py`, 4 in `DECK_INTEGRITY`, 4 attestation sections. Each fails a build; none is prose. |
| Every gate observed to fail | 16 fixtures, each carrying exactly one defect, plus `--disable` and threshold controls proving each finding comes from its own check. |
| Measured, not asserted | Screen space throughout, with one commented user-space exception for `viewbox-dead-space`. |
| The unmeasurable is not dropped | `check_attestation.py` fails a missing or empty record, and `test_attestation_never_scores_content` asserts it never judges quality. |
| The loop is mandatory | wired into `presentify`, the skill, `/update docs`, `/update release`; `test_rendered_gate_wiring.py` asserts the wiring and is negative-controlled. |

**What the Goal does NOT yet reach**, stated because a review that finds nothing
is not a review:

- A first draft is not *proven* to survive inspection. No end-to-end qualification run was attempted in this plan; the evidence is that every gate fires correctly and that real output passes all of them. Those are different claims, and the weaker one is what ships.
- MT-5's animation half remains open.
- Four tells rely on an attestation a build could file thoughtlessly. The gate prevents silence, not carelessness, and no gate can prevent the latter without judging content.

**Considered and rejected:**

- **Wiring `geometric_audit.py` into the `docs` CI profile.** It needs a browser, and the `docs` group is stdlib-only and runs in seconds. Wiring it there would make every documentation check depend on Playwright. It belongs in the render job, which is a pipeline change and therefore out of scope for a plan whose CI impact is otherwise zero. Recorded rather than done.
- **A `--fix` mode for `viewbox-dead-space`.** The check already emits the exact crop, and the fixture pair proves it is applicable. Writing it automatically would edit a generated artifact, which the same release gate forbids.
- **Raising `TELL_THRESHOLD` when both handbooks failed.** That would have set the bar by what this repository happens to do. The checks were narrowed instead, and the thresholds never moved.

**Reviewer independence**: none. This review was performed by the agent that
wrote the code, which is a real limit on its weight and is recorded rather than
implied.

## Local GO

Every duty above quotes its proving command. No required gate is unresolved and
no failed gate is recorded as a pass.

**Publication and integration are NOT done.** Nothing has been pushed, no pull
request exists, and no remote CI has run for this plan.
