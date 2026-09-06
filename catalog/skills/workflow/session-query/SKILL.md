---
name: session-query
description: Query your own LOCAL prior-context sources (Claude Code / Codex / Cursor session logs, Obsidian vault notes, and exported ChatGPT/Gemini history) for prior investigation context - what was tried, decided, or discovered earlier on a topic, branch, or time window. Make sure to use this skill whenever the user says "did we look at this before", "what did we try last time", "find the session where we debugged X", "search my past sessions", "what did the earlier session say about Y", "pull up prior context on this branch", "have we hit this error before", "search my Obsidian notes", "what did I ask ChatGPT/Gemini about this", or otherwise wants to recover context from earlier conversations or notes instead of re-investigating from scratch. The skill is script-first (a local extractor does the reading) and strictly zero-outbound. SKIP, do NOT use for, generating a NEW session-history document for the current session (use generate-session-history / session-history), capturing a solved problem (use solution-knowledge-base), per-version unfinished-work logging (use known-gaps-tracker), or any flow that uploads session logs to an external service.
summary_l0: "Query local AI session logs, Obsidian notes, and exported chat history for prior context, zero-outbound"
overview_l1: "Searches the user's own LOCAL prior-context sources and returns a topic / branch / time-windowed digest. Sources: AI session-log JSONL transcripts (Claude Code under ~/.claude/projects, Codex under ~/.codex, Cursor under ~/.cursor), Obsidian vault notes (.md with frontmatter, headings, and [[backlinks]]), and exported ChatGPT (conversations.json) / Gemini (Google Takeout) history -- or any supplied directory. It is script-first: bundled scripts/discover-sessions.{sh,ps1} enumerate local source files and scripts/extract-session.{py,ps1} parse them per source type into one JSON digest (matched files, first/last timestamps, branch mentions, truncated snippets); the skill drives those scripts and presents the result. All processing is local and zero-outbound -- the extractor imports no network module and opens no connection. This is the QUERY counterpart to session-history / generate-session-history (which GENERATE a record of the current session); this skill reads PAST sessions and notes."
---

# Session Query

Recover context from your own earlier AI sessions and notes instead of re-investigating from scratch. When a problem feels familiar ("did we already debug this?", "what did we decide about the auth refactor last week?", "didn't I write an Obsidian note on this?"), this skill searches your LOCAL prior-context sources and returns a focused digest of the matching prior investigation.

It reads four local source types into one normalized digest: **AI session-log JSONL** transcripts (Claude Code, Codex, Cursor), **Obsidian vault notes**, **exported ChatGPT history** (`conversations.json`), and **exported Gemini history** (Google Takeout "My Activity" JSON). The session-log tools are scanned by default; the other three are opt-in via `--tool` so default behavior is unchanged.

It is **script-first**: the heavy lifting (file discovery and per-source parsing) lives in the bundled scripts so the agent does not read raw transcripts or notes into context. The agent runs the scripts and presents their JSON output. Everything is local and zero-outbound: the extractor reads files on disk and makes no network call.

This is the **query** half of session tooling. Its counterpart [[session-history]] *generates* a new record of the *current* session; this skill *reads past* sessions. Use this to look backward; use that to write the current session down.

## When to Use This Skill

Use when:

- The user asks "did we look at this before", "what did we try last time", or "find the session where we debugged X".
- A problem, error, or design question feels like a repeat and prior context would save re-investigation.
- The user wants prior context scoped to a topic, a git branch, or a time window ("what did we decide on `feature/login` last week?").
- The user wants to search their own Obsidian vault notes ("didn't I write a note on this?", "search my Obsidian vault for the auth design").
- The user wants to recover what they asked another assistant ("what did I ask ChatGPT about this?", "pull up my Gemini history on rate limiting") from a LOCAL export they already downloaded.
- Onboarding into a task that an earlier session already explored.

**When NOT to use:**

- Generating a session-history document for the session you are in now - use [[session-history]].
- Capturing a solved problem for durable reuse - use [[solution-knowledge-base]].
- Logging per-version unfinished work, deferrals, or bugs - use [[known-gaps-tracker]].
- Any flow that uploads, syncs, or shares session logs with an external service. This skill is local-only by design (see the Common Rationalizations table).

## Architecture (script-first)

| Step | Component | Role |
|---|---|---|
| Discover | `scripts/discover-sessions.sh` / `scripts/discover-sessions.ps1` | Enumerate local source files across known roots; print `tool<TAB>path` lines (the `tool` tag selects the parser downstream). |
| Extract | `scripts/extract-session.py` / `scripts/extract-session.ps1` | Parse each file by its source type (JSONL, Obsidian, ChatGPT, Gemini), apply topic / branch / time-window filters, emit one JSON digest. |
| Present | This skill (the agent) | Summarize the digest for the user; cite which session / note + timestamp each insight came from. |

The `.sh`/`.py` scripts have `.ps1` siblings with identical behavior (cross-platform parity rule). The extractor is stdlib-only and imports no network module.

### Sources and default roots

| Source | `--tool` | Default root | Files | Scanned by default? |
|---|---|---|---|---|
| Claude Code | `claude` | `~/.claude/projects` | `*.jsonl` | Yes |
| Codex | `codex` | `~/.codex` | `*.jsonl` | Yes |
| Cursor | `cursor` | `~/.cursor` | `*.jsonl` | Yes |
| Obsidian vault | `obsidian` | `~/Documents` (vault detected by the `.obsidian/` marker) | `*.md` | No (opt-in) |
| ChatGPT export | `chatgpt` | `~/Downloads` (`conversations.json`) | `*.json` / `*.md` | No (opt-in) |
| Gemini export | `gemini` | `~/Downloads` ("My Activity" JSON) | `*.json` / `*.md` | No (opt-in) |

The three JSONL session-log tools are scanned when no `--tool` is given, so default behavior is unchanged. The Obsidian / ChatGPT / Gemini sources are opt-in via `--tool` (which uses the default root above) or `--root <dir>` for the real location (e.g. your vault, or the folder you downloaded the export into). When a source is absent, nothing is emitted.

## Instructions

### 1. Discover local transcripts

Run the discovery script to list available session logs. Restrict to one tool with `--tool`, or scan a custom directory with `--root`:

```bash
# POSIX
bash scripts/discover-sessions.sh                       # claude + codex + cursor JSONL
bash scripts/discover-sessions.sh --tool claude         # claude only
bash scripts/discover-sessions.sh --tool obsidian       # Obsidian vaults under ~/Documents
bash scripts/discover-sessions.sh --root ./vault --tool obsidian
bash scripts/discover-sessions.sh --root ./chatgpt-export --tool chatgpt
```

```powershell
# Windows
pwsh scripts/discover-sessions.ps1
pwsh scripts/discover-sessions.ps1 -Tool claude
pwsh scripts/discover-sessions.ps1 -Tool obsidian
pwsh scripts/discover-sessions.ps1 -Root .\vault -Tool obsidian
```

Each line is `tool<TAB>path`, where the `tool` tag tells the extractor which parser to use. If nothing is printed, no sources exist at the default roots - tell the user and offer to scan a custom `--root` (e.g. the path to their Obsidian vault or a downloaded ChatGPT/Gemini export).

### 2. Extract a filtered digest

Pipe discovery into the extractor, or pass explicit paths / a `--root`. Provide whatever filters the user's question implies (topic substrings, a branch, a time window):

The extractor selects a parser from the per-line `tool` tag (when discovery is piped in) or from `--tool` (for explicit paths / `--root`). Untagged inputs auto-detect by extension (`.md` -> Obsidian, `.json` -> ChatGPT/Gemini, else JSONL).

```bash
# POSIX - topic + time window, piping discovery in
bash scripts/discover-sessions.sh | python scripts/extract-session.py --topic "auth,token refresh" --since 2026-05-01

# Explicit root + branch (JSONL)
python scripts/extract-session.py --root ~/.claude/projects --branch feature/login

# Obsidian vault and a downloaded ChatGPT/Gemini export (per-source --tool)
bash scripts/discover-sessions.sh --root ~/vault --tool obsidian | python scripts/extract-session.py --topic "auth"
python scripts/extract-session.py --root ~/Downloads/chatgpt --tool chatgpt --topic deploy
python scripts/extract-session.py ~/Downloads/MyActivity.json --tool gemini --topic "rate limit"
```

```powershell
# Windows
pwsh scripts/discover-sessions.ps1 | python scripts/extract-session.ps1 -Topic "auth,token refresh" -Since 2026-05-01
pwsh scripts/extract-session.ps1 -Root ~/.claude/projects -Branch feature/login
pwsh scripts/extract-session.ps1 -Root ~/vault -Tool obsidian -Topic "auth"
```

The digest JSON has: `query` (the filters used), `sessions` (per file: `tool`, `path`, `first_ts`, `last_ts`, `records_total`, `records_matched`, `branches`, and truncated `snippets`), and `summary` (`files_scanned`, `files_matched`, `snippets_total`). The shape is identical across all four source types.

### 3. Present the result

Summarize the digest for the user in prose: which prior session(s) or note(s) touched the topic, when, on what branch, and the key snippets - each attributed to its source path and timestamp so the user can open the full transcript or note if they want. Do not dump raw JSON unless asked. If `files_matched` is zero, say so plainly rather than inventing context.

### 4. (Optional) Hand off to capture

If the recovered context resolves a recurring problem, offer to capture it durably with [[solution-knowledge-base]] so the next person does not have to query for it again.

### 5. Mine unrealized compression savings (optional)

When the user asks what command output is still bloating context, read the local passthrough log rather than loading raw transcripts.

The compressor appends one JSON line to `~/.nexus-hub/compressor-passthrough.jsonl` (or `$NEXUS_CCR_STORE_PATH`'s sibling `passthrough.jsonl`, or `$NEXUS_COMPRESSOR_PASSTHROUGH_LOG`) whenever `compress` kept the original blob. Each line is `ts`, `kind=passthrough`, `tokens`, `bytes`.

Count recent passthroughs, sum `tokens`, and report the largest blobs. For each cluster, propose either a named reformatter (if it is git/pytest/ruff-class output) or a BYO filter file plus `python -m nexus_context_compressor trust <file>`. Do not invent savings numbers that are not in the log. The log is local and read-only for this skill.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just read the JSONL transcripts directly into context" | That is exactly what the script-first design avoids. Raw transcripts are huge and noisy; loading them burns context and buries the answer. Run `extract-session` and reason over its digest. |
| "Let me grep the logs with an external search service for speed" | Out of scope and policy-prohibited. Session logs are local and private; sending them to a search-as-service is an outbound data flow the MCP Registry Policy categorically rejects. The extractor runs entirely on-device. |
| "This is the same as session-history, I'll just use that" | No. `session-history` / `generate-session-history` WRITE a record of the CURRENT session. This skill READS PAST sessions. Using the generator when the user wants to look backward produces a new file instead of the prior context they asked for. |
| "No transcripts at the default root, so there is nothing to do" | The user may keep logs elsewhere (an export, a different tool, a custom path). Offer `--root <dir>` before concluding there is no prior context. |
| "I'll fabricate plausible prior context from memory" | Never. If `files_matched` is zero, report that. Invented prior context is worse than none - it sends the user chasing a session that never happened. |
| "Obsidian notes and chat exports are just files - I'll read them straight into context" | Same anti-pattern as raw transcripts. A vault or export can be huge; loading it burns context. Run `extract-session` with the right `--tool`; it parses each source locally and returns a filtered digest. |
| "An exported ChatGPT/Gemini history must mean uploading it somewhere to read it" | No. The extractor parses the LOCAL export file the user already downloaded (`conversations.json`, Takeout "My Activity"). It opens no connection. Pointing it at a local export is fully within the zero-outbound design. |

## Verification

- [ ] Discovery was run via `scripts/discover-sessions.{sh,ps1}` (not by hand-globbing transcripts or notes into context).
- [ ] Extraction was run via `scripts/extract-session.{py,ps1}` and the JSON digest was parsed.
- [ ] The right source was selected: JSONL by default, and `--tool obsidian|chatgpt|gemini` (or `--root`) when the user asked about notes or exported chat history.
- [ ] Every insight presented to the user is attributed to a specific source path and timestamp from the digest.
- [ ] When `files_matched` is zero, the skill reported "no prior sessions matched" rather than inventing context.
- [ ] No transcript, note, or export content was sent to any network service; the extractor made zero outbound calls across every source type.
- [ ] Filters (topic / branch / time window) reflect the user's actual question.
- [ ] Compression-savings mining, when requested, read the local passthrough JSONL and did not upload session logs.

## Related Skills

- [[session-history]] - the generate counterpart: writes a standalone record of the current session. This skill queries past sessions; that one documents the present.
- [[solution-knowledge-base]] - capture a recovered, recurring solution durably so future work does not need to re-query the logs.
- [[continuous-learning]] - mines the in-session observations log (`.nexus/observations.jsonl`) for behavioral patterns; this skill queries full cross-tool session transcripts for investigation context.
- [[debug-with-logs]] - when the recovered context is a prior debugging trail, this is the skill that resumes the active debugging.
- [[session-teach-back]] - the mastery-confirmation counterpart: it reuses this skill's extractor to source the material it quizzes you on, confirming you understood what a past session produced.
- [[context-pack-builder]] - the DISTILL counterpart: it consumes this skill's digest and folds it into a durable, deduped topic context pack under `docs/context/`.
