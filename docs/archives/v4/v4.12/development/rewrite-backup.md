# v4.12 attribution rewrite backup

Operator recovery record for the isolated all-ref rewrite. Created 2026-09-14 after Phase 1 commit `1b8f94df618fa1d2bba84eb51ca82356c1394201`. Original checkout and backup remain unchanged by the rewrite operation; remote publication is a separate explicit approval.

## Verified original mirror

- Backup path, relative to the original Nexus-Hub checkout: `../Nexus-Hub-backups/2026-09-14-v4.12-attribution/pre-rewrite.git`.
- Manifest: `../Nexus-Hub-backups/2026-09-14-v4.12-attribution/ref-manifest.json`, including the original source root, remote URL and exact local/remote ref tips.
- HEAD: `1b8f94df618fa1d2bba84eb51ca82356c1394201`.
- Local refs: 139; branches: 13; tags: 118; other refs: 8. All names and tips match the source at backup time.
- Reachable commits: source 1,697; mirror 1,697; set difference zero.
- Remote branches captured: main, develop and fix/target-manifest-git-trust-skip. The new v4.12 branch is local only.
- Seven stash commits are present as objects. Their local-only reflog is separately retained in `stash-reflog.txt`; cloning does not reproduce that reflog automatically.
- `git fsck --full` on the mirror exited 0. Output is retained in `backup-fsck.txt` beside the manifest.
- Available space before cloning: 401 GB; the source object database was approximately 239 MB. `--no-hardlinks` gives the mirror independent object files.

## Creation and local recovery

Run from the original Nexus-Hub checkout:

```powershell
git clone --mirror --no-hardlinks --quiet . ../Nexus-Hub-backups/2026-09-14-v4.12-attribution/pre-rewrite.git
git --git-dir ../Nexus-Hub-backups/2026-09-14-v4.12-attribution/pre-rewrite.git fsck --full
```

To create a separate recovery copy without overwriting either working repository:

```powershell
git clone --mirror --no-hardlinks ../Nexus-Hub-backups/2026-09-14-v4.12-attribution/pre-rewrite.git ../Nexus-Hub-recovery.git
```

Remote recovery must compare each current remote tip against the approved recovery lease, then restore the corresponding captured original branch/tag tip. Do not use a blanket mirror push: local stash, remote-tracking and Codex checkpoint refs are recovery data, not public branches. The earlier pre-cleanup `all-refs.bundle` remains an independent backup of the merged-branch cleanup boundary.

## Rewrite preparation

`uv tool install git-filter-repo --quiet` installed the operator tool outside project dependencies; `git filter-repo --version` reports `a40bce548d2c`. The rewrite will use an independently copied mirror and the Phase 1 checker policy. Explicitly enumerate every captured ref to prevent the tool's default remote-tracking ref renaming; preserve empty commits, merge topology, dates, commit encoding and ordinary message SHA references. Expire and prune only the rewritten copy after verification, because explicit-ref mode does not do that automatically.

The original mirror is never a rewrite target. The final publication ref set must be reviewed separately: local-only historical branches and internal refs do not become authorized remote branches merely because they exist in this backup.

## Executed rewrite and preservation proof

The independent target is `../Nexus-Hub-backups/2026-09-14-v4.12-attribution/rewritten.git`, relative to the original checkout. `rewrite-callback.py` beside the manifest loads the Phase 1 checker as policy owner, canonicalizes forbidden author/committer fields, and removes forbidden attribution fields plus their folded continuation lines. The callback was first exercised on a temporary repository with a Cursor author, GitHub committer, two forbidden fields, an annotated tag and fixed timestamps. Its checker returned exit 0; dates, tree, GitHub committer, ordinary prose and tag name matched their originals.

The full invocation used `git --git-dir <rewritten.git> filter-repo --force --prune-empty never --prune-degenerate never --preserve-commit-hashes --preserve-commit-encoding --commit-callback <rewrite-callback.py> --refs <every key in ref-manifest.json local_refs>`. These paths are resolved from the external manifest; `rewrite-output.txt` preserves the first failure and `rewrite-longpaths-output.txt` the successful attempt.

The first full attempt failed before changing any ref: `fatal: failed to stat 'refs/codex/turn-diffs/checkpoints/...': Filename too long`. Setting `core.longpaths=true` in the isolated target resolved the Windows environment mismatch. Every ref still matched the backup before retrying; no partially rewritten history was layered.

Independent verification used the generated `filter-repo/commit-map` and raw `git cat-file --batch` objects from both repositories. All 1,697 commit trees, author/committer timestamps and ordered parent relationships matched. An independent byte-pattern comparison confirmed exactly 182 co-author fields were removed and all other message bytes were unchanged. All 139 ref names, including 118 tags, remain. `rewrite-proof.json` records the result.

Only the rewritten repository ran `git reflog expire --expire=now --all` and `git gc --prune=now --quiet`. The former Cursor-trailer commit `89e8e3dcc70becf1743ca30c4a5135ba33f6cebe` is absent there and still present in the original backup. The live scanner returned `Attribution: 1697 commits scanned; 0 findings; 0 errors`.

## Active implementation checkout

Subsequent phases run from `../Nexus-Hub-worktrees/v4.12-implementation`, relative to the original checkout. It is a Git worktree of the rewritten mirror, on `feat/v4.12.0-sole-contributor-attribution`. The original checkout remains on its unre-written Phase 1 commit, available for recovery; it is not the active Phase 3 workspace. Rewritten Phase 1 is `0dd54bad647345d0602f31d20e535faccd1c2374`.

The rewritten repository's origin still reads the local backup, and its push URL is the nonexistent `PUBLICATION-DISABLED` path. Do not fetch the unre-written GitHub history into this candidate. Remote-state checks use the captured GitHub URL with `git ls-remote`, without importing old objects or refs. Final publication must replace the disabled destination only after approval of the precise branch/tag scope and lease values.
