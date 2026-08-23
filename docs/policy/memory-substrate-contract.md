# Memory Substrate Contract

Decision date: 2026-07-28. The `nexus-memory` store is the durable, cross-platform source of truth for persistent agent memory. A harness-native memory surface (for example Claude Code's per-project memory directory and its `MEMORY.md` index) is a platform-specific INDEX that points into the substrate. It is never a competing store.

This file is the design the storage engine (Phase 3) and the compression tree (Phase 4) implement against. It names no upstream project.

## What belongs where

**Substrate** (chronological, append-only): facts, decisions, and events with lasting effect. Examples: a design choice and why the alternative lost; a broken assumption that later work must not repeat; a user preference that survives the session. The default root is user-scoped. A root inside a git working tree is refused unless `NEXUS_MEMORY_ALLOW_IN_REPO=1`.

**Harness-native index**: pointers into the substrate (paths, entry ids, "read this first" links) and preferences that only that harness reads (keybindings, hook toggles, model pins). Never a second copy of a substrate fact.

## Session-start read order

1. Read the substrate (paged through the Phase 1 helper, within the caller's line budget).
2. Read the harness-native index, if the current host has one.
3. Treat index entries as pointers. Follow them into the substrate; do not treat the index as a second narrative.

## Conflict rule

When the substrate and a harness-native index make claims about the same fact, the **substrate wins**. The index is repaired to point at the substrate entry, not the other way around. Two surfaces must never both claim ownership of the same substrate entry.

## Distinction from existing memory-adjacent skills

| Skill | What it still owns | Why it is not the substrate |
|---|---|---|
| `session-query` | Searching past session logs and exported chats | Retrospective and query-driven. Requires the user to ask. |
| `context-pack-builder` | Distilling digests into topic packs under `docs/context/` | Manual, on-demand, topic-organized. Downstream of `session-query`. |
| `continuous-learning` | Minting behavioral instincts (how to behave) | Stores rules, not what happened. Clustering is on-demand. |
| `solution-knowledge-base` | Capturing one solved problem as a reusable solution | One-shot, problem-scoped. Not a chronological store. |

Skill routing: a request to remember, recall, or wake persistent memory goes to `agent-memory` (Phase 5). A request to search old chats, pack a topic, mint an instinct, or file a solved problem stays with the skill in the table.

## Compression protocol

The store never calls a model. When a merge is due, the tool emits one request and waits. Nothing runs in a background process. Merges are surfaced one at a time.

Each request contains:

1. The identifier of the range being compressed (`lo`, `hi`).
2. The content to compress: the raw entries for a small range, or the two child summaries for a larger one.
3. The maximum character length of the result.
4. The instruction: keep what has lasting effect; invent nothing.
5. The exact command the agent must run to return the summary (a resolved, self-named path from Phase 1.3).

**Missing or blank child.** If a child summary required for a larger merge is missing or blank, the tool refuses. It does not fabricate. It prints the exact recovery command (usually: rebuild the missing child, or `drop` the bad summary and merge again).

**Cache invariant.** The summary tree is a pure cache and must be fully rebuildable from the log alone. Deleting the tree loses no information.

## Provenance invariant

Every new `record` write must carry a `source`. The store rejects a write that cannot name one. Pre-provenance rows are readable as `source: legacy-import` and must not be rewritten. Mutations append to `changelog.log` (`added`, `superseded`, `archived`). A superseded or archived entry is marked, never deleted. Maintenance is preview-first (`maintain`, then `maintain --apply`) and copies a backup before appending archival rows.

File-backed notes follow `catalog/memory/record.md`. ADRs in `catalog/memory/decisions.md` require a **Source** field and an append-only changelog. `scripts/check_memory_provenance.py` gates the templates in `make validate` and CI.

## Subagent write exclusion

Parallel top-level sessions on one machine are the same identity and may all write the substrate. A spawned subagent must never write: it cannot judge what is already known, and its entries would arrive duplicated and out of context.

A spawning agent MUST include this exact line in the subagent prompt:

`Do not write to persistent agent memory. You are a spawned subagent; only the parent session may record memory.`

The same clause is in `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md`.

## Tier-1 token budget

The always-loaded integration prose (the block that tells an agent to read memory at startup and record entries while working) lives at `docs/policy/memory-integration-prose.md`.

**Budget: 500 tokens.** Always-loaded text is paid on every session, on every platform. 500 tokens is enough for read-on-start, write-during-work, the one-line subagent rule, and one recovery command, and is small enough that the block cannot quietly become a second AGENTS.md. `scripts/check_memory_integration_budget.py` enforces the cap in `make validate` and CI. Token counting prefers `tiktoken` when it is already available locally and degrades to a deterministic stdlib estimate otherwise, so the guard never requires a network call. The script is repo-internal (`DEV_ONLY_SCRIPTS`); it is not installer-copied.
