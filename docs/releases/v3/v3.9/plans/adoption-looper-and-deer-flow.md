# Plan -- Loop-Design + Cross-Model Egress Hygiene (Looper + DeerFlow 2.0 adoption)

**Project**: Nexus-Hub
**Version**: v3.9.0
**Slug**: adoption-looper-and-deer-flow
**Plan Type**: Feature / Enhancement (skill-native catalog enrichment; no new skill, command, hook, outbound call, dependency, or credential)
**Created**: 2026-06-24
**Goal**: Enrich `cross-model-orchestrator`, `loop-engineering`, `agent-access-policy`, and one memory skill with the design-time and cross-model-egress loop doctrine that a design coach (Looper) and a SuperAgent runtime (DeerFlow 2.0) revealed, leading with a security-relevant gap (egress redaction plus first-send consent before a cross-model handoff), with zero new skill, command, outbound call, dependency, or credential.

## Overview

This plan operationalizes the prioritized adoption plans in [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-looper.md](../comparison-looper.md) (the substance) and [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-deer-flow.md](../comparison-deer-flow.md) (two optional P3 doctrine notes). The Looper comparison is the fifth in the loop domain; the v3.8.0 ralph adoption already absorbed the runtime loop doctrine (exit-signal protocol, three-class stall and fault detection, untrusted-task-source fence, task-readiness gate, per-iteration recovery points). Looper is a design coach rather than a runtime, so its genuinely-new contribution is the doctrine that happens before the first iteration and at the cross-model boundary. DeerFlow 2.0 is overwhelmingly a convergent-design validation of Nexus-Hub's authoring model; it yields only two low-priority skill-native doctrine notes.

Every recommended item is `skill-native` (the comparison's Step 5.4 ordering placed all of them in the skill-native bucket, with no re-full, re-partial, or vendor-intrinsic items). With `reverse-engineer-first=true`, the skill-native bucket comes first, and within it the items are sequenced by P-tier: the two P1 items (L1 egress redaction plus consent, L2 design-first rubric interview), then the two P2 items (L3 reviewer-versus-judge verdict-honesty rule, L4 typed-verification ordering plus design-render confirm gate), then the three P3 items (L5 argv-array invocation discipline, D1 default-deny host-execution posture, D2 typed memory schema). The three Looper declines (the `run-loop.py` runner and the resolved-JSON compile step, both pre-adjudicated `drop-outright` by the v3.8.0 standalone-loop-runtime matrix row; and the advisory cost caps, weaker than `ai-billing-safeguards` hard caps) are recorded as declines, not built.

Delivery is local Markdown enrichment of four existing skills: `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`, `catalog/skills/workflow/loop-engineering/SKILL.md` (and optionally a new `references/loop-design-rubric.md` under it), `catalog/skills/orchestration/agent-access-policy/SKILL.md`, and one memory skill (`catalog/skills/workflow/context-pack-builder/SKILL.md` or `continuous-learning`). Phasing is by target-skill cohesion so a file is opened in one phase only, ordered so the highest-value file (the cross-model handoff path carrying the P1 security gap) comes first.

Success looks like: a handoff-egress-hygiene discipline (redaction-glob defaults, a first-send consent gate, a record of what was sent) and the reviewer-versus-judge verdict-honesty rule present in `cross-model-orchestrator`; a design-first loop section and the typed-verification ordering plus design-render confirm gate present in `loop-engineering`; the argv-array invocation discipline noted in both; the default-deny host-execution posture in `agent-access-policy`; an optional typed-fact schema note in a memory skill; every cross-link resolving; every edited SKILL.md body still under the 500-line norm (overflow pushed to a `references/` file that is itself linked); all content ASCII-only and conformant to the Markdown style guide; generic naming with no upstream attribution in any distributed artifact (no "Looper", "ksimback", "DeerFlow", "ByteDance", and no literal tokens such as `loop.yaml`, `loop.resolved.json`, `run-loop.py`, `ensure_consent`, `RUN_IN_SESSION`); the registry-edit decision made and validated; the declines and the convergent-validation finding recorded in `docs/policy/mcp-reverse-engineering-matrix.md`; and the full validator chain green.

## Constitution Check

*GATE: Must pass before Phase 1. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.9/constitution.md` - skipping the formal check. Recommend running `/constitution` to establish project principles; this is informational, not blocking. The plan is nonetheless aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy and the Reverse-Engineering Attribution Rule): every recommended item is `skill-native` over an owned skill, introduces no outbound call, dependency, or credential, and uses generic artifact naming with no upstream attribution in the distributed content. The highest-value item (L1) strengthens the egress posture the policy exists to enforce. The three declines are dropped because they would reverse a documented decision (the v3.1.0 host-driver decision, the v3.8.0 standalone-loop-runtime decline) or regress a posture (`ai-billing-safeguards` hard caps), and they are recorded as declines rather than smuggled into the plan.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Cross-model handoff hygiene | `cross-model-orchestrator` gains a handoff-egress-hygiene section (redaction defaults plus a first-send consent gate plus a record-of-sends) (L1, P1, security), the reviewer-versus-judge verdict-honesty rule in its quality-gate step (L3, P2), and the argv-array invocation discipline (L5 cross-model half, P3) | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 2 | Design-first loop doctrine | `loop-engineering` gains a "Design the Loop Before You Run It" section with a staged rubric composing the existing task-readiness gate (L2, P1), the typed-verification ordering plus a render-and-confirm-before-first-run note (L4, P2), the argv-array note in the `check_command` guidance (L5 loop half, P3), and a cross-link to the Phase 1 egress hygiene from the council-seat material | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 3 | Low-priority doctrine notes + consolidation | `agent-access-policy` gains the default-deny host-execution posture and log-before-execute note (D1, P3); a memory skill gains an optional typed-fact schema note (D2, P3); the declines and the convergent-validation finding are recorded in the RE matrix; the registry-edit decision is made; CHANGELOG and known-gaps updated | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |

The "Rec. model / effort" column is a best-effort planning-time assessment, recorded as platform-agnostic tier intent plus the concretely-enumerated Claude Code model. Live model enumeration was not available at plan time, so the concrete name follows the v3.8.0 precedent (Opus 4.8); `/implement` re-confirms each phase's recommendation against the then-current live model set before building.

## Phase 1: Cross-model handoff hygiene

**Goal**: Add to `cross-model-orchestrator` the egress discipline it currently lacks entirely: redaction-glob defaults and a first-send consent gate before any project artifact crosses to a second model (L1, the P1 security headline), the reviewer-versus-judge verdict-honesty rule in its quality-gate step (L3), and the argv-array invocation discipline for model invocations (L5, cross-model half).
**Prerequisites**: None.
**Stability Gate**: `cross-model-orchestrator/SKILL.md` contains a handoff-egress-hygiene section (default redaction globs, a first-send consent gate, a record of what was sent), the reviewer-versus-judge distinction and verdict-honesty rule in its quality-gate step, and an argv-array invocation note; all cross-links resolve; the body remains under 500 lines; validators green.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this phase authors a new security discipline (egress redaction plus consent) on an existing skill that currently has no egress posture, and it must integrate with the standing MCP Registry Policy and not contradict the skill's file-based-handoff model. Doctrine drift and a weak or misleading egress guarantee are the high-risk failure modes. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 1.1 -- Add the handoff-egress-hygiene section (L1)

**Objective**: Add a section teaching that any artifact crossing to a second model is an egress event requiring redaction defaults and first-send consent.

**Prompt**:
> In `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`, add a new section titled "## Handoff Egress Hygiene" immediately after "### Step 3: Configure Communication Between Models" (the artifacts in Step 3 are what cross to another model, so the hygiene rule belongs there) and before "### Step 4: Quality Gates Between Models". Teach this discipline (aim for 16-24 lines): (1) every artifact handed to a second model (the plan, the review, the progress log, any cited file) is an EGRESS event when that model runs behind an external CLI or API, so treat the handoff as a content-egress boundary governed by the MCP Registry Policy; (2) apply default redaction before the first send: substitute the contents of files matching a default deny-glob set (`.env`, `.env.*`, `secrets/**`, `**/*.key`, and any project-specific secret paths) with a visible redaction marker such as `[redacted:<relative-path>]`, rather than sending raw contents; (3) require explicit first-send consent: before the first time a given destination model receives project content, state in one place WHAT will be sent (the artifact list), WHICH model/CLI receives it, and WHICH redaction globs apply, and require an explicit confirmation; record that the consent was given (destination, the sends list, the redaction list) so subsequent sends in the same session do not re-prompt; (4) note that a fully-local reviewer (a local model served on the operator's own machine) keeps the handoff in-house and needs no egress consent. Cross-link the MCP Registry Policy in `AGENTS.md` and `[[agent-access-policy]]`. Apply the Reverse-Engineering Attribution Rule: describe the discipline generically; do NOT name "Looper" or use literal tokens such as `privacy.egress`, `ensure_consent`, or `redact_prompt_for_member`. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md` (blank line before and after the heading and any list); do NOT modify the YAML frontmatter in this sub-task; keep the body under the 500-line norm. Acceptance: the section exists, frames the handoff as an egress boundary, gives the default redaction globs and the marker convention, defines the first-send consent content and the record-of-consent, notes the local-reviewer carve-out, cites the MCP Registry Policy by name, and both cross-links resolve.

---

#### 1.2 -- Add the reviewer-versus-judge verdict-honesty rule (L3)

**Objective**: Add to the quality-gate step the distinction between a notes-only reviewer and a verdict-returning judge, and the rule that only a judge or a human may be the deciding source for a revise-until-clean gate.

**Prompt**:
> In `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`, in "### Step 4: Quality Gates Between Models", add a short subsection (6-10 lines) titled "Reviewer vs. judge" (or fold it into the Gate Actions area). Teach: a REVIEWER produces non-binding notes (observations, adversarial critique, tone), while a JUDGE returns a structured, parseable verdict (a pass-or-revise decision with blocking issues and a confidence value); only a judge or a human may be the deciding source for a gate whose policy is "revise until clean", because a notes-only reviewer cannot honestly certify "clean" -- treating reviewer notes as a blocking clean verdict is fake precision. Tie this to the existing rule in the Common Rationalizations table (a model reviewing its own work re-confirms its own assumptions): the reviewer-versus-judge split is the same anti-self-deception discipline applied to the gate's deciding source. Prefer a judge (or human) for any gate that blocks progress; a reviewer is for brainstorming and adversarial notes where a deterministic pass/fail would be false precision. Cross-link `[[quality-gate-definitions]]` and `[[adversarial-verifier]]`. Apply the Reverse-Engineering Attribution Rule (generic description; no upstream names or literal field tokens). Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; body under 500 lines. Acceptance: the reviewer-versus-judge distinction and the verdict-honesty rule are present in Step 4, tied to the existing self-review rationalization, and both cross-links resolve.

---

#### 1.3 -- Add the argv-array invocation discipline (L5, cross-model half)

**Objective**: Add a one-line-to-three-line security-hygiene note that model and check invocations should be expressed as argument arrays with explicit timeouts, never as interpolated shell strings.

**Prompt**:
> In `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`, in the "## Best Practices" section, add one bullet: when a workflow invokes another model or a check via a CLI, express the invocation as an argument array (program plus discrete arguments) with an explicit per-call timeout, never as an interpolated shell string; this is injection-resistant by construction and matches the project's Bash security rules (use arrays, never interpolate input into a command string). Keep it to one bullet (2-3 lines). Apply the Reverse-Engineering Attribution Rule. Constraints: ASCII-only; Markdown style guide; no frontmatter change. Acceptance: the Best Practices bullet is present and states the argv-array-with-timeout discipline and the injection-resistance rationale.

---

#### 1.4 -- Testing and Stabilization

**Objective**: Validate the Phase 1 edits and iterate until stable before advancing.

**Prompt**:
> Validate the Phase 1 edits to `catalog/skills/orchestration/cross-model-orchestrator/SKILL.md`. Run `make validate` if `make` is on PATH; otherwise run the documented Windows fallback directly: `python scripts/validate_skills.py --verbose` (JSON catalog integrity plus the orphan-bundle audit) and the catalog dangling-wikilink audit. Confirm: (1) validators exit 0; (2) no new orphan bundles; (3) no dangling wikilinks (the MCP Registry Policy reference and `[[agent-access-policy]]`, `[[quality-gate-definitions]]`, `[[adversarial-verifier]]` all resolve); (4) every added line is ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters); (5) the SKILL.md body is under 500 lines (if it would exceed, move the longest new subsection into a `references/` file linked from SKILL.md and re-run the orphan-bundle audit); (6) grep the diff for "Looper", "ksimback", "DeerFlow", "privacy.egress", "ensure_consent", "redact_prompt_for_member" and expect zero matches in the distributed artifact (Reverse-Engineering Attribution Rule). Fix any failure and re-run until all checks pass. Then run `/session history` to document Phase 1.

---

## Phase 2: Design-first loop doctrine

**Goal**: Add to `loop-engineering` the pre-flight design doctrine Looper surfaces: a staged design pass that tightens the goal and types the verification before the first iteration (L2, the P1 design gap), the programmatic-then-judge-then-human verification ordering plus a render-and-confirm-before-first-run note (L4), the argv-array note in the `check_command` guidance (L5, loop half), and a cross-link from the council-seat material to the Phase 1 egress hygiene.
**Prerequisites**: Phase 1 complete (the egress-hygiene section that the council-seat cross-link points to must exist first).
**Stability Gate**: `loop-engineering/SKILL.md` contains a design-first section composing `[[ambiguity-detector]]` and `[[requirement-enhancer]]` without duplicating them, the typed-verification ordering, a render-and-confirm note, an argv-array note in the `check_command` guidance, and a cross-link to the Phase 1 egress hygiene; if a `references/loop-design-rubric.md` is created it is linked from SKILL.md; the body remains under 500 lines; validators green.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this phase authors a new doctrine section that must compose existing skills (the task-readiness gate, `ambiguity-detector`, `requirement-enhancer`) without duplicating them, and must stay internally consistent with the Strict Control Loops, Exit-Signal Protocol, and Stall and Fault Detection sections added in prior versions; design drift and accidental duplication of the task-readiness gate are the failure modes. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 2.1 -- Add the "Design the Loop Before You Run It" section (L2)

**Objective**: Add a pre-flight design section that walks the operator through tightening the goal and structuring verification before the loop runs, composing (not duplicating) the existing task-readiness gate.

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/SKILL.md`, add a new section titled "## Design the Loop Before You Run It" placed before "## Instructions" (it is a pre-flight pass that precedes assembly). Teach a short, staged design discipline (aim for 18-28 lines, or move the detailed rubric to a reference file per the size rule below): before assembling or running a loop, walk these design stages and critique each against a rubric: (1) GOAL shape -- the goal must name a concrete outcome and the artifact or state that proves the loop finished, set scope boundaries (included, excluded, maximum depth), name the context sources the loop must read instead of assume, and name who consumes the result; reject goals like "improve the project" with no target artifact or "make it good" with no criteria; a useful critique prompt is "what would count as done if two competent agents disagreed?". (2) VERIFICATION typing -- every check is one of programmatic (a command with an expected exit or output), judge (a rubric a second model or human evaluates), or human (a manual signoff); require at least one non-vibe check. (3) CONTROL guards -- confirm the loop has its termination guards (the mandatory `iteration_cap` and command-derived `exit_condition`, plus `progress_check` and `handoff` for production loops). State that this design pass COMPOSES the existing task-readiness gate: if the goal is underspecified, route it to `/plan` or `/idea-refine` first, and use `[[ambiguity-detector]]` and `[[requirement-enhancer]]` to score and improve it -- do NOT duplicate their logic here. If the detailed goal/verification/control rubric would push the SKILL.md body over the 500-line norm, create `catalog/skills/workflow/loop-engineering/references/loop-design-rubric.md` holding the per-stage criteria, critique prompts, and anti-patterns, and link to it from this section (the orphan-bundle audit requires the link). Apply the Reverse-Engineering Attribution Rule: describe the design pass generically; do NOT name "Looper" or use literal tokens such as `loop.yaml`, the seven-stage labels verbatim, or `definition_of_done`. Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task. Acceptance: the section exists, teaches the goal/verification/control design stages, explicitly composes the task-readiness gate and the two named skills without duplicating them, ties underspecified-goal-looping back to the existing loopmaxxing guardrail, and any new reference file is linked from SKILL.md.

---

#### 2.2 -- Add the typed-verification ordering and the render-and-confirm note (L4)

**Objective**: State the programmatic-then-judge-then-human verification preference and a render-the-design-for-confirmation-before-the-first-run step.

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/SKILL.md`, add two short pieces. (A) Verification ordering: in the new "## Design the Loop Before You Run It" section (or in the assembly step that picks the `check_command`), state the preference order for the verification types from sub-task 2.1: prefer a programmatic check first (cheapest and unambiguous), then a judge rubric where a programmatic check is not possible, then a human signoff only where neither fits; a loop whose only check is a judge or human signoff should say why a programmatic check was not available. (B) Render-and-confirm: add a 3-5 line note that before the first run of a non-trivial or unattended loop, the operator should render the loop's design (its goal, its gates, its termination caps, and which model sits in each seat) and confirm it, so a bad design is caught before any file is changed; a simple textual or ASCII rendering of goal -> gates -> caps is enough. Tie the render-and-confirm to the existing scope-first calibration discipline (calibrate one iteration, inspect, cap, then widen). Apply the Reverse-Engineering Attribution Rule (generic; no "ASCII flow preview" as a product feature name, no upstream names). Constraints: ASCII-only; Markdown style guide; body under 500 lines. Acceptance: the verification-type ordering is stated; the render-and-confirm-before-first-run note is present and tied to scope-first calibration.

---

#### 2.3 -- Add the argv-array note to `check_command` guidance and the egress cross-link (L5 + L1 link)

**Objective**: Note the argv-array invocation discipline where the loop's `check_command` is described, and cross-link the council-seat material to the Phase 1 egress hygiene.

**Prompt**:
> Two small edits to `catalog/skills/workflow/loop-engineering/SKILL.md`. (A) Argv-array note (L5, loop half): where the `check_command` and any model invocation are discussed (Step 4 assembly, or the Strict Control Loops section), add one sentence that a loop's check and any model invocation should be expressed as an argument array with an explicit timeout, never an interpolated shell string, consistent with the project Bash security rules. (B) Egress cross-link (L1): where the loop assigns maker and checker or council seats (Step 4, item 7, and the Scheduled-Triage Recipe's maker-checker step), add a one-line pointer that when a checker or council seat is a different model behind an external CLI, the handoff is an egress event governed by the handoff-egress-hygiene discipline in `[[cross-model-orchestrator]]` (redaction defaults plus first-send consent). Keep both edits minimal. Apply the Reverse-Engineering Attribution Rule. Constraints: ASCII-only; Markdown style guide; `[[cross-model-orchestrator]]` must resolve. Acceptance: the argv-array sentence is present; the council-seat material cross-links the cross-model egress hygiene; the wikilink resolves.

---

#### 2.4 -- Testing and Stabilization

**Objective**: Validate the Phase 2 edits and iterate until stable before advancing.

**Prompt**:
> Validate the Phase 2 edits to `catalog/skills/workflow/loop-engineering/SKILL.md` and any new `references/loop-design-rubric.md`. Run `make validate` (or the fallback: `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) orphan-bundle audit clean (if `references/loop-design-rubric.md` was created, it is linked from SKILL.md; both existing reference files remain linked); (3) no dangling wikilinks (`[[ambiguity-detector]]`, `[[requirement-enhancer]]`, `[[cross-model-orchestrator]]` resolve); (4) all added lines ASCII-only; (5) the SKILL.md body is under 500 lines (if not, move the design rubric into the reference file and re-validate); (6) grep the diff for "Looper", "ksimback", "loop.yaml", "definition_of_done", "ASCII flow preview" and expect zero matches in the distributed artifact. Confirm the new design section does not contradict the existing Strict Control Loops, Exit-Signal Protocol, Stall and Fault Detection, or task-readiness-gate material. Fix any failure and re-run until green. Then run `/session history` to document Phase 2.

---

## Phase 3: Low-priority doctrine notes and consolidation

**Goal**: Fold in the two DeerFlow P3 doctrine notes (D1 default-deny host-execution posture in `agent-access-policy`; D2 optional typed-fact memory schema in a memory skill), record the declines and the convergent-validation finding in the RE matrix, make the registry-edit decision, and update CHANGELOG and known-gaps.
**Prerequisites**: Phases 1 and 2 complete (the registry-edit decision depends on the final state of both enriched skills).
**Stability Gate**: `agent-access-policy/SKILL.md` carries the default-deny host-execution posture and the log-before-execute note; one memory skill carries an optional typed-fact schema note; the RE matrix records the Looper and DeerFlow declines and the convergent-validation finding; the registry-edit decision is made and validated; CHANGELOG `## [Unreleased]` and known-gaps updated; validators green.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: structured, low-complexity edits to existing skills plus bookkeeping (matrix rows, registry decision, changelog), lower risk than Phases 1 and 2; the strong tier per the no-degradation default, medium effort because the work is articulation and recording rather than new doctrine design. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 3.1 -- Add the default-deny host-execution posture (D1)

**Objective**: Articulate, in `agent-access-policy`, a default-deny posture for host (non-sandboxed) command execution and a log-before-execute audit note, cross-linked from the loop-engineering sandbox subsection.

**Prompt**:
> In `catalog/skills/orchestration/agent-access-policy/SKILL.md`, add a short subsection (8-12 lines) on default-deny host execution: an agent's access policy should deny host (non-sandboxed) shell execution by default and grant it only deliberately; when execution is needed, prefer an isolated sandbox tier (a local container) over the host, and escalate isolation with risk (a local container for untrusted input, stronger isolation for multi-tenant or network-exposed runs); and log shell and file operations before they execute (an audit-before-execute step) so a misbehaving step is visible. Frame this as access-policy doctrine, not a runtime to build. Cross-link the local-only sandbox subsection in `[[loop-engineering]]` ("Sandboxing an Unattended Loop") and `[[containerization]]` and `[[using-git-worktrees]]`. Then add a one-line pointer from the `loop-engineering` "Sandboxing an Unattended Loop" subsection back to this default-deny posture in `[[agent-access-policy]]`. Apply the Reverse-Engineering Attribution Rule: describe generically; do NOT name "DeerFlow", "ByteDance", or literal tokens such as `allow_host_bash` or `SandboxAuditMiddleware`. Constraints: ASCII-only; Markdown style guide; bodies under 500 lines; the new cross-links must resolve. Acceptance: the default-deny host-execution posture and the log-before-execute note are present in `agent-access-policy`; the reciprocal cross-link between it and the loop-engineering sandbox subsection resolves both ways; no upstream names or literal tokens appear.

---

#### 3.2 -- Add the optional typed-fact memory schema note (D2)

**Objective**: Note an optional typed-fact schema for callers who want auditable, source-attributed memory entries, in the memory skill that fits best.

**Prompt**:
> Choose the better target between `catalog/skills/workflow/context-pack-builder/SKILL.md` and `catalog/skills/workflow/continuous-learning/SKILL.md` (prefer `context-pack-builder` if it already discusses durable memory entries; otherwise `continuous-learning`). Add a short optional note (6-10 lines): for callers who want auditable memory, a persisted fact can carry a typed shape -- an id, the fact content, a category, a confidence value, a created-at timestamp, and a source (where the fact came from) -- so memory entries are filterable and their provenance is inspectable. State that this is an optional schema for the persisted entries, not a required format, and that it does NOT introduce an extraction runtime (any LLM-driven extraction is the caller's choice, outside this skill). Apply the Reverse-Engineering Attribution Rule: describe generically; do NOT name "DeerFlow" or use literal tokens such as `memory.json`, `topOfMind`, or `workContext`. Constraints: ASCII-only; Markdown style guide; body under 500 lines; no frontmatter change unless the skill's summary genuinely needs it (decide in 3.4). Acceptance: the optional typed-fact schema note is present in the chosen memory skill, framed as optional and as a schema only (no extraction runtime), with no upstream names or literal tokens.

---

#### 3.3 -- Record the declines and the convergent-validation finding in the RE matrix

**Objective**: Add durable matrix rows so a future comparison recognizes the declined items as already-adjudicated and records the DeerFlow convergent-validation finding.

**Prompt**:
> In `docs/policy/mcp-reverse-engineering-matrix.md`, add a new dated section (modeled on the existing "Declined in the loop-engineering enrichment" section) recording the v3.9.0 adoption-cycle decisions. Record as `drop-outright` (citing the existing standalone-loop-runtime row as precedent): (a) a portable thin loop runner script, and (b) a design-spec-to-resolved-spec compile step that exists only to feed such a runner -- both reverse the v3.1.0 host-driver decision and are already covered by the declarative loop definition plus the host driver. Record as a cautionary not-recommended item (not a drop, since it is the opposite of an adoption): (c) advisory-only cost caps, weaker than the hard caps `ai-billing-safeguards` provides. Add a short note recording the DeerFlow convergent-validation finding: a separate large agent runtime independently converged on the same markdown-SKILL.md plus 3-tier-loading authoring model, which validates the existing design rather than introducing a gap; the runtime itself is out-of-category for a catalog. Reference [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-looper.md](../v3.9.0/comparison-looper.md) and [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-deer-flow.md](../v3.9.0/comparison-deer-flow.md) as the full analyses. Apply the Reverse-Engineering Attribution Rule in the distributed-artifact sense: the comparison report file names already exist and may be cited; do NOT introduce upstream product names into any skill body. Constraints: ASCII-only; Markdown style guide; do not alter existing matrix rows. Acceptance: the new dated section records the two `drop-outright` runtime items with the precedent citation, the advisory-cost-cap cautionary note, and the convergent-validation finding, each referencing the two comparison reports.

---

#### 3.4 -- Registry-edit decision, CHANGELOG, known-gaps, and full consolidation

**Objective**: Decide whether any enriched skill's frontmatter summary changed enough to require the three-registry update, then finalize the cross-file consistency, CHANGELOG, and known-gaps.

**Prompt**:
> Make the registry-edit decision and finalize. (1) Read the final `summary_l0` and `overview_l1` of `cross-model-orchestrator`, `loop-engineering`, `agent-access-policy`, and the memory skill edited in 3.2. If a new headline capability materially changes a one-line summary (the most likely case is `cross-model-orchestrator` gaining handoff egress hygiene as a headline capability), update that skill's `summary_l0` / `overview_l1` AND the three registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) per the AGENTS.md registration rules, and bump the skill's footer version where the skill carries one (cross-model-orchestrator has a `**Version**` footer). If the summaries still accurately describe the enriched skills, leave them and the registries unchanged and record that no registry edit was needed. (2) Run `make validate` (or the fallback validators) after any registry edit and confirm green. (3) Do a full read-through across all four edited skills and the two new/edited reference files for cross-file consistency: the egress-hygiene discipline (Phase 1), the design-first section and verification ordering (Phase 2), and the default-deny posture (Phase 3) do not contradict each other or the existing Strict Control Loops, Exit-Signal Protocol, Stall and Fault Detection, Workflow-Control Patterns, or Sandboxing material; the L1 egress hygiene and the loop-engineering council cross-link agree. (4) Grep the full diff across all three phases for "Looper", "ksimback", "DeerFlow", "ByteDance", "loop.yaml", "loop.resolved.json", "run-loop.py", "ensure_consent", "RUN_IN_SESSION", "allow_host_bash", "memory.json" and expect zero matches in any distributed artifact. (5) Add a `## [Unreleased]` entry to `CHANGELOG.md` describing the loop-design and cross-model-egress-hygiene enrichment, the two DeerFlow doctrine notes, and the recorded declines plus convergent-validation finding. (6) Update `docs/v3/v3.9/known-gaps.md` (create it if absent) with any deferred items. Fix any failure and re-run until green. Then run `/session history` to document Phase 3.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - no constitution file; all recommended items are skill-native over owned skills with no policy violations; the highest-value item strengthens the egress policy) | | |

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed (1.1, 1.2, 1.3)
- [x] Handoff Egress Hygiene section present: default redaction globs, marker convention, first-send consent content, record-of-consent, local-reviewer carve-out; MCP Registry Policy cited by name
- [x] Reviewer-versus-judge distinction and verdict-honesty rule present in Step 4, tied to the self-review rationalization
- [x] Argv-array invocation discipline bullet present in Best Practices
- [x] No upstream product name or literal field token in any distributed artifact (grep clean)
- [x] `cross-model-orchestrator` body under 500 lines (310); frontmatter unchanged in this phase
- [x] Validators green (JSON integrity PASS; orphan-bundle audit PASS, 0 errors; three wikilinks resolve; MCP Registry Policy reference resolves)
- [x] Session history generated for Phase 1
- [x] Ready to advance to Phase 2

### Phase 2 Exit Checklist

- [x] All sub-tasks completed (2.1, 2.2, 2.3)
- [x] "Design the Loop Before You Run It" section present; composes the task-readiness gate plus `ambiguity-detector` plus `requirement-enhancer` without duplication
- [x] Verification-type ordering (programmatic, then judge, then human) stated; render-and-confirm-before-first-run note present and tied to scope-first calibration
- [x] Argv-array note present in the `check_command` guidance; council-seat material cross-links the cross-model egress hygiene
- [x] Any new `references/loop-design-rubric.md` is linked from SKILL.md (no orphan) -- N/A: body at 207 lines stayed under the norm, so no reference file was created
- [x] No upstream product name or literal token in any distributed artifact (grep clean)
- [x] `loop-engineering` body under 500 lines (207); new section consistent with existing loop sections
- [x] Validators green (JSON integrity OK; orphan-bundle audit PASS 0 errors; unicode-safety exit 0; three wikilinks resolve)
- [x] Session history generated for Phase 2
- [x] Ready to advance to Phase 3

### Phase 3 Exit Checklist

- [x] All sub-tasks completed (3.1, 3.2, 3.3, 3.4)
- [x] Default-deny host-execution posture and log-before-execute note present in `agent-access-policy`; reciprocal cross-link with the loop-engineering sandbox subsection resolves both ways
- [x] Optional typed-fact memory schema note present in the chosen memory skill (`context-pack-builder`), framed as optional and schema-only (no extraction runtime)
- [x] RE matrix records the two `drop-outright` runtime declines (with v3.8.0 host-driver precedent citation), the advisory-cost-cap cautionary note, and the convergent-validation finding, each referencing the two comparison reports
- [x] Registry-edit decision made and validated: NO edit needed (all four summaries still accurate; doctrine refinements within existing scope, per the v3.8.0 precedent); registries and cross-model-orchestrator footer version unchanged
- [x] Full cross-file consistency read-through passed; nothing implies a shipped loop runtime or a new dependency (egress hygiene and default-deny cover different boundaries and reinforce each other)
- [x] No upstream product name or literal token in any distributed artifact (grep clean across the full diff)
- [x] Validators green (JSON integrity OK; orphan-bundle PASS 0 errors; quality PASS 0 warnings; unicode-safety exit 0, no edited file flagged); all edited bodies under 500 lines (agent-access-policy 277, context-pack-builder 159, cross-model-orchestrator 310, loop-engineering 209)
- [x] CHANGELOG `## [Unreleased]` entry added; `docs/v3/v3.9/known-gaps.md` created
- [x] Session history generated for Phase 3

---

## Definition of Done

- All three phases complete with their Exit Checklists satisfied.
- The P1 security gap (L1 handoff egress hygiene) and the P1 design gap (L2 design-first loop section) are both delivered.
- The two P2 items (L3 verdict-honesty rule, L4 verification ordering plus render-and-confirm) and the three P3 items (L5 argv-array discipline, D1 default-deny posture, D2 typed memory schema) are delivered.
- The three declines and the DeerFlow convergent-validation finding are recorded in the RE matrix.
- Every recommended change is local Markdown over owned skills; no new skill, command, hook, outbound call, dependency, or credential was introduced.
- No upstream attribution appears in any distributed artifact; all content is ASCII-only and conformant to the Markdown style guide; the full validator chain is green.
