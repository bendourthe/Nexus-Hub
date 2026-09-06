# Verification Ladder - v4.3.0

**Status**: Accepted for implementation
**Plan**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md`
**Decision date**: 2026-08-29

## Decision

Nexus-Hub will verify behavior as well as artifacts. Every implementation subtask keeps its effectively free compile or import check, every phase adds a cheap deterministic functional smoke, every phase records whether implementation changed the plan's credibility, and the final phase runs one blast-radius-scaled deep pass before release.

The ladder deliberately spends fewer iterations during a phase and more once at the end. Later phases often rewrite earlier work, so repeating the deepest review at every boundary pays several times for evidence that later edits invalidate. Cheap checks still run continuously because they localize defects while the changed code is fresh.

## Contract summary

| Tier | When | Required work | Typical budget | Failure meaning | Waiver authority |
|---|---|---|---|---|---|
| Tier 0 | After each subtask | Compile, import, parse, or load the changed unit | 1-30 seconds; no separate model pass; at most a one-line record | The subtask is broken and the next subtask must not start | No routine waiver; an explicit maintainer decision must become a `QG` gap before work continues |
| Tier 1 | At every phase GO/NO-GO gate | Tests, coverage, lint, build, artifact-appropriate static checks, and one proportional functional smoke of the phase's own output | 10 seconds to 5 minutes in the common case; roughly 200-800 tokens to select, interpret, and record the smoke | The phase produced an artifact but did not prove its observable behavior | Maintainer only, explicitly, with a `QG` gap naming the missing evidence |
| Tier 2 | During every phase post-phase sequence | One plan-delta paragraph: no delta, wrong plan, incomplete plan, or false assumption | Under 2 minutes; roughly 100-300 output tokens | A blocking delta means the remaining plan is no longer trustworthy as written | The record itself is not waivable; a blocking delta must be fixed in the plan or recorded as `DF` or `QG` with an owner |
| Tier 3 | Once in the final phase when blast-radius triggers fire | Exercise every feature from the whole plan, review UI/UX when applicable, run an adversarial pass, and audit whether the plan was sufficient for the Goal | 20-90 minutes and roughly 3,000-15,000 working tokens, bounded to three fix-and-rerun iterations | Release evidence is incomplete or the plan Goal is not fully served | Maintainer only, explicitly, with each omitted duty recorded as `QG` or `DF`; release remains fail-closed otherwise |

The time and token figures are operating budgets, not performance promises. Local commands themselves consume no model tokens; the token ranges describe the reasoning needed to choose checks, interpret results, and write evidence.

## Tier 0 - subtask integrity

Tier 0 prevents broken subtasks from accumulating. After each subtask, run the smallest deterministic check that proves the changed unit can be loaded by its real runtime:

- Python: compile or import the changed module.
- JavaScript or TypeScript: parse, type-check, or build the changed unit.
- Shell or PowerShell: parse the script and invoke a no-op or help path when one exists.
- JSON, YAML, or configuration: parse and validate against its schema or consuming loader.
- Markdown or generated documentation: run the repository's structural or Unicode-safety check for the changed file.

Tier 0 does not prove user behavior. It answers only: "Can the next subtask safely build on this state?".

## Tier 1 - phase behavior gate

Tier 1 retains the existing four gates and adds the missing fifth gate: the phase's own feature was exercised and observed. The evidence must be proportional to the artifact and must check output as well as successful execution.

| Artifact | Cheap functional smoke | Evidence that counts | Evidence that does not count |
|---|---|---|---|
| CLI | Run one representative real command with real arguments | Exit code plus expected stdout/stderr fragment or created artifact | Exit code alone |
| Library or API | Call through one real public boundary | Returned value, response, persisted state, or observable side effect | An isolated unit mock that bypasses the boundary |
| Web UI | Render the changed view, perform its primary interaction, and run the visual detector on the affected page | Loaded page, interaction result, console/runtime verdict, and detector result | Source inspection or an old screenshot |
| Hook or script | Fire one valid and one malformed payload through the real entry point | Exit code, stdout/stderr contract, and intended block/allow behavior | Parsing the source without invoking it |
| Document or artifact generator | Generate one representative output and open or parse it with the intended consumer | Output path plus successful consumer load and one content assertion | File existence alone |
| Configuration | Apply the configuration to the real loader or a faithful scratch install | Observed behavior change and parsed effective value | Reading the edited text |
| Documentation-only release evidence | Run static Markdown, link, and Unicode checks; record that no runnable feature changed | Passing checks plus the diff path proving the no-op | A silent skip |

The fifth gate delegates the per-artifact procedure to `functional-verification`. `verification-before-completion` still owns whether the resulting evidence is fresh and sufficient for a completion claim. Tier 1 never expands into the whole-plan Tier 3 pass.

## Tier 2 - plan-delta note

Every phase history file gains a `## Plan delta` paragraph with exactly one primary disposition:

- **No delta**: implementation confirmed the phase's assumptions and scope.
- **Wrong**: a planned instruction would have produced the wrong behavior.
- **Incomplete**: reaching the phase Goal required work no task captured.
- **False assumption**: a dependency, platform behavior, or repository fact differed from the plan.

The note names the evidence and the consequence for remaining phases. A non-blocking delta stays in session history and may inform later phases. A blocking delta updates the plan before the driver continues or becomes a `DF` or `QG` known gap with Source phase, Plan reference, Reason, and Suggested next step. "No delta" is a considered result, not an omitted section.

## Tier 3 - final deep pass

Tier 3 runs once after all implementation phases have contributed their final shape. In order, it:

1. Evaluates the objective blast-radius triggers and writes either a run verdict or a reasoned no-op.
2. Enumerates every user-observable feature produced by every phase, then exercises each through its real boundary.
3. For rendered surfaces, invokes browser runtime checks, accessibility review, the visual-defect detector, and holistic interface review through their owning skills.
4. Invokes `adversarial-verifier` after standard functional verification and requires observed proof for confirmed findings.
5. Runs code-vs-plan convergence through `implementation-convergence`.
6. Runs the distinct plan-completeness audit: whether the plan itself was sufficient to reach the stated Goal and the maintainer's request.
7. Fixes findings and repeats the affected checks, up to three total fix-and-rerun iterations.

At iteration-budget exhaustion, remaining findings become owned known gaps. A release blocker still blocks publication unless the maintainer explicitly downgrades it with a recorded `QG` gap.

## Economics

The ladder minimizes repeated expensive judgment without weakening continuous feedback. Let `P` be the number of phases, `C` the combined Tier 1 plus Tier 2 cost per phase, and `D` the Tier 3 cost. Running the deep pass at every phase costs `P * (C + D)`. This ladder costs `P * C + D`. The avoided cost is `(P - 1) * D`, which grows with every phase while the final evidence remains current against the completed tree.

For this five-phase plan, use an illustrative midpoint of 3 minutes for Tier 1, 1 minute for Tier 2, and 60 minutes for Tier 3:

- Deep pass every phase: `5 * (3 + 1 + 60) = 320 minutes`.
- Tiered ladder: `5 * (3 + 1) + 60 = 80 minutes`.
- Avoided repeated work: `240 minutes`, or 75 percent of the first approach.

Using illustrative reasoning budgets of 500 tokens for Tier 1, 200 for Tier 2, and 10,000 for Tier 3 gives the same shape:

- Deep pass every phase: `5 * (500 + 200 + 10,000) = 53,500 tokens`.
- Tiered ladder: `5 * (500 + 200) + 10,000 = 13,500 tokens`.
- Avoided repeated reasoning: `40,000 tokens`, about 75 percent.

These examples justify the ordering, not a fixed quota. A security boundary may need the high end of the Tier 3 range; a prose-only correction should record a no-op.

## Objective blast-radius triggers

Tier 3 runs when any trigger is positive. Detection uses the final plan diff against the integration base, not a remembered summary. Ambiguity resolves in the safe direction: run Tier 3.

| Trigger | Mechanically evaluable diff evidence | Result |
|---|---|---|
| User-facing surface | Changes to UI templates/styles/components, CLI commands or output strings, user-facing hooks, interactive guides, or generated documents | Run Tier 3 and exercise the changed primary flow |
| Rendered or generated artifact | Changes to `.html`, `.css`, SVG, generator code/templates, document exporters, presentation builders, or renderer tooling | Run Tier 3; include real generation/rendering and geometry checks |
| Distributed or released artifact | Changes under `catalog/`, `templates/`, `configs/`, installers, package manifests, registries, extensions, or release workflows | Run Tier 3; include a scratch install or package inspection |
| Security, authentication, or data boundary | Changes to permissions, credentials, auth/session logic, network egress, persistence, schemas, migrations, validation, or security hooks/rules | Run Tier 3; include adversarial inputs and boundary evidence |
| Public interface or contract | Changes to a public API, CLI syntax, hook payload, schema, skill/command contract, config key, installer destination, or documented compatibility promise | Run Tier 3; exercise both normal and malformed consumers |

The only automatic no-op class is a diff limited to release evidence or living prose that changes no command, code block, link target, contract statement, generated output, or user workflow. Examples include a spelling correction in a release history or a date correction in an evidence table. A documentation change under `catalog/skills/`, `catalog/commands/`, rules, templates, or user guides is distributed behavior and therefore triggers Tier 3.

The required no-op record is:

```markdown
### Tier 3 blast-radius verdict

- **Verdict**: no-op
- **Diff evidence**: <exact paths and change class>
- **Reason**: <why none of the five triggers applies>
- **Ambiguity check**: none; if ambiguous, change the verdict to run
```

## Finding disposition and waiver rules

| Finding | Default action | Record |
|---|---|---|
| Tier 0 failure | Fix before the next subtask | Subtask log; `BG` only if unresolved |
| Tier 1 failure | Reopen the phase and fix, then rerun the smoke | Phase history and `BG`, `MT`, or `QG` if unresolved or bypassed |
| Tier 2 blocking delta | Correct the remaining plan before continuing | `## Plan delta`; `DF` or `QG` if not corrected |
| Tier 3 functional, visual, UX, adversarial, or plan-completeness finding | Fix and rerun within the three-iteration budget | Last-phase evidence; owned known gap at exhaustion |
| Cannot-run or missing instrument | Treat as missing evidence, never as a pass | `QG` with the unavailable dependency, owner, and next step |

Only the maintainer may waive a blocking verification duty. Silence, a passing unrelated test, an earlier screenshot, or a prior agent's confidence is not a waiver.

## Historical failure coverage

| Historical defect | First catching tier | How it is caught |
|---|---|---|
| Scene 5 command chip was 58 px for a label needing about 80 px | Tier 1 for the changed UI; Tier 3 as the final backstop | Render the affected page and flag text in an undersized rendered box |
| Outcome subtitle extended past the SVG viewBox | Tier 1 for the changed UI; Tier 3 as the final backstop | Compare rendered SVG text geometry with the viewBox bounds |
| Two Scene 5 captions collided | Tier 1 for the changed UI; Tier 3 as the final backstop | Detect overlapping text-bearing boxes at the affected viewport |
| Training takeaway rule stopped at 45 percent because a `78ch` cap survived | Tier 1 | Static fixed-width declaration check and rendered geometry smoke |
| Training terminal echoed the command twice | Tier 1 | Perform the interaction and assert the observed output, not only exit success |
| A monitor was silently dead because `jq` was absent | Tier 1 | Invoke the real script without the optional tool and require a non-zero cannot-run result or a native fallback, never silence |
| A contrast token regressed when a new component used it for small text | Tier 3 | Render the final component set and delegate applicability/severity to accessibility review and measurement/remediation to the color owner |

Every named historical defect has a catching tier. The first four green artifact gates alone would catch none of the rendered or interactive failures.

## Rule ownership

Exactly one skill owns each concern. Non-owners invoke or reference that owner and do not restate its rules.

| Concern | Owner | Boundary and handoff |
|---|---|---|
| Fresh evidence before any "done", "works", or "pass" claim | `verification-before-completion` | Owns claim-to-evidence matching and freshness; `functional-verification` produces behavioral evidence but does not decide whether an unsupported claim is allowed |
| Dynamic exercise by artifact type and the observable evidence each exercise must produce | `functional-verification` | New owner; delegates browser, accessibility, interface, adversarial, and evidence-freshness concerns rather than restating them |
| Post-implementation plan sufficiency against the Goal and maintainer request | `functional-verification` Tier 3 plan-completeness audit | New owner; distinct from code-vs-plan convergence because it questions whether the plan was enough |
| Hostile stress testing and proof-of-failure | `adversarial-verifier` | Runs after baseline functional verification; does not own the baseline smoke or plan audit |
| Automated browser regression architecture and CI integration | `e2e-testing-automation` | Owns Playwright/Cypress/Selenium suites, selectors, snapshots, and flake control; the geometry detector is an instrument invoked by `functional-verification` |
| Development-time browser runtime observation and diagnosis | `browser-testing-with-devtools` | Owns network, console, storage, Elements, and performance evidence; not automated-suite design or accessibility rules |
| Holistic multi-domain UI review orchestration and one consolidated verdict | `interface-review` | Owns ordering, coverage honesty, deduplication, and caps; its delegates keep their domain rules |
| Accessible interaction requirements and severity | `accessibility-engineering` | Owns names, semantics, keyboard, focus, forms, hit areas, motion, and zoom/reflow; `color-systems` measures and remediates rendered contrast |
| Post-implementation code against the plan's stated intent | `implementation-convergence` | Treats the plan as intent and reports unimplemented, partial, divergent, and unrequested code; it does not judge plan sufficiency |
| Gate criteria, thresholds, PASS/FAIL/PARTIAL behavior, escalation, and waiver mechanics | `quality-gate-definitions` | Owns gate policy; domain skills own how checks run and evidence is produced |
| Test-suite adequacy, coverage quality, pyramid balance, and maintainability | `testing-review` | Reviews the suite; does not exercise the shipped artifact or author the E2E harness |
| Fixed-width text prohibition for generated HTML | `catalog/rules/html/responsive-layout.md` | New rule owner; HTML-producing skills cite it and the hook enforces it without duplicating the policy |

The highest-risk collisions are explicitly separated: evidence freshness versus exercise procedure; code-vs-plan convergence versus Goal-vs-plan sufficiency; screenshot baselines versus geometry detection versus interface judgment; DevTools or Axe execution versus accessibility rule ownership; and gate definitions versus domain check execution.

## Deliberately not verified

The ladder does not claim exhaustive correctness. It deliberately excludes:

- Every browser, operating-system, device, locale, zoom level, and assistive-technology combination. The chosen viewport and platform matrix must be recorded; omitted environments remain outside the claim.
- Live third-party services, credentials, billing state, or production-only infrastructure that is unavailable to the local gate. Their absence is missing evidence or a remote follow-up, not a simulated pass.
- Subjective aesthetic preference beyond objective geometry, accessibility, project design rules, and an explicitly requested interface review. A detector cannot prove that a design is tasteful.
- Performance, load, soak, and resource-exhaustion guarantees unless the plan or blast radius includes those risks.
- Human learning outcomes, usability-cohort results, or organizational adoption. No agent may invent workshop participants or user feedback.
- A zero-defect guarantee. Passing the ladder proves the recorded checks against the recorded revision and environments, not every possible future input.

These boundaries make the positive claim testable: the release exercised what it built through real boundaries, recorded what it could not observe, and did not mistake green artifact checks for working behavior.

## Phase 1 acceptance review

- All four tiers state timing, required work, cost, failure meaning, and waiver authority.
- The economics show the cost difference for this five-phase plan.
- All five blast-radius triggers derive from diff evidence and ambiguity defaults to running Tier 3.
- The no-op class is narrow and leaves a durable record.
- Every historical defect named by the plan maps to a catching tier and mechanism.
- Each verification concern has exactly one owner, including the two genuinely new concerns.
- Deliberate exclusions prevent an unbounded or misleading claim.
