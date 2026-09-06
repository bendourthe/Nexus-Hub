---
name: architecture-decision-record
description: "Produce a single Architecture Decision Record (ADR) capturing one architecturally-significant decision, its context, the options considered, the chosen option, and the consequences. Make sure to use this skill whenever the user mentions ADR, architecture decision record, architecture decision, record this decision, document this decision, MADR, Nygard ADR, decision log, design decision writeup, or asks to capture the rationale behind a choice with long-term architectural impact. SKIP: full architecture design from scratch (use `architecture-design`), general technical documentation (use `technical-documentation`), API contract design narrower than architecture-level (use `api-design`), product or feature requirements (use `business-analyst` or `product-manager`). Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
summary_l0: "Author append-only decisions outside release-scoped documentation"
overview_l1: "This skill produces one Architecture Decision Record -- a short, durable document that captures a single architecturally-significant decision and its rationale. It supports both MADR (Markdown Any Decision Records) and Nygard templates, helps the user pick between them based on team conventions, and enforces a status lifecycle (Proposed -> Accepted -> Deprecated -> Superseded). The output documents the context that forced the decision, at least two alternatives with rejection rationale, the chosen option, the consequences (positive AND negative), the risks, and metadata (date, author, ID). It is for decisions you want a future engineer to be able to look up six months from now -- not for routine implementation choices. Trigger phrases: ADR, architecture decision record, architecture decision, MADR, Nygard ADR, decision log. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Architecture Decision Record

Produce a single Architecture Decision Record (ADR) that captures one architecturally-significant decision. The ADR is a short, immutable-once-accepted document that future engineers can read to understand why a system looks the way it does.

The skill is opinionated on five points: ADRs document **one decision per file** (not a bundle of related choices); the document captures the **context that forced the decision** (not just the chosen option); at least **two alternatives** are recorded with explicit rejection rationale; **consequences** include both positive AND negative outcomes; and the **status lifecycle** is explicit (Proposed -> Accepted -> Deprecated -> Superseded) so a reader can tell whether the record still reflects current reality.

## When to Use This Skill

Use this skill for:

- Choosing between fundamentally different architectural approaches (event-driven vs. request-response, monolith vs. service-per-domain, sync vs. async messaging).
- Picking a foundational technology with long-term lock-in (database engine, message broker, runtime platform, cloud provider, identity provider).
- Establishing a cross-cutting convention that will constrain future code (auth model, error contract, observability standard, API versioning policy).
- Recording a deliberate trade-off the team accepts (consistency vs. availability, build vs. buy, single-tenant vs. multi-tenant).
- Documenting why a previously-rejected option is now being adopted (or vice versa) -- the new ADR supersedes the older one with an explicit link.

**Trigger phrases**: "ADR", "architecture decision record", "architecture decision", "record this decision", "document this decision", "MADR", "Nygard ADR", "decision log", "design decision writeup", "capture the rationale".

### When NOT to use this skill

- **Full architecture design from scratch** -- if the user is asking for the architecture itself (component decomposition, runtime topology, data flow), use `architecture-design`. An ADR is the record of one decision within that broader design.
- **General technical documentation** -- design specs, runbooks, API references, architecture-overview documents belong in `technical-documentation`. ADRs are narrower: one decision, one document.
- **API contract design** below the architecture level -- choosing field names, pagination style, or error envelope for a specific endpoint goes through `api-design`. ADRs record the policy ("we use cursor-based pagination across all list endpoints"); api-design applies the policy to a specific endpoint.
- **Product or feature requirements** -- "should we build feature X" is a product decision; use `business-analyst` or `product-manager`. ADRs are technical decisions with long-term architectural impact, not product prioritization.
- **Routine implementation choices** -- picking a logging library, choosing tabs vs. spaces, or selecting which Python version to use in a service do not need an ADR unless they are cross-cutting at the architectural level. If a single team in one repo can revisit the choice without ripple effects, it does not need an ADR.

## What This Skill Does

Produces one ADR document in the team's preferred template format with a complete status lifecycle, an explicit alternatives section, and two-sided consequences.

### Template selection: MADR vs. Nygard

The two dominant ADR templates differ in shape and ceremony. Pick one based on team conventions; if the team has no convention, default to MADR for greenfield repos and Nygard for repos that already have a `docs/adr/` directory using Nygard format.

| Aspect | MADR (Markdown Any Decision Records) | Nygard (Michael Nygard, 2011) |
|---|---|---|
| Sections | Context and Problem Statement, Decision Drivers, Considered Options, Decision Outcome, Pros and Cons of the Options, More Information | Context, Decision, Status, Consequences |
| Length | Medium to long; per-option pros and cons explicit | Short; rationale embedded in Decision and Consequences narrative |
| Best for | Teams that want explicit option comparison, decision drivers, and a structured pros/cons table per option | Teams that want a terse, prose-driven log entry per decision |
| Filename pattern | `<NNNN>-<short-title>.md` (e.g. `0042-use-cursor-pagination.md`) | Same -- both use 4-digit ID prefix and kebab-case title |
| Tooling | `adr-tools`, `log4brains`, `madr-cli` | `adr-tools` (Nygard-compatible by default) |

The skill states the chosen template in the document's metadata block so future readers can interpret the section structure consistently.

### Repository layout and lifespan

Never release-scope an ADR. A decision can remain in force after its originating release closes, so archiving that release would archive a decision still governing the system. Recognize `docs/decisions/` alongside `docs/adr/`. When the repository mandates the Nexus-Hub decision tree, file records at `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md`, where lifecycle is `proposed`, `implemented`, or `rejected` and class is `architecture`, `policy`, `process`, or `tooling`; otherwise preserve the repository's existing ADR convention.

### Status lifecycle

Every ADR has a status field that follows a standard lifecycle:

- **Proposed** -- the decision is drafted but not yet accepted by the team. The ADR is open for discussion. PRs that depend on the decision should reference the ADR but should not merge until status is Accepted.
- **Accepted** -- the team has agreed and the decision is in force. The ADR is immutable from this point; any change is a new ADR that supersedes this one.
- **Deprecated** -- the decision is no longer in force, but no replacement has been chosen. New code should not rely on the deprecated pattern; existing code is allowed to remain until a Superseded ADR replaces it.
- **Superseded** -- the decision has been replaced by a newer ADR. The Superseded ADR must link to the replacement (`Superseded by: ADR-0073`); the replacement must link back (`Supersedes: ADR-0042`).

## Instructions

### Step 1: Confirm the decision is ADR-worthy

Before drafting, confirm the decision meets at least three of these criteria:

- The decision is **architecturally significant** -- it constrains future code, costs significant rework to reverse, or affects multiple teams or services.
- The decision involves a **deliberate trade-off** -- there were real alternatives with real downsides.
- The decision will be **looked up by a future engineer** who was not in the room -- the rationale needs to outlive the people who made it.
- The decision is **non-obvious** -- the chosen option would not be the default pick for someone reading the code cold.
- The decision is **cross-cutting** -- it affects more than one service, team, or repository.

If fewer than three criteria match, the decision is probably a tactical or implementation choice; record it in the relevant code comment or design doc instead of opening an ADR.

### Step 2: Gather the Required Inputs

Collect before writing:

- **Title** -- one short imperative phrase ("Use cursor-based pagination", "Adopt PostgreSQL as the primary OLTP store"). Filename will be `<NNNN>-<kebab-title>.md`.
- **Context** -- the situation that made the decision necessary. What problem, what constraint, what change in requirements?
- **Decision drivers** -- the forces that shaped the choice (performance, cost, regulatory, operational burden, team familiarity, vendor lock-in tolerance).
- **Considered options** -- at least two; ideally three to five. Each option has a one-paragraph description plus pros and cons.
- **Chosen option** -- which option won and why.
- **Status** -- Proposed (almost always for a brand-new ADR; team flips it to Accepted in review).
- **Consequences** -- what becomes easier, what becomes harder, what new risks appear.
- **Author and date** -- one person as author (not the team); ISO date `YYYY-MM-DD`.
- **ADR ID** -- next available 4-digit number in the team's `docs/adr/` directory.

If any of these are missing, request them before drafting. ADRs written without a real context section read as "we chose X" with no rationale a future reader can use.

### Step 3: Write the Context

The Context section answers two questions:

1. What was the situation that made this decision necessary? (A new requirement, a discovered constraint, a scaling threshold, a security finding, an incident, an architectural review.)
2. What were the forces that the decision had to balance? (Latency budgets, cost budgets, regulatory requirements, team skills, operational burden, vendor lock-in tolerance, time-to-market.)

The Context is 3-8 short paragraphs. It is descriptive, not prescriptive. A reader who is unfamiliar with the system should be able to understand why a decision was needed after reading only this section.

Common failure mode: writing the Context as a one-line "we needed to pick a database". A future reader cannot evaluate whether the decision is still valid if they do not know what forces shaped it.

### Step 4: Document at Least Two Alternatives

Every ADR has a "Considered Options" (MADR) or implicit alternatives narrative (Nygard) section. Document at least two alternatives -- ideally three to five -- with the same level of detail for each, including the one that was ultimately chosen.

For each option, capture:

- **Name** of the option (one line: technology name, pattern name, or short label).
- **Description** -- one paragraph explaining what the option entails.
- **Pros** -- 2-5 bullets, factual and specific (not "easy to use" but "team already operates two production deployments of this stack").
- **Cons** -- 2-5 bullets, factual and specific (not "complex" but "requires a separate operational runbook because failover semantics differ from the existing stack").

Symmetric treatment matters: if the rejected options have one-line pros and the chosen option has five-bullet pros, the document fails verification. Bias in option treatment is the most common ADR anti-pattern.

### Step 5: State the Decision

The Decision section is one to three short paragraphs. It states:

- **The chosen option** by name.
- **Why** -- the specific decision drivers that tipped the balance. Reference the drivers from the Context section.
- **What is explicitly NOT being decided** -- if the ADR is narrowly scoped, name the adjacent decisions that remain open so a future reader does not assume this ADR settles more than it does.

Example: "We will adopt PostgreSQL 16 as the primary OLTP store for the order, inventory, and customer services. This decision applies only to OLTP workloads; analytical workloads are explicitly out of scope and will be addressed in a separate ADR. We have not decided on the multi-region replication strategy; that decision is tracked as ADR-0044 (Proposed)."

### Step 6: Capture the Consequences (Both Sides)

The Consequences section is the single most-skipped section and the single most-valuable section to a future reader. Capture both positive and negative outcomes.

**Positive consequences** -- what becomes easier:

- New capability the chosen option unlocks.
- Reduction in operational burden, cost, or complexity.
- Better alignment with team skills or existing infrastructure.

**Negative consequences** -- what becomes harder, or what new burdens appear:

- New operational requirements (backups, replication, monitoring, runbooks the team must now own).
- New skill or training requirements.
- New failure modes or risks.
- Increased coupling to a vendor, framework, or pattern.

**Neutral consequences** -- what changes shape without being clearly better or worse:

- Migration work the team must plan.
- Existing patterns that need to be retired or wrapped.

An ADR that lists only positive consequences fails verification. The point of recording the negatives is so a future engineer who is hitting them does not assume the decision was a mistake; they can see the team chose to accept those costs explicitly.

### Step 7: Set the Status and Metadata Block

The metadata block goes at the top of the document, immediately under the title.

Example (MADR-flavored):

```
# ADR-0042: Use Cursor-Based Pagination Across All List Endpoints

- **Status**: Proposed
- **Date**: 2026-05-19
- **Authors**: @bendourthe
- **Template**: MADR
- **Supersedes**: -
- **Superseded by**: -
- **Related**: ADR-0017 (REST API conventions), ADR-0031 (gRPC streaming model)
```

Status starts at Proposed for a brand-new ADR. The team review flips it to Accepted (or rejects the ADR entirely; rejected ADRs are kept in the directory with status Rejected and a short note on why).

If the ADR is superseding an earlier decision, fill in `Supersedes`. Open the superseded ADR and add the reciprocal `Superseded by` link with the same edit so the two records stay consistent.

### Step 8: Add Risks and Open Questions (Optional but Recommended)

A short Risks section captures the known unknowns at the time of decision. Each risk has:

- A one-sentence description.
- A likelihood (Low / Medium / High).
- An impact (Low / Medium / High) -- impact if the risk materializes.
- A mitigation plan -- what the team will do if the risk turns out to be real (or a pointer to a separate document or backlog item that tracks it).

Open Questions captures items the team deliberately deferred. Each is one line; if any is critical, it becomes its own follow-up ADR.

### Step 9: File and Cross-Link the ADR

File the ADR in the detected append-only decision tree. Use `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md` when that governed layout exists; otherwise use `docs/adr/<NNNN>-<kebab-title>.md` with the next available 4-digit ID. Update the owning README index when the chosen convention uses one.

Cross-link from any relevant existing ADR. The Related field is a comma-separated list of ADR IDs with a short context phrase for each.

Open a PR for the ADR review. The PR title is the ADR title; the PR description is a 2-3 line summary plus a link to any backlog items or incidents that motivated the decision. Reviewers either approve (status flips to Accepted on merge) or request changes (the ADR is iterated in place while status remains Proposed).

### Step 10: Maintain the Lifecycle Over Time

After Acceptance the ADR is immutable. Any change is a new ADR.

When the decision is later revisited:

- If the decision is being replaced by a different choice, open a new ADR; the new one has status Proposed, the old one stays Accepted until the new one is Accepted, then both flip on merge: old -> Superseded, new -> Accepted, with reciprocal `Supersedes` / `Superseded by` links.
- If the decision is being abandoned without a replacement, the ADR moves to Deprecated. Add a one-line note explaining why and a date. New code should not rely on the pattern, but existing code is allowed to remain.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We already discussed it in the meeting, that's enough" | Meeting memory degrades within weeks. A future engineer joining the team has no access to the meeting. The cost of an ADR is one hour; the cost of relitigating the decision in three years because nobody remembers why is much higher. |
| "The PR description has the rationale" | PR descriptions are easy to find for a few months and impossible to find after the next merge into main reorders history. PR rationale is the right place for "why this implementation"; ADRs are the right place for "why this architectural choice". The two are not interchangeable. |
| "It's reversible, so no ADR needed" | The reversibility test is whether reversing the decision requires changes across more than one service / team / repo. Most "reversible" architectural choices actually cost weeks of migration work; the team will not undertake that work without re-reading the original rationale. If the decision is genuinely cheap to reverse, then yes, no ADR is needed -- but verify the cost honestly, not optimistically. |
| "We'll write it after the implementation lands" | Implementation-first ADRs read as "we did X because we did X". They do not capture the alternatives that were considered before the implementation foreclosed them. Write the ADR before or during the implementation; revise the Decision section once during implementation if the team learned something new; finalize at merge. |
| "Just record the chosen option, alternatives are noise" | The alternatives section is the highest-value section for a future engineer who is considering reopening the decision. Without it, they cannot tell whether the rejected options were rejected on principle (still valid today) or on circumstance (might be valid now). Skipping it makes the ADR much less useful in three years than it is today. |
| "Consequences are obvious from the decision" | The negative consequences in particular are rarely obvious. A team that wrote down "this means we now own backup and replication for a second database engine" is much better positioned to plan that work than a team that did not. The consequences section pays for itself the first time you reread it during a postmortem. |

## Verification

Before marking the ADR Accepted, walk this binary checklist. Every item must be true.

- [ ] The Status field is set and is one of: Proposed, Accepted, Deprecated, Superseded, Rejected.
- [ ] The Date field is set in ISO format (`YYYY-MM-DD`).
- [ ] The Author field names one person (not "the team" or "the architecture group").
- [ ] The Template field states which template format the document follows (MADR or Nygard).
- [ ] The Context section is at least 3 paragraphs and explains both the situation and the decision drivers.
- [ ] At least 2 alternative options are documented with comparable depth (each with description, pros, and cons of similar length and specificity).
- [ ] The chosen option is named explicitly and the rationale references the decision drivers from the Context section.
- [ ] The Consequences section covers both positive and negative outcomes; not only the positives.
- [ ] If the ADR supersedes an earlier one, the `Supersedes` field is set AND the superseded ADR's `Superseded by` field has been updated reciprocally.
- [ ] The ADR is in `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md` when that governed tree exists, or in the repository's inherited `docs/adr/` convention otherwise.
- [ ] The ADR is outside `docs/releases/`; archiving a release cannot hide a decision still in force.
- [ ] The selected lifecycle and class match the decision's status and concern, and the owning index is updated when the repository uses one.
- [ ] One person is identified as the author (not the team) and the same person is named in the PR.

If any checklist item is false, the ADR is not yet ready for Accepted status. Iterate on Proposed until every box is checked.

## Related Skills

- [[architecture-design]] -- the broader architecture design work that an ADR records one decision within. Use it when designing the overall system; use this skill when recording a single decision within that design.
- [[technical-documentation]] -- general design specs, architecture overviews, and reference docs. An ADR is one document type within the broader technical-documentation practice; use that skill for everything that is not strictly one-decision-per-document.
- [[api-design]] -- designing a specific API contract once the architectural policy is set. ADRs record the cross-cutting policy ("we use cursor pagination"); api-design applies the policy to a specific endpoint.
- [[ddd-strategic-design]] -- bounded contexts, aggregates, and domain events. Strategic DDD decisions are exactly the kind of architecturally-significant choice that warrants an ADR. Use the two skills together: ddd-strategic-design to do the work, this skill to record it.
- [[component-boundary-identifier]] -- module boundary analysis. The "where do we split this monolith" decision is an ADR-worthy choice; use this skill to record it once the boundary analysis is done.
