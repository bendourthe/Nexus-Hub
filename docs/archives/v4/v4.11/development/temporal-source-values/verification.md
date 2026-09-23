# Temporal source-value qualification

This record covers the post-release v4.11 MT-5 DOM-text guard. It is for maintainers deciding whether a handbook's source-backed slide numbers have temporal verification; it does not certify unmapped or canvas-painted values.

## Contract

The independent `measure_handbook.py` inventory may name exact expected text for a CSS selector on a specific slide. The browser starts a mutation observer before presentation activation, samples only while that slide and value are visible, and checks every observed text change plus the settled state. Missing or ambiguous selectors are unverified. With no mappings, `source_value_guard` is `unchecked`, even when the remaining geometry report passes. Exact equality catches an in-range but wrong intermediate number that a range-only check would miss.

## Local verification, 2026-09-23

- The four initial red tests failed against the prior sampler: it had no source-value sub-verdict and accepted a brief wrong value.
- After implementation, the final 58-test measurement module passed. The five focused source-value cases passed after the final sub-verdict adjustment: static value, 60 ms wrong value between settled checkpoints, absent mapping, missing mapped selector, and unrelated layout failure with a passing source-value sub-verdict.
- `ruff check` passed for `measure_handbook.py`. The existing test module has import-order and line-length findings outside the changed lines; no new-line lint finding was observed. `git diff --check` passed.
- The actual `measure_handbook.py` CLI measured `docs/handbooks/distribution.html` against its retained independent inventory at 200 states: overall `pass`, zero errors, and `source_value_guard: unchecked` because that inventory declares no source values. This is real-artifact status reporting, not temporal coverage.

## Remaining boundary

No retained production handbook inventory yet maps its source-backed numbers into `source_values`, so real-artifact temporal coverage remains zero. Canvas pixels and values without independent source mapping remain unchecked. A passing mapped DOM-text check does not prove the source computation or whole-chart fidelity; the figure worksheet and attestation still own those claims.
