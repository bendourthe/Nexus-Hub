# Feature Specification: [FEATURE_NAME]

**Feature Branch**: `[NNN-feature-slug]`
**Created**: [YYYY-MM-DD]
**Status**: Draft

> User description: `$ARGUMENTS`

<!--
Section conventions:
- Mandatory sections MUST be completed for the spec to advance to /clarify-spec or /generate-plan.
- Optional sections are include-if-relevant. If a section does not apply to the feature, remove it entirely - do not leave it as "N/A".
- Use [NEEDS CLARIFICATION: <specific question>] to surface ambiguity. Hard limit: 3 markers per spec. Prioritize by scope > security/privacy > UX > technical; demote the rest to assumptions with informed defaults. See the project-constitution skill body for the full marker convention.
- Functional Requirement IDs are FR-001, FR-002, ... Success Criteria IDs are SC-001, SC-002, ... These IDs are consumed by /analyze-spec to populate the Coverage Summary table.
-->

---

## Problem Statement *(mandatory)*

<!--
This section carries forward the problem statement produced by the `idea-refine` stage. Copy and tighten that output; do not restate the problem from scratch, or the spec and the refined problem drift apart immediately.

Keep it technology-agnostic like the rest of the spec. Name the actor, the failure, and the observable outcome; never the framework, library, or service that will fix it.
-->

**Actor**: [Who has this problem? Name the role or user type rather than "the user".]

**Problem**: [What fails today, in plain language a non-technical stakeholder understands. State the current behavior and why it is inadequate.]

**Observable outcome that marks success**: [What a reader can observe once this is solved, in one sentence. This is the plain-language ancestor of the SC-### items below, not a restatement of them.]

---

## User Scenarios & Testing *(mandatory)*

<!--
User stories should be PRIORITIZED as user journeys ordered by importance. Each user story / journey must be INDEPENDENTLY TESTABLE - if you implement just ONE of them, you should still have a viable MVP. Priorities P1 / P2 / P3 / ... are assigned by user value, not by implementation order. The Independent Test paragraph is the contract: it tells the implementer what manual or automated check proves the story is delivered.
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language. Who is the actor, what are they trying to accomplish, and what observable outcome marks success?]

**Why this priority**: [Why is this P1 rather than P2 or P3? Cite the user value at stake - the journey that delivers the most value with the smallest scope is usually P1. If you mark something P1, implementing just this story must yield a viable MVP.]

**Independent Test**: [Describe the smallest end-to-end test that proves this story is delivered. The test must be runnable without implementing any other user story. Example: "Run the CLI with `--help`, verify the new command appears in the usage block and prints a non-empty description."]

**Acceptance Scenarios**:

1. **Given** [precondition], **When** [user action], **Then** [observable outcome].
2. **Given** [precondition], **When** [user action], **Then** [observable outcome].

---

### User Story 2 - [Brief Title] (Priority: P2)

[Plain-language journey.]

**Why this priority**: [...]

**Independent Test**: [...]

**Acceptance Scenarios**:

1. **Given** [...], **When** [...], **Then** [...].

---

### User Story 3 - [Brief Title] (Priority: P3)

[Plain-language journey.]

**Why this priority**: [...]

**Independent Test**: [...]

**Acceptance Scenarios**:

1. **Given** [...], **When** [...], **Then** [...].

---

### Edge Cases

- [Edge case 1: what happens when the input is empty, malformed, or at the boundary of a documented limit?]
- [Edge case 2: what happens when an upstream dependency is unreachable, slow, or returns an unexpected status?]
- [Edge case 3: what happens when two users perform conflicting actions concurrently?]

---

## Requirements *(mandatory)*

### Functional Requirements

<!--
Each requirement uses the format **FR-###**: System MUST <capability>. IDs are sequential and stable; once assigned, do not renumber on edits. The MUST modal verb is mandatory - SHOULD requirements belong in a separate sub-section or in the Assumptions block. Example NEEDS CLARIFICATION usage is shown in FR-002.
-->

- **FR-001**: System MUST [observable capability stated in user-visible terms].
- **FR-002**: System MUST [observable capability]. [NEEDS CLARIFICATION: <specific question about an unresolved constraint that materially affects the design - example: "is the per-tenant rate limit enforced at the gateway or per-service?">]
- **FR-003**: System MUST [observable capability].

### Key Entities *(include if feature involves data)*

<!--
Use this subsection only when the feature introduces or modifies data entities. List the entity name, a one-sentence description, and the key attributes that distinguish it from existing entities. Do not include database schemas, column types, or implementation details - those belong in the plan, not the spec.
-->

- **[EntityName]**: [One-sentence description.] Key attributes: [attr1, attr2, attr3].
- **[EntityName]**: [...]

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

<!--
Each success criterion uses the format **SC-###**: <measurable outcome>. Criteria MUST be Measurable (a number, a boolean, a checkable signal), Technology-agnostic (no framework / library / CLI names), User-focused (phrased in terms of user-visible effect, not internal mechanism), and Verifiable (a reader can determine pass/fail without asking the author).

Anti-patterns to avoid:
- "System is fast" - not measurable.
- "Uses Redis for caching" - not technology-agnostic; cache implementation is a plan-level decision.
- "Code is well-structured" - not user-focused.
- "Tests pass" - not specific to this feature.
-->

- **SC-001**: [Measurable outcome with explicit threshold or boolean condition. Example: "95% of `/search` requests return in under 200 ms at p95 over a 24-hour window."]
- **SC-002**: [Measurable outcome.]
- **SC-003**: [Measurable outcome.]

---

## Non-Goals *(mandatory)*

<!--
Each entry declares something the system explicitly will NOT do, and every entry MUST carry a reason. Accepted reasons: deferred to a later release, a separate initiative, not yet validated with users, too expensive for the value it would add. A Non-Goal without a reason invites the reviewer to assume you forgot the item rather than excluded it deliberately.

Boundary against Assumptions: an Assumption records a decision the reviewer can override with one line ("actually, use JWT"). A Non-Goal records scope the reviewer is being asked to confirm is excluded. If overriding the entry would change WHAT gets built rather than HOW, it belongs here. The A1 example under Assumptions below ("JWT is out of scope for this feature") is a Non-Goal wearing an Assumption's clothing; statements of that shape belong in this section.

This section is what `spec-quality-checklist.md`'s "Scope is clearly bounded" item and the `scope-guardian-reviewer` agent check against, and it is where the `idea-refine` stage's **Out of Scope** block lands.
-->

- **[Thing this feature will not do]**. Reason: [deferred to a later release, a separate initiative, not yet validated, or too expensive for the value, with the specific detail. Example: "deferred to v2; the mobile client that needs it is not yet scheduled."]
- **[Thing this feature will not do]**. Reason: [...]

---

## Invariants *(include if the change touches existing behavior)*

<!--
Each entry declares existing behavior this change must NOT break. These entries become the regression tests for the change.

Boundary against Non-Goals: a Non-Goal is something that will not be built; an Invariant is something that must not break. "We are not adding SSO" is a Non-Goal. "Existing password logins keep working" is an Invariant.

Remove this section entirely when the feature is purely additive and touches no existing behavior.
-->

- **[Existing behavior that must continue to hold]**, stated observably enough that a test can assert it.
- **[Existing behavior that must continue to hold]**, [...]

---

## Assumptions

<!--
Document the informed-default position for every candidate ambiguity that was demoted below the 3-marker hard limit. The reviewer can override any assumption with one line; an unanswered [NEEDS CLARIFICATION] marker requires full back-and-forth. Use this section liberally - explicit assumptions are cheaper to overturn than hidden ones.
-->

- **A1**: [Assumed default that the spec relies on. Example: "Authentication uses the existing session-cookie middleware; JWT is out of scope for this feature."]
- **A2**: [...]
- **A3**: [...]
