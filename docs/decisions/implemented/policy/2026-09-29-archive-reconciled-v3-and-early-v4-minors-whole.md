# Decision: Archive the reconciled v3 minors and the v4.0-v4.11 active residue whole, including their gap ledgers

Status: implemented - on 2026-09-29, every v3 minor directory and the remaining active content of v4.0, v4.1, v4.3, v4.4, v4.5, v4.9, v4.10, and v4.11 moved from `docs/releases/` to `docs/archives/`, after each open gap was resolved with evidence, closed with a cited reason, or migrated to the v4.13 ledger; the general rules of `docs/policy/docs-retention.md` are unchanged for every other minor

## Problem

At v4.13 the active tree still held all 22 v3 minors and residual `development/`, `analysis/`, and cleanup-report content for eight v4 minors. Every one of those versions had shipped, most of them months earlier. Their ledgers were never finalized after release: most v3 Status lines still read "release-ready, pending `/update release`", many item headings still read `OPEN` although a later section of the same file had closed them, and none of the v3 ledgers carried the explicit `**Open items**: 0` line the closure test requires. The closure test in `scripts/check_docs_retention.py` therefore held every v3 minor open, correctly, and nothing could leave the active tree.

The maintainer asked, on 2026-09-29, for the v3 releases and the v4.0-v4.11 releases to be archived once each is either fully addressed or its remaining gaps are minimal and documented in the next live version's ledger.

## Decision

1. **Reconcile first.** Every item in each in-scope ledger that its own file did not record as resolved, closed, accepted, or declined was audited against the current tree. Each received exactly one disposition: resolved with cited evidence (a file, commit, test, or later ledger entry), closed with a cited reason (feature removed, decision record, superseded by a later ledger), or migrated. Nothing was marked resolved without evidence. The source ledger records every disposition in a closing `Archive reconciliation - 2026-09-29` section and marks each affected item line.
2. **Migrate the remainder once.** Genuinely open items moved to one new section of `docs/releases/v4/v4.13/known-gaps.md`, merged where two ledgers recorded the same obligation, each with a provenance line naming its source minor and item.
3. **Then move whole directories.** With every source ledger truthfully stating `**Open items**: 0`, the directories moved to the matching `docs/archives/` minor, merging into the existing archive folders without any filename collision, and every inbound reference was repaired.

This is a second bounded exception to "`known-gaps.md` stays in the active tree", alongside the 2026-09-28 v4.0-v4.12 historical transfer. It applies only to the minors named above and does not change the default for any later minor.

## Alternatives considered

- **Keep the ledgers active and archive only plans, comparisons, and history.** Rejected: the maintainer's instruction names the releases as the unit to archive, and a v3 ledger answering "nothing carries forward" is still an active-tree file that the next plan must open. After reconciliation the v4.13 section is the single forward entry point, which is the purpose the active-ledger rule served.
- **Transfer tracking without reconciliation, as the 2026-09-28 v4 transfer did.** Rejected for v3: that transfer bound source ledgers by hash while leaving source-open items open. The v3 ledgers had accumulated stale markers across more than twenty minors, so a hash-bound pointer would have carried the staleness forward unexamined. Item-level reconciliation costs more once and leaves a smaller, verified forward list.
- **Leave CI-executed fixtures and hook-cited contracts in `docs/releases/`.** Rejected: the retention policy kept them in place because a blanket move would break their callers silently. This move repairs every caller in the same change (the `presentify-extractor.yml` steps and path filter, hook and test comments, and `.gitattributes` / `.gitignore` patterns), so the risk the policy guarded against is handled rather than deferred.
- **Rewrite point-in-time JSON and HTML evidence to the new paths.** Rejected, following the 2026-09-22 record: captured evidence records the tree as it was, and editing it would falsify the record. Only Markdown links and repository-level path mentions were repaired.

## Consequences

- `docs/releases/v3/` no longer exists; the v4 active tree holds v4.13 and later only.
- The v4.13 ledger gains one migrated section. Items there remain open until their own evidence closes them; migration transfers tracking, not completion.
- A reader looking for a v3 or early-v4 ledger follows the v4.13 provenance lines or the `docs/archives/README.md` index.
- **Reversal condition.** If the migrated section proves too coarse and readers routinely need the source ledgers, the move is mechanical in the other direction, and every source item line still names its disposition.

## Related

- [`docs/policy/docs-retention.md`](../../../policy/docs-retention.md) - the policy whose `known-gaps.md` default this record makes a second bounded exception to
- [`2026-09-22-archive-plans-of-closed-minors.md`](2026-09-22-archive-plans-of-closed-minors.md) - the closure-based plan archival this record extends to whole minors
- [`docs/releases/v4/v4.13/known-gaps.md`](../../../releases/v4/v4.13/known-gaps.md) - the migrated-items section
- [`docs-layout-refactor`](../../../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and the reference-repair procedure used here
