---
name: session-teach-back
description: Socratic mastery-confirmation loop that quizzes the HUMAN operator on what a development session actually built and why, one concept at a time against a persistent dated checklist, and refuses to finish until every item is confirmed. Make sure to use this skill whenever the user says "teach me what we built", "quiz me on this session", "teach-back", "did I understand X", "drill me on the session", "make sure I actually get what we did", "test my understanding of this work", or otherwise wants to confirm THEIR OWN understanding of a completed session instead of just recording it. SKIP, do NOT use for, generating a record of what happened (use generate-session-history / session-history), querying or recovering context from PAST sessions (use session-query), or tracking task or phase progress (use dev-progress-tracker).
summary_l0: "Socratic teach-back loop that quizzes the human on a session until every concept is confirmed"
overview_l1: "Adds a Socratic mastery-confirmation loop that quizzes the human operator on what a development session produced, confirming each concept before finishing. It sources the session by reusing session-query's local, script-first, zero-outbound extractor rather than re-grepping transcripts, then writes a dated mastery checklist under docs/teaching/ (or .nexus/teaching/) with mode/source/started frontmatter, The Problem / The Solution / Broader Context sections, [ ]/[x] checkboxes, and an n/total confirmed progress line. The loop opens by asking the user to restate their understanding (calibration), asks one targeted question per exchange, drills into WHY behind each decision, marks items confirmed immediately, and refuses to wrap up until every item is checked. It is a teaching loop, not requirements intake, so it deliberately does not batch questions. Trigger phrases: teach me what we built, quiz me on this session, teach-back."
---

# Session Teach-Back

Confirm that the HUMAN actually understands what a session built, not just that the work shipped. After an AI session produces code and decisions, the operator's grasp of *what was built and why* silently degrades. This skill closes that gap with an explicit, item-by-item Socratic quiz against a persistent checklist sourced from the real session, and a hard gate: it does not declare the debrief complete until every concept is confirmed by a correct answer.

It quizzes *you*, the operator. It is the mastery-confirmation counterpart to the rest of the session family: [[session-query]] reads past sessions, [[session-history]] / [[generate-session-history]] write a record of the current one, and this skill checks that you can explain that record back.

## When to Use This Skill

Use when:

- The user says "teach me what we built", "quiz me on this session", "teach-back", "did I understand X", or "drill me on the session".
- A session produced non-trivial work (a feature, a refactor, a debugging trail, an architectural decision) and the operator wants to be sure they could explain or maintain it later.
- Onboarding a developer onto work an earlier session produced, where confirmed understanding (not just a written record) is the goal.
- The user wants to test their own retention before a handoff, a review, or building on top of the work.

**When NOT to use:**

- Generating a record of what happened in the session - use [[generate-session-history]] / [[session-history]]. That writes the document; this skill quizzes you on it.
- Recovering context from a PAST session ("did we look at this before?") - use [[session-query]].
- Tracking task or phase progress against a plan - use [[dev-progress-tracker]].
- Gathering requirements before building. This is a teaching loop, not requirements intake (see the Common Rationalizations table for why the one-question-per-exchange rule here is the deliberate opposite of the usual batch-your-questions rule).

## Instructions

### 1. Resolve and digest the session source (reuse, do not re-implement)

Do NOT grep `~/.claude/projects` or re-read raw transcripts by hand. The catalog already ships a script-first, cross-platform, zero-outbound extractor in [[session-query]]; reuse it.

1. Discover candidate transcripts with session-query's `scripts/discover-sessions.{sh,ps1}`.
2. Extract a filtered digest with session-query's `scripts/extract-session.{py,ps1}`, scoped by topic / branch / time window to the session being taught back. The digest returns matched files, first/last timestamps, branch mentions, and truncated snippets.
3. If no argument or topic is given, list the most recent sessions from the digest and let the user pick which one to be quizzed on.
4. From that digest, synthesize a short teaching narrative (roughly 500-1000 words) of what the session did and why: the problem, the solution taken, the alternatives weighed, the design decisions, and the edge cases. This narrative is the source material for the checklist - it is internal scaffolding.

Do NOT narrate the discovery/extraction mechanics to the user. Begin teaching directly. If the extractor returns nothing for the requested scope, say so plainly and offer to widen the scope or take a file path; never invent a session that did not happen.

If the digest is too thin to build concrete items from, prefer extending [[session-query]]'s extractor over re-implementing extraction here - one extractor, not two divergent ones.

### 2. Write the dated mastery checklist

Persist a checklist so progress survives across exchanges and sessions. Write it to a catalog-convention, git-aware path:

- Default: `docs/teaching/<YYYY-MM-DD>-<slug>.md`.
- Alternative: `.nexus/teaching/<YYYY-MM-DD>-<slug>.md` when the user prefers a scratch (often git-ignored) location.

Do NOT use the upstream `sessions/teaching/` path. For the date, use the current LOCAL date in `YYYY-MM-DD` (the harness provides today's date; otherwise `date +%F` on POSIX or `Get-Date -Format yyyy-MM-dd` in PowerShell). Do NOT hard-code a timezone such as `America/New_York`. Derive `<slug>` from the session topic in kebab-case.

The checklist file structure:

```markdown
---
mode: solo
source: <session path or topic the digest came from>
started: <YYYY-MM-DD>
---

# Teach-Back: <session topic>

**Progress: 0/<total> confirmed**

## The Problem

- [ ] <concrete item: the actual problem this session addressed>
- [ ] <concrete item: why that problem existed / what made it hard>

## The Solution

- [ ] <concrete item: the approach actually taken>
- [ ] <concrete item: a specific design decision and the alternative rejected>
- [ ] <concrete item: an edge case or failure mode handled>

## Broader Context

- [ ] <concrete item: how this fits the wider system or what it unblocks>
```

Item rules:

- Items must be CONCRETE and tied to the real session (the actual problem, the real file or function, the specific decision and the alternative weighed), never generic placeholders like "understand the architecture".
- One checkbox per distinct concept worth confirming. Keep the list focused; a tight, real list beats a long, vague one.
- Keep the `mode: solo` / `source` / `started` frontmatter and the `Progress: n/total confirmed` line at the top so any later exchange can resume from file state alone.

### 3. Run the solo teach-back loop

This is the core mechanic. One concept per exchange, confirmed before moving on:

1. **Re-read the checklist file** before every exchange. The file, not your memory, is the source of truth for what is confirmed.
2. **Open with calibration.** Before quizzing, ask the user to restate, in their own words, their understanding of what the session did. Use their answer to skip what they already know and target the gaps - do not re-cover material they just demonstrated.
3. **Pick the next unconfirmed item** (`[ ]`) from the checklist.
4. **Ask ONE targeted question** about that item. Drill into the WHY behind the decision, not just the what ("why was that approach chosen over the alternative?", not only "what was built?").
5. **On a correct answer:** mark that item `[x]` in the file IMMEDIATELY, update the `Progress: n/total` line, and move to the next item. Never batch confirmations to the end.
6. **On a miss or a partial answer:** explain the concept briefly, then re-ask in a different form (a reframed question, a concrete example, or a multiple-choice). Do not mark it confirmed until the user answers correctly.
7. **Show progress** every 3-4 exchanges (e.g. "4/9 confirmed, next up: the retry-backoff decision") so the user feels the finish line.

### 4. Hard completion gate

Do NOT offer to wrap up, summarize, or declare the teach-back done until 100% of the checklist items are `[x]` and the `Progress` line reads `n/n confirmed`. An unfinished checklist means unconfirmed understanding; finishing early defeats the entire purpose of the skill. When every item is confirmed, state that mastery is confirmed and stop. (Committing the checklist is out of scope for this core version; it arrives as an opt-in step in a later enhancement.)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will quiz all the concepts in one message to save round-trips" | Batching breaks the entire retention mechanic. One question per exchange forces the user to actively recall and articulate each concept; a wall of questions gets a skimmed, shallow answer and confirms nothing. This is a teaching loop, not requirements intake - it deliberately does the opposite of the usual "batch your clarifying questions" rule, and both can coexist because that rule governs gathering requirements before acting, not confirming human mastery. |
| "I will mark the items confirmed at the end once we are done" | Deferred updates mean an interrupted session loses the record of what was confirmed, and the next exchange re-quizzes settled material. Mark `[x]` and update the progress line immediately after each correct answer, the same incremental-update discipline [[dev-progress-tracker]] enforces for tasks. |
| "The user clearly knows this, I will skip the calibration opener" | Skipping calibration either re-covers what they already know (wasting the loop) or assumes mastery they do not have (defeating it). Always ask them to restate first, then target the real gaps. |
| "Asking what was built is enough, I do not need the why" | Confirming the what without the why produces an operator who can describe the change but cannot maintain or extend it. Drill into the motivation and the rejected alternative before advancing. |
| "Generic items like 'understand the design' are faster to write" | Generic items cannot be answered correctly or incorrectly, so the gate becomes meaningless. Tie every item to the real problem, the real decision, and the real edge case from the digest. |
| "I will just re-grep the transcripts myself instead of using session-query" | That creates a second, divergent extractor and pulls noisy raw transcripts into context. Reuse session-query's local zero-outbound extractor; extend it if the digest is too thin. |
| "I will declare it done at 8/10 since the rest is minor" | The hard gate is the point. Unconfirmed items are unconfirmed understanding; finishing early ships a false sense of mastery. Do not offer to wrap up until the progress line reads n/n. |

## Verification

- [ ] A dated checklist file exists at `docs/teaching/<YYYY-MM-DD>-<slug>.md` (or the `.nexus/teaching/` alternative), with `mode`/`source`/`started` frontmatter and a `Progress: n/total confirmed` line.
- [ ] Checklist items are concrete and tied to the actual session (real problem, real decision, real edge case), not generic placeholders.
- [ ] The session was sourced via session-query's `discover-sessions` + `extract-session` scripts, not by hand-grepping transcripts.
- [ ] The loop opened with a calibration question (user restated their understanding) before any quiz question.
- [ ] Exactly one targeted question was asked per exchange; confirmations were written to the file immediately, never batched.
- [ ] No wrap-up was offered until every item was `[x]` and the progress line read `n/n confirmed`.
- [ ] No transcript content was sent to any network service, and no new slash command or `scripts/` directory was added by this skill.

## Related Skills

- [[session-query]] - the local, script-first, zero-outbound session extractor; this skill reuses it to source the material it quizzes you on rather than re-grepping transcripts.
- [[session-history]] - writes a standalone record of the current session; this skill quizzes you on what that session produced. Generate the record, then teach-back on it.
- [[generate-session-history]] - the command that produces a session-history document; use it (not this skill) when the goal is to write the record, not confirm understanding.
- [[dev-progress-tracker]] - tracks task/phase progress with the same `[ ]`/`[x]` checkbox-file pattern this skill uses to track mastery; that file is forward-looking work, this one is confirmed understanding.
- [[quality-gate-definitions]] - the reusable GO/NO-GO gate pattern; this skill applies that gate to human mastery (100% of items confirmed) rather than to artifact state.
