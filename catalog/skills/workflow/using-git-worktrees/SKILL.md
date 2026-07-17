---
name: using-git-worktrees
description: "Use when starting isolated feature work, beginning a new branch, or before executing an implementation plan that will modify files, so the work happens in a clean separate workspace instead of the main checkout. Trigger phrases: start a worktree, work in isolation, new feature branch, spin up a workspace, isolate this change, before I start implementing, set up an isolated environment. SKIP for quick in-place edits, read-only exploration, or when you are already inside an isolated worktree or a disposable sandbox."
summary_l0: "Set up isolated worktree workspaces safely, preferring the native tool over raw git"
overview_l1: "This skill ensures substantial feature work happens in an isolated worktree rather than the shared main checkout, using a safe, ordered procedure. Step 0 detects whether you are already isolated (comparing the git-dir against the git-common-dir, with a submodule guard) so you never nest a worktree. Step 1 prefers the harness's native worktree tool (EnterWorktree / a worktree command) and falls back to raw git worktree add only when no native tool exists, choosing the directory by a safe priority order and running git check-ignore first so the new worktree is never created inside tracked or ignored project paths. Step 3 auto-detects and runs project setup (install dependencies, copy env files). Step 4 verifies a clean test baseline before reporting the workspace ready. It includes a quick-reference command table, common mistakes, red flags, and a binary verification checklist. Use it before executing any multi-file plan."
---

# Using Git Worktrees

Isolated work belongs in an isolated workspace. A git worktree gives a branch its own directory backed by the same repository, so feature work, experiments, and plan execution do not collide with the main checkout or with each other. This skill encodes the safe sequence for getting into a worktree: confirm you are not already isolated, prefer the harness's native worktree tool over raw git, verify the target path is safe before creating anything, set the project up, and confirm a clean baseline before declaring the workspace ready.

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

## Step 1: Create the Worktree (native tool first)

### Step 1a: Prefer the harness's native worktree tool

If the agent harness exposes a native worktree capability, use it instead of raw git. The native tool typically handles directory placement, cleanup of unchanged worktrees, and branch wiring for you, and it stays consistent with the rest of the harness's state tracking.

- In Claude Code, this is the `EnterWorktree` tool (or the `/worktree` affordance). Use it to enter an isolated worktree for the feature; let it choose and manage the location.
- Only if no native worktree tool is available do you fall back to Step 1b.

Using the native tool is not a stylistic preference: a raw `git worktree add` run alongside a harness that also manages worktrees can produce two sources of truth for where work lives. Prefer the one the harness knows about.

### Step 1b: Raw git fallback (only when no native tool exists)

When you must use raw git, choose the worktree directory by this priority order, and **verify the path is safe before creating it**:

1. A sibling directory outside the repository (preferred): `../<repo>-worktrees/<branch>`. This keeps worktrees entirely out of the project tree, so they can never be accidentally tracked or matched by project tooling.
2. A dedicated, git-ignored directory inside the repo only if a sibling location is not workable.

Mandatory safety check before creating an in-repo worktree: confirm the target path is git-ignored, so the worktree contents are never picked up as tracked files.

```bash
branch="feature/my-change"
target="../$(basename "$(git rev-parse --show-toplevel)")-worktrees/$branch"

# If you must place it inside the repo, the path MUST be ignored first:
# git check-ignore exits 0 only if the path is ignored.
# Example for an in-repo path:
#   inrepo=".worktrees/$branch"
#   if ! git check-ignore -q "$inrepo"; then
#     echo "Refusing: $inrepo is not git-ignored; it would be tracked. Add it to .gitignore or use a sibling path."
#     exit 1
#   fi

git worktree add -b "$branch" "$target"
```

Never create a worktree inside a path that is tracked by git. A worktree placed in a tracked directory pollutes `git status` in the main checkout and risks committing the entire nested checkout. The `git check-ignore -q` gate is the verification that prevents this; do not skip it for in-repo placements.

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
| Add a worktree (fallback) | `git worktree add -b <branch> <path>` |
| Remove a worktree | `git worktree remove <path>` |
| Prune stale worktree metadata | `git worktree prune` |

## Common Mistakes

- **Creating a worktree from inside a worktree.** Skipping Step 0 nests isolation and confuses every later `git worktree` command. Always run the git-dir vs git-common-dir check first.
- **Placing the worktree in a tracked directory.** This pollutes the main checkout's `git status` and risks committing a nested checkout. Use a sibling path, or gate in-repo placement behind `git check-ignore`.
- **Reusing the main checkout's installed dependencies.** A worktree does not inherit `node_modules` or a virtualenv. Run setup (Step 3) or the first command fails for the wrong reason.
- **Reporting "ready" without a baseline run.** If you skip Step 4 and the baseline was already red, you will misattribute pre-existing failures to your own change.
- **Leaving stale worktrees behind.** After finishing, remove the worktree (`git worktree remove`) so the repo does not accumulate orphaned workspaces.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just work on the main checkout, it's faster." | Working on main mixes your in-progress change with the releasable state, so a mid-task interruption (a hotfix, a review) forces a messy stash. A worktree keeps main clean and switchable at zero cost. |
| "raw git worktree add is simpler than the native tool." | Simpler to type, but it creates a second source of truth the harness does not know about. Prefer the native tool so worktree state stays consistent with everything else the harness tracks. |
| "I don't need the check-ignore step, the path looks fine." | "Looks fine" is how a worktree ends up in a tracked directory and pollutes the main checkout. The `git check-ignore -q` gate is one command and removes the guesswork. Run it. |
| "Setup can wait until the first test fails." | Then your first test fails for a setup reason and you debug the wrong thing. Run Step 3 up front so the first real failure is about your code. |
| "The baseline obviously passes, I'll skip Step 4." | A fresh worktree has fresh untracked state; "obviously" is exactly when broken setup hides. A 30-second baseline run tells you whether red means you or means the environment. |

## Red Flags (stop and reconsider)

- You are about to run `git worktree add` and a **native worktree tool exists** in the harness. Use the native tool instead.
- You are about to create a worktree **inside the repository** without having run `git check-ignore` on the target path.
- Step 0 reported you are **already in a worktree or a submodule**, but you are continuing to create another one anyway.
- You are about to report the workspace **ready** without having run the test baseline in the new worktree.

## Verification

- [ ] Step 0 ran: confirmed inside a git repo, ran the submodule guard, and compared git-dir against git-common-dir to detect existing isolation.
- [ ] A worktree was created with the native tool, OR the raw-git fallback was used only because no native tool exists.
- [ ] If an in-repo path was used, `git check-ignore -q` confirmed the path is ignored before creation; otherwise a sibling-of-repo path was used.
- [ ] `git worktree list` shows the new worktree at the expected location.
- [ ] Project setup ran in the new worktree (dependencies installed, required local files present).
- [ ] The existing test suite was run in the new worktree and the baseline is clean before any feature work began.
- [ ] No worktree was created from inside an existing worktree or a submodule.

## Related Skills

- [[incremental-implementation]] -- once isolated, implement the plan one tested step at a time inside the worktree.
- [[verification-before-completion]] -- "the worktree is ready" and "the feature works" are both completion claims that need a fresh proving run.
- [[shipping-and-launch]] -- worktree-aware finishing: merge or clean up the worktree as part of shipping the branch.
- [[multi-agent-coordinator]] -- when several agents work in parallel, each gets its own worktree so their changes never collide.
- [[competitive-generation]] -- runs parallel attempts that each benefit from an isolated worktree.
