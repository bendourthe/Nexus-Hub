# Decision: Move the roadmap ordering document to a living root

Status: implemented - Relocate `roadmap-prioritization.md` out of the release tree, superseding the "Not moved" line in the 2026-08-21 plan-filename decision

## Problem

`docs/v3/roadmap-prioritization.md` is the single authority on the order of unshipped work. It currently ranks seventeen plans targeting v3.21.0, v4.0.0, v4.1.0, and v4.2.0, and it is amended whenever priority changes - six recorded amendments between 2026-08-07 and 2026-08-24.

It lived inside the v3 major bucket, directly beside the `v3.<minor>/` release directories rather than inside one. `docs/decisions/implemented/process/2026-08-21-plan-filenames-track-target-version.md` considered relocating it and declined: "Not moved: `docs/v3/roadmap-prioritization.md` stays put even though it now ranks v4 plans. Relocating it would pull CHANGELOG, README, and DEVLOG references along for a cosmetic gain."

The v4.0.0 lifespan migration invalidates the premise of that reasoning in two ways. The gain is no longer cosmetic, because `docs/v3/` ceases to exist as a container: leaving the file behind strands a legacy directory that the `old-version-docs-guard` now flags. And the cost is no longer marginal, because the migration is rewriting references across the repository in the same pass, so the roadmap file's references are repaired by the same mechanism that repairs the other 762 files rather than by a separate errand.

The lifespan admission test the same release adopts asks: "will this document still change after this release closes?" For the roadmap document the answer is unambiguously yes.

## Decision

The file lives at `docs/roadmap-prioritization.md`, a living root, and its inbound references were repaired through the migration's rename map.

This keeps the two properties the 2026-08-21 decision actually depended on. The document remains the single ordering authority reachable from `docs/todos.md`, `README.md`, `CHANGELOG.md`, and every plan's `Rank` field. And it remains excluded from automated version-string sweeps, which matters more after the move than before: the file names version numbers as *data about other documents*, and a sweep treating them as its own version corrupts the ranking. That hazard is unchanged.

## Alternatives considered

### Move it to `docs/releases/v3/roadmap-prioritization.md`

Rejected. It preserves the file's position relative to the v3 bucket and requires the least thought, but it files a document that is still being amended into a tree whose entire purpose is release-bound material. That is a lifespan contradiction of exactly the kind the same release adds a detector for, so the repository would ship a signal and immediately violate it. It also misleads: a reader finding v4.2.0 rankings inside the v3 release tree has to reconstruct why.

### Leave it at `docs/v3/roadmap-prioritization.md`

Rejected. It honors the 2026-08-21 record literally and touches no references, but it strands a `docs/v3/` directory containing exactly one file after every sibling has moved. The migration would be visibly incomplete, the legacy-layout detection branch would keep firing on this repository forever, and the next person would have to make this same decision with less context.

### Split it - keep shipped-release history in the release tree, move only the forward ranking

Rejected. The document's value is that order is readable from one place; the 2026-08-20 revision exists precisely because ordering had been scattered across filenames. Splitting it re-creates the problem it was written to solve, and neither half is independently useful.

## Verified by

- `docs/roadmap-prioritization.md` exists and `docs/v3/` no longer exists.
- Git records the relocation as a rename, not as a delete plus an unrelated add.
- The move-aware link diff reports zero newly broken links across the repository, and `docs/todos.md`, `README.md`, and `AGENTS.md` each resolve every relative link.
- The document still opens with its amendment history and ranking table, unmodified in content by the move.

## Risks

- **A stale reference is missed and reads as a broken link.** Mitigated by the rename-map repair plus the move-aware set diff, which is a set comparison rather than a count and therefore cannot report "no change" while one side breaks.
- **A future automated version-string sweep treats the file's ranking data as its own version.** Unchanged by this decision and still live. The move does not add protection, so the hazard must stay recorded wherever sweeps are implemented.
- **The superseded 2026-08-21 record is read later without this one.** Mitigated by naming that record explicitly here and confining the supersession to its single placement line.

## Consequences

- The 2026-08-21 record's "Not moved" line is superseded. That record stays accurate about *why* plan filenames track target versions; only its placement conclusion for this one file changes.
- Inbound references in `CHANGELOG.md`, `docs/todos.md`, three decision records, and several plan files are rewritten by the migration's rename-map pass and verified by the move-aware link diff rather than by hand.
- The no-automated-version-sweep hazard on this file is unchanged and still needs to be respected by any future tooling.
