# Session History - GitHub Usage Monitor Accuracy Phase 6: Refactor, Known-Gaps Reconciliation, and CI/CD

**Date**: 2026-08-22
**Branch**: `feat/v3.18.1-github-usage-monitor-accuracy`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.1-github-usage-monitor-accuracy.md`](../../plans/v3.18.1-github-usage-monitor-accuracy.md)
**Phase**: 6 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD (terminal phase)
**Environment**: Windows 11, Git Bash, Node 22 / `vitest` 4.1.10, Python 3.12, ShellCheck; GNU Make unavailable, so `make` targets were run as their constituent commands
**Outcome**: Extension at 0.4.0 with the behavior change announced leading the CHANGELOG entry. Every gate passes, the VSIX packages and verifies, gaps are reconciled with zero release blockers, and CI needed no change for a documented reason.

## 1. Starting State

- **Starting commit**: `0d132641` (Phase 5: policy document and decision record)
- **Extension version**: 0.3.3
- **Routing decision**: the plan recorded `frontier / max` on the grounds that this is the last point a cross-cutting inconsistency can be caught. Implementation ran on Opus 5. The compensating measure was breadth of checking rather than depth of reasoning: every gate in the validate target was run individually and its result recorded, rather than trusting an aggregate.

## 2. The Layout Pass Found Three Stale Assertions, Not Dead Code

The weight-table removal and the toast removal left less debris than expected, because both were removed with their callers in their own phases. What the grep sweep did find was **comments still describing the old behavior**, which is the more dangerous residue: dead code is inert, while a stale comment actively misinforms.

| Location | Was | Now |
|---|---|---|
| `src/types.ts` `drawdown` doc | "weighted per runner OS", drawdown "about 121" | "each weighted by its own list price relative to the standard Linux rate", "about 127" |
| `src/migration.ts` | Bare `"notificationTimeoutSeconds"` entry | Annotated: deprecated in 0.4.0, retained so a value set under the old extension id still migrates rather than resurfacing as an orphan |
| `README.md` (Phase 5) | "weighted per runner OS", cited the stale 1,584 | Derived weights, measured 1,724, three links |

Confirmed absent repo-wide: `OS_DRAWDOWN_WEIGHTS`, `usedWeighting`, `scheduleWarningDismissal`, and any test asserting a hardcoded weight table. The four monitors' warning paths remain in parity, enforced by `test/warning-parity.test.ts` rather than by inspection.

## 3. The Version Bump, and One Question the Plan Told Us To Ask Rather Than Assume

`package.json`, `package-lock.json` (both occurrences), and `GITHUB_USER_AGENT` in `src/providers/github.ts` all moved to 0.4.0. The user agent carries the version string, so leaving it behind would have made outbound requests misreport the client.

The plan asked whether `scripts/check_version_sync.py` governs extension versions. **It does not.** Its canonical version is `.claude-plugin/plugin.json` (3.18.0) and its surfaces are `data/marketplace.json`, both installers, `CHANGELOG.md`, `README.md`, and `AGENTS.md`. No extension is in its scope. Recording that explicitly, because "checked, does not apply" is a different answer from "assumed it did not" and the plan asked for the distinction.

Verified no other file pins 0.3.3.

## 4. The CHANGELOG Leads With the Consequence, Not the Cause

The Actions percentage will read **higher** for any account running Windows or macOS CI. A user calibrated against 0.3.3 who sees a jump with no explanation reports a correct number as a new bug, so the entry leads with the jump and states why in the same sentence, before describing the mechanism.

The **capability usage gate** applies: this release deprecates a setting. All five required elements are documented on that surface in the CHANGELOG's `Deprecated` section:

| Element | For `notificationTimeoutSeconds` |
|---|---|
| Activation | None - the change is unconditional in 0.4.0 |
| Validation | Cross a threshold twice in one session; the panel appears both times and stays |
| Disable / rollback | Pin 0.3.3; there is no per-setting opt-out, because the timer and the toast were coupled and re-enabling one alone reproduces a worse defect |
| Authority boundary | Changes no permission, grants no new scope, reads no additional GitHub data |
| Canonical link | `extensions/github-usage-monitor/README.md` |

No other opt-in surface, installer flag, managed skill, or host surface changed in this release.

## 5. CI Needed No Change, and That Is a Finding

`.github/workflows/github-usage-monitor.yml` runs `vitest run`, which discovers `test/*.test.ts` without enumeration, and its path filter `extensions/github-usage-monitor/**` already covers all four new test files. Verified rather than assumed.

The path filter is **safe** here, which is worth stating because a path-filtered workflow caused six administrator bypasses in v3.17.5. That failure mode requires the workflow's check to be **required**: GitHub leaves a check from an untriggered workflow Pending forever. This workflow's check is not in `docs/policy/required-checks.json`, and `check_required_check_coverage.py` passes, confirming all ten declared contexts across two branches are produced unconditionally. The filter therefore costs nothing but saves run time and noise on unrelated changes.

`.vscodeignore` needed no edit: it excludes `src/**` and `test/**` wholesale, so the new source and test files are covered by existing rules rather than needing new ones.

## 6. Verification

| Gate | Result |
|---|---|
| `make validate` (27 constituent commands, run individually) | All pass. 273 skills, 15 bundles, 13 decision records, 8 budgeted docs, permission baseline, installer parity, unicode, supply-chain, workflow security, required-check coverage, doc co-location, incident notes, registry entries, version sync, base-template parity, model-prompting profiles, platform contracts and freshness, platform defaults |
| `make lint` (ShellCheck) | Pass |
| `make test` (pytest hook suite) | Pass |
| `npm run compile` | Pass |
| `npm test` | 466 tests, 30 files |
| `npm run test:coverage` | Statements 83.31%, branches 79.95%, functions 83.87%, lines 86.08% |
| `npm run package` | `github-usage-monitor-0.4.0.vsix`, 67 files, 184.64 KB |
| `npm run verify:package` | Pass, 65 files verified |
| Built VSIX gitignored | Yes, via `extensions/github-usage-monitor/.gitignore:4` |
| `check_docs_retention.py` | 1 advisory (v3.16 history), recorded as MT-1 rather than acted on |

## 7. Known-Gaps Reconciliation

A `## v3.18.1 - github-usage-monitor-accuracy` section was appended to `docs/v3/v3.18/known-gaps.md` with its own numbering. Two items closed in implementation, four open and dispositioned:

- **NI-1 (open by design)**: price ratios and the legacy 2x / 10x cannot be separated by any saturated month. Disposition is the Phase 3 falsifier plus the ledger, not a promise to revisit.
- **NI-2 (open by design)**: the allowance is still plan-table-derived because no endpoint returns it. Scraping is recorded as a rejected alternative, not an open idea.
- **DF-1 (deferred)**: no scope-escalation prompt when a repository's visibility cannot be read. An authorization-flow change, declined under the Boundaries rule.
- **MT-1 (open, pre-existing)**: v3.16 development history due for archival. Unrelated to this plan; a 39-file move belongs in its own change with its own reference-repair pass, which is exactly the lesson the v3.18.0 archive pass recorded when a comparable move turned up 227 inbound references.

**Prior-version ingest**: v3.16 **NI-2** is marked **SUPERSEDED** in its own ledger with a pointer here, since the constants it described no longer exist. v3.16 **NI-4** (self-hosted and larger-runner exclusion rules tested against invented SKU strings only) stays open and is noted as mattering slightly more now, because an excluded runner that should have counted is a hole in a weighted figure rather than an unweighted one.

**Release blockers: 0.**

## 8. Hand-Off

The plan's terminal step routes release work to `/update release`, which owns the version bump across Nexus-Hub's own surfaces, the changelog finalization, the `develop` -> `main` merge, the tag, the push, and the GitHub Release publish. The extension-level bump to 0.4.0 and its `## [Unreleased]` CHANGELOG entry are done here because they are extension artifacts, not repository-version surfaces.
