# Operator Migration Guide: Opus 4.6 -> Opus 4.7

**Audience**: operators running DevAI-Hub on Opus 4.7 who were previously on Opus 4.6 (including mixed 4.6-era habits carried forward). If you started on 4.7 and have never shipped a 4.6 session, most of this guide is informational rather than actionable - skim the **Operator must-do** section then stop.

**Source**: synthesized from Anthropic's ["Best practices for using Claude Opus 4.7 with Claude Code"](https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code) and the DevAI-Hub gap analysis at [docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md](comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md).

**Release that shipped these changes**: v0.9.7 (see [CHANGELOG.md](../../CHANGELOG.md)).

---

## TL;DR

Four things to do today, in order:

1. Reconfirm your `effortLevel`. The DevAI-Hub default is `xhigh`; `max` is almost never correct on iterative or parallel workloads.
2. Adopt explicit parallel-fan-out prompting. 4.7 does not volunteer concurrency; you must ask for it.
3. Remove any `max_thinking_tokens=N` settings you still have. Let 4.7 scale thinking adaptively.
4. Update your clarifying-questions habit to batch into the first turn rather than drip one question per turn.

If you do those four things and do nothing else, you will capture ~80% of the value of 4.7 over 4.6. The rest of this guide covers model-side changes that require no action, things to remove, and a cross-reference table from every behavioral delta to its canonical location in the DevAI-Hub catalog.

---

## Operator must-do

These are operator-side changes: habits, configuration, and prompt shape you need to actively update. Each links to the canonical skill or guide that documents the change in depth.

### 1. Reconfirm `effortLevel`

**What changed**: 4.7 exposes a five-tier effort hierarchy (`xhigh` / `high` / `max` / `medium` / `low`). The DevAI-Hub installer writes `effortLevel: xhigh` by default. On 4.6, `max` was often the reflex choice for hard problems; on 4.7, `max` compounds cost on iterative or parallel workloads without matching quality gains.

**Action**:
- Verify `effortLevel` in your `~/.claude/settings.json` or the DevAI-Hub catalog template (`catalog/hooks/settings.json`) is `xhigh`. Do not leave it at `max`.
- For loop-operator runs, temporal-orchestration workflows, and multi-agent fan-out: set per-context effort to `high`, not `xhigh`. Aggregate cost matters.
- Reserve `max` for single-turn deep analyses (security audits, architectural review, root-cause investigations) where you want one-shot depth without caring about latency.

**Canonical location**: [catalog/skills/ai-development/prompt-engineering/SKILL.md - Effort-Level Strategy section](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#effort-level-strategy).

### 2. Adopt explicit parallel-fan-out prompting

**What changed**: 4.6 would frequently volunteer concurrent subagent spawning when the task was obviously parallelizable. 4.7 does not. An ambiguous instruction like "explore these areas" usually sequentializes on 4.7 unless you ask for parallelism explicitly.

**Action**: when you want N agents to run in parallel, name it:

> "Spawn 3 subagents in parallel: one to do X, one to do Y, one to do Z. Send them in a single message."

Generic phrasing that worked on 4.6 ("check everything") now produces serial behavior on 4.7.

**Canonical location**: [catalog/skills/orchestration/multi-agent-coordinator/SKILL.md - Pattern A: Parallel Launch for Independent Agents](../../catalog/skills/orchestration/multi-agent-coordinator/SKILL.md) - includes the Opus 4.7 behavior callout and three worked fan-out prompts (research, code generation, verification).

### 3. Remove fixed thinking-budget parameters

**What changed**: 4.7 scales its thinking budget adaptively per turn based on task difficulty. Fixed thinking budgets (`max_thinking_tokens=20000`, explicit budget flags, per-turn overrides) truncate reasoning on hard turns and waste budget on easy ones. On 4.6 a fixed budget was a defensible cost-control lever; on 4.7 it is an anti-pattern.

**Action**:
- Remove every `max_thinking_tokens` setting from your config, wrapper scripts, and API calls. Do not replace with a different fixed number.
- If you need to cap reasoning for cost reasons, drop one effort tier (`xhigh` -> `high`, `high` -> `medium`) rather than clamping thinking tokens directly.
- Replace prompts like "use 20k thinking tokens for this" with "think through this carefully."

**Canonical location**: [catalog/skills/ai-development/ai-agent-development/SKILL.md - Anti-Patterns (Opus 4.7)](../../catalog/skills/ai-development/ai-agent-development/SKILL.md) - row 1 of the Anti-Patterns table explains why fixed budgets hurt on 4.7.

### 4. Batch clarifying questions into the first turn

**What changed**: the 4.6-era habit of asking one clarifying question per turn wastes 4.7's reasoning budget and your context. 4.7 can absorb a five-line specification (goal / constraints / acceptance / out-of-scope / context pointers) in the first turn and commit its reasoning to the right target immediately. Per-question ping-pong dilutes it.

**Action**:
- Front-load your first turn with the five-line specification (see the skill's "First-turn specification checklists" section).
- When ambiguity remains, surface multiple interpretations and acceptance criteria together so the user answers them in a single round-trip.
- Do not ask one question, wait, ask the next, wait again. This pattern leaked into many 4.6-era session habits and it is now actively counterproductive.

**Canonical locations**:
- Platform templates (the rule itself): [templates/ai-instructions/base-claude.md](../../templates/ai-instructions/base-claude.md) and the four companion `base-*.md` files in the same directory.
- First-turn template: [catalog/skills/ai-development/prompt-engineering/SKILL.md - Opus 4.7 Practices - First-turn specification checklists](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#opus-47-practices).

---

## Informational (model-side, no action needed)

These are 4.6 -> 4.7 behavioral shifts you should be *aware* of. They do not require any change to your config, prompts, or habits - but understanding them prevents you from mis-diagnosing 4.7 behavior as regressions.

### Auto-calibrated response length

**What changed**: 4.6 was more verbose by default; 4.7 adapts response length to task complexity, producing shorter responses on simple tasks and longer responses on dense ones. If your 4.6 session habit was "the response is too long, prompt for brevity," drop that rule - 4.7 is already doing the calibration. Adding brevity pressure on top of 4.7's adaptive length usually over-clips output.

**What NOT to do**:
- Do not add "be concise" to every first turn. On simple tasks 4.7 is already concise; on complex tasks the added pressure strips useful detail.
- Do not codify per-message length caps in your base templates. The installer defaults are correct for 4.7.

### Reasoning-first posture

**What changed**: 4.7 prefers reasoning over tool invocation when given an ambiguous choice. It will think through a problem before reaching for tools, where 4.6 was more likely to tool-first. This is mostly a win - tool calls cost tokens and latency - but it means 4.7 needs explicit prompting when you do want a tool run.

**What NOT to do**:
- Do not prompt "check for issues" and expect 4.7 to run your lint pipeline. Name the tool: "run `ruff check .` and report violations."
- Do not interpret "4.7 is not running tools like 4.6 did" as a regression. It is a deliberate shift - and usually the right default.

---

## What to remove from your project

If your project still carries any of the following, delete or rewrite it:

- **Guide or rule codifying "always prefer tools over reasoning"** - this was appropriate 4.6-era advice; it is backwards on 4.7.
- **Per-turn thinking-budget clamps** in hook scripts, installer defaults, or CI configs.
- **4.6-specific tool-first prompt prefaces** like "before reasoning, check the following tools..." - 4.7 handles tool selection itself with an explicit nudge.
- **Unbounded clarifying-questions rules** in your CLAUDE.md / AGENTS.md / equivalent. The DevAI-Hub base templates shipped the batched variant in v0.9.7; if your project uses custom templates, mirror the change.
- **Stale verbosity guidance**: "keep responses under 200 words unless asked to be longer" is a 4.6-era rule that fights 4.7's auto-calibrated length. Remove it unless a specific downstream consumer (log parser, CI checker) actually needs a hard word cap.

---

## Cross-reference table: behavioral delta -> canonical location

Every 4.6 -> 4.7 behavioral delta has a single canonical location in the DevAI-Hub catalog. Use this table as the index when you need to re-read or share context.

| Delta | Canonical location | What you will find there |
|-------|--------------------|---------------------------|
| Five-tier effort hierarchy (`xhigh`/`high`/`max`/`medium`/`low`) | [prompt-engineering/SKILL.md - Effort-Level Strategy](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#effort-level-strategy) | Per-tier cost/latency notes, default rationale, escalation/de-escalation rules, anti-patterns, decision table |
| Reasoning-first posture (reasoning > tools when ambiguous) | [ai-agent-development/SKILL.md - Anti-Patterns (Opus 4.7)](../../catalog/skills/ai-development/ai-agent-development/SKILL.md) | Row 2 of the Anti-Patterns table ("Excessive tool-calling as thorough investigation") |
| Explicit parallel fan-out required | [multi-agent-coordinator/SKILL.md - Pattern A + Step 0 delegation gate](../../catalog/skills/orchestration/multi-agent-coordinator/SKILL.md) | Pattern A callout + three worked fan-out prompts + the "should I delegate" reuse test |
| No fixed thinking budgets | [ai-agent-development/SKILL.md - Anti-Patterns (Opus 4.7)](../../catalog/skills/ai-development/ai-agent-development/SKILL.md) and [prompt-engineering/SKILL.md - Adaptive thinking](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#opus-47-practices) | Why fixed budgets truncate; how to cap reasoning via effort tier instead |
| Batched clarifying questions | [templates/ai-instructions/base-claude.md Critical Rules](../../templates/ai-instructions/base-claude.md) (+ 4 sibling templates + global `CLAUDE.md`) | The replacement rule verbatim; first-turn specification template lives in `prompt-engineering/SKILL.md` Opus 4.7 Practices |
| Positive examples over negative instructions | [prompt-engineering/SKILL.md - Opus 4.7 Practices](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#opus-47-practices) | Before/after tables for three canonical prompt shapes |
| Explicit tool-invocation prompting | [prompt-engineering/SKILL.md - Opus 4.7 Practices](../../catalog/skills/ai-development/prompt-engineering/SKILL.md#opus-47-practices) | "Check for issues" (bad) vs "run `ruff check src/auth.py`" (good) pattern table |
| Auto-calibrated response length | (no action needed - informational only) | Remove length caps from base templates if carried over from 4.6 |
| Proactive `/compact focus on X, drop Y` | [context-compression/SKILL.md - Proactive steering subsection](../../catalog/skills/orchestration/context-compression/SKILL.md) and [guides/TOKEN_OPTIMIZATION.md - When NOT to compact](../../guides/TOKEN_OPTIMIZATION.md) | Six directly-usable steering directives + recognition signals for bad-compact |
| 1M-context Lost-in-Middle calibration (300-500k threshold) | [context-degradation/SKILL.md - Step 1 calibration table](../../catalog/skills/orchestration/context-degradation/SKILL.md) | Green/Yellow/Orange/Red token-band table with recommended actions |
| Session lifecycle decisions (continue / `/rewind` / `/clear` / `/compact` / delegate) | [guides/SESSION_LIFECYCLE_DECISIONS.md](../../guides/SESSION_LIFECYCLE_DECISIONS.md) | Five-branch decision tree + three worked examples + "summarize from here" handoff |
| "Summarize from here" mid-session handoff | [session-history/SKILL.md - Operating Modes](../../catalog/skills/workflow/session-history/SKILL.md) | Handoff message template + four-step usage pattern |
| Default hunter effortLevel for parallel security audits | [catalog/commands/run-penetration-test.md - Phase 2 header](../../catalog/commands/run-penetration-test.md) | `effortLevel: high` default with cross-reference to the Effort-Level Strategy |

---

## Migration checklist

Use this checklist the next time you open a DevAI-Hub-tracked project that has been dormant since 4.6:

- [ ] Open `~/.claude/settings.json` and confirm `effortLevel` is `xhigh` (or `high` if you are on an iterative-heavy workload).
- [ ] Grep your project for `max_thinking_tokens` and remove every hit. Replace with effort-tier adjustments if needed.
- [ ] Grep your project templates and guides for "ask clarifying questions before coding" - if the wording is the unbounded 4.6-era variant, replace with the batched-first-turn rule.
- [ ] Open any hook scripts, wrapper CLIs, or CI configs that invoke Claude Code; confirm none pass fixed thinking budgets.
- [ ] Read [guides/SESSION_LIFECYCLE_DECISIONS.md](../../guides/SESSION_LIFECYCLE_DECISIONS.md) once; the five-branch decision tree is the most valuable ~5 minutes you can spend before your next long session.
- [ ] If you manage a team: share this guide's TL;DR section. The four must-do items cover the changes that actually affect behavior day-to-day.

---

## Sources

- Anthropic - "Best practices for using Claude Opus 4.7 with Claude Code" (canonical blog post).
- Anthropic - "Managing Claude Code sessions on the 1M context window" (session-management post).
- DevAI-Hub gap analyses: [comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md](comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md) and [comparison-claude-code-session-management-1m-context.md](comparison-claude-code-session-management-1m-context.md).
- v0.9.7 release: [CHANGELOG.md](../../CHANGELOG.md).
