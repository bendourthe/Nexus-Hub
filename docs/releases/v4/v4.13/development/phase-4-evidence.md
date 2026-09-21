# Phase 4 Evidence -- Smallest useful visual explanation

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A4
**Phase**: 4 of 7
**Prior phase commit**: `37d15a84` (verified ancestor of HEAD)

No model was invoked. No HTML artifact was generated during verification, so no rendered-output claim is made.

## The conflict resolved

`html-output-conventions` opened with a blanket preference: "Prefer HTML over Markdown for human-facing artifacts that will actually be read." Read as written, it directs a three-row comparison into a file the reader must open.

The amendment scopes that preference to **artifacts** and adds a ladder for **answering a question in the conversation**, where the smallest representation that answers it wins. The original decision table is unchanged and still governs once the answer is genuinely an artifact; a test asserts the table and its template references survive.

| Rung | Applies when |
|---|---|
| Prose | one or two facts, no structure to show |
| Small table | a handful of items across two or three attributes |
| Pseudocode | a sequence, algorithm, or control flow |
| Mermaid | a small graph of states, steps, or dependencies |
| HTML | state, interactivity, spatial complexity, many-way comparison, or past ~100 lines |

## Scenario coverage

`tests/fixtures/agent-improvement/representation-cases.json` instantiates the plan's four required mappings plus three guards.

| Case | Request shape | Expected rung |
|---|---|---|
| REP-1 | three settings across two attributes | table |
| REP-2 | retry loop control flow | pseudocode |
| REP-3 | four-state request lifecycle | mermaid |
| REP-4 | filterable eleven-way comparison with toggles | html |

### The two near-misses

These are the cases the owners previously answered inconsistently, and they point in opposite directions:

| Case | Trap | Correct rung |
|---|---|---|
| REP-5 | the word "compare" read as an artifact trigger; two items on two attributes pushed to HTML | **table** |
| REP-6 | the ladder over-applied until an interactive state comparison collapses to a paragraph | **html** |

REP-6 exists because a ladder with only one failure direction produces the opposite defect. "Smallest useful" is not "smallest", and a reader who asked to switch between states while reading is not served by prose.

A third guard, REP-7, rejects substituting a textual responsibility list for connection topology: a list of six service names explains ownership, not how they connect, and it is no more accessible than the diagram it replaced.

## Verification run

```
$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
110 passed in 1.65s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

Warning count unchanged. The diff added zero non-ASCII lines across all changed Markdown.

### Structural checks observed

| Check | Result |
|---|---|
| Every required rung has a scenario | pass |
| No case both expects and forbids the same rung | pass |
| Both near-misses present, guarding opposite directions | pass |
| Invariants reference only real case ids | pass |
| HTML rules preserved (no color-only meaning, offline delivery, responsive, full QA) | pass |
| Original decision table and template references survive | pass |
| Communication skill does not duplicate the ladder | pass |

The self-contradiction check is a guard on the fixture rather than the product: a case declaring the same rung in `expected_rung` and `must_not_be` would be satisfiable either way and would assert nothing.

## Ownership boundary

Representation choice now has exactly one owner. `agent-communication` gained a handoff and nothing else: it governs formatting **within** a response, `html-output-conventions` governs what form the answer takes. A test asserts the ladder text does not appear in the communication skill, because a copied ladder is a second source of truth that drifts on the first edit.

`catalog/style-guides/agent-communication.md` was inspected and **left unchanged**. The plan directs editing it only if it restates the conflicting format rule; it does not. Its formatting rules concern lists, bullets, and plain prose for conversational exchanges, which is a different question from which representation carries the answer. A test asserts it stays untouched, so a later well-meaning edit that copies the ladder into it fails the suite.

## CI impact record (Phase 4)

Recorded against `[[cicd-architect]]`. No pipeline file changed; CI/CD is not this phase's deliverable.

| Dimension | This phase | Covered by existing profiles |
|---|---|---|
| New commands | none | n/a |
| New dependencies | none | yes |
| New environment variables | none | n/a |
| New test paths | none beyond the existing module | yes |
| New artifacts | none | n/a |

Nothing from this phase is carried into the terminal reconciliation.

## Phase 4 gate

| Gate element | Result |
|---|---|
| Test failures | 0 (110 passed) |
| Lint errors | 0 new |
| Build | n/a |
| Functional smoke | fixture scenarios evaluated against the owner text; ownership boundary asserted in both directions |
| Feature matches expected behavior | yes -- four required mappings plus both near-misses resolve as specified |

**Verdict: GO.**

## Limitations

- These are structural consistency checks between owners. They are **not** a measured human comprehension result, and the fixture says so in its own provenance.
- No HTML was generated or rendered in this phase, so no visual-correctness claim is made. Had any been produced, the rendered-evidence procedure would apply rather than source inspection.
