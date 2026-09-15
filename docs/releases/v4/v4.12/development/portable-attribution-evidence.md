# Portable user-attribution qualification

Phase 5 extends v4.12.0 from Nexus-Hub's own history repair to installable user-attribution rules and Git enforcement. This record covers fresh installation, identity handling, existing hooks, rollback, platform delivery, review findings and the release boundary. Integration and release remain pending until their own checks complete.

## Candidate and evidence ownership

The implementation starts at `1d30cc33879c9009a7ef194becaf8bce504c0a61` on `feat/v4.12.0-sole-contributor-attribution`. The phase commit binds the final tracked implementation and this record. External receipts are under `Nexus-Hub-backups/2026-09-14-v4.12-attribution/` beside the worktree collection. Each Linux run retains its immutable staged patch, patch SHA-256, index tree, input HEAD, Python version and complete command output. Later passing evidence never replaces an earlier failed receipt.

## Delivered behavior

Both installers distribute `scripts/nexus_git_attribution.py` and activate it after installing the CLI. Default installation sets global hooks; workspace installation uses repository or worktree scope. The helper derives each user's effective Git identity. It does not distribute Nexus-Hub's maintainer identity or rewrite installed users' history. The repository-specific maintainer checker remains excluded from installation.

All 17 instruction templates include the same mandatory preflight and shared attribution guide. New work must use the configured user, with no agent identity, coauthor trailer or agent footer. Claude's documented empty commit/PR attribution settings are seeded through the canonical defaults and generated settings. Cursor receives the policy through sessionStart additional context, using the installer's resolved Python executable. Aider receives the policy read path, five disabled attribution flags and enabled Git verification. Existing conflicting settings are preserved with NEEDS SETUP notes. The detailed policy lives once in the distributed style guide; the five locked template word budgets increased by exactly 30 words for the new preflight section.

The new delivery contracts were checked against [Cursor's official hook reference](https://cursor.com/docs/hooks) and [Aider's official YAML reference](https://aider.chat/docs/config/aider_conf.html) on 2026-09-14. Cursor's sessionStart context is nonblocking and unavailable on ordinary cloud agents; local Git hooks remain the enforcement boundary. Aider searches home, repository and current-directory configuration in increasing precedence, so later user settings may override the seeded defaults. This targeted refresh does not renew unrelated platform-default verification dates or claim interactive model compliance.

## Functional verification

| Boundary | Representative operation | Observed result |
|---|---|---|
| New-user metadata | Commit as Alex Human, change repository configuration to Robin Human, commit and push again | Both commits use their respective configured human identities; existing remote baseline is accepted. |
| Identity overrides | Real commits with agent author/committer environment overrides, including a commit with `--no-verify` | The non-skippable message-preparation hook rejects the incorrect pending identity. |
| Messages | Mixed-case/folded attribution trailers and plain Generated/Made/Written agent footers | Commits reject the metadata; ordinary discussion of Claude in a subject remains allowed. |
| Outgoing history | Seed agent author/committer or prohibited footer before activation, then push | Push fails and the bare remote receives no branch. |
| Hosting-service history | Push human-authored history with GitHub's exact service committer; then attempt a service-authored commit | Legitimate human history is accepted; the service-author push is rejected. |
| Tags | Checked user tag and normal push; annotated tag with wrong tagger | User tag succeeds; outgoing wrong tagger fails. |
| Existing hooks | Prior pre-commit failure, pre-push arguments/input, commit-msg appending a trailer | Original behavior is preserved; a trailer appended by the prior hook is rejected afterward. |
| Special hooks | Push into an `updateInstead` repository with no push-to-checkout hook | Git still updates the worktree; installing the guard does not replace the default with a no-op hook. |
| Streaming hook | Prior proc-receive reads a line while stdin remains open | Independent scratch reproduction confirms forwarding does not wait for EOF. |
| Worktrees and replay | Worktree-specific hooks configuration and a cherry-pick authored by another human | Correct scope activates; original human author is retained with the current user as committer. |
| Interpreter lifecycle | Install with temporary Python, remove it, check through system Python, reinstall | Check requires reinstall; obsolete special wrapper is removed using its recorded interpreter; the next commit succeeds. |
| Real workspace installers | Bash and PowerShell on Windows, installed CLI, five selected agent platforms | Both installations pass, execute Cursor context delivery, verify Aider configuration, expose the rules and reject an agent commit. |
| Real global installers | Native Windows PowerShell and Linux Bash in disposable homes | Both installations pass and activate the installed guard. |
| Rollback | Install, uninstall, reinstall; separately change hooks configuration before uninstall | Previous configuration is restored; later user configuration is not overwritten. |

Missing identity produces an explicit setup-pending result and blocks contributions. A non-Git workspace requires `git init` and workspace activation. A repository overriding global hooks must activate at workspace scope. These states are not reported as active protection.

## Validation receipts

- Windows focused Git and CI checks passed 35 cases including the interpreter-lifecycle regression. After the human-name correction, all 36 non-installer Git cases passed with four installer parameter cases deselected. Earlier actual workspace installer checks passed both runtimes; the native global PowerShell check passed with the POSIX-global-on-Windows case explicitly skipped.
- Windows platform-default, template and handbook-related qualification: 88 passed. The repaired date-format and documentation-budget subset separately passed 46 checks.
- Windows fast profile: all 15 commands passed in 75.3 seconds. Final workflow-only reconciliation passed both commands after macOS coverage was added. Handbook freshness reports both live documents verified with no errors.
- Linux `phase5-linux-final`: all 47 full-profile commands passed in 393.7 seconds. This receipt predates the last two interpreter-lifecycle corrections; it is not presented as final-byte evidence for them.
- Linux `phase5-linux-qualified`, `phase5-linux-terminal` and `phase5-linux-complete`: all 47 commands passed in 381.7, 380.4 and 392.2 seconds respectively. The last includes the human-name and GitHub service-committer fixes, but predates the final Cursor/Aider delivery changes.
- Broad Windows installer/validator/integration run: 2 failed, 2,823 passed, 50 skipped in 2,598.89 seconds. Both failures used the earlier non-ISO Claude verification-date cell; the corrected subset passes. The original run remains a non-pass.
- Targeted Cursor/Aider/defaults suite: 95 passed in 68.99 seconds, including preservation and invalid-YAML setup behavior. The subsequent absolute-interpreter refinement is separately checked before final qualification.
- Final Windows installation run: 3 passed, 1 skipped, 37 deselected in 374.88 seconds. Bash workspace, PowerShell workspace and native PowerShell global installation each execute the generated Cursor context command, verify Aider attribution settings and exercise human/agent commits. Global Bash on Windows remains explicitly outside native coverage.
- Final Windows fast profile `phase5-fast-delivery`: all 15 commands passed in 121.5 seconds. Targeted independent adapter review passed 26 cases and executed the generated Cursor command with Python absent from PATH and spaces in the installed home. No delivery-review findings remain.
- Linux `phase5-linux-delivery`: 46 of 47 commands passed in 341.9 seconds; repository tests reported 1 failed, 5,011 passed and 345 skipped. The sole failure assumed uninstall deletes Aider's deliberately retained shared YAML. Independent review confirmed append-only configuration ownership; the contract now verifies exact byte preservation while retaining every other file-leak assertion. The guide documents cleanup of the retained read path after workspace platform uninstall. The original failed receipt remains immutable.
- Final Linux `phase5-linux-delivery-qualified`: all 47 full-profile commands passed in 320.2 seconds with zero failures, skipped commands or advisory failures. The immutable source binding and staged patch cover the final implementation, adapter delivery, corrected ownership contract and documentation. Subsequent edits only reconcile this result and phase status before the commit.

The first Linux Phase 5 run failed three commands: documentation budgets, stale handbook evidence and repository tests containing the date/budget assertions. Those causes were fixed and the passing rerun is separate. The first Windows installer attempt exposed output decoding and Python alias differences; corrected actual installer runs passed. A global Bash installation on Windows exposed an existing POSIX virtual-environment layout assumption, so supported native coverage is Bash on Linux/macOS and PowerShell on Windows. No unrelated installer repair or timeout increase was made.

## Independent review and convergence

Correctness, testing, project standards and maintainability reviewers inspected the new portable feature. Reproduced correctness findings were fixed: validation after a prior commit-msg hook, special-hook absence, streaming stdin forwarding, worktree configuration precedence, unavailable recorded Python, obsolete wrappers after switching Python, legitimate human names containing an agent product word and Cursor's dependence on a Python PATH alias. New real-Git and native-command regression coverage exercises the corrections. Testing findings led to actual installer cases, outgoing agent-history rejection and human cherry-pick coverage. Standards findings led to the portable attribution decision record and sourced Claude defaults. Maintainability review found no reportable defect.

Inspected and rejected candidates include shell quoting for paths with spaces, subprocess Git argument construction, ordinary hook argument/input forwarding, rollback protection for later user configuration, required Bash/PowerShell delivery duplication, and splitting the small standalone helper into a new package. The footer detector's tested variants and use of another Python while the installed interpreter remains available were also retained as correct behavior. No clean review of the older history rewrite is inferred from these reviews.

Direct API writes, cloud runtimes without this installation, altered executables, deliberately disabled hooks and hosting authentication cannot be guaranteed by local Git hooks. The installed rules require the intended publishing account and verification before other publication paths. Git has no pre-tag hook: the checked CLI protects local tag creation, and pre-push validates outgoing annotated tags. Rebase follows the same replay-state handling but has no separate live rebase qualification in this record. Native macOS execution is assigned to the integration PR's existing installer matrix and remains pending until that job passes.

The automated evidence exercises installers, delivered instruction artifacts and actual Git operations. It does not represent interactive sessions with every supported agent or prove that every model follows prose instructions. The Git guard provides the independently tested normal-operation boundary.

## Documentation and CI reconciliation

The distribution handbook retains its five sections/slides and approved presentation design. Its ownership explanation now covers the new guard. Source, model, generated HTML and build metadata agree. Chromium measured 200 states across ten viewport sizes with zero defects; the changed desktop slide and mobile reading section were also visually inspected. The overview handbook is unchanged and its existing receipt remains fresh. This targeted maintenance verification does not close the separate native-authoring gap from v4.11.

The portable helper reuses standard-library Python, the existing CLI and both installer copy/activation paths. No new service, package, skill or hook catalog entry is needed. The local generated Git wrappers are not catalog agent-event hooks. Runtime guidance belongs in living guides/style guides, the implemented design in `docs/decisions/`, and qualification in this release tree. No unrelated layout migration is required.

CI already runs all repository tests on Linux. The existing Windows installer/validator group now includes the attribution tests, and the macOS installer job runs native Bash and Git attribution cases. Existing required contexts, event separation, timeouts and other platform jobs are preserved. The extension uses one final phase commit and normal feature integration; it does not repeat the historical force-push.

## Release handoff

PR #217 at `3ba28395` exposed a native macOS test-environment gap: both Bash installer cases completed installation and policy delivery, then the test interpreter failed to import PyYAML for the Aider configuration assertions. The macOS test step now installs that test dependency alongside pytest. The original job log is retained as `pr217-macos-first.log` in the external evidence root; this correction does not change the installer or attribution runtime. Required checks must pass on the corrected head before merge.

The [known gaps](../known-gaps.md) retain GitHub PR-ref limitations, the stale Code contributor display, incomplete historical adversarial review and the earlier Windows whole-profile timeout. None is silently closed by portable enforcement. The existing CI lint/reporting and native authoring gaps retain their owners. The user operation and recovery procedure is in the [attribution guide](../../../../guides/user-attribution.md).

Before release, merge the feature PR with required checks green, verify post-merge results, derive release notes from the actual `v4.11.2..develop` range, and obtain the release-notes approval required by `/update release` before version mutation. v4.11.2 does not contain this portable guard. A new published artifact and its download verification are required before telling users it is available to install.
