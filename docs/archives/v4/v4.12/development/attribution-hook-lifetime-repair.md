# Attribution hook lifetime repair - v4.12 follow-up

**Purpose**: Record the worktree-lifetime defect in the shared Git attribution guard, its bounded repair, and the evidence needed before removing the installer worktree. Read during v4.12 gap reconciliation and worktree cleanup.

## Reproduction

On 2026-09-23, the repository's `core.hooksPath` pointed to its shared `.git/nexus-attribution-hooks` directory, but every wrapper invoked `scripts/nexus_git_attribution.py` by an absolute path inside a temporary linked worktree. `attribution check` from a second worktree reported `Attribution hook missing or modified: applypatch-msg`. Removing the installer worktree would have left every wrapper unable to invoke the guard. The existing main checkout is dirty and behind integration, so using it as the permanent script host would not have been safe.

A real Git regression test creates an installer worktree, installs from a source file there, removes that worktree, then checks the guard and attempts two commits. Before the implementation it failed at `attribution check` with the wrapper mismatch. After the implementation it passes, permits the configured human commit, and rejects a `Co-Authored-By` trailer. The original failing test result is not relabeled as a pass.

## Candidate repair

Workspace and global installation now place a copy of the guard script in the guard's own hook directory and make wrappers invoke that copy. The install state records a SHA-256 digest; `check` rejects a missing, symlinked, or modified copy and a newer caller source that has not been installed, while installation refuses to replace a symlinked guard. Existing hook chaining, identity checks, message checks, and push-destination scanning remain in the same script. Reinstallation moves the executable copy forward when the installed script changes. A second red-before/green-after test proves source drift is not silently accepted and a modified installed copy is rejected.

## Qualification boundary

Both focused regressions pass, and the final `tests/test_git_attribution.py` run passes 45 tests with one Windows-host skip. Ruff passes for the changed script and test file; the native fast profile passes 17/17 and the docs group passes 8/8. The affected distribution handbook was rebuilt reproducibly from retained inputs, reviewed in both views, and measured in 200 Chromium states with zero errors; its read-only freshness gate verifies both living handbooks. Hosted, merge-tree, and actual cleanup evidence remain pending. This document is a local candidate record, not a completed publication claim. The dirty main checkout and unrelated future-plan branches remain outside cleanup scope.
