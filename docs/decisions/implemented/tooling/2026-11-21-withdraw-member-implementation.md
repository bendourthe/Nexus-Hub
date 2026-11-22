# Decision: A captured decision can withdraw one member's implementation claims

Status: implemented - `record withdraw-implementation` releases the recorded implementation admission of one unstarted member, and the record writer accepts that removal only for the consumed action.
Date: 2026-11-21
Author: Ben Dourthe
Template: Nygard

## Problem

A minor run admits each member for implementation with recorded read and write claims, and refuses to admit another member whose writes overlap an admitted, unmerged member's reads or writes. Publication runs in version order. A later member that reads a file an earlier member must write therefore deadlocks the run: the earlier member cannot be admitted, and the later member cannot publish first. For v4.15 this stopped v4.15.6 behind the admitted v4.15.11 and v4.15.12.

No supported action released a later member's admission. The record writer refuses any unsanctioned change to signed member state, so the only ways out were a hand edit of the record, which the signature rejects, or abandoning the run.

## Decision

- A new action, `withdraw-implementation`, follows the `correct-read` shape: `record render --action withdraw-implementation --member` opens an approval round and `record withdraw-implementation` consumes it. The page binds the repository, controller, owner session, record hash, member, frozen plan hash, the exact current `implementation` object, both branches and the member branch head at render time.
- The consumed decision appends `{implementation, page, accepted}` to the member's `implementation_withdrawals` list and removes `implementation`. The removed object is kept exactly, so the history shows what was released.
- The page is rebuilt and compared before the single-use approval is consumed, and again before the write, so a slow check cannot spend an approval without a result.
- The central writer accepts the removal only for the consumed action under the lease, only when the entry's `implementation` equals the removed one and nothing else in the record changed. It refuses any other removal of `implementation` and any edit, reorder or removal of the history.
- Branches, worktrees and commits are never touched. Admitting the member again is the ordinary `record member-implement-start`, which already requires a clean worker at a commit merged into the target branch, so commits that exist only on the member branch are preserved and reapplied by the operator.
- The action refuses a member that was never admitted, holds a publication start, is archived or merged, or carries a `permit-member-paths`, `correct-read`, `correct-ci-read`, manifest, output or historical-scope entry, coordinator paths or an execution permission. Original and amended members are both supported.
- The signing domain does not change. The list is member data inside the signed member lists, so records without it sign exactly as before.

## Alternatives considered

- **Edit the record by hand.** Rejected: the record is signed and the writer refuses unsanctioned member changes. A bypass would remove the guarantee the signature gives.
- **Reorder publication so the later member publishes first.** Rejected: publication order is the version order the run approved, and the earlier member's writes would then land on top of the later member's reads.
- **Delete the member's branch and worktree as part of the withdrawal.** Rejected: it destroys commits the operator may need, and the admission rules already handle the clean-start requirement on re-admission.
- **Release only the conflicting paths, like `correct-read`.** Rejected: `correct-read` covers one read file until the publication start. A write claim or a dependency cannot be released that way, and a partial release leaves a claim set the operator never reviewed.
- **Support members that already carry permission entries.** Rejected for now: each entry type has its own writer guard, and untangling them needs a design of its own. The named refusal keeps the scope narrow.

## Consequences

- A deadlocked minor run can continue through one reviewed, captured decision instead of a rebuild of the run.
- The operator carries the work of preserving unique commits on the withdrawn member's branch before it is admitted again; the page says so.
- A member with a permission entry cannot be withdrawn until a later decision covers that case.
- The record gains one more append-only member history that every native writer must keep.
