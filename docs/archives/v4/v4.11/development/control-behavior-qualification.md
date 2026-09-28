# MT-9 declared control behavior qualification

This record qualifies a bounded browser behavior guard for presentation controls. It is for maintainers deciding whether a mapped control's intended effect was observed, not evidence that every control in a handbook has been mapped or that the full handbook passes visual QA.

## Boundary and input

- **Base revision**: `d052af9e`, on the isolated `fix/v411-control-behavior` branch before publication.
- **Consumer entry point**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/measure_handbook.py` with `--inventory` and `--detector`.
- **Browser**: Playwright Chromium 151.0.7922.34; behavior probes use 1366x768 and reduced motion in a fresh page for each declaration.
- **Inventory**: [control-behavior-inventory.json](control-behavior-inventory.json) declares that clicking the first chart-series button changes the plotted marks' computed `display` from `inline` to `none`.
- **Generated inputs**: `test_authored_chart_toggle_passes_declared_mark_visibility_transition` generated the valid chart, SHA-256 `FE0089C0B9467F92940F39ED37271CEED33394DE2169F6A810E4485B383AF268`; `test_detached_slide_series_control_is_reported` generated the detached-button mutation, SHA-256 `E71B2EE4C3D0AC298D4C359A99CFBBEFC1C140B6B0FA05BF9E7E2718BEABF33B`. Both are recreated by the named tests; pytest temporary paths are not retained.

## Red and green evidence

- The second-slide inert-control test first failed with `KeyError: 'control_behavior_guard'` on the baseline harness, then passed after the guard was added. The idempotent Reset test failed before setup clicks were implemented, and the no-change-contract test failed while an inert control could be certified as passing; both pass after correction.
- An initial chart assertion using `aria-pressed` was rejected: the detached button changed that flag while the plotted marks remained visible. The independent inventory now measures the marks themselves. The valid chart and detached mutation both passed their targeted browser assertions; a separate positive test covers attribute-state observation without treating it as proof of plotted-mark behavior.
- Standalone CLI on the valid chart returned page `fail` with 54 page findings, but `control_behavior_guard: pass`, one observation, `inline -> none`, and zero guard findings. The same CLI on the detached mutation returned page `fail` with 66 page findings, `control_behavior_guard: fail`, and one guard finding: CSS `display` remained `inline` instead of `none`. Both CLI exits were 1 because the whole test fixtures do not meet the default all-viewport handbook quality gate.

## Final local checks

- `python -m pytest tests/skills/test_presentify_measure_handbook.py -q` with `NEXUS_REQUIRE_RENDER=1`: 65 passed, zero failed, in Playwright Chromium.
- `python -m coverage run --concurrency=greenlet --source=catalog/skills/specialized-domains/document-to-interactive-html/scripts -m pytest tests/skills/test_presentify_measure_handbook.py -q` with `NEXUS_REQUIRE_RENDER=1`: 65 passed, and `coverage report -m --include='*measure_handbook.py'` measured 221 of 261 statements, 85%. A first run through default pytest-cov tracing reported 28% and marked the executed browser loop wholly missed; greenlet-aware tracing is required for this Playwright suite.
- `python -m ruff check` on the changed measurement and test modules: clean.
- `python scripts/ci/run.py --profile fast --base origin/develop --quiet` on Windows with Git Bash first on `PATH`: 17 passed, zero failed or skipped.
- `python scripts/check_docs_conventions.py --root docs/releases/v4/v4.11` and the same checker with `--root docs/archives/v4/v4.11/development`: both exit 0. The default checker scans only the current v4.13 release tree, so these explicit roots are required for this evidence.

## Claim boundary

The guard reports `unchecked` when no independent `control_behaviors` inventory is supplied. A `pass` certifies only the declared controls and their specified before/after property at one representative viewport. The author must derive expected effects from the storyboard or source, include setup for idempotent controls, and enumerate all meaningful controls before claiming generic liveness coverage. This record does not qualify the original unretained four-button artifact, the full retained pilot, keyboard paths, or the fixture's typography. MT-9 remains open pending broader artifact inventory, browser qualification, protected integration, and post-merge evidence.
