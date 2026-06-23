# Session Lifecycle Decisions

A decision guide for managing Claude Code sessions on the 1M-token Opus 4.7 / Sonnet 4.6+ context window. Codifies five recurring branch points that every heavy operator hits: whether to continue, `/rewind`, `/clear`, `/compact`, or delegate to a subagent. Pick deliberately; every branch has a different cost, recovery profile, and quality impact.

---

## TL;DR decision flowchart

```
                       +------------------------------------+
                       |  Am I starting a new task?         |
                       +------------------------------------+
                            |                       |
                          yes                       no
                            |                       |
                +---------------------+             |
                | Related to current? |             |
                +---------------------+             |
                   |              |                 |
                  yes             no                |
                   |              |                 |
                   v              v                 v
           +--------------+  +---------+    +----------------------+
           | keep context |  | /clear  |    | Is context healthy?  |
           | (exception:  |  | or new  |    | (see degradation     |
           |  docs after  |  | session |    |  signals below)      |
           |  impl)       |  +---------+    +----------------------+
           +--------------+                      |            |
                                                yes           no
                                                 |            |
                                                 v            v
                                     +----------------+   +-----------------+
                                     |  Continue.     |   | Did the last    |
                                     |  If I only     |   | few turns go    |
                                     |  need the      |   | off-rails?      |
                                     |  conclusion,   |   +-----------------+
                                     |  delegate to   |        |       |
                                     |  a subagent.   |       yes      no
                                     +----------------+        |       |
                                                               v       v
                                                      +----------+  +-----------------+
                                                      | /rewind  |  | /compact focus  |
                                                      | with     |  | on X, drop Y    |
                                                      | summary  |  | (proactive)     |
                                                      +----------+  +-----------------+
```

The rest of this guide expands each branch.

---

## 1. When to start a new session

**Default rule**: new task = new session. The cost of starting a fresh session is small. The cost of letting unrelated context bleed into your next task is large: irrelevant files stay in context, Claude conflates goals, and the 1M window is no longer a buffer but a liability.

### Exception: documentation after implementation

When you have just finished implementing a feature and now want to document it (devlog, changelog, session history, commit message), **do not clear**. The context from the work itself - files touched, decisions made, blockers encountered - is exactly what you need to write accurate documentation. A fresh session would force Claude to re-read diffs and git history to reconstruct the narrative.

Checklist for staying in the same session:
- You are producing artifacts that describe the work just done (devlog, commit message, release notes, session history).
- You will not ask Claude to make further code changes after the docs are written.
- The current session is not already showing degradation signals (see section 4).

If any of those fail, write the docs in a fresh session and paste in a short handoff (see section 2).

---

## 2. When to `/rewind`

`/rewind` drops the last N turns and returns to an earlier checkpoint. Use it when a specific turn (or handful of turns) took the conversation off-rails and you want to re-attempt with different context - but you still want the earlier work to stay alive.

### Typical trigger

- You see Claude pattern-matching to a wrong interpretation and the last 2-6 turns are noise.
- Tool output from a failed exploration is now crowding out the signal.
- You gave a bad instruction and want to restate it without Claude anchoring on the first framing.

### The "summarize from here" handoff pattern

Before calling `/rewind`, ask Claude for a compact handoff message (5-10 bullets) capturing the current task goal, decisions made so far, files touched, known blockers, and the next concrete step. Then `/rewind` (or `/clear`) and paste the handoff as the opening message of the next turn.

Why this matters: `/rewind` without a handoff throws away Claude's *learnings* along with the noise. The summary preserves conclusions without the raw tool output bloat.

```
Step 1: "Summarize from here: task goal, key decisions, files touched,
         blockers, next step. Keep it under 10 bullets."
Step 2: /rewind (or /clear for a harder reset)
Step 3: Paste the summary as the first message of the new turn.
Step 4: Continue.
```

This is a strictly better handoff than letting autocompact fire mid-task.

---

## 3. When to `/clear`

`/clear` is the full reset. Everything drops: files read, tool results, conversation history. Use when the next task is fundamentally unrelated to the current one and you want no bleed.

### Typical trigger

- You finished a feature and your next task is in a different module or a different repo concern.
- You want to start fresh with a well-scoped first-turn specification (see `plan-before-code`).
- A long session is showing cross-task confusion: Claude keeps referencing details from an earlier, now-irrelevant task.

### When `/clear` beats a new session

Both produce an empty context. Use `/clear` if you want to keep the same Claude Code session open (same terminal, same flags, same CWD). Use a brand-new session if the task also warrants changing the working directory, reloading memory, or restarting tooling.

### When NOT to `/clear`

- Mid-feature, even if long. Use `/compact focus on X, drop Y` instead (section 4).
- When you still need the handoff summary. Always generate the handoff *before* clearing.

---

## 4. When to `/compact`

`/compact` summarizes the current session and continues with the summary in place of the raw history. Use it **proactively** - do not wait for autocompact to fire mid-reasoning.

### Proactive trigger (the reliable case)

- Approaching 70-80% of the context window on a long, still-on-topic task.
- Recent turns include large tool outputs or file reads you no longer need, but the overall goal is unchanged.
- You want to shed closed-thread content while keeping the current open thread intact.

### The steerable variant: `/compact focus on X, drop Y`

Plain `/compact` lets Claude decide what to keep. The steerable variant is strictly better for long tasks because *you* know which thread is live:

```
/compact focus on the auth middleware refactor, drop the database schema exploration
/compact focus on the failing integration tests, drop the feature-spec discussion
/compact focus on the latest 3 files touched, drop earlier unrelated analysis
```

Use this whenever you can articulate the live thread in one sentence.

### Reactive compaction (autocompact) is a red flag

If autocompact fires on its own, Claude's quality often drops for several turns afterward. This is the **bad-compact failure mode** documented in `guides/TOKEN_OPTIMIZATION.md`. Recognition signals:

1. Sudden drop in response quality or coherence.
2. Claude re-reads files it already read, because the compaction dropped references.
3. "What were we working on?" style recovery turns.

If you see any of the above, the damage is done for this session - write a handoff and `/rewind` or `/clear`.

---

## 5. When to delegate to a subagent

Subagents run a scoped sub-task in their own context, return a result, and do not leave their raw exploration in your main session. The single test is:

> **Will I need this tool output again later in the session, or just the conclusion?**

| Need | Run it where |
|------|--------------|
| Raw output used for further inspection | Main session |
| Only the conclusion used going forward | Subagent |

### Three good delegation shapes

1. **Verify-then-report.** "Run the test suite and report pass/fail + first failing test." The raw stack traces stay in the subagent; you keep the conclusion.
2. **Summarize an external codebase.** "Explore that 80k-file repo and return a one-page architectural summary." You never wanted the file-by-file reads in your main context.
3. **Produce a derived artifact.** "Read the full diff and write the CHANGELOG entry." You keep only the CHANGELOG text.

### Counter-examples (do NOT delegate)

- You need to read the code yourself to make further decisions. Do it in the main session - the conclusion alone will not carry enough detail.
- The task is highly interactive (multiple clarifying rounds) - delegation prevents back-and-forth with the user.
- The task is cheap enough that the subagent overhead outweighs the win.

---

## Three worked examples

### Example A - "I just finished a feature, now I need to document it"

- Task just finished: implemented auth middleware with JWT rotation.
- Next action: write the devlog entry, commit message, and session history.

**Decision**: stay in the same session (documentation-after-implementation exception, section 1). All the useful context - files touched, rationale, edge cases handled - is already loaded. Clearing would force Claude to reconstruct it from git history and guess at intent.

---

### Example B - "The debugging went off-rails six turns ago"

- Task: diagnose a flaky integration test.
- Last six turns: Claude pattern-matched to a false lead, ran diagnostics that confirmed nothing, and re-analyzed the same fixture twice.
- Current state: partial understanding of the test harness was valid *before* turn -6, but the last six turns are pure noise.

**Decision**: (1) ask for a "summarize from here" capturing only the pre-turn-6 learnings; (2) `/rewind`; (3) paste the summary as the next message; (4) retry the debug from a cleaner framing. You keep the real progress, drop the noise, and do not pay for autocompact.

---

### Example C - "I need to answer one question about a large codebase"

- Task: answer "which service owns the quote-expiration logic" in a monolith you do not normally work in.
- Natural approach: glob/grep repeatedly, load lots of files into context, synthesize.

**Decision**: delegate to an Explore subagent. "Find the module responsible for quote-expiration logic in `services/`. Report file path, the owning class/function, and any adjacent scheduling/cron config. Under 150 words." You keep the 150-word answer; the subagent eats the token cost of reading twenty files.

---

## Related anchors in this repository

- [TOKEN_OPTIMIZATION.md](TOKEN_OPTIMIZATION.md) - compaction tactics, `/compact focus on X, drop Y`, and the bad-compact failure mode.
- [catalog/skills/ai-development/prompt-engineering/SKILL.md](../../catalog/skills/ai-development/prompt-engineering/SKILL.md) - Effort-Level Strategy section covers the effort-tier half of session economics.
- [catalog/skills/orchestration/context-compression/SKILL.md](../../catalog/skills/orchestration/context-compression/SKILL.md) - concrete compression recipes for handoffs.
- [catalog/skills/orchestration/context-degradation/SKILL.md](../../catalog/skills/orchestration/context-degradation/SKILL.md) - recognition signals for the 300-500k range.
- [catalog/skills/orchestration/multi-agent-coordinator/SKILL.md](../../catalog/skills/orchestration/multi-agent-coordinator/SKILL.md) - subagent delegation patterns in depth.
- [catalog/skills/workflow/session-history/SKILL.md](../../catalog/skills/workflow/session-history/SKILL.md) - the "summarize from here" mode used in sections 2 and 4.

---

## Sources

- Anthropic - "Managing Claude Code sessions on the 1M context window" (official blog post; no canonical URL maintained in this repo).
- Anthropic - "Best practices for using Claude Opus 4.7 with Claude Code" (official blog post).
- Nexus-Hub comparison notes: `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
