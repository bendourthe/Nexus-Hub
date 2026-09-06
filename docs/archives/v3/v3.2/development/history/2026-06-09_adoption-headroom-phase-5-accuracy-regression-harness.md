# Session History -- v3.2.0 adoption-headroom Phase 5: Accuracy-regression harness

**Date**: 2026-06-09
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 5 of 7 -- Accuracy-regression harness (re-full)
**Branch**: `feat/adoption-headroom` (continuing from Phase 4)
**Outcome**: complete; all three sub-tasks (T016-T018) closed, all quality gates green (GO).

## Goal

Prove the engine's compression preserves answer quality so aggressive ratios can ship safely, and gate that property in CI. headroom's upstream `eval.yml` measures accuracy by running GSM8K / TruthfulQA / SQuAD / BFCL through a live model; the plan (T016) deliberately rejects that for a deterministic, offline structural-fidelity harness -- a live LLM call is non-deterministic, slow, and an outbound call this repo refuses to add. The mandate (comparison Section 13) is that this gate exists before aggressive ratios ship by default, because lossy compression can silently drop data the model needs.

## Subtasks completed

1. **T016 -- accuracy-regression harness** (`extensions/nexus-context-compressor/evals/`). Built a top-level harness package (sibling of `src/` and `tests/`, the literal path the plan names, mirroring headroom's own top-level `evals/`). `runner.py` scores each fixture on two independent axes: **fidelity** (the accuracy proxy) and **effectiveness**. Fidelity is three deterministic structural checks -- CCR round-trip completeness (for a JSON array, `reconstruct(compress(x)) == x`, plus each dropped span retrieves byte-identically; for code, each elided body resolves back to its exact lines), and signature-preservation rate (every import / decorator / class header / function-method signature in the fixture's `manifest.json` answer key survives in the skeleton). Effectiveness is a tokenizer-free character-length reduction (token ratio is computed and reported but never gated, because `tiktoken` availability varies across machines). Shipped a fixed local dataset under `fixtures/` (two JSON arrays with duplicate runs + a Python and a TypeScript module with multi-line bodies), a `manifest.json` describing each fixture, a committed `baseline.json`, Markdown + JSON report renderers, the `check_baseline` gate, and an `--update-baseline` path. The runner bootstraps `src/` onto `sys.path` so `python -m evals` runs from a bare checkout with no install.
2. **T017 -- wire the gate**. Three surfaces: a `make compress-eval` target (writes a report to `docs/v3/v3.2/compression-eval-baseline.md` and runs the gate), a step inside the `make validate` recipe, and a step in the CI `validate` job (`.github/workflows/ci.yml`) immediately after the skill-security gate. The CI step runs `cd extensions/nexus-context-compressor && python -m evals --check` -- no `pip install` needed because the runner self-bootstraps. The gate stays quiet in pure `--check` mode (one-line PASS/FAIL to stderr) to respect the repo's output-minimization convention. Documented the threshold and the intentional re-baseline procedure in `evals/README.md`.
3. **T018 -- tests + stabilization**. 12 harness tests in `tests/test_evals.py`, including the load-bearing proof that a deliberately broken (irreversible) compressor is caught: injecting a no-op CCR store drops spans that can never be retrieved, so CCR round-trip fidelity falls below 1.0 and the gate fails. Added synthetic below-floor (effectiveness) and signature-loss detections too. Confirmed AST and regex code strategies produce identical fixture numbers, so the floor is environment-independent.

## Key decisions

- **Structural fidelity, not a live-LLM benchmark.** "Accuracy preserved" is reframed as a checkable invariant the engine guarantees (reversibility + structure preservation), measured exactly and offline. This is the plan's explicit T016 design and keeps the gate deterministic and zero-outbound. The trade-off (no semantic answer-quality measurement) is logged as DF-v32hr-12.
- **Two independent thresholds.** Fidelity is gated at exactly 1.0 with zero tolerance (any reversibility miss is a correctness bug in a deterministic engine). Effectiveness is gated at a floor (0.36) with a 10-point safety margin below the measured 0.458, so a strategy that compresses *harder* never trips it while one that silently *stops compressing* always does.
- **Gate on character reduction, not token reduction.** `tiktoken` (and its cached vocab) may be absent offline; gating a token metric would make the floor flaky across environments. Char reduction is deterministic and a faithful proxy; the token ratio is reported informationally (DF-v32hr-13).
- **Top-level `evals/`, self-bootstrapping.** Honors the plan's literal path and headroom's layout, and `python -m evals` works with no install on any platform (CI, bare checkout, dev host) because `runner.py` adds `src/` to `sys.path` exactly as the test `conftest.py` does.
- **`--update-baseline` is the only sanctioned way to move thresholds.** It recomputes fidelity (pinned 1.0) and an effectiveness floor a margin below the measured reduction, with a `_comment` warning never to lower a fidelity threshold to silence a failing gate.

## Test results

- Package suite: **171 passed** (12 added in Phase 5; same count from the repo-root invocation CI uses).
- Gate command verbatim (`cd extensions/nexus-context-compressor && python -m evals --check`): **exit 0** -- CCR round-trip 100%, signature preservation 100%, mean char reduction 45.8%.
- Forced-regex-fallback run (mirroring the CI validate job where tree-sitter is absent): **identical** per-fixture reductions and 100% fidelity, confirming the floor is strategy-independent.
- `make validate` validators run directly (no-personal-paths, unicode-safety, version-sync): **0 errors** (the unicode WARNs are pre-existing legacy templates).
- Lint: `ruff` not installed locally, so a `py_compile` syntax check on the new modules (clean); CI's pre-commit run covers ruff.
- Confirmed `git add -n` for `evals/` stages exactly the 10 intended files; `.pytest_cache`, `.coverage`, and `evals/__pycache__` are all gitignored.

## CI/CD edits

- `.github/workflows/ci.yml`: added a "Compression accuracy-regression gate (v3.2.0 Phase 5)" step to the `validate` job, after the skill-security gate. No package install needed (the harness self-bootstraps).
- `Makefile`: added `compress-eval` to `.PHONY`, a `compress-eval` target (report + gate), and a gate line inside the `validate` recipe.

## Deviations

- **Placement.** The plan writes the path as `extensions/nexus-context-compressor/evals/`; it is implemented there as a top-level harness package (sibling of `src/`/`tests/`), matching headroom's own `evals/` layout and the in-repo `nexus-code-search` eval precedent, rather than nesting it under `src/nexus_context_compressor/`.
- **No CHANGELOG entry yet.** Per the plan, the CHANGELOG `## [Unreleased]` entry for the whole context-compressor adoption is Phase 7's T023; Phase 5 records itself in known-gaps + this session history instead, to respect the phase boundary.

## Troubleshooting / environment notes

- `make` is not on PATH (WN-v32-2 / WN-v32hr-2 / WN-v32hr-3 root class); the gate and validators were run by invoking the underlying commands directly -- the gate command itself ran verbatim and green.
- Verified the test imports resolve both ways the suite is invoked: `cd extensions/nexus-context-compressor && pytest` (local) and `pytest extensions/nexus-context-compressor/tests/` from the repo root (CI) -- the `conftest.py` now also puts the package root on `sys.path` so `from evals.runner import ...` resolves without an install.

## Known gaps

Logged in [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md): new DF-v32hr-12 (structural-fidelity gate, no live-LLM semantic benchmark), DF-v32hr-13 (effectiveness gated on char reduction, token ratio reported but not gated), WN-v32hr-3 (partial Windows local verification). The Phase 1-3 deferred refinements (DF-v32hr-1 near-dup fingerprinting, DF-v32hr-2 adaptive sizing, DF-v32hr-3 error/outlier preservation, DF-v32hr-5 prose-embedded arrays) now have the measurement tool they were waiting on, but remain open enhancements -- the harness is the gate, not the implementation.

## Next steps

- **Phase 6 (Optional ML token-dropper)**: a default-off ModernBERT importance-scorer using public pre-trained ONNX weights, offline-capable, behind the `[ml]` extra, with the Phase 5 accuracy gate re-run with the module enabled to confirm no fidelity regression at the default ratio. This is the free-text compression path that closes the rtk parity gap (DF-v32hr-10).
