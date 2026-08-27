# Spec-Driven Development in Nexus-Hub

A methodology essay for v2.1.0. This document explains why the v2.1.0 adoption of constitution, clarification, spec-template, and cross-artifact-analyzer machinery shifts the way Nexus-Hub thinks about writing software, and how to practice it with the catalog you already have installed.

## 1. The Power Inversion

For most of the history of software, the source code has been the authoritative artifact and the specification has been a secondary, decaying document - written once, drifting immediately, abandoned within weeks. The asymmetry was a consequence of the cost gradient: writing prose was free, writing executable code was expensive, and the executable side won by attrition. Specifications were aspirational; the binary was real.

That asymmetry no longer holds. With modern LLM-driven coding harnesses (Claude Code, Codex, Gemini Antigravity, Cursor, OpenCode, Copilot - all the platforms Nexus-Hub targets), generating thousands of lines of compliant code from a clear prompt is now cheap. The expensive part has moved upstream: deciding what the system should do, in what order, under what constraints, with what success criteria. Nexus-Hub's v2.1.0 adoption is built around that inversion.

The proposition is simple: **the specification is the source of truth, and code is the artifact the specification compiles to**. When the spec changes, the code is regenerated or amended to match. When the code drifts, the analyzer flags it and the spec is updated to reflect the new ground truth. Neither side is allowed to silently outpace the other.

This is not a rhetorical flourish. The v2.1.0 commands - `/constitution`, `/clarify-spec`, `/analyze-spec`, `/generate-plan` with `--specs-layout`, `/tasks-to-issues` - are each designed to enforce a specific direction of that compile step. The constitution constrains what plans are allowed. The clarification loop forces the spec to be unambiguous before planning starts. The analyzer cross-checks that every requirement has a task and every task traces to a requirement. The plan generator emits tasks in a strict format that downstream tooling (the analyzer, the issues converter) can parse without guessing.

The gap between intent and implementation does not close on its own. The commands close it deliberately, one gate at a time.

## 2. The Nexus-Hub SDD Workflow

The full v2.1.0 spec-driven flow has seven stations. Each one corresponds to a command or template you already have installed:

1. **Constitution** - `/constitution`. Establish the project's MUST / SHOULD principles in a versioned governance file (`docs/<version>/constitution.md`). This file is consulted by every downstream command. Constitutions are SemVer'd: MAJOR for principle removals, MINOR for additions, PATCH for clarifications. The amendment workflow emits a Sync Impact Report at the top of the file so reviewers can see what changed.
2. **Specify** - write a feature spec using `catalog/templates/spec-template.md`. The template forces user stories at P1 / P2 / P3 priority, each with an Independent Test criterion, and functional requirements with `FR-###` IDs plus success criteria with `SC-###` IDs. These IDs are not decoration. They are the join keys the analyzer uses to build the Coverage Summary table.
3. **Clarify** - `/clarify-spec`. A sequential five-question loop scans the spec for the ten ambiguity categories (Functional Scope, Domain & Data Model, Interaction & UX, Non-Functional Quality, Integration, Edge Cases, Constraints, Terminology, Completion Signals, Misc Placeholders). Each question is asked one at a time with a Recommended option at the top and the remaining options in a Markdown table. Accepted answers are written back into a `## Clarifications` section in the spec, and the relevant body sections are updated atomically after each answer.
4. **Plan** - `/generate-plan`. Produces a phased implementation plan that surfaces a Constitution Check gate before Phase 0 research and re-checks after Phase 1 design. Plans that violate a constitution MUST principle have to document the violation in a Complexity Tracking table or revise the plan.
5. **Tasks** - the same `/generate-plan` invocation emits tasks in the strict `- [ ] T### [P?] [US?] description with file path` format. Setup and foundational phases have no `[US#]` label; user-story phases require one; the `[P]` marker is added only to genuinely parallelizable tasks.
6. **Analyze** - `/analyze-spec`. Read-only cross-artifact pass: duplication, ambiguity, underspecification, constitution alignment, coverage gaps, inconsistency. Findings are severity-tagged (CRITICAL / HIGH / MEDIUM / LOW) and reproducible across reruns (stable IDs).
7. **Implement** - `/implement-phase` plus the existing phase-by-phase machinery from the workflow skill catalog. Implementation does not begin until the analyzer is clean, or until the user explicitly accepts known gaps with documented justification.

Each station has an exit gate, and each gate is observable - the analyzer either reports coverage gaps or it does not, the constitution either has a Sync Impact Report or it does not, the clarification session either resolved the markers or it did not. Specs that pass the gates are the artifacts the implementation step compiles from.

## 3. Why Now

Three pressures meet in 2026. Each is independently sufficient to motivate spec-driven discipline; together they make it unavoidable.

**AI capability has crossed a threshold**. The bottleneck in agentic coding is no longer "the model cannot write the code" - it is "the model wrote the wrong thing because the specification was ambiguous". A capable LLM applied to a vague prompt produces a confident, plausible artifact that solves a different problem than the one the user had in mind. The error is invisible at the line-of-code level and only surfaces during integration testing or, worse, in production. Nexus-Hub's catalog includes a `semantic-bug-detector` skill, an `ambiguity-detector` skill, and a `cross-artifact-analyzer` skill precisely because line-level review no longer suffices.

**Software complexity is compounding**. Modern features touch authentication, data persistence, observability, billing, compliance, and at least three frontend frameworks before they are considered shipping-ready. The implicit knowledge required to reason about all of them in a single human head no longer fits there. The specification document is the only artifact that survives the round-trip across a multi-disciplinary review.

**The pace of change has accelerated past the documentation cycle**. Code is rewritten weekly; the README, the design doc, and the architecture diagram lag behind by months. When the specification IS the source of truth - when code is regenerated from the spec, when changes to behavior require an amendment to the spec first, when the analyzer flags drift - the documentation stops being a separate maintenance burden. It becomes the thing you edit when you want to change behavior.

The harness exists to amplify the developer, not to replace them. The developer's role shifts from "type the code" to "make the specification crisp enough that the code follows mechanically". That is more, not less, intellectual work. It is just different intellectual work.

## 4. Core Principles

Six principles run through every v2.1.0 command. They are not aspirational - they are testable assertions about the artifacts the commands produce.

**Specs as lingua franca**. A specification written in the v2.1.0 template is readable by a non-technical stakeholder, by an LLM agent, and by the analyzer. The template forbids implementation details in the spec - no language names, no framework names, no API names. The spec describes what the system does for the user, in language the user understands. A spec that mentions "we'll use Postgres for this" has leaked an implementation detail and the spec-quality-checklist flags it.

**Executable specs**. The spec is structured so that downstream tooling can compile it. `FR-###` IDs become join keys for the coverage matrix. `SC-###` IDs become acceptance criteria for `/implement-phase`. User stories at P1 / P2 / P3 become the MVP sequencing for the plan. The structure is mechanical because the next station consumes it mechanically.

**Continuous refinement**. The clarification loop is not a one-shot interrogation. It is a tool you run any time you notice an ambiguity, and re-run when new information surfaces. The Clarifications section in the spec accumulates - each session timestamped, each Q-and-A appended - so the reasoning history is preserved.

**Research-driven context**. `/generate-plan` consumes the constitution, the spec, the existing catalog of skills, and the prior known-gaps file. It is not asked to invent context; it is asked to combine context that has already been written down. This is why the catalog has dedicated skills for `context-engineering`, `context-manager`, and `known-gaps-tracker` - they ensure the relevant context is captured in a form the plan generator can find.

**Bidirectional feedback**. When implementation reveals that a requirement was wrong, the spec is amended, not patched in code. When the analyzer flags a task without a requirement, the requirement is added, not the task deleted. The two artifacts converge over the life of the feature, with the spec leading and the code following.

**Branching for exploration**. The `--specs-layout` flag (Phase 7) opts into a `specs/<NNN>-<slug>/` directory. This is the substrate for running multiple parallel explorations against the same backlog item - one branch tries a state-machine approach, another tries a CRDT, the analyzer runs against both, and the user picks. Branching is cheap when the spec is the source of truth, because each branch is just a different compilation target.

## 5. Implementation Approaches

There is no single "right" way to run a spec-driven feature in Nexus-Hub. The catalog supports three approaches, scaled to the size of the change.

**Tiny change (one file, one obvious behavior)**. Skip the spec entirely. Use `incremental-implementation` or the tactical workflow skills directly. The cost of writing a spec exceeds the cost of the change. Examples: a typo fix, a config-file value bump, a one-line refactor.

**Medium change (one feature, one or two user stories, touches three to ten files)**. Run the lightweight flow: `/clarify-spec` against a one-page spec, `/generate-plan` without `--specs-layout`, `/analyze-spec` once before implementation, `/implement-phase` per phase. The output lives under `docs/<version>/plans/<slug>.md` with no separate `specs/` directory. This is the dominant mode for catalog work inside Nexus-Hub itself.

**Large change (cross-cutting initiative, multiple user stories, touches multiple packages or installer logic)**. Run the full flow: `/constitution` if no constitution exists yet, the spec template with three or more user stories, `/clarify-spec` until the spec is clean, `/generate-plan --specs-layout` to land at `specs/<NNN>-<slug>/spec.md` + `plan.md` + `tasks.md`, `/analyze-spec` repeatedly through development, `/tasks-to-issues` if the team uses GitHub Issues for visibility. The G12 installer-refactor effort in v2.2.0 is the canonical example.

Choosing the right approach is itself a spec-quality skill. Over-specifying a tiny change wastes effort. Under-specifying a large change strands the implementation in rework. The constitution can mandate which approach applies above a complexity threshold - this is one of the things constitutions are for.

## 6. Template-Driven Quality

The v2.1.0 templates are not stylistic preferences. Each constraint they impose corresponds to a failure mode that has actually happened in catalog work.

**`[NEEDS CLARIFICATION: <specific question>]` with a 3-marker hard limit**. Markers force the agent to surface uncertainty rather than guess. The 3-marker limit forces prioritization - scope first, then security and privacy, then UX, then technical concerns. If a spec accumulates more than three markers, the agent is required to demote the lower-priority ones to assumptions documented in the Assumptions section, with an informed default value. The cap exists because specs with twelve outstanding markers do not get clarified - they get abandoned.

**FR-### and SC-### IDs**. The analyzer's Coverage Summary table is keyed on these IDs. A spec written with prose bullets instead of IDs produces an empty matrix, and the analyzer cannot tell whether requirements have tasks. The IDs are the data model of the coverage check.

**User stories at P1 / P2 / P3 with Independent Test criteria**. The MVP rule states that implementing only the P1 story must yield a viable shipped product. This forces the spec author to commit to which behavior is truly load-bearing versus which is enhancement. The Independent Test criterion forces a verifiable success condition per story - "this story is done when X is true" rather than "this story is done when it feels right".

**Spec-quality-checklist as unit tests for English**. Before planning begins, the spec passes through the checklist: no implementation details, no [NEEDS CLARIFICATION] markers remain, requirements are testable, success criteria are measurable, all acceptance scenarios are defined, edge cases are identified, scope is bounded, assumptions are documented. Each line item is a binary check, and the checklist is iterated up to three times until clean. Beyond three iterations the remaining gaps are documented in the Notes section and the user is warned - the spec is allowed to proceed with known weak points, but the weak points are visible rather than hidden.

The constraints reinforce one another. A spec that satisfies the template is one the analyzer can mechanically check; a spec the analyzer can check is one the planner can mechanically decompose into tasks; a task list with strict format is one the issues converter can mechanically translate. The compile chain is only as strong as the format constraints holding it together.

## 7. Pitfalls and Anti-Patterns

Spec-driven development has its own failure modes. Naming them prevents the methodology from becoming a religion.

**Over-specifying the trivial**. A two-line fix to a typo does not need a constitution check, a spec, a clarification loop, an analyzer pass, and a plan. The catalog includes `incremental-implementation` and tactical refactoring skills for exactly this case. Apply spec-driven discipline at the threshold where the cost of mis-specification exceeds the cost of writing the spec.

**Hiding behind the gate**. A spec that passes every checklist item but is still ambiguous in practice has been gamed. The checklist items are necessary, not sufficient. The clarification loop is the corrective: when a reviewer cannot answer "what does this spec actually want?" in one breath, more clarification is needed regardless of which checkboxes are ticked.

**Forgetting that constitutions are versioned**. A constitution that has not been amended in six months while the project has shipped twelve features is probably out of date. The Sync Impact Report is the prompt to revisit. When a feature plan keeps grinding against a constitution principle, the answer is sometimes "amend the principle", not "delay the feature". Constitutions are governance documents, not stone tablets.

**Treating the analyzer as a linter**. The analyzer's findings include severity tags for a reason. CRITICAL findings (constitution MUST violations, zero-coverage core requirements) block. HIGH and MEDIUM findings inform. LOW findings are noise unless a pattern emerges. A team that treats every analyzer warning as blocking will spend all its time servicing the analyzer and none of its time shipping.

**Spec drift in long-running features**. Specs written for week-long features stay roughly stable. Specs for month-long features need an explicit re-clarification cadence - the catalog's `dev-progress-tracker` skill keeps `docs/todos.md` in sync, but the spec itself needs intentional revisiting. A spec that has not been touched in three weeks while the implementation has continued is, by definition, drifted.

**Conflating skills with commands**. Skills (`spec-driven-development`, `ambiguity-detector`, `idea-refine`) are knowledge bundles the agent triggers automatically. Commands (`/clarify-spec`, `/analyze-spec`, `/generate-plan`) are explicit invocations the user types. Both exist for the same reason - to convert vague intent into checkable artifacts - but they are not interchangeable. A skill answers "how should I think about this?". A command answers "go do this now".

## 8. Closing

The v2.1.0 commands are tools, not a methodology in themselves. The methodology is the disciplined practice of treating the specification as the artifact that compiles, and the code as the artifact that compiles from it. The commands are how Nexus-Hub makes that practice mechanical instead of aspirational.

The thing to keep in mind, when starting a feature: the gate is not "did I run the commands". The gate is "is the specification crisp enough that someone other than me could turn it into the right code". When the answer is yes, the implementation flows. When the answer is no, the commands exist to help you get to yes.

That is the inversion. Code follows. Specs lead.

## Related artifacts

- `catalog/skills/developer-experience/spec-driven-development/SKILL.md` - the catalog skill this essay grounds.
- `catalog/templates/spec-template.md` - the spec skeleton with FR-### / SC-### conventions.
- `catalog/templates/constitution-template.md` - the governance file skeleton.
- `catalog/templates/spec-quality-checklist.md` - the "unit tests for English" checklist.
- `catalog/commands/constitution.md`, `clarify-spec.md`, `analyze-spec.md`, `generate-plan.md`, `tasks-to-issues.md` - the v2.1.0 command surface.
- `docs/archive/v2/v2.0/comparison-spec-kit.md` - the upstream comparison that motivated v2.1.0.
- `docs/archive/v2/v2.1/plans/adoption-spec-kit.md` - the phased implementation plan for v2.1.0 and v2.2.0.
