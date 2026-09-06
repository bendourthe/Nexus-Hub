# Roadmap Prioritization

**Created**: 2026-08-07 (covering the 12 unimplemented plans in `docs/v3/v3.16/` and `docs/v3/v3.17/`)
**Revised**: 2026-08-20 (covering all 14 unshipped plans, adopting slug-first plan naming, and designating v4.0.0)
**Amended**: 2026-08-21 (confirming `docs-lifespan-tree-and-enforcement` as the third v4.0.0 bundle member, taking the ranked total to 15)
**Reordered**: 2026-08-21 (promoting `presentify-slide-navigation` from rank 11 to rank 4 by maintainer direction, and renaming all 14 unshipped plan files so every filename matches its target version)
**Relocated**: 2026-08-21 (moving every unshipped plan into the directory matching its target version, moving the six coupled comparison reports with them, and fixing three fail-open defects in the co-location gate that the move exposed)
**Amended**: 2026-08-24 (inserting `adoption-skill-trial-records-and-low-evidence-ts` at v4.1.0 as rank 15 by maintainer direction, and moving `interactive-guide-redesign` last to v4.2.0 as rank 16)
**Amended**: 2026-08-24 (inserting `plan-implement-lifecycle-and-docs-architecture` at v3.21.0 as rank 12, bumping the v4.0.0 bundle to ranks 13-15, v4.1.0 to rank 16, and v4.2.0 to rank 17)
**Amended**: 2026-08-29 (appending `guide-visual-education` at v4.2.1 as rank 18, after the unpublished v4.2.0 guide redesign)
**Purpose**: establish a priority order for unshipped work, classify each plan as patch, feature, or breaking, and make the ORDER readable from one place instead of from filenames.

---

## Why this document was revised

The 2026-08-07 pass ranked 12 plans and closed with a warning: "Numbering must stop encoding authoring order. The durable fix is to name plans by slug and record the target version inside the document, so a priority change is a one-line edit rather than a rename of two files plus every cross-reference."

That warning came true within thirteen days. Three things happened:

1. **Six new plans were authored** (`v3.17.6` through `v3.17.11`) and numbered by authoring order again. This document did not know they existed, so the only artifact explaining sequence was silently incomplete.
2. **One ranking was reversed without a recorded reason.** The presentify plan was ranked 12th of 12 here, at `v3.20.1`, on the grounds that it is "an opt-in enhancement to one command, narrowest audience on the list." It now exists as `v3.17.8-presentify-slide-navigation.md`, a jump of ten places. Either the ranking was wrong or the re-slot was, and nothing on disk says which.
3. **A cross-project comparison landed** (the cybersecurity skills library, 2026-08-20) whose adoption target was initially resolved as `v3.17.12` on the false premise that v3.17.11 was the last planned version. Plans already existed through `v3.20.0`. The resolution rule in the comparison skill walks forward through plan directories, and it produced a wrong answer because the directory listing it walked was read in alphabetical order, placing `v3.18` before `v3.5`.

Each of these is the same root cause: **priority lives in filenames, and filenames are expensive to change, so they stop being changed and drift from the real order.**

## The naming rule (revised 2026-08-21)

**The ranking table below remains the single authority on sequence.** What changed on 2026-08-21 is the naming rule that sat alongside it.

The 2026-08-20 pass froze existing filenames and named new plans by slug alone, on the estimate that renaming would cost "thirteen files plus every cross-reference to them". That estimate was wrong. The measured cost was **14 files and 22 references, of which only 6 needed repair**. The other 16 sit in frozen historical records that the repository's own precedent leaves untouched (stated at `docs/v3/v3.16/docs-cleanup-report.md` and `docs/v3/v3.16/known-gaps.md`: live references are repaired, a record of what was true at the time is not).

The frozen-filename rule also failed its first contact with a reader. Within a day of being written it produced exactly the confusion it was meant to prevent, because a filename reading `v3.17.8` while the plan targets something else is not a neutral historical identifier; it is a wrong answer sitting in the most visible place.

- **Every unshipped plan filename now matches its target version.** All 14 were renamed on 2026-08-21.
- **The `**Filename**` field is removed from plan headers.** It rotted in 2 of the 2 files that carried it, both naming a file that did not exist. A file's name is authoritative for itself and needs no field restating it.
- **Each plan carries `**Target version**` and `**Rank**`**, the latter linking back to this table so a reader who arrives at a plan file first can still find the authority.
- **Re-prioritizing now costs a rename plus two field edits per moved plan, and one edit to this table.** That is the honest price. It was paid on 2026-08-21 and is expected to be paid again.
- **Every unshipped plan now lives in the directory matching its target version**, done 2026-08-21 after the rename pass left `docs/v3/v3.17/plans/` holding v3.18, v3.20, and v4.0 plans. A filename that agrees with its target while sitting in a directory that disagrees is the same defect one level up.
- **The six coupled comparison reports moved with their plans**, were renamed to their new target, and had their `Adoption target` field updated. This is forced, not cosmetic: the co-location gate requires a plan and its seeding comparison to share a version directory, AND requires a comparison to sit in the directory its own `Adoption target` names. Moving a plan alone breaks the first rule; moving the pair without retargeting breaks the second.
- **The four v4.x plans moved to a new `docs/v4/` tree**, which is what exposed the gate defects below.
- Still deferred: a flat `docs/plans/` queue directory. Rank 15 (`docs-lifespan-tree-and-enforcement`) owns container layout, so that decision belongs to it.

## The classification used

**Patch**: fixes behavior that is already shipped and wrong, or is contained to one skill or one document. No new user-facing capability, no new subsystem, no change to what gets installed.

**Feature (minor)**: adds a capability, a subsystem, or a new skill cluster, or changes what an install produces.

**Breaking (major)**: changes what an ALREADY-INSTALLED Nexus-Hub does, without the user asking for the change. This is a narrower test than "large" or "risky". See the v4.0.0 section.

## v4.0.0: reserved for changed install behavior

**Decision (2026-08-20): v4.0.0 is not a completion milestone. It is the release that lands the breaking bundle.**

Nexus-Hub is a catalog consumed directly from `main` by an installer, and users upgrade with `nexus-hub upgrade` rather than by pinning a version and reading release notes first. The major-version bump is therefore the only advance warning a user gets that their configuration is about to behave differently. That makes the signal load-bearing, and it means spending it on a release that breaks nothing would leave the next genuinely breaking release with no way to announce itself.

The repository's own precedent set this meaning: v3.0.0 was the command migration, forty deprecation shims with real migration cost, removed in v3.2.0.

Three reasons the alternative ("ship v4.0.0 when the current list is done") was rejected:

- It signals breakage that does not exist across twelve of the fifteen queued plans.
- The list is not a fixed target. It gained six plans in thirteen days while draining none, so a version pinned to backlog completion slips indefinitely, and the pressure to declare completion pulls scope into the release rather than letting it ship.
- It redefines what v3.0.0 meant, retroactively.

**Three plans qualify** on the changed-install-behavior test, and they share one coherent story, so they ship together. The third was confirmed on 2026-08-21, after the first two:

| Plan | What changes for an existing install |
|---|---|
| `cost-effective-ci-cd` | Makes repository-native end-of-plan CI/CD the default lifecycle for every consuming project, and migrates Nexus-Hub's own workflows to it. A project that upgrades inherits a different CI contract. |
| `agent-communication-overhaul` | Changes how every installed agent communicates across all supported platforms. The distributed instruction templates change, so agent behavior changes on upgrade. |
| `docs-lifespan-tree-and-enforcement` *(added 2026-08-20, CONFIRMED 2026-08-21)* | Renames the prescribed docs containers to `docs/releases/` + `docs/archives/`. Qualifies on two counts: `/update release` canonicalizes a consuming repo's whole docs tree via `docs-layout-refactor --canonicalize-layout`, so an upgraded install reshapes the user's docs tree without being asked; and it edits all 12 substantive distributed instruction templates, the same test that qualified `agent-communication-overhaul`. Ships third in the bundle. The alternative - making canonicalization strictly opt-in, which would drop it to v3.20.x - is recorded in the plan's Version classification section and was not chosen. |

**Explicitly NOT in the bundle**, having been considered:

- `docs-lifecycle-retention` relocates sections of Nexus-Hub's own `AGENTS.md` and archives its DEVLOG. Both are repo-internal, not distributed to users, so nothing about an install changes. It is a high-leverage internal refactor and ships early, at rank 2.
- The two new skill categories from `adoption-cybersecurity-skills` (`ot-security`, `mobile-security`) are purely additive. Adding a category breaks nothing; reorganizing existing ones would.
- `agent-memory-substrate` is a new subsystem, which is additive by definition.

v4.0.0 must carry a migration note covering both changes, per the capability-usage gate in `catalog/commands/update.md`.

## Priority ranking

Ranked on **leverage** (does shipping this make later work cheaper or safer?), then **user-visible value**, then **containment** (can it ship without dragging other plans with it?).

Filenames now agree with targets, so the former `Filename says` column has been removed rather than left to drift. One caution survives it: this document must never receive an automated version-string sweep. It names version numbers as data about other documents, not as its own version, and a sweep that treats them as the latter corrupts the ranking.

| Rank | Plan | Target version | Class | Why here |
|---|---|---|---|---|
| 1 | ci-gate-and-branch-hygiene | v3.17.6 | Feature | **SHIPPED 2026-08-21.** No PR can be blocked by a required check its workflow cannot produce. Pure leverage: it removed a failure mode that silently blocked every later plan. |
| 2 | docs-lifecycle-retention | v3.18.0 | Refactor | Highest leverage of the unstarted work. `AGENTS.md` is at its context-pressure point and every later plan edits it; a 208k-word DEVLOG is unreadable to an agent. Doing this first makes each following plan cheaper. |
| 3 | github-usage-monitor-accuracy | v3.18.1 | Bug-fix | An active defect in shipped behavior: the drawdown is computed from a hardcoded multiplier table that no longer matches GitHub's meter. Contained to one extension, and it is wrong right now. |
| 4 | **presentify-slide-navigation** | **v3.18.3** | Feature | **Promoted from rank 11 on 2026-08-21 by maintainer direction, which closes the open reconciliation this document previously flagged.** The earlier ranking (last of twelve, on "narrowest audience") was a leverage judgment reasserted from the 2026-08-07 pass, never a decision; the promotion to `v3.17.8` was real intent the table had not recorded. Recorded here: it ships directly after the monitor fix. **Re-slotted 2026-08-22 from v3.18.2 to v3.18.3**: v3.18.2 was consumed by the GitHub Usage Monitor withdrawal, an unplanned bug-driven release that followed the v3.18.1 monitor fix. Prerequisites: none. |
| 5 | code-intelligence-hardening | v3.19.0 | Feature | Direct, measurable cost reduction on `nexus-code-search`, with a deterministic local harness to prove it. Contained to one subsystem. |
| 6 | agent-memory-substrate | v3.19.1 | Feature | A genuinely new subsystem. Ranked above its overlapping sibling because it DEFINES the substrate; the sibling consumes it. |
| 7 | rtk-and-meterless | v3.19.2 | Feature | **Needs a rewrite before implementation, not just a retarget.** Its memory portion overlaps rank 6 and its eval portion overlaps work already shipped in v3.16.1. See the findings below. |
| 8 | adoption-agent-security-layers | v3.20.0 | Feature | Catalog adoption, fully contained, all four items skill-native. Establishes the conditional `/review security` engagement pattern that rank 9 then reuses, so it must precede it. |
| 9 | adoption-cybersecurity-skills | v3.20.1 | Feature | High user value: doubles security-domain coverage from 40 to 80 skills and closes domains with zero current coverage. Depends on rank 8's engagement pattern. |
| 10 | interface-craft-skills | v3.20.2 | Feature | Five new design skills plus a coordinating review skill. Pure catalog growth with no dependencies, which is exactly why it can wait: nothing else is blocked on it. |
| 11 | skills-craft-and-prime-agent | v3.20.3 | Feature | Skills-authoring craft plus invocation-policy metadata and a prepared marketplace listing. The marketplace listing is the highest-value part and is separable if this slips. |
| 12 | plan-implement-lifecycle-and-docs-architecture | **v3.21.0** | Feature | **Inserted 2026-08-24.** Fail-closed last phase, `/implement in-full` and `phase-by-phase`, and living `docs/handbooks/` on the current `docs/v*` scheme. Ships on 3.x so the v4.0.0 bundle inherits the equivalent instead of declining it. |
| 13 | cost-effective-ci-cd | **v4.0.0** | **Breaking** | Changes the default CI lifecycle for every consuming project. Widest blast radius on the list, touching planning, implementation, commit, branch, and release. |
| 14 | agent-communication-overhaul | **v4.0.0** | **Breaking** | Changes how every installed agent communicates on every platform. Ships with rank 13 because both change installed behavior, and one migration note is cheaper for users than two. |
| 15 | docs-lifespan-tree-and-enforcement | **v4.0.0** | **Breaking** | **Added 2026-08-20; target CONFIRMED 2026-08-21** after both breaking claims were verified against the repository rather than accepted from this plan. Renames the prescribed docs containers, and `/update release` canonicalizes the change for consuming projects. Sequenced after rank 2 so the lifecycle work it builds on is already in place. **Amended 2026-08-24** to consume the v3.21.0 handbooks equivalent rather than declining it. |
| 16 | adoption-skill-trial-records-and-low-evidence-ts | v4.1.0 | Feature | **Inserted 2026-08-24 by maintainer direction, taking the v4.1.0 slot.** Catalog authoring (procedural runbooks, outcome-labeled distillation, confusable-trigger fences) plus TypeScript typed-boundary hygiene. Ships before the guide so the last plan can describe it. |
| 17 | interactive-guide-redesign | v4.2.0 | Feature | **Merged to develop 2026-08-29 (PR #145), not a public GitHub Release.** It describes the product rather than changing it, so it ran after the v4.0.0 bundle and the v4.1 catalog work. Maintainer visual QA rejected shipping that draft as the public 4.2 guide. |
| 18 | guide-visual-education | v4.2.1 | Feature | **Inserted 2026-08-29 by maintainer direction.** Next draft of the interactive guide: chrome and theme bugs, visual Foundations education, Training slideshow with Glow Booth, Cheatsheets merge. Public `/update release` targets v4.2.1 and must not tag the rejected v4.2.0 UI. |

## Findings that are not about ordering

**The RTK/Meterless plan should not be implemented as written.** Unchanged from the 2026-08-07 pass and now more true, since the evals work it overlaps has since shipped in v3.16.1. Retargeting it without rewriting it repeats the v3.15.12 failure, where a plan's stated premise had been overtaken by later work.

**The presentify reconciliation is closed.** Resolved 2026-08-21: the maintainer directed the plan to rank 4, immediately after the monitor fix. The 2026-08-07 ranking (last of twelve) and the unexplained promotion to `v3.17.8` were in genuine conflict, and this document flagged it rather than guessing. The promotion was deliberate; the table now records it.

**The comparison skill's version-resolution rule has a real bug, not just a stale input.** Its walk-forward step enumerates plan directories and stops at the first free slot. Directory enumeration is alphabetical by default, which orders `v3.10` and `v3.18` before `v3.5`, so the walk can terminate early and report a free slot that is not free. Any future automation over version directories must sort numerically on the parsed minor, never lexically. This produced a wrong adoption target on 2026-08-20 and was caught only by human review.

**Creating the `docs/v4/` tree exposed three fail-open defects in the co-location gate, all now fixed.** The `colocation` required check computed a single `CURRENT_MAJOR` with `sort -n | tail -1` and scoped its scan to that one tree, so the moment `docs/v4/` existed, every plan under `docs/v3/` stopped being checked while the gate still reported green. Two further holes were found alongside it: a `Seeded from` citing a file that does not exist passed, because the version directory was parsed out of the path string without ever opening the file; and a relative `../comparisons/x.md` reference was skipped entirely, because the extraction regex required a literal `docs/v` prefix. The third hole is why the first two went unnoticed: `v3.19.0-code-intelligence-hardening` and `v3.19.1-agent-memory-substrate` both cited comparison files under pre-rename slugs (`jcodemunch`, `optmem`) that had not existed for some time. The inline bash implementation moved to `scripts/check_doc_colocation.py` so the fixes could be unit-tested, it now runs in `make validate` as well as CI (it was CI-only before), and the `colocation` job name and unfiltered triggers are unchanged so the required context still resolves. Negative-controlled in both directions: the old logic reports CLEAN on a real v3 violation once a `docs/v4` tree exists, and the new script exits 1 on the same fixture.

**Twelve plans carry stale version citations in their body text, and each one is the implementer's job to fix.** The 2026-08-21 rename corrected filenames and header fields, not prose. Plan bodies still name known-gaps sections, self-referencing plan paths, and `/update release` steps by the old target, and several of those paths were already wrong before the rename (`v4.0.0-cost-effective-ci-cd` cites `docs/v3/v3.16/plans/` with a slug that never existed). Rewriting roughly 35 instruction lines across six plan documents was deliberately NOT done in a renaming pass: a mis-edited phase instruction misdirects an implementation, and the citations have to be right at implementation time regardless. Each retargeted plan therefore carries a `**Retargeted**` header line naming the old version and stating that the Target version governs. Reconcile the prose when the plan is picked up.

**Filenames are renumbered when priority changes, and that is now the accepted cost.** The 2026-08-20 position was the opposite, on a cost estimate that measured 22 references where 6 needed repair. Three renumbering passes in a month argued for freezing names; the fourth pass argued the other way, because a filename that contradicts the plan inside it misleads every reader who trusts it. The table remains the authority, and each plan's `**Rank**` field points here.
