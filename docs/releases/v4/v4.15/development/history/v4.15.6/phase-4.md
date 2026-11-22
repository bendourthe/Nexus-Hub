# Centralized Worktrees Phase 4

**Version**: v4.15.6
**Phase**: 4, Machine Campaign and Agent Handoff
**Base**: review-fix commit `82b02fec7`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.6`

## Subtasks

| Task | Outcome |
|---|---|
| T013 | Complete. The candidate `82b02fec7` passed independent review and the focused suites. The full machine audit was partial, so the user accepted a derived inventory (5 repositories, 117 worktrees). The reviewed manifest `v4156-manifest-3.json` has SHA-256 `b2b4d2537d83...`. |
| T014 | Notices written, validation open. `docs/runbooks/worktree-organization.md` now has copy-ready pre-move and post-move notices built from verified state; none was delivered. The independent-agent check of the notice has not run. |
| T015 | Complete for the approved scope. The user approved and acknowledged 50 moves; apply moved and verified all 50 (exit 3, `partial`, 67 unresolved by design). The read-only smoke passed 50 of 50. Removal candidates: the dry run printed `KEEP` for all three, so none was deleted. |
| T016 | Open. Conservation balances (96 registrations before and after, none lost), but pending items remain: 1 locked, 1 registration-missing, and the live-run and active-run worktrees that move at minor close. |

## Evidence

Full detail, counts per class and receipt locations: `../../v4.15.6-worktree-policy-review.md`, section Phase 4 Machine Campaign.

- Apply: `migrate --apply --manifest v4156-manifest-3.json --expect-sha256 b2b4d253...` printed status `partial`, 50 `moved`, 67 unresolved; every receipt reached `verified`.
- `git worktree list`: 50 entries under `~/.worktrees/nexus-hub-a564dd4d/`, 0 prunable. Every moved worktree has an empty `git status --porcelain --ignore-submodules=all`.
- Smoke: receipt `verified` 50, `scripts/check_version_sync.py` passed in 50 of 50 destinations.
- `nexus_worktrees.py list --json` after apply: 96 registrations (1 main, 95 linked), 50 in policy, 45 outside the folder, 0 prunable.
- Old container `~/.worktrees/nexus-hub/` kept: 39 entries remain.

## Plan delta

Disposition: Minor deltas. Evidence: (1) apply was run without a bound `--smoke`, so the per-move project smoke ran afterwards as a read-only pass over all destinations. (2) The full audit could not finish, so a derived inventory under a recorded user decision replaced it (DF-65). (3) Install-test worktrees are detached, and the cleanup executor keeps every detached worktree (WN-50). Consequence for remaining phases: Phase 5 records the unresolved classes as owned deferrals and runs the independent notice check before release.

## CI impact

None. No pipeline file and no test file changed in this phase.

## Deviations

- The approval receipt's approver field holds the placeholder text from the command template. The approval itself was run by the user and is bound to the digest.

## Next steps

- Phase 5: the independent-agent notice validation (T014), the coordinator deltas, the full local gate, then the single push.
- After release: the cross-repository and second-machine campaign (DF-64).
