# Decision: Validation cadence for completed plans

Status: implemented - phases use focused checks; complete plans receive long validation before publication and release
Date: 2026-10-18
Author: Ben Dourthe
Template: Nygard
Supersedes: [Non-final phase testing cadence](2026-09-23-scope-nonfinal-phase-tests-to-blast-radius.md)

## Problem

The earlier cadence reserved the full suite for the final phase, but still selected a full run when phase scope was ambiguous, repeated phase tests unconditionally, and requested another local gate during pipeline reconciliation. These execution paths allowed long validation before implementation and final corrections were finished.

During v4.14, repeated broad local qualification consumed hours while the first plan remained in stabilization. Hosted CI was already reserved for the completed plan, so moving remote validation alone would not address the repeated local work.

The maintainer requested a standard that completes each plan's implementation before the longer checks while retaining enough focused feedback to locate defects and preserving release evidence. Test selection and evidence validity need explicit rules so time savings do not become unsupported completion claims.

## Decision

Use focused tests, cheap checks and representative boundary evidence during implementation. Defer comprehensive testing and coverage collection until all implementation tasks, final refactors and known-gap corrections are complete in each plan. Validate each completed plan before its release, including every member of a minor run.

Apply the [canonical lifecycle contract](../../../policy/ci-cd-lifecycle-contract.md#24-validation-cadence-must) and the test-selection owner, [cicd-integration](../../../../catalog/skills/tests-generation/cicd-integration/SKILL.md). Inventory coverage to avoid duplicate suites, reuse unchanged terminal evidence, and rerun failed or invalidated scopes after corrections. Required full validation, platform coverage, explicit acceptance criteria, approval boundaries and green merge-result checks remain mandatory.

Existing plans retain deferred comprehensive commands under their original task IDs in phase history. The implementation driver can advance after focused proof and its local commit while those test tasks stay unchecked; the final gate must discharge them before completion. Specifically required earlier proof remains blocking.

## Alternatives considered

- **Repeat broad validation after every phase and correction.** This provides frequent broad feedback, but pays repeatedly for interfaces and integrations that later tasks still change. It does not replace the completed-plan gate.
- **Defer every check until the end of the minor.** This minimizes intermediate work, but accumulates failures across dependent plans and allows an individual release to lack its own final proof. Reject this option.
- **Use focused phase checks and comprehensive validation per completed plan.** This preserves early attribution while reducing repeated broad runs. It requires explicit scope selection and evidence invalidation; those obligations justify the retained final gate and are part of the chosen option.

## Consequences

- Intermediate phases spend less time on repeated tests, coverage collection and unnecessary local platform sweeps. No runtime reduction is promised for a plan already at its final acceptance gate.
- Cross-phase defects can surface at the final gate, where they block publication. A known failure or safety-critical prerequisite still blocks dependent implementation earlier.
- Evidence reuse requires source fingerprints, relevant dependencies and environment, terminal results, and a documented reason unaffected scopes remain valid. Combined evidence cannot be presented as a fresh unfiltered run.
- Existing recorded acceptance criteria remain binding. The running v4.14 stabilization qualification is preserved; later phases and corrections follow the new cadence without waiving its required native proof.
