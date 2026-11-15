# Decision: CI test shards guarded by a partition proof

Status: implemented - the slow Linux and Windows test jobs run as shards, and a partition proof fails CI when a shard set loses or duplicates a test file.
Date: 2026-11-13
Author: Ben Dourthe
Template: Nygard

## Problem

A full-scope CI run took a mean of 43.5 minutes (median 39.6) across the 10 most recent green runs of `ci.yml`, and every plan's final phase and every re-push waited for it. The longest jobs were `tests-windows-validators-2` (mean 37.6 minutes), `tests-windows` (35.4), `tests` on Linux (27.6) and `tests-hooks` on Linux (21.1). Splitting a job into shards shortens the run, but a shard list maintained by hand can silently drop a test file or run one twice, and a green run would not show it.

## Decision

Split the slow jobs into shards defined in `scripts/ci/profiles.py`, the repository-native source of truth that CI and `python scripts/ci/run.py --profile full` share:

- Linux `tests` becomes three legs (`tests-validators`, `tests-governance`, `tests-core`), and `tests-hooks` becomes two legs, with the heavy hook files named once in `HOOK_HEAVY_FILES` and shared with Windows.
- Windows `tests-windows` splits its hook tests into a second job, `tests-windows-hooks-rest`, and the validator quarter that took 37.6 minutes splits into `tests-windows-validators-2` and a new `tests-windows-validators-4`. Windows shards are balanced by process launches, from per-command times in CI artifacts, not by test count.
- `tests/validators/test_ci_partition_proof.py` collects every sharded root unsharded and per shard, and fails unless the shard sets are pairwise disjoint and their union equals the unsharded collection. It runs on Linux and on Windows.
- Required checks stay as declared: only the aggregate `ci-required` is required, every new job is wired into `report` and `ci-required`, `docs/policy/required-checks.json` is unchanged, and no new job widens `permissions:`.

This work was taken out of plan v4.15.7 (its former Phases 2 and 3) and ships as a standalone pull request, so every later plan's CI rounds are shorter; the process decision is recorded as `2026-11-13-release-trains-and-standalone-infrastructure-prs` under `docs/decisions/implemented/process/`.

## Alternatives considered

- **Keep the jobs whole and wait for v4.15.7 in plan order.** Rejected by the maintainer on 2026-11-13: v4.15.1 to v4.15.6 would each pay the slower rounds first.
- **Shard by test count or by a pytest plugin such as random splitting.** Rejected: on Windows the cost is dominated by child-process launches, so equal counts give unequal times, and a random split is not reproducible locally with `run.py`.
- **Shard without a proof and rely on review of the shard lists.** Rejected: a dropped file passes CI silently, which is the failure the proof exists to catch; the proof was made to fail on purpose (a file dropped from every shard, and a file placed in two shards) before it was accepted.
- **More Linux legs (the plan's four-leg option).** Not used: the existing `tests-hooks` job already covers the hook legs, so a fourth leg would duplicate it.

## Consequences

- The total job count rises from 26 to 31, under the 40-job limit, and each shard writes its own JUnit file, so later rebalancing uses measured per-file times.
- The after-time is estimated, not measured, until the pull request's first run; the Windows hook split uses a Linux per-file proxy, so it may need one rebalance.
- `guide-render` (engine leg, mean 20.3 minutes, max 27.3) becomes the longest job and was outside this change; if it stays the long pole, splitting it is a follow-up.
- Adding a test file under a sharded root needs no shard edit when it falls under an existing glob; a file that falls under none fails the partition proof until it is assigned.
