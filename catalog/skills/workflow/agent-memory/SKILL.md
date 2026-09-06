---
name: agent-memory
description: "Read and record lasting facts in the local persistent agent-memory store (nexus-memory) so every session starts from a chronological substrate. Make sure to use this skill whenever the user says \"read persistent agent memory\", \"wake persistent memory\", \"record this lasting fact\", \"remember this decision in nexus-memory\", \"search the memory store\", \"merge the pending memory range\", \"source provenance\", \"memory changelog\", \"supersede a memory\", or otherwise wants an always-on chronological store that is read at session start and written as work happens. SKIP, do NOT use for: searching past session logs or exported chats (use session-query); distilling digests into topic packs (use context-pack-builder); minting behavioral instincts (use continuous-learning); capturing one solved problem (use solution-knowledge-base); or designing an agent architecture's memory system (use ai-agent-development)."
summary_l0: "Read and record lasting facts in the local persistent agent-memory store"
overview_l1: "Teaches the agent to treat nexus-memory as the durable cross-platform substrate for lasting facts, decisions, and events. Every write must name a source; mutations append to a changelog; superseded rows are marked, never deleted. At session start the agent reads the store within the caller line budget. While working it records only what should survive the session. When the tool emits a merge request the agent summarizes the supplied content, invents nothing, and returns the result with the printed command. The store never calls a model, starts no background process, and lives under a user-scoped root. Spawned subagents are told not to write. Distinct from session-query, context-pack-builder, continuous-learning, and solution-knowledge-base, which stay on-demand and topic-scoped."
---

# Agent Memory

Use the local `nexus-memory` store as the always-on chronological substrate for facts, decisions, and events that should survive this session. Read it at the start of every session. Record lasting items as you work. When a merge is due, you (the agent) write the summary; the store never calls a model.

This skill is not a second copy of session logs, topic packs, instincts, or solved-problem write-ups. Those stay with the skills named in the SKIP clause.

## When to Use This Skill

Use when:

- A session is starting and persistent agent memory has not been read yet.
- The user says "read persistent agent memory", "wake persistent memory", "record this lasting fact", "remember this decision in nexus-memory", or "search the memory store".
- A design choice, broken assumption, or user preference should survive the current session.
- The store printed a merge request and you must return a summary.

**When NOT to use:**

- Searching past session logs, Obsidian notes, or exported chats - use [[session-query]].
- Distilling already-gathered digests into a topic pack under `docs/context/` - use [[context-pack-builder]].
- Minting behavioral instincts (how to behave) from corrections - use [[continuous-learning]].
- Capturing one solved problem into `docs/solutions/` - use [[solution-knowledge-base]].
- Designing how an agent architecture stores memory - use [[ai-agent-development]].

## Instructions

### 1. Read at session start

Before other tool work, run:

```bash
python -m nexus_memory read
```

If the output ends with a `# next:` trailer, fetch the next page with that exact command. Do not invent entries that the read did not return.

The default root is `~/.nexus-hub/memory/` (user-scoped, never a project directory). `NEXUS_MEMORY_ROOT` relocates it. A root inside a git working tree is refused unless `NEXUS_MEMORY_ALLOW_IN_REPO=1`. A harness-native memory file, if the host has one, is an index that points into this store; the substrate wins on conflict. See `docs/policy/memory-substrate-contract.md`.

### 2. Record lasting items only

When a fact, decision, or event should survive the session:

```bash
python -m nexus_memory record --text "the lasting item" --source "conversation-or-file"
```

Every recorded item must name a `source`. A write with no source is rejected. When importing a pre-provenance file, use `--source legacy-import`. Do not record chatter, transient todos, or anything a spawned subagent discovered in isolation.

If `record` prints a merge request, go to step 3. Otherwise continue working.

### 2b. Provenance, tiers, and maintenance

- Envelope fields: `source` (required), `tier` (`session` / `working` / `durable`), optional `derived_from`, optional `supersedes`.
- Mutations append to `changelog.log`. Supersede a fact by recording a new row that points at the old index. Never delete or rewrite the old row.
- Preview archival first: `python -m nexus_memory maintain`. Apply with `--apply`, which copies a backup and then appends `archived` changelog rows. Session-tier entries stay readable.
- File-backed notes use `catalog/memory/record.md`. ADRs in `catalog/memory/decisions.md` require a **Source** field and the same append-only changelog rule.

### 3. Answer one merge at a time

A merge request names a range, supplies the content to compress, states `max_chars`, and prints the exact return command. Summarize that content only. Keep what has lasting effect. Invent nothing. Run the printed return command with your summary.

Merges are one at a time. Nothing runs in a background process. If a child is missing or blank, run the printed recovery command; do not fabricate a child summary.

### 4. Search, zoom, drop

- Search: `python -m nexus_memory search --pattern REGEX`
- Open a summarized range: `python -m nexus_memory zoom --lo LO --hi HI`
- Discard a bad summary so the next merge rebuilds it: `python -m nexus_memory drop --lo LO --hi HI`

### 5. Subagent write exclusion

When you spawn a subagent, include this exact line in its prompt:

`Do not write to persistent agent memory. You are a spawned subagent; only the parent session may record memory.`

Parallel top-level sessions on one machine may all write. Spawned subagents may not.

### 6. Redaction and relocation

Memory content must be redacted before it enters a shared artifact; see [[egress-redaction]]. The store remains plaintext at rest and is owner-only on POSIX (`0700` / `0600`). If the store root is relocated into a repository, set `NEXUS_MEMORY_ALLOW_IN_REPO=1` and use the ignore pattern in `extensions/nexus-memory/gitignore.recommended`. The `memory-store-guard` hook blocks writes and git staging of store artifacts inside a repository unless that override is set.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I already have the conversation in context, so I can skip the session-start read." | Context is lost on compact and on the next session. An unread store is a silent empty memory. |
| "I will record this later, after the task is done." | The decision that needed recording is the one that disappears when the session ends. Record when the fact is still crisp. |
| "A merge is due, but I will batch several ranges first." | The protocol is one merge at a time. Batching invents order and drops the printed return command. |
| "The child summary is missing, so I will write a plausible stand-in." | A fabricated child poisons every ancestor. Run the recovery command. |
| "The subagent found a useful fact, so it should record it." | A spawned subagent cannot judge what the parent already knows. Its write arrives duplicated and out of context. |
| "This belongs in a context pack / instinct / solutions entry instead." | Those skills are on-demand and topic-scoped. Chronological lasting facts belong here. |

## Verification

- [ ] `python -m nexus_memory read` ran at session start and its output was used (or the store was empty).
- [ ] Each lasting fact, decision, or event recorded this session was written with `python -m nexus_memory record --text ... --source ...`.
- [ ] Every merge request printed this session was answered with the exact return command from that request.
- [ ] No background process was started to watch or compress the store.
- [ ] Every spawned subagent prompt contains the exact write-exclusion line.
- [ ] `python scripts/check_memory_integration_budget.py` still reports the always-loaded prose under 500 tokens.

## Related Skills

- `session-query` -- searches past session logs and exported chats; retrospective, not the chronological substrate
- `context-pack-builder` -- distills digests into topic packs under `docs/context/`
- `continuous-learning` -- mints behavioral instincts (how to behave), not what happened
- `solution-knowledge-base` -- captures one solved problem as a reusable write-up
- `multi-agent-coordinator` -- carries the same subagent write-exclusion line
- `egress-redaction` -- redacts memory content before any shared artifact
