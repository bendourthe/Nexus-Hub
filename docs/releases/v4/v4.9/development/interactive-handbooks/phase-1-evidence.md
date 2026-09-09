# v4.9.1 interactive handbooks - Phase 1 evidence

Phase 1 establishes the shared contract and neutral retained-source seam. It does not qualify a production presentation. Base: develop at 27136cd74ce1dbfec757adea6fbfea9efabcaaa5; isolated branch feat/v4.9.1-interactive-handbooks.

## Contract reconciliation

| Existing draft difference | Disposition | Evidence and owner |
|---|---|---|
| One file with reading and presentation views | Kept | Existing dual-view reference matches R01-R03 |
| Resolved session/project intake retained | Kept; legacy consumer correction assigned Phase 4 | Old HTML body still says re-ask; R30 and T012 own correction |
| Visible controls, global slide-1 reset and authentic branding | Kept | R25-R30 represented in neutral inventory |
| Fullscreen interaction ambiguity | Revised | Explicit owner, denial fallback, native exit versus toggle and modal priority recorded |
| Single legacy slide navigation and fragment stepping | Revised | Shared contract is authoritative; Phase 2 uses automatic builds and bounded navigation |
| Baseline builder success as production evidence | Rejected | Fixture labels missing runtime and production assembly explicitly |
| Source-specific palette, board count and private paths | Rejected as universal constraints | Neutral brands, six-slide budget and synthetic data transfer failure mechanisms |

The plan's R01-R30 requirement-to-task proving map is retained unchanged. The owner table covers output/runtime/figures, candidate freshness, layout, format exports, design, prose, rendered measurement and evidence. The implemented living-docs decision was read and preserved.

## Functional exercise and tests

- Existing presentify and extractor workflow baseline: 270 passed (`python -m pytest` over `tests/skills/test_presentify*.py` plus `tests/workflows/test_presentify_extractor_workflow.py`).
- `python -m pytest tests/skills/test_presentify_dual_view_foundation.py -q --cov=tests/fixtures/interactive-handbooks --cov-report=term-missing`: 5 passed, 84% fixture-builder line coverage. The remaining five lines are CLI setup; the subprocess smoke exercises that boundary separately.
- The CLI builds two distinct temporary outputs with identical bytes. Parsed output contains one title, all six independently inventoried section anchors and a declared six-slide storyboard. Direct and CLI output bytes agree. Duplicate/missing source IDs and conflicting output paths reject before writing.
- `python -m ruff check` on the two new Python files: pass. Ruff formatting applied.
- `python scripts/validate_skills.py --bundles-only`: 336 skills, 0 errors, 64 existing advisory warnings.
- Chromium 151.0.7922.34 launched successfully through Playwright. Presentation behavior remains a Phase 2 duty, not a Phase 1 pass.

## Source boundary

The five historical example hashes remain in the source analysis. Private corpus availability is optional for this foundation; no private content was copied into the fixture or distributed skill. The raster is a labeled synthetic aspect-ratio specimen, not a source photograph. Sixteen negative mutations are retained for later semantic/runtime qualification; their declaration is not a claim that every detector already exists.

## CI impact

GitHub Actions invokes repository-native CI profiles. New stdlib fixture builder and tests reside in the existing tests/skills discovery path; Pillow was already an extractor dependency and is not required to replay the committed fixture. New retained assets require no service, secret or paid call. Browser and distribution additions are owned by Phases 2 and 7. No pipeline file changed and no remote run was started.

## Post-phase sequence

Gitignore: 0 patterns added; temporary outputs use pytest directories and existing cache exclusions. Post-phase test review passed: 275 tests; Ruff and git diff --check passed. Documentation audit is read-only and limits new evidence to the active release tree. Product version remains 4.9.0; only this unfinished plan is retargeted to v4.9.1 with incoming link repair. Known gaps and the development index record the active work. No scratch deletion or archive mutation was requested.

## Retained input hashes

- `tests/fixtures/interactive-handbooks/aster-brand.json`: `117d841bbe56b2cfd7d66c5d55bddf76ede0a273eb3921769916d5503efb178e`.
- `tests/fixtures/interactive-handbooks/brand.svg`: `ccb7d9679a3c8113806eab6d6fea3efc813bdbb8a23ec5996ba32a449f512a32`.
- `tests/fixtures/interactive-handbooks/build_fixture.py`: `dcb19ee5e2f47ae60d08e96db11f5a7ac8446c2f2379865db97f8af322984d2d`.
- `tests/fixtures/interactive-handbooks/flow.svg`: `4e9f0ed605e3e824d8426fa13337a38e3f37278286241ba2515310f964934055`.
- `tests/fixtures/interactive-handbooks/handbook.md`: `ed0c1c8572b836d0d94418887f2d86298754bae5f587245496fdc626ea94a68d`.
- `tests/fixtures/interactive-handbooks/inventory.json`: `9d015f15ec2e5c0dea905e20c1bec68b45acd197678c01a51e6618219fda2c5f`.
- `tests/fixtures/interactive-handbooks/map.json`: `a18a46649efbc4b08bc34df7f004ff5a0ced098bbf87d5fdc6e7c392dc3a43c7`.
- `tests/fixtures/interactive-handbooks/model.json`: `8d9ea0b59c7419405fe82c9b81341b0dad43d58ff339c38cd27300fd7b753240`.
- `tests/fixtures/interactive-handbooks/negative-variants.json`: `bc4153c0a06d261ab49722f8ed3b3e5417103851954d6864cb8d466fd4193936`.
- `tests/fixtures/interactive-handbooks/subject-fixture.png`: `feaa1928bc7efad1099775f1630eb9df960d36ce63a1746f99f2e3acbc2055e1`.
- `tests/fixtures/interactive-handbooks/tide-brand.json`: `2a3d6cf09f048f30350f6bf1646976be814efe25187042cad161506d3a8427d6`.
- `tests/fixtures/interactive-handbooks/wave.svg`: `b12e65ecd4ef39a316f3e78ed9f23cf3e7bd3338ea0aba9267ed1fab15c7a0f4`.
