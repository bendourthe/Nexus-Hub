# v4.0.0 CI/CD task reconciliation

**Purpose**: Reconcile the 62 unchecked strict tasks in the [cost-effective CI/CD plan](../plans/v4.0.0-cost-effective-ci-cd.md) against surviving phase evidence and current behavior. This is a retrospective audit, not a rewrite of what each 2026-08-25 phase knew.
**Checked**: 2026-09-23.
**Disposition**: All 62 task paths resolve to current artifacts after the documented v3.16-to-v4.0 path migration. The implementation shipped, but the original Phase 8 post-merge gate failed once and must not be relabeled green. The plan's original checkboxes remain unchanged.

## Artifact and phase evidence

Each of the 62 strict `T001` through `T062` lines was parsed separately. All 62 trailing paths exist after mapping `docs/v3/v3.16/` to `docs/releases/v4/v4.0/` and `docs/archive/v3/v3.16/` to `docs/archives/v4/v4.0/`. The stale paths are plan text retained from its v3.19.0 origin; they are not missing deliverables. Artifact existence alone does not prove a task's behavior, so the phase commits and histories below are the second part of the check.

| Tasks | Phase commit | Surviving task and test evidence |
|---|---|---|
| T001-T005 | `256e665f` | [Phase 1 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-1-lifecycle-contract-and-baseline-audit.md): canonical contract, two audits, expected-red contract suite, local gate. |
| T006-T012 | `d8843083` | [Phase 2 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-2-canonical-cicd-skill-architecture.md): canonical skill, two references, dependent skills, registry/routing and test gates. |
| T013-T017 | `734eaf3a` | [Phase 3 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-3-plan-generation-defaults.md): plan generator, dispatcher, lifecycle parser/review tests and stabilization. |
| T018-T023 | `37caeadb` | [Phase 4 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-4-implementation-and-commit-lifecycle.md): implement runbook, dispatcher, commit discipline and transition tests. |
| T024-T033 | `f23baf4c` | [Phase 5 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-5-branch-release-and-cross-platform-policy.md): release/branch policy, templates, project instructions, rendering and parity tests. |
| T034-T042 | `a1fa77e9` | [Phase 6 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-6-repository-native-ci-engine.md): five profiles, reports, classifier, Makefile, guide and engine tests. T042's aggregate `full` run was not complete then; it passed later as recorded in the [known-gaps ledger](../../../../releases/v4/v4.0/known-gaps.md). |
| T043-T053 | `41f1f32e` | [Phase 7 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-7-workflow-migration.md): event-separated workflows, security/contract tests and settings runbook. T049's upload half was partial then; hosted artifact retention was proved later through PRs #235 and #243. |
| T054-T058 | `3494192e` | [Phase 8 history](history/2026-08-25_v4.0.0-cost-effective-ci-cd-phase-8-refactor-known-gaps-and-cicd.md) and [terminal audit](ci-cd-final-audit.md): architecture, gap reconciliation, 23-field comparison, local tests and README. |
| T059-T060 | PR [#124](https://github.com/bendourthe/Nexus-Hub/pull/124) | The final-phase branch was published and merged after its integration checks passed. This does not imply the subsequent post-merge run passed. |
| T061 | [v4.0.0 release](https://github.com/bendourthe/Nexus-Hub/releases/tag/v4.0.0) | The release was published on 2026-08-27. The plan header retargeted the old v3.19.0 body, so v4.0.0 is the applicable tag. |
| T062 | PR [#125](https://github.com/bendourthe/Nexus-Hub/pull/125), later hosted gates | PR #124's first post-merge smoke failed because PyYAML was absent. PR #125 repaired that dependency before the current v4.0.0 tag commit. Later PR #252 proved the protected integration gate and post-merge smoke/provenance on the current pipeline. This is later functional closure, not an original clean Phase 8 result. |

The fresh current-tree contract run passed 313 tests across the lifecycle, plan, implementation, CI-engine and workflow-contract suites. The live required-check coverage guard also passed: 10 declared contexts across `develop` and `main`, produced unconditionally. PR #252 was blocked while its five required contexts were queued, became clean when they succeeded, merged without bypass, and its post-merge smoke and provenance passed in [run 35889175597](https://github.com/bendourthe/Nexus-Hub/actions/runs/35889175597).

## Historical limits retained

- PR #124's original [post-merge run 32912434291](https://github.com/bendourthe/Nexus-Hub/actions/runs/32912434291) failed the fast profile because the new workflow did not install PyYAML. Its provenance job passed. PR #125 fixed the cause, and that repair is an ancestor of the current v4.0.0 tag commit. The red run remains red evidence.
- The historical hosted `v4.0.0` release workflow passed [run 33121989035](https://github.com/bendourthe/Nexus-Hub/actions/runs/33121989035) at head `5bcfa897`; the current annotated tag resolves to `436a5a1f` after repository history changed. The successful run proves the historical tag event, not a new run on the current tag object.
- T042 and T049 were deferred at the original final-phase gate and closed by later bounded evidence in the release ledger. A present-day green test suite cannot retroactively turn those original gates green.

No new implementation task is inferred from the 62 unchecked task lines. They are retained in the plan as historical checklist state; this addendum supplies the later task-path and outcome reconciliation without erasing the original partial and failed evidence.
