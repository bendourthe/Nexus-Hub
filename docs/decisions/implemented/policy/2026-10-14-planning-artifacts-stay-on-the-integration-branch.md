# Decision: Planning artifacts stay on the integration branch

Status: implemented - unreleased. `/compare` and `/plan` create no branch; their artifacts are committed on the integration branch and published the same day, through a short-lived `publish/<slug>` pull request where that branch requires one. A version branch is created only when `/implement` starts that plan.

## Problem

`/plan` and `/compare` said nothing about where their output is committed or how it reaches the integration branch. Agents filled the gap by creating a branch per artifact (`docs/v4.18.4-plan`, `docs/v4.16.3-comparison`, and others). On 2026-10-14 an audit found a dozen stale local branches and one finished plan, the v4.16.3 comparison and adoption plan, that existed only on a local branch in another session's scratch worktree. It never reached `develop` and was invisible to every other session and platform until the audit.

## Decision

Branches exist for implementation, not for planning. Comparisons, plans, and their tracker entries are committed on the integration branch and published the same day. Because `develop` requires a pull request (with admins included), publication pushes the commit to a remote-only `publish/<slug>` branch, opens a pull request, merges it when green with `--delete-branch`, and fast-forwards local `develop`. Every merged work branch is then deleted locally and remotely.

The procedure lives in Step 4d of `catalog/skills/workflow/git-branching-workflow/SKILL.md`. `/plan`, `/compare`, `implementation-plan`, and `cross-project-comparison` reference it without restating it.

Reopening trigger: `develop` stops requiring pull requests (direct push then replaces the publish branch), or a platform's tooling cannot open pull requests.

## Alternatives considered

**Keep plans local until `/implement`.** Rejected. The plan would travel with its version branch, but it stays invisible on the remote until implementation starts, which is the exact failure that stranded the v4.16.3 plan.

**Allow direct pushes to `develop` for plan files.** Rejected. It loosens branch protection for the whole branch, since protection cannot be scoped to a path, and the post-merge workflow filters assume every `develop` push is a reviewed merge.

**A per-plan `docs/vX.Y.Z-plan` branch, merged by pull request.** Rejected. This was the de facto practice, and its branches outlived their merges and accumulated; a version-named branch also suggests implementation has started.

## Consequences

- Planning work is visible on `develop` the day it is written, and nothing version-named exists before `/implement`.
- Each publication costs one pull request and one CI run on the integration branch.
- The `publish/<slug>` branch exists only remotely and only until merge.
