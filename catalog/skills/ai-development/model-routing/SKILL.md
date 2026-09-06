---
name: model-routing
description: "Score work to a portable model tier and effort, refresh the Anthropic/OpenAI/Google/Cursor model map for plans, and resolve that intent to a live host model for implementation or switching. Use whenever the user says \"route this to the right model\", \"which model should I use\", \"pick the cheapest model\", \"save tokens on this phase\", \"what reasoning effort\", or when /plan or /implement needs model routing. SKIP: checking usage limits -> /usage; hard spend caps -> ai-billing-safeguards; choosing an API provider -> multi-provider-ai."
summary_l0: "Score portable routing intent, refresh provider maps, and resolve it on the active platform"
overview_l1: "Routes work without locking a plan to its authoring host. Planning scores five signals to frontier/strong/standard/fast plus low/medium/high/max, then validates a websearch-refreshed Anthropic/OpenAI/Google/Cursor map or emits a visibly dated offline fallback. Implementation re-confirms that generic intent and resolves the selected provider cell without downshifting. Direct /route use still detects the host, enumerates its live models, and applies platform-native switch mechanics. SKIP for usage-limit checks, hard spend caps, or provider selection."
---

# Model Routing

Route a task to the cheapest capability tier and reasoning effort that can carry it with no loss in output quality. Long-lived plans record portable intent, not a product name: `frontier` / `strong` / `standard` / `fast` plus `low` / `medium` / `high` / `max`. Concrete model ids live in one dated provider map and are resolved against the implementation platform later.

The skill has two deliberately separate paths. `/plan` uses public web search and official provider documentation to refresh all four provider columns; `/implement` re-confirms the generic intent and selected provider cell; direct `/route` remains host-native and enumerates only models the active platform can actually switch to. Public documentation lookup is best-effort and needs no credential. Direct routing introduces no new credential; its one optional network call is Anthropic `GET /v1/models`, made only when `ANTHROPIC_API_KEY` already exists.

> **Planning contract vs. direct switching.** `/plan` records generic tier and effort in each phase and keeps concrete ids in `## Current model map`. The map is refreshed from public Anthropic, OpenAI, Google, and Cursor documentation and may use the visibly dated `last-known-model-map.json` fallback. Direct `/route` validates the selected host model before switching. A plan map never grants cross-provider switching capability.

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

Run the steps in order. First select the operating mode, then score portable intent. Refresh or resolve concrete models only where that mode needs them.

### Step 1: Select the routing mode

Choose exactly one mode:

- **Planning** (`/plan`): score every phase to generic tier + effort and produce a fresh four-provider map before writing the plan.
- **Implementation** (`/implement`): read the phase's generic tier + effort, refresh or revalidate the map, and resolve the user's selected provider cell against that provider's live surface.
- **Direct switching** (`/route`): detect the current host, enumerate its live models, score the target, and recommend or switch only within that host.

Historical plans with `**Recommended model**` or `Rec. model / effort` remain valid inputs. Treat their concrete id as legacy evidence, re-score the phase, and do not copy the old host lock into a new plan.

### Step 2: Score the five complexity signals

Score the task on five signals. Each signal is `low`, `medium`, or `high`. Be honest: under-scoring is the failure mode that breaks the quality guarantee.

| Signal | low | medium | high |
|---|---|---|---|
| **Task scope** | one file, one function | a few related files | cross-cutting, many modules |
| **Structural complexity** | boilerplate, mechanical | standard pattern, some logic | novel algorithm or architecture |
| **Context volume required** | localized, self-contained | a handful of files to read | large, spread across the repo |
| **Risk / blast radius** | throwaway, tests, docs | internal feature code | production, security, data, migration |
| **Reasoning type** | rename, format, lookup | compose known pieces | design, debug, optimize, prove |

### Step 3: Map the score to generic tier and effort

Use the deterministic mapping below. Any `high` signal pins `frontier`; uncertainty never resolves downward.

| Aggregate reading | Generic tier | Effort |
|---|---|---|
| Uncertain, or two or more `high` signals | `frontier` | `max` |
| Exactly one `high` signal | `frontier` | `high` |
| No `high`; three or more `medium` signals | `strong` | `high` |
| No `high`; one or two `medium` signals | `standard` | `medium` |
| All five signals `low` | `fast` | `low` |

For reproducible scoring, use `model-map.py` through the matching platform wrapper:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.sh score low medium medium low low
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.ps1 score low medium medium low low
```

The wrappers call the standard-library `model-map.py` implementation and print JSON. Add `--uncertain` when the evidence is incomplete.

### Step 4: Build or refresh the Current model map

Planning mode MUST attempt public web search on every full `/plan` invocation:

1. Search current official model catalogs, release notes, and platform model-picker documentation for Anthropic, OpenAI, Google, and Cursor.
2. Select one concrete model id for each `frontier`, `strong`, `standard`, and `fast` cell. Record at least one official source URL per provider.
3. Put the candidate in the same JSON shape as `last-known-model-map.json`.
4. Validate it before writing the plan:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.sh validate <candidate.json>
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.sh render <candidate.json> --status fresh --as-of <YYYY-MM-DD>
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.ps1 validate <candidate.json>
~/.nexus-hub/skills/ai-development/model-routing/scripts/model-map.ps1 render <candidate.json> --status fresh --as-of <YYYY-MM-DD>
```

The helper validates the 4x4 schema, non-empty cells, date, and official-source URL shape. It does not fetch the web: the harness performs research, then the helper deterministically validates and renders the result.

If web search or official docs are unavailable, render the bundled snapshot with `model-map.sh fallback` or `model-map.ps1 fallback`. This emits `offline fallback; stale as of <snapshot-date>` from `last-known-model-map.json`. If the snapshot is missing or fails validation, run the `unavailable` command and use `assess at implementation time` in all 16 cells. Never silently reuse an undated map, invent an id, or collapse the table to the current host.

### Two verification rules the map depends on

**Effort levels are not comparable across models.** An effort name such as `high` does not buy the same amount of thinking on two different models, so an effort sweep measured on one model does not transfer: when the mapped model for a tier changes, re-run the sweep on the new model before trusting the old level. The vendor guidance is to start at the documented default effort and test the other levels against local evals, and the mid and low levels belong in that sweep, because a stronger model at lower effort can beat a weaker model at higher effort on both quality and cost.

**A recognized name is not a known name.** When a query centers on a name the agent does not confidently recognize, or recognizes from a fast-moving area such as AI models and developer tools, the name itself is the thing to verify: search before answering and include the name exactly as the user wrote it in at least one query. Partial background is what makes an out-of-date answer sound authoritative, so familiarity is not a reason to skip the search. This skill's own `references/last-known-model-map.json` exists because these names go stale within months, which is the concrete case for the rule.

### Step 5: Resolve the active provider

For implementation or direct switching, detect the active platform before assuming switch mechanics:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.sh
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.sh <platform-id>
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.ps1
~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.ps1 <platform-id>
```

For `/implement`, start with the plan's selected-provider map cell and verify it against the live platform surface. If unavailable, select the nearest model at the same or stronger generic tier and surface the delta. For `/route`, resolve the scored tier directly against the enumerated host set. A picker sentinel is valid evidence that switching is manual; it is not permission to guess a concrete id.

Present the generic tier, effort, concrete model when verified, all five signal readings, map freshness, and best-effort official citations. A plan's phase fields remain generic even when the current implementation recommendation names a concrete model.

### Step 6: Apply the switch per the platform profile

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
| "This phase looks simple, so the cheap model is fine." | "Looks simple" is not a rubric result. One hidden high-risk signal must pin `frontier`; otherwise production or migration work can be under-tiered and reworked. |
| "The host model list is enough for the plan." | A host-only map makes the plan unusable on another provider and recreates the defect this contract fixes. Planning requires all four provider columns. |
| "Yesterday's map is probably still current." | Model catalogs change quickly. `/plan` must attempt official-source refresh every invocation; only an explicitly dated fallback may be reused offline. |
| "Auto-switching works everywhere, so I'll script it on every platform." | The Claude Code main loop cannot switch its own model mid-session, and Cursor / Copilot / OpenCode expose no scriptable switch at all. Scripting a switch on a manual platform either no-ops silently or errors; the posture must branch on `can_script_switch`. |
| "When unsure, I'll pick `strong` as a safe middle ground." | Uncertainty maps to `frontier` + `max`. A middle tier silently weakens the no-degradation guarantee. |

## Verification

- [ ] Every new plan phase contains only an allowed generic tier and effort; no host-only concrete id is authoritative.
- [ ] The recommendation states all five signal readings; any `high` maps to `frontier`, and uncertainty maps to `frontier` + `max`.
- [ ] `model-map.py validate <candidate.json>` passes before a fresh map is written, and all 16 provider cells are non-empty.
- [ ] A fresh map cites official sources for Anthropic, OpenAI, Google, and Cursor; an offline map visibly uses the date from `last-known-model-map.json`.
- [ ] When a tier's mapped model changed, the effort sweep was re-run on the new model rather than carried over, and any unfamiliar or fast-moving model name in the request was searched as written before it was used.
- [ ] `/implement` preserves or upshifts the plan's generic tier when the selected provider model is unavailable.
- [ ] A direct `/route` model appears in the live-enumerated set, or the picker sentinel leaves the recommendation tier-named and manual.
- [ ] The switch instruction matches the detected platform's `switch_mechanism` (scriptable execute / Claude Code keystroke / picker instruction) and never scripts a switch on a manual-only platform.
- [ ] A mid-task escalation (Step 7) only ever upshifts the tier or effort; the router never auto-downshifts a model mid-phase while a task is failing.
- [ ] No new credential or dependency was introduced; public plan research uses existing web access, and optional Anthropic enumeration runs only with an existing key.

## Related Skills

- [[multi-provider-ai]] -- choosing the API provider (Anthropic / Bedrock / Vertex / OpenRouter); this skill reuses its tier abstraction but enumerates dynamically instead of from a hardcoded matrix.
- [[prompt-engineering]] -- operationalizes its task-complexity routing table and effort-level strategy; this skill is the platform-aware, live-enumerated extension of that section.
- [[ai-billing-safeguards]] -- hard spend caps the router respects; routing recommends a tier, billing-safeguards block at a budget.
- [[agent-orchestration-primitives]] -- decides whether to fan out at all; routing then picks the tier each agent runs on.
- [[implementation-plan]] -- scores plan phases to generic tier/effort and owns the dated four-provider Current model map.
- `/usage` (the `check-usage` skill) -- the consumption-time counterpart that reports usage against limits; this skill is the planning/task-time counterpart and does not duplicate it.

---

**Version**: 1.2.0
**Last Updated**: August 2026
