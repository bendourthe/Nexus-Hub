# Known Gaps - v3.13

**Project**: Nexus-Hub
**Status**: release-ready (pending `/update release` commit / merge / tag / push)
**Last updated**: 2026-07-13 (Phase 5 reconciliation for the presentify universal-ingestion overhaul)

## v3.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 5 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

### Capabilities added this version

- Universal ingestion: source code / config, Markdown / plain text, CSV / TSV, standalone images, and a recursive directory / repository walk with ignore rules, a best-effort `.gitignore` matcher, a binary sniff, and `--max-files` / `--max-text-bytes` caps; repository assembly (synthesized overview + file tree + README-first + code grouped by directory).
- Image prominence signals (`width` / `height` / `page_fraction`) and a prominence-preservation authoring rule (a dominant source visual stays a hero, never flattened into a uniform thumbnail grid).
- Spacing / vertical-density discipline and an output-aspect control (`--layout` + a full-width / standard / portrait / other menu, content-aware non-interactive fallback).

### Open Items

#### Deferred

##### DF-1 - `.gitignore` matching is best-effort

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk reads the root `.gitignore` and supports leading-`/` anchoring plus basename / path globs via `fnmatch`, but does NOT implement negation (`!pattern`) or git's full `**` semantics. Documented as a runbook limit.
- **Suggested next step**: Adopt a vetted local `.gitignore`-spec library only if real repos show meaningful mismatch; the current matcher plus the ignore-dir list covers the common cases.

##### DF-2 - Markdown parser is intentionally minimal

- **Source phase**: Phase 1 (1.3)
- **Reason**: The in-house Markdown parser handles ATX / setext headings, fenced code, bullets, pipe tables, and standalone local images; it is not a full CommonMark implementation (reference-style links, footnotes, and HTML blocks pass through as prose). Standard-library-only by design (no Markdown dependency).
- **Suggested next step**: Revisit only if richer Markdown fidelity is needed; a lazy-imported CommonMark parser could be added behind the same lazy-import discipline.

##### DF-3 - No secret redaction on the repository walk

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk ingests text / config files by extension; dotfiles with no recognized extension (`.env`) are not ingested, but a file such as `secrets.yaml` would be. There is no content-based secret detection.
- **Suggested next step**: Users should not point `/presentify` at a repository holding plaintext secrets; a future pass could integrate the `egress-redaction` skill's typed policy before ingestion.

##### DF-4 - Video / audio media embedding (carried from v3.9 / v3.12)

- **Reason**: Media in any source format is ignored; embedded media would break the single-file offline / size guarantee. Unchanged by this version.
- **Suggested next step**: Out of scope for the self-contained-HTML deliverable.

##### DF-5 - Brand web-font embedding (carried from v3.9 / v3.12)

- **Reason**: Fonts stay as system stacks or base64 `@font-face`; fetching a brand web font would break the offline guarantee. Unchanged by this version.
- **Suggested next step**: A base64 `@font-face` embed path could be added; never an external fetch.

#### Warnings

##### WN-1 - Full-repo validators and browser visual-QA unavailable on the Windows dev host

- **Source phase**: Phases 1-5
- **Reason**: `validate_unicode_safety.py` / `validate_no_personal_paths.py` (full-repo scans) and the compression eval time out on the dev host, and no headless browser is installed, so the rendered visual-QA loop (screenshots) and the per-aspect / hero-vs-gallery rendered demonstrations could not run locally. Change-relevant validators were run directly (bundle audit, JSON integrity, version-sync, ASCII, ruff); edited files are ASCII-verified.
- **Suggested next step**: Rely on CI for the full validator chain; run the rendered visual-QA in a browser-capable session.

##### WN-2 - Deck-PDF prominence path not exercised end-to-end locally

- **Source phase**: Phase 2
- **Reason**: `pdfplumber` / `python-pptx` are not installed on the dev host, so the PDF path falls back to `pypdf` (no bbox geometry) and the PPTX path was not run; the PDF/PPTX `page_fraction` geometry was validated by code review plus the common-sink unit-check (rounding / clamp / absence). CI installs `pdfplumber` / `python-pptx`.
- **Suggested next step**: Covered by MT-1.

#### Missing tests / coverage gaps

##### MT-1 - No automated verifier check for PDF / PPTX `page_fraction` geometry

- **Source phase**: Phase 2 / Phase 5
- **Reason**: `verify_universal_ingestion.py` (28 checks) covers the text / code / CSV / image walk, repository assembly, determinism, caps, and the prominence sink (rounding / clamp / absence / native dims), but not the PDF-bbox / PPTX-shape `page_fraction` computation end-to-end. The v3.12 `verify_phase1.py` exercises PDF/PPTX extraction but predates `page_fraction`.
- **Suggested next step**: Add a `page_fraction` assertion to `verify_phase1.py` (it already generates a PDF/PPTX fixture with `reportlab` / `python-pptx` in CI), or a small dedicated fixture check, in a follow-up.

#### Hand-offs

##### HO-1 - Stale-duplicate-install / skill-name collision (belongs to the flattening migration)

- **Source phase**: Discovered during the investigation that motivated this plan
- **Reason**: Under `~/.claude/skills/` (and `~/.gemini/...`) a flat skill directory and a category-nested directory can both declare the same `name`, so they collide, and a stale flat copy can shadow the correct one (the original reported bad `/presentify` output came from a stale pre-fidelity flat copy shadowing the v3.12.0 one). Three stale copies were removed manually during this session. The ROOT cause is the skill-flattening install migration (the v3.12.1 cross-platform-adapters work), not this presentify skill.
- **Owner**: the `cross-platform-install-adapters` / flattening migration.
- **Suggested next step**: On install, prune stale / duplicate skill directories (or detect same-`name` collisions across flat and nested layouts) so a re-install cannot leave two same-named skills side by side.

### Deferred to the Phase 5 release-readiness / a browser-capable run

- The rendered visual-QA screenshots for the worked example (WN-1) and the deck-PDF prominence demonstration (WN-2 / MT-1).
