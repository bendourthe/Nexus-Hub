---
name: context-degradation
description: Detect and mitigate context quality decay in long AI agent sessions. Use when an agent starts forgetting instructions, repeating mistakes, confusing files, or producing lower-quality output mid-session.
summary_l0: "Detect and mitigate context quality decay in long AI agent sessions"
overview_l1: "This skill detects and mitigates context quality decay in long AI agent sessions. Use it when an agent starts forgetting instructions, repeating mistakes, confusing files, producing lower-quality output mid-session, or when session length exceeds typical context window limits. Key capabilities include decay signal detection (instruction amnesia, file confusion, quality regression, repetitive errors), decay severity classification, mitigation strategy selection (context refresh, session split, checkpoint and restart, selective compaction), proactive decay prevention through session planning, and session health monitoring. The expected output is detection of degradation signals with recommended mitigation actions and session management strategies. Trigger phrases: context degradation, forgetting instructions, agent quality decay, session too long, repeating mistakes, context window full, agent confused, session health."
---

# Context Degradation

Specialized expertise in recognizing, diagnosing, and recovering from context quality degradation in AI-assisted development sessions. Context degradation is the single most common cause of agent errors in long-running sessions.

## When to Use This Skill

Use this skill for:

- Long-running sessions where output quality noticeably drops
- Agent "forgetting" earlier instructions or decisions
- Repeated mistakes despite prior corrections
- Confusion between similarly named files, functions, or concepts
- Agent giving generic responses instead of project-specific ones
- Multi-file changes where consistency breaks down

**Trigger phrases**: "context degradation", "forgetting instructions", "lost context", "quality dropping", "repeating mistakes", "confused about files", "session getting stale", "agent not remembering"

## What This Skill Does

Provides context degradation management including:

- **Pattern Recognition**: Identifying the 5 common degradation patterns
- **Severity Assessment**: Measuring how degraded the current context is
- **Targeted Mitigation**: Applying the right fix for each degradation type
- **Recovery Verification**: Confirming that mitigation restored quality
- **Prevention Strategies**: Proactive techniques to avoid degradation
- **Session Health Monitoring**: Ongoing quality indicators to watch

## Instructions

### Step 1: Recognize Degradation Patterns

Context degradation manifests in 5 distinct patterns. Identifying the correct pattern determines the mitigation strategy.

**The Five Degradation Patterns**:

| Pattern | Symptoms | Root Cause | Severity |
|---------|----------|------------|----------|
| **Lost-in-Middle** | Agent ignores instructions from mid-conversation; favors recent or very early context | Attention mechanisms weight sequence endpoints more heavily; middle content receives 10-40% lower recall | HIGH |
| **Context Poisoning** | Errors compound through repeated references; agent doubles down on early mistakes | Incorrect information gets reinforced each time it is referenced, becoming "authoritative" in context | CRITICAL |
| **Context Distraction** | Agent addresses tangential topics; output includes irrelevant details | Verbose tool outputs, off-topic history, or unnecessary file contents compete for attention | MEDIUM |
| **Context Confusion** | Agent conflates similar but distinct concepts (e.g., two services with similar names) | Semantically similar tokens in context cause cross-contamination of representations | HIGH |
| **Context Clash** | Agent produces contradictory outputs or oscillates between approaches | Conflicting instructions, outdated decisions still in context, or contradictory code patterns | HIGH |

**Quick Diagnostic Questions** (ask the agent these to detect degradation):

```markdown
## Degradation Probe Questions

1. "Summarize the original task we are working on."
   → If vague or wrong: Lost-in-Middle or Context Distraction

2. "List all files we have modified in this session and what changed."
   → If missing files or wrong changes: Context Poisoning or Lost-in-Middle

3. "What was the last decision we made and why?"
   → If wrong rationale: Context Poisoning

4. "Explain the difference between [similar concept A] and [similar concept B]."
   → If conflated: Context Confusion

5. "Are there any conflicting requirements in our current approach?"
   → If unaware of contradictions: Context Clash
```

**1M-window calibration (Opus 4.7 / Sonnet 4.6+)**: Lost-in-Middle degradation becomes noticeable around **300-400k tokens** of conversation history on the 1M-token context window, and accelerates past 500k. Below 100k, degradation is usually task-related (the five patterns above) rather than window-related. This is task-dependent and model-dependent; use the table below as guidance, not a hard threshold.

| Session size | Degradation risk | Recommended action |
|--------------|------------------|---------------------|
| < 100k tokens | Green - low risk | Continue normally; degradation here is usually task-shaped, not window-shaped |
| 100-300k | Yellow - monitor | Watch for repeat clarifications, dropped references, generic responses |
| 300-500k | Orange - mitigate | Proactive `/compact focus on X, drop Y` (see Step 3 and context-compression Step 2); consider a summarize-then-handoff |
| 500k+ | Red - high risk | `/compact` or `/rewind` with a handoff summary; delegate new subtasks to subagents rather than loading them into the main session |

**Caveat**: Tasks with dense context (many files, long tool outputs) hit Orange earlier; tasks with mostly conversational context hit Orange later. The Five Patterns above are the ground truth - use the table to decide when to start actively monitoring for them.

### Step 2: Assess Degradation Severity

**Severity Indicators**:

| Indicator | Green (Healthy) | Yellow (Early Degradation) | Red (Severe Degradation) |
|-----------|----------------|---------------------------|--------------------------|
| **Task recall** | Agent accurately restates original goal | Agent has partial recall, misses nuance | Agent cannot summarize the task |
| **File tracking** | Agent knows all modified files and changes | Agent tracks recent files but misses earlier ones | Agent confuses file contents or purposes |
| **Decision memory** | Agent recalls decisions with rationale | Agent recalls decisions but not rationale | Agent contradicts earlier decisions |
| **Instruction adherence** | Agent follows all instructions precisely | Agent misses occasional guidelines | Agent ignores or contradicts instructions |
| **Output specificity** | Responses are project-specific and detailed | Responses mix generic and specific content | Responses are generic boilerplate |

**Context Length Thresholds** (approximate):

| Context Usage | Risk Level | Recommended Action |
|---------------|------------|-------------------|
| 0-50% | Low | No action needed |
| 50-70% | Moderate | Begin planning compression |
| 70-85% | High | Active compression recommended |
| 85-100% | Critical | Immediate session handoff or compression |

**Companion guidance for compression and handoff decisions**: the percentages above describe *severity*; deciding which tool to reach for when you hit Orange or Red is a separate call. See the **Proactive steering with `/compact focus on X, drop Y`** subsection of [context-compression/SKILL.md](../context-compression/SKILL.md) for the steerable-compaction syntax used at the Orange threshold, and [guides/SESSION_LIFECYCLE_DECISIONS.md](../../../../guides/SESSION_LIFECYCLE_DECISIONS.md) for the continue / `/rewind` / `/clear` / `/compact` / delegate decision tree that decides when compression is the wrong tool.

### Step 3: Apply Mitigation

Apply the appropriate mitigation based on the identified pattern. Use the **4-Bucket Approach**: Writing, Selecting, Compressing, Isolating.

#### Bucket 1: Writing Better Context

**When**: Context Distraction or Context Clash patterns detected.

- **Restate the objective**: Explicitly re-inject the task description into the conversation
- **Clarify contradictions**: Identify and resolve conflicting instructions ("We previously decided X, but we also said Y. The correct approach is X because...")
- **Remove noise**: Ask the agent to ignore specific earlier messages or tool outputs that are no longer relevant

**Template**:
```
"Let me restate our current objective clearly:
- Task: [clear description]
- Approach decided: [specific approach]
- Constraints: [active constraints]
- Ignore: [any earlier discussion that is now superseded]

Please proceed with this context."
```

#### Bucket 2: Selecting Relevant Context

**When**: Lost-in-Middle or Context Distraction patterns detected.

- **Re-read critical files**: Have the agent re-read the most important files to bring them to the top of attention
- **Summarize and discard**: Ask for a summary of completed work, then start fresh with the summary
- **Focus the scope**: Narrow the active task to reduce the number of files and concepts in play

**Template**:
```
"Before continuing, please:
1. Re-read [critical file 1] and [critical file 2]
2. Summarize what we have completed so far
3. List the remaining tasks

Then proceed with only [specific next task]."
```

#### Bucket 3: Compressing Context

**When**: Context is at 70%+ capacity with any degradation pattern.

- **Anchored summary**: Create a structured summary that preserves key decisions, file modifications, and next steps (see `context-compression` skill for detailed procedures)
- **Session handoff**: Write a complete context document to file and start a new session with it
- **Tool output cleanup**: Replace verbose tool outputs in memory with compact summaries

**Template**:
```
"Please write a complete session summary to `tasks/session-handoff.md` including:
1. Original task and current status
2. All files modified (with what changed)
3. Key decisions (with rationale)
4. Remaining work items
5. Known issues or blockers

This will serve as the starting context for a fresh session."
```

#### Bucket 4: Isolating Sub-Tasks

**When**: Context Confusion or complex multi-concern tasks.

- **Sub-agent delegation**: Offload specific sub-tasks to fresh agent contexts
- **File-based communication**: Have sub-agents write results to files rather than passing through the main context
- **Sequential focus**: Address one concern at a time instead of juggling multiple

**Template**:
```
"This task has become complex. Let's isolate:
1. Use a sub-agent to handle [concern A] independently
2. Write results to [output file]
3. Then address [concern B] in the main session
4. Finally, integrate the results"
```

### Step 4: Verify Recovery

After applying mitigation, verify that context quality has been restored.

**Recovery Verification Checklist**:

```markdown
## Post-Mitigation Verification

### Probe Tests (re-run diagnostic questions from Step 1)
- [ ] Agent accurately summarizes the original task
- [ ] Agent correctly lists all modified files
- [ ] Agent recalls recent decisions with rationale
- [ ] Agent distinguishes between similar concepts
- [ ] Agent identifies and addresses contradictions

### Output Quality Check
- [ ] Next output is project-specific (not generic)
- [ ] Output follows all stated instructions
- [ ] Output is consistent with prior decisions
- [ ] Output correctly references file paths and function names

### Result
- [ ] RECOVERED: All probes pass, quality restored
- [ ] PARTIAL: Some probes pass, monitor closely
- [ ] FAILED: Consider starting a new session with handoff document
```

## Best Practices

- **Monitor proactively**: Run probe questions every 15-20 turns in long sessions
- **Compress early**: Start summarizing at 70% context, not 95%
- **One concern at a time**: Context confusion almost always comes from juggling too many concerns simultaneously
- **Write findings to files**: Any time the agent produces a large analysis, have it write to a file and reference the path rather than keeping it all in context
- **Re-read, don't recall**: If you need the agent to use specific file content, have it re-read the file rather than relying on earlier context
- **Explicit over implicit**: Restate important constraints rather than assuming the agent remembers them
- **Session boundaries are features**: Starting a fresh session with a good handoff document often produces better results than fighting degradation

## Common Patterns

### Pattern 1: Long Session Recovery

**Situation**: 30+ turn session, agent producing generic or inconsistent output.

**Solution**:
1. Run probe questions (Step 1) to identify degradation type
2. Write session handoff document to file (Bucket 3)
3. Start fresh session, reference the handoff document
4. Verify recovery with probe questions

### Pattern 2: Multi-File Confusion Reset

**Situation**: Agent confusing contents or purposes of similar files (e.g., `UserService.ts` vs `UserController.ts`).

**Solution**:
1. Identify the confused concepts (Step 1, question 4)
2. Have agent re-read both files sequentially (Bucket 2)
3. Ask agent to explicitly state the difference between them
4. Proceed with narrowed scope (one file at a time)

### Pattern 3: Contradictory Instruction Detection

**Situation**: Agent oscillates between approaches or produces contradictory output.

**Solution**:
1. Ask agent to list all active constraints and decisions (Step 1, question 5)
2. Identify the contradiction explicitly
3. Resolve it with a clear directive (Bucket 1)
4. Verify the agent follows the resolved approach

## Quality Checklist

- [ ] Degradation pattern identified correctly
- [ ] Severity assessed using indicators table
- [ ] Appropriate mitigation bucket applied
- [ ] Recovery verified with probe questions
- [ ] Proactive monitoring plan established for remainder of session
- [ ] Critical context persisted to files (not just in conversation)

## Related Skills

- `context-manager` - Foundational context management and attention budget concepts
- `context-compression` - Detailed compression procedures and summary templates
- `plan-before-code` - Structured planning that prevents some degradation
- `task-coordinator` - Task isolation that reduces context overload
- See also: [SESSION_LIFECYCLE_DECISIONS](../../../../guides/SESSION_LIFECYCLE_DECISIONS.md) - decision tree for continue vs `/rewind` vs `/clear` vs `/compact` when degradation sets in

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
