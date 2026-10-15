---
name: test-suite-prioritizer
description: Order and prioritize test suites for faster CI feedback using failure history analysis, code change correlation, coverage-based prioritization, risk-based ordering, and test selection strategies. Use when CI pipelines are slow, you need faster feedback loops, or you want to run the most important tests first.
summary_l0: "Prioritize test suites for faster CI feedback with failure history and risk analysis"
overview_l1: "This skill orders and prioritizes test suites for faster CI feedback using failure history analysis, code change correlation, coverage-based prioritization, risk-based ordering, and test selection strategies. Use it when CI pipelines are slow, you need faster feedback loops, or you want to run the most important tests first. Key capabilities include failure history analysis for predictive ordering, code change correlation to run affected tests first, coverage-based prioritization for maximum impact, risk-based ordering for critical path testing, test selection to skip unaffected tests, execution time optimization, and CI pipeline integration for dynamic test ordering. The expected output is a prioritized test execution order with rationale, estimated time savings, and CI configuration. Trigger phrases: test prioritization, slow CI, faster feedback, test ordering, test selection, important tests first, CI optimization, failure prediction, risk-based testing."
---

# Test Suite Prioritizer

Order and prioritize test execution to deliver faster CI feedback by running the tests most likely to fail first. This skill applies failure history analysis, code change correlation, coverage-based prioritization, and risk-based ordering to reduce the time between code commit and actionable test results, often by 50-80%.

## When to Use This Skill

Use this skill when you need to:

- Reduce CI feedback time by running high-value tests first
- Implement test selection to skip tests unrelated to the current code change
- Prioritize tests based on failure history (tests that failed recently run first)
- Correlate code changes with the tests most likely to catch regressions
- Apply risk-based ordering where tests covering critical business logic run before tests covering cosmetic features
- Implement tiered test execution (fast smoke tests, then unit tests, then integration tests)
- Optimize parallel test distribution across CI runners
- Reduce CI costs by avoiding unnecessary full-suite runs

**Trigger phrases**: "prioritize tests", "test ordering", "faster CI", "test selection", "skip unrelated tests", "failure-based ordering", "risk-based testing", "CI optimization", "test parallelization", "smoke tests first", "test impact analysis"

## What This Skill Does

### Prioritization Strategies

#### 1. Failure History Prioritization

Tests that failed recently are more likely to fail again. Ordering tests by their recent failure rate provides the fastest feedback for regressions.

**Signal**: Failure count in the last N runs, time since last failure, failure rate trend

#### 2. Code Change Correlation (Test Impact Analysis)

Analyze which tests cover the files that changed in the current commit. Run only those tests, or run them first.

**Signal**: Coverage data mapping files to tests, dependency graph analysis

#### 3. Coverage-Based Prioritization

Tests that cover more unique code paths provide more value per execution second. Prioritize tests that maximize cumulative coverage.

**Signal**: Line/branch coverage per test, unique coverage contribution

#### 4. Risk-Based Ordering

Assign risk scores to code modules based on business criticality, defect density, and change frequency. Run tests covering high-risk modules first.

**Signal**: Business criticality labels, historical defect counts, code churn metrics

#### 5. Execution Time Optimization

Short tests provide faster feedback than long tests. Run the fastest tests first to catch obvious regressions within seconds.

**Signal**: Historical execution time per test

#### 6. Tiered Execution

Structure the test suite into tiers that run sequentially, with each tier providing progressively deeper coverage:

| Tier | Tests | Target Time | Purpose |
|---|---|---|---|
| 0 | Lint, type check | < 30 seconds | Catch syntax and type errors |
| 1 | Smoke tests | < 2 minutes | Verify critical paths work at all |
| 2 | Unit tests | < 5 minutes | Verify function-level correctness |
| 3 | Integration tests | < 15 minutes | Verify component interactions |
| 4 | E2E tests | < 30 minutes | Verify full user workflows |

## Instructions

### Step 1: Implement Failure History Prioritization

Full walkthrough: [step-1-implement-failure-history-prioritization.md](references/step-1-implement-failure-history-prioritization.md) (load this step when you reach it).

### Step 2: Implement Test Impact Analysis (Code Change Correlation)

Full walkthrough: [step-2-implement-test-impact-analysis-code-change-correlation.md](references/step-2-implement-test-impact-analysis-code-change-correlation.md) (load this step when you reach it).

### Step 3: Implement Coverage-Based Prioritization

Full walkthrough: [step-3-implement-coverage-based-prioritization.md](references/step-3-implement-coverage-based-prioritization.md) (load this step when you reach it).

### Step 4: Implement Risk-Based Ordering

Full walkthrough: [step-4-implement-risk-based-ordering.md](references/step-4-implement-risk-based-ordering.md) (load this step when you reach it).

### Step 5: Implement Tiered Test Execution in CI

Full walkthrough: [step-5-implement-tiered-test-execution-in-ci.md](references/step-5-implement-tiered-test-execution-in-ci.md) (load this step when you reach it).

### Step 6: Combine Multiple Prioritization Strategies

Full walkthrough: [step-6-combine-multiple-prioritization-strategies.md](references/step-6-combine-multiple-prioritization-strategies.md) (load this step when you reach it).

## Best Practices

- **Start with failure history prioritization**: It is the simplest to implement and provides the largest feedback time reduction; most CI systems already have test result data available
- **Build and update the coverage map regularly**: Run a full test suite with coverage weekly or on the main branch to keep the test-to-file mapping current
- **Fail fast with tiered execution**: Configure CI so that if tier 1 (smoke) fails, tiers 2-4 are skipped entirely; this saves the most time and money
- **Use test impact analysis for large monorepos**: In repositories with thousands of tests, running only the impacted subset can reduce CI time from 30 minutes to 3 minutes
- **Combine strategies with weighted scores**: No single strategy is optimal; a composite approach that weighs failure history, risk, coverage, and speed together produces the best ordering
- **Track metrics over time**: Measure "time to first failure" and "total CI time" before and after implementing prioritization to quantify the improvement
- **Maintain a safety net**: Periodically run the full test suite (e.g., nightly) to catch issues that test selection might miss
- **Distribute tests across parallel runners efficiently**: When using multiple CI runners, assign tests so that each runner has approximately equal total execution time

## Common Pitfalls

- **Optimizing test order without fixing slow tests**: Prioritization makes slow suites faster to produce feedback, but the total execution time remains the same; also invest in making individual tests faster
- **Relying solely on test selection**: Skipping tests based on code change analysis can miss indirect dependencies (e.g., a configuration change that affects all modules); always run the full suite periodically
- **Stale coverage maps**: A coverage map from last month may not reflect recent code changes; update it at least weekly
- **Ignoring flaky tests in failure history**: A test that fails due to flakiness (not real regressions) will be prioritized highly, wasting the benefit of failure-based ordering; fix flaky tests first (see the flaky-test-detector skill)
- **Over-partitioning into too many tiers**: Three to five tiers is sufficient; more tiers add complexity without proportional benefit
- **Not measuring the impact**: Implementing prioritization without measuring before/after metrics makes it impossible to justify the investment or identify regressions in the approach
- **Treating all tests as equal in parallel distribution**: Assigning tests round-robin to parallel runners ignores execution time differences; one runner may finish in 1 minute while another takes 10 minutes; use time-balanced distribution
- **Skipping integration tests too aggressively**: Unit tests passing does not guarantee integration correctness; always run at least a smoke-level integration test on every commit

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We will just buy more CI runners instead of prioritizing." | Throwing hardware at a 30-minute suite shortens wall-clock time but not time-to-first-failure; a developer still waits minutes to learn their one-line change broke a test that could have run first. |
| "Test selection lets us skip everything the diff did not touch." | Change-impact analysis misses indirect dependencies such as a config or shared-fixture change that affects every module; without a periodic full run, a real regression escapes the selected subset. |
| "Failure history ordering will surface our worst tests first." | If flaky tests dominate the failure history they get prioritized highest and waste the feedback budget on noise; flaky tests must be fixed before failure-based ordering pays off. |
| "Round-robin distribution balances the parallel runners." | Round-robin ignores per-test duration, so one runner finishes in a minute while another takes ten; only time-balanced assignment actually shortens the critical path. |

## Verification

- [ ] The prioritized ordering is derived from recorded failure history and/or change correlation, not an arbitrary list.
- [ ] A tiered CI config fails fast: a tier-1 (smoke) failure skips the later tiers.
- [ ] The coverage/test-impact map has been refreshed within the documented staleness window.
- [ ] The full suite still runs on a periodic schedule (e.g. nightly) as a safety net.
- [ ] Before/after metrics for time-to-first-failure and total CI time are recorded to quantify the gain.

## Related Skills

- [[flaky-test-detector]] -- fixes the flaky tests that otherwise poison failure-history prioritization
- [[cicd-integration]] -- the pipeline this ordering and tiering is wired into
- [[code-coverage]] -- supplies the test-to-file map that drives coverage-based and impact-based selection
- [[test-strategy-doc]] -- defines the risk weighting that risk-based ordering applies
- [[performance-testing]] -- profiles slow tests so prioritization is paired with actually making them faster
