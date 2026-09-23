# Decision: A fully closed minor archives its plans and comparisons, reversing the permanent exemption

Status: implemented - closure, not age, now retires a minor's `plans/` and `comparisons/` to `docs/archives/`; `known-gaps.md` never moves, the age rule is unchanged, and the checker stays advisory

## Problem

The retention policy adopted on 2026-08-18 ages out only `development/history/` and exempts `plans/`, `comparisons/`, and `known-gaps.md` permanently. Two records have already defended that exemption. The [2026-08-18 record](2026-08-18-docs-retention-policy.md) rejected sweeping plans and comparisons because "the DEVLOG index links plan files directly, so archiving them would either break those links or force the index to point into the archive for recent releases, which defeats the index". The [2026-09-20 record](2026-09-20-archive-history-one-minor-behind.md), two days before this one, rejected widening to whole version directories because the established meaning of archiving a version was history-only, and because it "would put `known-gaps.md` behind an extra hop from the plans that must read it".

The exemption was written as permanent, so it applied to finished work as well as live work. At v4.13.0 every released minor existed in both trees, 39 active directories against 44 archived, including all 22 released v3 minors. The retrieval problem the policy exists to solve had reappeared inside the subtree it exempted.

Released is not the same as closed, and the distinction matters here. When the closure test was first run, only two minors (v3.18 and v3.5) proved fully closed. Every other released v3 minor still carried open known-gaps items, which is exactly the live work the exemption is right to protect.

## Decision

A minor's `plans/` and `comparisons/` move to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/` once that minor is **fully closed**, meaning both of these hold:

1. Its `known-gaps.md` proves no open work: no `in-progress` or bare `open` status, no unchecked box, and no `NI-`/`DF-`/`BG-`/`WN-`/`MT-`/`QG-` id inside an Open Items region.
2. None of its plans carries an unchecked task line.

This is state 3b of `docs/policy/docs-retention.md`. Everything else about the policy stands:

- **`known-gaps.md` never moves**, even for a closed minor. It is the one file the next `/plan` reads forward, and a closed register answering "nothing carries forward" is cheaper to read in place than through an archive hop.
- **The age rule is unchanged.** Age alone still never retires a plan; `development/history/` still archives one minor behind.
- **The checker stays advisory**, exit 0 always. `scripts/check_docs_retention.py` reports closed minors; the move runs through `[[docs-layout-refactor]]` with reference repair, and `/update release` reports the list without acting on it.
- **The closure test is conservative by construction.** An unparseable or ambiguous register reads as OPEN, and a minor with no register at all is reported as inferred rather than proven. A false "closed" archives live work while a false "open" costs one advisory line, so the two errors are not symmetric and the test leans to the cheap one.

Applied in the same change: v3.18 (`plans/`, three files) and v3.5 (`plans/` and `comparisons/`, which had no register and was confirmed by hand), with inbound references repaired in 24 Markdown files and four DEVLOG entry points repointed.

## Alternatives considered

- **Keep the permanent exemption.** Rejected by the maintainer, who asked that fully implemented plans and version directories be actively archived at release. This is the decisive input and is recorded as such rather than presented as a technical finding. The technical case below explains why the reversal is safe; it is not the reason the reversal happened.
- **Archive whole minors on age, as `development/history/` does.** Rejected, and this is the objection the prior records were right about. Age says nothing about whether a plan's work is finished. A two-year-old minor with one open gap is live work that a later plan still reads, while last month's fully closed minor is not. An age trigger would archive the first and is exactly what the 2026-08-18 record refused.
- **Archive `known-gaps.md` along with the plans.** Rejected for the reason the 2026-09-20 record gives: the register is read forward by the next plan, and moving it adds a hop on every plan for a saving of one small file. Keeping it active is also what makes the closure test cheap to re-run.
- **Infer closure from the release having shipped.** Rejected on evidence. Shipping and closing are different states, and the first run of the closure test showed the gap: 22 released v3 minors, two closed. A release-based trigger would have archived 20 minors' worth of plans that still had open items.
- **Make closed-minor archival a blocking release gate.** Rejected, unchanged from both prior records: archiving is reference-repair work that belongs in a reviewed, confirmed pass, and a blocking gate would stop an unrelated release over documentation that harms nothing by sitting in place one more cycle.

## Consequences

- **Both prior objections are answered rather than overruled.** The 2026-08-18 concern was that DEVLOG links would point into the archive for recent releases. Since the 2026-09-20 threshold change, the DEVLOG already points into the archive for the history of every minor but the current one, so plans following the same path adds no new shape; the entry points are repointed by the same move. The 2026-09-20 concern about an extra hop to `known-gaps.md` is honored in full, because the register never moves.
- **A version's documentation can now split three ways**: register in `docs/releases/`, plans and history in `docs/archives/`. The shape a reader has to learn gets one more case, bounded to minors that are finished.
- **Correctness now depends on the closure test, and its first version was wrong.** It checked only for unchecked boxes and `in-progress`, and cleared fourteen minors, including v4.9, whose register reads `Status: open` with live items. The shipped test reads the gap-id schema that `[[known-gaps-tracker]]` owns and cleared two. That incident is why the test fails toward OPEN, and why `tests/validators/test_check_docs_retention.py` pins both sides: an open minor keeps its plans, a closed one is reported, and a single unchecked task line holds a minor open even when its register says `finalized`.
- **The retention checker is repo-internal**, so a consuming project running `/update release` applies the same closure test by reading the files. `catalog/commands/update.md` states the test in words and names the script as Nexus-Hub tooling for that reason.
- **Point-in-time JSON evidence is not rewritten** when a plan moves. `repository-audit.json` and `v4.9-layout-public.json` record the tree as they captured it, so editing their paths would falsify the record rather than repair a link. Their stale paths are expected, not a defect.
- **Reversal condition.** If readers routinely need a closed minor's plan and the archive hop proves costlier than the smaller active tree is worth, this is the record to reverse, and the move is mechanical in the other direction.

## Related

- [`2026-08-18-docs-retention-policy.md`](2026-08-18-docs-retention-policy.md) - the original policy, whose plans-and-comparisons exemption this record narrows
- [`2026-09-20-archive-history-one-minor-behind.md`](2026-09-20-archive-history-one-minor-behind.md) - the threshold change, whose whole-directory rejection this record answers
- [`docs/policy/docs-retention.md`](../../../policy/docs-retention.md) - state 3b, the policy text this decision adds
- [`docs-layout-refactor`](../../../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and executes the move
