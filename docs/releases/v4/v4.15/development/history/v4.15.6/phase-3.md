# Centralized Worktrees Phase 3

**Version**: v4.15.6
**Phase**: 3, Migration and Recovery
**Base**: Phase 2 commit `191590be8`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.6`

## Subtasks

| Task | Outcome |
|---|---|
| T009 | `migrate --dry-run --inventory <report> --manifest <new-file>` writes a versioned manifest (`nexus-worktree-migration/1`) with one item per linked worktree: identity, original and destination paths, expected Git state and content fingerprint, disposition, reason, owner, acknowledgment token hash, authorization slot, path-bound files, optional smoke command. Dry runs write the manifest, a notice file and nothing else. |
| T010 | `migrate --apply` executes only an unchanged, digest-matching, approved and acknowledged manifest: per-repository lock, full revalidation, preservation package, final ancestor check, `git worktree move` under the non-executing profile, exact postcondition comparison, durable step receipts, and recovery of an interrupted item. |
| T011 | `docs/runbooks/worktree-organization.md` defines the checkpoint, acknowledgment and reopen contract, the path-bound state inventory, and the signed-run rule. `--approve` and `--ack` write local receipts bound to the digest. |
| T012 | `tests/validators/test_worktree_migration.py` (23 tests) runs the real executor on fixtures, this history, one local commit. |

## Evidence

`python -m pytest tests/validators/test_worktree_migration.py -q` gave 23 passed. Together with the Phase 1 and Phase 2 Python suites and the installed-postcondition suite: 159 passed (43 + 54 + 23 + 39). `catalog/hooks/tests/test_worktree_policy.py` (24) was rerun with the final helper.

A real move, with every kind of content. A worktree carries an unstaged edit, a staged new file with non-ASCII bytes, an untracked file, an ignored file, and a nested binary file. After the apply: the old folder is gone, the destination sits at `<root>/<identity>/<name>`, a hash of every file outside `.git` is identical, `git status --porcelain=v1 -z`, `git diff --cached --binary` and `git diff --binary` are byte-identical, HEAD and branch are unchanged, the repository registers the new path and not the old one, the pointer file starts with `gitdir:`, and a follow-up `git commit` works. The preservation package holds the index, the tracked patch, and a copy of the untracked file. The receipt steps are `started`, `preserved`, `moving`, `verified`, and the `moving` step records the resolved source and destination. A second apply reports the item as already verified.

Interruption boundaries, each simulated with an interrupt raised at that point and then resumed:

- After validation and packaging (receipt `preserved`): nothing moved; the rerun moves it.
- Before Git runs (receipt `moving`, source present): nothing moved; the rerun revalidates from the start and moves it.
- After Git moved the folder but before verification (receipt `moving`, destination present): the rerun verifies the destination against the manifest and reports `recovered`.

In every case the repository lock is released, content is identical afterward, and the receipt ends `verified`. Recovery refuses rather than guesses: a destination edited after an interrupted move gives `recovery-unverified`, and a source and destination both present gives `recovery-ambiguous`, both leaving the receipt `recovery-refused`.

Refusals, each leaving the source untouched and nothing created at the destination: a changed digest (a one-byte edit), a malformed manifest, a wrong schema, a changed worktree root (`manifest-stale`), a missing approval, a missing or wrong acknowledgment token, a blank checkpoint note, and drift in the source (edit, new commit, staged file, new untracked file, lock, or a destination that appeared). A competing writer between validation and the move stops the item (`competing-writer`). The deterministic ancestor fixture replaces `<root>/<identity>` with a junction after validation; the final check refuses it (`destination-reparse`) and nothing is created at the junction target. A repository lock held by another operation refuses with `repository-locked`.

Proposal classification, checked on one fixture set: a normal item is `move`; a locked worktree is `pending` and never unlocked; a worktree named by a live signed run record is `pending` for the run owner, becomes `move` once the record is stamped complete, and an unreadable record blocks every item; a worktree with submodules and a cross-volume destination are `pending` with a reviewed-procedure reason; `--exception` gives `exception-pending`; `--remove-candidate` gives `remove-candidate` owned by `cleanup_merged`, which apply never executes and which takes no approval here; an in-policy worktree is `retain`. The proposal leaves every source tree, the main repository and the run records byte-identical, and refuses a state directory placed inside a worktree it touches.

Hostile Git configuration during proposal and move: the marker program never ran. This test failed first: the move itself ran Git without the non-executing profile and launched the configured fsmonitor program. The move now runs under the profile (`neutral=True`); creation keeps Git's normal checkout, because a checkout is the authorized action that runs a repository's own filters.

A manifest-bound smoke command (argv list, no shell) runs at the destination after the move and its result is part of the item result.

Not exercised: a move across real volumes (refused by design and checked with a forced volume mismatch), a move of a worktree that holds submodules (refused), and an existing native controller handoff. Under the confirmed finish-in-place route no handoff is used, so its prerequisites were not needed here. The existing controller handoff requires a distinct clean registered target and is not a dirty-worktree relocation API; that is unchanged.

Fast gate: `python scripts/ci/run.py --profile fast` passed (18 groups).

## Plan delta

Disposition: Minor deltas. Evidence: (1) the plan names a cooperative-writer boundary; the implementation states it in the runbook and relies on the owner acknowledgment, because the final ancestor check cannot stop a replacement after Git starts. (2) The plan asks for process and lock observations; a process list is not available through the standard library, so the guard against an active session is the acknowledgment, and the Git lock. An operating-system refusal to rename a folder that a process holds open would make Git's move fail and leave the item pending, but that case was not tested with a real open handle. (3) The plan asks for per-item authorities in a local approval receipt; `--approve` writes it, but the tool cannot tell who runs it, so the approver is a recorded name and the receipt is only as trustworthy as the person who runs the command. Consequence for remaining phases: Phase 4 must run `--approve` only on explicit per-item answers from the user, and must not run `--apply` until those exist.

## CI impact

No pipeline file changed. The new test file `tests/validators/test_worktree_migration.py` needs a shard entry (listed in `coordinator-deltas.md`); it runs about 80 seconds and launches many Git processes.

## Deviations

None in code. No `# DEVIATION:` markers.

## Phase 4 preparation

The Phase 1 decision about the identity folder suffix still needs the user's answer. Other user decisions Phase 4 needs: the per-item approvals; the three pending worktree deletion decisions named in the plan (kept pending); disposition for the 35 permission-denied directories and two excluded volumes from the live audit; and whether the cloud-backed volume should be scanned at all, since it reports as fixed storage and a directory read on it blocked until the new timeout was added. Apply, `git worktree move`, `git worktree remove` and `git worktree prune` were not run against any real worktree.

## Next steps

Phase 4 is a live machine campaign and was not started.
