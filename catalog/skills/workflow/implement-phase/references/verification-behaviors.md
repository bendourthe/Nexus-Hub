# Verification Behaviors

**Covers**: the concrete verification behaviors that high reasoning effort tends to produce, when each applies, and which skill owns its procedure. Read at the GO/NO-GO gate (runbook Phase 7) to decide which behaviors to request for a phase.

This list names behaviors and delegates their procedures; it restates none of them. Applicability is stated by the edge-case density defined in `[[model-routing]]` `references/effort-modifiers.md`, referenced here by name.

Every request stays inside the phase's blast radius. Requesting a behavior explicitly is also how a lower-effort run gets it: when the phase's verification effort cannot be applied (no user is available to switch it, or the platform or model has no effort knob), the gate requests the matching behaviors from this list instead.

## Behaviors

| Behavior | Applies when | Owner |
|---|---|---|
| Reproduce the failure before editing, and confirm the new test fails on the unfixed code. | The phase fixes a bug in existing code from a failure report (edge-case density `high`). | `bug-reproduction-test-generator` |
| Confirm the tests fail on a deliberately half-finished fix. | Edge-case density `medium` or `high`, where a weak test could pass a partial fix. | `mutation-testing` |
| Test against a simpler reference or brute-force implementation on random inputs. | A numeric, search, parsing, or transformation algorithm with a correctness target (edge-case density `high`). | `property-based-test-generator`, `metamorphic-test-generator` |
| Time larger inputs against a stated target. | The phase states a performance target. | `performance-testing` |
| Fuzz untrusted input. | The phase parses or sanitizes untrusted input (edge-case density `high`). | `fuzzing-input-generator` |
| Review the first draft adversarially. | Edge-case density `high`, or a security or permission boundary. | `adversarial-verifier` |
| Read the source of a dependency whose behavior the fix relies on. | The fix depends on undocumented or version-specific dependency behavior. | `direct-corpus-interaction` |
| Stop and explain the difference before choosing, when two reasonable approaches give different results. | Any density, whenever two approaches disagree. | The gate itself: record both results and the explanation in the phase history. |

Exercising the phase's feature through its real boundary is gate 5 of GO/NO-GO, owned by `functional-verification`. This list does not request it a second time.

## Missing owner

If an owner named above is unavailable in the installed catalog, mark that behavior not covered in the phase history, name the missing skill, and continue. Never reconstruct its procedure from memory or substitute a neighboring skill.
