# Session History - v3.4.0 adoption-nessie-and-agency-agents Phase 3: session-query extension to Obsidian + exported ChatGPT/Gemini history

**Date**: 2026-06-15
**Plan**: [`../../plans/adoption-nessie-and-agency-agents.md`](../../plans/adoption-nessie-and-agency-agents.md) Phase 3 (A4, re-full)
**Branch**: `develop`
**Outcome**: Complete. All Phase 3 exit-checklist items satisfied; quality gate GO. Phase 3 of 5; not the final phase, so no release-readiness run.

## Goal

Extend the `session-query` skill's LOCAL discovery and extraction to three additional zero-outbound prior-context sources beyond AI session-log JSONL: Obsidian vault notes, exported ChatGPT history, and exported Gemini history - so the session-query (and downstream context-pack) flows see more of the user's prior context without breaking the zero-outbound invariant or changing default behavior.

## What shipped

- **`extract-session.py` / `extract-session.ps1`**: a per-file source dispatcher (`iter_normalized_records` / `Get-NormalizedRecords`) selects a parser from the discovery `tool` tag (or `--tool`/`-Tool`), with extension auto-detect for untagged inputs (`.md` -> Obsidian, `.json` -> ChatGPT/Gemini auto-detect, else JSONL). Three new parsers - Obsidian (frontmatter timestamp + title, heading-section split, `[[backlinks]]` preserved in section text), ChatGPT (`conversations.json` `mapping`/`messages`, epoch `create_time` -> ISO, title prepended to first message), and Gemini (Takeout "My Activity" entries, ISO `time`, title + subtitles/details) - all normalize into the existing `ts`/`role`/`text` record shape, so topic/branch/time-window filtering, snippet truncation, and the `query`/`sessions`/`summary` digest are reused unchanged. JSONL behavior is byte-for-byte identical. The stdin reader now preserves the per-line `tool` tag so a `discover | extract` pipe dispatches per file.
- **`discover-sessions.sh` / `discover-sessions.ps1`**: added Obsidian vault discovery (locate vault roots by the `.obsidian/` marker, bounded depth, emit `*.md`, fallback to a plain `*.md` folder) and ChatGPT/Gemini export discovery (default `~/Downloads` canonical-name match; explicit `--root` emits all `*.json`/`*.md`). The no-`--tool` default scan still covers only Claude/Codex/Cursor JSONL, and an explicit `--root` with no `--tool` still tags `custom` + `*.jsonl` - both unchanged.
- **`SKILL.md`** (149 lines): frontmatter `description`/`summary_l0`/`overview_l1` broadened to name the new sources and add trigger phrases ("search my Obsidian notes", "what did I ask ChatGPT about this"); a "Sources and default roots" table; new When-to-Use bullets, Instructions `--tool` examples, two Common-Rationalizations rows, and Verification items; the zero-outbound statement kept explicit throughout.
- **`CHANGELOG.md`**: `## [Unreleased]` "Added" entry recording the extension as `re-full`, local-only, zero new outbound call / dependency / credential.
- **`tests/validators/test_session_query_extract.py`**: 13 new cases (Obsidian frontmatter ts + backlink topic match + no-match drop + `.md` auto-detect; ChatGPT two-message extract + epoch time-window + `.json` auto-detect; Gemini multi-entry + single-entry; root-scan-with-`--tool`; default-root-ignores-md; stdin tool-tag dispatch; bash-gated discovery vault-marker). The existing zero-outbound static guard now implicitly covers the extended scripts.

## Key decisions / troubleshooting

- **Reuse the digest pipeline, dispatch by source tag.** Rather than fork the extractor per source, every new parser yields the existing normalized record shape. This kept the change additive and the JSONL path untouched (13 original tests pass unchanged).
- **PowerShell `ConvertFrom-Json` single-element-array unrolling (the one real bug).** A multi-message ChatGPT fixture returned 0 records in PowerShell while 1-message worked. Bisection (slicing the function out of the script and running it in isolation, then dumping `$parts`) showed `ConvertFrom-Json` collapses a single-element `content.parts` array to a scalar `String`; the guard `$parts -isnot [string]` then rejected it. Python's `json` never unrolls. Fixed by making the `.ps1` parsers accept either a string or an enumerable for `parts`, and applying the same `@()`-normalization to ChatGPT `messages` and Gemini single-entry/`subtitles`. Added a defensive string-`parts` branch to Python for symmetry. Both languages now produce identical digests on the same input.
- **Default-unchanged guarantee.** New sources are opt-in via `--tool`; the no-`--tool` scan and `--root`-without-`--tool` paths are untouched. `test_default_root_scan_ignores_md` asserts a Markdown folder yields nothing under the default JSONL scan.

## Verification (quality gate: GO)

- `make` is not on PATH (WN-v33-1), so gates were run via direct equivalents:
  - **Tests**: `tests/validators/test_session_query_extract.py` 26 passed; full repo suite `tests/` 452 passed (9m19s); hook suite `catalog/hooks/tests/` 439 passed / 7 skipped.
  - **Validate**: orphan-bundle audit PASS (0 errors, 1 pre-existing WN-v33-2 `.pyc` warning); unicode-safety 0 errors (touched files ASCII-clean); no-personal-paths clean; supply-chain-iocs clean; workflow-security clean; version-sync all surfaces match 3.3.4.
  - **Lint**: `bash -n discover-sessions.sh` clean; PowerShell `[Parser]::ParseFile` clean on both `.ps1`. ShellCheck not on local PATH; CI ShellChecks `catalog/**/*.sh` on the ubuntu runner.
  - **Security**: skill-security scan on `session-query` - 0 findings, install-OK.
  - **Zero-outbound**: static-analysis guard over all four scripts green; manual grep for banned network tokens clean.
- Manual parity dry-run on this Windows host (bash + Windows PowerShell 5.1) confirmed all three sources produce identical digests across topic and time-window filters, plus stdin tool-tag dispatch and `--root` discovery.

## Files changed

- `catalog/skills/workflow/session-query/SKILL.md`
- `catalog/skills/workflow/session-query/scripts/discover-sessions.sh`
- `catalog/skills/workflow/session-query/scripts/discover-sessions.ps1`
- `catalog/skills/workflow/session-query/scripts/extract-session.py`
- `catalog/skills/workflow/session-query/scripts/extract-session.ps1`
- `tests/validators/test_session_query_extract.py`
- `CHANGELOG.md`
- `docs/v3/v3.4/plans/adoption-nessie-and-agency-agents.md` (Phase 3 exit checklist)
- `docs/v3/v3.4/known-gaps.md` (status + WN-v33-1 Phase 3 re-confirmation)
- `docs/v3/v3.4/development/2026-06-15_session-query-extension-design.md` (sub-task 3.1 design note)
- `docs/DEVLOG.md`

## Next

Phase 4: optional Kimi / Qwen / OpenClaw integrations (A3-ext), reusing the Phase 2 `IntegrationBase` pattern.
