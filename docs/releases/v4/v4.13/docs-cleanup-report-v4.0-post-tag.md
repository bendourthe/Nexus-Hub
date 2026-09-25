# Docs Cleanup Report - Nexus-Hub - 2026-09-24

**Active version:** v4.13.0
**Mode:** original propose-only audit with a bounded application recorded below
**Scope:** the four v4.0 paths reported by `audit-docs.py lifespan-contradictions` on `origin/develop` at `434da421`, then rechecked after `d052af9e`; this is not a whole-tree cleanup audit
**Owner:** [v4.0 WN-2](../v4.0/known-gaps.md)

## Summary

| Category | Count |
|---|---:|
| Cat 1 (delete) | 0 |
| Cat 2 (archive now) | 0 |
| Cat 3 (living, placement review) | 2 |
| Cat 4 (active closure hold) | 2 |
| **Total** | **4** |

The post-tag scan still exits 1 and names exactly these four v4.0 files. Its repository-wide findings are outside this scoped report. The earlier migration-era count of 243 and the later whole-tree count of 1,419 are not a current v4.0 baseline. The minor-root `known-gaps.md` is intentionally active and is excluded by the [scoped detector correction](../v4.0/known-gaps.md); no date amnesty was applied.

After rebasing this proposal onto `d052af9e`, the detector still returned exactly the four v4.0 paths in the table, with 1,388 findings across all release buckets. The broader count is context only; this proposal classifies the v4.0 subset.

## Dispositions

| Current path under `docs/releases/v4/v4.0/` | Category | Evidence and lifespan | Proposed destination or hold |
|---|---|---|---|
| `development/ci-cd-profile-guide.md` | Cat 3 | Introduced in v4.0.0 but edited in three CI-profile commits on 2026-09-22; [README](../../../../README.md) links to it as the current usage guide. It must describe the live runner, not a frozen v4.0 state. | Propose `docs/guides/repository-native-ci-profiles.md`, with a content refresh and inbound-link repair, at the confirmation gate. |
| `development/github-ci-settings-runbook.md` | Cat 3 | Introduced in v4.0.0, updated on 2026-08-30, and linked by the v4.0 lifecycle contract and final audit. It tells an operator how to verify current GitHub settings. | Propose `docs/runbooks/github-ci-settings.md`, with a settings read-back and inbound-link repair, at the confirmation gate. |
| `plans/v4.0.0-agent-communication-overhaul.md` | Cat 4 | The 2026-09-06 post-tag edit changed two exit-checklist boxes against later evidence, not the plan's intended behavior. The file remains a release plan while v4.0 has open gaps. | Keep in the active v4.0 plan tree. Archive only after the whole-minor closure conditions in the [retention policy](../../../policy/docs-retention.md) hold. |
| `plans/v4.0.0-cost-effective-ci-cd.md` | Cat 4 | Later edits record the task reconciliation and historical status without restating the failed original post-merge run as a pass. The 62 original strict task boxes remain unchecked even though the [reconciliation](../../../archives/v4/v4.0/development/ci-cd-task-reconciliation.md) traces each path. | Keep active. The current retention rule requires zero unchecked strict task lines; any audited exception needs an explicit policy decision before archiving. |

The two Cat 3 documents are not deletion candidates. The retention policy explicitly permits referenced live content under a release's `development/` directory while treating a relocation to living roots as a separate refactor. Their post-tag edits are therefore classified, not silently excused or auto-moved. The plans are held by the minor's still-open state; the CI plan has an additional mechanical checkbox hold.

## Cat 3 refresh queue

| Path | Why refresh is required before a move | Proposed action |
|---|---|---|
| `docs/releases/v4/v4.0/development/ci-cd-profile-guide.md` | It claims to document current profile commands and costs. | Compare its command and profile table with `scripts/ci/`, then repair the README and other inbound references. |
| `docs/releases/v4/v4.0/development/github-ci-settings-runbook.md` | It instructs current account-backed repository settings checks. | Re-read the protected-branch and required-check settings before relocating the runbook. |

## Lifespan contradictions

The `v4.0.0` tag closed on 2026-08-27. The dates below are the latest post-tag commits for the four paths, not a claim that every commit since the tag was reviewed.

| File | Release close | Latest post-tag commit | Interpretation |
|---|---|---|---|
| `development/ci-cd-profile-guide.md` | 2026-08-27 | `967aca2b`, 2026-09-22 | Living guide under a release path. |
| `development/github-ci-settings-runbook.md` | 2026-08-27 | `342db59e`, 2026-08-30 | Living runbook under a release path. |
| `plans/v4.0.0-agent-communication-overhaul.md` | 2026-08-27 | `311e9bed`, 2026-09-06 | Later evidence corrected two checklist boxes. |
| `plans/v4.0.0-cost-effective-ci-cd.md` | 2026-08-27 | `8c7ce91e`, 2026-09-23 | Later reconciliation appended status evidence; the original boxes remain. |

## Target tree preview

```text
docs/
  guides/repository-native-ci-profiles.md       proposed at audit time; moved 2026-09-25
  runbooks/github-ci-settings.md                 proposed at audit time; moved 2026-09-25
  releases/v4/v4.0/plans/                        held until whole-minor closure
  releases/v4/v4.0/known-gaps.md                 stays active by policy
```

No existing archive path changes in this proposal. The two possible living-document moves need the docs-layout confirmation gate and a before/after link-set diff. The CI plan needs a separate decision on its 62 historically preserved task boxes. WN-2 stays open until those decisions and the resulting detector baseline are verified.

## Bounded application - 2026-09-25

The two Cat 3 documents were copied byte-for-byte to `docs/guides/repository-native-ci-profiles.md` and `docs/runbooks/github-ci-settings.md` before their old paths were removed. Their source hashes were `1AC5FC809E4BA07A824648552616A777EC1D1F7E4D35641941D7FCD6C5882711` and `E9E8FA4D6EA6458DFAFD598E7E5B3B00574464E1AB91D6C73124F98D4591408D`, respectively. The moved guide now describes the observed Windows full-run duration and generated coverage/SARIF receipts; the runbook reflects the 2026-09-25 repository read-back without claiming access to account billing or a rendered merge-queue setting.

The staged rename-map link comparison reported zero newly broken links, with 465 pre-existing unresolved references before and after. The direct inbound Markdown links in README, the v4.0 lifecycle contract, and the v4.0 final audit were repaired; the `post-merge.yml` path comment was updated. This is a relocation proof, not a clean whole-repository link baseline.

Two frozen records now have post-tag link-maintenance edits: `development/ci-cd-lifecycle-contract.md` and `development/ci-cd-final-audit.md`. On the committed relocation tree, the lifespan detector exited 1 with 1,388 findings across release buckets and exactly four in v4.0: those records and the two plans in the original table. The CI plan's 62 unchecked historical task boxes remain untouched. WN-2 cannot close from the two-file relocation alone; re-run the detector after protected publication and decide the records' living or archival disposition.

## Self-classification

This proposal is Cat 4 while v4.13 closeout is active. It is a decision input, not evidence that the proposed moves occurred.
