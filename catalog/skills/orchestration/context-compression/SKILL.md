---
name: context-compression
description: Minimize tokens per task in long-running agent sessions while preserving critical information. Use when hitting context limits, preparing session handoffs, or managing verbose tool outputs.
summary_l0: "Minimize tokens per task while preserving critical information in agent sessions"
overview_l1: "This skill minimizes tokens per task in long-running agent sessions while preserving critical information. Use it when hitting context limits, preparing session handoffs, managing verbose tool outputs, or needing to extend effective session duration. Key capabilities include selective context retention (keeping decisions, discarding exploration), tool output compression and summarization, session handoff document generation, token budget tracking and forecasting, verbose log suppression strategies, critical information extraction from large outputs, and checkpoint-based context management. The expected output is compressed context with retained critical information, token usage reports, and session handoff documents. Trigger phrases: context compression, token limit, session handoff, compress context, reduce tokens, verbose output, session management, context budget."
---

# Context Compression

Specialized expertise in compressing conversation context to extend effective session length and maintain quality. Context compression is the primary tool for managing long-running agent sessions without losing critical decisions, file modifications, or task state.

> **Programmatic counterpart -- the `nexus-context-compressor` engine.** This skill is the *methodology* for compressing conversation context with judgment. For automatic, reversible compression of verbose *tool output* before it ever enters the window, Nexus-Hub ships an engine at `extensions/nexus-context-compressor/`: a local-first PreToolUse compressor that routes JSON dumps, code, and logs to deterministic strategies and persists every dropped span behind a `<<ccr:HASH N_rows>>` marker that resolves back on demand. Reach for the engine when the bloat is *mechanical* tool output (the Observation Masking pattern below, automated); apply the approaches in this skill when the bloat is conversation history and decisions that need a human-or-agent summary. See [[context-optimization]] for the one-env-var setup and [[prompt-token-optimization]] for the token-economics view.

## When to Use This Skill

Use this skill for:

- Sessions approaching 70-80% context capacity
- Preparing handoff documents between sessions
- Reducing verbose tool outputs that bloat context
- Long-running implementations spanning many turns
- Multi-file tasks generating significant read/search output
- Sessions where the agent starts showing degradation signs

**Trigger phrases**: "compress context", "session handoff", "running out of context", "summarize session", "reduce token usage", "too much context", "context cleanup", "session summary"

## What This Skill Does

Provides context compression capabilities including:

- **Compression Assessment**: Determining when and how aggressively to compress
- **Approach Selection**: Choosing the right compression strategy for the situation
- **Structured Summarization**: Preserving critical information in compact format
- **Tool Output Management**: Handling verbose command and file outputs
- **Quality Validation**: Verifying no critical information was lost
- **Session Continuity**: Enabling seamless handoffs between sessions

## Instructions

### Step 1: Determine Compression Need

**Context Capacity Assessment**:

| Signal | Status | Action |
|--------|--------|--------|
| Session length <15 turns | Green | No compression needed |
| Session length 15-30 turns | Yellow | Monitor; prepare for compression |
| Session length 30+ turns | Orange | Active compression recommended |
| Agent shows degradation symptoms | Red | Immediate compression required |
| Multiple large file reads in context | Orange | Compress tool outputs |
| Context auto-truncation occurring | Red | Emergency handoff needed |

**What Consumes the Most Context** (typical distribution):

| Component | % of Total | Compression Opportunity |
|-----------|-----------|------------------------|
| Tool outputs (file reads, search results, command output) | 40-60% | HIGH (often 80%+ reducible) |
| Message history (user + agent turns) | 25-35% | MEDIUM (summarizable) |
| System prompts and skill definitions | 10-15% | LOW (needed for behavior) |
| Current task working state | 5-10% | LOW (actively needed) |

**Rule**: Tool outputs are almost always the biggest compression opportunity. A single file read can consume 2,000+ tokens; a search result set can consume 5,000+. Most of this content is used once and then occupies attention budget indefinitely.

### Step 2: Select Compression Approach

Choose based on the situation:

**Decision Tree**:

```
Is this an emergency (context at 90%+)?
├── YES → Approach C: Regenerative Full Summary (session handoff)
└── NO
    ├── Are tool outputs the main bloat?
    │   ├── YES → Approach B: Observation Masking
    │   └── NO
    │       └── Is conversation history the main bloat?
    │           ├── YES → Approach A: Anchored Iterative Summarization
    │           └── NO → Combine A + B
```

#### Proactive steering with `/compact focus on X, drop Y`

See also: [SESSION_LIFECYCLE_DECISIONS.md](../../../../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) for the companion decision tree on continue vs `/rewind` vs `/clear` vs `/compact`.

The approaches A / B / C above choose *how* to compress. The decision of *when and how aggressively* to compress also matters. Default posture: **steer compaction proactively rather than waiting for autocompact**.

**When to steer proactively** (before engaging any of the A/B/C approaches):

- You are approaching **70-80% of the context window** on a long, still-on-topic task.
- Recent turns include large tool outputs or file reads you no longer need, but the overall goal is unchanged.
- You want to shed closed-thread content while keeping the live thread fully intact.

Waiting for autocompact is the **bad-compact failure mode**: the automatic trigger fires mid-reasoning, drops context Claude was about to use, and quality tanks for the next several turns. See `guides/reference/TOKEN_OPTIMIZATION.md` for the recognition signals.

**Syntax**: `/compact focus on <current work>, drop <closed threads>`

Plain `/compact` lets the model decide what to keep; the steerable variant is strictly better on long tasks because *you* know which thread is live.

**Common pre-compaction directives** (each is a directly-usable example):

- `/compact focus on the auth middleware refactor, drop the database schema exploration`
- `/compact focus on the failing integration tests, drop the feature-spec discussion`
- `/compact focus on the latest 3 files touched, drop earlier unrelated analysis`
- `/compact focus on the plan, drop the research outputs I no longer need`
- `/compact focus on the current test failures, drop the earlier green runs and exploration`
- `/compact focus on the error trace and the hypothesis we are testing, drop the initial reconnaissance`

**When `/clear` beats `/compact`**: if the live task is actually *done* and the next work is unrelated, `/clear` removes the compaction summary entirely rather than carrying it forward as dead weight.

### Step 3: Execute Compression

#### Approach A: Anchored Iterative Summarization

**Best for**: Long conversation histories where decisions and rationale must be preserved.

**Procedure**: Create a structured summary that anchors key information. The summary replaces detailed history while preserving everything needed to continue.

**Summary Template**:

```markdown
## Session Summary (Anchored)
**Task**: [One-sentence description of the overall task]
**Status**: [In Progress / Blocked / Near Completion]
**Last Updated**: [Current turn/timestamp]

### Intent
[What we are trying to accomplish and why]

### Files Modified
| File | Change | Status |
|------|--------|--------|
| [path] | [What was changed and why] | Done / In Progress |

### Key Decisions
1. **[Decision]**: [What was decided] because [rationale]
2. **[Decision]**: [What was decided] because [rationale]

### Current State
[What is working, what is broken, where we are in the process]

### Active Constraints
- [Constraint 1: e.g., "Must use existing AuthService, not create new one"]
- [Constraint 2: e.g., "All changes must be backward compatible"]

### Next Steps
1. [Immediate next action]
2. [Following action]
3. [Following action]

### Open Issues
- [Issue 1: description and potential resolution]
```

**Usage**: After creating the summary, re-inject it into the conversation:
```
"Here is our current session state. Use this as your primary context:
[paste summary]

Please proceed with [next step]."
```

#### Approach B: Observation Masking

**Best for**: Sessions with many tool outputs (file reads, search results, command output) that have already been consumed.

**Procedure**: Replace verbose tool outputs with compact references.

**Techniques**:

1. **Write-to-file pattern**: Instead of keeping large outputs in context, write them to temporary files:
   ```
   "Write the analysis results to tasks/analysis-output.md instead of
   displaying them in the conversation."
   ```

2. **Summary replacement**: After reading a file, summarize what was learned:
   ```
   "You just read src/services/auth.ts. Summarize the key findings
   (exported functions, patterns, dependencies) in 5 bullet points.
   We can re-read the file later if needed."
   ```

3. **Selective re-reading**: Instead of relying on earlier file reads in context, re-read only the specific sections needed:
   ```
   "Re-read lines 45-80 of src/services/auth.ts for the validateToken
   function. Don't rely on the earlier full-file read."
   ```

**Anti-pattern to avoid**: Do NOT ask the agent to "forget" earlier content. Context cannot be selectively erased. Instead, push important information to the end of context (where attention is strongest) by restating it.

#### Approach C: Regenerative Full Summary

**Best for**: Emergency compression when context is near capacity, or preparing a clean session handoff.

**Procedure**: Generate a complete, self-contained document that enables a fresh session to continue the work.

**Session Handoff Document Template**:

```markdown
## Session Handoff Document
**Generated**: [timestamp]
**Task**: [Complete task description]
**Repository**: [repo path]

### Background
[Why this task was started, what problem it solves, any relevant context
that a fresh session would need]

### Completed Work
1. [Completed item 1]: [What was done, which files, key details]
2. [Completed item 2]: [What was done, which files, key details]

### Files Modified (Complete List)
| File | Changes Made | Status | Notes |
|------|-------------|--------|-------|
| [path] | [Specific changes] | Complete | [Any caveats] |

### All Decisions Made
| # | Decision | Rationale | Alternatives Considered |
|---|----------|-----------|------------------------|
| 1 | [What] | [Why] | [What else was considered] |

### Current Blockers / Issues
- [Issue]: [Description and potential resolution path]

### Remaining Work (Prioritized)
1. [Task]: [Details, affected files, approach to take]
2. [Task]: [Details, affected files, approach to take]

### Important Context
- [Non-obvious information that would be hard to re-discover]
- [Gotchas encountered during this session]
- [Dependencies or constraints to remember]

### How to Continue
[Specific instructions for resuming: what to read first, what to do next,
what to watch out for]
```

**Usage**:
```
"Write the session handoff document to tasks/handoff-[date].md.
I will start a fresh session and reference this document."
```

### Preservation contract for client-side summaries

When the summary is produced client-side (a compaction hook, a session digest, a handoff document), it must preserve six categories, stated here as the contract the probes in Step 4 test against:

1. Difficulties met and how each was resolved.
2. Options raised or set aside, and why.
3. Anything asked, decided, agreed, ruled out, or established as a constraint, stated exactly.
4. Where things stand now.
5. What is still open or promised.
6. Hard-to-reconstruct specifics: names, numbers, dates, paths, and exact wording.

Weight the user's own words close to verbatim and condense the agent's own reasoning to what it concluded; a summary that paraphrases the user and preserves the agent's deliberation has the priorities inverted. Dropping a required category is a defect to report in the summary itself ("no record of open items survived compaction"), never an acceptable compression.

### Step 4: Validate Compression Quality

After compressing, verify no critical information was lost.

**Validation Probes** (ask these questions; the compressed context should still enable correct answers):

```markdown
## Compression Quality Probes

### Task Continuity
- [ ] "What is the original task?" → Correct and complete
- [ ] "What approach are we using?" → Matches decisions made

### Artifact Tracking (most commonly lost in compression)
- [ ] "List all files modified" → Complete list with correct descriptions
- [ ] "What changed in [specific file]?" → Accurate details

### Decision Recall
- [ ] "Why did we choose [approach X]?" → Correct rationale
- [ ] "What alternatives did we consider?" → At least the major ones

### Continuation Planning
- [ ] "What should we do next?" → Correct next step
- [ ] "Are there any known issues?" → All issues surfaced

### Quality Score
- 5/5 probes pass: Excellent compression (proceed confidently)
- 3-4/5 probes pass: Acceptable (add missing info to summary)
- <3/5 probes pass: Insufficient (re-compress with more detail)
```

**Critical insight**: Artifact trail integrity (which files were modified and how) is the information most commonly lost during compression. Always double-check file modification tracking in your summaries.

## Best Practices

- **Compress proactively at 70%**, not reactively at 95%
- **File modifications are sacred**: Never lose track of what files were changed and how
- **Write summaries to files**: A summary on disk is more reliable than one in conversation context
- **Re-read rather than recall**: When you need specific file content post-compression, re-read the file
- **Decisions need rationale**: A decision without rationale is useless in a handoff; the next session will re-decide it
- **Compress tool outputs first**: They are the lowest-value, highest-volume content in most sessions
- **Test your summaries**: Run the validation probes before relying on compressed context

## Common Patterns

### Pattern 1: Session Handoff Summary

**Situation**: End of a work session, need to continue tomorrow.

**Solution**:
1. Use Approach C (Regenerative Full Summary)
2. Write to `tasks/handoff-YYYY-MM-DD.md`
3. Next session: "Read tasks/handoff-YYYY-MM-DD.md and continue from where we left off"

### Pattern 2: Tool Output Compaction

**Situation**: Session has read 10+ files; context is bloated with file contents already consumed.

**Solution**:
1. Use Approach B (Observation Masking)
2. For each major file read, have the agent state what was learned in 3-5 bullets
3. For future reads, use line-range reads instead of full files
4. Write large analysis outputs to files

### Pattern 3: Conversation Condensation

**Situation**: Long back-and-forth discussion about approach; decision was made 20 turns ago.

**Solution**:
1. Use Approach A (Anchored Iterative Summarization)
2. Capture the decision and rationale in the summary
3. Re-inject the summary as a clear context reset
4. Proceed with focused execution

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just keep going; the context window is not full yet." | Quality degrades well before the hard limit -- around 70-80% capacity the agent starts dropping earlier decisions silently. Waiting for a hard truncation means you compress under duress, with no chance to validate what was lost. |
| "Summarizing in my head is enough; I do not need to write a handoff file." | An in-context summary evaporates the moment the session compacts or ends. Only a summary written to a file survives a `/clear`, a crash, or a handoff to another session. |
| "I will compress aggressively and drop the tool outputs to save the most tokens." | Discarding raw exploration is fine, but dropping a file-modification record or a decision rationale means the next turn re-derives (and may re-break) work already done. Compress exploration, never the decisions and file changes. |

## Verification

- [ ] Compression need identified (capacity or degradation)
- [ ] Appropriate approach selected via decision tree
- [ ] Summary/handoff document created with all required sections
- [ ] File modifications completely tracked
- [ ] Key decisions preserved with rationale
- [ ] Validation probes passed (4+/5)
- [ ] Summary written to file for durability

## Related Skills

- [[context-manager]] - Context fundamentals and attention budget management
- [[context-degradation]] - Detecting when compression is needed
- [[context-optimization]] - Configures the programmatic `nexus-context-compressor` engine (the automated, reversible counterpart to this skill's manual methodology)
- [[plan-before-code]] - Structured planning that reduces context bloat
- [[filesystem-context-patterns]] - File-based context management patterns
- See also: [SESSION_LIFECYCLE_DECISIONS](../../../../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) - when to compact vs `/rewind`, `/clear`, or delegate to a subagent

---

**Version**: 1.0.0
**Last Updated**: February 2026
**Author**: Nexus-Hub
**Attribution**: Adapted from [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License)


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
