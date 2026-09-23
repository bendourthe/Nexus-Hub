# Decision: Test each non-final phase's blast radius and run the full suite at the final gate

Status: implemented - non-final phases run affected tests and the fast gate; the final phase owns the complete suite, coverage threshold, and cross-phase integration tests
Date: 2026-09-23
Author: Ben Dourthe
Template: Nygard

## Problem

The implementation workflow previously ran the complete repository test suite with coverage and then ran the complete suite again during post-phase verification. A six-phase plan could therefore pay for twelve full-suite runs before the final tree existed. Those runs exercised interfaces that later phases were scheduled to change, making an intermediate red result costly to interpret and an intermediate green result weaker than it appeared.

Testing only at the end would create the opposite failure: a defect introduced in an early phase would surface after several commits and documentation records had declared that phase complete. The workflow needs a phase-boundary test that is small enough to run consistently but still proves the behavior the phase changed.

This decision refines the existing [tiered functional-evidence rule](2026-08-29-require-tiered-functional-evidence-before-completion.md). That rule already requires a proportional real-boundary smoke in each phase and a whole-plan deep pass before publication; the missing detail was where the full automated suite and global coverage threshold belong.

## Decision

Each non-final phase runs the tests covering files it changed plus the repository's fast gate, writes tests for genuinely new behavior, checks for coverage regression on touched files, and exercises its feature through the proportional real boundary. Failures remain local to that phase and use its troubleshooting gate. The final phase runs the complete suite, the 80 percent coverage threshold, and cross-phase integration tests once against the completed tree, before the plan's one branch publication and protected pull-request checks.

This is a scheduling decision, not a waiver of tests. A phase with a broad blast radius selects broad affected tests; an ambiguous boundary takes the deeper path. A failed required check after publication reopens the final phase for local reproduction and repair.

## Alternatives considered

- **Run the complete suite twice in every phase.** This maximizes repeated test execution, but pays high runtime and CI-adjacent cost against known-incomplete trees. It does not replace the final integrated verdict and makes expected cross-phase churn look like a new defect.
- **Defer all automated tests to the final phase.** This is cheapest during implementation, but loses phase attribution and permits early defects to accumulate behind later commits. The final failure then has a much larger search surface.
- **Run only the fast gate in non-final phases.** This is predictable and cheap, but its generic checks may not exercise the feature just changed. A phase could pass without any test of its own behavior.

## Consequences

- Local phase feedback becomes faster and more attributable while every phase still ends with affected-test and real-boundary evidence.
- The final phase becomes the single expensive integrated gate. It can uncover cross-phase interactions that were not visible earlier, so its failure must block publication rather than be reclassified as expected churn.
- Test selection now requires judgment about the changed files' consumers. The phase record must name its chosen tests and observed result; an omitted consumer is a coverage gap, not a silent pass.

## Related

- [`require-tiered-functional-evidence-before-completion.md`](2026-08-29-require-tiered-functional-evidence-before-completion.md) - establishes proportional phase and whole-plan functional evidence
- [`implement-phase`](../../../../catalog/skills/workflow/implement-phase/SKILL.md) - owns the executable phase and final gates
