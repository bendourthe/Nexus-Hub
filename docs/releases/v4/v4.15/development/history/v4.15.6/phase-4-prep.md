# Centralized Worktrees Phase 4 Preparation

**Version**: v4.15.6
**Scope**: read-only and dry-run evidence gathered after Phase 3, before any machine campaign. No worktree was moved, removed or pruned, and nothing was applied or approved.

## User decisions recorded

1. The eight-hex identity suffix stays.
2. The 35 permission-denied folders and the two excluded volumes are recorded as a known gap. The cloud-backed volume is not rescanned.
3. Only idle worktrees migrate now. Active v4.15 run worktrees stay put as exceptions until minor close: the v415-controller-g7, v4.15.6, v4.15.7 and v4.15.9 worktrees, and any worktree with uncommitted changes.
4. The three plan-pending worktrees (check-minor-budget-qualified, develop-install-2ef94ca, develop-install-8bc588e) are remove-candidates with the reason `pending-user-decision`.
5. The fingerprint hashing budget is recorded in the manifest and reused by apply (`--hash-budget-mib`). This pass covers Nexus-Hub only; every item of another repository is an exception with the reason `other-repository-deferred`, and the other sessions' scratch worktrees are exceptions with the reason `other-session-scratch`.
6. The derived inventory described below is accepted.

## Derived inventory

The live audit report was too large to propose from in reasonable time: 9,828 repositories, of which 9,778 are pytest and temporary fixtures, and a proposal over all of them ran for about an hour without finishing. A derived copy was produced by a scratch script (`filter_real.py`, not part of the repository) that reads the original report and writes a new one with the same schema.

- Original report: `<scratch>/live/audit-report-4.json`, SHA-256 `adb682f464a9d34fae6e705eff68971d6af311825e4627f72ff2fe5c1eb8b60a`.
- Derived copy: `<scratch>/live/audit-report-4-real.json`, SHA-256 `283aa9f86168a1d282d09f98f7a1a8f3b400274bfb005094ba7db6a7495febdc`.

Filter, exactly as run. A repository is dropped as a fixture when its main checkout path or its common Git directory path, lowercased with forward slashes and a trailing slash, contains any of: `/.venvs/`, `/appdata/local/temp/`, `/appdata/roaming/`, `c:/tmp/`, `/pytest-of-`. The test looks only at the main checkout and common directory, never at the linked worktree paths, so a repository with a worktree in a temp folder is kept. Among the kept repositories, only those with at least one linked worktree (not the main one, not a bare one) remain. Result: 9,778 fixture repositories dropped, 45 repositories without linked worktrees dropped, 5 repositories and 117 linked worktrees kept (Nexus-Hub, MileStone, algorithms, console-dev and a bare backup). Nothing else in the report was edited; the copy adds a `derived_from` object.

One inaccuracy to know about: the `derived_from.rule` sentence inside the derived copy says "no path under a virtual-environment folder, a temp folder or a pytest fixture folder". That wording is looser than the filter above. The filter above is the one that ran. The sentence was left alone so the recorded hash stays valid.

A manifest proposed from the derived copy records the derived copy's hash (`inventory.sha256`), not the original report's, and carries `inventory.status` `partial` inherited from the original (35 permission-denied folders, two excluded volumes).

## Hashing budget

The shipped budget (512 MiB of ignored files hashed per worktree) was impractical on this host: each file open costs about 14 ms under real-time antivirus scanning, so one Android build tree took about two minutes. The first manifest (`v4156-manifest.json`, SHA-256 `550013b75ce6fa7eedcc6f130c3e8a47b43793c27919f20c0326ccd9131bba12`) was produced through a wrapper that lowered the budget to 16 MiB. It was proposal-only: apply would have refused it, because apply recomputed fingerprints with the default budget and the ignored-file digest differs.

The follow-up change records `hash_budget_bytes` in the manifest and makes apply reuse it. A manifest without the field uses the default. The proposal takes `--hash-budget-mib`. Limit that remains by design: beyond the budget, a changed ignored file is detected only if its size changes.

## Not done

- Apply, approve, `git worktree move`, `git worktree remove` and `git worktree prune`: not run.
- The three plan-pending removal decisions: not decided here.
- A rescan of the cloud-backed volume or of the 35 permission-denied folders: deliberately not done.
