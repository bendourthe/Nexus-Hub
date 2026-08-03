---
name: model-routing
description: "Detect the current agentic platform, enumerate its available models live, score a task's complexity, and recommend (then help apply) the cheapest model and reasoning effort that carries the work with zero quality loss. Use whenever the user says \"route this to the right model\", \"which model should I use\", \"pick the cheapest model that can do this\", \"is this an Opus task or a Sonnet task\", \"save tokens on this phase\", or \"what reasoning effort for this\". SKIP: checking current usage against limits -> use /usage; setting hard spend caps for autonomous agents -> ai-billing-safeguards; choosing an API PROVIDER rather than a model tier -> multi-provider-ai."
summary_l0: "Detect the platform, enumerate models live, and route a task to the cheapest capable model"
overview_l1: "Routes a task to generic capability tier and effort, then resolves that intent for the active platform without quality loss. Direct /route use detects the platform, enumerates its live model set, scores five complexity signals, and applies host-native switch mechanics. Planning use records frontier/strong/standard/fast plus low/medium/high/max and keeps concrete Anthropic/OpenAI/Google/Cursor ids in a separately refreshed plan map so recommendations survive platform changes. SKIP for usage-limit checks, hard spend caps, or provider selection."
---

# Model Routing

Route a task to the cheapest model and reasoning effort that can carry it with no loss in output quality. The premise: most implementation work does not need the strongest model, but a minority genuinely does, and guessing wrong on the minority is expensive. This skill downshifts the easy majority on a high-confidence reading and defaults to the strongest available tier whenever the reading is uncertain or any signal is high. To the user it looks like the best model was used for everything, while the easy 70 percent costs less.

The skill is platform-agnostic by a small capability abstraction (a routing profile per platform), not by a per-model special case. Direct recommendation and switching introduce no new outbound call, dependency, or credential: every enumeration and switch surface belongs to the platform the user is already running. The one optional direct-routing network call (the Anthropic `GET /v1/models` enumeration) is best-effort and used only when an `ANTHROPIC_API_KEY` is already present; otherwise the skill falls back to the platform's model picker.

> **Planning contract vs. direct switching.** `/plan` records only generic `frontier` / `strong` / `standard` / `fast` tier and `low` / `medium` / `high` / `max` effort in each phase. Its separate Current model map is refreshed from public Anthropic, OpenAI, Google, and Cursor documentation and may use a visibly dated offline fallback. The direct `/route` flow below remains host-native and validates the chosen model against the detected platform before switching. The exact plan-document schema is defined in `docs/v3/v3.15/development/cross-provider-routing-contract.md`; Phase 2 supplies the map-refresh helpers.

> **Model choice is the reliable cost lever; some context tricks are not.** Some token-cost techniques are vision-encoder-specific rather than universal: rendering static context as images to save tokens works only on encoders that tolerate dense rendering, and it inverts on the high-resolution image-billing tier that strong reasoning models use (Opus-class, Sonnet 5, Fable 5), where a legible page costs more tokens than the equivalent text while exact strings are silently corrupted. Choosing the cheapest capable model for a task is the more reliable, lossless cost lever than lossily compressing context to fit an expensive one. See [[prompt-token-optimization]] for the full treatment of image-token / optical compression.

## When to Use This Skill

Use this skill for:

- Deciding which model a task, plan phase, or session needs ("is this an Opus task or a Sonnet task").
- Choosing a reasoning-effort level for a task to balance cost, latency, and quality.
- Recommending the cheapest capable model when a user asks to "save tokens" without losing quality.
- Wiring planning-time or implementation-time routing into a `/plan` or `/implement` loop.
- Producing a defensible recommendation (reasoning plus best-effort citations) before switching.

**When NOT to use this skill**:

- Checking current consumption against your usage window or rate limit -- use `/usage` (the `check-usage` skill); this skill is the task-time counterpart, not a consumption monitor.
- Enforcing a hard dollar spend cap on an autonomous agent -- use `[[ai-billing-safeguards]]`; routing recommends a tier, it does not block execution at a budget.
- Choosing an API provider (Anthropic vs. Bedrock vs. Vertex vs. OpenRouter) rather than a model tier -- use `[[multi-provider-ai]]`.

## Instructions

Run the steps in order. Steps 1-2 gather the live facts; steps 3-4 decide; steps 5-6 present and apply.

### Step 1: Detect the platform

Identify which agentic platform is running before assuming any model names or switch mechanics. Run the bundled helper rather than guessing:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.sh
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.ps1
```

The helper prints a single normalized platform id (`claude-code`, `codex`, `antigravity`, `gemini-cli`, `cursor`, `copilot`, `opencode`, or `unknown`) from environment cues that are already present (the `CLAUDECODE` / `CLAUDE_CODE_*` env vars, the `codex` / `agy` / `gemini` binaries on PATH and their config dirs, Cursor / Copilot markers). It makes no network call and requires no credential.

### Step 2: Enumerate available models live

Never assume a fixed catalog -- model lists go stale within weeks. Enumerate from the detected platform's own surface:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.sh <platform-id>
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.ps1 <platform-id>
```

The helper prints the available models as JSON by calling that platform's enumeration command (see the routing profiles below). For Claude Code it issues the optional `GET /v1/models` call only when `ANTHROPIC_API_KEY` is set; otherwise it prints a sentinel telling you to read the model set from the `/model` picker. Cache the result for the session so you enumerate once, not per task.

### Step 3: Score the task on the complexity rubric

Score the task on five signals. Each signal is `low`, `medium`, or `high`. Be honest: under-scoring is the failure mode that breaks the quality guarantee.

| Signal | low | medium | high |
|---|---|---|---|
| **Task scope** | one file, one function | a few related files | cross-cutting, many modules |
| **Structural complexity** | boilerplate, mechanical | standard pattern, some logic | novel algorithm or architecture |
| **Context volume required** | localized, self-contained | a handful of files to read | large, spread across the repo |
| **Risk / blast radius** | throwaway, tests, docs | internal feature code | production, security, data, migration |
| **Reasoning type** | rename, format, lookup | compose known pieces | design, debug, optimize, prove |

### Step 4: Map the score to a model and effort (strong-tier default)

Apply this rule, in order:

1. **If the assessment is uncertain, OR any single signal is `high`** -> pin the **strongest available** model in the enumerated set and a **high** reasoning effort. This is the no-degradation guarantee. Do not downshift on a hard or unclear task.
2. **If all signals are `low`** -> route to the **cheapest** capable model and a **low** effort. This is where the savings come from.
3. **Otherwise (a mix of `low` and `medium`, no `high`, not uncertain)** -> route to a **mid** tier and a **medium** effort.

| Aggregate reading | Model tier | Reasoning effort |
|---|---|---|
| Any `high`, or uncertain | strongest available | high / max |
| All `low` | cheapest available | low |
| Mixed low/medium, no high | mid tier | medium |

The tier names map to whatever the live enumeration returned -- "strongest available" is the top model in the set, not a hardcoded `opus`. Effort levels map to the platform's effort knob (see the profiles): Claude Code uses `/effort` (`low` / `medium` / `high` / `xhigh` / `max`); Codex uses `model_reasoning_effort`; manual platforms have no effort knob, so the recommendation is model-only.

### Step 5: Assemble the recommendation

Present the recommendation with its reasoning, never a bare model name:

- The chosen model id (which MUST appear in the step-2 enumerated set) and the effort level.
- The per-signal rubric reading that produced it (so the user can challenge a score).
- Best-effort citations (model docs, pricing pages) ONLY when the harness already has web access; never block on the network. If offline, say so and proceed.

### Step 6: Apply the switch per the platform's tier

Switching is a three-tier spectrum, not uniform automation (see the routing profiles). The posture is **confirm, then auto-execute**: present the recommendation, get approval, then act per the platform's `can_script_switch`:

- **Scriptable** (Codex, Antigravity `agy`, Gemini CLI): execute the switch directly (a `-c` / `-m` / `--profile` invocation or a config write). Run the bundled helper, which validates the requested model against the enumerated set before acting and is idempotent:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/switch-model.sh <platform-id> <model-id> [effort]
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/switch-model.ps1 <platform-id> <model-id> [effort]
```
- **One user action** (Claude Code): the main loop cannot switch its own model mid-session. Emit the exact one-key `/model` and `/effort` instruction, AND auto-route any delegated subagent work to the chosen tier via the Task / Workflow `model` parameter (the built-in `opusplan` alias is native routing of this shape).
- **Manual only** (Cursor, Copilot, OpenCode): no flag, env, config, or rule field pins a model. Emit the recommendation plus a "select X in the model picker" instruction.

### Step 7: Mid-task escalation during an implement loop (upshift only)

When routing is wired into an implementation loop (the `/implement` per-phase pre-flight), persistent failure is itself a routing signal. If a phase's tests fail repeatedly -- after several troubleshooting iterations on the same failure -- the task was likely under-tiered, so recommend an **upshift** to a stronger reasoning tier or a higher effort before continuing. Rules:

- **Upshift only.** Never auto-downshift mid-phase: the no-degradation guarantee forbids dropping to a cheaper model while a task is actively failing, because a downshift mid-failure trades the one thing routing must never gamble on (output quality on a hard task) for marginal token savings.
- **Best-effort and platform-aware.** Follow the same posture as Step 6 -- on Claude Code surface the `/model` + `/effort` keystroke; on scriptable platforms (Codex, Antigravity `agy`, Gemini CLI) apply it with confirmation; on manual-only platforms print the picker instruction.
- **Confirm, do not silently switch.** Surface that repeated failure triggered the escalation so the user can approve the stronger tier; it is a confirm-then-apply action, not an automatic one.

## Platform routing profiles

Each platform is a small profile. Adding a platform is adding a row, not rewriting the router. The fields are `can_script_switch`, `enumerate_command` / `model_list_source`, `switch_mechanism`, and `effort_knob`.

| Platform | can_script_switch | Enumerate (model_list_source) | switch_mechanism | effort_knob |
|---|---|---|---|---|
| Claude Code | one-action | `GET /v1/models` if key set, else `/model` picker | `/model` + `/effort` keystroke; Task/Workflow `model` param for subagents | `/effort` (low/medium/high/xhigh/max) |
| Codex | yes | `codex debug models` (JSON) | `-c model=...` / `-c model_reasoning_effort=...` or `--profile` | `model_reasoning_effort` (low/medium/high) |
| Antigravity (`agy`) | yes | `agy models` | `agy -m <model>` flag / config key | config key (if exposed) |
| Gemini CLI | yes | alias set / `settings.json` model aliases | `--model` / `GEMINI_MODEL` / `settings.json model.name` | none documented |
| Cursor | manual | in-app model picker | select in the model picker (no scriptable surface) | none |
| Copilot | manual | in-app model picker | select in the model picker | none |
| OpenCode | manual | `opencode models` / config | select in config or picker | none |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This phase looks simple, so the cheap model is fine." | "Looks simple" is exactly the under-scoring failure. If the change touches production, security, or data (high blast radius), a wrong cheap-model output costs far more than the tokens saved. Any single high signal pins the strong tier -- scope alone does not earn a downshift. |
| "I'll just hardcode the current model names so I don't have to enumerate." | Model catalogs change within weeks; a new, cheaper, or stronger model ships and the hardcoded list silently routes to a stale option. The whole skill is built on live enumeration precisely so the recommendation survives a model release. |
| "Auto-switching works everywhere, so I'll script it on every platform." | The Claude Code main loop cannot switch its own model mid-session, and Cursor / Copilot / OpenCode expose no scriptable switch at all. Scripting a switch on a manual platform either no-ops silently or errors; the posture must branch on `can_script_switch`. |
| "When unsure, I'll pick the mid tier as a safe middle ground." | Uncertainty is a high-risk signal, not a neutral one. The guarantee is to default UP to the strongest tier when the reading is unclear, because the cost of an under-tiered hard task (rework, wrong output shipped) dwarfs the marginal token cost of one strong-tier run. |

## Verification

- [ ] The recommended model id appears verbatim in the step-2 live-enumerated set (or the model-picker sentinel was returned and the recommendation is tier-named).
- [ ] The recommendation states the per-signal rubric reading, not just a model name.
- [ ] Any task scored `high` on at least one signal, or scored as uncertain, resolves to the strongest available tier and a high/max effort.
- [ ] The switch instruction matches the detected platform's `switch_mechanism` (scriptable execute / Claude Code keystroke / picker instruction) and never scripts a switch on a manual-only platform.
- [ ] No hardcoded model list is used; the model set came from `enumerate-models`.
- [ ] A mid-task escalation (Step 7) only ever upshifts the tier or effort; the router never auto-downshifts a model mid-phase while a task is failing.
- [ ] No new outbound call, dependency, or credential was introduced; the only optional network call (`GET /v1/models`) ran only because a key was already present.

## Related Skills

- [[multi-provider-ai]] -- choosing the API provider (Anthropic / Bedrock / Vertex / OpenRouter); this skill reuses its tier abstraction but enumerates dynamically instead of from a hardcoded matrix.
- [[prompt-engineering]] -- operationalizes its task-complexity routing table and effort-level strategy; this skill is the platform-aware, live-enumerated extension of that section.
- [[ai-billing-safeguards]] -- hard spend caps the router respects; routing recommends a tier, billing-safeguards block at a budget.
- [[agent-orchestration-primitives]] -- decides whether to fan out at all; routing then picks the tier each agent runs on.
- [[implementation-plan]] -- scores plan phases to generic tier/effort and owns the dated four-provider Current model map.
- `/usage` (the `check-usage` skill) -- the consumption-time counterpart that reports usage against limits; this skill is the planning/task-time counterpart and does not duplicate it.

---

**Version**: 1.1.0
**Last Updated**: June 2026
