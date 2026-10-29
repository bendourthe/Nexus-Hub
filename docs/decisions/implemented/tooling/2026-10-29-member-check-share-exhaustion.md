# Decision: Member Check Share Exhaustion Is Retryable

Status: implemented - a member's spent 20-second share is reported as `previous-member-unverified` (retryable, still refused) instead of `previous-member-incomplete`, and the share and caps are unchanged.

Completion-checker maintainers and anyone reading a `record member-start` refusal read this before changing the member budget or the member-gate reasons. It records why exhaustion is separated from incompleteness and why the share was not simply enlarged.

**Date**: 2026-10-29. **Release**: maintenance, follows v4.14.3. Resolves known gap WN-28 (v4.14).

## Problem

`check-minor`, `check-member` and `record member-start` evaluate each member inside its own 20-second share (`MEMBER_BUDGET_SECONDS`). The release and integration predicates (`release.main`, `approval.remote`, `integration.*`) make several sequential `gh` and `git ls-remote` calls. With ordinary latency the share could run out part-way, every later lookup read `cannot-verify` ("member budget exhausted"), and `record member-start` treated any non-met line as an incomplete predecessor. The v4.14.3 publication gate refused three times with `previous-member-incomplete (v4.14.2)` and then passed on a retry with no change in state. The reason string said the predecessor was incomplete when the only fact established was that the lookups had not finished.

## Decision

- **Mark exhaustion.** `MemberResult` gains `share_exhausted`, set when a member's own share reaches zero during its evaluation. It is distinct from the existing `exhausted`, which means the member was never evaluated, so `check-minor`'s ids and progress score are unchanged.
- **Separate the refusal reason.** In `record member-start`, when the predecessor's share (or the whole budget) ran out, no predicate is `unmet`, and the predecessor's member gate is neither `unmet` nor `violated`, the gate is refused with `previous-member-unverified (vX.Y.Z)` and a stderr notice to repeat the command. Every other refusal keeps `previous-member-incomplete`.
- **Stay fail-closed.** The refusal is the same `BLOCKED: member-gate (vX.Y.Z)` line and exit 3 in both cases. A lookup past the share still reads `cannot-verify`, never met. Because a spent budget can only produce `cannot-verify`, a verified `unmet` or `violated` is never relabeled, and the local predicates (unchecked tasks, evidence files) are read before any hosting call, so a really incomplete predecessor still reads `previous-member-incomplete` under any latency.
- **Say so where the user reads it.** The member notice that already existed now states that lookups past the share read `cannot-verify` and the check can be repeated unchanged.

The 20-second share, the 360-second `check-minor` cap and the 60-second cap of single-command invocations are unchanged.

## Alternatives considered

Rejected alternative: raise `MEMBER_BUDGET_SECONDS`. The share is pinned to the per-plan budget and to the seven-member sizing of the 360-second cap (`test_seven_member_budget_includes_shared_observations`); raising it enough to cover a slow day trades gate latency for every run and still fails on a slower day. No observed latency distribution exists to size it against.

Rejected alternative: treat `cannot-verify` from an exhausted share as passing, or as `deferred`. That would open the publication gate on an unverified release, which is the fail-open direction the contract forbids.

Rejected alternative: retry the previous member inside `record member-start`. The command's total budget is 60 seconds, so a second 20-second share competes with the later tag and worktree checks, and a silent retry hides the exhaustion the user should see. Repeating the command achieves the same retry explicitly.

Deferred, not rejected: sizing the share from measured per-call latency. It needs latency measurements the checker does not record today.

## Consequences

A refusal now tells the user whether the predecessor is wrong (`previous-member-incomplete`) or merely unverified (`previous-member-unverified`, repeat the command). Anything that parses the reason string must accept the new fixed value. Regression tests in `tests/validators/test_completion_minor_verdict.py` simulate slow `gh` and `git ls-remote` calls and cover the retryable refusal, the retry that passes, the never-met rule, and a really incomplete predecessor under the same latency.
