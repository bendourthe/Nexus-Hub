---
name: git-branching-workflow
description: Follow a project's declared branching model when creating branches, committing, merging, and releasing. Make sure to use this skill whenever the user or task involves "create a branch", "which branch should I use", "feature branch", "branch off develop", "merge to develop", "merge to main", "cut a release", "protected branch", "develop vs main", "git flow", "github flow", "trunk-based", or you are about to commit/merge work and need to confirm the correct branch and flow first. The skill is CONFIG-DRIVEN -- it reads the project's declared branching strategy and follows THAT, rather than imposing one. SKIP, do NOT use for: writing the commit message itself (use code-commit-workflow), resolving merge conflicts (use conflict-analyzer), or bumping version numbers across files (use version-upgrade).
summary_l0: "Follow a project's declared branching model for branches, merges, and releases"
overview_l1: "This skill keeps branch, merge, and release actions aligned with the project's DECLARED branching model instead of imposing a fixed one. It first resolves the model (reading an explicit declaration in AGENTS.md / CLAUDE.md / a config file, else inferring from repo state, else defaulting to GitHub Flow), then applies the matching discipline: which branch is protected (release-only), which is the integration target, how feature branches are named and based, when to merge and with what merge style, and how a release is cut and tagged. It supports develop+main, GitHub Flow, trunk-based, and git-flow. The core invariant across every model is: never commit feature or version work directly to the protected/release branch -- branch off the integration branch, and integrate through it. Use whenever creating a branch, deciding where work goes, merging a finished unit, or cutting a release. Trigger phrases: which branch, create a feature branch, branch off develop, merge to develop, merge to main, cut a release, protected branch, develop vs main, git flow, github flow, trunk-based."
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

### Step 3: Never commit protected-branch work directly

The cross-model invariant: do not commit feature or version work directly to the protected branch. Branch off the integration branch first:

```
git checkout <integration-branch>
git pull        # if a remote exists
git checkout -b feat/<slug>      # or fix/<slug>
```

Use `feat/<slug>` for features, `fix/<slug>` for fixes; keep `<slug>` short, lowercase, hyphenated, and aligned with any plan/spec slug (e.g. `feat/adoption-claude-red`). For GitHub Flow and trunk-based, the integration branch IS the default branch -- you still branch off it rather than committing to it directly (trunk-based keeps the branch very short-lived).

### Step 4: Work, validate, then integrate

1. Do the work on the feature branch; commit there (use [[code-commit-workflow]] for messages).
2. Run the project's validation/tests before integrating.
3. Merge the finished unit into the integration branch. Prefer `--no-ff` so each unit stays a revertable group in history:

    ```
    git checkout <integration-branch>
    git merge --no-ff feat/<slug>
    ```

4. If the integration branch advanced while you worked (e.g. a shared prerequisite landed), bring it into your branch first (`git merge <integration-branch>` or rebase) and re-validate before merging up.

### Step 5: Cut a release

For models with a protected branch (develop+main, git-flow), a release is the only time the protected branch is touched:

```
git checkout <protected-branch>
git merge --no-ff <integration-branch>
git tag vX.Y.Z          # bump version surfaces first (see version-upgrade)
git push origin <protected-branch> --follow-tags
```

For GitHub Flow / trunk-based, "release" is tagging the default branch at a chosen commit; there is no separate merge step. Bump version-carrying files before tagging.

### Step 6: Surface the rule cross-platform

This discipline is advisory on platforms without enforcement hooks. When working on a project that declares a protected branch, restate the rule at the start of branch/commit work so it survives context drift, and (on hook-capable platforms) rely on a protected-branch guard as the backstop. The guidance reaches every platform through the skill index; the hard stop only exists where hooks run.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It is a tiny change, I will just commit to main." | The protected branch is the release surface; a direct commit bypasses integration, skips the gate, and (for catalogs/libraries consumed from the branch) can ship a half-applied change to downstream users. Branch off the integration branch even for one-liners. |
| "I do not know the model, so I will assume develop+main." | Assuming the wrong model is as harmful as having none -- you might create a `develop` branch a trunk-based project does not want, or block a legitimate commit. Resolve the model from Step 1 first and state it. |
| "I will commit on the feature branch and push it straight to main to save a step." | That defeats the integration branch. Merge into the integration target; the protected branch only receives release merges. |
| "Fast-forward merges are cleaner, I will skip --no-ff." | Fast-forward erases the boundary of the unit you merged, making it hard to revert one feature without others. `--no-ff` keeps each unit atomic in history. |
| "There is no hook on this platform, so the rule does not apply here." | The rule is the project's, not the platform's. Hooks only add a backstop where they run; on Cursor/OpenCode/Copilot the discipline is yours to keep. |

## Verification

- [ ] The resolved branching model is stated explicitly, with how it was determined (declaration / inference / default).
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
