# Known Gaps - v3.12

**Project**: Nexus-Hub
**Status**: in development (presentify-fidelity-and-variety Phase 4 of 6 complete; Phase 4 added no gaps)
**Last updated**: 2026-07-11 (Phase 3: one new warning WN-3; Phase 2 added no gaps but fixed the Phase 1 region-crop defect inline - tick labels outside the rasterized crop - via label-inclusive crop expansion in `extract_content.py`, 45/45 fixture checks green)

## v3.12.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 3 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - PDF text/figure interleaving is approximate

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md` sub-task 1.2
- **Reason**: Within a PDF page section, extracted figure images are placed after the page's text and tables (ordered among themselves by vertical position) rather than interleaved at their exact in-flow position; true interleaving would require full layout reflow, which is out of scope. Documented as a runbook gotcha.
- **Suggested next step**: The `page` + `caption` metadata is sufficient for the Phase 2 authoring stage to place figures sensibly; revisit only if authoring proves to need exact in-flow positions.

##### DF-2 - Caption text remains duplicated in page paragraph text

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: sub-task 1.2 (caption pairing)
- **Reason**: A detected caption is ATTACHED to its figure block, not moved: the same line also remains inside the page's paragraph text. Removing it from the text flow risks dropping content on false-positive matches, so the extractor keeps both. Documented as a runbook gotcha.
- **Suggested next step**: The authoring stage should prefer the block `caption` and drop the duplicate line; consider extractor-side dedup once caption matching has real-world mileage.

##### DF-3 - OCR table recovery is geometry-based; pytesseract path recovers paragraphs only

- **Source phase**: Phase 1 (1.5)
- **Plan reference**: sub-task 1.5 (two-tier OCR path)
- **Reason**: Tier-A table reconstruction clusters OCR boxes into aligned multi-cell rows, which works on well-separated columns (fixture-verified) but not on dense or borderless tables; the `pytesseract` fallback emits paragraphs only. The tier-B scanned-page image plus the Phase 2 transcription/verification pass are the accuracy backstop in all cases.
- **Suggested next step**: Revisit only if real scans show tier-A table recovery failing where it matters; the mandatory Phase 2 numeric verification already guards correctness.

#### Warnings

##### WN-1 - Pre-existing local test failures on the Windows dev host (unrelated to this phase)

- **Source phase**: Phase 1 (1.6 validation)
- **Plan reference**: sub-task 1.6
- **Reason**: The full pytest sweep shows failures that reproduce identically on a clean HEAD with this phase's changes stashed: 99 bash-invoking hook tests and 4 installer/branch-flag repo tests (`bash -n` fails with empty stderr on this host - the WN-v33/WN-v36 environment family), plus two pre-existing local failures in untouched domains (`nexus-context-compressor::test_small_input_never_expands_under_store`, `validators::test_discover_obsidian_vault_marker`). All suites touching this phase's surface are green (4 extension suites pass; compression accuracy gate PASSED).
- **Suggested next step**: CI (ubuntu/macOS) remains the authoritative gate for the bash suites; confirm green on the release run. The two non-bash local failures predate this version and should be triaged in their own domains.

##### WN-2 - build_presentation.py fails `ruff format --check` (pre-existing)

- **Source phase**: Phase 1 (1.6 lint)
- **Plan reference**: sub-task 1.6
- **Reason**: The builder was not ruff-format-normalized when shipped in v3.9.0; this phase edited only its schema-version acceptance block and left whole-file reformatting out of scope (every changed line must trace to the phase). `ruff check` passes; only the formatter diff is outstanding, and no repo gate enforces `ruff format` today.
- **Suggested next step**: Normalize the file in the plan's Phase 6 architecture-refactor pass (behavior-preserving, reviewed as its own commit).

##### WN-3 - Interaction-budget demo verified by static structural review only (no headless browser on the dev host)

- **Source phase**: Phase 3 (3.3)
- **Plan reference**: sub-task 3.3
- **Reason**: The chart-free budget demo (`docs/v3/v3.12/development/fixtures/budget_demo.py` -> `models/budget-demo.html`) passes an 11-check structural verification (all five budget points wired, zero external refs, JS within the 60 KB cap, reduced-motion + keyboard guards present), but no headless browser is available on this host to render it and screenshot the interactive states - the skill's own documented degradation path (static review + a one-line note) was applied.
- **Suggested next step**: Exercise the rendered page during the Phase 5 worked example's visual-QA loop on a host with a headless browser (or accept the same degradation there and note it); no code change expected.

#### Missing tests / coverage gaps

##### MT-1 - extract_content.py has no pytest suite; validation is via the committed fixture verifier

- **Source phase**: Phase 1 (1.6)
- **Plan reference**: sub-task 1.6; Phase 6 sub-task 6.3
- **Reason**: Skill-bundle scripts have no pytest convention in this repo; Phase 1 validation runs `docs/v3/v3.12/development/fixtures/verify_phase1.py` (45 binary checks over generated fixtures: visuals, native charts, captions, dedup, scanned/OCR tiers, degradation, determinism, builder compat) manually rather than under CI.
- **Suggested next step**: Phase 6 (6.3) decides whether to promote the fixture verifier (or extracted pure-function unit tests) into CI.
