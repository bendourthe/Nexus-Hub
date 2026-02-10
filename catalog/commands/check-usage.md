---
description: Check your Claude Code usage limits and get smart model-switching recommendations based on current consumption.
---

# Check Usage Command

Analyze your current Claude Code usage limits and provide actionable recommendations for model selection and usage optimization.

## Phase 1: Collect Usage Data

Ask the user to provide their current usage data from `claude.ai/settings/usage`. Collect the following:

1. **Current Session**:
   - Usage percentage (e.g., 92%)
   - Reset timer (e.g., "Resets in 3 min")

2. **Weekly Limits (All Models)**:
   - Usage percentage (e.g., 11%)
   - Reset timer (e.g., "Resets Fri 1:59 PM")

3. **Weekly Limits (Sonnet Only)**:
   - Usage percentage (e.g., 0%)
   - Reset timer (e.g., "Resets Mon 10:59 AM")

4. **Current Model**: Which model are you using right now? (Opus 4.6, Sonnet 4.5, or Haiku 4.5)

If the user provides all data at once (e.g., pasted from the usage page), parse it directly instead of asking individual questions.

## Phase 2: Analyze & Classify

Classify each usage metric into urgency levels:

| Usage % | Level | Indicator | Action |
|---|---|---|---|
| 0-50% | Low | GREEN | Continue current model freely |
| 51-75% | Moderate | YELLOW | Be mindful of task complexity |
| 76-90% | High | ORANGE | Model switch recommended |
| 91-100% | Critical | RED | Immediate switch or wait for reset |

## Phase 3: Generate Recommendations

Apply the following model switch logic based on the collected data:

### Model Switch Matrix

| Situation | Recommendation |
|---|---|
| Using Opus, session usage >75% | Switch to Sonnet 4.5 for routine coding tasks. Reserve Opus for architecture decisions and complex reasoning. |
| Using Opus, weekly all-models >75% | Switch to Sonnet 4.5 until the weekly reset. Sonnet handles most coding tasks effectively. |
| Using Sonnet, weekly all-models >75% | Use Haiku 4.5 for simple tasks (lookups, small edits, explanations). Save Sonnet for complex logic. |
| Sonnet-only limit >75% | Switch to Opus or Haiku (neither counts against the Sonnet-only limit). |
| Any model, session >90% | Pause and wait for session reset (typically resets within minutes). Use the break productively. |
| All limits <50% | Stay on your current model. You have plenty of capacity. |

### Optimization Tips (include when usage is Moderate or higher)

- **Use `/compact`** to reduce context window consumption in long conversations
- **Batch related questions** into single, well-structured prompts instead of many small ones
- **Use plan mode** for complex tasks to reduce iteration cycles and wasted tokens
- **Match model to task complexity**:
  - Haiku 4.5: Simple lookups, formatting, small edits, explanations
  - Sonnet 4.5: Standard coding, debugging, refactoring, test writing
  - Opus 4.6: Architecture design, complex reasoning, multi-file refactors, plan mode
- **Use subagents** for parallelizable research (focused prompts consume fewer tokens)
- **Start new conversations** for unrelated tasks instead of extending long threads

## Phase 4: Output Report

Present the analysis in this format:

```markdown
## Claude Usage Report

| Metric | Usage | Resets In | Status |
|---|---|---|---|
| Session | [X]% | [timer] | [GREEN/YELLOW/ORANGE/RED] |
| Weekly (all models) | [X]% | [timer] | [GREEN/YELLOW/ORANGE/RED] |
| Weekly (Sonnet only) | [X]% | [timer] | [GREEN/YELLOW/ORANGE/RED] |

**Current Model**: [model name]

---

### Recommendation

[Primary recommendation based on the most urgent metric. Be specific and actionable.]

[If applicable, include secondary recommendation for longer-term optimization.]

### Usage Tips

[Include 2-3 of the most relevant optimization tips based on the user's current situation.]

---

### What would you like to do?
1. **Get model guidance** for a specific task I'm about to work on
2. **Show all optimization tips** for reducing token consumption
3. **No action needed** (review complete)
```

## Edge Cases

- **All metrics are GREEN**: Congratulate the user and confirm they can continue freely. Still mention the model-to-task matching tip as a general best practice.
- **Session is RED but weekly is GREEN**: Emphasize that this is temporary. Suggest waiting a few minutes for the session reset rather than switching models.
- **Weekly is RED**: This is the most impactful scenario. Strongly recommend switching to a lighter model and provide specific task-matching guidance.
- **User doesn't know their usage**: Direct them to `claude.ai/settings/usage` or suggest they run `/usage` in their Claude Code terminal session.

## Iterative Refinement

If the user selects option 1 ("Get model guidance"), ask them to describe their upcoming task and recommend the most cost-effective model that can handle it well. Provide a brief rationale for the recommendation.
