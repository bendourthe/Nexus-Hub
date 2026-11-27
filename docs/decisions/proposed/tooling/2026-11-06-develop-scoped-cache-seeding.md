# Decision: Seed dependency caches from develop after merge

Status: proposed - a push to develop writes the pip and Playwright caches that pull requests restore, under the lifecycle contract's minimal post-merge work.
Date: 2026-11-06
Author: Ben Dourthe
Template: Nygard

## Problem

`ci.yml` has no `push` trigger and `post-merge.yml` sets up Python without a cache, so no cache is ever written in the `develop` scope that every pull request can restore. `gh cache list` shows the same `setup-python` pip keys and the 270 MB `ms-playwright-chromium-Linux-1.63.0` entry saved again for each pull request, and each new pull request starts cold. From the 14 baseline runs in `v4.15.7-ci-latency-baseline.md`, setup is a small share of job time: the Chromium download is about 54 seconds per `guide-render` shard, a pip install about 20 seconds, and setup averages 0.5 to 1.6 minutes per job. The cost is real but small, and the maintainer decided on 2026-11-06 to keep the seeding because the saving repeats on every pull request.

## Proposal

Add one job to `.github/workflows/post-merge.yml` that runs only for a `push` to `develop`, holds `permissions: contents: read`, uses no secret, and runs no repository script or test. It checks out, runs `actions/setup-python` with the same `cache-dependency-path` inputs as the `guide-render` job, installs the same requirement files, and saves the Playwright browser cache under a key that includes the resolved Playwright version and a hash of `scripts/ci/requirements-py311.txt` and `scripts/ci/requirements-guide-render.in`. The `guide-render` job uses the identical key expression. Every action is pinned by commit SHA. The lifecycle contract names this work as merged-state work (section 4.1) and records the trust boundary: it relies on branch protection rejecting direct pushes to `develop`.

## Alternatives considered

- **No seeding.** Keeps `post-merge.yml` free of any cache logic and removes the trust-boundary dependency, but every pull request keeps paying the cold setup (about 1.5 minutes on the `guide-render` shards and about 0.5 minutes elsewhere) and re-saves a 270 MB entry per pull request. Rejected by the maintainer on 2026-11-06.
- **Dispatch-only seeding (`workflow_dispatch` or a schedule).** No dependence on branch protection, because a person or a timer starts it. Rejected: the cache would lag the merged lockfile until someone runs it, and a stale key gives no benefit exactly when a lockfile changes, which is when a pull request is most likely to need the new packages.
- **Seed from the pull-request workflow.** Not possible: a pull request writes only to its own merge-ref scope, which no other pull request can restore.
- **Seed on every push to `main` as well.** Rejected as unnecessary: pull requests target `develop`, and `main` receives only release merges.

## Acceptance criteria

- The seed job is guarded by `github.event_name == 'push' && github.ref == 'refs/heads/develop'`, declares only `contents: read`, and contains no `secrets.` reference, repository script or pytest call.
- The seed job and `guide-render` build the identical Playwright key and the identical `cache-dependency-path` list, asserted by `tests/workflows/test_ci_python_cache_contract.py`.
- A cache miss still installs normally and never fails a run.
- After the first merge to `develop`, `gh cache list` shows the seeded keys in the `refs/heads/develop` scope and a new pull request reports a cache hit in its `guide-render` setup step.

## Risks

- A key that omits an input that changes the cached content cannot be corrected by overwriting, because GitHub keeps the first saved value for a key. Mitigation: the key includes the tool version and the requirement-file hash.
- If branch protection on `develop` were removed, an unreviewed push could write a cache that later pull requests restore. Mitigation: the dependency is stated in the lifecycle contract and the settings runbook, and the cache holds downloaded packages and a browser, not repository code.
- One more job runs after each merge to `develop`, an estimated 3 minutes of Linux time (not yet measured), which does not block anything.
