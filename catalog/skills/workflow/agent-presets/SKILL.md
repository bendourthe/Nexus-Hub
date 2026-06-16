---
name: agent-presets
description: Invoke a ready-made agent preset (morning-briefing, research, coding-assistant) that wires existing skills and slash commands into a one-shot working bundle. Use to orient at session start, kick off research, or enter a plan-test-commit coding loop.
summary_l0: "Ready-made agent presets that compose existing skills and slash commands into one-invocation bundles"
overview_l1: "This skill defines a small set of agent presets -- morning-briefing, research, and coding-assistant -- each a named bundle that composes existing catalog skills and slash commands into a single invocation. Instead of remembering which skills and commands to chain for a recurring activity, the user names the preset and the agent activates the bundle in order: morning-briefing orients on what changed and what is next; research enters an evidence-gathering posture that ends in a cited report; coding-assistant runs a plan, implement, test, verify, commit loop. Presets are templates over capabilities that already exist -- they introduce no new tools and make no outbound calls. The agent announces the active preset, lists what it activates, and runs the bundle's steps. Trigger phrases: morning briefing, start my day, research preset, coding assistant, enter coding mode, run the research bundle, agent preset, daily standup."
---

# Agent Presets

A preset is a named bundle that wires existing skills and slash commands into a one-invocation workflow for a recurring activity. Rather than re-deriving "for research I should switch posture, gather multiple sources, then gate before coding" every time, the user names the preset (`research`) and the agent runs the whole bundle.

Presets are templates over capabilities that already exist. They add no new tools and make no outbound calls; they only orchestrate what is already installed.

## When to Use This Skill

Use when:

- The user names a preset: "run the morning briefing", "research preset", "coding assistant".
- The user starts a recurring activity that maps to a bundle: opening the day, beginning a multi-source investigation, or settling into an implementation loop.
- A workflow or runbook references a preset by name.

**When NOT to use:**

- A one-off task that does not match a bundle -- invoke the single relevant skill or command directly.
- Defining a brand-new reusable command -- use [[create-custom-command]] to author it, then (optionally) add it as a preset here.
- Switching only the agent's posture without the surrounding workflow -- use [[context-modes]] directly.

## The Three Presets

| Preset | Purpose | Composes |
|---|---|---|
| `morning-briefing` | Orient at the start of a session: what changed, where you left off, what is next. | `/session` resume, [[dev-progress-tracker]], [[session-query]], `git log` review |
| `research` | Gather multi-source evidence and end with a cited report, gated before any code. | [[context-modes]] (research), [[deep-research-compilation]] / [[trend-research]] / [[local-docs-lookup]], [[research-plan-implement]] |
| `coding-assistant` | Run a disciplined plan -> implement -> test -> verify -> commit loop. | [[context-modes]] (dev), [[plan-before-code]], [[incremental-implementation]], [[test-driven-development]], [[verification-before-completion]], [[code-commit-workflow]] |

## Instructions

When a preset is invoked, announce it in one line, list what it activates, then run the bundle's steps in order.

```
Activating preset: research. Composes context-modes (research), deep-research-compilation, research-plan-implement.
```

### Preset: morning-briefing

A start-of-session orientation. Run in order:

1. **Resume context** -- pull the last session's state (`/session` resume, or [[session-history]] if a written record exists).
2. **Review progress** -- read the project tracker via [[dev-progress-tracker]] (`docs/todos.md`): what is done, what is in flight.
3. **Scan recent activity** -- use [[session-query]] over local session logs and a `git log` of recent commits to see what changed since last time.
4. **Brief** -- produce a short summary: what changed, where work was left off, and the top 3 prioritized next actions. No code is written in this preset.

### Preset: research

An evidence-gathering posture that produces a decision, not an implementation. Run in order:

1. **Enter research posture** -- [[context-modes]] `research` (gather evidence, compare options, do not edit source or commit).
2. **Gather** -- choose the retrieval skill that fits: [[deep-research-compilation]] for a multi-source cited document, [[trend-research]] for recent ecosystem signal, [[local-docs-lookup]] for library / API questions from local docs.
3. **Gate** -- run the [[research-plan-implement]] GO / NO-GO gate so research concludes with an explicit decision before any code is proposed.
4. **Output** -- a written report with the alternatives compared and sources cited. Hand off to `coding-assistant` only after the gate passes.

### Preset: coding-assistant

An implementation loop. Run in order:

1. **Enter dev posture** -- [[context-modes]] `dev` (write code, run tests, keep commits atomic).
2. **Plan** -- [[plan-before-code]] to frame the change and surface approach trade-offs.
3. **Implement incrementally** -- [[incremental-implementation]] one tested step at a time; pair with [[test-driven-development]] (red -> green -> refactor) where a test can be written first.
4. **Verify** -- [[verification-before-completion]]: require fresh passing evidence (build / lint / test) before claiming done.
5. **Commit** -- [[code-commit-workflow]] for an atomic conventional commit once the step is green.

## Customizing a preset

Presets are starting templates, not fixed scripts. To adapt one:

- **Swap a step** -- substitute a skill of the same role (e.g. use [[plan-before-code]] instead of [[research-plan-implement]] when no research gate is needed).
- **Add a step** -- drop in another catalog skill where it fits the flow.
- **Add a preset** -- author a new bundle as another section here, or formalize a frequently-used one as a slash command via [[create-custom-command]].

A custom preset must still compose only existing capabilities and introduce no new outbound surface.

### Composition strategies

When one preset layers on top of a lower-priority base (a project preset over a catalog default, or a per-task tweak over a named preset), four strategies say how the override combines with what it sits on. They are a vocabulary for layering without forking the base bundle (the copy that drifts out of sync):

- **`replace`** (default) -- the higher-priority content fully replaces the lower-priority content. Example: a project's own `plan` step replaces the catalog `plan-before-code` step entirely.
- **`prepend`** -- place the override before the base, blank-line separated. Example: a `load project conventions` step runs ahead of the inherited `coding-assistant` bundle.
- **`append`** -- place the override after the base. Example: a `post to the team channel` step runs after the inherited bundle's commit step.
- **`wrap`** -- the override embeds a `{CORE_TEMPLATE}` placeholder that is replaced with the lower-priority content, so the base runs inside the override's framing:

    ```
    enter project posture
    {CORE_TEMPLATE}        # the inherited plan -> implement -> test -> verify -> commit bundle
    run project smoke check
    ```

Prefer `replace` unless you specifically need to keep the base; `prepend` / `append` / `wrap` let a project layer its own steps onto a catalog preset without copying the whole bundle.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A preset is just a macro, I can skip the steps I find boring" | The order is the value: research before coding prevents premature implementation; verify before commit prevents shipping red. Skipping the gate defeats the preset. |
| "I will invoke the skills ad hoc instead of naming the preset" | Ad hoc invocation is exactly what presets remove. Naming the bundle guarantees the full sequence runs and the user knows what posture the agent is in. |
| "Presets need new tooling to be useful" | A preset is a composition of existing skills and commands. If it needs a new tool, that is a separate capability gap, not a preset -- presets stay zero-new-surface by design. |
| "I do not need to announce which preset is active" | Announcing the preset (and what it composes) tells the user what the agent will do next and lets them redirect before the bundle runs. |

## Verification

- [ ] Invoking a preset emits a one-line announcement naming the preset and listing the skills / commands it activates.
- [ ] The preset composes only existing catalog skills and slash commands -- no new tool and no outbound call is introduced.
- [ ] `morning-briefing` produces a since-last-session summary plus prioritized next actions and writes no code.
- [ ] `research` enters research posture and ends with a cited report gated by a GO / NO-GO before any implementation.
- [ ] `coding-assistant` runs plan -> implement -> test -> verify -> commit in that order, with verification before any done claim.

## Related Skills

- [[context-modes]] -- the posture primitive every preset enters first (research / dev); presets add the surrounding workflow.
- [[research-plan-implement]] -- the gated workflow the `research` preset wraps; presets are the one-invocation front door to it.
- [[create-custom-command]] -- formalize a frequently-used preset into a dedicated slash command.
- [[dev-progress-tracker]] -- the tracker `morning-briefing` reads to report progress and next actions.
- [[test-driven-development]] -- the red-green-refactor inner loop of the `coding-assistant` preset.
