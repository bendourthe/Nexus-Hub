# Session History -- presentify universal ingestion, Phase 1 (extraction fidelity)

**Date**: 2026-07-13
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-universal-ingestion.md`
**Phase**: 1 of 5 -- Universal ingestion (new formats + recursive repo walk)
**Branch**: `feat/presentify-robustness` (off `develop`)

## Goal

Make `/presentify` accept any mix of file types and whole directories / repositories: source code and config, Markdown / plain text, CSV / TSV, and standalone images, plus a recursive directory walk that assembles a repository into one coherent, navigable model. This builds on the released v3.12.0 fidelity work (PDF images, figure reconstruction, native charts, scanned-page OCR) without touching it.

## What was built

### Content model (`references/content-model.md`, additive; schema_version stays 2)

- `code` blocks gained optional `path` (repository-relative) and `truncated`.
- New `image` origin `standalone-image` (an image supplied as its own input file).
- `sources[].format` vocabulary extended with `code`, `markdown`, `text`, `csv`.
- New top-level optional `tree` object (the ingested layout) and `coverage.walk` sub-object (recursive-walk accounting).
- New section `kind: "overview"` (the synthesized repository landing section; unknown kinds already fall back to `content` in the builder).
- Per-format mapping subsections for code / config, Markdown / text, CSV / TSV, standalone images, and the directory / repository walk.

### Extractor (`scripts/extract_content.py`)

- New format maps: `CODE_LANGUAGES` (extension -> highlight language), `MARKDOWN_EXTENSIONS`, `TEXT_EXTENSIONS`, `CSV_EXTENSIONS`, `IMAGE_EXTENSIONS`, `SPECIAL_BASENAMES` (Dockerfile / Makefile / etc.); `EXTENSION_FORMATS` is derived from them.
- New extractors: `_extract_code`, `_extract_markdown` (intentionally-minimal in-house parser: ATX / setext headings, fenced code, bullets, pipe tables, local image references), `_extract_text`, `_extract_csv` (delimiter sniff + reuse of the Excel grid-to-block logic + numeric coercion), `_extract_image_file` (+ `_svg_image_block` for `image/svg+xml`).
- `_read_text_file` (UTF-8 with latin-1 fallback + truncation), `_coerce_cell`.
- Recursive walk: `_walk_directory` (`os.walk` with `IGNORE_DIRS` pruning, `IGNORE_BASENAMES` lockfiles, `_is_binary` sniff, `_load_gitignore` / `_gitignored` best-effort matcher, `--max-files` cap, deterministic sort) returning a walk report; `_expand_inputs` rewritten to walk directories and flag single-directory repo mode.
- Repository assembly: `_build_tree` / `_sort_tree`, `_assemble_repository` (overview section + README-first / docs / code-by-directory / data / images ordering), factored `_assemble_single` / `_assemble_multi` out of `build_model`.
- `build_model` threads `max_text_bytes` / `max_files`, computes repository-relative paths, and attaches `tree` + `coverage.walk`.
- New CLI flags `--max-text-bytes` (default 300000) and `--max-files` (default 400); updated description, docstring, and a stderr walk summary.

## Verification

Fixture: `docs/v3/v3.13/development/fixtures/mixed-repo/` (README with a table / code / bullets / a local SVG image, `.py` / `.js` / nested `.go` code, a numeric `.csv`, a `.txt`, an `.svg`, a `.png`, a `.gitignore` excluding `secret.txt`, and a `node_modules/` decoy).

- Walk: 8 files included; `secret.txt` gitignored; `node_modules` ignored; `pixel.png` not binary-skipped (image format).
- Repository model: `overview` section first, `tree` built, README-first ordering, per-directory code grouping.
- CSV -> `chart` (provenance `source-data`) with real `Revenue` + `Cost` series over Q1-Q4.
- Markdown -> table + code + bullets + inline image (origin corrected to `inline-image`).
- Determinism: two runs byte-identical (`cmp`).
- Caps: `--max-files 3` -> `file_count_capped: 5`; `--max-text-bytes 40` -> `truncated: true` with a marker.
- Single-file and multi-file explicit paths still assemble correctly (no `tree` / `overview`).
- `python -m ruff check`: all checks passed. `python -m py_compile`: OK.
- Validators: bundle audit 0 errors (3 pre-existing `.pyc` warnings, one removed); no-personal-paths clean; unicode-safety 0 errors; edited skill files ASCII-verified.

## Known limitations (carried to Phase 5 known-gaps)

- `.gitignore` matching is best-effort (leading-`/` anchor, basename / path globs via `fnmatch`); no negation (`!`) or full `**` semantics.
- No secret redaction on the walk; dotfiles with no recognized extension (`.env`) are not ingested, but a `secrets.yaml` would be.
- The Markdown parser is intentionally minimal (not full CommonMark).

## Next

Phase 2 -- image prominence preservation (extractor emits native `width` / `height` + `page_fraction`; authoring rule keeps dominant visuals as heroes, never a uniform thumbnail grid).
