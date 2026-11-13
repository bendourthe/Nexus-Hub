# Decision: Release trains and standalone infrastructure pull requests

Status: implemented - consecutive finished plans release as one train, infrastructure that every plan benefits from ships outside plan order, and /status moves into v4.15.1; the checker change and the develop setting are still to be applied
Date: 2026-11-13
Author: Ben Dourthe
Template: Nygard

## Problem

A minor run publishes its member plans in version order, and each member's start had to contain the previous member's release tag. Three effects followed.

First, a plan that finishes early cannot start the next member until the previous member is released, tagged and merged back, and its release needs the next member when the two plans depend on each other (v4.15.4 and v4.15.8 must reach users together, so neither tag can come first). That is a wait that cannot end.

Second, work that every plan benefits from, such as a faster CI pipeline or a checker rule, waits for its numbered place in the queue while every other plan pays its cost, and a plan numbered v4.15.12 ships last even when the maintainer wants its result first (the `/status` command and the progress footer).

Third, the `develop` branch requires every pull request to be up to date with `develop` before merging. A queue of consecutive plan pull requests then forces a rebase and a new 50-minute CI run each time another one merges.

## Decision

Release consecutive finished plans as a train:

- Each plan pull request merges into `develop` as soon as that plan finishes.
- When every member of the train has integrated, one release pull request bumps every version in the train and adds each changelog section, and one develop-to-main pull request ships them.
- Each version still gets its own tag and its own GitHub Release. No back-merge pull request is needed when `develop` already holds every released file.
- The completion checker accepts a member whose start contains the previous member's integration merge instead of its release tag. That change ships as a standalone pull request (branch `fix/minor-train-member-gate`) and is released with v4.15.1. Until it ships, a train member that depends on a not-yet-tagged predecessor cannot be admitted.

Ship infrastructure that every plan benefits from as a standalone pull request outside plan order. The CI test split (the Linux matrix and the Windows job split, formerly Phases 2 and 3 of the v4.15.7 plan) ships on branch `ci/split-slow-test-jobs`, and the member-gate rule ships on branch `fix/minor-train-member-gate`. The plan that owned the work keeps its ids, marks the phases as moved, and ticks nothing; v4.15.7 keeps its audit script, its optional Phase 4, and its final phase, and measures the standalone result.

Fold the v4.15.12 plan (status command and progress footer) into v4.15.1, the next release, as Phases 2b to 2d (tasks T120 to T132), placed before v4.15.1's final phase. v4.15.12 becomes a pointer file, as v4.15.10 did when it was folded into v4.15.4 and v4.15.8.

Turn off the repository setting "Require branches to be up to date before merging" on `develop` only. This is a repository setting that the maintainer changes by hand; no script changes it. `main` keeps the setting. The required checks still run on each pull request against the merge result as of its last run, so a plan is tested before it lands; they do not re-run when another pull request merges first.

## Alternatives considered

- **One release per plan, each tagged before the next plan starts.** The existing behavior. It keeps every release small, but it serializes finished plans behind hosted checks and cleanup, and it cannot release two plans that must reach users together. Declined.
- **Keep v4.15.12 last in version order.** No renumbering and no fold, but the maintainer would wait for every other v4.15 plan to ship before getting `/status` and the footer. Declined; the fold costs one plan file and a new set of task ids.
- **Keep the CI test split inside v4.15.7.** One owner for the pipeline work and a single plan-level measurement, but the speed-up would arrive only after v4.15.7's place in the queue, and every plan implemented before it would pay for the slow pipeline. Declined.
- **Renumber plans so the status work is v4.15.1 and the others shift.** Moves the same content with one more plan-file rewrite, and the checker hardcodes the v4.15 member versions until the v4.15.4 task T052 lands, so renumbering is risky. Declined.
- **Add a merge queue on `develop`.** It would serialize merges and test each one on the merge result without a manual rebase, but it adds a service to configure and another required status context, which the required-checks contract treats as a risk. Declined for now; revisit if the unchecked up-to-date setting produces a bad merge.
- **Turn the up-to-date setting off on both `develop` and `main`.** Removes the rebase cost everywhere, but `main` receives only release merges and loses its guarantee that the shipped tree is the tested tree. Declined.
- **Keep the up-to-date setting on `develop`.** Safest for merge results, and slow: each merge to `develop` forces every open pull request to update and run CI again. Declined.

## Consequences

- Plans finish faster than they release. The release of a train needs one release pull request instead of one per plan, and the changelog carries one section per version.
- The train rule is only valid with the checker change. Until `fix/minor-train-member-gate` is merged, the member gate still requires the previous release tag. That pull request is the first item to merge and is released with v4.15.1.
- v4.15.4 and v4.15.8 release as one train (their ordering comment is updated in both plans). No released version reads the approval mode as `manual` only because the Settings control is missing.
- The v4.15.7 plan no longer promises the 30-minute CI result. It records the result as a measurement against the standalone pull request, and a miss becomes a known gap against that pull request. The moved tasks stay unticked, and the completion checker counts every task line, so the maintainer must decide at the next run approval page how those nine moved tasks are treated (tick them after the standalone merge, or record them through a known-gap migration).
- v4.15.1 now carries thirteen definition-of-done items and six phases, and a run record that froze its earlier hash must be approved again against the amended file.
- With the up-to-date setting off on `develop`, two pull requests can each pass CI alone and fail together. The checks ran against the `develop` tip of the pull request's last run, so a conflict between the two can reach `develop`; the post-merge workflow on `develop` is the next place it shows. The setting change is manual and is not part of this commit.
