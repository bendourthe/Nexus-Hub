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
- Before a new plan or comparison takes a version, to place it by priority with the placement rule below.
- While authoring a plan, to record the queued predecessors whose completion would alter its content.
- At the start of a plan, and at the start of every phase, to re-validate the plan against the tree it is about to modify.
- After a release, to report which still-open plans that release changed.
- Whenever the maintainer asks what to build next, whether two plans can run in parallel, or whether the queue order still makes sense.
- Before a minor run is approved, to read every member plan together for overlap, redundancy, merge, split and renumber opportunities (see Minor re-plan analysis).

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Author a new plan | `[[implementation-plan]]` |
| Execute a phase | `[[implement-phase]]` |
| Move a docs tree for layout reasons | `[[docs-layout-refactor]]` |
| Record a comparison's adoption target | `[[cross-project-comparison]]` Step 6.5, which calls this skill's placement rule and, in Step 6.6, its queue-impact check |
| Claim re-ordering made delivery faster | Nothing here. That needs measurement this skill does not perform. |

## Rule ownership

This skill's territory overlaps four others. Exactly one owner states each rule.

| Concern | Owner |
|---|---|
| What makes a plan stale; how a queue is ranked; which version a new plan takes (the placement rule); the renumber procedure | **this skill** |
| Deterministic queue inventory (versions, counts, touched paths, status) | `scripts/enumerate_plan_queue.py` |
| Minor re-plan analysis (overlap, redundancy, dependency graph, merge/split/renumber proposals, parallel schedule) | **this skill**, through its bundled `scripts/replan_minor.py` |
| Draft implementation-claims pre-check against admitted members | `implement-phase/scripts/claims_precheck.py` (read-only mirror of the native overlap rule); the native admission keeps the verdict |
| Resolving and confirming a comparison's `Adoption target:` field (it applies the placement rule) | `[[cross-project-comparison]]` Step 6.5 |
| The plan template and its required sections | `[[implementation-plan]]` |
| Phase lifecycle, automatic worker dispatch, ordered publication, and the `## Plan delta` disposition vocabulary | `[[implement-phase]]` |
| Signed implementation claims, parent-bound projections and publication admission | `implement-phase/references/completion-contract.md` and its native checker |
| Worker scope prompts and concurrent-writer coordination | `[[multi-agent-coordinator]]` |
| Moving a documentation tree and repairing references | `[[docs-layout-refactor]]` and `[[project-refactor]]` |

When this skill needs one of those, it names the owner and describes only the handoff. If an owner is unavailable, say so and mark that portion not covered; do not reconstruct its rules from memory.

## Instructions

### Step 1 - Get the inventory

Run the enumerator and read its output, including its findings:

```bash
python scripts/enumerate_plan_queue.py --root . --json
```

Exit 1 means at least one plan is unreadable. Those plans are still listed. **An unreadable plan is an explicit unknown for every judgment below, never a silent no-impact**, because a plan you could not read is exactly the one most likely to surprise you.

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

### Implementation compatibility inventory

Before recommending concurrent implementation, expand task-derived paths into complete literal `read_paths` and exclusive `write_paths`, including source, tests, plan checkboxes and plan-specific history/evidence. Name actual `depends_on` members and the merged commit each requires on the proposed worker base. Distinguish a semantic-version release predecessor from an implementation prerequisite: an unrelated earlier release does not block implementation. Report write/write and write/read conflicts, directory-prefix overlap, case collisions, unstated contracts and all unknowns. Shared known-gaps ledgers, CHANGELOG, version/release metadata and docs/todos belong to the coordinator; workers propose these deltas separately. When a plan explicitly changes an input another worker reads, keep that change as an explicit coordinator proposal for its publication turn, with the original implementation task unchecked until the coordinator applies and tests it. Removing those shared files from worker claims does not remove a substantive source dependency.

Read claims name semantic implementation inputs. Generic broad validators may inspect a pinned isolated worker snapshot without turning every scanned file into an implementation dependency; defer broad validation to the coordinator's refreshed complete candidate and never use that snapshot result as current integration proof. A model-routing preflight reads the pinned verified orchestration baseline, never unpublished sibling changes. Actual semantic read/write dependencies remain blocking.

Record candidate concurrent groups, named compatibility evidence, prerequisites still missing and a conservative serial fallback for every unknown. A shared production file stays ordered even when regions look disjoint unless the complete ownership contract permits concurrent work; native whole-file claims may still require sequencing. For already frozen plans, put this refreshed inventory in a release-scoped assessment sidecar rather than editing approved prose. This assessment recommends eligibility; the completion contract's native admission validates claims and [[implement-phase]] dispatches actual workers.

### Step 5 - Rank the queue

Rank on two axes, in this order:

1. **Parallel-implementation compatibility.** Plans with disjoint surfaces and no stated dependency can run concurrently and should be grouped. This axis is computed from Step 4.
2. **Impact on the harness.** Which plan makes the product better for its users. This axis is a **structured maintainer judgment, not a computed score.** Record the reasoning; never present it as derived.

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

## Minor re-plan analysis

A queue assessment ranks plans one at a time. A minor re-plan analysis reads every member plan of one minor together and asks whether the set itself should change: merged, split, renumbered, or stripped of duplicated work, so that as many plans as possible can run at once. This skill owns that analysis. `/implement vX.Y` runs it before approval today, and again at every minor-run start and resume as the minor-entry re-plan in `implement-phase-runbook.md` Phase 0c; `/compare` and `/plan` call the same entry point later, so keep the interface stable.

Run the bundled helper against the minor's plans folder. It is read-only, standard-library Python, and writes nothing except the optional JSON file:

```bash
python scripts/replan_minor.py docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans --json <scratch>/replan.json
```

The path above is relative to this skill's folder (from a runbook in `implement-phase/references/`, use `../../plan-queue-assessment/scripts/replan_minor.py`). Options: `--lanes N` (default `min(cores / 2, 6)`, floor 1, or `NEXUS_IMPLEMENT_LANES`), `--similarity 0.8`, `--include-all`, `--claims-deps-only`. Exit 1 means a plan was unreadable and is reported as an explicit unknown, as in Step 1. Markdown goes to the terminal; `--json -` prints JSON only.

What it reports, and the evidence behind each line:

- **Overlap.** Pairwise write/write and write/read conflicts using the minor checker's own overlap rule (casefold, directory prefix). Coordinator-owned paths (CHANGELOG, docs/todos.md, known-gaps ledgers, `data/` registries) never count, because workers only propose deltas to them. A pair marked narrowable conflicts only because one plan reads a whole directory another plan writes into.
- **Redundancy.** Open tasks in different plans with near-identical normalized text, or similar text aimed at the same file. Per-phase template tasks (commit, evidence, hygiene, terminal CI) are suppressed and counted, because they repeat by design.
- **Dependencies.** Edges from each plan's claims `depends_on`, plus prose hints (a version named after "depends on", "requires", "blocked by"). Hints print their source line: read it before treating the edge as real. The critical path is the longest dependency chain by open-task count.
- **Merge and split candidates.** Merge: heavy shared writes or repeated tasks and a small combined size. Split: a large plan whose phases share no files.
- **Claims that block parallel lanes.** Each directory claim, or exact file shared by several writers, ranked by how many plans it serializes, with the narrowing that frees them. This is the first proposal set: narrow these before considering a merge or renumber. `dispatch_now` in the JSON (the "Dispatch now" line) lists the members that can start immediately.
- **Schedule.** Plans grouped into waves under the lane cap, honoring dependencies and hard conflicts, with the best of five ordering strategies compared against the current version order; and a renumbering that makes version order match the best wave order. Pinned plans (any task checked, or in progress) never move.

Wave counts are structural: how many plans can be in flight at once, not measured delivery time. This skill still never claims that re-sequencing makes delivery faster; say "fewer waves" and name the cost.

### Turning the report into proposals

Convert findings into a numbered list. Each proposal states the change, the report evidence, the structural effect, and the cost. Never propose from a bare number.

| Finding | Proposal | Cost to name |
|---|---|---|
| Narrowable overlap | Replace the directory read claim with the exact files the plan reads | Plan text edit only |
| Hard overlap on one file | Assign the file to one plan and let the other read it after that plan lands, or order the pair | One plan waits |
| Redundant tasks | Keep the task in the plan that owns the file; drop or reference it from the other | Two plan edits |
| Merge candidate | Merge into the lower version; free the other slot; keep both task lists | Lost parallelism between the pair, one fewer renumber |
| Split candidate | Split along the independent phase groups into two plans | New version slot, new approval scope |
| Prose dependency | Confirm from the cited line; if real, move it into claims `depends_on` | Plan text edit |
| Renumber moves | Offer only when the report shows at least one wave saved, with the move count beside it | Seven reference classes per move, per the Renumber procedure |

Rules for proposals:

1. Show every proposal to the user for approval. Silence is not approval, and a plan the user already confirmed is not edited or renumbered without an explicit decision for that plan.
2. Apply only approved proposals, through the Renumber procedure and `[[docs-layout-refactor]]` and `[[project-refactor]]` for moves, and plain plan edits for the rest. The helper never edits a plan.
3. Prefer the cheapest proposal that removes a conflict: narrowing a claim beats reordering, reordering beats merging, and renumbering is last.
4. Once a minor's plan text is frozen by approval, the analysis is advisory: only new members can join through the completion contract's amend-minor, and findings about frozen members feed the next minor's plans.
5. Write the summary into the run's evidence even when it finds nothing to change, as Step 6 requires.

### Plan-time use by `/compare` and `/plan`

`/compare` and `/plan` run this same analysis right after they resolve the target version, so a new plan or adoption target is checked against the other plans of that minor before the user confirms it.

1. Resolve the target version first (placement rule below). Take its minor's plans folder, `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans`.
2. If the folder does not exist or holds no other open plan, record "No other plans in v<MAJOR>.<MINOR>; nothing to compare." and continue. Do not run the helper on a missing folder (exit 2).
3. Otherwise run `scripts/replan_minor.py` on that folder. `/plan` runs it after the draft plan file is written into the folder, so the new plan is part of the set. `/compare` has no plan file yet, so it runs against the existing plans and reads the report against the comparison's adoption items: shared files, repeated work, and dependencies. Use `--claims-deps-only` when prose hints are noisy.
4. Turn the findings into proposals as described above and show them next to the version confirmation (`/compare`) or the phases table (`/plan`). Record the outcome, including "no change proposed", in the report's `## Queued-plan impact` section (`/compare`) or the plan's `## Queued predecessors` section (`/plan`).
5. Never apply a proposal without approval, and never edit the prose of an existing member plan. An approved change that touches existing plans goes through the Renumber procedure or a plan edit the user confirmed for that plan; a plan the user already confirmed or that is in progress is pinned. Declined proposals leave every file as written.

## Placement rule for a new plan

This skill owns which version a NEW plan or comparison takes. `[[cross-project-comparison]]` Step 6.5 and `[[implementation-plan]]` Step 4.6 call this rule; neither restates it. The goal is that version order equals release order. Independent plans may implement concurrently; actual prerequisites and ownership decide implementation admission.

1. **Rank the new plan against the queue.** Use the inventory from Step 1 and the membership from Step 2. For each queued plan, decide whether the new plan must precede it (it unblocks it, changes the same surfaces first, or the user ranks it higher) or may follow it. Existing plans count as ordered as long as the latest queue assessment's placement still holds; re-rank them only when the new plan changes their order.
2. **Find the target range.** The new version must sort after every plan it follows and before every plan it must precede, comparing parsed integers, never strings. A slot is free when no plan (queued, in flight, or shipped) and no release tag holds that exact version.
3. **Prefer a free lower slot.** Take the lowest free version in the range, typically the next patch after the last release or an unused patch between two queued plans. No renumber is needed. Report the version with a one-line reason.
4. **When the range holds no free slot, propose a renumber.** List every move (old version to new version, with its reason) and, per moved plan, the seven reference classes of the Renumber procedure below to repair. Confirm with the user before anything moves, then hand the move to `[[docs-layout-refactor]]` and the reference repair to `[[project-refactor]]`. A plan already mid-implementation is not moved without the maintainer's explicit decision (see the mid-implementation case).
5. **Never take a free slot that sorts after a plan the new one must precede.** A free slot in the wrong place is exactly how version order stops meaning release order.

## Renumber procedure

Renumbering rewrites version identity that merged pull requests, changelogs, and published documentation already reference. It is the highest-blast-radius operation this skill touches.

1. **Propose.** Present the new order with the reason per move. Wait for explicit confirmation. Silence is not approval.
2. **Move the tree** via `[[docs-layout-refactor]]`. Do not reimplement the move. **A swap needs a temporary name**: moving tree A onto tree B directly collides, so go A to temp, B to A, temp to B. Every real swap has needed this.
3. **Rename** the plan and comparison files to their new version prefix.
4. **Repair every reference class** via `[[project-refactor]]`. All seven have been observed in practice:
   1. Intra-tree version strings (`**Version**:`, `**Filename**:`, body prose).
   2. Relative plan links from sibling version trees.
   3. Link-reference definitions (`[N8]: ../../..`), which a link-text-only scan misses entirely.
   4. Self-referential output paths inside the plan's own task lines.
   5. Tracker dashboard rows.
   6. Tracker prose and section headings.
   7. Committed implementation evidence under the moved tree.
5. **Prove the repair.** Run the residual-reference check; it fails on a single surviving reference.

    ```bash
    python scripts/enumerate_plan_queue.py --root . --check-residual v<OLD_VERSION>
    ```

    Exit 0 means no reference to the old version survives in repository Markdown or documentation JSON outside an explicit exemption; generated `data/` inventories and other file types are not scanned. Exit 1 lists every survivor with its file, line, and text. One survivor is a failure, because one broken link is a broken link. The check matches only `v`-prefixed forms, so a bare section number is never rewritten, and it exempts a line carrying a dated renumber note, because a historical claim is repaired with a note rather than a restatement. For a sealed historical JSON record that must retain its original bytes, review it and pass its narrow path prefix through `--skip`; the command prints every skipped prefix.

### Two traps a blanket rewrite hits

Both have occurred. Both must be checked by hand.

- **A bare section number is not a version.** A plan carrying the heading `#### 4.10 - Publication and integration` is corrupted by a `4.10 -> 4.12` substitution. Rewrite only `v`-prefixed forms.
- **A blanket rewrite cannot tell a plan's own version from a reference to another plan.** One observed swap corrupted eleven cross-references in a single plan, including its sequencing intent, which inverted. Two further statements were rewritten into factual falsehoods about what had been confirmed on a given date.

**Repair a historical claim with a dated note, never a silent restatement.** "The user confirmed v4.10.0 on 2026-09-09" does not become "v4.11.0" because the plan moved; it becomes the original claim plus what changed and when.

### The mid-implementation case

Renumbering a plan whose phases are already committed costs more than the rename. The committed implementation must be re-applied at the new paths, and in practice that means all of:

1. **Cherry-picking will conflict.** The rename and the phase edits touch the same files, so the picks fail on the plan file and the tracker.
2. **Reconstruct the branch from the integration branch instead.** Take the path-stable files (source, tests) from the old branch tip, then re-write the moved documentation at its new paths.
3. **Per-phase commits collapse into one.** State that in the commit message and name where the per-phase record survives, which is the session-history files.
4. **Re-apply the plan's own checkbox state and status line**, because the plan file moved with the tree and its progress markers came from commits that no longer apply cleanly.

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
| "Impact on the harness is basically obvious, I can just assert the order." | It is a judgment, which is exactly why it must be recorded with reasoning. An asserted ranking cannot be argued with or revisited. |
| "I could not read that plan, so it probably does not matter." | An unreadable plan is an explicit unknown. It is the one most likely to surprise you, not the one safest to ignore. |

## Verification

- [ ] `python scripts/enumerate_plan_queue.py --root .` ran, and its exit code and findings are recorded.
- [ ] Queue membership was established from declared status or an explicit maintainer statement, never inferred from open task counts.
- [ ] Every queued plan carries exactly one verdict, and every verdict names its evidence.
- [ ] Every unreadable or undeclared-status plan appears as an explicit unknown.
- [ ] Overlapping surfaces are listed as paths, not asserted.
- [ ] Concurrent candidates have complete dependency/read/write inventories, coordinator-owned metadata deltas, named unknowns and serial fallback; release predecessors are distinguished from actual implementation prerequisites.
- [ ] The written artifact exists and states the recommended order with a reason per position.
- [ ] Impact-on-harness is recorded as a judgment with reasoning, not presented as a computed score.
- [ ] No claim was made that re-sequencing improves delivery speed.
- [ ] For a minor, `scripts/replan_minor.py` ran against its plans folder, its exit code is recorded, and every proposal derived from it was shown to the user and is marked approved, declined, or advisory (frozen).
- [ ] No plan file changed without an approved proposal for it.
- [ ] If a renumber was performed, the residual-reference check ran and passed, and every historical claim was repaired with a dated note rather than a restatement.

## Related Skills

- `[[implementation-plan]]` -- authors the plans this skill assesses; owns the plan template and the queued-predecessor section this skill fills.
- `[[implement-phase]]` -- executes them; owns the phase gates and the `## Plan delta` vocabulary this skill supplies evidence to.
- `[[cross-project-comparison]]` -- records and confirms the adoption target; calls this skill's placement rule (Step 6.5) and queue-impact check (Step 6.6).
- `[[docs-layout-refactor]]` -- owns moving a documentation tree; the renumber procedure delegates the move.
- `[[project-refactor]]` -- owns reference repair across a move.
- `[[known-gaps-tracker]]` -- records an unresolved verdict that cannot be closed now.
- `[[verification-before-completion]]` -- owns what counts as evidence for a claim; this skill's written-artifact requirement is that rule applied to queue checks.
