---
name: using-git-worktrees
description: "Use when starting isolated feature work, beginning a new branch, or before executing an implementation plan that will modify files, so the work happens in a clean separate workspace instead of the main checkout, at the one central worktree root. Trigger phrases: start a worktree, work in isolation, new feature branch, spin up a workspace, isolate this change, before I start implementing, set up an isolated environment. SKIP for quick in-place edits, read-only exploration, or when you are already inside an isolated worktree or a disposable sandbox."
summary_l0: "Place isolated worktrees at one central root through the nexus-hub worktree helper"
overview_l1: "This skill ensures substantial feature work happens in an isolated worktree rather than the shared main checkout, using a safe, ordered procedure. Step 0 detects whether you are already isolated (comparing the git-dir against the git-common-dir, with a submodule guard) so you never nest a worktree. Step 1 resolves the destination with the central helper and places every new worktree at `<root>/<repository-identity>/<worktree-name>` through `nexus-hub worktree create`, treating a native tool that cannot honor that destination as a visible exception. Step 3 auto-detects and runs project setup (install dependencies, copy env files). Step 4 verifies a clean test baseline before reporting the workspace ready. It includes a quick-reference command table, common mistakes, red flags, and a binary verification checklist. Use it before executing any multi-file plan."
---

# Using Git Worktrees

Isolated work belongs in an isolated workspace. A git worktree gives a branch its own directory backed by the same repository, so feature work, experiments, and plan execution do not collide with the main checkout or with each other. This skill encodes the safe sequence for getting into a worktree: confirm you are not already isolated, create it at the central root through the helper, verify the target path is safe before creating anything, set the project up, and confirm a clean baseline before declaring the workspace ready.

## When to Use This Skill

Use this skill when:

- You are starting a self-contained feature, refactor, or experiment that will touch multiple files.
- You are about to execute an implementation plan (for example via `[[incremental-implementation]]` or the `/implement-phase` command).
- You want to keep an in-progress change isolated from the main checkout so the main checkout stays releasable.

**When NOT to use:**

- Quick in-place edits (a one-line fix, a typo) where setting up a workspace costs more than the change.
- Read-only exploration or code review that modifies nothing.
- When you are **already** inside an isolated worktree or a disposable sandbox. Creating a worktree from inside a worktree is almost never what you want; Step 0 below catches this.

## Step 0: Detect Existing Isolation First

Before creating anything, determine whether you already have isolation. Creating a worktree when you are already in one (or inside a submodule) produces confusing nested state.

POSIX:

```bash
# Are we even in a git repo?
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Not a git repo"; exit 1; }

# Submodule guard: if this is a submodule, stop and surface it rather than
# creating a worktree in an unexpected place.
superproject=$(git rev-parse --show-superproject-working-tree 2>/dev/null)
if [ -n "$superproject" ]; then
  echo "Inside a submodule of: $superproject - resolve at the superproject level, not here."
  exit 1
fi

# Isolation check: in the main checkout, git-dir and git-common-dir are equal.
# In a linked worktree, git-dir points under .git/worktrees/<name> while
# git-common-dir still points at the shared repo. If they differ, we are
# already in a worktree.
gitdir=$(git rev-parse --git-dir)
commondir=$(git rev-parse --git-common-dir)
if [ "$gitdir" != "$commondir" ]; then
  echo "Already in a linked worktree - no new worktree needed."
  exit 0
fi
```

PowerShell equivalents (Windows users without Git Bash): run the same `git rev-parse` commands and compare with `if ($gitDir -ne $commonDir) { ... }`. The git commands are identical; only the shell glue differs (`$(...)` becomes `$(git rev-parse --git-dir)` assigned to a variable, and `[ ... ]` becomes `if (...)`).

If Step 0 reports you are already isolated or inside a submodule, stop. Do not proceed to Step 1.

## Step 1: Create the Worktree at the Central Root

This skill owns where a linked worktree lives. Every Nexus-Hub creation flow uses one resolver, `nexus-hub worktree`, and one layout: `<root>/<repository-identity>/<worktree-name>`. The root is the `NEXUS_WORKTREE_ROOT` variable, then the user's own `config/worktrees.json` under the Nexus-Hub home, then `~/.worktrees`. A repository file never sets it, and nothing falls back silently to a sibling, vendor, temporary, network, or synchronized folder. Other skills and instruction files delegate here instead of restating placement.

### Step 1a: Create through the helper

```bash
nexus-hub worktree path --repo <checkout> --name <name> --json     # resolve only, writes nothing
nexus-hub worktree create --repo <checkout> --branch <branch> --base <commit> --name <name>
nexus-hub worktree list --repo <checkout> --json                   # registered paths and canonical destinations
```

`create` refuses an out-of-policy root, an existing branch, an unresolved base, a destination another repository owns, a case or name collision, and a destination reached through a symlink or junction. It exits 0 on success, 2 when it refused before changing anything, and 3 when a check could not be completed. Read the JSON `status` and `code`; do not retry with another path.

### Step 1b: Native worktree tools

A native tool is used only when it can honor the resolved destination.

| Surface | Can it create at the resolved destination | What to do |
|---|---|---|
| `nexus-hub worktree create` | Yes | Preferred everywhere. |
| Claude Code `EnterWorktree` with `name` | No. It creates inside `.claude/worktrees/`, a vendor directory | Visible exception: do not use `name`. Create with the helper, then call `EnterWorktree` with `path` set to the created worktree. |
| Claude Code `EnterWorktree` with `path` | Not a creator; it enters a worktree the repository already registers | Allowed after Step 1a. |
| Raw `git worktree add` or `git worktree move` | Yes, if you pass the resolved destination | Allowed only with the destination from `path`. The `worktree-policy` guard refuses any other destination on hosts that run Nexus-Hub hooks. |
| Hosts without Nexus-Hub hooks or with their own worktree feature (Cursor and Codex agent worktrees, Copilot, a manual shell) | Not verified | Uncovered. The guard does not run there, so use the helper and expect `nexus-hub worktree audit` to report any worktree placed elsewhere. |

The guard covers recognized `git worktree add` and `git worktree move` commands in the Bash and PowerShell tools. It cannot certify a destination built from a variable or substitution, an alias, a script, or a nested shell, and it refuses those that it can recognize as worktree mutations. This is organizational enforcement on supported surfaces, not an operating-system boundary.

**Never place a worktree inside a vendor or tool directory**, even when that directory is git-ignored. `.claude/`, `.cursor/`, `.vscode/`, `.idea/`, `.codex/`, `.gemini/`, `.windsurf/`, `.agents/` and their siblings belong to one product's configuration. The work is platform-agnostic, and a full checkout buried under one product's folder is lost when the repository moves. `git check-ignore` passes on these paths, so the ignore gate alone does not catch this; the vendor-directory rule is a separate check.

A real instance: a worktree at `.claude/worktrees/guide-foundations-ml` sat inside a vendor directory and held 1,267 lines of uncommitted work. When the repository was later moved, every worktree pointer broke and that work became unreachable through git until the pointers were repaired.

Never create a worktree inside a path that is tracked by git. The central root is outside every repository, so this cannot happen by following Step 1a.

### Migration, handoff and cleanup

An existing worktree outside the root moves only through `nexus-hub worktree migrate`, which executes one reviewed manifest and preserves dirty, staged, untracked and ignored content. Move active work only after its agent checkpoints and acknowledges the handoff, and finish a signed run where its record is bound before moving it. Removal of a finished worktree stays with `scripts/cleanup_merged.py`, which owns the merged-history checks; this skill never deletes one. The runbook is `docs/runbooks/worktree-organization.md`.

### Worktree hygiene

Run this at session start in a git repository and at the start and end of every plan run, so the user never has to hunt for leftover worktrees. The session-start hook prints `Worktrees: N outside <root>/<identity>, M prunable` when this repository needs it.

1. **Check.** `nexus-hub worktree list --repo . --json`. Every linked worktree with `in_policy: false` is misplaced; `prunable: true` means its folder is gone.
2. **Move.** For misplaced idle worktrees, run the audit, then `nexus-hub worktree migrate --dry-run` to write one manifest, and ask the user for a single approval of the reviewed set. The user runs `--approve` in their own terminal and each owner runs `--ack` after checkpointing. Never synthesize either; the guard refuses an agent's `--approve`. Then `--apply`, and verify every receipt.
3. **Retire.** `python ~/.nexus-hub/scripts/cleanup_merged.py --dry-run --integration-branch <branch>`, then `--apply` only under an approval. A `KEEP` line is never overridden by hand.
4. **Report.** List what remains and why (uncommitted changes, live signed run, lock, another repository), each with its owner and next step.
5. **Other repositories and machines.** `nexus-hub worktree audit --machine --json --output <new-report> --max-seconds <n>`, resumed with `--resume`, then one manifest per repository.

## Step 3: Auto-Detect and Run Project Setup

A fresh worktree shares the repository's history but not its untracked working state (installed dependencies, local env files, build artifacts). Detect the project type and run setup so the worktree is actually usable:

- Node: if `package.json` exists, run the install for the detected manager (`npm ci` / `pnpm install` / `yarn`).
- Python: if `pyproject.toml` or `requirements.txt` exists, create/sync the environment (`pip install -e .` / `uv sync` / `poetry install`).
- Go: `go mod download`.
- Copy or recreate local-only files the repo expects but does not track (for example `.env` from `.env.example`), without copying secrets you should not duplicate.

Run only the setup the project actually needs; do not install toolchains the repo does not use.

## Step 4: Verify a Clean Test Baseline Before Reporting Ready

Do not announce the worktree is ready until you have confirmed it builds and its existing tests pass in this fresh workspace. A worktree that fails the baseline on the first run is broken setup, not a code problem, and you want to know that before you start changing things.

Run the project's test (and, if fast, build) command in the new worktree and confirm a clean baseline. This dovetails with `[[verification-before-completion]]`: "the worktree is ready" is a completion claim and needs evidence. Only after a green baseline do you report the workspace ready and begin the feature work.

## Quick Reference

| Goal | Command |
|---|---|
| Confirm inside a repo | `git rev-parse --is-inside-work-tree` |
| Submodule guard | `git rev-parse --show-superproject-working-tree` (non-empty means submodule) |
| Detect existing worktree | compare `git rev-parse --git-dir` with `git rev-parse --git-common-dir` (differ = already isolated) |
| List worktrees | `git worktree list` |
| Verify a path is ignored | `git check-ignore -q <path>` (exit 0 = ignored = safe for in-repo placement) |
| Resolve the destination | `nexus-hub worktree path --repo <checkout> --name <name> --json` |
| Create a worktree | `nexus-hub worktree create --repo <checkout> --branch <branch> --base <commit> --name <name>` |
| Remove a worktree | `git worktree remove <path>` |
| Prune stale worktree metadata | `git worktree prune` |

## Common Mistakes

- **Creating a worktree from inside a worktree.** Skipping Step 0 nests isolation and confuses every later `git worktree` command. Always run the git-dir vs git-common-dir check first.
- **Placing the worktree outside the central root.** Sibling, in-repo, vendor and temporary folders are what make worktrees impossible to find or move. Use `nexus-hub worktree create`.
- **Reusing the main checkout's installed dependencies.** A worktree does not inherit `node_modules` or a virtualenv. Run setup (Step 3) or the first command fails for the wrong reason.
- **Reporting "ready" without a baseline run.** If you skip Step 4 and the baseline was already red, you will misattribute pre-existing failures to your own change.
- **Leaving stale worktrees behind.** After finishing, remove the worktree (`git worktree remove`) so the repo does not accumulate orphaned workspaces.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just work on the main checkout, it's faster." | Working on main mixes your in-progress change with the releasable state, so a mid-task interruption (a hotfix, a review) forces a messy stash. A worktree keeps main clean and switchable at zero cost. |
| "raw git worktree add with a path I like is simpler." | Simpler to type, but it scatters worktrees across sibling and vendor folders and the guard refuses it. `nexus-hub worktree path` gives the destination in one command. |
| "I'll use EnterWorktree with a name, it is the native tool." | It creates under `.claude/worktrees/`, a vendor directory the policy forbids. Create with the helper and enter by `path`. |
| "Setup can wait until the first test fails." | Then your first test fails for a setup reason and you debug the wrong thing. Run Step 3 up front so the first real failure is about your code. |
| "The baseline obviously passes, I'll skip Step 4." | A fresh worktree has fresh untracked state; "obviously" is exactly when broken setup hides. A 30-second baseline run tells you whether red means you or means the environment. |

## Red Flags (stop and reconsider)

- You are about to run `git worktree add` with a destination that did not come from `nexus-hub worktree path`.
- You are about to call `EnterWorktree` with `name`, which creates under `.claude/worktrees/`.
- Step 0 reported you are **already in a worktree or a submodule**, but you are continuing to create another one anyway.
- You are about to report the workspace **ready** without having run the test baseline in the new worktree.

## Verification

- [ ] Step 0 ran: confirmed inside a git repo, ran the submodule guard, and compared git-dir against git-common-dir to detect existing isolation.
- [ ] The worktree was created with `nexus-hub worktree create`, or with a raw command whose destination came from `nexus-hub worktree path`.
- [ ] `git worktree list` shows the new worktree at the expected location.
- [ ] Project setup ran in the new worktree (dependencies installed, required local files present).
- [ ] The existing test suite was run in the new worktree and the baseline is clean before any feature work began.
- [ ] No worktree was created from inside an existing worktree or a submodule.
- [ ] The worktree is NOT inside a vendor or tool directory (`.claude/`, `.cursor/`, `.vscode/`, `.idea/`, `.codex/`, `.gemini/`, `.windsurf/`, `.agents/`), regardless of git-ignore status.
- [ ] The worktree path is `<root>/<repository-identity>/<worktree-name>` as `nexus-hub worktree list --repo <checkout>` reports (`in_policy` true).

## Related Skills

- [[incremental-implementation]] -- once isolated, implement the plan one tested step at a time inside the worktree.
- [[verification-before-completion]] -- "the worktree is ready" and "the feature works" are both completion claims that need a fresh proving run.
- [[shipping-and-launch]] -- worktree-aware finishing: merge or clean up the worktree as part of shipping the branch.
- [[multi-agent-coordinator]] -- when several agents work in parallel, each gets its own worktree so their changes never collide.
- [[competitive-generation]] -- runs parallel attempts that each benefit from an isolated worktree.
