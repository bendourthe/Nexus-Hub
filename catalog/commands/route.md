---
description: Detect the current platform, enumerate its models live, score a task, and recommend (then with confirmation apply) the cheapest model and reasoning effort that carries it with no quality loss. Use to "route this to the right model", "which model should I use", "pick the cheapest model that can do this", "is this an Opus task or a Sonnet task", "save tokens on this phase", "what reasoning effort for this". SKIP - checking usage against limits (use /usage), hard spend caps for autonomous agents (ai-billing-safeguards), or choosing an API provider rather than a model tier (multi-provider-ai).
---

# /route Command

Recommend - and, with confirmation, apply - the cheapest model and reasoning effort that can carry a task with no loss in output quality. `/route` detects the agentic platform you are running, enumerates that platform's available models live (no hardcoded list), scores the task on a complexity rubric, and produces a defensible recommendation, defaulting to the strongest available tier whenever the reading is uncertain or any signal is high (the no-degradation guarantee).

This is a thin dispatcher over the retained `model-routing` skill. The heavy logic - platform detection, live enumeration, the complexity rubric, the strong-tier-default rule, and the per-platform switch mechanics - lives in that skill; this file resolves the target, delegates, and applies the switch posture.

## Target resolution

Resolve a TARGET from the first positional argument (`$ARGUMENTS`):

- `/route phase N of <plan-path>` or `/route <plan-path> phase-N` - assess that specific plan phase. Read the named plan, locate the phase, and assess its scope and sub-tasks (the phase Goal, the sub-task prompts, and the Stability Gate are the rubric inputs).
- `/route "<free-text task>"` - assess the quoted task description directly.
- `/route` (bare) - assess the current in-flight task inferred from the conversation context. If the current task is ambiguous, state the assumption you are scoring before recommending.

## Delegation

Dispatch the resolved target to the `[[model-routing]]` skill, which runs its own sequence:

      (any invocation) -> model-routing

The skill detects the platform (`scripts/detect-platform.{sh,ps1}`), enumerates the live model set from that platform's own surface (`scripts/enumerate-models.{sh,ps1}`), scores the task on the five-signal rubric, maps the score to a model + reasoning effort with the conservative strong-tier default, and assembles the recommendation with its per-signal reasoning and best-effort citations. Pass the resolved target through unchanged.

## Switch posture: confirm, then auto-execute

After the skill produces a recommendation, present it (the model id, the effort level, and the rubric reading that produced it), ask the user to approve, and on approval act per the detected platform's tier in the switch spectrum:

- **Scriptable** (Codex, Antigravity `agy`, Gemini CLI): execute the switch directly via the bundled helper `scripts/switch-model.{sh,ps1}`, which validates the model against the enumerated set before acting and is idempotent.
- **One user action** (Claude Code): the main loop cannot switch its own model mid-session. Print the exact one-key `/model` and `/effort` instruction, and offer to route any delegated subagent work to the chosen tier via the Task / Workflow `model` parameter.
- **Manual only** (Cursor, Copilot, OpenCode): no scriptable switch surface exists. Print the recommendation plus a "select X in the model picker" instruction.

Never script a switch on a manual-only platform, and never apply a switch without approval. If the platform is unknown or enumeration is unavailable, the skill falls back to the model-picker sentinel; surface the recommendation as tier intent ("strong reasoning tier, high effort") and proceed without failing.

## Notes

- Keep this dispatcher thin. The routing logic and the platform profiles live entirely in the `model-routing` skill.
- Platform-agnostic by design: the recommendation records tier intent alongside the concretely-enumerated model name, so it survives a platform switch.
- Adds zero new outbound calls, dependencies, or credentials. The only optional network call is the Anthropic `GET /v1/models` enumeration, made strictly when `ANTHROPIC_API_KEY` is already present; otherwise the model picker is used.
