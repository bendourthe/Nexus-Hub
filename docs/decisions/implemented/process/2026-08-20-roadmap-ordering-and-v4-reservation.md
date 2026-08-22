# Decision: Plan order lives in a table, and v4.0.0 is reserved for changed install behavior

Status: implemented - new plans are named by slug with a Target version field inside, existing filenames are frozen as historical identifiers, and v4.0.0 will land only the queued plans that change what an installed Nexus-Hub does (three as of 2026-08-21) **Naming half SUPERSEDED 2026-08-21** by [2026-08-21-plan-filenames-track-target-version](2026-08-21-plan-filenames-track-target-version.md): filenames are no longer frozen and now track the target version. The v4.0.0 reservation below stands.

## Problem

Two problems with one root, both about what a number is allowed to mean.

**Plan filenames encoded priority, and priority moved.** The 2026-08-07 prioritization pass ranked 12 unimplemented plans and renamed their files to carry the order. It closed with an explicit warning: "Numbering must stop encoding authoring order. The durable fix is to name plans by slug and record the target version inside the document, so a priority change is a one-line edit rather than a rename of two files plus every cross-reference."

That warning came true in thirteen days. Six plans (`v3.17.6` through `v3.17.11`) were authored afterwards and numbered by authoring order again, so the document explaining sequence did not know they existed. One ranking reversed by ten places with no recorded reason: the presentify plan was ranked 12th of 12 at `v3.20.1` on the grounds that it is "an opt-in enhancement to one command, narrowest audience on the list", and now exists as `v3.17.8-presentify-slide-navigation.md`. Either the ranking was wrong or the re-slot was, and nothing on disk says which.

A filename-encoded order also invites automated repair. A prior version-string sweep rewrote the table's "Filename says" column to agree with its "Target version" column, which destroyed the only information the table existed to carry.

**v4.0.0 had no declared meaning.** With fourteen plans queued and none draining, the obvious reading is that the major bump arrives when the list is finished. That reading is wrong in a way that matters to users rather than to maintainers: Nexus-Hub is installed from `main` via `nexus-hub upgrade`, so the major version is the ONLY advance warning an installed user gets that something about their install is about to change. v3.0.0 already set that meaning with the 40-shim command migration. Twelve of the fourteen queued plans break nothing, so shipping them under a major would signal breakage that does not exist and retroactively redefine what v3.0.0 meant.

## Decision

**Order lives in `docs/v3/roadmap-prioritization.md`, not in filenames.** That table ranks all fourteen unshipped plans and is the single authority on sequence. New plans are named `<slug>.md` and carry a `**Target version**` field inside the document. Existing plan filenames are FROZEN as historical identifiers and are deliberately not renumbered, so re-prioritizing is a one-line table edit rather than a rename of two files plus every cross-reference.

Two consequences are load-bearing and easy to undo by accident:

- The table's "Filename says" column INTENTIONALLY contradicts its "Target version" column. That contradiction is the information. No automated version-string sweep may touch this file. `check_version_sync.py` is verified safe here, covering only `data/marketplace.json`, both installers, `CHANGELOG.md`, `README.md`, and `AGENTS.md`; the standing risk is a broader find-and-replace during release prep.
- Renumbering existing files to match the table is explicitly out of bounds. It would be the third renumbering pass in a month, which is the exact cost slug-first naming exists to end.

**v4.0.0 is reserved for the changed-install-behavior bundle.** It will land `cost-effective-ci-cd` (changes the default CI lifecycle for consuming projects) and `agent-communication-overhaul` (changes installed agent behavior on every platform), under one migration note. It is not a backlog-completion milestone. `docs-lifecycle-retention` was considered for inclusion and excluded: it touches only Nexus-Hub's own `AGENTS.md` and `DEVLOG`, changing nothing about an install, so it moves up to rank 2 for its leverage instead.

**Amendment, 2026-08-21: the bundle has a third member.** `docs-lifespan-tree-and-enforcement` was authored on 2026-08-20, classified Breaking by its author, and confirmed into the bundle on 2026-08-21 after both of its breaking claims were verified against the repository rather than accepted from the plan.

The first claim is that an upgraded install reshapes the user's own documentation tree without being asked. `catalog/commands/update.md` states that `/update refactor` "and, at release, `/update release`" canonicalizes *that repo's* whole docs tree via the `docs-layout-refactor --canonicalize-layout` path, "so a project adopting Nexus-Hub gets the same migration with one command", and the `release` scope does run `refactor`. Verified.

The second is that it changes installed instruction content: its Phase 5 edits all 12 substantive `templates/ai-instructions/` files, which both installers copy recursively. That is the same test that placed `agent-communication-overhaul` in the bundle. Verified.

The comparison that settles it is with `docs-lifecycle-retention` above. Both are documentation plans; that one was excluded because its changes are repo-internal, and this one's stated purpose is to reach every install. Same subject matter, opposite answer, on a criterion that discriminates rather than a judgement call.

Two consequences are worth stating because they were weighed and accepted. The bundle now couples three plans, so a stall in any one delays the others, and three slip more easily than two. And the plan itself recorded a clean alternative that was NOT taken: making the migration strictly opt-in would drop it to a v3.20.x target, at the cost of most consuming repositories never adopting the standard, which is the plan's whole purpose. Choosing the reservation over the escape hatch is the deliberate trade.

## Alternatives considered

- **Ship v4.0.0 at the end of the current plan list, as a completion milestone.** Rejected on three independent grounds. It signals breakage that does not exist across twelve of the fourteen plans. The list gained six plans in thirteen days while draining none, so a target defined as "when the list is done" slips indefinitely and communicates nothing. And it retroactively redefines what v3.0.0 meant, since that major was cut for a migration users had to act on rather than for a volume of finished work.
- **Never cut a major; keep incrementing minors.** Rejected because the two genuinely breaking plans would then ship inside a minor, giving an installed user no advance warning at the one place they would look for it. This is the failure the reservation exists to prevent, not a conservative alternative to it.
- **Renumber all thirteen existing plan files to match the new order.** Rejected on cross-reference churn for no gain the table does not already provide. It is also self-defeating: it re-encodes order into filenames immediately after deciding that filenames must stop carrying it, guaranteeing a fourth pass the next time priority moves.
- **Keep filename-encoded ordering and simply be more disciplined about renames.** Rejected because it was already tried. The 2026-08-07 pass adopted exactly that discipline and recorded the warning quoted above; the discipline lasted under two weeks against six new plans.

## Consequences

- **A plan's filename may disagree with its target version, and that is correct.** `v3.17.8-presentify-slide-navigation.md` may target something other than v3.17.8. A reader who trusts the filename over the table will be wrong, so the table has to be found first; it is linked from each new plan's `Rank` field for that reason.
- **The presentify ten-place move is left as an open reconciliation at rank 11.** The decision records the discrepancy rather than resolving it, because neither the original ranking nor the re-slot left a reason on disk and inventing one now would be worse than naming the gap.
- **Automated tooling over plan directories is now a hazard surface.** Anything enumerating `docs/v3/v3.*/plans` must sort NUMERICALLY on the parsed minor rather than lexically, or it orders v3.10, v3.18, and v3.20 before v3.5. A live instance of exactly that bug is recorded in the v3.17 known gaps.
- **v4.0.0 cannot be cut until every reserved plan is ready**, which couples them. If one stalls, the others wait, or the reservation is revisited by a new record rather than by quietly shipping one in a minor. The bundle held two plans when this was written and three from 2026-08-21, so the coupling cost grows with each addition and each addition should be argued on the changed-install-behavior test alone.
- **Twelve queued plans can now ship as minors without a versioning debate each time**, which is the practical benefit: the question "does this deserve a major" has one answer, checkable against a two-item list.
