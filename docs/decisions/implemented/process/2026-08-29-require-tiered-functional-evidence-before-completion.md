# Decision: Require tiered functional evidence before completion

Status: implemented - completion now requires proportional real-boundary evidence per phase, an always-recorded plan delta, and one fail-closed whole-plan deep pass before publication

## Problem

Nexus-Hub's implementation workflow could pass syntax, lint, unit-test, coverage, and repository validation gates while the feature a user would actually operate remained broken. The v4.2 guide exposed the gap: source and structural checks were green while rendered layouts still clipped, overlapped, or became unreadable at real viewport sizes.

The missing control was not another static validator. Different artifacts become trustworthy at different boundaries: a CLI must run through its public command, a hook must consume real payloads, an installer must materialize and register files in a destination, and rendered HTML must be measured in a browser. Treating all of those as ordinary unit tests either misses the boundary or forces expensive infrastructure into every phase.

Verification cost also has to scale with blast radius. Running the complete repository suite and an adversarial whole-plan review after every subtask would make the workflow too slow to follow, while reserving every dynamic check for release repeats the original failure. The process needs cheap feedback while work is local and deeper evidence only when the complete tree exists.

The decision must remain ownership-safe across the catalog. Evidence freshness, gate disposition, browser diagnosis, accessibility, visual judgment, adversarial testing, code-to-plan convergence, and known-gap lifecycle already have owners. A new verification surface cannot restate those rules without creating conflicting contracts.

## Decision

Nexus-Hub uses a four-tier verification ladder tied to the existing implementation lifecycle.

Tier 0 runs cheap compile, import, schema, or parse checks while a subtask is being built. Tier 1 is a fifth phase-boundary gate: exercise the phase's own feature through a representative real boundary and record expected versus observed behavior. Tier 2 always writes `## Plan delta` during post-phase work so a false assumption or incomplete plan remains visible even when it is not blocking. Tier 3 runs once in the final phase, inventories every independently observable feature from the full plan, exercises each at its real boundary, invokes the relevant rendered-surface and adversarial owners, and independently reviews the resulting tree against the plan Goal before publication.

`functional-verification` owns the artifact-specific exercise procedure and the bounded Tier 3 runbook. It delegates evidence freshness to `verification-before-completion`, gate disposition to `quality-gate-definitions`, browser and rendered judgments to their existing owners, hostile testing to `adversarial-verifier`, implementation-to-plan assessment to `implementation-convergence`, and residual work to `known-gaps-tracker`. Missing required delegates are recorded as `NOT COVERED`; their rules are never reconstructed from memory.

The ladder is enforced at the highest-leverage generation and execution points. `implementation-plan` emits an explicit verification expectation beside every phase Stability Gate and emits the final Tier 3 evidence duty. `implement-phase` requires the proportional Tier 1 smoke, always records Tier 2, and treats missing Tier 3 evidence as fail-closed. Installer and platform checks prove that the skill, its bundled resources, the responsive-layout rule, and its enforcement hook reach real user destinations.

Blast-radius ambiguity selects the deeper path. The Tier 3 runbook has one global maximum of three fix-and-rerun cycles across all findings and delegates; the counter cannot reset per feature. This bounds cost without turning exhausted findings into silent passes.

## Alternatives considered

- **Keep compile, lint, unit tests, coverage, and repository validators as the complete gate.** Rejected because those checks prove their own contracts, not the user-facing boundary. They all passed while the rendered guide still failed. Adding more source-shape assertions would strengthen the same blind spot.
- **Run the complete Tier 3 deep pass after every phase.** Rejected because most phases change one narrow surface and do not yet contain a coherent whole-plan tree. Repeated browser, installer, adversarial, and full-suite work would multiply runtime and CI cost while producing weaker evidence against known-incomplete work.
- **Use screenshots or maintainer eyeballing as the functional gate.** Rejected because a screenshot lacks a declared expected result, measured geometry, interaction state, environment, and reproducible action. Visual review remains useful, but only through the rendered-surface owners and with observable evidence rather than an impression.
- **Create separate verification rules inside every producing skill.** Rejected because duplicate rules drift and produce conflicting findings. One procedure owner with explicit delegates keeps artifact exercise reusable while preserving the existing ownership boundaries.
- **Reserve dynamic verification for the publication pull request.** Rejected because the first real exercise would then occur after every local phase had been declared complete and committed. A failure would invalidate several phase records at once and train maintainers to treat late red checks as expected noise.

## Consequences

- Every phase now carries one additional proportional functional smoke. This adds local cost, but the exercise is limited to the feature changed by that phase rather than the complete suite.
- Every phase leaves a durable plan-delta record, including a truthful no-blocking-delta result. Future plans can distinguish implementation success from confirmation that the original assumptions were correct.
- Final phases take longer because Tier 3 dynamically exercises the whole plan, runs adversarial and convergence delegates, and precedes publication. That cost is intentional and occurs once on a complete tree.
- Artifact-specific evidence becomes comparable: records name the revision, input, action, expected result, observed result, environment, and evidence paths. A zero exit code with wrong output no longer qualifies as a pass.
- Missing tools, delegates, browsers, or platform evidence become visible `NOT COVERED` findings or owned known gaps instead of implicit coverage claims.
- The process depends on generated plans and executors retaining the ladder contract. Lifecycle and cross-link tests therefore make those text contracts load-bearing and will fail on accidental removal or reordering.
- Browser-backed visual verification stays optional in ordinary CI. The renderer-backed tests skip cleanly without a local browser, while final-phase work on a capable host must run them when the blast radius includes rendered HTML.
- Installer upgrades now reconcile managed hook registrations generically. This increases installer complexity, but it prevents a copied hook from remaining inert in an existing user's settings and keeps cross-host `.sh` and `.ps1` counterparts idempotent.
