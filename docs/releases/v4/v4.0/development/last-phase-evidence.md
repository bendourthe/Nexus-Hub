# Last-Phase Evidence - v4.0.0 Docs Lifespan Tree and Enforcement

**Date**: 2026-08-27
**Plan**: [`v4.0.0-docs-lifespan-tree-and-enforcement.md`](../plans/v4.0.0-docs-lifespan-tree-and-enforcement.md)
**Phase**: 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD (final)
**Branch**: `feat/v4.0.0-docs-lifespan-tree-and-enforcement`

Each section quotes the proving command or scan. An empty finding is recorded with its output rather than asserted.

## Architecture refactor

**Empty directories** - four found under the tracked tree, all pruned. All were untracked (git does not track empty directories), confirmed by `git status --porcelain docs` reporting nothing after the prune:

```
pruned docs/releases/v3/v3.17/development/history
pruned docs/releases/v3/v3.18/development
pruned docs/releases/v3/v3.19/development
pruned docs/decisions/rejected/process
=== remaining empty dirs under docs/ ===
(end)
```

**Byte-identical duplicates** - six groups, all pre-existing and all intentional. Flagged, none merged, per the project-refactor rule that duplicates are surfaced rather than auto-resolved:

```
byte-identical duplicate groups: 6
  catalog/skills/code-review/code-quality/references/code-quality-checklist.md | catalog/skills/code-review/performance-review/references/code-quality-checklist.md
  extensions/claude-usage-monitor/LICENSE | extensions/codex-usage-monitor/LICENSE
  extensions/claude-usage-monitor/icons/warning.svg | extensions/codex-usage-monitor/icons/warning.svg
  extensions/claude-usage-monitor/src/updateWatcher.ts | extensions/codex-usage-monitor/src/updateWatcher.ts | extensions/cursor-usage-monitor/src/updateWatcher.ts
  extensions/claude-usage-monitor/tsconfig.json | extensions/codex-usage-monitor/tsconfig.json
  templates/ai-instructions/base-aider.md | templates/ai-instructions/base-kimi.md | templates/ai-instructions/base-openclaw.md | templates/ai-instructions/base-qwen.md | templates/ai-instructions/base-windsurf.md
```

Each group is a deliberate per-package copy (sibling VS Code extensions), a Tier-3 bundle that must be self-contained in both consuming skills, or the five guardrails-only templates whose content is identical by design.

**Orphans** - zero, across the 103 active-tree documents in the reference graph:

```
orphans: 0 | after allowlist: 0
```

**Structure complexity** - `docs/` holds 19 top-level entries, and only two of them (`releases/`, `archives/`) are version-bearing. The top level therefore does not grow with the release count, which is the property Phase 7.1 asks to confirm.

## Known-gaps reconciliation

Every `docs/**/known-gaps.md` was enumerated with its Status line. Exactly one is open:

```
docs/releases/v4/v4.0/known-gaps.md                  in-progress
```

All 28 others read `finalized` or carry a closed per-cycle summary; per the note already in the v4.0 file, an older file whose Status is not literally `finalized` is a historical record of its own cycle, not a live queue.

A marker scan over every file this branch changed (excluding frozen v0-v3 buckets) found no unrecorded `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` introduced by this plan. Every hit was documentation *about* the practice (skill bodies teaching it) or CHANGELOG prose.

Open items for v4.0.0, all recorded with Source phase, Reason, and Suggested next step:

| Bundle | Open |
|---|---|
| agent-communication-overhaul | DF-1, WN-2, MT-1, MT-3 |
| cost-effective-ci-cd | DF-1, DF-2, WN-1 |
| docs-lifespan (this plan) | BG-6 (half), WN-1, WN-2 -- BG-3, BG-4, BG-5 and one half of BG-6 were FIXED in the post-phase gaps pass |

BG-3 bore directly on the plan Goal, so it was fixed rather than shipped: see the Goal review below. BG-4 and BG-5 were fixed in the same pass because both were defects this migration exposed in shipped tooling. What remains open is deliberately scoped: WN-1 is a local environment gap that CI already covers, WN-2 is a one-time detector sweep with no automated consequence, and BG-6's second half is a file deleted by an earlier retention pass whose citation must not be silently re-aimed.

## Living docs architecture

Present and correctly placed at the docs root, unmoved by the migration:

```
docs/handbooks/   README.md, html, markdown
docs/decisions/   README.md, implemented, proposed, rejected
docs/*.md         CATALOG-COVERAGE, DEVLOG, README, dev-environment-windows,
                  framework-coverage, permissions-research, permissions-setup,
                  roadmap-prioritization, todos
```

Nothing under `docs/testing/` or `docs/validation/` was invented; neither exists and neither was created.

## Git-tree hygiene

`python scripts/check_release_preconditions.py --branches --repo-settings` (report only; nothing deleted):

```
Branch hygiene (merged into origin/develop)
  OK: no merged remote branches to clean up
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  NOTE: the repository description disagrees with README.md:
    - skills: description says 324, README.md declares 325
```

Two items for the maintainer, neither blocking: one stale remote branch from a closed unmerged PR, and a GitHub repository description that says 324 skills where README declares 325. The description is not a version-carrying surface, so `check_version_sync.py` cannot see it; it must be corrected by hand in repository settings.

## CI/CD coverage

```
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.
workflow-security: PASS
installer parity: PASS
```

CI covers every change in this release. The `tests` job runs the whole `catalog/hooks/tests` and `tests/` trees through `scripts/ci/run.py --profile full --only tests,extension-tests` rather than enumerating directories, and it pip-installs all six extension packages - so the three suites blocked locally by WN-1 do run in CI.

**Two migration-induced CI fail-opens were found and fixed in this phase.** Both would have failed silently rather than loudly, which is the dangerous shape:

1. `.github/workflows/presentify-extractor.yml` - the job's change filter named its fixture scripts with escaped dots (`docs/v3/v3\.12/...`), so after the migration it matched nothing and the job would simply have stopped triggering on fixture changes. Six `run:` steps that execute those scripts by path were repaired in Phase 6.
2. `.github/workflows/ci.yml` - the changed-path classifier matched development contract docs with `^docs/[^/]+/[^/]+/development/[^/]+\.md$`, three segments before `development`. The canonical tree is one level deeper, so a contract-doc change fell through to "every changed path is ignorable documentation prose" and skipped CI entirely. Widened to `^docs/(releases/)?[^/]+/[^/]+/development/[^/]+\.md$`.

The classifier fix is covered in both directions. Three canonical-tree cases were added to `tests/validators/test_ci_changes_classifier.py`, and the new contract-doc case was proven to fail against the un-widened pattern before the fix was restored:

```
FAILED tests/validators/test_ci_changes_classifier.py::test_classification[development contract, canonical tree-changed7-true]
1 failed, 2 passed, 23 deselected
...
3 passed, 23 deselected      (after restoring the fix)
```

**Coverage re-confirmed after the gaps pass**, which touched two `.ps1` files and one `.sh`:

- `shellcheck` over every `catalog/**/*.sh` runs unconditionally in the `shellcheck` job, and the changed hook passes locally.
- `powershell-parse` is an unconditional AST floor over every `catalog` and `scripts` `*.ps1`; run locally it reports `1 passed` after the `link-baseline.ps1` and `old-version-docs-guard.ps1` changes.
- The PowerShell **5.1 behavior** leg is a separate claim and lives in `tests-windows`, which runs the same suites on Windows.
- No new script needs an installer copy step: both changed files are inside already-recursively-copied trees, and no new repo-internal guard was added.

## Platform contract and installer parity

```
installer parity: PASS        (hard gate)
platform contracts: PASS
[contract-freshness] OK: contract verified for v3.21.0 (last_verified 2026-08-25).
```

Two read contracts were re-verified this cycle against **fetched** official vendor documentation, not recalled:

| Platform | Source | Result |
|---|---|---|
| Claude Code | `https://code.claude.com/docs/en/skills` | MATCH - `~/.claude/skills/` confirmed verbatim, `.claude/commands/` confirmed still read |
| Cursor | `https://cursor.com/docs/skills` | MATCH - `~/.cursor/skills/` confirmed verbatim; the doc additionally names `~/.agents/skills/` and backward-compatible reads of `~/.claude/skills/`, both additive and requiring no installer change |

No adapter, installer path, `contract_checks` entry, or `install_verify` entry requires a change.

**Open, and owned by the release step**: `meta.verified_for_version` is stamped `3.21.0` and the freshness gate requires an exact match against the canonical version. It therefore CANNOT be re-stamped here - stamping `4.0.0` while the repository still declares `3.21.0` would fail the gate immediately. The re-stamp belongs in `/update release`, after the version bump, carrying the two MATCH results above so the release step does not have to re-fetch blind.

## Goal-vs-codebase review

**Plan Goal, restated**: "Every supported agentic platform, on its next install, receives a docs-tree standard organised by one enforceable axis (document lifespan) plus the four mechanisms that make adopting it survivable - so a consuming project can reshape its docs tree and prove nothing broke, rather than asserting it."

Inspected as if the phases had not been implemented here:

| Success claim | Artifact | Verdict |
|---|---|---|
| One command reshapes a docs tree | `audit-docs.py canonicalize-layout` migrated 763 files across 26 movements, including the archive container Phase 6 had to add | SATISFIED |
| ...and returns a set diff proving zero newly-broken links | `link-baseline diff --rename-map` reports `newly_broken: 0, fixed: 60` and exits 0 against this release's own 763-file move | SATISFIED (was a miss; see below) |
| A `docs/releases/` file edited after its release closed is flagged | `audit-docs.py lifespan-contradictions` exits 1 with 243 structured findings against the live tree | SATISFIED |
| An ADR cannot be filed under a release | `docs/decisions/` is declared "never release-scoped" and append-only in the skill's placement rules | SATISFIED |
| Living `docs/handbooks/` stays at the docs root, snapshotted at close | `docs/handbooks/` present at root; snapshot rule to `docs/archives/v<M>/v<M>.<m>/handbooks/` documented | SATISFIED |
| The standard reaches all 13 named platforms on one upgrade | 12 substantive instruction templates carry a byte-identical `Documentation Layout` block, parity-guarded; 4 thin stubs inherit | SATISFIED |

**The one miss, stated plainly.** The Goal's own words are "prove nothing broke, rather than asserting it", and the proving mechanism is the set diff. As shipped, `link-baseline diff` keys identity on `(source, link, resolved_target)`, so a moved file's pre-existing broken links are counted as `newly_broken`. On this migration the shipped gate read **873 newly_broken** where the true number of links broken by the move was 444, and 0 after repair. Phase 6 proved the property with an external normalization script instead.

This was recorded as **BG-3** and has since been FIXED in the known-gaps pass, before the single push, so the Goal is met in the shipped release rather than shipped with a recorded hole. `link-baseline diff` now accepts `--rename-map` (taking `git diff --name-status -M` output verbatim), projects the before-baseline into post-move coordinates, and drops `link` from the identity because a correct repair rewrites the link text. Directory renames are inferred from the file pairs and kept only when nearly every mapped file beneath a prefix agrees, which is what rejects the over-broad `docs -> docs/releases` rule a naive majority vote selected during this migration.

Run against this release's own move, the shipped tool reports `{"after": 773, "before": 833, "newly_broken": 0, "fixed": 60, "unchanged": 773}` and exits 0, matching the external proof. Four tests cover it, parametrized over both the Python and PowerShell implementations, including one asserting the map does NOT launder a genuine break introduced during a move.

## Human/manual testing suggestions

Machine checks cannot cover these; each needs a person:

1. **Run `nexus-hub upgrade` on a clean machine** and confirm the `## Documentation Layout` block appears in the instruction file of at least one guardrails-only platform (Aider's `CONVENTIONS.md` or Windsurf's rules file). Phase 5 proved this through isolated workspace renders, not a real global install - and BG-2 records that the global `--target` seam does not isolate, so a real install is the only honest way to see it.
2. **Migrate a second, unrelated repository** with `/update refactor --canonicalize-layout`. Nexus-Hub's own tree was already two-level and its archive already canonical inside the container; a repo on the flat `docs/<vSEMVER>/` or three-level `docs/versions/` shape exercises code paths this dogfood run did not.
3. **Confirm the presentify job actually triggers** on a change to `docs/releases/v3/v3.12/development/fixtures/gen_fixtures.py`. The filter fix is static-checked only, and its failure mode is silence.
4. **Open the migrated tree in an editor and navigate by clicking links** from `README.md` and `docs/README.md`. The set diff proves resolution, not that a human can find their way around.
5. **Verify the GitHub repository description** now matches the README skill count.

## Full-suite testing and stabilization

| Suite | Result |
|---|---|
| `tests/plans` + `tests/workflows` + `tests/validators` | 1287 passed, 15 skipped |
| `tests/skills` + `tests/ci` (presentify excluded, see DF-2) | 978 passed |
| `catalog/hooks/tests` | 1125 passed, 53 skipped (1 failure found and fixed: `test_all_v0_9_7_source_artifacts_exist`) |
| Full validate guard chain (27 guards) | PASS |
| `shellcheck --severity=warning scripts/installer.sh install.sh` | PASS |
| Extension suites | 3 of 6 clean (183 passed); 3 blocked by the local environment, recorded as WN-1 and covered in CI |

Link integrity re-verified after every subsequent edit, including the label sweeps:

```
{"after_unresolved": 774, "newly_broken": 0, "fixed": 59}
```

**Honest limits.** Two suites were not run to completion locally: the aggregate `--profile full` invocation (DF-2, roughly 2.5 hours on this workstation because `tests/skills/test_presentify_*` saturates 60-second subprocess timeouts that complete in milliseconds on the runner) and the three extension suites blocked by a missing `tree_sitter_javascript` grammar and an uninstalled `nexus_code_search` (WN-1). Both are environment properties, both are recorded, and CI runs both to completion. On this workstation CI is the authoritative complete run, which is the same conclusion DF-2 reached.
