---
name: solution-knowledge-base
description: Capture a problem you just solved (a bug fix or a durable lesson) into a categorized, reusable docs/solutions/ knowledge base so future planning and review can reuse it. Make sure to use this skill whenever the user says "document how we fixed that", "save this solution", "capture this for next time", "add this to the knowledge base", "we should remember this fix", "write this up so we don't hit it again", or whenever a non-trivial bug, gotcha, or hard-won insight has just been resolved and is worth persisting. Also trigger right after a debugging session ends with a root cause found. SKIP, do NOT use for, in-session todo tracking (use dev-progress-tracker), per-version unfinished-work logging (use known-gaps-tracker), minting in-session behavioral instincts (use continuous-learning), or any request to send the captured solution to an external service or shared store.
summary_l0: "Document a solved problem into a categorized docs/solutions/ knowledge base for future reuse"
overview_l1: "Captures a recently solved problem into docs/solutions/<category>/<slug>.md so the knowledge survives the session and feeds future planning and review. Each entry uses a two-track frontmatter contract (bug track: symptoms / root_cause / resolution_type; knowledge track: applies_when) with a generic, framework-agnostic component taxonomy defined in references/schema.md. The skill runs parallel read-only research (a context analyzer, a solution extractor, and a related-docs finder that each return text only), then a single orchestrator writes exactly one file. Before writing, a 5-dimension overlap score decides whether to update an existing entry or create a new one. A Discoverability Check surfaces the store in AGENTS.md / CLAUDE.md via a dedicated marker block that never clobbers installer-managed content. Everything is local and zero-outbound. Trigger phrases: document how we fixed that, save this solution, capture this for next time, add to the knowledge base."
---

# Solution Knowledge Base

Turn a problem you just solved into a durable, categorized entry under `docs/solutions/` so the next plan, the next reviewer, and the next debugging session can find it. This is the capture half of a compound knowledge loop: solved problems become grounding for future work. The lifecycle half (Keep / Update / Consolidate / Replace / Delete) lives in [[solution-refresh]].

Everything this skill does is local and zero-outbound: it reads the current session / repo and writes one Markdown file. It never uploads the solution, never calls an external model, and never shares across projects.

## When to Use This Skill

Use when:

- A non-trivial bug was just fixed and the root cause is understood (capture it before the context is lost).
- A hard-won insight about how the system behaves emerged ("the installer copies scripts by explicit name", "this API silently truncates on `#`").
- The user says "document how we fixed that", "save this solution", "capture this for next time", or "add this to the knowledge base".
- A debugging or investigation session is wrapping up with a concrete resolution.

**When NOT to use:**

- In-session todo / progress tracking - use [[dev-progress-tracker]].
- Per-version unfinished work, deferrals, and bugs left open - use [[known-gaps-tracker]].
- Minting lightweight in-session behavioral instincts from your own corrections - use [[continuous-learning]].
- Any flow that sends the captured solution to an external service, a shared team store, or a hosted knowledge base. This skill is local-only by design (see the Common Rationalizations table).

## Storage Layout

| Path | Written by | Read by | Lifecycle |
|---|---|---|---|
| `docs/solutions/<category>/<slug>.md` | This skill | Planning / review grounding; [[solution-refresh]] | Persistent; audited by `solution-refresh`. |
| `docs/solutions/README.md` | This skill (on first write) | Humans | A one-line index row per entry. |
| Marker block in `AGENTS.md` / `CLAUDE.md` | This skill (Discoverability Check) | The agent on future sessions | Idempotently merged; never clobbers other content. |

The field contract, controlled enums, category mapping, and the parser-safety quoting rule live in [references/schema.md](references/schema.md). Read it before writing your first entry in a repo.

## Instructions

### 1. Run parallel read-only research (text only)

Gather the raw material with three read-only passes. Each pass RETURNS TEXT; none of them writes a file. Only the orchestrator (step 4) writes, and it writes exactly one file. Keeping research read-only is what prevents half-written or duplicated entries.

1. **Context analyzer**: from the current session, the git diff (`git diff`, `git log -n 20 --oneline`), and the conversation, extract *what problem was solved* - the observable symptoms or the question that was answered.
2. **Solution extractor**: extract *the concrete resolution* - the specific change, command, or insight that resolved it, in enough detail that a future reader can apply it without re-deriving it.
3. **Related-docs finder**: search `docs/solutions/` (and the repo) for entries that might already cover this, returning their slugs, categories, components, and tags. This feeds the overlap score in step 3.

You may run these as three subagents or as three sequential read passes; either way they only read.

### 2. Classify the entry

Decide, per [references/schema.md](references/schema.md):

- **Track**: `bug` (a defect that was fixed) or `knowledge` (a durable lesson / how-it-works insight).
- **Category**: the top-level directory (`bug`, `performance`, `security`, `integration`, `build`, `infra`, `data`, `api`, `ui`, `tooling`, `process`, `knowledge`).
- **Component**: one value from the generic, framework-agnostic taxonomy (`backend`, `frontend`, `database`, `api`, `auth`, `build`, `ci`, `infra`, `testing`, `tooling`, `docs`, `performance`, `security`, `dependency`). Never invent framework-specific component names.

### 3. Score overlap (update vs create)

Before writing, score the new entry against each candidate the related-docs finder returned, across five dimensions (1 point each):

1. **Same category** as the candidate.
2. **Same component** as the candidate.
3. **Title / symptom token overlap** is high (the same failure or topic).
4. **Same root-cause family** (bug track) or **same `applies_when` scope** (knowledge track).
5. **Tag overlap** of two or more tags.

Decision:

- Score **>= 4**: UPDATE the existing entry (merge the new detail, bump `updated`). Do not create a duplicate.
- Score **2-3**: ask the user whether to update the existing entry or create a new cross-linked one.
- Score **0-1**: CREATE a new entry.

### 4. Write exactly one file

Write `docs/solutions/<category>/<slug>.md` with parser-safe frontmatter (apply the YAML-safety quoting rule from [references/schema.md](references/schema.md): quote any scalar containing ` #` or `: `, quote reserved-indicator list items, keep `---` delimiters clean). The body holds: the context, the resolution in reusable detail, and (bug track) how to recognize a recurrence. Set `created` and `updated` to today; on an UPDATE, bump only `updated`.

Then add or update the one-line index row in `docs/solutions/README.md` (create it if absent): `| <slug> | <category> | <component> | <track> | <title> |`.

### 5. Discoverability Check

So future planning and review actually find the store, ensure `docs/solutions/` is pointed to from the repo's agent-instruction file(s) (`AGENTS.md` and/or `CLAUDE.md`). Insert or refresh a dedicated marker block - use a distinct marker pair so it never collides with or clobbers the installer-managed `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->` section:

```markdown
<!-- NEXUS_SOLUTIONS_START -->
## Solved-problem knowledge base

Before planning or reviewing, search `docs/solutions/` for prior solutions to the problem at hand.
Capture new solutions with the `solution-knowledge-base` skill; audit them with `solution-refresh`.
<!-- NEXUS_SOLUTIONS_END -->
```

Merge semantics: if both markers exist, replace the slice between them; otherwise append the block after a trailing blank line. Never overwrite content outside this marker pair, and never touch the installer's `NEXUS_HUB` block.

### 6. (Optional) Validate parser-safety

Run `python scripts/validate_solution_frontmatter.py docs/solutions/<category>/<slug>.md`. Exit 0 means the frontmatter is parser-safe; a non-zero exit names the offending field to fix.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This fix is obvious, I'll remember it" | You will not, and neither will the next agent or teammate. The whole point of the store is that solved problems stop being re-solved. A two-minute capture saves an hour the next time the symptom reappears. |
| "I'll just write a quick note, frontmatter is overkill" | The frontmatter is what makes the entry *retrievable*. Planning grounding and `solution-refresh` query `track`, `category`, `component`, and `tags`. A bodied note with no frontmatter is invisible to the loop. |
| "Let me create a new entry, searching for duplicates is slow" | Duplicates fragment the knowledge base and the overlap score in step 3 is cheap. Two entries for the same root cause means the next reader finds one and misses the other. Always run the related-docs finder. |
| "I should push this to our team wiki / a hosted KB so everyone sees it" | Out of scope and against the local-only design. This skill writes to the repo's `docs/solutions/` only. Syncing to an external store is an outbound data flow the MCP Registry Policy governs; if the team wants that, they wire it explicitly, not through this skill. |
| "I'll let the research subagents write the file directly to save a step" | That is how you get half-written or duplicated entries. Research is read-only; the single orchestrator write in step 4 is the only writer, after the overlap score decides update-vs-create. |
| "Framework-specific component names are more precise (model / controller)" | They break cross-project retrieval and the schema's controlled taxonomy. Map them onto the generic set (`database`, `backend`, `api`, ...). Precision that no query can match is not precision. |

## Verification

- [ ] Exactly one file was written under `docs/solutions/<category>/<slug>.md` (no duplicate, no half-written research artifact).
- [ ] The frontmatter declares `track` (`bug` or `knowledge`) and every required field for that track per [references/schema.md](references/schema.md).
- [ ] `component` is a value from the generic taxonomy (not a framework-specific name).
- [ ] `python scripts/validate_solution_frontmatter.py <the new file>` exits 0.
- [ ] The 5-dimension overlap score was computed and update-vs-create was decided accordingly (no blind duplicate).
- [ ] `docs/solutions/README.md` has a one-line index row for the entry.
- [ ] `AGENTS.md` / `CLAUDE.md` contains the `<!-- NEXUS_SOLUTIONS_START -->` ... `<!-- NEXUS_SOLUTIONS_END -->` block, and no content outside that block (especially the installer's `NEXUS_HUB` block) was modified.
- [ ] No network call, upload, or external store write occurred.

## Related Skills

- [[solution-refresh]] - the lifecycle half (Keep / Update / Consolidate / Replace / Delete) that audits and maintains these entries over time.
- [[known-gaps-tracker]] - records per-version unfinished work; a resolved gap can graduate into a `docs/solutions/` entry via this skill.
- [[continuous-learning]] - mints lightweight in-session behavioral instincts (`.nexus/instincts/`); this skill captures durable, bodied solved-problem docs - the heavier, longer-lived sibling.
- [[generate-plan]] - reads `docs/solutions/` as grounding before designing, closing the capture -> plan loop.
- [[debug-with-logs]] - a debugging session that ends with a root cause is the canonical trigger to capture here.
