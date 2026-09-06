# Specification Quality Checklist: [FEATURE NAME]

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: [DATE]
**Feature**: [Link to spec.md]

## Content Quality

- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed (including `## Problem Statement` and `## Non-Goals`)

## Requirement Completeness

- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic (no implementation details)
- [ ] All acceptance scenarios are defined
- [ ] Edge cases are identified
- [ ] Scope is clearly bounded (the `## Non-Goals` section is present and non-empty)
- [ ] Every `## Non-Goals` entry carries a reason (deferred, separate initiative, not validated, or too expensive)
- [ ] Invariants are declared where the change touches existing behavior
- [ ] Dependencies and assumptions identified

## Feature Readiness

- [ ] All functional requirements have clear acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria
- [ ] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before /clarify-spec or /generate-plan.
- After at most 3 iteration passes, document any remaining unchecked items in the spec's `## Assumptions` section and surface them to the user before advancing.
- Each FR-### / SC-### in the spec MUST be testable; if a checklist item cannot be ticked because a requirement is inherently non-testable, rewrite the requirement (do not silently tick the item).
- This checklist is the "unit test for English" - it validates the spec's prose, not the implementation. The implementation is validated separately by tests against FR-### / SC-### IDs.
