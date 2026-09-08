---
name: git-branching-workflow
description: "Follow a project's declared branching model when creating branches, committing, merging, and releasing. Make sure to use this skill whenever the user or task involves \"create a branch\", \"which branch should I use\", \"feature branch\", \"branch off develop\", \"merge to develop\", \"merge to main\", \"cut a release\", \"protected branch\", \"develop vs main\", \"git flow\", \"github flow\", \"trunk-based\", or you are about to commit/merge work and need to confirm the correct branch and flow first. The skill is CONFIG-DRIVEN -- it reads the project's declared branching strategy and follows THAT, rather than imposing one. SKIP, do NOT use for: writing the commit message itself (use code-commit-workflow), resolving merge conflicts (use conflict-analyzer), or bumping version numbers across files (use version-upgrade)."
summary_l0: "Follow a project's declared branching model for branches, merges, and releases"
overview_l1: "This skill keeps branch, merge, and release actions aligned with the project's DECLARED branching model instead of imposing a fixed one. It first resolves the model (an explicit declaration in AGENTS.md / CLAUDE.md / a config file, else inferred from repo state, else GitHub Flow), then applies the matching discipline: which branch is protected (release-only), which is the integration target, how feature branches are named and based, when and how to merge, and how a release is cut and tagged. It supports develop+main, GitHub Flow, trunk-based, and git-flow. The core invariant across every model: never commit feature or version work directly to the protected branch -- branch off the integration branch and integrate through it. Use whenever creating a branch, deciding where work goes, merging a finished unit, or cutting a release."
---

# Git Branching Workflow

Keep every branch, commit, merge, and release action aligned with the project's *declared* branching model. This skill does not impose a single model; it discovers the one the project uses and enforces that model's discipline. The one invariant it enforces across all models: feature and version work never lands directly on the protected (release) branch.

## When to Use This Skill

Use this skill when:

- You are about to create a branch and need to know what to base it on and how to name it.
- You have finished a unit of work and need to know where and how to merge it.
- You are cutting a release and need the correct integration-to-release flow.
- The user asks "which branch?", "should I branch off develop or main?", "how do we release?", or names a model (develop+main, GitHub Flow, trunk-based, git-flow).
- You are an agent on any platform (Claude, Codex, Cursor, Gemini/Antigravity, OpenCode, Copilot) about to commit or merge, and you have not yet confirmed the project's branch discipline this session.

**When NOT to use this skill:**

- Writing the commit message text -> use [[code-commit-workflow]].
- Resolving a merge conflict -> use [[conflict-analyzer]].
- Bumping version numbers across files for a release -> use [[version-upgrade]].
- The repository has a single branch and no remote, and the task is a throwaway local experiment.

**Trigger phrases**: "which branch", "create a feature branch", "branch off develop", "merge to develop", "merge to main", "cut a release", "protected branch", "develop vs main", "git flow", "github flow", "trunk-based".

## Instructions

### Step 1: Resolve the declared branching model

Determine the model in this order; stop at the first that resolves:

1. **Explicit declaration.** Look for a "Branching" / "Branching and Release" / "Branching and Commits" section in `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, or a config file (e.g. `.nexus/branching.json`). Use what it states.
2. **Repo-state inference.** If no declaration:
    - A `develop` (or `dev`) branch exists alongside `main`/`master` -> treat as **develop+main**.
    - Only `main`/`master` plus short-lived branches, releases tagged on the default branch -> **GitHub Flow**.
    - Long-lived `release/*` branches present -> **git-flow**.
3. **Default.** If nothing resolves, assume **GitHub Flow** (simplest safe default) and state that assumption to the user.

Always state which model you resolved and how, before acting on it.

### Step 2: Identify the protected and integration branches

Per the resolved model:

| Model | Protected (release-only) | Integration target | Feature base |
|---|---|---|---|
| **develop + main** | `main` | `develop` | `develop` |
| **GitHub Flow** | `main`/`master` | `main`/`master` (always releasable) | the default branch |
| **trunk-based** | (none; trunk IS the working branch) | `main`/`master` | the trunk (short-lived branches, merge fast) |
| **git-flow** | `main`/`master` | `develop` | `develop` (features), `main` only via `release/*` and `hotfix/*` |

### Step 3: Bootstrap the integration branch when missing

When a project has **no declared model, no `develop` (or `dev`) branch, and is not deliberately trunk-based** - the greenfield / inherited-project case that `/setup` handles - bootstrap the develop+main model rather than leaving work stranded on a lone default branch:

1. **Confirm with the user first.** Creating a branch is a repo-shaping action; never bootstrap silently.
2. Create `develop` from the current default branch and adopt develop+main: `git checkout -b develop` (from `main`/`master`), then treat `main` as protected and `develop` as the integration target.
3. Record the adopted model where the project declares conventions (AGENTS.md / CLAUDE.md), so later sessions resolve it via Step 1 rather than re-inferring.

Do NOT bootstrap when the project has DECLARED trunk-based (a single-branch flow is a deliberate choice) or already has an integration branch. This is the create-if-missing path only; a project that resolved a model in Step 1 skips it.

### Step 4: Never commit protected-branch work directly

The cross-model invariant: do not commit feature or version work directly to the protected branch. Branch off the integration branch first:

```
git checkout <integration-branch>
git pull        # if a remote exists
git checkout -b feat/<slug>      # or fix/, refactor/, ci/, docs/, chore/, test/
```

Use `feat/<slug>` for features and `fix/<slug>` for fixes; the fuller work-branch prefix set is `refactor/`, `ci/`, `docs/`, `chore/`, and `test/` (matching the conventional-commit types), all branched off and integrated through the integration branch. Keep `<slug>` short, lowercase, hyphenated, and aligned with any plan/spec slug (e.g. `feat/adoption-claude-red`, `refactor/docs-layout`). For GitHub Flow and trunk-based, the integration branch IS the default branch -- you still branch off it rather than committing to it directly (trunk-based keeps the branch very short-lived).

### Step 4b: Publication timing for plan-driven work

Creating a branch and PUBLISHING it are separate decisions, and for multi-phase plan work they happen at different times.

- Create the feature branch from the integration branch at the start of the plan, as Step 4 describes.
- Keep phase commits LOCAL. A non-final phase commits and stops: no push, no pull request, no remote CI. A pipeline run per phase bills to validate work the plan itself calls incomplete, and a red check on incomplete work teaches the reader to ignore red checks.
- Push ONCE, in the plan's final phase, after the complete local gate and with explicit approval.
- Integrate only through a reviewed pull request against the INTEGRATION branch, never the protected release branch. That pull request is the plan's first remote validation, and it tests the merge result rather than the branch tip.

This applies to plan-driven work. A one-off fix on a short-lived branch is published whenever it is ready; the rule exists because a multi-phase plan multiplies the cost, not because pushing is bad. See `[[cicd-architect]]` for the pipeline half and `[[implement-phase]]` for the execution half.

### Step 4c: What a protected branch buys you

A push event carries no evidence that an update came from a reviewed merge. "This workflow runs on merges" is only true in a repository whose branch protection REJECTS direct pushes to that branch.

So the protected-branch settings are load-bearing for more than discipline: they are what makes a branch-filtered `push` workflow mean "a merge or a release happened". Configure them, verify them by hand, and never assume them. They cannot be set from a pipeline file, and Nexus-Hub deliberately does not mutate them on a user's repository.

Required, at minimum, on both the integration and the protected release branch:

- Direct pushes rejected.
- A pull request required before merge, with the aggregate status check required.
- Administrator bypass disabled where the project's risk tolerance allows.

### Step 5: Work, validate, then integrate

1. Do the work on the feature branch; commit there (use [[code-commit-workflow]] for messages).
2. Run the project's validation/tests before integrating.
3. Merge the finished unit into the integration branch. Prefer `--no-ff` so each unit stays a revertable group in history:

    ```
    git checkout <integration-branch>
    git merge --no-ff feat/<slug>
    ```

4. If the integration branch advanced while you worked (e.g. a shared prerequisite landed), bring it into your branch first (`git merge <integration-branch>` or rebase) and re-validate before merging up.

### Step 5b: Stage explicitly when sessions may share a worktree

More than one agent session can be running in the same working directory at once, each editing different files. Nothing in git makes that safe, because git operations act on the whole index and working tree rather than on the files one session happens to care about. A session that stages everything it finds will commit another session's half-finished work under its own message, and a session that discards uncommitted changes will destroy work it never saw.

Both failures are silent. The commit succeeds, the tree looks clean, and the damage surfaces later as a phase that "was already done" or a file that reverted for no reason.

Three rules prevent it, and the first is the one that matters:

1. **Stage explicit paths.** `git add <path> <path>` and never the whole-worktree forms (`git add -A`, `git add .`). This is the rule that holds even when the others are forgotten, because it is the only one that makes the blast radius equal to the intended change.
2. **Read `git status` before committing** and confirm every staged path is one this session actually touched. Treat an unexpected path as a stop signal, not as noise to commit past.
3. **Do not run a command that discards or rewrites shared state** on someone else's behalf: a hard reset, a whole-tree checkout or restore, a force-clean of untracked files, a stash, or a commit that skips hooks. Several of these are already blocked by the `git-guardrails` hook; the rule stands whether or not the hook is installed, because the hook is defense-in-depth and not a boundary.

This composes with the plan lifecycle rather than competing with it. A phase already commits only files tracing to that phase, and that rule says WHICH files belong in the commit. This one says HOW to stage them so the answer survives a second session running beside you. If a rebase conflict lands in a file this session did not modify, stop and ask rather than resolving it: the other session owns that file's intent.

Two exemptions, stated so they are not smuggled in silently. A generated file the project designates as always-shareable may accompany any commit; name it in the project's own rules rather than deciding case by case. And a genuinely single-session repository loses nothing by following these rules, so there is no "solo work" exemption worth writing down.

### Step 6: Cut a release

A release starts only after the integration branch is GREEN: the plan's integration pull request passed every required check and merged, and the post-merge work (if any) succeeded. Releasing from an unvalidated integration branch ships a tree nothing proved.

For models with a protected branch (develop+main, git-flow), a release is the only time the protected branch is touched:

```
git checkout <protected-branch>
git merge --no-ff <integration-branch>
git tag vX.Y.Z          # bump version surfaces first (see version-upgrade)
git push origin <protected-branch> --follow-tags
```

For GitHub Flow / trunk-based, "release" is tagging the default branch at a chosen commit; there is no separate merge step. Bump version-carrying files before tagging.

### Step 7: Surface the rule cross-platform

This discipline is advisory on platforms without enforcement hooks. When working on a project that declares a protected branch, restate the rule at the start of branch/commit work so it survives context drift, and (on hook-capable platforms) rely on a protected-branch guard as the backstop. The guidance reaches every platform through the skill index; the hard stop only exists where hooks run.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It is a tiny change, I will just commit to main." | The protected branch is the release surface; a direct commit bypasses integration, skips the gate, and (for catalogs/libraries consumed from the branch) can ship a half-applied change to downstream users. Branch off the integration branch even for one-liners. |
| "I do not know the model, so I will assume develop+main." | Resolve the model from Step 1 first and state it. You MAY *bootstrap* develop+main (Step 3) for an undeclared / greenfield / inherited project - that is the `/setup` path, and it requires user confirmation - but never auto-create `develop` in a project that has DECLARED trunk-based. Silently assuming the wrong model can block a legitimate commit or impose a branch a trunk-based project rejects. |
| "I will commit on the feature branch and push it straight to main to save a step." | That defeats the integration branch. Merge into the integration target; the protected branch only receives release merges. |
| "Fast-forward merges are cleaner, I will skip --no-ff." | Fast-forward erases the boundary of the unit you merged, making it hard to revert one feature without others. `--no-ff` keeps each unit atomic in history. |
| "I will push each phase so the branch is backed up remotely." | A remote branch is a backup; a remote PIPELINE RUN is a bill. If durability is the goal, push a branch that triggers no validation, or keep a local mirror. Pushing into a validation trigger to get a backup pays for a full run per phase to solve a problem that is not about CI. |
| "The workflow only runs on merges because it is filtered to develop." | Only if branch protection rejects direct pushes to develop. Without that setting the same filter fires on any developer push, and every post-merge assumption (the tree was reviewed, the gate was green) is false. The protection is what makes the filter mean what you think it means. |
| "There is no hook on this platform, so the rule does not apply here." | The rule is the project's, not the platform's. Hooks only add a backstop where they run; on Cursor/OpenCode/Copilot the discipline is yours to keep. |
| "I am the only session in this repo, so staging everything is fine." | You cannot see the other sessions from inside yours, and the cost of being wrong is committing or destroying work you never read. Explicit paths cost one line and remove the question. |
| "The unexpected staged file is probably mine from earlier." | Probably is not a basis for a commit. Check it or leave it out; a file committed under the wrong message is findable only by whoever goes looking for it later. |

## Verification

- [ ] Every commit staged explicit paths; no whole-worktree staging form was used, and `git status` was read before committing so no unexpected path was included.
- [ ] The resolved branching model is stated explicitly, with how it was determined (declaration / inference / default / bootstrap).
- [ ] If the integration branch was missing and the project is not trunk-based, `develop` was created (with user confirmation) and the adopted model recorded, so the integration branch now exists.
- [ ] No feature or version commit was made directly on the protected branch.
- [ ] The feature branch is based on the correct integration branch and named `feat/<slug>` or `fix/<slug>`.
- [ ] Project validation/tests ran green before any merge into the integration branch.
- [ ] Merges into the integration branch use `--no-ff` (or the project's documented merge style).
- [ ] A release touched the protected branch only via an integration-branch merge plus a version tag.

## Related Skills

- [[code-commit-workflow]] - writes the actual commit messages (conventional, atomic) once this skill has placed you on the right branch.
- [[conflict-analyzer]] - resolves merge conflicts that arise when integrating branches.
- [[version-upgrade]] - bumps version-carrying files before a release tag is cut.
- [[pre-commit-checklist]] - the pre-commit validation gate to run before integrating.
- [[cicd-architect]] - owns the pipeline half of the lifecycle this skill's publication timing serves.
