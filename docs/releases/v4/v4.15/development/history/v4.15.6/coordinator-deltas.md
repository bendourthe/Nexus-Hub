# Coordinator Deltas

**Version**: v4.15.6
**Scope**: Phases 1 to 3 (Inventory and Identity, Centralized Creation and Distribution, Migration and Recovery)
**Audience**: the coordinator who owns the shared files below. The worker did not edit any of them.

Each item names the file, the exact change, and why it is needed.

## CHANGELOG.md

Add under `## [Unreleased]`:

- Added `nexus-hub worktree` (`path`, `create`, `list`, `audit`, `migrate`) and the helper `scripts/nexus_worktrees.py`: one configurable worktree root (`NEXUS_WORKTREE_ROOT`, then the user's `config/worktrees.json`, then `~/.worktrees`), a stable repository identity, a resumable read-only machine audit with an explicit coverage ledger, and a reviewed-manifest migration executor that preserves dirty, staged, untracked and ignored content.
- Added the always-on `worktree-policy` PreToolUse guard (`worktree-policy.sh`, `worktree-policy.ps1`, `_worktree_policy.py`) for `git worktree add` and `git worktree move`, registered for `Bash|PowerShell` and wired into the Antigravity `run_command` group.
- Changed `using-git-worktrees`, the implement runbook and the fourteen instruction templates to place worktrees at `<root>/<repository-identity>/<worktree-name>`.

Capability usage gate (update.md governance step 6) for the opt-in surfaces:

- Activation: nothing is opt-in. The guard and helper install with the normal installers.
- Validation command: `nexus-hub worktree path --repo <checkout> --name <name> --json`.
- Disable or rollback: remove the single `worktree-policy` group from the installed `settings.json` (or the Antigravity `hooks.json` set entry). `NEXUS_HOOK_PROFILE` and `NEXUS_DISABLED_HOOKS` do not disable it by design.
- Authority not granted: the guard reads only the proposed command and never runs it; `migrate` moves only worktrees named in an approved manifest and never removes or unlocks anything.
- Documentation: `docs/runbooks/worktree-organization.md`.

## MANIFEST.sha256

Regenerate after the release-version reconciliation. New distributed files: `scripts/nexus_worktrees.py`, `catalog/hooks/_worktree_policy.py`, `catalog/hooks/worktree-policy.sh`, `catalog/hooks/worktree-policy.ps1`. Changed distributed files: both installers, `catalog/hooks/settings.json`, `catalog/skills/workflow/using-git-worktrees/SKILL.md`, the implement runbook, `scripts/nexus_hub_cli.py`, `scripts/check_installer_smoke.py`, `scripts/lib/integrations/antigravity.py`, and the fourteen instruction templates.

## scripts/lib/installer/legacy_fingerprints.json

All fourteen templates under `templates/ai-instructions/` that carry a Branching or Plan Lifecycle section changed. The five budgeted bases (claude, codex, cursor, gemini, opencode) had zero to 34 words of headroom under `docs/policy/doc-budgets.json`, so in them the existing branching sentence now ends "See `git-branching-workflow` (branches) and `using-git-worktrees` (`nexus-hub worktree create`)." (two words fewer than before). The other nine carry a fuller bullet with the layout. Budgets pass (`scripts/validate_doc_budgets.py`: 8 within ceiling). If a uniform fuller bullet is preferred, the five ceilings would need a justified raise of about 40 words. Run `python scripts/build_legacy_fingerprints.py`, then `python scripts/build_legacy_fingerprints.py --check`, after the template and version reconciliation. The worker ran `python scripts/check_base_template_parity.py` (passes).

## data/ registry (using-git-worktrees)

The worker left the `SKILL.md` frontmatter unchanged because `scripts/check_registry_entries.py --check --strict` compares it to `data/skills.json`. The body is new. Apply these together in `SKILL.md`, `data/skills.json` and `data/SKILL_INDEX.md`:

- `summary_l0`: "Place isolated worktrees at one central root through the nexus-hub worktree helper"
- `overview_l1`: replace the sentence beginning "Step 1 prefers the harness's native worktree tool" with "Step 1 resolves the destination with the central helper and places every new worktree at `<root>/<repository-identity>/<worktree-name>` through `nexus-hub worktree create`, treating a native tool that cannot honor that destination as a visible exception."
- `description`: replace "so the work happens in a clean separate workspace instead of the main checkout." with "so the work happens in a clean separate workspace instead of the main checkout, at the one central worktree root."

Derived counts that include hooks (AGENTS.md "37 registered hooks" and any generated inventory) grow by one hook, `worktree-policy`.

## scripts/ci/profiles.py (CI shards)

Every new test file needs a shard. Process-launch weight is noted because Windows shards are balanced by launches:

| Test file | New or changed | Suggested shard | Weight note |
|---|---|---|---|
| `tests/validators/test_worktree_policy.py` | new | a Windows validators shard and the Linux tests job | about 40 s, real Git repositories and a hostile-config fixture |
| `tests/validators/test_worktree_migration.py` | new | its own light Windows validators shard | about 80 s, hundreds of Git launches |
| `catalog/hooks/tests/test_worktree_policy.py` | new | the hooks job and the Windows hooks shard | about 50 s, starts bash and PowerShell per case |
| `tests/validators/test_plan_worktree_isolation.py` | changed (23 tests added) | existing shard | about 20 s |
| `tests/installer/test_installer_smoke_postconditions.py` | changed | existing shard | seconds |
| `tests/integrations/test_antigravity.py` | changed | existing shard | already about 2 minutes |
| `catalog/hooks/tests/test_antigravity_guard_delivery.py` | changed | existing shard | one test added |
| `catalog/hooks/tests/test_hook_sibling_parity.py` | changed | existing shard | 10 parametrized cases added |

Run the shard collection guards after listing the new files.

## docs/policy/permission-mode-contract.md

`worktree-policy` exits 2, so the contract asks for a table entry and a test across `default`, `auto` and `bypassPermissions`. The worker proved the behavior in `catalog/hooks/tests/test_worktree_policy.py` (all four modes deny) but did not edit the policy or `test_permission_mode_contract.py`. Proposed policy text: list `worktree-policy` under "Not covered, by design" as a workflow rule the user configured independently of approvals, active in every mode.

## Distribution handbook and guide evidence

Installer edits normally need refreshed distribution-handbook evidence and remapped guide `data-src` installer line citations. Both installers gained one copy block each (after the `nexus_hub_cli.py` block).

## docs/todos.md

Tick T001 to T012 (12 of 26 tasks, 3 of 5 phases) and update the dashboard counts.

## Hook registration authority

The single exact append to `catalog/hooks/settings.json` was made as instructed. The worker cannot confirm that the separately qualified typed permission and genuine capture exist for it; the coordinator should confirm that before the registration is treated as authorized.

## Phase 4 inventory evidence (derived report)

The Phase 4 dry runs propose from a derived copy of the live audit report, not from the original. Full filter and reasoning: `history/v4.15.6/phase-4-prep.md`.

- Original report SHA-256: `adb682f464a9d34fae6e705eff68971d6af311825e4627f72ff2fe5c1eb8b60a` (9,828 repositories, 1,119 linked worktrees, status partial).
- Derived copy SHA-256: `283aa9f86168a1d282d09f98f7a1a8f3b400274bfb005094ba7db6a7495febdc` (5 repositories, 117 linked worktrees).
- Filter: drop a repository whose main checkout or common Git directory path contains `/.venvs/`, `/appdata/local/temp/`, `/appdata/roaming/`, `c:/tmp/` or `/pytest-of-`; then keep only repositories with at least one linked worktree. 9,778 fixture repositories and 45 repositories without linked worktrees were dropped.
- The derived copy's `derived_from.rule` sentence is looser than the filter that ran; the filter above is authoritative.

Hashing budget (for the CHANGELOG): the migration manifest now records `hash_budget_bytes`, apply reuses it, and `migrate --dry-run` takes `--hash-budget-mib`. A manifest without the field keeps the 512 MiB default.

## Review hardening (after the independent review of e6f53fa04..6286f2e61)

Fixed in code and tests: an OS error on one item leaves it pending and the rest processed, and `main` always prints a terminal JSON status; apply re-checks native binding and unreadable run records under the repository lock; the Git executable is never resolved from the current directory; the tracked patch is captured and hashed as bytes; size-only fingerprint rows record the modification time; a failed smoke command makes the run partial; every child process gets a closed stdin; an unreadable Git configuration is cannot-verify; inspection status ignores submodules; the dry run proposes a dirty worktree as an exception (`uncommitted-changes`) unless `--include-dirty` is given; `--approve` needs at least one `--item` and accepts several in one command; the guard denies relative destinations after a directory change, denies `--approve` from agent tool calls, and no longer fires on quoted text, single-quoted spans or heredoc and here-string bodies.

Proposed known gaps for Phase 5 (not fixed here):

- `recover_item` classifies an interrupted item outside the repository lock, so a concurrent operation could change the state it reads. Take the lock around recovery.
- Notice files are keyed by the manifest file name and rewritten on a dry run; reusing a manifest name after deleting the manifest overwrites the tokens of the old notices. Key notices by digest.
- `worktree.useRelativePaths` (Git 2.48 and later) writes relative gitdir pointers; the back-pointer and ownership checks assume absolute pointers. Read and normalize relative pointers.
- Destination length is checked for the worktree folder only, not for the deepest path inside it. Add a deepest-path check against the platform limit before a move.
- The placement guard checks that a destination sits two levels under the root, not that the identity folder belongs to this repository. Verify the identity folder against the identity mapping when the guard can read it.
- An unquoted bash heredoc can run command substitutions; the guard treats every heredoc body that does not feed a shell as text.
- The ignore-submodules status option means submodule state is not part of the fingerprint; submodule worktrees are still refused by a separate check.
