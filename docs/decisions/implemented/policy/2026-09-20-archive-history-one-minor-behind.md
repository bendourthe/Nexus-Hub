# Decision: Per-version history archives one minor behind, reversing the two-minor threshold

Status: implemented - `ARCHIVE_AFTER_MINORS` drops from 2 to 1, so every minor below the current one is archivable; scope is unchanged (still `development/history/` only), and the checker stays advisory

## Problem

The retention policy adopted on 2026-08-18 archives a version's `development/history/` subtree once that version is two or more minors behind the current one. That record considered archiving at one minor behind and [rejected it](2026-08-18-docs-retention-policy.md): "while the current minor is stabilizing, the previous minor's history is still actively consulted (patch releases routinely revisit the prior release's decisions). One minor would move content out from under the work in progress."

In practice the two-minor rule leaves one released version's history sitting in the active tree for an entire extra cycle. At v4.13 that was v4.12, plus a backlog the advisory checker had been reporting without blocking anything: v4.7, v4.8, v4.9 and v4.10 were all overdue under the *existing* rule and still in place.

## Decision

`ARCHIVE_AFTER_MINORS` becomes 1. Every minor version below the current one is archivable; only the current minor's history stays in `docs/releases/`.

Nothing else about the policy changes:

- **Scope is unchanged.** Only `development/history/` ages out. `plans/`, `comparisons/`, `known-gaps.md`, CI-executed fixtures, and cited contract documents stay in `docs/releases/`, for the reasons the 2026-08-18 record gives. A `known-gaps.md` in particular is read by the *next* plan, so it never moves.
- **The checker stays advisory**, exit 0 always. The reasoning against a hard gate is untouched.
- **Nothing is deleted**; files move and references are repaired.

Applied in the same change: v4.7 through v4.12, six subtrees, 51 files, with 77 links repaired across 40 files and the five DEVLOG entry points repointed.

## Alternatives considered

- **Keep the two-minor threshold.** Rejected by the maintainer, who asked for v4.2 through v4.12 archived as part of the v4.13 release. This is the decisive input and is recorded as such rather than dressed up as a technical finding.
- **Keep two minors and just clear the backlog.** This would have archived v4.7-v4.10 and left v4.11 and v4.12 in place. Rejected: it treats the symptom. The backlog existed because an advisory checker reports drift that nobody is obliged to act on, and a threshold that leaves a closed release's history in the working tree makes that drift arrive a cycle sooner than anyone notices it.
- **Widen the scope to whole version directories** (plans, comparisons, known-gaps too). Rejected, and worth stating because "archive v4.2 to v4.12" reads that way at first. The three prior archived versions (v4.0, v4.2, v4.4) each contain `development/history/` and nothing else, so the established meaning of "archive a version" in this repository is already history-only. Moving plans would also contradict the exemption the 2026-08-18 record argues for directly, and would put `known-gaps.md` behind an extra hop from the plans that must read it.
- **Make the checker a hard gate now that the threshold is tighter.** Rejected, unchanged from the original record: a blocking failure would stop an unrelated release the moment a version aged out, and archiving is a reference-repair operation that belongs in a reviewed pass.

## Consequences

- The active tree now holds exactly one version's session history. That is the point, and it is also the new failure mode: the moment v4.13 publishes, v4.13's own history becomes archivable on the next release, so the archive pass is now a per-release chore rather than an occasional one. The advisory checker names the destination, which keeps the chore mechanical.
- **The original rejection is now reversed, and the case behind it is real.** A patch release that revisits the prior release's decisions will find that history under `docs/archives/` rather than `docs/releases/`. It is still reachable, still linked from the DEVLOG line that the move repoints, and one directory different. If that hop turns out to cost more than the tidier active tree is worth, this is the record to reverse.
- A version's documentation remains split across two trees: plan in `docs/releases/`, history in `docs/archives/`. The 2026-08-18 record already flagged this as a shape a reader has to learn. Tightening the threshold makes it the normal case rather than the aged case.
- The link repair has a specific shape worth reusing: a relative link inside a moved history file breaks only when it lands inside the version directory, because the source and destination sit at equal depth. Links to the repo root or to other `docs/` subtrees survive untouched. The repair rewrites the broken class to `../../../../../releases/v4/v4.N/...`, matching what the already-archived v4.2 and v4.4 histories use.

## Related

- [`2026-08-18-docs-retention-policy.md`](2026-08-18-docs-retention-policy.md) - the record this one amends; its scope, exemptions, and advisory-checker reasoning all still stand
- [`docs/policy/docs-retention.md`](../../../policy/docs-retention.md) - the policy text updated by this decision
- [`docs-layout-refactor`](../../../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and executes the move
