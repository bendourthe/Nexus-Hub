# Decision: Assess queued-plan staleness and rank the queue from one owner

Status: implemented - `catalog/skills/workflow/plan-queue-assessment` is the single source of truth for staleness verdicts and queue ranking, consumed by `/compare`, `/plan`, `/implement`, and `/update release`, with deterministic enumeration in `scripts/enumerate_plan_queue.py`

## Problem

A `/compare` report is a snapshot of the codebase at the moment it was written. The plan `/plan from-comparison` derives from it is executed later, often several releases later, against a codebase that has moved and alongside other plans that will move it further. Nothing in the command set re-validated that assumption at any point between authoring and execution, so a plan written against v3.5.0 could be executed unchanged at v4.2.0.

Queue order had the same problem from the other direction. A version slot was allocated by finding the next free number, which answers "where does this go" but never "should this go before or after the four things already queued". At the time of this decision the earliest slot in the queue held a documentation plan, which by any reasonable ordering should run last, because it documents what the other plans build.

Three manual renumbers were performed in a single session to correct queue order by hand. The third was performed while the displaced plan was mid-implementation, and a blanket version rewrite corrupted eleven cross-references including a plan's sequencing intent, and turned two dated statements into factual falsehoods.

## Decision

Adopt a single owner for two rules and have four surfaces consume it.

1. **`catalog/skills/workflow/plan-queue-assessment/SKILL.md`** owns what makes a queued plan stale and how a queue is ranked. No consuming surface restates either rule.
2. **`scripts/enumerate_plan_queue.py`** owns deterministic enumeration: numeric version sorting, whole-tree scanning, per-plan status, task counts, and touched-file surfaces.
3. **Four consumers**: `/compare` Step 6.6, the `/plan` template's `## Queued predecessors` section, the `/implement` runbook's plan-entry and phase-entry re-assessment, and `/update release` governance step 5a.

Four constraints are load-bearing:

- **An open task count is never queue membership.** Shipped and abandoned plans retain unchecked task lines; at adoption time more than a dozen did, three of them larger than any genuinely queued plan.
- **A verdict requires named evidence.** "No impact" without the disjoint surfaces listed is indistinguishable from not having looked.
- **Every check writes an artifact, including a no-op.** An unwritten check is indistinguishable from a skipped one. This is what stops four added assessment steps becoming ritual.
- **Impact-on-harness is a recorded maintainer judgement, not a computed score.** Only parallel compatibility is computed.

Ranking places documentation, interactive-guide, and refactor classes last, and attaches a real content-refresh task to whatever lands there.

Re-sequencing is a **recommendation**. Acting on one is propose-then-apply behind explicit confirmation, proven by a residual-reference check that fails on a single survivor.

## Alternatives considered

**Automatic renumbering.** Rejected. Renumbering rewrites version identity that merged pull requests, changelogs, and published documentation already reference. The observed blanket-rewrite failures (eleven corrupted cross-references, two falsified dated statements, one corrupted section heading that merely looked like a version) are what a fully automatic pass would produce unattended and unreviewed.

**A persisted queue database.** Rejected. It adds a state file that can disagree with the tree, and the tree is already the source of truth. Enumeration is fast enough to run on demand.

**Skill-only, no script.** Rejected under the repository's own preference for LLM-native solutions, because the enumeration has two documented failure modes (lexical sorting, current-minor-only scanning) that have each produced a confident wrong answer. Those are exactly the cases a deterministic scanner should own and a re-derived judgement should not.

**Inline instructions in each of the four commands.** Rejected. It puts one rule in four places, which the repository's rule-ownership policy forbids for overlapping skills, and which would drift within a release or two.

**Computing impact-on-harness.** Rejected. Any score would be an invented weighting presented as derived, and it would be argued with as if it were measured. A recorded judgement can be disagreed with on its reasoning.

**Folding this into the v4.13.0 evaluation plan.** Rejected at authoring time. That plan is blocked on a native-runner prerequisite, and this capability has no measurement dependency.

## Consequences

- A comparison and a plan each carry a queued-predecessor record, so a later reader can distinguish a considered finding from a missed one.
- `/implement` re-validates before writing code rather than after.
- A release reports its own effect on everything still queued.
- The catalog gains one skill, one maintainer script, and two test modules. No new dependency, environment variable, or outbound call.
- **This decision does not claim re-sequencing makes delivery faster.** It reduces rework from stale plans. Any speed claim would need measurement that was not performed.
- The capability cannot rank itself, so its own placement stays a maintainer decision.
