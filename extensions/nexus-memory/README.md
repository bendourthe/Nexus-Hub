# nexus-memory

> Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage.

Nexus-Hub persistent agent-memory store. An append-only, fixed-width log of short entries that an agent writes continuously and reads in full at session start within a caller-supplied budget. Older ranges collapse through an age-decaying summary tree; **compression is performed by the calling agent, never by this package**.

**Policy compliance**: Python standard library only at runtime, zero outbound calls, zero API keys, zero model downloads. Governed by the [MCP Registry Policy](../../AGENTS.md) in the repo root; classified `already-local` in the [Reverse-Engineering Matrix](../../docs/policy/mcp-reverse-engineering-matrix.md). The store never imports a network module and never calls a model. When a merge is due, the tool emits a compression request and the exact command to return the result; the calling agent performs the summarization.

The relationship to harness-native memory (an index, not a competing store) is in [`docs/policy/memory-substrate-contract.md`](../../docs/policy/memory-substrate-contract.md).

## Why fixed-width records

Every log record is padded to a constant byte width, so record *N* lives at offset *N* times the width. Every lookup is one seek. There is no index file to keep in sync. The on-disk cost is roughly 2x versus a packed log; constant-time access and crash-safe repair (a non-integral tail is truncated, complete prior records are never touched) are worth that cost.

## Store location

The default root is a **local, user-scoped** path (`~/.nexus-hub/memory/`), never a project directory. `NEXUS_MEMORY_ROOT` relocates it, for a synced folder.

A root inside a git working tree is **refused** unless `NEXUS_MEMORY_ALLOW_IN_REPO=1`. That override does not encrypt the log and does not stop a later commit; it only lifts the refusal. The `memory-store-guard` hook blocks Write, Edit, and `git add` / `git commit` of store artifacts that sit inside a repository, unless the same override is set. Use the recommended ignore pattern in `gitignore.recommended` if you relocate into a repo anyway.

On POSIX, the store directory is `0700` and store files are `0600`. Content remains plaintext at rest: anyone who can read the files as that user can read the memory. Redact before any shared artifact; see [[egress-redaction]].

The read budget is a reading budget, not a storage budget. It can be changed in either direction at any time with nothing recomputed.

## Install

From the Nexus-Hub repo root:

```bash
pip install -e "extensions/nexus-memory[dev]"
```

```bash
python -m nexus_memory config show
python -m nexus_memory config set read_budget 200
python -m nexus_memory read
python -m nexus_memory record --text "a lasting fact"
python -m nexus_memory search --pattern REGEX
python -m nexus_memory zoom --lo 0 --hi 4
python -m nexus_memory drop --lo 0 --hi 2
```

## Tunables

Per-store `config.json` (created on first write) overrides:

| Key | Default | Meaning |
|---|---|---|
| `record_width` | 1024 | Bytes per log record. Existing records are never rewritten; changing this on a non-empty store is rejected. |
| `max_entry_length` | 512 | Maximum UTF-8 byte length of one entry. Longer entries are rejected, never truncated. |
| `read_budget` | 200 | Maximum lines a read may return. Changeable at any time. |
| `page_max_bytes` | 16000 | Transport paging byte cap (Phase 1, OpenClaw-tightened). |
| `page_max_lines` | 256 | Transport paging line cap (Phase 1). |

## Tests

```bash
cd extensions/nexus-memory && python -m pytest -q
```
