---
name: functional-verification
description: Exercise built artifacts. Use for "did you actually test it", "verify this works", "check the feature runs", "does the UI actually render", or "exercise the feature". SKIP writing unit tests, accessibility audits, visual-design reviews.
summary_l0: "Exercise built artifacts through real boundaries and record observable behavioral evidence"
overview_l1: "Exercise shipped behavior through the artifact's real boundary and capture output as well as execution. Select a proportional path for CLI, library or API, web UI, hook or script, generator, configuration, or narrow documentation changes. For a final whole-plan review, follow references/deep-pass.md to inventory every feature, invoke domain delegates, audit Goal-vs-plan sufficiency, and bound fixes to three rerun cycles. This skill owns exercise procedure and the plan-sufficiency audit; adjacent skills own evidence freshness, gate policy, accessibility, visual judgment, browser diagnosis, E2E architecture, adversarial rules, code-vs-plan convergence, and gap records."
---

# Functional Verification

Exercise the thing that was built through the boundary its user or consumer reaches. A green build proves that an artifact can be produced; functional verification records what the artifact actually did.

## When to Use This Skill

Use this skill when:

- A phase needs a proportional functional smoke of its changed feature.
- A completion review needs observed behavior in addition to tests, lint, build, or file checks.
- A CLI, API, browser view, hook, script, generator, configuration, or documentation workflow must be exercised through its real entry point.
- A final whole-plan review must exercise every feature and audit whether the plan was sufficient for the Goal.

**When NOT to use:**

- Writing or expanding unit tests belongs to [[unit-tests]].
- Auditing accessibility requirements belongs to [[accessibility-engineering]].
- Judging visual design belongs to [[hallmark-design]].
- Designing a durable browser regression suite belongs to [[e2e-testing-automation]].
- Deciding whether evidence is fresh enough for a completion claim belongs to [[verification-before-completion]].

## Instructions

### 1. Identify the artifact and real boundary

Record the feature, exact revision, changed paths, artifact type, intended consumer, real entry point, representative input, expected observable contract, and actual observable result. Choose the boundary the consumer reaches, not an internal helper that bypasses integration.

Use one artifact type as the primary path. Add another path only when the feature crosses multiple independently observable boundaries.

### 2. Choose the proportional exercise

For a phase smoke, exercise the changed feature once through its primary real boundary with representative input and capture output as well as execution. Keep the exercise scoped to the phase.

For a final whole-plan review, load `references/deep-pass.md` and follow it in order. That reference owns the blast-radius decision, every-feature inventory, rendered delegates, adversarial handoff, implementation-convergence handoff, Goal-vs-plan sufficiency audit, and global rerun budget.

### 3. Exercise by artifact type

| Artifact | Action | Evidence that counts | Evidence that does not count |
|---|---|---|---|
| CLI | Run one real command with representative arguments through the shipped entry point. | Command, arguments, exit code, and the expected stdout or stderr fragment or created artifact. | Parsing the command, opening help, or recording exit code alone. |
| Library or API | Call one public boundary with representative input and observe the consumer-visible result. | Returned value or response plus status, persisted state, emitted event, or another observable side effect. | An isolated unit mock or a direct call to a private helper that bypasses the public boundary. |
| Web UI | Render the affected view in a real browser runtime, perform its primary interaction, observe the result and runtime verdict, then run the visual detector. | Loaded page, interaction input and result, console or runtime result, detector JSON, and detector exit code. | Source inspection, a build result, or an old screenshot without a current interaction and geometry result. |
| Hook or script | Fire a representative valid payload and a malformed payload through the real executable entry point. | Inputs, exit codes, stdout and stderr contract, and the intended allow or block behavior. | A parse check or source review without invoking the entry point. |
| Document or artifact generator | Generate a representative output, open or parse it with the intended consumer, and assert one meaningful content result. | Generator command, output path, consumer-load result, and a content assertion. | File existence or byte size alone. |
| Configuration | Apply the change to the real loader or a faithful scratch install, then trigger the behavior it controls. | Parsed effective value and the observed behavior change at the consuming boundary. | Reading the edited text or validating syntax without loading it. |
| Narrow documentation-only change | Run the repository's Markdown, link, and Unicode checks, then record the exact diff paths and why no runnable feature, command, code block, link target, contract, generated output, or workflow changed. | Passing static checks plus a durable no-runnable-change record tied to the diff. | A silent skip, prose inspection alone, or applying this path to distributed skills, commands, rules, templates, or user guides. |

For a web UI, replace `path/to/page.html` with the affected local HTML path and run the detector from this skill directory:

```bash
python scripts/detect_visual_defects.py path/to/page.html --viewports 420 900 1440
```

When the affected view is hash-routed, add its validated route name so the detector measures that view instead of the default page: `python scripts/detect_visual_defects.py path/to/page.html --fragment foundations --viewports 420 900 1440`.

Exit `0` with JSON `status` equal to `pass` is a clean geometry result. Exit `1` reports rendered findings, exit `2` reports invalid input, and exit `3` reports an unavailable renderer with an installation hint. Preserve stdout as the JSON artifact and stderr as the readable diagnostic; a nonzero cannot-run result is evidence of missing coverage, not a clean result.

### 4. Invoke adjacent owners without copying their rules

| Concern | Owner and handoff |
|---|---|
| Evidence freshness and support for a completion claim | Give the exercise record to [[verification-before-completion]] for the claim decision. |
| Gate thresholds, severity, escalation, and waivers | Give findings and cannot-run states to [[quality-gate-definitions]] for disposition. |
| Accessibility requirements and severity | Invoke [[accessibility-engineering]] for an accessibility audit. |
| Visual judgment | Invoke [[hallmark-design]] for design judgment and [[interface-review]] when a consolidated multi-domain interface verdict is required. |
| Browser runtime diagnosis | Invoke [[browser-testing-with-devtools]] for console, network, storage, and runtime diagnosis. |
| Browser regression architecture | Invoke [[e2e-testing-automation]] when the result must become a durable automated suite. |
| Hostile stress testing | Invoke [[adversarial-verifier]] after the baseline exercise. |
| Code against the plan's stated intent | Invoke [[implementation-convergence]]. |
| Known-gap ledger behavior | Invoke [[known-gaps-tracker]] for residual or unavailable coverage. |

When a required owner is unavailable, write `NOT COVERED: [[owner]] unavailable - <scope>` in the record and continue the coverage that remains possible. Keep the missing portion visible; never reconstruct the absent owner's rules from memory or substitute a neighboring skill.

### 5. Record the observation

Write one record per independently observable feature:

```markdown
### Functional exercise - <feature>

- **Revision**: <exact revision>
- **Artifact and boundary**: <type, path, and real entry point>
- **Command or action**: <exact command or interaction>
- **Input**: <representative input or payload>
- **Expected contract**: <expected exit, value, text, response, state, interaction, or measurement>
- **Exit code or measurement**: <number and unit>
- **Observed output or state**: <specific value, text, response, state, or interaction result>
- **Comparison**: <matches, mismatch, or cannot-run, with the compared values>
- **Environment**: <runtime, browser, viewport, or consumer>
- **Evidence paths**: <logs, JSON, screenshots, or generated artifacts>
- **Delegates**: <owners invoked and their result locations>
- **NOT COVERED**: <unavailable scope and owner, or none>
```

Capture the actual result even when it differs from the expected result. A mismatch, failed load, missing runtime, malformed output, or unavailable dependency remains a finding and must stay in the record for `[[quality-gate-definitions]]` to disposition; it cannot satisfy the exercise merely because an exit code and output were recorded.

### 6. Rerun the affected behavior after a fix

After a functional finding is fixed, rerun the exercise that found it and any directly impacted feature boundary. Follow the active plan or gate's iteration budget. Append the new result with its revision or replace the draft record while preserving the final evidence artifact required by the phase.

### 7. Hand off the evidence

Pass the completed record to [[verification-before-completion]] for evidence-to-claim matching and to [[quality-gate-definitions]] for gate disposition. Functional verification produces the observation; it does not declare evidence fresh, define a waiver, or redesign another owner's test discipline.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The tests pass" | Four green artifact gates certified a layout with rendered defects because none exercised the changed page. Run the artifact through its real boundary and record the observed result. |
| "The screenshots looked fine" | A command chip narrower than its label shipped after screenshot inspection. Measure current rendered geometry with `scripts/detect_visual_defects.py` and retain its JSON result. |
| "I checked it earlier" | A contrast token regressed as soon as a new component used it. Exercise the final changed artifact, then give the record to [[verification-before-completion]] for the freshness decision. |
| "It is a small change" | A trailing newline blocked a pull request despite the change appearing trivial. Choose the smallest real-boundary exercise, but still run it and capture a binary result. |

## Verification

- [ ] Every changed feature in scope has a named artifact type, consumer, and real entry point.
- [ ] Every exercise record contains the exact revision, representative input, command or action, expected contract, exit code or measurement, observed output or state, and explicit comparison result.
- [ ] Every mismatch or cannot-run result remains a finding handed to `[[quality-gate-definitions]]`; no record passes solely because execution and output were captured.
- [ ] CLI evidence includes output or an artifact in addition to the exit code.
- [ ] Library or API evidence crosses a public boundary and records the consumer-visible result.
- [ ] Web UI evidence includes a current interaction result and the JSON plus exit code from `scripts/detect_visual_defects.py`.
- [ ] Hook or script evidence includes valid and malformed payloads with observed allow or block behavior.
- [ ] Generated output was opened or parsed by its intended consumer and has a content assertion.
- [ ] Configuration evidence includes the parsed effective value and observed consuming behavior.
- [ ] A narrow documentation-only record names exact diff paths and proves that no runnable or distributed behavior changed.
- [ ] Every unavailable delegate appears as `NOT COVERED` with the owning skill and affected scope.
- [ ] A final whole-plan review followed `references/deep-pass.md`, answered all four plan-sufficiency questions, and recorded the global fix-and-rerun count.
- [ ] The evidence record contains no subjective substitute such as "looks right" in place of an artifact, exit code, value, or measured number.

## Related Skills

- [[verification-before-completion]] - owns evidence freshness and whether an observation supports a completion claim.
- [[quality-gate-definitions]] - owns gate criteria, severity, escalation, and waiver mechanics.
- [[unit-tests]] - owns isolated unit-test design and implementation.
- [[accessibility-engineering]] - owns accessible interaction requirements and severity.
- [[hallmark-design]] - owns visual-design judgment for the AI-generated look.
- [[interface-review]] - owns consolidated multi-domain interface review.
- [[browser-testing-with-devtools]] - owns development-time browser observation and diagnosis.
- [[e2e-testing-automation]] - owns durable automated browser regression architecture.
- [[adversarial-verifier]] - owns hostile stress testing and confirmation of adversarial findings.
- [[implementation-convergence]] - owns comparison of implementation to the plan's stated intent.
- [[known-gaps-tracker]] - owns the release-scoped ledger for unresolved or unavailable coverage.
