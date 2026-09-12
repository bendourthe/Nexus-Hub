# Phase 3 evidence - Authoring-time wiring

Evidence for Phase 3 (T008-T010) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). Records how `/compare` and `/plan` now account for the queue, the one-owner proof, and what the new rules would have produced against the v4.11.0 cache-and-diagram artifacts used as read-only fixed inputs. Read this to confirm D3 before Phase 4 wires execution time.

## T008 - Comparison-time accounting

Two changes to `catalog/skills/workflow/cross-project-comparison/SKILL.md`.

**Step 6.5 now invokes the enumerator.** The hand-executed numeric walk is replaced by `python scripts/enumerate_plan_queue.py --root . --json`. Both documented failure modes are **kept as stated rationale**, because they explain why the script exists rather than being superseded by it; the live `v3.17.12` instance is kept for the same reason. Two behaviours from Phase 1 are surfaced here: an unreadable plan is reported with exit 1 and still occupies its slot, and unchecked tasks are not queue membership.

**Step 6.6 is new: assess queue impact on the comparison.** Slotting decides where a comparison lands; it never asked whether the comparison would still be true when that slot is reached. Step 6.6 assesses each queued plan that would complete before the adoption target and requires a `## Queued-plan impact` report section with a verdict and named evidence per plan, or an explicit "no queued predecessors" statement.

The classification rule is **not** restated; the section names `[[plan-queue-assessment]]` as owner. A finding does not block the comparison: it is recorded so the adoption plan inherits it and so a later reader can tell a considered finding from a missed one.

The skill's own output checklist gained a line, so a report missing the section fails that checklist rather than passing quietly.

## T009 - Plan-time accounting

`catalog/skills/workflow/implementation-plan/SKILL.md` gained a required `## Queued predecessors` template section between `## Overview` and `## Constitution Check`: one row per queued plan that could complete first, carrying the verdict and its evidence, with an explicit "No queued predecessors." line when the queue is empty. A matching line was added to the plan-generation checklist.

`catalog/commands/plan.md` gained a short "Queue-aware planning (guarantee)" section stating the outcome in two sentences and naming the owner, consistent with how that dispatcher surfaces its other guarantees.

Nothing else changed: the goals-first step, the mandatory final phase, the model-map contract, and the task-line format are untouched.

### Line-budget consequence, found and fixed

The first version of the template block was 17 lines and pushed `implementation-plan/SKILL.md` from **exactly 500** body lines to 517, tripping the soft-cap warning that AGENTS.md sets at 500. The block was compressed to 9 lines and the file is under the cap again. Warning count returned to the pre-existing 64.

This is worth recording because the file sat exactly at its limit, so *any* addition would have tripped it. A future addition to this template must either compress elsewhere or start the `references/` split AGENTS.md prescribes beyond 500.

## T010 - Verification

### One-owner proof

The classification vocabulary appears in exactly one file across the whole catalog:

```text
$ grep -rln "content impact|ordering impact" catalog/
catalog/skills/workflow/plan-queue-assessment/SKILL.md
```

Both consuming surfaces reference the owner by name and describe only their handoff. This satisfies the repository's rule-ownership requirement for overlapping skills, and it is the specific failure mode a four-surface feature invites.

### Applied to fixed real inputs

The v4.11.0 cache-and-diagram comparison and plan were used as **read-only** inputs. Neither was edited. What the new rules would have produced:

**For the comparison's `## Queued-plan impact` section**, at its authoring time the queue held the handbook plan and the evidence plan:

| Queued plan | Verdict | Evidence |
|---|---|---|
| v4.9.1 interactive handbooks | Ordering impact | Shares `document-to-interactive-html/references/figure-reconstruction.md` and `.../scripts/visual_qa_score.py`, both named in A5 and A6 |
| v4.13.0 evidence-driven improvement | Content impact | Owns native-runner qualification, which bounds what the comparison may claim about measured effectiveness |

What the comparison actually says: its Grounding section records the v4.9.1 reconciliation as a Phase 4 entry task, and its scope section defers all measured-effectiveness claims to the evaluation plan. **Both findings were already reached by hand.** The new rule would have produced them as a structured section with named evidence instead of prose scattered across two sections, and would have produced them for a future comparison whose author did not happen to think of it.

**For the plan's `## Queued predecessors` section**, the same two rows apply. The plan carries both facts today in `## Grounding and sequencing`, again as prose.

This is the honest result: on these two artifacts the new sections would have **restructured** existing diligence rather than caught a miss. That is still worth having, because prose diligence is not checkable and a checklist line is. It is not evidence that the rule catches something a careful author would miss, and this evidence file does not claim it does.

### Checks run

```text
$ python scripts/validate_skills.py --bundles-only
Scanned 337 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 64 warnings)

$ python -m pytest tests/validators/test_enumerate_plan_queue.py -q
21 passed

$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 7.7s
```

## Limitations

- The applied-to-real-inputs exercise is retrospective. It shows the sections would have been producible, not that a future author will produce them well.
- Neither consuming surface was executed end to end through its own command, because doing so would author a real comparison or plan. The wiring is verified by reading and by the one-owner grep, not by an end-to-end run. Phase 6's Tier 3 pass is where an end-to-end exercise belongs.

## CI impact

Documentation and catalog validation only. No new command, dependency, environment variable, test path, or artifact. Nothing carried to Phase 6.
