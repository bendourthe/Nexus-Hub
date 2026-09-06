# Session History -- agentic-setup-adoption, Phase 4 (visual-regression discipline)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 4 of 8 -- Visual-regression discipline
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Adopt point 15 of the comparison: baseline screenshots, a perceptual diff, and an agent visual-review gate on top of the existing screenshot capture, with git-lfs-optional storage and a PR-attach fallback.

## What was done

### 4.1 visual-regression-testing skill

Authored `catalog/skills/testing/visual-regression-testing/SKILL.md` (74 lines): choose views/viewports, capture and store a baseline (git-lfs when available, else attach baseline + current + diff to the PR), diff current-vs-baseline, gate with an AGENT VISUAL REVIEW above threshold (read before/after/diff, approve intended changes, re-baseline deliberately). References both bundled scripts. Distinguished from `e2e-testing-automation` (behavior), `demo-capture` (one-off capture), and `browser-testing-with-devtools` (browser debugging). Registered across `skills.json` (271 skills), `SKILL_INDEX.md` (+1 row, total 271), and `marketplace.json` (testing 3 -> 4).

### 4.2 Bundled scripts + test + CI

- `scripts/perceptual_diff.py` (Pillow lazy-imported): mean-normalized-absolute-difference metric in [0,1]; writes a diff image; exits non-zero over threshold OR on a size mismatch (a dimension change is a regression - it never resizes to compare, which would mask a layout shift). Exit codes 0/1/2/3.
- `scripts/capture_screenshot.py`: best-effort headless Chromium-family screenshot (chrome / chromium / msedge), degrades with a clear install hint (exit 3) when no browser is present.
- `tests/skills/test_perceptual_diff.py` (7 tests, Pillow-gated, fixtures generated at runtime - no committed binaries): identical pass, near-identical within-threshold pass, clearly-different fail, size-mismatch fail, diff-image written, bad input -> exit 2.
- CI: added `Pillow` to the `tests` job's install step so the perceptual-diff tests run (they were already collected by the Phase 3 `pytest tests/skills -v` step).

## Deviations

- **`.py`-only bundled scripts** (no `.sh`/`.ps1` runners), consistent with Phase 3 and every presentify bundled script; Python is cross-platform and the parity rule targets `.sh` scripts.
- **`capture_screenshot.py` is not unit-tested** (browser-dependent) - recorded as MT-1; the perceptual-diff core is fully tested.

## Dependency note

Pillow is introduced as a LAZY import in `perceptual_diff.py` (the script prints `pip install Pillow` and exits non-zero without it, per the AGENTS.md lazy-import rule) and added to the CI tests job so the diff tests run. It is NOT a hard runtime dependency of the catalog - the skill and script degrade gracefully without it. No new outbound call or credential.

## Validation

- `pytest tests/skills/test_perceptual_diff.py`: 7 passed locally (pure Python; fixtures via Pillow).
- `ruff check` + `ruff format --check`: clean on both scripts and the test.
- `skills.json`: valid, 271 skills, no dupes, vrt present. Bundle-orphan audit: PASS (both scripts referenced from SKILL.md). New skill + scripts + test ASCII-clean.
- Quality gate: GO.

## Next steps

- Phase 5: performance profiling harness (augment `code-optimizer` with bundled profiler + profile-compare scripts; no new skill).
