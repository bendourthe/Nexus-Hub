# Validation Diff: pre-rename vs post-rename

**Date**: 2026-05-20
**Plan reference**: [docs/archives/v2/v2.0/plans/nexus-hub-rename.md](../plans/nexus-hub-rename.md) Phase 8 sub-task 8.1
**Purpose**: Confirm the post-rename repository is functionally indistinguishable from the pre-rename baseline (except for the rename itself).

## Skill bundle validator (`scripts/validate_skills.py --bundles-only`)

| Run | Result | Errors | Warnings | Skills scanned |
|---|---|---|---|---|
| Pre-rename ([validate-skills-pre.txt](validate-skills-pre.txt)) | PASS | 0 | 4 | 207 |
| Post-rename ([validate-skills-post.txt](validate-skills-post.txt)) | PASS | 0 | 4 | 207 |

The 4 warnings are the same WN-001 framework-specialist orphan-bundle warnings as in the pre-rename baseline. Closed in Phase 8 sub-task 8.3.

## Hook tests (`pytest catalog/hooks/tests`)

| Run | Result | Passed | Skipped | Failed |
|---|---|---|---|---|
| Pre-rename ([hook-tests-pre.txt](hook-tests-pre.txt)) | PASS | 366 | 3 | 0 |
| Post-rename ([hook-tests-post.txt](hook-tests-post.txt)) | PASS | 370 | 3 | 0 |

The post-rename run includes 4 new tests added during Phase 3 sub-task 3.3 (legacy-install migration smoke tests for both `installer.sh` and `installer.ps1`). 366 + 4 = 370 - matches expected count from the plan.

## Extension test suites

| Extension | Pre-rename | Post-rename | Result |
|---|---|---|---|
| nexus-skill-server | 37 passed | 37 passed | identical |
| nexus-code-search | 36 passed, 1 skipped | 36 passed, 1 skipped | identical |
| nexus-web-fetch | 23 passed | 23 passed | identical |

All three extensions run cleanly with the renamed Python package names (`nexus_skill_server`, `nexus_code_search`, `nexus_web_fetch`).

## JSON metadata parse-check

All 6 source-of-truth JSON files parse cleanly:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `data/skills.json`
- `data/marketplace.json`
- `data/bundles.json`
- `catalog/mcp-configs/mcp-servers.json`

## Bash syntax check

`bash -n` over `catalog/hooks/*.sh`, `scripts/installer.sh`, and `install.sh`: no syntax errors.

## Residual-rename grep (final)

Filter applied per plan Phase 8 sub-task 8.1 step 6:

```
grep -rln "DevAI-Hub|DevAI Hub|devai-hub|devai_hub|DEVAI_HUB|DEVAI-HUB" \
  | grep -v "node_modules|.git|docs/archive|docs/v0\.|docs/v1\.|CHANGELOG.md|README.md|README_zh.md|DEVLOG.md|v2.0.0/RELEASE_NOTES.md|v2.0.0/known-gaps.md|plans/nexus-hub-rename.md|rename-|sync-manifest|gitignore-audit|baselines|history|installer-smoke|apply_rename|installer.(sh|ps1)|docs/git/"
```

Result: **0 unintended residuals**.

The 68 total matches that remain in the working tree are all in expected locations:

- Frozen historical directories (`docs/v0.*/`, `docs/v1.*/`)
- Intentional rename callouts (`README.md`, `CHANGELOG.md`, `docs/archive/v2/v2.0/RELEASE_NOTES.md`)
- v2.0.0 self-documenting artifacts (plans/, rename-decisions.md, rename-inventory.md, sync manifests, baselines)
- The DEVLOG entries that describe the rename effort (documented as expected in `docs/archive/v2/v2.0/known-gaps.md` Phase 7 close note)
- The `scripts/apply_rename.py` Python helper that uses the old strings as match patterns
- Both installers' user-facing legacy-install migration prompt ("Detected existing DevAI-Hub install at $HOME/.devai-hub")
- `README_zh.md` v1.0.0 historical block (DF-005)
- `docs/git/gitignore-audit-2026-04-22.md` (historical audit predating the rename)

## Conclusion

No regressions vs. pre-rename baselines. All validators green. Phase 8 sub-task 8.1 acceptance criteria met.
