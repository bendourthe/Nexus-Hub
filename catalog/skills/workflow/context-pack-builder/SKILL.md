---
name: context-pack-builder
description: Distill already-gathered prior-session digests and solved-problem records into a single committed, deduped, topic-organized context pack the next session, a teammate, and an agent can all load. Make sure to use this skill whenever the user says "build a context pack", "distill our sessions", "carry context forward", "give the next session a head start", "shared project context", "package what we know about X", or wants prior context turned into a durable, loadable artifact instead of re-derived. It consumes session-query / solution-knowledge-base output and does everything locally and zero-outbound. SKIP, do NOT use for, querying or searching past sessions (use session-query), capturing one solved problem (use solution-knowledge-base), writing the current session's record (use session-history), minting in-session instincts (use continuous-learning), or any flow that uploads or shares the pack with an external service.
summary_l0: "Distill prior-session digests and solutions into a reusable, deduped, topic-organized context pack"
overview_l1: "Turns already-gathered prior context into a single committed, reusable context pack so the next session, a teammate, and an agent all start with the same grounding instead of re-investigating. It is the DISTILL step downstream of session-query (which queries local session logs) and solution-knowledge-base (which captures one solved problem): the agent feeds their digests in, then distills and dedupes them by topic into docs/context/<topic>.md, where every fact cites its source session and timestamp, open questions are tracked, and links point to the relevant solution docs. A docs/context/README.md index lists every pack. Distillation and merge are LLM-driven judgment, so no script ships; everything is local and zero-outbound, with no new dependency or credential. Trigger phrases: build a context pack, distill our sessions, carry context forward, give the next session a head start, shared project context."
---

# Context Pack Builder

Turn the prior context you have already gathered into a single, durable, loadable artifact. When a topic spans several past sessions and a couple of solved-problem write-ups, this skill distills all of it into one deduped, topic-organized "context pack" under `docs/context/` so the next session, a teammate, and an agent all open with the same grounding instead of re-investigating from scratch.

This is the **distill** step in a compound context loop. Its inputs come from skills that *gather*: [[session-query]] reads your past session logs, and [[solution-knowledge-base]] captures individual solved problems. This skill consumes their output and folds it into a topic-level pack. Everything it does is local and zero-outbound: it reads digests and repo files and writes Markdown. It never queries logs itself, never uploads the pack, and introduces no new dependency or credential.

## When to Use This Skill

Use when:

- The user says "build a context pack", "distill our sessions", "carry context forward", "give the next session a head start", or "package what we know about X".
- A topic has accumulated context across several past sessions (recovered via [[session-query]]) and/or solved-problem records, and that context should become a durable artifact rather than something re-derived each time.
- You are about to hand a topic off to a teammate or a future session and want one file that carries the grounding.
- A long or multi-phase effort needs a stable "shared project context" file that an agent can load at the start of each phase.

**When NOT to use:**

- Querying or searching past session logs for prior context - use [[session-query]] (this skill consumes its digest; it does not produce one).
- Capturing a single solved problem or hard-won lesson - use [[solution-knowledge-base]].
- Writing a record of the session you are in right now - use [[session-history]].
- Minting lightweight in-session behavioral instincts from your own corrections - use [[continuous-learning]].
- Any flow that uploads, syncs, or shares the pack with an external service or team store. This skill is local-only by design (see the Common Rationalizations table).

## Storage Layout

Context packs are committed artifacts so a teammate and a future session can load them. They live under `docs/context/`, not `.nexus/` (which is gitignored, ephemeral, and session-scoped).

| Path | Written by | Read by | Lifecycle |
|---|---|---|---|
| `docs/context/<topic>.md` | This skill | The next session, a teammate, an agent loading grounding | Persistent; merged in place on the next distillation for the topic. |
| `docs/context/README.md` | This skill (on first write) | Humans | A one-line index row per pack. |

## Context Pack Format

Each pack is one Markdown file with parser-safe frontmatter and three body sections:

```markdown
---
topic: <topic-slug>
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_sessions:
  - path: <session path or digest source>
    timestamp: <ISO 8601 timestamp>
tags: [<tag>, <tag>]
---

# Context Pack: <Topic>

## Distilled Facts

- <atomic, deduped fact> (source: <session path> @ <timestamp>)
- <fact confirmed in two sessions lists both> (sources: <path-a> @ <ts-a>; <path-b> @ <ts-b>)

## Open Questions

- <unresolved question carried forward from the prior context>

## Links to Solutions and Related Artifacts

- `docs/solutions/<category>/<slug>.md` - <one-line on what it covers>
- `<path/to/plan-or-doc>` - <one-line>
```

Apply the standard YAML-safety quoting rule: quote any scalar containing ` #` or `: `. Keep `---` delimiters clean so the MCP server and other parsers can read the frontmatter.

## Instructions

### 1. Gather the inputs (read-only)

Collect the raw material; do not write anything yet. Each pass returns text only.

1. **Prior sessions**: run [[session-query]] for the topic (a topic / branch / time-window digest of past session logs). Use its JSON digest as the primary input - this skill does not read raw transcripts itself.
2. **Solved problems**: search `docs/solutions/` for entries on the topic ([[solution-knowledge-base]] writes them). Note their paths and the resolution each records.
3. **Current session (optional)**: if the live session added durable facts on the topic, include them too, attributed to today.

If [[session-query]] returns zero matches and no solution docs exist, tell the user there is no prior context to distill rather than inventing one.

### 2. Choose the topic and check for an existing pack

Pick a stable `kebab-case` topic slug (e.g. `auth-token-refresh`). Look for `docs/context/<topic>.md`:

- If it exists, you are **merging** into it (step 4 updates it in place) - read it first so you dedupe against what is already there.
- If it does not, you are **creating** a new pack.

### 3. Distill and dedupe by topic

This is the judgment step and the whole value of the skill:

1. Extract **atomic facts** - one finding per bullet, stated so a future reader can use it without re-deriving it.
2. **Attribute every fact** to its source session path and timestamp (or solution-doc path). A fact with no source is not admissible.
3. **Dedupe**: when the same fact appears in two sessions, write it once and list both sources on that single entry. Do not carry two bullets that say the same thing.
4. **Group by sub-topic** under `## Distilled Facts` if the topic is broad enough to warrant headings.
5. Move anything unresolved into `## Open Questions`; do not promote a guess to a fact.

### 4. Write (or merge) the context pack

Write `docs/context/<topic>.md` using the format above.

- **Create**: set `created` and `updated` to today; populate `source_sessions` from step 1.
- **Merge**: keep `created`, bump `updated` to today, append new `source_sessions` entries, and fold new facts into the existing `## Distilled Facts` - deduping against what is already there, never appending a duplicate. Resolved open questions move into Distilled Facts; new ones are added.

### 5. Update the index and link related artifacts

Add or update the one-line row in `docs/context/README.md` (create it if absent): `| <topic> | <updated> | <one-line summary> |`. In the pack's `## Links to Solutions and Related Artifacts`, link each relevant `docs/solutions/` entry and any plan or design doc, so the pack is a hub the reader can navigate from.

### 6. (Optional) Offer to load it

A context pack earns its keep when it is loaded as opening context. Offer to load `docs/context/<topic>.md` at the start of the next session or phase - see [[context-engineering]] for using it as a Layer-1 orientation artifact.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just re-run session-query each time instead of building a pack" | session-query returns a raw, unstructured digest scoped to one query; it does not dedupe across sessions or persist. The next teammate re-queries from scratch and re-derives the same conclusions. The pack is the durable, deduped distillation that survives the session. |
| "I'll paste the raw digests straight into the pack" | Raw digests are noisy and overlapping; an undeduped dump is as hard to load as the transcripts it came from. The value is the distillation - atomic, deduped, attributed facts - not a copy of the input. |
| "This fact is obvious, I don't need to cite a source session" | An unattributed fact is unverifiable: the reader cannot open the originating session to confirm it or get detail, and when it goes stale no one can trace it back. Every fact cites a source path and timestamp. |
| "A pack for this topic probably exists, but a fresh one is faster" | Duplicate packs fragment the context so the next reader finds one and misses the other. Always check `docs/context/<topic>.md` first and merge into it, deduping, rather than creating a second pack for the same topic. |
| "I'll push the pack to our team wiki so everyone sees it" | Out of scope and against the local-only design. This skill writes to the repo's `docs/context/` only. Syncing to an external store is an outbound data flow the MCP Registry Policy governs; if the team wants that, they wire it explicitly, not through this skill. |
| "session-query found nothing, so I'll reconstruct the context from memory" | Never. If there is no prior context to distill, say so. A pack of invented facts is worse than no pack - it sends the next session chasing grounding that was never established. |

## Verification

- [ ] The context pack exists at `docs/context/<topic>.md` with valid, parser-safe frontmatter (`topic`, `created`, `updated`, `source_sessions`, `tags`).
- [ ] Every distilled fact cites a source session path and timestamp (or a solution-doc path).
- [ ] Facts are deduped by topic - no two entries state the same fact; a fact seen in two sessions lists both sources on one entry.
- [ ] Inputs came from [[session-query]] / [[solution-knowledge-base]] output (or the current session), not fabricated; if no prior context existed, no pack was invented.
- [ ] `docs/context/README.md` has a one-line index row for the pack.
- [ ] When a pack for the topic already existed, it was merged in place (`updated` bumped, facts deduped) - no duplicate pack was created.
- [ ] No network call, upload, or external store write occurred, and no new dependency or credential was introduced.

## Related Skills

- [[session-query]] - the upstream QUERY step: recovers prior investigation context from local session logs. This skill distills that digest into a durable pack.
- [[solution-knowledge-base]] - captures one solved problem; this skill folds those records into a topic-level pack and links back to them.
- [[session-history]] - writes a record of the CURRENT session; this skill reads across PAST sessions to distill a topic pack. Use that to write the present, this to carry the past forward.
- [[continuous-learning]] - mints lightweight in-session instincts from your own corrections; this skill distills cross-session context into a loadable artifact - the heavier, durable sibling.
- [[context-engineering]] - decides what context to load and when; a context pack is a ready-made Layer-1 orientation artifact for that discipline.
- [[loop-engineering]] - loops persist state through the external-memory layer; a context pack is one such durable memory artifact a loop can load at each iteration.
