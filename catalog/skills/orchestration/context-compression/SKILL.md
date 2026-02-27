---
name: context-compression
description: Minimize tokens per task in long-running agent sessions while preserving critical information. Use when hitting context limits, preparing session handoffs, or managing verbose tool outputs.
---

# Context Compression

Specialized expertise in compressing conversation context to extend effective session length and maintain quality. Context compression is the primary tool for managing long-running agent sessions without losing critical decisions, file modifications, or task state.

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

## Quality Checklist

- [ ] Compression need identified (capacity or degradation)
- [ ] Appropriate approach selected via decision tree
- [ ] Summary/handoff document created with all required sections
- [ ] File modifications completely tracked
- [ ] Key decisions preserved with rationale
- [ ] Validation probes passed (4+/5)
- [ ] Summary written to file for durability

## Related Skills

- `context-manager` - Context fundamentals and attention budget management
- `context-degradation` - Detecting when compression is needed
- `plan-before-code` - Structured planning that reduces context bloat
- `filesystem-context-patterns` - File-based context management patterns

---

**Version**: 1.0.0
**Last Updated**: February 2026
**Author**: DevAI-Hub
**Attribution**: Adapted from [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License)


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
