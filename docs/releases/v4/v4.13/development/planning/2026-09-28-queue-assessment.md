# Plan Queue Assessment - 2026-09-28

This note records where the plans and comparisons written by six concurrent agent sessions on 2026-09-28 sit in the v4 queue, and why. It is for whoever next runs `/plan`, `/implement`, or `/update release` against v4.13 to v4.18, and covers queue membership, the version order (which is the execution order), placement reasons, parallel-compatible groups, and the unknowns left open. The ranking rules are owned by [[plan-queue-assessment]]; this note applies them and restates none.

## Inventory

`python scripts/enumerate_plan_queue.py --root . --json` ran on the integration branch after PRs [#380](https://github.com/bendourthe/Nexus-Hub/pull/380) and [#381](https://github.com/bendourthe/Nexus-Hub/pull/381) merged, with this change set applied. Exit code 0: every plan was readable. The enumerator reports 75 plans repository-wide with no `**Status**:` line; the nine inside v4.13.4 to v4.18.0 are listed under Unknowns.

## What changed today

| Plan or comparison | Session outcome | Placement |
|---|---|---|
| `v4.17.3` harness-economics delta comparison and plan amendment | Merged via PR #381 | Unchanged at v4.17.3 |
| `v4.18.0` code-rendered animation and illustration quality comparison and plan | Merged via PR #380 | Unchanged at v4.18.0; predecessor table updated for the four plans queued after it was written |
| `v4.17.9` pinned rules and prune compaction plan, with the system-one decision-models comparison | Revised plan replaced the earlier `prune-compaction-and-decision-discipline` draft; `tests/plans` passes | Unchanged at v4.17.9 |
| `v4.17.10` structural slop signatures plan and comparison | Plan-review findings applied, including five maintainer decisions | Unchanged at v4.17.10 |
| `v4.17.11` effort allocation plan and comparison | Interrupted plan review re-run and its findings applied | Unchanged at v4.17.11 |
| Copilot Usage Monitor (new) and usage-limit handoff (drafted as `v4.19.0`) | Combined into one plan at the maintainer's request | Moved to `v4.13.7` |

## Membership

Queued by declared status: v4.13.5, v4.13.6, v4.13.7, v4.15.1, v4.16.3, v4.17.2, v4.17.3, v4.17.6, v4.17.7, v4.17.8, v4.17.9, v4.17.10, v4.17.11, v4.18.0. v4.14.0 declares "implementation not started", which is queued. v4.13.4 was in flight on `feat/v4.13.4-training-rebuild` when this assessment began; it was released as tag `v4.13.4` and back-merged into `develop` (PR #385) the same night, so it has left the queue. v4.13.2 declares `queued` with one open task while its other 28 are done; it is carried as in-progress and not re-ranked here.

## Recommended order

Version order is execution order. Only the positions that moved or were created today carry a new reason; every other plan keeps the position its own `## Queued predecessors` table last established.

| Position | Plan | Reason |
|---|---|---|
| 1 | v4.13.4 guide-training-rebuild | Released as `v4.13.4` during this assessment; listed only so the positions below read in context. |
| 2 | v4.13.5 completion-checker-remote-resolution | Unblocks v4.13.6: without it a full `/implement` run in this repository cannot reach `PLAN COMPLETE`. |
| 3 | v4.13.6 minor-scope-implement-and-verified-cleanup | The minor-scope driver. After it lands, `/implement v4.13` builds every remaining queued v4.13 plan in version order. |
| 4 | v4.13.7 copilot-usage-monitor-and-usage-limit-handoff | Maintainer priority, 2026-09-28: "prioritized and part of the next available v4.13.X release". v4.13.7 was the lowest free v4.13.X slot on every branch and tag, and it sorts after the three plans it must follow (v4.13.5 and v4.13.6 edit the same installer files; v4.13.6 is the driver that will build it). |
| 5 to 20 | v4.14.0 through v4.17.8 | Unchanged. Impact judgement for them was recorded by their own authoring sessions. |
| 21 | v4.17.9 adoption-pinned-rules-and-prune-compaction | Unchanged slot. Now a successor of v4.13.7: it registers a hook in the same `catalog/hooks/settings.json` and edits the `context-compression` handoff pattern that `session-handoff` owns the cross-platform half of. |
| 22 | v4.17.10 adoption-structural-slop-signatures | Hard dependency on v4.17.6 (`detect_sentence_headings.py` and the `anti-slop-editing` rule-ownership table must exist first). |
| 23 | v4.17.11 adoption-effort-allocation | Follows v4.17.10 (it references `anti-slop-editing` but does not edit it) and edits only the routing rubric. |
| 24 | v4.18.0 adoption-code-rendered-animation-and-illustration-quality | A minor-version feature; no touched path intersects any plan above it that was added today. |

Impact on the harness is a maintainer judgement, not a computed score. The one judgement made today is that the Copilot Usage Monitor and the automatic handoff outrank the v4.14 to v4.18 work: the usage-limit cutoffs that stopped these six sessions mid-task are the failure the handoff exists to prevent, and a Copilot usage percentage is its input on that platform.

## Parallel-compatible groups

Touched-path intersections from the inventory (a lower bound, per the skill):

- v4.13.7 intersects v4.13.5 and v4.13.6 (`scripts/installer.sh`, `scripts/installer.ps1`, different regions), v4.17.9 (`catalog/hooks/settings.json`), and v4.14.0 and v4.16.2 (both installers and `catalog/hooks/tests/test_installer_smoke.py`). It does not run in parallel with any of them.
- v4.17.9, v4.17.10, v4.17.11, and v4.18.0 share no touched path with each other. They can be built concurrently once their own predecessors land, subject to v4.17.10's hard stop on v4.17.6.

## Unknowns

- No `**Status**:` line: v4.15.0, v4.16.0, v4.16.1, v4.16.2, v4.17.0, v4.17.1, v4.17.4, v4.17.5. They keep their version positions and were not re-ranked. (v4.13.4 also had none, but was released during this assessment.) Confirm each is still queued before `/implement v4.15`, `v4.16`, or `v4.17` resolves members.
- v4.13.2 is marked queued with one open task after 28 completed ones. Whether that task is still owed was not determined.
- The relationships in this note come from touched paths named in task lines, which under-report real surfaces. Each plan re-validates at the start of every phase, per [[implement-phase]].
