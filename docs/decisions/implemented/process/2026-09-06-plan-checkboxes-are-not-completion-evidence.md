# Decision: A plan checkbox is a bookkeeping artifact, not completion evidence

Status: implemented - 156 exit-checklist boxes across eight v4 plans reconciled against per-class artifacts; 343 left open because no artifact proves them; the release tag plus `last-phase-evidence.md` named as the authoritative completion signal

## Problem

Counting unticked checkboxes across the v4 plan set suggested that roughly a third of the released v4 line was unimplemented: 738 open boxes across 25 plans, with `v4.0.0-cost-effective-ci-cd.md` showing 0 of 159 complete and both v4.7.0 plans showing under 40 percent. Read at face value, that says v4.7.0 was tagged and published on top of substantially unfinished work.

It says nothing of the kind, and the discrepancy is structural rather than accidental.

Splitting the boxes by the section they sit in separates two populations that a raw count merges:

| Population | Count | What it tracks |
|---|---|---|
| Sub-task boxes | 239 open | Actual implementation work |
| Exit Checklist boxes | 499 open | Per-phase process bookkeeping |

Exit-checklist items are things like "Session history generated for this phase", "One local commit created for this phase", and "No branch push, pull request, or remote CI run occurred". They are ticked by the agent driving `/implement` at a phase boundary, which is precisely the moment a long session is most likely to end, be interrupted, or hand off. The work completes, the commit lands, the release ships, and the box stays open. Nothing downstream reads these boxes, so nothing ever noticed.

Filtering to sub-tasks on *released* versions collapses the apparent backlog to one plan:

| Version | Sub-tasks | `last-phase-evidence.md` | Tag | Verdict |
|---|---|---|---|---|
| v4.0.0 | 121 / 121 | 15 KB | yes | shipped |
| v4.1.x - v4.4.x | all | 15 - 107 KB | yes | shipped |
| v4.5.0 | 30 / 30 | 24 KB | yes | shipped |
| **v4.6.0** | **0 / 31** | **absent** | **absent** | **never started** |
| v4.7.0 | 60 / 60 | 28 KB | yes | shipped |

v4.0.0's 80 open sub-task boxes were checked against the tree directly: `scripts/ci/profiles.py`, `docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`, `.github/workflows/post-merge.yml`, `scripts/check_required_check_coverage.py`, `docs/policy/required-checks.json`, three test modules, and the `Plan Lifecycle and CI/CD` block in all thirteen instruction templates are all present. The plan shipped in full.

The one genuine gap was already recorded in prose, in the v4.7.0 changelog entry: "v4.6.0 was never cut; its plan is unimplemented and carries forward." The checkbox count did not surface that; it buried it under 499 false positives.

## Decision

**A plan's checkbox state is a bookkeeping artifact and is not evidence of completion.** The authoritative completion signal for a release is its tag plus `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/last-phase-evidence.md`. A ledger that disagrees with those two is stale.

Reconciling a stale box requires the artifact that box names. Ticking off a tag would assert a per-phase verification nobody performed, which is the same defect in the opposite direction. Each class is verified against its own evidence:

| Class | Ticked only when |
|---|---|
| `SUBTASKS` | every sub-task box in that phase is already ticked |
| `HISTORY` | a session-history file exists for that plan and phase |
| `TESTS`, `VERIFY` | that history file carries a `## Verification` section |
| `CI` | that history file carries a `## CI impact record` section |
| `COMMIT` | one commit message names both that version and that phase |
| `ADVANCE` | the next phase's history exists, so it demonstrably advanced |
| `RELEASED` | the version's tag exists |
| `EVIDENCE` | the version's `last-phase-evidence.md` exists |

Two rules make the result trustworthy rather than merely tidy.

**No history means nothing is verifiable.** If a phase has no session-history file, that phase did not run, and only `SUBTASKS` may tick (it reads straight off the plan). Without this gate, a commit that merely *names* a version scores phase work for it: the commit migrating the v4.8.0 and v4.9.0 plans onto `develop` ticked a box in a plan with zero implemented sub-tasks.

**The slug must match, not just the version.** v4.7.0 shipped two plans, and every v4.7 history filename carries `v4.7.0`, so a version-only match had phase N of one plan verifying phase N of the other. Under the corrected matcher the `gpt-6-astra-prompting` plan resolves to no history of its own (its amendments were folded into the other plan's phases) and drops from 33 ticks to 4.

**343 boxes stay open on purpose.** 108 are phrasing the classifier does not recognize, and 38 assert a negative - "no branch push occurred" - that no artifact records. An absence of evidence is not evidence of absence, and a box asserting that nothing happened cannot be closed by finding something.

## Alternatives considered

- **Tick every box in any tagged version.** Fastest, and it reaches 100 percent on every shipped plan. Rejected: it asserts per-phase verification that was never performed, which is the same class of untruth as leaving a shipped release looking unimplemented. It would also have ticked v4.2.2 and v4.2.3, which have complete six-phase histories but no tag at all, for the wrong reason.
- **Leave every box untouched and add a status banner per plan.** Minimal churn in historical documents, and it is honest. Rejected as insufficient on its own: the banner tells a reader the count is unreliable but leaves them no way to see *which* items were confirmed. The per-class reconciliation answers that, and this record supplies the banner's content once instead of eight times.
- **Delete the exit checklists from historical plans.** Removes the misleading signal entirely. Rejected: the checklist is the plan's own definition of a complete phase and is worth reading later; and deleting a ledger to fix its accuracy destroys the audit trail the ledger exists for.
- **Add a validator that fails when a tagged version has open sub-task boxes.** Rejected for now. It would have caught this, but a hard gate on a bookkeeping artifact blocks releases on paperwork, and the same reasoning that keeps `check_docs_retention.py` advisory applies. The tag plus evidence file are the signal; a gate on the derived ledger inverts that.
- **Retarget the v4.6.0 plan and implement it as v4.6.0.** Rejected as impossible rather than undesirable: `v4.7.0` is already tagged and published and `plugin.json` reads `4.7.0`, so a `v4.6.0` tag would sort behind the current release and be invisible to anything resolving latest. The plan carries forward into v4.8.0.

## Consequences

- Eight plans changed, 156 lines, every one of them a checkbox character. No prose was touched, and the added and deleted line counts are equal per file.
- `v4.6.0` is confirmed as the only unimplemented version in the v4 line, and its plan carries forward into v4.8.0 rather than shipping under its own number.
- The reconciliation was a one-off script under the session scratchpad, deliberately not added to `scripts/`. It encodes assumptions about history-filename shape that hold for the v4 line and should be re-derived rather than trusted if this is ever needed again.
- Anyone auditing release completeness should read the tag and `last-phase-evidence.md`. The checkbox ledger is a convenience for the agent mid-plan and carries no authority after the release closes.
