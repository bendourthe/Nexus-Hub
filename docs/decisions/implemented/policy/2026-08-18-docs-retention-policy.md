# Decision: Per-version documentation ages out of `development/` on a two-minor rule, advisory not enforced

Status: implemented - `development/` subtrees archive two minors behind current; plans, comparisons, and known-gaps never age out; a report-only checker makes drift visible without blocking a release

## Problem

`docs/v3/` had reached 440 Markdown files across 21 minor-version directories with no rule for when any of them stopped being current. Every release adds a plan, a comparison, a known-gaps file, and one per-phase session history per phase, and nothing had ever moved out.

The cost is retrieval, not storage. An agent looking for how a subsystem came to be needs recent history in reach and old history findable, and an undifferentiated tree of 440 files provides neither: recent work is diluted by two years of superseded notes, and the superseded notes are not organized well enough to be a usable archive either.

`docs/solutions/` already had a refresh lifecycle and `docs/decisions/` has its own. Nothing covered `development/`, which is where the volume actually is.

## Decision

Four states, defined in `docs/policy/docs-retention.md`:

1. **ACTIVE** - the current minor version's directory is unrestricted.
2. **CONSOLIDATE at release** - `development/history/` files stay exactly where they are; what changes is that the release's DEVLOG index line becomes the single entry point. Navigation consolidates, content does not.
3. **ARCHIVE at two minors behind** - a minor version's `development/` subtree moves to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/`, the canonical layout `docs-layout-refactor` already owns. Files move, references are repaired, nothing is deleted.
4. **EXEMPT** - `docs/solutions/`, `docs/decisions/`, `docs/incidents/`, and the living `docs/policy/`, `docs/specs/`, `docs/git/` subtrees.

Within an aging version, only `development/` is swept. `plans/`, `comparisons/`, and `known-gaps.md` stay, because a plan is the durable statement of intent that the DEVLOG index links, and a known-gaps file is read by the *next* plan to decide what carries forward.

`scripts/check_docs_retention.py` reports violations and **exits 0 always**. The archive pass itself runs through `[[docs-layout-refactor]]`, propose-then-apply.

## Alternatives considered

- **No rule; let `docs/v*` grow indefinitely.** Rejected: this was the status quo that produced 440 files, and the failure mode is silent. Nothing breaks, retrieval just degrades a little per release, so there is never a moment that forces the question.
- **Delete old history instead of archiving it.** Rejected: the per-phase histories hold the troubleshooting record, which is the highest-value content in the tree for an agent trying not to repeat a dead end. This project has concrete cases of a hazard being rediscovered years later (the Windows `bash`-resolves-to-WSL-stub PATH shadowing was documented in v3.15.6 and re-diagnosed from scratch in v3.17.6). Deleting that record makes the repeat certain rather than likely.
- **A per-file TTL (archive anything older than N days).** Rejected as arbitrary. Age in days is not the signal; distance from the current version is. A file written during a slow quarter is not staler than one written during a fast one, and a TTL would archive the previous release's history while it is still the most-consulted content in the tree.
- **Consolidate each released version's histories into one summary file.** Rejected: it looks like a saving and is a loss. The value of a per-phase history is the specific failed attempt and the specific error message; a summary keeps the narrative and discards exactly the details that would have saved the next person. Merging is also irreversible in practice.
- **Sweep `plans/` and `comparisons/` along with `development/`.** Rejected: the DEVLOG index links plan files directly, so archiving them would either break those links or force the index to point into the archive for recent releases, which defeats the index. Known-gaps is read forward by the next plan and must stay where that plan looks.
- **Make the checker a hard gate in `make validate` and CI.** Rejected: the failure would be blocking-but-irrelevant. The moment a minor version ages past the threshold, every unrelated release stops until someone runs an archive pass that repairs references across the repo. Nothing is broken by history sitting in place one version longer than the rule prefers, so the gate would impose a real cost to prevent no harm. Archiving is also a reference-repair operation with a confirmation gate; a validator is the wrong place for it.
- **Archive one minor behind instead of two.** Rejected: while the current minor is stabilizing, the previous minor's history is still actively consulted (patch releases routinely revisit the prior release's decisions). One minor would move content out from under the work in progress.

## Consequences

- **The rule is advisory, so it can be ignored indefinitely.** That is the deliberate trade for not blocking releases, and it means the policy's effect depends on someone reading the checker's output during a release. The report is wired into `make validate` as informational for exactly that reason; if it turns out to be ignored in practice, the honest fix is a release-flow step, not a hard gate.
- **The first archive pass is large.** At v3.17, the two-minor rule makes every `development/` subtree from v3.0 through v3.15 archivable at once, which is 16 directories. That backlog is a one-time cost of having had no rule, and it lands in v3.18.0 Phase 5.
- **`docs/archive/v3/` will hold `development/` subtrees for versions whose `plans/` are still in `docs/v3/`.** A version's documentation is therefore split across two trees. That is intentional (the plan is still linked and current, the working notes are not), but it is a shape a reader has to learn, and the policy states it explicitly rather than leaving it to be discovered.
- **The plan that authorized this specified `docs/archive/versions/v<MAJOR>/`**, which is the legacy three-level layout `docs-layout-refactor` explicitly canonicalizes away from and which does not exist in this repo. The canonical `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/` was used instead. Writing the plan's literal path would have introduced a second archive layout while a canonicalization pass exists to remove exactly that.
- **Reference repair is the real work, not the move.** Any archive pass has to fix inbound links from plans, the DEVLOG index, known-gaps files, and the CHANGELOG. The checker deliberately does not attempt it, which keeps the checker trivially safe and leaves the hard part in a reviewed skill.
