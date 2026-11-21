# Centralized Worktrees Phase 2

**Version**: v4.15.6
**Phase**: 2, Centralized Creation and Distribution
**Base**: Phase 1 commit `bdda0c832`
**Worktree**: `~/.worktrees/nexus-hub/v4.15.6`

## Subtasks

| Task | Outcome |
|---|---|
| T005 | `create` and `list` added to `scripts/nexus_worktrees.py`; `nexus-hub worktree` forwards to it from `scripts/nexus_hub_cli.py`. Creation is serialized per repository, rechecks ownership under the lock, refuses an existing branch, an unresolved base, a dash-leading argument and an occupied destination, and reports `exists` for a repeat of the same branch and name. |
| T006 | Both installers copy `nexus_worktrees.py` (one block each, after the CLI core). `scripts/check_installer_smoke.py` expects the script, the `worktree-policy` hook and helper in the workspace, and exactly one host-correct `Bash|PowerShell` registration. `installer.ps1` kept its BOM and parses under Windows PowerShell 5.1. |
| T007 | `using-git-worktrees` is the owner of placement (central root, native-tool table, uncovered surfaces, migration and cleanup pointers). The implement runbook delegates to it. Instruction templates carry the placement pointer. The guard pair and `_worktree_policy.py` ship; the single exact registration is appended to `catalog/hooks/settings.json`; Antigravity gains the script in its curated list and in the `run_command` group. |
| T008 | New creation, parity and delivery tests, the real installer run, this history, one local commit. |

## Evidence

Python suites: `tests/validators/test_worktree_policy.py` (43), `tests/validators/test_plan_worktree_isolation.py` (54, of which 11 are new), `tests/installer/test_installer_smoke_postconditions.py` (39, of which 5 are new) passed together as 136 tests with the Phase 2 helper in place. Hook suites: `catalog/hooks/tests/test_worktree_policy.py` (24 tests, each running the real `.sh` and `.ps1`) and the worktree cases of `test_hook_sibling_parity.py` and `test_antigravity_guard_delivery.py` passed (34 selected). `tests/integrations/test_antigravity.py` passed (35). `catalog/hooks/tests/test_installer_smoke.py` passed (44). `scripts/check_installer_parity.py` passed.

Entry-point parity. The same fixture worktree is created through the helper script, the CLI, and an installed copy of the CLI and helper under a temporary home. Ownership, location, `created` then `exists`, the refusal for the same name with another branch (`destination-registered-other-branch`), `base-unresolved` and `invalid-branch` are identical across the three. PowerShell 5.1 and Git Bash resolve the same destination for a name with spaces and an apostrophe. (A name with embedded double quotes is altered by Windows PowerShell 5.1's own native-argument quoting before the helper sees it, so the test uses a name without them.)

Refusals observed before any Git write: an existing branch, a relative root (`root-not-absolute`), a root inside the repository (`root-inside-repository`), a dash-leading branch, and a missing helper (`nexus_worktrees.py missing`, exit 2). Concurrency: three simultaneous creates of one branch and name gave one `created` and two `exists`; three of one name with different branches gave one success and two refusals, with exactly three registrations and no lock file left behind. A held lock refuses with `repository-locked`.

Real installer. `python scripts/ci/run.py --profile platform --only workspace-smoke` ran the Windows installer into a redirected home and workspace and passed the shared postconditions, which now include the helper, the guard payload and its single registration. The POSIX installer was edited in lockstep and parse-checked (`bash -n`); it was not run on this host.

Guard behavior, through both wrappers: out-of-root, sibling, vendor-directory, direct-child and over-deep destinations deny with exit 2; in-root destinations, `list`, `prune` and unrelated commands allow; `bash -c`, `eval` and command-substitution wrappers deny; an invalid root denies a worktree mutation but not other commands; the minimal profile, `NEXUS_DISABLED_HOOKS`, and the `default`, `auto`, `dontAsk` and `bypassPermissions` modes all still deny; a repository file cannot set policy; with no Python interpreter a worktree add or move is denied and anything else is allowed; helper collection works from the `.sh` alone and the `.ps1` alone, a comment-only reference is not collected, and an isolated copied payload with no source back-reference behaves the same. The guard helper and the CLI agree on root validation for a table of cases.

Antigravity: the real bridge turns `CommandLine` and `Cwd` into the guard's input; an out-of-root add returns `deny`, an in-root add and `git status` return `allow`, under both shells. Cursor: the guard is delivered only through the catalog `settings.json` registration, with no curated or native entry, and the test asserts exactly one registration appended last. Not exercised: a live Cursor, Codex or Antigravity host; hosts that run no Nexus-Hub hooks are listed as uncovered in the skill and the runbook.

Fast gate: `python scripts/ci/run.py --profile fast` passed (18 groups). `python scripts/check_base_template_parity.py` passed. The five budgeted templates were at their word ceilings, so the pointer was merged into the existing branching sentence (two words shorter than before) and `scripts/validate_doc_budgets.py` passes.

## Plan delta

Disposition: Minor deltas. Evidence: (1) `tests/validators/test_plan_worktree_isolation.py` already existed with 43 tests about plan isolation; the new tests were appended and the four assertions that named superseded text were kept satisfied by keeping the vendor-directory and "predictable directory" sentences, so no existing test was edited. (2) The `SKILL.md` frontmatter was not changed because the registry text-agreement check compares it with `data/skills.json`, which the coordinator owns; the proposed text is in `coordinator-deltas.md`. (3) `docs/policy/permission-mode-contract.md` asks every exit-2 hook for a table entry and a three-mode test; the test is in the worker's own file and the policy edit is a coordinator delta. Consequence for remaining phases: none for Phase 3; Phase 5 should reconcile the three coordinator items.

## CI impact

No pipeline file changed. New or changed test files and their suggested shards are in `coordinator-deltas.md`. The new hook test starts bash and PowerShell per case (about 50 seconds) and the Antigravity registration test is already about two minutes, so shard weight matters on Windows.

## Deviations

None in code. No `# DEVIATION:` markers.

## Next steps

Phase 3 adds the reviewed-manifest migration executor, interruption recovery and the hand-off contract.
