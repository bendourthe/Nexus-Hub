# Nexus-Hub Workflow Baseline Audit (v4.0.0 Phase 1)

**Project**: Nexus-Hub
**Status**: baseline, measured 2026-08-25 against `.github/workflows/*.yml` at `develop`
**Measured against**: [`ci-cd-lifecycle-contract.md`](ci-cd-lifecycle-contract.md)
**Plan**: [`docs/releases/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md`](../plans/v4.0.0-cost-effective-ci-cd.md)

Nine workflow files, seventeen jobs. This is the evidence baseline for Phase 7. Two findings from the original plan text are already CLOSED by work that shipped between v3.16 and v3.21; they are recorded as closed rather than silently dropped, because a plan that lists a fixed problem as open teaches the next reader to distrust the plan.

## 1. Event topology, by workflow

| Workflow | `push` | `pull_request` | `schedule` | `workflow_dispatch` | Belongs to |
|---|---|---|---|---|---|
| `ci.yml` | `main`, `develop`, `v*` tags | `main`, `develop` | no | yes | pull-request validation |
| `doc-colocation.yml` | `main`, `develop` | `main`, `develop` | no | no | pull-request validation |
| `presentify-extractor.yml` | `main`, `develop` | `main`, `develop` | weekly Mon 04:17 | no | mixed (verify = PR; render = post-merge + schedule) |
| `code-search.yml` | `main`, `develop` (path-scoped) | same paths | no | no | pull-request validation |
| `nexus-memory.yml` | `main`, `develop` (path-scoped) | same paths | no | yes | pull-request validation |
| `claude-usage-monitor.yml` | `main`, `develop` (path-scoped) | same paths | no | no | pull-request validation |
| `codex-usage-monitor.yml` | `main`, `develop` (path-scoped) | same paths | no | no | pull-request validation |
| `cursor-usage-monitor.yml` | `main`, `develop` (path-scoped) | same paths | no | no | pull-request validation |
| `codeql.yml` | `main` only (path-scoped) | none | weekly Sun 00:00 | yes | post-merge + schedule |

### Finding W1 (open, HIGH): every validation workflow duplicates itself after merge

Eight of the nine workflows fire on BOTH `pull_request` into a protected branch AND `push` to that same protected branch. Under develop-plus-main with a pull-request-only merge policy, the push event is the merge commit of the pull request that just ran. The tree is identical, so the second run is a complete re-billing of the first.

For `ci.yml` the duplication is worse than one-for-one, because the push leg is where the expensive matrix legs are enabled. `bootstrap` adds the macOS leg (roughly ten times the Linux minute rate), `bootstrap-windows` and `tests-windows` run only on push (roughly twice the rate), and `install-smoke` expands to three operating systems. So the merge run is materially MORE expensive than the pull-request run that already proved the same tree.

Contract 4 forbids it: a suite that already proved the merge result must not run again on the merge commit.

### Finding W2 (open, HIGH): expensive platform proof happens after merge, not before

The cost gating in `ci.yml` is inverted relative to the contract. Three jobs are explicitly `github.event_name != 'pull_request'`:

- `bootstrap-windows` (the only place the real `irm | iex` Windows standalone flow runs end to end)
- `tests-windows` (the only Windows PowerShell 5.1 leg, which exists because a BOM defect there does not reproduce under PowerShell 7)
- the macOS leg of `bootstrap`, and the macOS and Windows legs of `install-smoke`

That means Windows 5.1 and macOS compatibility are proven only AFTER the change is merged into a shared branch. Contract 4 requires the reverse: full supported-platform validation belongs to the pull-request gate, and the post-merge event is where nothing expensive runs. The current shape is not cheaper overall; it is the same minutes spent at the moment they can no longer prevent a bad merge.

`installer-smoke` is the one job that already gets this right: its matrix expands on `pull_request`, `workflow_dispatch`, and tags, and contracts to Ubuntu on push.

### Finding W3 (open, MEDIUM): no release-scoped workflow

`ci.yml` accepts `tags: ['v*']` and runs the entire validation suite on a release tag. There is no packaging, provenance, or publication step keyed to a tag, and no `release` profile to call. Contract 4 assigns tags their own event class.

### Finding W4 (open, MEDIUM): no post-merge workflow

There is no file whose purpose is protected-branch post-merge work. The behavior exists only as a side effect of W1. `presentify-extractor.yml`'s `render` job is the sole genuine post-merge worker, and it is embedded in a workflow that also carries a pull-request `verify` job.

### Finding W5 (open, LOW): `codeql.yml` has no workflow-level `permissions`

Its single `analyze` job sets `security-events: write` at job scope, so the effective permission is bounded. Contract 10 still requires an explicit workflow-level default so an added job cannot inherit the repository default silently.

### Finding W6 (open, LOW): `codeql.yml` provides no pre-merge analysis

It triggers on `push` to `main` only, so a pull request into `develop` gets no CodeQL signal and the analysis lands two merges after the code did. Contract 4 places static analysis on the integration pull request, with the schedule kept for advisory drift.

## 2. Duplicated repository commands

`ci.yml`'s `validate` job re-declares, as thirty-one separate `run:` steps, the same validator sequence the `Makefile`'s `validate` target already owns. The two lists have drifted before: `validate_no_personal_paths.py` was silently dropped from CI for a period because a duplicate `run:` key in one step overwrote the other (repaired in v3.14.5 Phase 7).

Contract 3 requires the definitive list to live in the repository and the workflow to call it. This is the single largest source of the "green locally, red in CI" and "green in CI, broken locally" classes in this repository's history.

| Workflow surface | Duplicates | Contract remedy |
|---|---|---|
| `ci.yml` `validate` (31 steps) | `make validate` | call `python scripts/ci/run.py --profile full` |
| `ci.yml` `shellcheck` (3 steps) | `make lint` plus a PowerShell AST pass | fold into a profile group |
| `ci.yml` `tests` (17 steps) | `make test` | fold into a profile group |
| `ci.yml` `tests-windows` (7 steps) | a Windows subset with no local equivalent | becomes the `platform` profile's Windows leg |

## 3. Runner and cost inventory

| Job | Runner class | Trigger scope today | Relative minute cost |
|---|---|---|---|
| `changes` | ubuntu | every event | 1x, under 1 minute |
| `validate` | ubuntu | every event | 1x |
| `shellcheck` | ubuntu | every event | 1x |
| `bootstrap` | ubuntu (+ macOS on push) | PR and push | 1x, plus 10x on push |
| `bootstrap-windows` | windows | push only | 2x |
| `tests` | ubuntu | PR and push | 1x |
| `tests-windows` | windows | push only | 2x |
| `install-smoke` | ubuntu (+ macOS, windows on push) | PR and push | 1x, plus 10x and 2x on push |
| `installer-smoke` | ubuntu (+ macOS, windows on PR, dispatch, tags) | PR and push | 1x, plus 10x and 2x on PR |
| `ci-required` | ubuntu | always | 1x, under 1 minute |
| 7 extension jobs | ubuntu | path-scoped PR and push | 1x each |
| `codeql` `analyze` | ubuntu | push to main, weekly | 1x, slow |

The multipliers above are the standard hosted-runner price ratios, not fixed constants. `docs/` records the lesson from the v3.18.1 usage monitor: derive weights from the live per-unit price rather than hardcoding them.

## 4. Findings CLOSED before this plan started

These appear in the plan body as open problems. They are not. Recording them as closed here prevents Phase 7 from "fixing" something that already works.

| Plan text | Actual state | Closed by |
|---|---|---|
| "the floating `actions/setup-node@v4` references" | CLOSED. Every `uses:` across all nine workflows is a full 40-character commit SHA with a readable version comment. A grep for a non-SHA `uses:` returns nothing. | pre-v4.0.0 hardening |
| "the risk that top-level path filtering can leave a required check unresolved" | CLOSED. `ci.yml` triggers are deliberately unfiltered; scoping lives in the `changes` job and is applied as job-level `if:`. `scripts/check_required_check_coverage.py` enforces it in `make validate` and CI. | v3.17.6 Phase 1 and 2 |
| "the push-only Windows PowerShell 5.1 and macOS gaps" | OPEN, and confirmed. See W2. | not closed |

## 5. Security and hygiene baseline

| Control | State |
|---|---|
| Immutable action references | PASS. All `uses:` are SHA-pinned with a version comment. |
| Least-privilege `permissions:` | PASS except `codeql.yml` (see W5). Eight of nine declare `contents: read` at workflow scope. |
| Concurrency with cancel-in-progress | PASS. Every workflow declares a group keyed on workflow plus ref. |
| Dependency caching | PARTIAL. `validate`, `tests`, and `tests-windows` cache pip keyed to a manifest. The bootstrap and smoke jobs do not, which is correct: they deliberately test a cold install. |
| Untrusted-fork exposure | PASS. No `pull_request_target`, no self-hosted runners, no secret consumption in any validation workflow. |
| Artifact retention | NOT APPLICABLE TODAY. No workflow uploads an artifact, which is the flip side of finding W7. |

### Finding W7 (open, MEDIUM): no structured reports anywhere

No workflow writes to `$GITHUB_STEP_SUMMARY`, uploads an artifact, or produces JUnit, coverage, or SARIF output (CodeQL's SARIF goes to the security tab, not to a run artifact). Every result is read by scrolling a log. Contract 6 requires a concise summary plus machine-readable evidence from the same execution a developer can reproduce locally.

## 6. Required-check suitability

`docs/policy/required-checks.json` declares the required set, and `tests/validators/test_ci_required_gate.py` asserts that `ci-required`'s `needs` covers every other job in `ci.yml` and that each needed job has a matching result variable.

`ci-required` conforms to contract 5 in full: `if: always()`, an allowlist verdict (`success` or `skipped` pass, everything else fails), pure-bash evaluation with no `jq` or `python3` dependency, a vacuous-pass guard, and `changes` included so a broken detector is loud.

Two workflows outside `ci.yml` contribute required contexts (`colocation`, `verify`). Both have unfiltered-enough triggers to resolve on any pull request into a protected branch. Phase 7 must not narrow either without moving its context behind an aggregate.

## 7. Phase 7 work list, derived

| Finding | Severity | Phase 7 sub-task |
|---|---|---|
| W1 duplicate post-merge suite | HIGH | 7.1: `ci.yml` drops the protected-branch `push` trigger; `post-merge.yml` takes the merge event |
| W2 platform proof after merge | HIGH | 7.1: invert the matrix gating so full platform coverage runs on the integration pull request |
| W3 no release workflow | MEDIUM | 7.1: `release.yml` on tags and dispatch, calling the `release` profile |
| W4 no post-merge workflow | MEDIUM | 7.1: `post-merge.yml` |
| W5 missing workflow permissions | LOW | 7.3 |
| W6 no pre-merge CodeQL | LOW | 7.2 |
| W7 no structured reports | MEDIUM | 7.3, over the Phase 6 reporting engine |
| Duplicated command lists | HIGH | 7.1, over the Phase 6 profile engine |
