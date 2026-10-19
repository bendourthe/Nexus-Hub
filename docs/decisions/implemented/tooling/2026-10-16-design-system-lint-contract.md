# Decision: Design-System Lint Contract

Status: implemented - interface-review owns existing-linter execution; no custom rule package is introduced.

UI skill maintainers and consuming-project authors use this decision when adding deterministic checks to an existing design system. It records execution ownership, policy handoffs, the reference-only scope, and the rejected custom rule package.

**Date**: 2026-10-16. **Release**: v4.14.0 Phase 4.

## Problem

The UI cluster has explicit domain owners, but its judgment checks alone do not identify mechanically disallowed token use. A second set of design rules would conflict with those owners. No active consumer requires an original rule package.

## Decision

`interface-review` owns design-system lint execution and coverage as a measurement concern. Domain owners continue to choose permitted values, exceptions, and severity. Its bundled reference supplies guidance and one adaptable existing-linter configuration. The other three affected skills hand off to that owner. Consumer adoption uses the consumer's installed dependency and existing lint task.

## Alternatives considered

Rejected alternative: build an original Nexus-Hub rule set. There is no active call site to justify a new package, runtime, or maintenance contract. Retaining judgment alone was also rejected because it supplies no repeatable failing check for mechanical violations.

## Consequences

The reference can be exercised without imposing a new repository dependency or workflow. Its CSS-only example has explicit coverage limits; components, rendered behavior, and other design concerns still require their owning checks. A future active consumer may justify a separate, scoped proposal, but this decision authorizes no theme catalog or custom rule framework.
