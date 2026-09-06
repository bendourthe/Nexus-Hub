## Effort-Level Strategy

Claude Code surfaces an `effortLevel` control that governs how much reasoning the model invests per turn. Opus 4.7 exposes five tiers. Choosing the right tier deliberately is the single highest-leverage cost/quality knob in the harness - higher than model routing in many workflows.

### The five tiers

| Tier | Behavior | Typical cost | Typical latency |
|------|----------|--------------|-----------------|
| `xhigh` | Extended reasoning with adaptive thinking budget | High | Moderate |
| `high` | Strong reasoning at a lower aggregate cost than `xhigh` | Moderate-high | Moderate |
| `max` | Deepest reasoning, largest thinking budget | Highest | Slowest |
| `medium` | Balanced reasoning and speed | Moderate | Fast |
| `low` | Minimal reasoning, fastest turn-around | Low | Fastest |

### Default: `high`

Nexus-Hub ships `"effortLevel": "high"` as the Claude Code installer default (raised from `medium` in v4.4.0), with the matching `env.CLAUDE_CODE_EFFORT_LEVEL` pinned alongside it. Both are declared in `configs/platform-defaults.json`, the single source for per-platform install defaults; `catalog/hooks/settings.json` is generated from it, so consult the source rather than this paragraph if the two ever disagree. `high` matches the plan-driven, multi-step work this harness is built around, where a shallow turn costs more in rework than the extra reasoning costs to run. Drop to `medium` if you want routine turns cheaper, or escalate for a single session via `/effort xhigh`, the `--effort xhigh` CLI flag, or the `CLAUDE_CODE_EFFORT_LEVEL` environment variable; because that environment variable is the highest-precedence lever, moving your standing default means editing both keys in `settings.json`.

### When to escalate to `max`

Use `max` for **one-shot** hard problems: deep architectural analysis, gnarly debugging with many interacting variables, security-critical reviews, root-cause investigations across dense code. Typical characteristics:

- You will run the prompt once and keep the output.
- Token cost is not your primary constraint (off-peak work, research).
- The problem rewards longer thinking (`max` typically widens reasoning budget, not just depth).

**Never** leave `max` enabled on:

- Loop-operator runs or any iterative agent loop - aggregate cost compounds quickly without matching quality gains.
- Temporal-orchestration workflows spanning many turns.
- Interactive sessions where a human is waiting per turn.

### When to de-escalate to `high`

Use `high` for cost-sensitive concurrent work and multi-agent fan-out:

- Running several subagents in parallel (multi-agent-coordinator fan-out). Aggregate cost = per-agent cost x N; de-escalating one tier per agent saves ~30-50% with minimal quality impact on independent subtasks.
- Long-running loops where each iteration benefits from real reasoning but `xhigh` would be excessive.
- Concurrent operators working the same repo - the cost compounds across operators, not just across turns.

### When to use `medium` or `low`

Use `medium` or `low` for latency-sensitive, tightly-scoped tasks where reasoning overhead is wasted:

- Formatting, renaming, mechanical edits.
- Short classifications or lookups.
- Interactive clarification loops where a human is responding turn-by-turn and extended thinking adds delay without improving the answer.

### Anti-patterns

- **Defaulting to `max`.** It is not "the best setting always." On routine coding work `max` produces output indistinguishable from `xhigh` at 2-3x the cost.
- **Leaving `max` on for loop-operator / temporal runs.** The cost compounds per iteration. Switch to `high` (or at most `xhigh`) for anything iterative.
- **Mixing tiers within a single session without reason.** If you bump the tier for one turn, bump it back. Unplanned tier drift makes cost modeling impossible.
- **Setting fixed thinking-budget tokens alongside `effortLevel`.** Opus 4.7 scales thinking adaptively - fixed budgets truncate reasoning. Set `effortLevel` and let the model manage the budget.

### Decision table

| Task shape | Recommended tier |
|------------|------------------|
| Interactive coding on a familiar codebase | `xhigh` (escalate from the `high` default) |
| One-shot deep architecture / root-cause analysis | `max` |
| Multi-agent parallel fan-out (N >= 2 subagents) | `high` per agent |
| Long-running loop-operator / temporal workflow | `high` (never `max`) |
| Mechanical edits, formatting, renames | `medium` or `low` |
| Short classification / lookup | `low` |
| Latency-critical interactive clarification | `low` or `medium` |
| Security audit / pen-test deep pass | `max` (one-shot) |

### Related

- [guides/reference/SESSION_LIFECYCLE_DECISIONS.md](../../../../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) - effort level is the reasoning-per-turn dial; session-lifecycle choices are the per-session dial. Both are needed.
- [guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md](../../../../guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md) - concrete config syntax for each tier.
