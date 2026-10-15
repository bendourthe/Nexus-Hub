---
name: test-strategy-doc
description: "Produce a complete test strategy document for a project, feature, or release with scope, risk assessment, test types, coverage targets, P0/P1 case index, tooling, schedule, and entry/exit criteria. Make sure to use this skill whenever the user mentions test strategy, test plan, testing strategy doc, QA strategy, test approach document, risk-based testing plan, test charter, or asks to write the upfront test planning artifact (not the tests themselves). SKIP: writing specific test cases (use `test-cases`), generating unit tests (use `unit-tests` or `/generate-unit-tests`), reviewing existing test coverage (use `testing-review`), setting up the test framework or harness (use `test-structure`)."
summary_l0: "Author a risk-based test strategy with scope, coverage targets, P0/P1 cases, tooling, and entry-exit criteria"
overview_l1: "This skill produces a test strategy document -- the upfront planning artifact that defines what will be tested, at what depth, with what tools, against what risk profile, and by which entry-exit criteria. It enforces risk-based prioritization (a likelihood-by-impact matrix), explicit coverage targets (numbers, not adjectives), a test-type matrix mapping each risk class to a test type, a P0/P1 test case index that traces to requirements, a test data and environment plan, and named entry and exit criteria. The output is the document a release manager reads before sign-off and a tester reads at the start of a cycle. Use it for new features, releases, audits, contractual quality reviews, or any project where 'we have tests' is not a sufficient answer. Trigger phrases: test strategy, test plan, QA strategy, test approach, risk-based testing plan."
---

# Test Strategy Document

Produce a complete test strategy document for a project, feature, or release. The strategy is the upfront planning artifact that defines what will be tested, at what depth, with what tools, against what risk profile, and by which entry-exit criteria.

The skill is opinionated on five points: testing depth is **risk-driven** (not uniform); coverage targets are **explicit numbers** (not "high" or "comprehensive"); each risk class maps to **specific test types** (not a generic "unit + integration + e2e" assumption); **P0 and P1 cases are named** and traced back to requirements; and the document has **explicit entry and exit criteria** so the team can tell when testing is done.

## When to Use This Skill

Use this skill for:

- A new feature large enough to warrant explicit test planning (multiple services touched, new data flow, new external integration, new SLAs).
- A release that requires sign-off from QA, security, compliance, or customer success before ship.
- A contractual or regulatory review where the test approach must be documented in advance (medical, financial, automotive, aviation, defense, public-sector).
- A net-new project where the test approach has not yet been established and the team needs a durable baseline.
- A risk-elevated change: a migration, a re-architecture, an algorithm replacement, a security-critical refactor.

**Trigger phrases**: "test strategy", "test plan", "testing strategy doc", "QA strategy", "test approach document", "risk-based testing plan", "test charter", "release test plan".

### When NOT to use this skill

- **Writing specific test cases** -- the individual scenarios (Given/When/Then) belong in `test-cases`. The strategy says "we will have 12 P0 integration tests covering the order-fulfillment flow"; `test-cases` writes those 12 tests.
- **Generating unit tests** -- the implementation-level tests are produced by `unit-tests` or the `/generate-unit-tests` command. The strategy sets the coverage target; those skills produce the code.
- **Reviewing existing coverage** -- if the goal is to assess what is already in place and find gaps, use `testing-review`. The strategy is forward-looking; the review is backward-looking.
- **Test framework setup** -- choosing pytest vs. vitest, configuring CI, structuring the `tests/` directory belongs in `test-structure`. The strategy says "we will use pytest + Playwright"; `test-structure` sets them up.
- **Routine sprint testing** for changes that fit the team's existing baseline. If the change is well within the existing strategy, there is nothing to plan.

## What This Skill Does

Produces a test strategy document with nine required sections.

| Section | Purpose | Required outputs |
|---|---|---|
| 1. Scope | What is in scope and what is explicitly out | In-scope features and surfaces; out-of-scope items with reason |
| 2. Risk Assessment | Likelihood-by-impact matrix per risk class | At least 5 rows; risk class, likelihood, impact, score, owner |
| 3. Test Types | Map each risk to a test type | Matrix linking risk class -> test type(s); justification per row |
| 4. Coverage Targets | Explicit, numeric coverage targets | Line / branch / functional / scenario targets per layer |
| 5. P0 / P1 Test Case Index | Named priority cases | Table mapping case ID -> requirement -> test type -> owner |
| 6. Test Data and Environments | Data strategy and environment plan | Sources, anonymization, ephemeral vs. persistent, environment list |
| 7. Tooling | Concrete tool selection | Tool per test type with version; CI integration plan |
| 8. Schedule | Test phases and milestones | Phase per milestone; entry / exit gates per phase |
| 9. Entry and Exit Criteria | When does each phase start and end | Numeric and binary criteria; sign-off owners |

## Instructions

### Step 1: Gather the Required Inputs

Before drafting, collect:

- **Scope statement** -- the feature, release, or system under test in one paragraph.
- **Requirements list** -- the source-of-truth requirements that testing will cover (PRD, RFC, ADR set, acceptance criteria, regulatory clauses). Each P0/P1 case will trace back to one of these.
- **Risk profile** -- the team's read on what could go wrong, in plain language. The strategy converts this into a structured matrix.
- **Existing test baseline** -- what tests already exist; what tools are already in use; what CI integration is already established. The strategy extends the baseline; it does not redesign it from scratch unless explicitly asked.
- **Stakeholders** -- engineering lead, QA lead, product owner, release manager, security or compliance reviewer if applicable. Each will own or sign off on parts of the strategy.
- **Schedule constraints** -- the target release date, any hard dependencies (audit deadlines, partner integration windows, regulatory submissions).
- **Budget and capacity** -- testing capacity available; test environment availability; tooling cost ceiling.

If any of these are missing, request them before drafting. A strategy written without a real risk profile or stakeholder list is a checklist, not a strategy.

### Step 2: Define the Scope

The Scope section is two parts:

**In scope**: a bulleted list of features, surfaces, integrations, data flows, and SLAs the strategy covers. Each bullet is one line, naming the surface, the change in scope, and the responsible team.

**Out of scope**: an equally explicit list of items that are NOT covered, with a reason. "Out of scope" without a reason invites reviewers to assume you forgot the item.

Example out-of-scope entry: "Multi-region failover testing is out of scope for this release. Reason: multi-region deployment is gated behind ADR-0044 (Proposed) and is not in the v1.4.0 release. Will be covered in a follow-up strategy document tied to that ADR's acceptance."

### Step 3: Build the Risk Assessment Matrix

The Risk Assessment is the spine of a risk-based strategy. It is a table with at least 5 rows and these columns:

| Risk ID | Risk class | Likelihood | Impact | Score | Owner | Notes |
|---|---|---|---|---|---|---|

- **Risk class**: a short name (e.g. "Payment processing failure under load", "Schema migration data loss", "Auth bypass in the new login flow", "Stale cache returns deleted record").
- **Likelihood**: Low / Medium / High.
- **Impact**: Low / Medium / High. Impact is customer-facing severity if the risk materializes.
- **Score**: an aggregate (e.g. Likelihood x Impact mapped to a 1-9 or Low/Medium/High/Critical scale; the team picks a scheme and uses it consistently).
- **Owner**: one person (not "the team") who owns mitigation.
- **Notes**: optional one-line clarification.

The score directly drives the Test Types section -- higher-scored risks get deeper coverage with more test types. Risks scored Low/Low may have only unit-test coverage; risks scored High/High require unit + integration + e2e + load / chaos / security depending on the class.

### Step 4: Map Risks to Test Types

The Test Types section is a matrix mapping each risk class to one or more test types. Common test types:

- **Unit tests** -- isolated function and class behavior.
- **Integration tests** -- service-to-service, service-to-dependency, contract tests.
- **E2E tests** -- user-flow tests through the full system, typically browser- or CLI-driven.
- **Performance tests** -- load, stress, spike, soak, scalability.
- **Security tests** -- SAST, DAST, dependency scan, secret scan, penetration tests.
- **Chaos / resilience tests** -- failure injection, latency injection, partition tests.
- **Accessibility tests** -- WCAG, ARIA, keyboard-only, screen-reader.
- **Compatibility / matrix tests** -- browser matrix, OS matrix, device matrix.
- **Data quality tests** -- schema validation, referential integrity, business-rule invariants.
- **Manual / exploratory tests** -- charter-driven exploratory testing for risks that resist automation.

For each risk row in the matrix, name the test types and justify the choice in one sentence. The justification answers "why this test type for this risk", not "what this test type is".

Example matrix row: "Payment processing failure under load -> unit (input validation), integration (gateway adapter), e2e (checkout flow), performance (3x peak load for 30 min). Justification: a failure in this path is customer-visible and revenue-impacting, so coverage spans correctness at the unit boundary, contract at the integration boundary, end-user behavior at the e2e boundary, and behavior under stress at the performance boundary."

### Step 5: Set Explicit Coverage Targets

Coverage targets are **numbers, not adjectives**. "High coverage" is not a target. The following targets are conventional defaults; the strategy may override any of them with a documented reason.

| Layer | Target | Notes |
|---|---|---|
| Unit line coverage | 80% minimum | 70% on legacy modules with a documented exception |
| Unit branch coverage | 70% minimum | Optional; required for security-critical modules |
| Integration coverage | All cross-service contracts covered | Listed by contract, not by percentage |
| E2E coverage | All P0 user flows + 80% of P1 user flows | Listed by flow name |
| Performance | Documented baseline for P0 paths | Latency p50/p95/p99 thresholds named |
| Security | Zero High/Critical CVEs in production dependencies | Plus zero secrets in source |
| Accessibility | WCAG 2.1 AA on customer-facing surfaces | Audit tool documented |

Each target row includes who measures it, where the measurement is reported, and what the failure response is.

### Step 6: Build the P0 / P1 Test Case Index

The P0 / P1 Test Case Index is a table of named, prioritized test cases that trace back to requirements. The strategy lists them; the cases themselves are written under `test-cases` or generated under the relevant test-generation skills.

| Case ID | Description | Priority | Requirement | Test type | Status | Owner |
|---|---|---|---|---|---|---|

- **Case ID**: a stable identifier (e.g. `TC-FULFIL-001`, `TC-AUTH-007`).
- **Description**: one line; not the full Given/When/Then.
- **Priority**: P0 (must-pass before ship), P1 (should-pass before ship), P2 (nice to have).
- **Requirement**: the requirement document and section the case verifies.
- **Test type**: unit / integration / e2e / etc.
- **Status**: Not started / Drafted / Implemented / Passing / Failing.
- **Owner**: one person.

P0 priority is reserved for cases whose failure blocks release. The strategy specifies how many P0s exist; the count itself is a quality signal (too few suggests under-specification; too many suggests the team is conflating "important" with "release-blocking").

### Step 7: Plan Test Data and Environments

Two sub-sections:

**Test data**:

- **Sources**: synthetic / production-derived / vendor-provided / fixture-based.
- **Anonymization**: if production-derived, the de-identification approach and the tool. If the data falls under GDPR / HIPAA / PCI scope, name the compliance owner.
- **Refresh cadence**: how often the test data is regenerated.
- **Volume**: enough data to exercise pagination, sorting, and edge cases without bloating the test runtime.

**Environments**:

- **Environment list**: local, CI-ephemeral, staging, performance, security, pre-production, production-canary -- name each one used and what test types run there.
- **Ephemeral vs. persistent**: is the environment torn down per test or shared across runs?
- **Capacity and isolation**: who can use which environment when; conflict resolution.
- **Cost ceiling**: testing environments are not free; the strategy states the monthly budget.

### Step 8: Specify Tooling

The Tooling section is a table of concrete tool selections with versions and CI integration notes.

| Test type | Tool | Version | CI integration | Owner |
|---|---|---|---|---|

Examples: pytest 8.x for Python unit tests; Vitest 2.x for TypeScript unit tests; Playwright 1.x for E2E; k6 for performance; Trivy or Snyk for dependency scan; axe-core for accessibility.

Do not name a tool without a version; "Playwright" without a version drifts within months. Do not name a tool without a CI integration plan; tools that only run locally are not part of the strategy.

### Step 9: Author the Schedule

The Schedule section is a phased plan with entry and exit gates per phase. A common structure:

| Phase | Window | Test types active | Entry criteria | Exit criteria | Sign-off |
|---|---|---|---|---|---|

Common phases: Unit (continuous during development), Integration (feature-branch + main), E2E (release-branch), Performance (pre-release), Security (pre-release), UAT (post-pre-release), Sign-off (release manager).

Each phase has both entry and exit criteria. The exit criterion is what flips the gate to "go" for the next phase.

### Step 10: Define Entry and Exit Criteria

This is the final section and is the single most-consulted part of the strategy in practice. Each criterion is binary and observable.

**Entry criteria for the cycle**:

- All P0 test cases are drafted and reviewed (Status >= Drafted).
- Test environment X is provisioned and reachable from CI.
- Test data set Y is loaded and validated.
- Tooling Z is installed in CI and passes a smoke test.

**Exit criteria for release**:

- All P0 test cases passing (zero failures).
- All P1 test cases either passing or with an approved waiver naming the exception, the risk, and the deadline for closure.
- Coverage targets met or with documented exception.
- Zero High/Critical security findings in production dependencies.
- Sign-off from named owners: QA lead, security reviewer (if applicable), release manager.

The exit criteria are the authoritative answer to "is the release ready". If a criterion fails, the release does not ship; the failure is logged and the decision to defer is itself documented (typically as a waiver attached to the strategy).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We have unit tests, that's the strategy" | Unit tests are one test type out of nine to twelve. A strategy that covers only unit tests leaves integration contracts, end-user flows, performance, and security uncovered. Most production incidents originate in a layer that unit tests do not exercise; a unit-only strategy is a known weak spot. |
| "QA will figure it out" | "QA will figure it out" is a hand-off, not a strategy. A test strategy aligns engineering and QA on scope, risk, depth, and exit criteria. Without it, QA is reacting to whatever code lands; with it, QA is enforcing a known coverage profile and a known release gate. |
| "We'll do exploratory testing" | Exploratory testing is a valid test type for specific risk classes (UX-heavy features, novel domains, look-and-feel quality). It is not a strategy by itself. A strategy includes exploratory testing as one type and pairs it with charters and risk classes -- not as the default for everything. |
| "Coverage targets are arbitrary" | Targets are arbitrary only if they are picked without reference to risk. Risk-based targets (80% line coverage on revenue-path code, 70% on internal tools, 95% on auth) are defensible and steer the team's effort to where it matters. The arbitrary version is "80% everywhere"; the strategy version is "80% by default, with named exceptions and named bumps". |
| "It's a small change, no strategy needed" | The strategy itself can be small. A one-page strategy for a small change is still a strategy. The trigger for skipping the document is when the change is fully covered by an existing strategy and adds no novel risk -- not when the change feels small to the author. |
| "We can write it after the implementation" | Implementation-first test strategies bias toward what is easy to test about what was built, not what is risky about what was built. The strategy is written before or during the design phase so that the risk view shapes the implementation (testable boundaries, observability hooks, contract clarity). Write it during the design; revise once if the implementation reveals a new risk; finalize before the release cycle starts. |

## Verification

Before submitting the test strategy for sign-off, walk this binary checklist. Every item must be true.

- [ ] The Scope section lists in-scope items AND out-of-scope items with reasons.
- [ ] The Risk Assessment matrix has at least 5 rows, each with a likelihood, impact, score, and named owner.
- [ ] Every risk class is mapped to one or more test types in the Test Types matrix, with a one-sentence justification.
- [ ] Coverage targets are stated as explicit numbers (not "high", "comprehensive", or "good"). At minimum: unit line coverage, integration contract coverage, E2E flow coverage, security finding threshold.
- [ ] The P0 / P1 Test Case Index has at least one row per P0 case; every row traces back to a requirement document.
- [ ] Every P0 row has a named owner (one person, not the team) and a status field.
- [ ] The Test Data section names the source, the anonymization approach (if production-derived), and the refresh cadence.
- [ ] The Environments section lists every environment used by the strategy with its purpose.
- [ ] The Tooling table names a tool, a version, and a CI integration plan for each test type that is in scope.
- [ ] The Schedule section has explicit phases with entry AND exit gates per phase.
- [ ] The Entry and Exit Criteria section is binary and observable; no soft language ("mostly", "generally", "broadly").
- [ ] Sign-off owners are named for the cycle exit criterion (QA lead, security reviewer if applicable, release manager).

If any checklist item is false, the strategy is not ready for sign-off. Iterate before circulating for review.

## Related Skills

- [[test-structure]] -- sets up the testing framework, directory layout, and CI integration. The strategy says which tools are used; [[test-structure]] sets them up.
- [[test-cases]] -- writes the individual P0/P1 scenarios named in the strategy's index. The strategy is the index; [[test-cases]] is the implementation.
- [[code-coverage]] -- analyzes existing coverage and identifies gaps. Use during cycle execution to validate that the strategy's coverage targets are actually being met.
- [[testing-review]] -- assesses the existing test suite against the strategy. Use it after the cycle to verify the strategy's exit criteria were enforced.
- [[integration-test-generator]] -- generates integration tests for the contracts named in the Test Types matrix. The strategy decides which contracts need integration tests; this skill produces them.
- [[e2e-testing-automation]] -- builds the E2E flows named in the P0 index using Playwright or Cypress with page objects and CI integration.
- [[performance-testing]] -- builds the load and stress tests required by performance risk rows in the matrix.
