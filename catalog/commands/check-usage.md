---
description: Check your Claude Code usage limits and get smart model-switching recommendations based on current consumption.
---

# Check Usage Command

Analyze your current Claude Code usage limits and provide actionable recommendations for model selection and usage optimization.

## Phase 0: Auto-Fetch Usage Data

Before asking the user for manual input, attempt to fetch usage data automatically from the Anthropic API.

1. Read the OAuth access token from `~/.claude/.credentials.json` (field: `claudeAiOauth.accessToken`).
2. Fetch usage data using Bash:
   ```bash
   curl -s -H "Authorization: Bearer TOKEN" \
        -H "anthropic-beta: oauth-2025-04-20" \
        https://api.anthropic.com/api/oauth/usage
   ```
3. If the API call succeeds, parse the JSON response:
   - `five_hour.utilization` → Session usage %
   - `five_hour.resets_at` → Session reset time (ISO 8601)
   - `seven_day.utilization` → Weekly (all models) usage %
   - `seven_day.resets_at` → Weekly reset time
   - `seven_day_sonnet.utilization` → Weekly (Sonnet only) usage %
   - `seven_day_sonnet.resets_at` → Sonnet reset time
4. Convert `resets_at` timestamps to human-readable relative times (e.g., "3 min", "Fri 1:59 PM").
5. If auto-fetch succeeds, **skip Phase 1 entirely** and proceed to Phase 2 with the fetched data.

If auto-fetch fails for any reason (no credentials file, expired token, network error, missing curl), fall back to Phase 1.

## Phase 1: Manual Usage Data Collection (Fallback)

Only use this phase if Phase 0 auto-fetch failed. Ask the user to provide their current usage data from `claude.ai/settings/usage`. Collect the following:

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
- **User doesn't know their usage**: Auto-fetch should handle this automatically. If auto-fetch also fails, direct them to `claude.ai/settings/usage`.
- **Auto-fetch returns expired token**: Inform the user their Claude Code session may need re-authentication and fall back to manual entry.

## Related Features

This command is one of three complementary usage monitoring features:

- **CLI Usage Display** (`.claude/hooks/usage-display.sh`): Automatic Stop hook that shows a compact one-line usage summary after each Claude Code response when any metric exceeds 50%. Passive monitoring, no user action required.
- **VS Code Extension** (`extensions/claude-usage-monitor/`): Status bar indicator, SVG tooltip, and full dashboard panel. Best for VS Code users who want persistent visual monitoring.
- **This command** (`/check-usage`): On-demand detailed report with model-switching recommendations and optimization tips. Best for a comprehensive assessment at a specific point in time.

## Iterative Refinement

If the user selects option 1 ("Get model guidance"), ask them to describe their upcoming task and recommend the most cost-effective model that can handle it well. Provide a brief rationale for the recommendation.
