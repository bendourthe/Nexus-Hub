# Decision: A fully closed minor archives its plans and comparisons, reversing the permanent exemption

Status: implemented - closure, not age, now retires a minor's `plans/` and `comparisons/` to `docs/archives/`; `known-gaps.md` never moves, the age rule is unchanged, and the checker stays advisory

## Problem

The retention policy adopted on 2026-08-18 ages out only `development/history/` and exempts `plans/`, `comparisons/`, and `known-gaps.md` permanently. Two records have already defended that exemption. The [2026-08-18 record](2026-08-18-docs-retention-policy.md) rejected sweeping plans and comparisons because "the DEVLOG index links plan files directly, so archiving them would either break those links or force the index to point into the archive for recent releases, which defeats the index". The [2026-09-20 record](2026-09-20-archive-history-one-minor-behind.md), two days before this one, rejected widening to whole version directories because the established meaning of archiving a version was history-only, and because it "would put `known-gaps.md` behind an extra hop from the plans that must read it".

The exemption was written as permanent, so it applied to finished work as well as live work. At v4.13.0 every released minor existed in both trees, 39 active directories against 44 archived, including all 22 released v3 minors. The retrieval problem the policy exists to solve had reappeared inside the subtree it exempted.

Released is not the same as closed, and the distinction matters here. The first closure test selected v3.18 and v3.5, but neither was proven closed: v3.18 still records BG-2 as OPEN, and v3.5 has no known-gaps register. Their plans and comparisons remain in the active tree. Other released v3 minors also carry open or unproven work.

## Decision

A minor's `plans/` and `comparisons/` move to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/` once that minor is **fully closed**, meaning both of these hold:

1. Its `known-gaps.md` affirmatively states a finalized or closed Status and `**Open items**: 0`, with no `in-progress` or bare `open` status, contradictory `OPEN` marker, unchecked box, or `NI-`/`DF-`/`BG-`/`WN-`/`MT-`/`QG-` id inside an Open Items region. A missing register is not proof.
2. None of its plans carries an unchecked task line.

This is state 3b of `docs/policy/docs-retention.md`. Everything else about the policy stands:

- **`known-gaps.md` never moves**, even for a closed minor. It is the one file the next `/plan` reads forward, and a closed register answering "nothing carries forward" is cheaper to read in place than through an archive hop.
- **The age rule is unchanged.** Age alone still never retires a plan; `development/history/` still archives one minor behind.
- **The checker stays advisory**, exit 0 always. `scripts/check_docs_retention.py` reports closed minors; the move runs through `[[docs-layout-refactor]]` with reference repair, and `/update release` reports the list without acting on it.
- **The closure test is conservative by construction.** An unparseable or ambiguous register, or no register at all, reads as OPEN. A false "closed" archives live work while a false "open" costs one advisory line, so the two errors are not symmetric and the test leans to the cheap one.

No minor is archived in this change. The initial v3.18 and v3.5 moves were reversed before merge, along with their inbound reference edits, when the false-positive closure evidence was found.

## Alternatives considered

- **Keep the permanent exemption.** Rejected by the maintainer, who asked that fully implemented plans and version directories be actively archived at release. This is the decisive input and is recorded as such rather than presented as a technical finding. The technical case below explains why the reversal is safe; it is not the reason the reversal happened.
- **Archive whole minors on age, as `development/history/` does.** Rejected, and this is the objection the prior records were right about. Age says nothing about whether a plan's work is finished. A two-year-old minor with one open gap is live work that a later plan still reads, while last month's fully closed minor is not. An age trigger would archive the first and is exactly what the 2026-08-18 record refused.
- **Archive `known-gaps.md` along with the plans.** Rejected for the reason the 2026-09-20 record gives: the register is read forward by the next plan, and moving it adds a hop on every plan for a saving of one small file. Keeping it active is also what makes the closure test cheap to re-run.
- **Infer closure from the release having shipped.** Rejected on evidence. Shipping and closing are different states; even the two minors initially selected by the checker were not proven closed. A release-based trigger would archive plans with unresolved work.
- **Make closed-minor archival a blocking release gate.** Rejected, unchanged from both prior records: archiving is reference-repair work that belongs in a reviewed, confirmed pass, and a blocking gate would stop an unrelated release over documentation that harms nothing by sitting in place one more cycle.

## Consequences

- **Both prior objections are answered rather than overruled.** The 2026-08-18 concern was that DEVLOG links would point into the archive for recent releases. Since the 2026-09-20 threshold change, DEVLOG already points into the archive for the history of every minor but the current one; a later qualified plan move must repair its DEVLOG entry points. The 2026-09-20 concern about an extra hop to `known-gaps.md` is honored in full, because the register never moves.
- **A version's documentation can now split three ways**: register in `docs/releases/`, plans and history in `docs/archives/`. The shape a reader has to learn gets one more case, bounded to minors that are finished.
- **Correctness now depends on the closure test, and its first two versions were wrong.** The first checked only unchecked boxes and `in-progress`, clearing fourteen minors including open v4.9. The second read gap IDs only under Open Items headings, missing v3.18's BG-2 OPEN outside that heading, and treated v3.5's absent register as inferred closure. The corrected test requires explicit zero-open-items evidence and rejects contradictory markers. `tests/validators/test_check_docs_retention.py` pins both false positives, the closed case, and an unchecked plan task.
- **The retention checker is repo-internal**, so a consuming project running `/update release` applies the same closure test by reading the files. `catalog/commands/update.md` states the test in words and names the script as Nexus-Hub tooling for that reason.
- **Point-in-time JSON evidence is not rewritten** when a plan moves. `repository-audit.json` and `v4.9-layout-public.json` record the tree as they captured it, so editing their paths would falsify the record rather than repair a link. Their stale paths are expected, not a defect.
- **Reversal condition.** If readers routinely need a closed minor's plan and the archive hop proves costlier than the smaller active tree is worth, this is the record to reverse, and the move is mechanical in the other direction.

## Related

- [`2026-08-18-docs-retention-policy.md`](2026-08-18-docs-retention-policy.md) - the original policy, whose plans-and-comparisons exemption this record narrows
- [`2026-09-20-archive-history-one-minor-behind.md`](2026-09-20-archive-history-one-minor-behind.md) - the threshold change, whose whole-directory rejection this record answers
- [`docs/policy/docs-retention.md`](../../../policy/docs-retention.md) - state 3b, the policy text this decision adds
- [`docs-layout-refactor`](../../../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and executes the move
