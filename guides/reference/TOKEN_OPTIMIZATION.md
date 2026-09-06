# Token Optimization Guide

Practical strategies for reducing Claude Code token consumption and cost without sacrificing output quality. Drawn from production usage patterns in high-throughput development workflows.

> **See also**: [SESSION_LIFECYCLE_DECISIONS.md](SESSION_LIFECYCLE_DECISIONS.md) for the companion decision guide on when to continue, `/rewind`, `/clear`, `/compact`, or delegate to a subagent.

---

## Quick Start: Environment Variables

Add these to your shell profile (`.bashrc`, `.zshrc`, or PowerShell `$PROFILE`) for immediate savings:

```bash
# Limit extended thinking tokens (default is uncapped; 10000 covers most reasoning tasks)
export MAX_THINKING_TOKENS=10000

# Trigger context compaction at 50% window usage instead of the default (reduces mid-session bloat)
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50
```

These two settings alone produce a 40-60% reduction in token usage for most development sessions with no measurable quality drop.

---

## Model Routing Strategy

Not every task needs Opus. Routing by task complexity is the single highest-leverage optimization.

| Task Type | Recommended Model | Rationale |
|-----------|------------------|-----------|
| Complex architecture, multi-file refactors, security audits | `claude-opus-4-6` | Highest reasoning quality; worth the cost |
| Feature implementation, bug fixes, code review | `claude-sonnet-4-6` | Excellent quality at 5x lower cost than Opus |
| File formatting, docstring generation, simple lookups | `claude-haiku-4-5` | Near-instant, very low cost |
| Exploratory chats, quick questions | `claude-haiku-4-5` | Reserve Sonnet/Opus for execution |

**Rule of thumb:** Start every session on Sonnet. Switch to Opus only when you encounter a reasoning-heavy task that Sonnet visibly struggles with (ambiguous architecture decisions, complex bug triage across many files).

To check your current model and switch from within a session:

```bash
# Check usage and model recommendation
/check-usage
```

---

## Context Window Management

### Auto-Compaction

Claude Code automatically compacts the context when it approaches the window limit. The `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` variable controls the trigger threshold (default: ~85%). Setting it to 50 means compaction fires at half-window, keeping the active context lean and reducing the cost of subsequent turns.

```bash
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50
```

**Trade-off:** Earlier compaction means older context (e.g., files read at session start) may be summarized rather than retained verbatim. Use `/continue-session` to restore critical context across sessions.

#### When NOT to compact

> See also: [SESSION_LIFECYCLE_DECISIONS.md](SESSION_LIFECYCLE_DECISIONS.md) for the companion decision tree covering `/compact`, `/rewind`, `/clear`, and subagent delegation.

Autocompact is a safety net, not a strategy. Letting it fire on its own is the **bad-compact failure mode**: Claude Code summarizes mid-reasoning, drops context that was about to be used, and quality tanks for the next several turns. Symptoms you paid this tax: sudden drop in response quality, Claude re-reads files it already read, or recovery turns like "what were we working on" appear.

**Three recognition signals** that you are about to hit a bad compact:

1. **70-80% of the window used on a long, still-open task.** You are crowding the autocompact threshold while the work is still live. Do not wait for the trigger.
2. **Mid-tool-use chain.** You just kicked off a multi-step tool sequence (exploration, then synthesis, then edit). Autocompact firing between steps can drop the exploration output the synthesis step was going to use. Example: three `Read` calls followed by a planned refactor - compact now and the refactor loses the reads.
3. **Recently loaded large files or web fetches you still need.** You pulled in a 4k-line file or a long web-fetch result *for* the current task. Autocompact will summarize it away before you use it.

**Proactive remedy**: use the steerable variant of `/compact` *before* you hit the autocompact threshold, naming what to keep and what to drop:

```
/compact focus on the auth middleware refactor, drop the database schema exploration
```

You choose what the live thread is; Claude compresses the rest. Strictly better than reactive autocompact because you know which files and turns are still load-bearing.

**When to `/clear` instead**: if the current task is complete and the next task is unrelated, `/clear` beats `/compact`. Compaction keeps a summary in context that you will not use; clearing removes it entirely and the next task gets a clean first-turn specification.

### Reduce Tool Call Overhead

Each tool call (file read, grep, bash) consumes tokens for both the call and result. Reduce unnecessary calls:

- Avoid re-reading files you already read in the same session. Reference line numbers instead.
- Use `Grep` with `head_limit` to return only the lines you need.
- Prefer `Glob` over `Bash find` — Glob results are more compact.
- Batch independent reads into a single message rather than sequential messages.

### Skip Non-Essential Context

The following prompt additions reduce token consumption in most sessions:

```
Focus only on the changed files. Skip unchanged files unless directly relevant.
Summarize rather than quote long outputs — report counts, errors, and key results only.
```

The Nexus-Hub CLAUDE.md template includes an "Output Minimization" section that enforces this automatically via the installed instructions.

---

## Thinking Token Budget

Extended thinking (used for complex reasoning) consumes tokens proportional to the reasoning depth. The `MAX_THINKING_TOKENS` variable caps this budget per turn.

| Budget | When to Use |
|--------|------------|
| `5000` | Simple feature work, single-file changes |
| `10000` | Default; covers most feature and bug-fix tasks |
| `20000` | Complex multi-system design, security analysis |
| Uncapped | Rarely needed; only for open-ended research |

Set the budget in your shell profile and override per-session if a task demands deeper reasoning.

---

## Hook-Level Optimization

Nexus-Hub hooks themselves consume tokens during PostToolUse events. If you are on a tight budget, disable non-essential hooks using the runtime controls:

```bash
# Disable formatting and lint hooks (saves 2-4 tool call cycles per file write)
export NEXUS_DISABLED_HOOKS=auto-format-on-write,lint-on-write

# Use the minimal hook profile (only secret-scan and git-guardrails remain active)
export NEXUS_HOOK_PROFILE=minimal
```

Available profiles:

| Profile | Active Hooks |
|---------|-------------|
| `full` (default) | All hooks enabled |
| `minimal` | `secret-scan`, `git-guardrails` only |
| `no-format` | All except `auto-format-on-write`, `lint-on-write` |

---

## Session-Level Practices

1. **Start focused.** Open sessions with a specific goal statement. Broad exploratory prompts generate long, expensive reasoning chains.
2. **Use `/continue-session` between sessions.** Reconstructing context from scratch is expensive. The command restores the prior session state from the version's `development/history/` files and recent git history.
3. **Scope file reads tightly.** Ask for "lines 42-80 of auth.py" rather than the whole file when you already know where to look.
4. **Prefer targeted skills over open-ended prompts.** Skills in `.claude/skills/` include pre-scoped instructions that reduce back-and-forth clarification rounds.
5. **Check usage before long tasks.** Run `/check-usage` before starting a large refactor to confirm you have sufficient weekly budget.

---

## Cost Estimation Reference

Approximate token costs (input + output) for common Nexus-Hub tasks on Sonnet 4.6:

| Task | Estimated Tokens | Cost Tier |
|------|-----------------|-----------|
| `/review-codebase` (small project, <50 files) | 40,000-80,000 | Medium |
| `/generate-tests` (full codebase) | 60,000-120,000 | Medium-High |
| Single skill execution (`/security-review` one file) | 5,000-15,000 | Low |
| `/compare-project` (full repo comparison) | 80,000-150,000 | High |
| `/generate-commit-message` | 2,000-5,000 | Very Low |

Use `/check-usage` to monitor your 5-hour session and 7-day rolling limits in real time.

---

## Reference: All Optimization Variables

| Variable | Default | Recommended | Effect |
|----------|---------|-------------|--------|
| `MAX_THINKING_TOKENS` | Uncapped | `10000` | Caps extended thinking budget per turn |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | ~85 | `50` | Triggers context compaction earlier |
| `NEXUS_HOOK_PROFILE` | `full` | `minimal` (tight budget) | Selects hook activation profile |
| `NEXUS_DISABLED_HOOKS` | None | `auto-format-on-write,lint-on-write` | Disables specific hooks by name |
