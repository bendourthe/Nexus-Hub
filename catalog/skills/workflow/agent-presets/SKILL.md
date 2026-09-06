---
name: agent-presets
description: "Run agent presets: morning-briefing, research, coding-assistant, or security-audit. Full local security audit, scan-fix-rescan, dependency plus IaC audit, or pre-release security verification. SKIP: CVE, cloud-posture, patch-only, or ordinary review."
summary_l0: "Ready-made agent presets that compose existing skills into one-invocation bundles"
overview_l1: "This skill defines agent presets -- morning-briefing, research, coding-assistant, and security-audit -- each a named bundle over existing catalog skills. Morning-briefing orients on what changed; research gathers cited evidence before code; coding-assistant runs plan, implement, test, verify, commit; security-audit runs local detection, triage, optional user-approved remediation, same-detector re-scan, and independent read-only verification. Presets introduce no tool, MCP, service, credential, or automatic installation. Announce the active preset and, for security-audit, the scanner coverage state. Trigger phrases: morning briefing, research preset, coding assistant, security audit, scan-fix-rescan, full local security audit, pre-release security verification. SKIP: a single CVE reachability question, a single cloud posture question, writing a security patch only, or ordinary code review."
---

# Agent Presets

A preset is a named bundle that wires existing skills and slash commands into a one-invocation workflow for a recurring activity. Rather than re-deriving "for research I should switch posture, gather multiple sources, then gate before coding" every time, the user names the preset (`research`) and the agent runs the whole bundle.

Presets are templates over capabilities that already exist. They add no new tools and make no outbound calls; they only orchestrate what is already installed.

## When to Use This Skill

Use when:

- The user names a preset: "run the morning briefing", "research preset", "coding assistant", "security audit", "scan-fix-rescan".
- The user starts a recurring activity that maps to a bundle: opening the day, beginning a multi-source investigation, settling into an implementation loop, or running a full local security audit.
- A workflow or runbook references a preset by name.

**When NOT to use:**

- A one-off task that does not match a bundle -- invoke the single relevant skill or command directly. A single CVE reachability question, a single cloud posture question, writing a security patch only, or ordinary code review must not activate `security-audit`.
- Defining a brand-new reusable command -- use [[create-custom-command]] to author it, then (optionally) add it as a preset here.
- Switching only the agent's posture without the surrounding workflow -- use [[context-modes]] directly.

## The Four Presets

| Preset | Purpose | Composes |
|---|---|---|
| `morning-briefing` | Orient at the start of a session: what changed, where you left off, what is next. | `/session` resume, [[dev-progress-tracker]], [[session-query]], `git log` review |
| `research` | Gather multi-source evidence and end with a cited report, gated before any code. | [[context-modes]] (research), [[deep-research-compilation]] / [[trend-research]] / [[local-docs-lookup]], [[research-plan-implement]] |
| `coding-assistant` | Run a disciplined plan -> implement -> test -> verify -> commit loop. | [[context-modes]] (dev), [[plan-before-code]], [[incremental-implementation]], [[test-driven-development]], [[verification-before-completion]], [[code-commit-workflow]] |
| `security-audit` | Run a local detection-to-verification security audit with scanner receipts. | [[security-review]], [[dependency-security-audit]], [[cve-reachability-analyzer]], [[cloud-security-posture-detection]], [[security-patch-advisor]], [[testing-review]], [[adversarial-verifier]] |

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

### Preset: security-audit

A local security-audit procedure over existing skills. Announce the preset, the skills it activates, and the current scanner coverage state (`complete` or `degraded`). Introduce no tool, MCP, service, credential, or automatic installation.

Run in order:

1. **Scope** -- [[security-review]] Step 0 component denominator and schema-v2 choice. Authentication and licensing stay with [[authentication-patterns]] and [[licensing-compliance]]; do not duplicate those procedures.
2. **Detect** -- application and secrets via [[security-review]] local-scanner recipes; dependencies via [[dependency-security-audit]] applicability; IaC via [[cloud-security-posture-detection]] when supported files exist. Record every scanner receipt as `RAN`, `NOT_APPLICABLE`, `UNAVAILABLE`, `FAILED`, or `DECLINED`.
3. **Triage** -- [[cve-reachability-analyzer]] on surviving dependency findings, preserving original severity. A no-fix audit may stop after triage and still close with scanner coverage reported.
4. **Remediate** -- only after detection and only with user approval, through [[security-patch-advisor]]. The fixer context is not the verifier.
5. **Test** -- [[testing-review]] on the patched scope.
6. **Re-scan** -- same detector, config fingerprint, and target scope as the before receipt.
7. **Independent verify** -- a read-only reviewer (`security-reviewer` plus [[adversarial-verifier]]) consumes before/after receipts and the patch diff. It does not apply patches or approve its own prior fixes.
8. **Close** -- [[security-review]] schema-v2 closure gate, then the report. Do not claim complete scanner coverage while any applicable receipt is not `RAN`.

Trigger evals for this preset live in `evals/trigger-cases.json`.

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

### Bundle-manifest semantics

A preset or bundle definition is a manifest, and three authoring disciplines keep that manifest honest across installs (generic to any bundle system):

- **Per-component version pinning** -- a bundle pins each component's version. Install-time idempotency that skips an already-present component does NOT re-pin it, so an explicit update pass is what re-applies pins; a skip is not an upgrade.
- **Provenance-tracked removal** -- a bundle uninstall removes only the components that bundle contributed, never a component another installed bundle still needs (the no-collateral-removal rule). Track which bundle contributed each component so removal stays scoped.
- **Update-vs-install semantics** -- an update refreshes owned components to their newly pinned versions while preserving user-level overrides; it is distinct from a fresh install, which seeds from scratch.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A preset is just a macro, I can skip the steps I find boring" | The order is the value: research before coding prevents premature implementation; verify before commit prevents shipping red. Skipping the gate defeats the preset. |
| "I will invoke the skills ad hoc instead of naming the preset" | Ad hoc invocation is exactly what presets remove. Naming the bundle guarantees the full sequence runs and the user knows what posture the agent is in. |
| "Presets need new tooling to be useful" | A preset is a composition of existing skills and commands. If it needs a new tool, that is a separate capability gap, not a preset -- presets stay zero-new-surface by design. |
| "I do not need to announce which preset is active" | Announcing the preset (and what it composes) tells the user what the agent will do next and lets them redirect before the bundle runs. |
| "I already reviewed the components, so I can skip scanner receipts" | `security-audit` exists to make scanner coverage and independent verification mandatory. Skipping them is a silent omission. |

## Verification

- [ ] Invoking a preset emits a one-line announcement naming the preset and listing the skills / commands it activates.
- [ ] The preset composes only existing catalog skills and slash commands -- no new tool and no outbound call is introduced.
- [ ] `morning-briefing` produces a since-last-session summary plus prioritized next actions and writes no code.
- [ ] `research` enters research posture and ends with a cited report gated by a GO / NO-GO before any implementation.
- [ ] `coding-assistant` runs plan -> implement -> test -> verify -> commit in that order, with verification before any done claim.
- [ ] `security-audit` announces active skills and scanner coverage, runs detection before remediation, re-scans before closure, and keeps the independent verifier read-only.
- [ ] `evals/trigger-cases.json` covers full security audit, scan-fix-rescan, dependency plus IaC audit, and pre-release verification as positives, and one-CVE, one-cloud-posture, patch-only, and ordinary code-review prompts as negatives.

## Related Skills

- [[context-modes]] -- the posture primitive every preset enters first (research / dev); presets add the surrounding workflow.
- [[research-plan-implement]] -- the gated workflow the `research` preset wraps; presets are the one-invocation front door to it.
- [[create-custom-command]] -- formalize a frequently-used preset into a dedicated slash command.
- [[dev-progress-tracker]] -- the tracker `morning-briefing` reads to report progress and next actions.
- [[test-driven-development]] -- the red-green-refactor inner loop of the `coding-assistant` preset.
- [[security-review]] -- detection, receipts, and closure gate for the `security-audit` preset. User-facing procedure: `guides/reference/SECURITY_AUDIT.md`.
