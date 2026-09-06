# Decision: Use a lightweight `develop` + `main` branching model

Status: implemented - version work integrates on `develop` and reaches `main` only at release, cut as a `vX.Y.Z` tag

## Problem

Nexus-Hub is a catalog consumed directly from the repository by an installer, across every supported AI platform. Whatever sits on the default branch is what a user installs. A multi-phase version in progress on that branch means users install half-applied phases.

At the same time, the repository is maintained by a small team, so branching ceremony has a real ongoing cost and no coordination benefit to offset it.

## Decision

Two long-lived branches:

- **`main`** is the stable, installable branch. It receives merges only at release time, each cut as a `vX.Y.Z` tag. It stays the GitHub default so clones and installer runs get stable content. Version and phase work never lands here directly.
- **`develop`** is the integration branch. All version work lands here, either directly or via short-lived `feat/<slug>` and `fix/<slug>` branches merged back into it.

Releases run through `/update release`, which bumps every version-carrying surface, finalizes the changelog, merges `develop` into `main`, tags, pushes, and publishes the GitHub Release.

## Alternatives considered

- **Full Git Flow** with `release/*` and `hotfix/*` branches. Rejected: the ceremony exists to coordinate parallel release trains and scheduled hardening periods, neither of which this repository has. The cost is per-release and permanent; the benefit is zero at this team size.
- **GitHub Flow** (feature branches straight to `main`). Rejected on the installability argument above: it puts in-progress multi-phase work on the branch users install from.
- **Trunk-based with feature flags.** Rejected: flags are a runtime mechanism, and most of this catalog is Markdown that has no runtime in which to evaluate a flag.

## Consequences

- `main` is effectively a release artifact, so its history is a clean sequence of tagged releases rather than a development log.
- Downstream installer users are protected from partially-applied phases, which is the whole point.
- A release is a distinct operation rather than a side effect of merging, which is what makes `/update release` worth having as a single atomic flow.
- Branch protection on `develop` requires status checks that a docs-only change does not trigger, so plan-only pull requests can block indefinitely. This is a live cost of the model, not a hypothetical: it required an administrator override to merge such a pull request more than once.
