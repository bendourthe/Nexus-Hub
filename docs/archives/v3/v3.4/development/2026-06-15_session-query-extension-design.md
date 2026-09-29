# Design Note - session-query extension to Obsidian + exported ChatGPT/Gemini history (v3.4.0 Phase 3, sub-task 3.1)

**Date**: 2026-06-15
**Plan**: [`../plans/adoption-nessie-and-agency-agents.md`](../plans/adoption-nessie-and-agency-agents.md) Phase 3 (A4, re-full)
**Scope**: Extend the `session-query` skill's local discovery and extraction to three additional zero-outbound sources beyond AI session-log JSONL - Obsidian vault notes, exported ChatGPT history, and exported Gemini history. Pure local file parsing, zero new outbound call / dependency / credential.

## Existing architecture (the invariant to preserve)

- `scripts/discover-sessions.{sh,ps1}` enumerate local `*.jsonl` transcripts under the Claude/Codex/Cursor roots and print `tool<TAB>path` lines.
- `scripts/extract-session.{py,ps1}` read each file as NDJSON, normalize each record via candidate-key lists (`TS_KEYS`/`ROLE_KEYS`/`TEXT_KEYS`/`BRANCH_KEYS`), apply topic / branch / time-window filters, and emit one JSON digest (`query` / `sessions` / `summary`).
- Zero-outbound: the extractor imports no network module; a static-analysis test (`tests/validators/test_session_query_extract.py`) bans network tokens in all four scripts.

## Decision: dispatch by per-file source tag, reuse the digest pipeline

The discovery scripts already emit a `tool` tag per file. Phase 3 stops discarding that tag in the extractor and uses it to pick a parser. New recognized tags: `obsidian`, `chatgpt`, `gemini`. Untagged inputs auto-detect by extension (`.md` -> Obsidian, `.json` -> export auto-detect, else JSONL). Every new parser yields dicts keyed `ts`/`role`/`text`, so the existing normalization, filtering, snippet truncation, and digest assembly are reused unchanged - JSONL behavior is byte-for-byte identical.

## Source formats

### Obsidian vault notes

- **Discovery**: locate vault roots by the `.obsidian/` marker (bounded depth) under a root; emit each `*.md` note (excluding the `.obsidian/` internal dir). Fallback: a plain `*.md` folder with no marker. Default root `~/Documents`; `--root` for the real vault.
- **Parse**: minimal frontmatter scan (no YAML lib) for a timestamp (`updated`/`modified`/`date`/`created`, else file mtime) and `title` (frontmatter `title` or filename stem); split the body into ATX-heading sections - one record per section so headings, body, and `[[backlinks]]` all become searchable snippets; a leading title record carries the note title and tags.

### Exported ChatGPT history

- **On disk**: `conversations.json` - a list of conversation objects, each with `title`, `create_time` (epoch seconds), and a `mapping` of message nodes (`message.author.role`, `message.content.parts`, `message.create_time`). A `messages` list shape is also accepted.
- **Parse**: one record per message; role from `author.role`, text joined from `content.parts`, epoch `create_time` -> ISO; the conversation title is prepended to the first message.

### Exported Gemini history

- **On disk**: Google Takeout "My Activity" JSON - a list of activity entries with ISO `time`, `title` (the prompt text), and optional `subtitles`/`details`.
- **Parse**: one record per entry; `ts` from `time`, text from `title` plus any subtitle/detail names, role `user`.

## Source-selection mechanism (default behavior unchanged)

The new sources are opt-in. The no-`--tool` "scan all" pass stays Claude+Codex+Cursor JSONL only; `obsidian`/`chatgpt`/`gemini` are reached solely via explicit `--tool` (with the default roots above) or `--root`. When a source is absent, nothing is emitted. ChatGPT/Gemini default roots (`~/Downloads`) use a narrow canonical-name match (`conversations.json`, `*ctivity*.json`) to avoid emitting unrelated JSON; an explicit `--root` emits all `*.json`/`*.md`.

## Cross-platform parity note

Windows PowerShell `ConvertFrom-Json` unrolls a single-element array to a scalar, so ChatGPT `content.parts` (and single-entry exports / single `subtitles`) arrive as a string, not an array. Python's `json` never unrolls. The `.ps1` parsers therefore accept both a string and an enumerable for these fields, so both languages produce the same digest on the same input. This is a behavioral-parity accommodation, not a logic divergence.

## Constraint

Zero new outbound call, dependency, or credential. Every parser uses only `json`/`pathlib`/`datetime` (already imported); the discovery scripts walk the filesystem only.
