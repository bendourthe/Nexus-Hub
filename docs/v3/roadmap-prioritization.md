# Roadmap Prioritization

**Created**: 2026-08-07 (covering the 12 unimplemented plans in `docs/v3/v3.16/` and `docs/v3/v3.17/`)
**Revised**: 2026-08-20 (covering all 14 unshipped plans, adopting slug-first plan naming, and designating v4.0.0)
**Purpose**: establish a priority order for unshipped work, classify each plan as patch, feature, or breaking, and make the ORDER readable from one place instead of from filenames.

---

## Why this document was revised

The 2026-08-07 pass ranked 12 plans and closed with a warning: "Numbering must stop encoding authoring order. The durable fix is to name plans by slug and record the target version inside the document, so a priority change is a one-line edit rather than a rename of two files plus every cross-reference."

That warning came true within thirteen days. Three things happened:

1. **Six new plans were authored** (`v3.17.6` through `v3.17.11`) and numbered by authoring order again. This document did not know they existed, so the only artifact explaining sequence was silently incomplete.
2. **One ranking was reversed without a recorded reason.** The presentify plan was ranked 12th of 12 here, at `v3.20.1`, on the grounds that it is "an opt-in enhancement to one command, narrowest audience on the list." It now exists as `v3.17.8-presentify-slide-navigation.md`, a jump of ten places. Either the ranking was wrong or the re-slot was, and nothing on disk says which.
3. **A cross-project comparison landed** (the cybersecurity skills library, 2026-08-20) whose adoption target was initially resolved as `v3.17.12` on the false premise that v3.17.11 was the last planned version. Plans already existed through `v3.20.0`. The resolution rule in the comparison skill walks forward through plan directories, and it produced a wrong answer because the directory listing it walked was read in alphabetical order, placing `v3.18` before `v3.5`.

Each of these is the same root cause: **priority lives in filenames, and filenames are expensive to change, so they stop being changed and drift from the real order.**

## The fix adopted (2026-08-20)

**The ranking table below is the single authority on sequence.** Filenames are no longer the ordering mechanism.

- **New plans are named by slug only**, with no version prefix: `adoption-cybersecurity-skills.md`, not `v3.20.1-adoption-cybersecurity-skills.md`. Each carries a `**Target version**` field inside the document.
- **Existing plan filenames are frozen as historical identifiers.** They are not renumbered. Renaming thirteen files plus every cross-reference to them would be the third renumbering pass and would buy nothing that this table does not already provide. Where a filename's embedded version disagrees with its target version below, the table wins.
- **Re-prioritizing is now a one-line edit** to this table, plus a one-line edit to the plan's `Target version` field.
- Deferred, deliberately not done in this pass: migrating all plans to a flat `docs/plans/` directory. That would fully decouple location from version but costs a thirteen-file move and a cross-reference sweep. Revisit if this table proves insufficient.

## The classification used

**Patch**: fixes behavior that is already shipped and wrong, or is contained to one skill or one document. No new user-facing capability, no new subsystem, no change to what gets installed.

**Feature (minor)**: adds a capability, a subsystem, or a new skill cluster, or changes what an install produces.

**Breaking (major)**: changes what an ALREADY-INSTALLED Nexus-Hub does, without the user asking for the change. This is a narrower test than "large" or "risky". See the v4.0.0 section.

## v4.0.0: reserved for changed install behavior

**Decision (2026-08-20): v4.0.0 is not a completion milestone. It is the release that lands the breaking bundle.**

Nexus-Hub is a catalog consumed directly from `main` by an installer, and users upgrade with `nexus-hub upgrade` rather than by pinning a version and reading release notes first. The major-version bump is therefore the only advance warning a user gets that their configuration is about to behave differently. That makes the signal load-bearing, and it means spending it on a release that breaks nothing would leave the next genuinely breaking release with no way to announce itself.

The repository's own precedent set this meaning: v3.0.0 was the command migration, forty deprecation shims with real migration cost, removed in v3.2.0.

Three reasons the alternative ("ship v4.0.0 when the current list is done") was rejected:

- It signals breakage that does not exist across twelve of the fourteen queued plans.
- The list is not a fixed target. It gained six plans in thirteen days while draining none, so a version pinned to backlog completion slips indefinitely, and the pressure to declare completion pulls scope into the release rather than letting it ship.
- It redefines what v3.0.0 meant, retroactively.

**Two plans qualify** on the changed-install-behavior test, and they share one coherent story, so they ship together:

| Plan | What changes for an existing install |
|---|---|
| `cost-effective-ci-cd` | Makes repository-native end-of-plan CI/CD the default lifecycle for every consuming project, and migrates Nexus-Hub's own workflows to it. A project that upgrades inherits a different CI contract. |
| `agent-communication-overhaul` | Changes how every installed agent communicates across all supported platforms. The distributed instruction templates change, so agent behavior changes on upgrade. |
| `docs-lifespan-tree-and-enforcement` *(added 2026-08-20, PENDING CONFIRMATION)* | Renames the prescribed docs containers to `docs/releases/` + `docs/archives/`. Qualifies on two counts: `/update release` canonicalizes a consuming repo's whole docs tree via `docs-layout-refactor --canonicalize-layout`, so an upgraded install reshapes the user's docs tree without being asked; and it edits all 12 substantive distributed instruction templates, the same test that qualified `agent-communication-overhaul`. Ships third in the bundle. The alternative - making canonicalization strictly opt-in, which would drop it to v3.20.x - is recorded in the plan's Version classification section and was not chosen. |

**Explicitly NOT in the bundle**, having been considered:

- `docs-lifecycle-retention` relocates sections of Nexus-Hub's own `AGENTS.md` and archives its DEVLOG. Both are repo-internal, not distributed to users, so nothing about an install changes. It is a high-leverage internal refactor and ships early, at rank 2.
- The two new skill categories from `adoption-cybersecurity-skills` (`ot-security`, `mobile-security`) are purely additive. Adding a category breaks nothing; reorganizing existing ones would.
- `agent-memory-substrate` is a new subsystem, which is additive by definition.

v4.0.0 must carry a migration note covering both changes, per the capability-usage gate in `catalog/commands/update.md`.

## Priority ranking

Ranked on **leverage** (does shipping this make later work cheaper or safer?), then **user-visible value**, then **containment** (can it ship without dragging other plans with it?).

The `Filename says` column records the version embedded in the plan's current filename, which is frozen and may disagree with the target. It is written in backticks deliberately: an earlier automated sweep over version strings rewrote this kind of column into the new numbers and made the table contradict itself, which is the same class of error this document exists to prevent.

| Rank | Plan | Target version | Filename says | Class | Why here |
|---|---|---|---|---|---|
| 1 | ci-gate-and-branch-hygiene | v3.17.6 | `v3.17.6` | Feature | In flight. No PR can be blocked by a required check its workflow cannot produce. Pure leverage: it removes a failure mode that silently blocks every later plan's PRs, and it is nearly done. |
| 2 | docs-lifecycle-retention | v3.18.0 | `v3.17.10` | Refactor | Highest leverage of the unstarted work. `AGENTS.md` is at its context-pressure point and every later plan edits it; a 208k-word DEVLOG is unreadable to an agent. Shipping this first makes all thirteen remaining plans cheaper to execute. Internal only, so it carries no install risk. |
| 3 | github-usage-monitor-accuracy | v3.18.1 | `v3.17.11` | Bug-fix | An active defect in shipped behavior: the drawdown is computed from a hardcoded multiplier table that no longer matches GitHub's meter. Contained to one extension. Smallest change with the highest certainty. |
| 4 | code-intelligence-hardening | v3.19.0 | `v3.18.0` | Feature | Direct, measurable cost reduction on `nexus-code-search`, with a deterministic local harness to prove it. Contained to one subsystem. |
| 5 | agent-memory-substrate | v3.19.1 | `v3.18.1` | Feature | A genuinely new subsystem. Ranked above its overlapping sibling because it DEFINES the substrate; the sibling consumes it. |
| 6 | rtk-and-meterless | v3.19.2 | `v3.18.2` | Feature | **Needs a rewrite before implementation, not just a retarget.** Its memory portion overlaps rank 5 and its eval portion overlaps work already shipped in v3.16.1. Must follow both and absorb what they shipped. |
| 7 | adoption-agent-security-layers | v3.20.0 | `v3.17.7` | Feature | Catalog adoption, fully contained, all four items skill-native. Establishes the conditional `/review security` engagement pattern that rank 8 then reuses, so it precedes it. |
| 8 | **adoption-cybersecurity-skills** | **v3.20.1** | *(slug-first, no version in filename)* | Feature | High user value: doubles security-domain coverage from 40 to 80 skills and closes domains with zero current coverage (threat intelligence, OT/ICS, cryptography, mobile, API security). Fully independent, so nothing is blocked on it, which is why it sits below the leverage items rather than above them. Depends on rank 7 only for the `/review security` pattern. |
| 9 | interface-craft-skills | v3.20.2 | `v3.19.1` | Feature | Five new design skills plus a coordinating review skill. Pure catalog growth with no dependencies, which is exactly why it can wait: nothing else is blocked on it. |
| 10 | skills-craft-and-prime-agent | v3.20.3 | `v3.19.2` | Feature | Skills-authoring craft plus invocation-policy metadata and a prepared marketplace listing. The marketplace listing is the highest-value part and is separable if this slips. |
| 11 | presentify-slide-navigation | v3.20.4 | `v3.17.8` | Feature | **Open reconciliation.** Ranked here on the original leverage logic: an opt-in enhancement to one command, narrowest audience on the list. Its filename says `v3.17.8`, a ten-place promotion made without a recorded reason. Confirm before scheduling: if the promotion was deliberate, record why here and move this row up. |
| 12 | cost-effective-ci-cd | **v4.0.0** | `v3.19.0` | **Breaking** | Changes the default CI lifecycle for every consuming project. Widest blast radius on the list, touching planning, implementation, commit, branch, and release guidance at once. Wants the guard from rank 1 and the docs work from rank 2 already in place. |
| 13 | agent-communication-overhaul | **v4.0.0** | `v3.17.9` | **Breaking** | Changes how every installed agent communicates on every platform. Ships with rank 12 because both change installed behavior, and one migration note should cover both. |
| 13b | **docs-lifespan-tree-and-enforcement** | **v4.0.0** | *(slug-first, no version in filename)* | **Breaking** | **Added 2026-08-20; target PENDING CONFIRMATION.** Requested as `v3.17.12` - the number the comparison skill's alphabetical-enumeration bug produced, and a slot that does not exist. Reclassified from Refactor to Breaking on the changed-install-behavior test: `/update release` canonicalizes a consuming repo's docs tree, and all 12 substantive instruction templates change. Ships with ranks 12 and 13 under one migration note. Wants rank 1's CI guard and rank 2's docs work in place first, and rank 2 touches the same `devlog-generation` and `docs/archive/` surfaces. |
| 14 | interactive-guide-redesign | v4.1.0 | `v3.20.0` | Feature | **Last by explicit direction.** It describes the product rather than changing it, so it must run after everything else in order to capture all updates, including the v4.0.0 behavior changes. Placing it earlier guarantees it ships describing a product that no longer exists. |

## Findings that are not about ordering

**The RTK/Meterless plan should not be implemented as written.** Unchanged from the 2026-08-07 pass and now more true, since the evals work it overlaps has since shipped in v3.16.1. Retargeting it without rewriting it repeats the v3.15.12 failure, where a plan's stated premise had been overtaken by later work.

**The presentify promotion is unexplained and should be resolved.** Rank 11 above is a judgment reasserted from the original pass, not a decision. Whoever moved it to `v3.17.8` had a reason or made a mistake, and this document cannot tell which. Resolve it by editing rank 11.

**The comparison skill's version-resolution rule has a real bug, not just a stale input.** Its walk-forward step enumerates plan directories and stops at the first free slot. Directory enumeration is alphabetical by default, which orders `v3.10` and `v3.18` before `v3.5`, so the walk can terminate early and report a free slot that is not free. Any future automation over version directories must sort numerically on the parsed minor, never lexically. This produced a wrong adoption target on 2026-08-20 and was caught only by human review.

**Filenames should stop being renumbered.** Three renumbering passes in a month is the signal. The table above is now the authority, and new plans are slug-named, so a fourth pass should not be necessary.
