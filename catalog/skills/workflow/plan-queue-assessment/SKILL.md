---
name: plan-queue-assessment
description: Assess whether a queued plan has gone stale against the current codebase and the other plans queued around it, and rank the queue by parallel-implementation compatibility and impact. Make sure to use this skill whenever the user mentions queued plans, plan ordering, plan sequencing, which plan to do next, whether a plan is still relevant, whether a comparison is out of date, re-slotting or renumbering a release, or says "is this plan still valid", "what should we build next", "can these two run in parallel", "did the last release change our plans", or "re-order the queue" - even when they do not use the word queue. SKIP - authoring a new plan (use implementation-plan), executing a phase (use implement-phase), moving documentation trees for layout reasons rather than re-sequencing (use docs-layout-refactor), and any claim that re-ordering makes delivery faster, which this skill never makes.
summary_l0: "Assess queued-plan staleness and rank the queue by parallel compatibility and impact"
overview_l1: "A comparison is a snapshot and a plan derived from it executes later, against a codebase that has moved and alongside plans that will move it further. This skill is the single owner of two rules: how to classify one queued plan's effect on another as no impact, content impact, or ordering impact with named evidence; and how to rank a queue by parallel-implementation compatibility and by judged impact on the harness, placing documentation, interactive-guide and refactor classes last with a refresh requirement attached. It consumes the deterministic inventory from scripts/enumerate_plan_queue.py and is invoked by the comparison, planning, implementation and release surfaces. It reports and recommends; it never rewrites a plan's content, and it never claims that re-sequencing improves delivery speed."
---

# Plan-Queue Assessment

A comparison is a photograph. The plan derived from it is executed later, against a codebase that has moved and alongside other plans that will move it further. Nothing re-validates that assumption unless something explicitly does, and by then the plan has been executed as written.

This skill owns two rules and nothing else: **what makes a queued plan stale**, and **how a queue is ranked**. Four surfaces consume it. None of them restates these rules.

## When to Use This Skill

- Before adopting a comparison into a version slot, to record which queued plans could change its findings first.
- While authoring a plan, to record the queued predecessors whose completion would alter its content.
- At the start of a plan, and at the start of every phase, to re-validate the plan against the tree it is about to modify.
- After a release, to report which still-open plans that release changed.
- Whenever the maintainer asks what to build next, whether two plans can run in parallel, or whether the queue order still makes sense.

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Author a new plan | `[[implementation-plan]]` |
| Execute a phase | `[[implement-phase]]` |
| Move a docs tree for layout reasons | `[[docs-layout-refactor]]` |
| Decide a comparison's adoption slot | `[[cross-project-comparison]]` Step 6.5, which calls this skill for the impact half |
| Claim re-ordering made delivery faster | Nothing here. That needs measurement this skill does not perform. |

## Rule ownership

This skill's territory overlaps four others. Exactly one owner states each rule.

| Concern | Owner |
|---|---|
| What makes a plan stale; how a queue is ranked; the renumber procedure | **this skill** |
| Deterministic queue inventory (versions, counts, touched paths, status) | `scripts/enumerate_plan_queue.py` |
| Which slot a comparison adopts | `[[cross-project-comparison]]` Step 6.5 |
| The plan template and its required sections | `[[implementation-plan]]` |
| Phase lifecycle, gates, and the `## Plan delta` disposition vocabulary | `[[implement-phase]]` |
| Moving a documentation tree and repairing references | `[[docs-layout-refactor]]` and `[[project-refactor]]` |

When this skill needs one of those, it names the owner and describes only the handoff. If an owner is unavailable, say so and mark that portion not covered; do not reconstruct its rules from memory.

## Instructions

### Step 1 - Get the inventory

Run the enumerator and read its output, including its findings:

```bash
python scripts/enumerate_plan_queue.py --root . --json
```

Exit 1 means at least one plan is unreadable. Those plans are still listed. **An unreadable plan is an explicit unknown for every judgement below, never a silent no-impact**, because a plan you could not read is exactly the one most likely to surprise you.

### Step 2 - Establish queue membership

**An open task count is not membership.** Shipped and abandoned plans retain unchecked task lines, and in this repository several of them are larger than any genuinely queued plan. Ranking on task volume alone puts a superseded plan at the top of the queue.

Determine membership from, in order of authority:

1. The plan's declared `**Status**:` line.
2. The maintainer's explicit statement.
3. Absence of a merged release for that version.

A plan whose status is undeclared is reported as **undeclared**, not assumed queued and not assumed finished. Ask, or carry it as unknown. Do not infer membership from counts.

### Step 3 - Classify each queued plan against the subject

For each queued plan other than the subject, assign exactly one verdict with named evidence:

| Verdict | Means | Required evidence |
|---|---|---|
| **No impact** | Completion changes nothing about the subject | The disjoint file surfaces, and the absence of any stated dependency |
| **Content impact** | Completion would change what the subject should say or do | The specific claim, assumption, or task in the subject that would change, quoted |
| **Ordering impact** | The two touch an overlapping file surface, so they cannot run in parallel | The overlapping paths, listed |
| **Unknown** | The plan could not be read or its status is undeclared and unresolvable | What could not be determined, and why |

A verdict without evidence is not a verdict. "No impact" asserted without naming the disjoint surfaces is the failure this step exists to prevent, because it is indistinguishable from not having looked.

Content impact and ordering impact are independent. Two plans can share no files and still change each other's content, if one establishes a rule or a capability the other assumes.

### Step 4 - Detect overlapping surfaces

Take the `touched` list from the inventory for each plan and intersect them pairwise. An intersection is **ordering impact**; an empty intersection is a necessary but not sufficient condition for parallel work.

Two cautions:

- The touched list comes from paths named in task lines. A plan that modifies a file without naming it is under-reported. Treat the list as a lower bound on the real surface, not a complete one.
- A shared file is not automatically a conflict when the two plans touch different regions of it, but resolving that requires reading both, so the default verdict stays ordering impact until someone does.

### Step 5 - Rank the queue

Rank on two axes, in this order:

1. **Parallel-implementation compatibility.** Plans with disjoint surfaces and no stated dependency can run concurrently and should be grouped. This axis is computed from Step 4.
2. **Impact on the harness.** Which plan makes the product better for its users. This axis is a **structured maintainer judgement, not a computed score.** Record the reasoning; never present it as derived.

Then apply the class rule:

**Documentation, interactive-guide, and refactor-class plans rank last.** They describe or reorganize what the other plans build, so running them first guarantees rework. A plan placed last by this rule is marked as **requiring a content refresh** against every plan sequenced ahead of it, and that refresh is a real task the plan must carry, not a note.

Classify by what the plan produces, not by its title. A plan that adds a capability *and* documents it is not a documentation plan.

### Step 6 - Report

Produce, as a written artifact:

- The queue with each plan's verdict and evidence.
- The recommended order, with the reason per position.
- Parallel-compatible groups, if any.
- Every unknown, named.

**A step that only asserts a check occurred is not evidence.** Write the artifact even when the finding is "nothing changed"; an unwritten no-op is indistinguishable from a skipped check, and four consuming surfaces asserting they checked is precisely the redundant-ritual failure a verification gap already warns about.

### Step 7 - Re-sequencing, if requested

Ranking produces a recommendation. Acting on it moves files and rewrites references, so it is **propose-then-apply, behind explicit confirmation, and never automatic**. See the renumber procedure below.

## Renumber procedure

Renumbering rewrites version identity that merged pull requests, changelogs, and published documentation already reference. It is the highest-blast-radius operation this skill touches.

1. **Propose.** Present the new order with the reason per move. Wait for explicit confirmation. Silence is not approval.
2. **Move the tree** via `[[docs-layout-refactor]]`. Do not reimplement the move.
3. **Rename** the plan and comparison files to their new version prefix.
4. **Repair every reference class** via `[[project-refactor]]`. All seven have been observed in practice:
   1. Intra-tree version strings (`**Version**:`, `**Filename**:`, body prose).
   2. Relative plan links from sibling version trees.
   3. Link-reference definitions (`[N8]: ../../..`), which a link-text-only scan misses entirely.
   4. Self-referential output paths inside the plan's own task lines.
   5. Tracker dashboard rows.
   6. Tracker prose and section headings.
   7. Committed implementation evidence under the moved tree.
5. **Prove the repair.** A residual-reference check must fail on a single surviving reference to the old version outside a deliberately historical statement.

### Two traps a blanket rewrite hits

Both have occurred. Both must be checked by hand.

- **A bare section number is not a version.** A plan carrying the heading `#### 4.10 - Publication and integration` is corrupted by a `4.10 -> 4.12` substitution. Rewrite only `v`-prefixed forms.
- **A blanket rewrite cannot tell a plan's own version from a reference to another plan.** One observed swap corrupted eleven cross-references in a single plan, including its sequencing intent, which inverted. Two further statements were rewritten into factual falsehoods about what had been confirmed on a given date.

**Repair a historical claim with a dated note, never a silent restatement.** "The user confirmed v4.10.0 on 2026-09-09" does not become "v4.11.0" because the plan moved; it becomes the original claim plus what changed and when.

### The mid-implementation case

Renumbering a plan whose phases are already committed requires a step beyond the rename: the committed implementation must be re-applied at the new paths. Cherry-picking across the rename conflicts, because the rename and the phase edits touch the same files. Reconstruct the branch at the new paths instead, and say in the commit message that the per-phase commits were collapsed and where the per-phase record survives.

Prefer not to renumber a mid-implementation plan at all. When it is done anyway, it is a maintainer decision and the cost above is the reason to state it out loud first.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "These plans obviously do not overlap, I do not need to list the files." | A verdict without evidence is indistinguishable from not having looked. The one time the surfaces did overlap is the time you will not have checked. |
| "This plan has 62 open tasks so it must be the biggest thing queued." | Open counts are not membership. In this repository the three largest open-task plans are all superseded or abandoned; ranking on volume puts a dead plan first. |
| "The queue has not changed since I last looked, so I can skip the check." | The check is cheap and its output is the artifact. Skipping it produces the same chat message as running it, which is why the artifact is required. |
| "I will just note that the queue is fine." | An unwritten no-op is a skipped check. Write the result. |
| "Re-ordering the queue will speed us up." | This skill has never measured that and must not claim it. It reduces rework from stale plans; that is a different claim and the only one supported. |
| "The rename is mechanical, I can run a find-and-replace." | A blanket rewrite corrupted eleven cross-references in one observed pass, inverted a plan's sequencing intent, and turned two dated statements into falsehoods. It also rewrites section numbers that merely look like versions. |
| "The documentation plan is small, let it go first." | It describes what the other plans build. Running it first guarantees rework, and its size is not the reason it ranks last. |
| "Impact on the harness is basically obvious, I can just assert the order." | It is a judgement, which is exactly why it must be recorded with reasoning. An asserted ranking cannot be argued with or revisited. |
| "I could not read that plan, so it probably does not matter." | An unreadable plan is an explicit unknown. It is the one most likely to surprise you, not the one safest to ignore. |

## Verification

- [ ] `python scripts/enumerate_plan_queue.py --root .` ran, and its exit code and findings are recorded.
- [ ] Queue membership was established from declared status or an explicit maintainer statement, never inferred from open task counts.
- [ ] Every queued plan carries exactly one verdict, and every verdict names its evidence.
- [ ] Every unreadable or undeclared-status plan appears as an explicit unknown.
- [ ] Overlapping surfaces are listed as paths, not asserted.
- [ ] The written artifact exists and states the recommended order with a reason per position.
- [ ] Impact-on-harness is recorded as a judgement with reasoning, not presented as a computed score.
- [ ] No claim was made that re-sequencing improves delivery speed.
- [ ] If a renumber was performed, the residual-reference check ran and passed, and every historical claim was repaired with a dated note rather than a restatement.

## Related Skills

- `[[implementation-plan]]` -- authors the plans this skill assesses; owns the plan template and the queued-predecessor section this skill fills.
- `[[implement-phase]]` -- executes them; owns the phase gates and the `## Plan delta` vocabulary this skill supplies evidence to.
- `[[cross-project-comparison]]` -- owns adoption-slot resolution; calls this skill for the queue-impact half.
- `[[docs-layout-refactor]]` -- owns moving a documentation tree; the renumber procedure delegates the move.
- `[[project-refactor]]` -- owns reference repair across a move.
- `[[known-gaps-tracker]]` -- records an unresolved verdict that cannot be closed now.
- `[[verification-before-completion]]` -- owns what counts as evidence for a claim; this skill's written-artifact requirement is that rule applied to queue checks.
