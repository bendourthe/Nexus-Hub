# v4.13 Scoped Documentation Archive Report

**Active version:** v4.13.0
**Mode:** applied under the user's 2026-09-22 archive request
**Scope:** the late v4.10.1 final-qualification history file

## Summary

| Category | Count |
|---|---:|
| Cat 1 (delete) | 0 |
| Cat 2 (archive) | 1 |
| Cat 3 (stale flag) | 0 |
| Cat 4 (active report) | 1 |

## Dispositions

| Source path | Category | Destination | Evidence |
|---|---|---|---|
| `docs/releases/v4/v4.10/development/history/2026-09-22-phase-7-final-qualification.md` | Cat 2 | `docs/archives/v4/v4.10/development/history/2026-09-22-phase-7-final-qualification.md` | The source and copy had SHA-256 `84609F1B02D2E06061A0E173F067EDA304EE2AB65C53B7FC8DDD2B69586F39BA`; the post-move link baseline found zero newly broken links. |

## Lifespan contradictions

None was auto-moved. This record was added during the v4.10.1 final integration after the earlier v4.10 archive pass, then archived under the user's explicit request after that implementation closed.

## Target tree

The v4.10 `plans/`, `comparisons/`, `known-gaps.md`, and non-history `development/` content remain under `docs/releases/v4/v4.10/`. The single late history file joins the existing six files in `docs/archives/v4/v4.10/development/history/`.

## Self-classification

This report is Cat 4 while v4.13 is current. It can be assessed for archival in a later release.

## 2026-09-25 historical carry-forward archive pass

The earlier summary and target-tree statement above describe the 2026-09-22 one-file pass. This later pass applies the user's verified-transfer exception in `docs/policy/docs-retention.md`: v4.13 links all twelve existing v4.0-v4.12 source ledgers, while every source-open gap remains open. v4.6 has no cut release directory. The v4.13.1-v4.13.4 plans are outside this pass.

| Source directory | Disposition | Archived files |
|---|---|---:|
| `docs/releases/v4/v4.0/plans/` | Cat 2 - transfer-qualified | 3 |
| `docs/releases/v4/v4.1/plans/` and `comparisons/` | Cat 2 - transfer-qualified | 8 |
| `docs/releases/v4/v4.3/plans/` | Cat 2 - transfer-qualified | 1 |
| `docs/releases/v4/v4.4/plans/` | Cat 2 - transfer-qualified | 7 |
| `docs/releases/v4/v4.9/plans/` and `comparisons/` | Cat 2 - transfer-qualified | 3 |
| `docs/releases/v4/v4.10/plans/` and `comparisons/` | Cat 2 - transfer-qualified | 3 |
| `docs/releases/v4/v4.11/plans/` and `comparisons/` | Cat 2 - transfer-qualified | 4 |

Each of the 29 files was copied, checked for equal byte length and SHA-256, and only then removed from its source path. Every archive destination was checked against `.gitignore` before moving. The [archive index](../../../archives/README.md) lists every old and new file path. The two plans with retained strict task boxes remain unchanged in task disposition: the v4.0 CI plan is supported by its task reconciliation, and the v4.4.6 guide plan is explicitly superseded by the user. Their post-reference-repair hashes are bound in [v4.13 known gaps](known-gaps.md).

The tracked-Markdown link baseline was 503 unresolved before and after the move; the rename-aware comparison projected 465 distinct unresolved targets on each side and found zero newly broken links. The 503 are pre-existing findings, not a pass claim for the whole documentation tree. The retention checker reports no further archive-qualified active `plans/` or `comparisons/` directories in this bounded v4.0-v4.12 set. No older known-gaps ledger was archived or marked resolved, and empty source directories were left alone rather than pruned.

The post-move transfer predicate passed for all twelve existing source ledgers. Its checklist inventory covers 22 archived plans, including eight archived before this pass, with 384 retained checkbox lines; 65 are strict `T###` lines in the two separately evidenced plans. These are review signals, not new completion claims.

## 2026-09-25 v4.0 lifespan WN-2 follow-up

A fresh `audit-docs.py lifespan-contradictions` scan after the 29-file pass found one more active v4.0 file, `development/last-phase-evidence.md`. It is a dated v4.0.0 final-phase record, not a living document or CI input, so this pass archived it at `docs/archives/v4/v4.0/development/last-phase-evidence.md`. The 15,534-byte source and copied destination had matching SHA-256 `895f20f701031893790d65da2807edbee7c7500bbc0f713728368ba0e9e9ca1b` before the destination's relative plan link was repaired. The inbound session-history link and archive index were updated; no active-version document was moved.

The rename-aware link baseline reported 465 unresolved targets before and after, with zero newly broken. The candidate-tree lifespan scan reported zero files under `docs/releases/v4/v4.0/`; findings in other release buckets remain outside this v4.0 disposition. The CI plan's 62 retained strict boxes are bound to its [task reconciliation](../../../archives/v4/v4.0/development/ci-cd-task-reconciliation.md), and the [v4.0 ledger](../v4.0/known-gaps.md) records WN-2's source-level resolution without editing the historical plan.
