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

## Assumptions

<!--
Document the informed-default position for every candidate ambiguity that was demoted below the 3-marker hard limit. The reviewer can override any assumption with one line; an unanswered [NEEDS CLARIFICATION] marker requires full back-and-forth. Use this section liberally - explicit assumptions are cheaper to overturn than hidden ones.
-->

- **A1**: [Assumed default that the spec relies on. Example: "Authentication uses the existing session-cookie middleware; JWT is out of scope for this feature."]
- **A2**: [...]
- **A3**: [...]
