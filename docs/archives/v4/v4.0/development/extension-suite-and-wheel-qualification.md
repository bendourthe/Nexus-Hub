# v4.0 WN-1 extension-suite and wheel qualification

This frozen record closes the old Windows host-dependency warning and records a wheel defect found while testing its declared prerequisite. It covers local extension tests and an installed wheel, not the whole-repository full profile or a live provider account.

## Boundary

- Date: 2026-09-24. Base revision: `e32b3c23` from `origin/develop`.
- Host: Windows PowerShell and Python 3.12 in a disposable virtual environment under the user temp directory. The repository's six `pyproject.toml` development extras were installed with the documented editable-install form; the user's base Python environment was not modified.
- Before installing extras, `nexus-code-search` failed collection on `nexus_code_search.config`, `nexus-web-fetch` had three import collection errors, and `nexus-context-compressor` had three AST-strategy failures. These reproduced the old WN-1 signatures rather than being attributed to current product code.

## Six-suite result with the declared development extras

| Extension | Passed | Skipped |
|---|---:|---:|
| nexus-skill-server | 43 | 0 |
| nexus-code-search | 379 | 1 |
| nexus-web-fetch | 29 | 0 |
| nexus-skill-scanner | 89 | 0 |
| nexus-context-compressor | 235 | 2 |
| nexus-memory | 53 | 1 |
| Total | 828 | 4 |

The three originally failing suites passed in the same disposable environment. This establishes that the historical host failures were missing development dependencies; it does not rewrite the original failed run.

## Wheel follow-up found during qualification

- The non-editable `nexus-code-search` build initially failed with Hatchling's duplicate-path error for `nexus_code_search/eval/fixtures/c_app/fixtures.yaml`. The `packages` root already included that fixture, and `force-include` added it again. A new wheel-layout test failed on the original configuration and passed after removing only the duplicate include.
- The first corrected wheel built and exposed its eval fixture exactly once, but eight benchmark checks failed when run against the installed wheel because `DEFAULT_CORPUS` pointed to a checkout-only `tests/fixtures/benchmark` directory. A second regression test failed before the corpus mapping was added.
- The final wheel includes the 13 KB committed benchmark corpus under `nexus_code_search/contextmap/benchmark_corpus` and selects it when installed, while editable checkout runs retain the source-test corpus fallback. Archive inspection found exactly one eval fixture and one benchmark sample file at their target paths.
- The final wheel installed into the disposable environment. `nexus_code_search` imported from `site-packages`, its default corpus resolved there, `python -m nexus_code_search.contextmap.benchmark --check` passed at 49.1% aggregate reduction, and the full code-search suite passed 381 tests with one skip against the installed wheel.

The change does not alter the benchmark formula or its committed baseline. Protected pull-request checks and post-merge smoke and provenance are still required before publication is closed.
