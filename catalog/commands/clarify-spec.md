---
description: Sequential 5-question clarification loop for an existing spec.md. Detects ambiguity across a 10-category taxonomy, asks one prioritized question per turn with a Recommended option highlighted at the top, integrates accepted answers back into the spec body and a Clarifications section. Use when a spec is written but underspecified; complements /analyze-spec (read-only audit) and /idea-refine (vague-idea-to-problem-statement). Trigger phrases: clarify the spec, drive the spec ambiguities, run the clarification loop, ask me the spec questions, 5-question clarification, spec quality questions, resolve [NEEDS CLARIFICATION] markers.
---
# Clarify Spec

Drive a sequential 5-question clarification loop against an existing spec. The command surfaces the highest-impact ambiguities in the spec body, asks them one at a time with a Recommended option highlighted at the top, and integrates each accepted answer back into the spec body plus a `## Clarifications` section.

This command is the bridge between `/analyze-spec` (read-only audit that flags ambiguity, underspecification, and missing coverage) and `/generate-plan` (which expects a spec that has already passed the spec-quality-checklist). It is destructive: it writes to the spec file after every answer. Use `/analyze-spec` first if you want a read-only inventory; use this command when you are ready to resolve the ambiguities the analyzer surfaced.

`/clarify-spec` complements `[[idea-refine]]` rather than replacing it: `idea-refine` produces a one-page problem statement from a vague request; `/clarify-spec` operates on an already-written spec.md and resolves ambiguity at the FR / SC / user-story granularity. Use `idea-refine` before writing the spec; use `/clarify-spec` after.

## How to Run This Command

- `/clarify-spec` - default. Resolves the latest spec under `docs/<version>/plans/` (or `specs/<NNN>-*/spec.md` if that layout exists from Phase 7 of the adoption-spec-kit plan).
- `/clarify-spec <path>` - explicit spec file or feature directory.
- `/clarify-spec --max-questions N` - lower the question cap (default 5; never raise above 5).

The command writes to the spec file after every accepted answer. There is no `--dry-run` flag - if you want a read-only inventory of ambiguities, run `/analyze-spec` first.

---

## Step 1: Resolve the Spec File

1. Detect the current version from the most recent git tag, `CHANGELOG.md` heading, or root manifest. Normalize to the `v` prefix form (e.g., `v2.1.0`).
2. Resolve the spec file in this priority order:
    1. The argument `<path>` if provided. If it points to a directory, look inside for `spec.md`; if it points to a file ending in `.md`, use that file directly.
    2. `.specify/feature.json` `feature_directory` field if it exists at repo root - look for `spec.md` inside.
    3. The most recently modified `specs/<NNN>-*/spec.md`.
    4. The most recently modified `docs/<version>/plans/<slug>.md` (treated as a self-contained plan + spec).
3. Confirm the resolved location with the user before proceeding.

**Abort with guidance** if no spec file is found:

```
No spec file found.

Searched (in priority order):
  1. <arg if provided>
  2. .specify/feature.json - <found or not found>
  3. specs/<NNN>-*/spec.md - <newest match or "none">
  4. docs/<version>/plans/<slug>.md - <newest match or "none">

Run /generate-plan or write a spec.md at one of these locations first.
```

---

## Step 2: Run the Structured Ambiguity Scan

Read the resolved spec file and classify each section's clarity across a 10-category taxonomy. Mark each category as **Clear** / **Partial** / **Missing**.

### The 10-Category Taxonomy

| # | Category | What "Clear" looks like |
|---|---|---|
| 1 | Functional Scope & Behavior | Every FR-### has a single, measurable verb and an Independent Test mapping. |
| 2 | Domain & Data Model | Key Entities listed with attributes; relationships explicit; no entity referenced without definition. |
| 3 | Interaction & UX Flow | User stories include Acceptance Scenarios in Given/When/Then format; primary flow covers the happy path end-to-end. |
| 4 | Non-Functional Quality Attributes | Performance, scalability, reliability, observability, security & privacy, compliance attributes have measurable thresholds where applicable. |
| 5 | Integration & External Dependencies | External APIs, queues, or services named with version constraints; auth method and rate-limit assumptions stated. |
| 6 | Edge Cases & Failure Handling | Explicit Edge Cases subsection; failure modes named with expected behavior. |
| 7 | Constraints & Tradeoffs | Constraints stated as `MUST` / `MUST NOT`; tradeoffs documented with rationale. |
| 8 | Terminology & Consistency | One canonical name per entity; no synonyms drifting across sections. |
| 9 | Completion Signals | SC-### are measurable, technology-agnostic, user-focused, and verifiable. |
| 10 | Misc / Placeholders | No `[NEEDS CLARIFICATION]` markers above the 3-cap, no `TBD` / `TODO` / `XXX` / `[ALL_CAPS]` leakage in content sections. |

Record the scan as an internal data structure (do not emit it as output yet). Use it to drive Step 3.

---

## Step 3: Generate the Prioritized Question Queue

From the scan, generate a prioritized queue of **at most 5 candidate questions**. The queue is internal - the user sees one question at a time, not the full queue.

### Prioritization rules

1. **Category priority** (matches the `[NEEDS CLARIFICATION]` marker convention from `[[spec-driven-development]]` and `[[idea-refine]]`):
    - **Scope** (Functional Scope, Domain & Data Model) - highest priority.
    - **Security / privacy** (Non-Functional Quality Attributes when security-related, Compliance).
    - **UX** (Interaction & UX Flow, Edge Cases).
    - **Technical** (Integration, Constraints, Terminology) - lowest priority.
2. **Status priority** within a category: Missing > Partial > Clear. Never ask a question about a category that scanned Clear.
3. **Impact filter**: only queue a question if its answer changes downstream artifacts (plan, data model, tasks). Skip cosmetic ambiguities - they belong in `/analyze-spec` LOW-severity findings, not the clarification loop.
4. **Balance**: cover at least 3 distinct categories across the 5 questions. Do not stack all 5 on one category - the loop's value is breadth.

### Question shape

Each candidate question must be answerable with **EITHER**:

- **Multiple choice** (2-5 options) - the agent has formed a strong prior about the most likely correct option but wants the user to confirm or override.
- **Short-phrase answer** (<=5 words) - the agent has no prior and needs the user to fill in a slot.

Questions that need a long-form answer DO NOT belong in this loop - they belong in a design doc. Re-scope to a multiple-choice or short-phrase form, or drop the question.

---

## Step 4: Sequential Questioning Loop

Present **EXACTLY ONE question at a time**. Wait for the user's answer before presenting the next. Do not batch.

### Multiple-choice question format

```markdown
**Question N of <=5** - Category: <category-name>

<one-sentence framing of the ambiguity in the spec>

**Recommended:** Option <X> - <one-sentence reasoning for why this option is the most likely fit, citing the spec / existing stack / project constitution as evidence>

| Option | Description |
|---|---|
| A | <option text> |
| B | <option text> |
| C | <option text> |
| D | <option text> (only if needed) |
| E | <option text> (only if needed) |

Reply with the option letter, accept the recommendation with `yes` or `recommended`, or provide your own short answer.
```

### Short-phrase question format

```markdown
**Question N of <=5** - Category: <category-name>

<one-sentence framing of the ambiguity in the spec>

**Recommended:** <agent's best guess, <= 5 words> - <one-sentence reasoning>

Reply with `yes` to accept, or provide your own short answer (<=5 words).
```

### Recommended-option rules

- The Recommended option **MUST** appear above the table (multiple-choice) or above the prompt (short-phrase). The agent commits to one preferred option even when uncertainty is high; "no recommendation" is not acceptable.
- The recommendation cites evidence: a specific section of the spec, an existing repo convention, a constitution principle, or the comparison report that drove the plan. Vague reasoning ("it's the most common") is not acceptable.
- The user can always override with a custom answer. The Recommended option is a starting point, not a forcing function.

### Answer acceptance rules

- `yes` / `recommended` / `accept` / `r` → accept the Recommended option.
- A single letter (A-E) → accept the corresponding option.
- A free-form short answer → use that answer literally.
- `skip` → record the question as Deferred and move to the next.
- `stop` / `done` / `good` / `no more` → end the loop early (Step 6).

---

## Step 5: Integrate the Accepted Answer

After each accepted answer, perform two updates in order. Save the spec **atomically** after EACH integration - do not batch multiple answers before saving.

### 5a. Append to the Clarifications section

Locate or create a `## Clarifications` section in the spec body (place it immediately after the front-matter / header block and before `## User Scenarios & Testing`).

Within `## Clarifications`, locate or create a `### Session YYYY-MM-DD` subheading (use today's UTC date in ISO format). Append a bullet:

```markdown
- Q: <question text> -> A: <final accepted answer>
```

Multiple sessions on different days produce multiple `### Session YYYY-MM-DD` subheadings under the same `## Clarifications` section.

### 5b. Apply the clarification to the spec body

Determine which section(s) of the spec the answer modifies, then edit in place:

| Question category | Where to apply the answer |
|---|---|
| Functional Scope & Behavior | Functional Requirements (`## Requirements`) - rewrite the relevant FR-### to remove the ambiguity. If the answer adds a new requirement, append it with the next sequential FR-### ID. |
| Domain & Data Model | `### Key Entities` subsection - add or update the entity definition. |
| Interaction & UX Flow | User Stories (`## User Scenarios & Testing`) - update the Acceptance Scenarios or add a new Given/When/Then row. |
| Non-Functional Quality Attributes | Add or update a measurable threshold in the relevant FR or in a `### Non-Functional Requirements` subsection. |
| Integration & External Dependencies | Add a constraint to the relevant FR, or create a `### External Dependencies` subsection if none exists. |
| Edge Cases & Failure Handling | `### Edge Cases` subsection. |
| Constraints & Tradeoffs | Header block or a `### Constraints` subsection. |
| Terminology & Consistency | Replace inconsistent terms across all sections (use the canonical name from the answer). |
| Completion Signals | Success Criteria (`## Success Criteria`) - update or add an SC-###. |
| Misc / Placeholders | Replace the placeholder in place; if a `[NEEDS CLARIFICATION]` marker was resolved, remove the marker entirely. |

Save the file atomically (write to a temp file, fsync, rename). Echo a short confirmation:

```
Saved: Question N applied to <section name>. Spec updated.
```

If the answer touches multiple sections, list all of them in the confirmation.

---

## Step 6: Stop Conditions

End the loop when **any** of the following is true:

1. **5 questions asked** (or `--max-questions N` reached).
2. **All critical ambiguities resolved**: the scan in Step 2 had no Missing categories AND at most one Partial category. Announce this as `Stopping early - the remaining ambiguities are below the clarification threshold.`
3. **User signal**: the user replied `stop` / `done` / `good` / `no more` to the last question.
4. **No queueable questions**: Step 3 produced an empty queue because every detected ambiguity is cosmetic (LOW severity under the `/analyze-spec` taxonomy).

---

## Step 7: Emit the Completion Report

```markdown
## /clarify-spec complete

**Spec**: <resolved path>
**Session**: <YYYY-MM-DD>
**Questions asked**: <N>
**Questions accepted**: <K>
**Questions deferred**: <D>
**Sections touched**: <comma-separated list>

### Coverage Summary

| Category | Status before | Status after |
|---|---|---|
| Functional Scope & Behavior | Partial | Clear |
| Domain & Data Model | Missing | Partial |
| ... | ... | ... |

### Outstanding ambiguities

- <one bullet per remaining Partial or Missing category, with a one-sentence note on what would close it>

### Recommended next command

- If outstanding ambiguities remain: rerun `/clarify-spec` to continue (or accept the remaining ambiguities as documented in `## Assumptions`).
- If all categories are now Clear: run `/analyze-spec` to verify the spec passes the read-only audit, then `/generate-plan` to build the implementation plan.
- If the spec gained new FR-### or SC-### IDs during this session: rerun `/analyze-spec` to refresh the Coverage Summary table.
```

---

## Behavior Guarantees

- **Sequential questioning**: exactly one question per turn. Never present 2 or more questions in a single message.
- **Recommended-option mandatory**: every question carries a Recommended option above the table / prompt with cited evidence. "No recommendation" is not acceptable.
- **Atomic save per answer**: the spec is saved after every accepted answer; a crash mid-loop leaves a spec that is consistent up to the last answered question.
- **Hard cap 5 questions**: the cap is a UX contract - users can rely on the loop terminating within 5 turns regardless of how many ambiguities the scanner detects.
- **No new files created**: the command edits the spec in place and adds a `## Clarifications` section. It does not create `clarifications.md`, `q-and-a.md`, or any sibling artifact.
- **Cross-link discipline**: every FR-### / SC-### ID added or modified by this command remains stable (no renumbering). New IDs use the next sequential number in the spec's existing scheme.

---

## Common Failure Modes

| Failure mode | What goes wrong | How this command avoids it |
|---|---|---|
| Question dump | Agent asks all 5 questions at once; user scans, picks easy ones, loses thread on the hard ones | Step 4 enforces one question per turn |
| Bias toward "more options" | Agent presents 5 options when 3 would suffice, paralyzing the user | Step 3 caps options at 5 and recommends 2-3 for clear binary / ternary choices |
| No recommendation | Agent asks "what would you like?" without a prior; user has to do the analyst's job | Step 4 makes the Recommended option mandatory with cited evidence |
| Answer never integrated | Agent records the answer in a Clarifications log but never updates FR / SC / user-story body | Step 5b enforces section-by-section application with a mapping table |
| Spec lost on crash | Agent batches multiple answers and writes at the end; a crash loses partial progress | Step 5 mandates atomic save per answer |
| Loop never terminates | Agent keeps asking follow-ups beyond the cap | Step 6 enforces 4 distinct stop conditions, any of which ends the loop |

---

## Related Skills and Commands

- `[[idea-refine]]` - earlier stage; turns a vague idea into a one-page problem statement. Use before writing the spec.
- `[[spec-driven-development]]` - the broader workflow that hosts the spec; defines FR-### / SC-### conventions and the 3-marker `[NEEDS CLARIFICATION]` cap.
- `[[ambiguity-detector]]` - the underlying detector for vague adjectives and unresolved markers. `/clarify-spec` builds on the same heuristics.
- `[[cross-artifact-analyzer]]` driven by `/analyze-spec` - read-only audit. Run before `/clarify-spec` to see the full inventory; rerun after to verify.
- `[[project-constitution]]` driven by `/constitution` - principle source that informs the Recommended option's reasoning when a question touches scope or compliance.
