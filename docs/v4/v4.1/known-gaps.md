# Known Gaps - v4.1

**Project**: Nexus-Hub
**Status**: in progress
**Last updated**: 2026-08-25

## v4.1.0 - pi-and-grill-me adoption

Seeded from `docs/v4/v4.1/comparisons/v4.1.0-comparison-pi-and-grill-me.md`.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-1 - Extension dependencies are still declared as caret ranges

- **Source**: comparison item A3 (supply-chain install hardening)
- **Reason**: the three extension manifests declare every devDependency as a caret range (`^5.3.0` and similar). Pinning them to exact versions was part of A3's intent, and it was deliberately NOT done in this pass because it is a change to what a fresh resolve installs, and verifying it means rebuilding and re-testing all three extensions against the pinned set. Shipping an unverified pin is how a build breaks for a reason unrelated to the change that caused it. The immediate risk is already lower than it looks: `package-lock.json` exists for all three, and CI installs with `npm ci`, which resolves from the lock rather than from the ranges. The new `.npmrc` (`save-exact=true`) also means every dependency added from now on is recorded exactly, so the range surface shrinks rather than grows.
- **Suggested next step**: pin each manifest to the version its lockfile already resolves, one extension at a time, running that extension's build and Vitest suite before moving to the next.

##### DF-2 - Extension build workflows still install with lifecycle scripts enabled

- **Source**: comparison item A3
- **Reason**: the three build workflows run plain `npm ci`, not `npm ci --ignore-scripts`. Adding the flag was part of A3 and was held back for a specific reason rather than a general one: `ttf2woff2` is a native module in two of the three manifests, and native modules commonly depend on an install-time build step. Disabling lifecycle scripts could therefore break icon generation in a way that only surfaces in CI. The new `npm-audit.yml` DOES use `--ignore-scripts`, safely, because it installs only to read the dependency tree and never builds.
- **Suggested next step**: run each extension's full build locally with `npm ci --ignore-scripts` and confirm the VSIX is byte-comparable. Where a native module genuinely needs its install step, add an explicit lifecycle-script allowlist (the pattern Pi uses) rather than dropping the flag for the whole tree.

##### DF-3 - `/plan` Step 4.5 stalls an unattended run by design

- **Source**: comparison item A5; recorded as a consequence, not a defect
- **Reason**: both gate stages run automatically, and stage 2 (the grill) waits for user answers. A plan generated while nobody is at the keyboard therefore stops at the gate. This is the configuration the user chose over the offered alternative (automatic critique, offered grill), with the trade-off stated at the time. Stage 1's findings are complete and on record before the pause, so nothing is lost except elapsed time.
- **Suggested next step**: none unless the stall proves annoying in practice. If it does, the smaller change is to make stage 2 offer-with-seeded-round-visible rather than to remove the gate; the decision record documents that alternative so it does not need re-deriving.

#### Bugs / Regressions

##### BG-1 - `git-guardrails` blocked documentation naming a destructive command (RESOLVED)

Found by being blocked while writing this version's own comparison report. Heredoc bodies are now separated from the blocking scan in both siblings, with a stderr note preserving the signal. Regression tests cover four heredoc opener forms plus the resume-after-close case.

##### BG-2 - `git-guardrails.sh` mis-decoded multi-line commands without `jq` (RESOLVED)

The grep/sed fallback left JSON `\n` escapes literal, so a multi-line command arrived as one line and every line-oriented check saw the wrong input. The fallback now un-escapes. The `.ps1` sibling was never affected because `ConvertFrom-Json` decodes escapes, which is why the regression test is parametrized over both.

#### Missing Tests / Coverage Gaps

##### MT-1 - No end-to-end install test for the Pi surfaces

- **Source**: comparison item A1
- **Reason**: `PiIntegration` is registered and covered by the registry-wide tests (roster, levers classification, defaults sync, contract freshness), but no test performs an install into a temporary `~/.pi` and asserts that `skills/` and `prompts/` are populated and that a non-existent `~/.pi` yields a skip rather than a write. The detection-gating path in particular is asserted only by reading the code.
- **Suggested next step**: add a case to the installer smoke suite mirroring the existing Qwen detection-gated coverage, including the negative case (no `~/.pi` -> `mark_not_detected`, no files written).

### Resolved Items

BG-1 and BG-2 above, both fixed in this version with regression tests.
