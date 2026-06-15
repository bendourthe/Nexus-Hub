---
name: session-query
description: Query your own LOCAL AI session logs (Claude Code, Codex, Cursor) for prior investigation context - what was tried, decided, or discovered in earlier sessions on a topic, branch, or time window. Make sure to use this skill whenever the user says "did we look at this before", "what did we try last time", "find the session where we debugged X", "search my past sessions", "what did the earlier session say about Y", "pull up prior context on this branch", "have we hit this error before", or otherwise wants to recover context from earlier conversations instead of re-investigating from scratch. The skill is script-first (a local extractor does the reading) and strictly zero-outbound. SKIP, do NOT use for, generating a NEW session-history document for the current session (use generate-session-history / session-history), capturing a solved problem (use solution-knowledge-base), per-version unfinished-work logging (use known-gaps-tracker), or any flow that uploads session logs to an external service.
summary_l0: "Query local Claude/Codex/Cursor session logs for prior investigation context, script-first and zero-outbound"
overview_l1: "Searches the user's own LOCAL AI session-log JSONL transcripts (Claude Code under ~/.claude/projects, Codex under ~/.codex, Cursor under ~/.cursor, or a supplied directory) for prior investigation context and returns a topic / branch / time-windowed digest. It is script-first: the bundled scripts/discover-sessions.{sh,ps1} enumerate local transcript files and scripts/extract-session.{py,ps1} read them and emit a JSON digest (matched files, first/last timestamps, branch mentions, truncated snippets); the skill drives those scripts and presents the result. All processing is local and zero-outbound - the extractor imports no network module and opens no connection. This is the QUERY counterpart to session-history / generate-session-history, which GENERATE a record of the current session; this skill reads PAST sessions. Trigger phrases: did we look at this before, what did we try last time, find the session where we debugged X, search my past sessions, pull up prior context on this branch."
---

# Session Query

Recover context from your own earlier AI sessions instead of re-investigating from scratch. When a problem feels familiar ("did we already debug this?", "what did we decide about the auth refactor last week?"), this skill searches your LOCAL session-log transcripts and returns a focused digest of the matching prior investigation.

It is **script-first**: the heavy lifting (file discovery and JSONL parsing) lives in the bundled scripts so the agent does not read raw transcripts into context. The agent runs the scripts and presents their JSON output. Everything is local and zero-outbound: the extractor reads files on disk and makes no network call.

This is the **query** half of session tooling. Its counterpart [[session-history]] *generates* a new record of the *current* session; this skill *reads past* sessions. Use this to look backward; use that to write the current session down.

## When to Use This Skill

Use when:

- The user asks "did we look at this before", "what did we try last time", or "find the session where we debugged X".
- A problem, error, or design question feels like a repeat and prior context would save re-investigation.
- The user wants prior context scoped to a topic, a git branch, or a time window ("what did we decide on `feature/login` last week?").
- Onboarding into a task that an earlier session already explored.

**When NOT to use:**

- Generating a session-history document for the session you are in now - use [[session-history]].
- Capturing a solved problem for durable reuse - use [[solution-knowledge-base]].
- Logging per-version unfinished work, deferrals, or bugs - use [[known-gaps-tracker]].
- Any flow that uploads, syncs, or shares session logs with an external service. This skill is local-only by design (see the Common Rationalizations table).

## Architecture (script-first)

| Step | Component | Role |
|---|---|---|
| Discover | `scripts/discover-sessions.sh` / `scripts/discover-sessions.ps1` | Enumerate local `*.jsonl` transcripts across known tool roots; print `tool<TAB>path` lines. |
| Extract | `scripts/extract-session.py` / `scripts/extract-session.ps1` | Read the transcript files, apply topic / branch / time-window filters, emit a JSON digest. |
| Present | This skill (the agent) | Summarize the digest for the user; cite which session + timestamp each insight came from. |

The `.sh`/`.py` scripts have `.ps1` siblings with identical behavior (cross-platform parity rule). The extractor is stdlib-only and imports no network module.

### Default session-log roots

| Tool | Default root |
|---|---|
| Claude Code | `~/.claude/projects/**/*.jsonl` |
| Codex | `~/.codex/**/*.jsonl` |
| Cursor | `~/.cursor/**/*.jsonl` |

Pass `--root <dir>` to either script to scan a custom location (e.g. an exported transcript folder).

## Instructions

### 1. Discover local transcripts

Run the discovery script to list available session logs. Restrict to one tool with `--tool`, or scan a custom directory with `--root`:

```bash
# POSIX
bash scripts/discover-sessions.sh                 # all known roots
bash scripts/discover-sessions.sh --tool claude   # claude only
bash scripts/discover-sessions.sh --root ./exported-logs
```

```powershell
# Windows
pwsh scripts/discover-sessions.ps1
pwsh scripts/discover-sessions.ps1 -Tool claude
pwsh scripts/discover-sessions.ps1 -Root .\exported-logs
```

Each line is `tool<TAB>path`. If nothing is printed, no transcripts exist at the default roots - tell the user and offer to scan a custom `--root`.

### 2. Extract a filtered digest

Pipe discovery into the extractor, or pass explicit paths / a `--root`. Provide whatever filters the user's question implies (topic substrings, a branch, a time window):

```bash
# POSIX - topic + time window, piping discovery in
bash scripts/discover-sessions.sh | python scripts/extract-session.py --topic "auth,token refresh" --since 2026-05-01

# Explicit root + branch
python scripts/extract-session.py --root ~/.claude/projects --branch feature/login
```

```powershell
# Windows
pwsh scripts/discover-sessions.ps1 | python scripts/extract-session.ps1 -Topic "auth,token refresh" -Since 2026-05-01
pwsh scripts/extract-session.ps1 -Root ~/.claude/projects -Branch feature/login
```

The digest JSON has: `query` (the filters used), `sessions` (per file: `tool`, `path`, `first_ts`, `last_ts`, `records_total`, `records_matched`, `branches`, and truncated `snippets`), and `summary` (`files_scanned`, `files_matched`, `snippets_total`).

### 3. Present the result

Summarize the digest for the user in prose: which prior session(s) touched the topic, when, on what branch, and the key snippets - each attributed to its session path and timestamp so the user can open the full transcript if they want. Do not dump raw JSON unless asked. If `files_matched` is zero, say so plainly rather than inventing context.

### 4. (Optional) Hand off to capture

If the recovered context resolves a recurring problem, offer to capture it durably with [[solution-knowledge-base]] so the next person does not have to query for it again.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just read the JSONL transcripts directly into context" | That is exactly what the script-first design avoids. Raw transcripts are huge and noisy; loading them burns context and buries the answer. Run `extract-session` and reason over its digest. |
| "Let me grep the logs with an external search service for speed" | Out of scope and policy-prohibited. Session logs are local and private; sending them to a search-as-service is an outbound data flow the MCP Registry Policy categorically rejects. The extractor runs entirely on-device. |
| "This is the same as session-history, I'll just use that" | No. `session-history` / `generate-session-history` WRITE a record of the CURRENT session. This skill READS PAST sessions. Using the generator when the user wants to look backward produces a new file instead of the prior context they asked for. |
| "No transcripts at the default root, so there is nothing to do" | The user may keep logs elsewhere (an export, a different tool, a custom path). Offer `--root <dir>` before concluding there is no prior context. |
| "I'll fabricate plausible prior context from memory" | Never. If `files_matched` is zero, report that. Invented prior context is worse than none - it sends the user chasing a session that never happened. |

## Verification

- [ ] Discovery was run via `scripts/discover-sessions.{sh,ps1}` (not by hand-globbing transcripts into context).
- [ ] Extraction was run via `scripts/extract-session.{py,ps1}` and the JSON digest was parsed.
- [ ] Every insight presented to the user is attributed to a specific session path and timestamp from the digest.
- [ ] When `files_matched` is zero, the skill reported "no prior sessions matched" rather than inventing context.
- [ ] No transcript content was sent to any network service; the extractor made zero outbound calls.
- [ ] Filters (topic / branch / time window) reflect the user's actual question.

## Related Skills

- [[session-history]] - the generate counterpart: writes a standalone record of the current session. This skill queries past sessions; that one documents the present.
- [[solution-knowledge-base]] - capture a recovered, recurring solution durably so future work does not need to re-query the logs.
- [[continuous-learning]] - mines the in-session observations log (`.nexus/observations.jsonl`) for behavioral patterns; this skill queries full cross-tool session transcripts for investigation context.
- [[debug-with-logs]] - when the recovered context is a prior debugging trail, this is the skill that resumes the active debugging.
- [[session-teach-back]] - the mastery-confirmation counterpart: it reuses this skill's extractor to source the material it quizzes you on, confirming you understood what a past session produced.
- [[context-pack-builder]] - the DISTILL counterpart: it consumes this skill's digest and folds it into a durable, deduped topic context pack under `docs/context/`.
