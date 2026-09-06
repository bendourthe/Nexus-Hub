# Functional-Verification Deep Pass

Use this runbook for a final whole-plan Tier 3 review. It exercises every user-observable feature after all implementation phases have contributed their final shape, then audits whether the plan itself was sufficient for the Goal.

## 1. Gather the inputs

Collect these inputs before assigning a deep-pass result:

- The approved plan, including its Goal, phases, tasks, acceptance criteria, and stated exclusions.
- The maintainer's request or a durable summary that preserves requested outcomes not copied into the plan.
- The final diff against the integration base and the exact revision under review.
- Phase evidence, known gaps, generated artifacts, executable entry points, and required runtime dependencies.
- The available environments, browsers, viewports, consumers, credentials, and external services, with unavailable items named.

The plan, Goal, maintainer request, final diff, and exact revision are hard inputs. If one is unavailable, write `NOT COVERED: required deep-pass input unavailable - <input>; owner <named owner>; next step <specific retrieval or reconstruction action>`, invoke [[known-gaps-tracker]] for the incomplete scope, and give the record to [[quality-gate-definitions]] for disposition. The deep pass remains incomplete and fail-closed; do not infer the input from memory.

## 2. Evaluate objective blast radius and record the verdict

Inspect the final diff against the integration base. Select `run` when any of these diff-evidenced triggers applies:

- User-facing UI, CLI behavior, output text, hooks, interactive guides, or generated documents changed.
- Rendered or generated HTML, CSS, SVG, templates, exporters, builders, or renderer tooling changed.
- Distributed catalog content, templates, configs, installers, manifests, registries, extensions, or release workflows changed.
- Security, authentication, permissions, credentials, network egress, persistence, schemas, migrations, or validation boundaries changed.
- A public API, CLI syntax, hook payload, schema, skill or command contract, configuration key, installer destination, or compatibility promise changed.

Ambiguous classification selects `run`.

Select `no-op` only when the diff is limited to release evidence or living prose and changes no command, code block, link target, contract statement, generated output, or user workflow. Documentation under distributed skills, commands, rules, templates, or user guides is behavior and selects `run`.

For a no-op, write this record and stop the deep-pass procedure:

```markdown
### Tier 3 blast-radius verdict

- **Verdict**: no-op
- **Diff evidence**: <exact paths and change class>
- **Reason**: <why none of the five triggers applies>
- **Ambiguity check**: none; ambiguous classification changes the verdict to run
```

For `run`, record the positive triggers and continue.

## 3. Inventory every feature from every phase

Build the inventory from the full plan and final diff, not from the last phase or a remembered summary. Include every user-observable feature, distributed contract, generated artifact, and behavior produced by any phase. Include both planned task artifacts and final-diff artifacts; leave code-vs-plan classification to [[implementation-convergence]].

Use this coverage matrix:

| Feature | Source phase or task | Artifact and path | Real boundary | Representative input | Observable result | Environment | Evidence status |
|---|---|---|---|---|---|---|---|
| <feature> | <plan reference> | <type and path> | <entry point> | <input> | <value, state, interaction, or artifact> | <runtime> | pending |

Do not sample away a feature. One action may cover multiple features only when the record names and observes each result separately.

## 4. Dynamically exercise every inventory row

For each row, apply the matching artifact procedure in the parent `SKILL.md`: CLI, library or API, web UI, hook or script, document or artifact generator, configuration, or narrow documentation-only exercise. Capture one functional exercise record per independently observable feature.

Exercise the real shipped entry point with representative input. Compare the observed result with the feature's stated result, retain both values, and update the inventory row with its evidence path. A failed command, page load, consumer open, malformed-payload contract, or dependency check remains a finding rather than an omitted row.

## 5. Invoke rendered-surface delegates

Classify each visual surface before invoking rendered-surface owners:

| Surface | Intended consumer | Required rendered checks |
|---|---|---|
| Browser UI, local HTML, or generated HTML that is itself the shipped boundary | Real browser | Invoke [[browser-testing-with-devtools]], invoke [[accessibility-engineering]], run `scripts/detect_visual_defects.py` from the parent skill across the recorded viewport matrix, and invoke [[hallmark-design]]; add [[interface-review]] when the scope needs one consolidated multi-domain UI or UX verdict. |
| Non-HTML generated document or presentation such as PDF, DOCX, or PPTX | The format's intended renderer or consumer | Open the artifact through the parent skill's document or generator procedure. Invoke only delegates that declare the format in scope. Record browser testing and the HTML detector as `NOT APPLICABLE` with the format reason. |
| Non-visual generated artifact | Its intended parser or consumer | Use the parent skill's generator procedure; record the rendered-surface step as `NOT APPLICABLE` with the artifact reason. |

The detector accepts local HTML and measures browser geometry; it does not accept PDF, DOCX, PPTX, or another non-HTML format and does not replace accessibility or visual judgment. When an applicable required delegate is unavailable, record `NOT COVERED: [[owner]] unavailable - <surface and scope>` and continue the available checks. Never reconstruct the missing owner's rules or mark an applicable unavailable check as not applicable.

## 6. Invoke the adversarial pass

After baseline functional exercises, invoke [[adversarial-verifier]] against the full feature inventory. Use that skill's own attack selection, confirmation, and evidence rules. Attach its output to the affected inventory rows.

If the delegate is unavailable, record `NOT COVERED: [[adversarial-verifier]] unavailable - whole-plan hostile stress testing`. Do not invent an adjacent stress-test procedure.

## 7. Invoke code-vs-plan convergence

Invoke [[implementation-convergence]] against the approved plan and final implementation. Retain its classification of unimplemented, partial, divergent, or unrequested implementation and link each finding to the relevant inventory row.

If the delegate is unavailable, record `NOT COVERED: [[implementation-convergence]] unavailable - code-vs-plan comparison`. The next step remains the distinct plan-sufficiency audit; one cannot substitute for the other.

## 8. Audit Goal-vs-plan sufficiency

This audit owns a different question from code-vs-plan convergence: was the plan itself sufficient to reach the Goal and the maintainer's request?

Answer all four questions with evidence:

1. What did implementing this teach that the plan did not know?
2. What did the plan assume that turned out false?
3. What would a reader of the Goal expect that no phase delivered?
4. What did the maintainer ask for that no task line captured?

Record the result in this table. `None found` is acceptable only with the plan, diff, or exercise evidence that supports it.

| Question | Answer | Evidence | Change needed now | Owner |
|---|---|---|---|---|
| 1-4 | <finding or none found> | <plan line, diff path, or exercise record> | <specific correction or none> | <owner> |

Fix in-scope findings during this phase. Invoke [[known-gaps-tracker]] for residual or deferred findings so that skill owns ledger format and lifecycle rather than this runbook duplicating it.

## 9. Fix findings within one global rerun budget

Set `fix_rerun_cycles_used` to `0` before the initial deep pass. Complete Steps 1 through 8 and record the initial finding set before changing the tree whenever the remaining exercises can still run. The initial evidence-collection pass does not increment the counter because it does not change the tree. If a finding blocks completion of the initial pass, its correction starts cycle 1 and the remaining initial exercises finish inside that cycle. Every tree-changing correction caused by this deep pass consumes a cycle; there is no pre-counter repair window. Use one global maximum of three fix-and-rerun cycles across all features and delegates, not three cycles per feature, finding, or section.

For each cycle:

1. Select the in-scope findings to correct and retain their owners.
2. Apply the fixes.
3. Rerun each check that found a corrected defect and every directly impacted feature exercise.
4. Update the inventory, evidence paths, plan-sufficiency answers, and `fix_rerun_cycles_used`.

Stop when the affected checks are clean or `fix_rerun_cycles_used` reaches `3`. At exhaustion, invoke [[known-gaps-tracker]] for every remaining finding and invoke [[quality-gate-definitions]] for gate and release disposition. The finite counter applies to the whole run and prevents a finding from opening an unbounded loop.

## 10. Write the final record

Add a `## Tier 3 deep pass` section to the final evidence artifact containing:

- Exact revision and integration base.
- Blast-radius verdict, positive triggers, and diff paths.
- Feature inventory count, exercised count, and uncovered count.
- Per-feature evidence paths and observed results.
- Rendered-surface delegate outputs and detector JSON paths.
- Adversarial-verifier output.
- Implementation-convergence output.
- All four Goal-vs-plan sufficiency answers.
- `fix_rerun_cycles_used`, fixes applied, and rerun results.
- Every `NOT COVERED` item with its owning skill and scope.
- Residual known-gap references and owners.
- Environments and deliberate exclusions that bound the evidence.
- Gate disposition supplied by [[quality-gate-definitions]].

Give the record to [[verification-before-completion]] for evidence freshness and claim support. The final record reports what ran, what it observed, and what remains uncovered; it does not substitute for any delegated owner's verdict.
