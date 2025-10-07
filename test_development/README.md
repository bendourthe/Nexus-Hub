# Test Development Templates

Stand up reliable, automated test suites with clear prompts for every phase—from initial structure to CI/CD integration and coverage enforcement.

---

## Quick navigation
- [Start here](#start-here)
- [Phase overview](#phase-overview)
- [Build paths](#build-paths)
- [Phase details](#phase-details)
- [Toolkit & automations](#toolkit--automations)
- [Sustaining quality](#sustaining-quality)
- [Support](#support)

---

## Start here
1. Open the language folder you need (Python today) and copy the prompt for the target phase.
2. Gather project context—architecture, dependencies, existing tests—before running the prompt.
3. Paste the prompt into your AI assistant, generate the draft suite or artifact, and adapt it to your tooling.
4. Run the tests, capture coverage, and commit only once the suite is green.

**Tip:** Nail infrastructure (Phase 1) before writing cases—clean structure keeps future phases fast.

---

## Phase overview
| Phase | Focus | Primary outcome | Prompt |
| --- | --- | --- | --- |
| 1 | Test structure | Project-ready folders, runners, and utilities | [Python](test_structure/python_test_structure.md) |
| 2 | Test cases | Unit, integration, and edge-case coverage with AAA patterns | [Python](test_cases/python_test_cases.md) |
| 3 | Mocks & fixtures | Reusable data builders, dependency isolation, and cleanup | [Python](mocks_fixtures/python_mocks_fixtures.md) |
| 4 | Performance testing | Load, stress, and benchmark suites with acceptance thresholds | [Python](performance_testing/python_performance_testing.md) |
| 5 | Maintenance & CI/CD | Automated pipelines, flaky-test triage, and reporting | [Python](maintenance_cicd/python_maintenance_cicd.md) |
| 6 | Code coverage | Measurement, gap analysis, and enforcement strategy | [Python](code_coverage/python_code_coverage.md) |

---

## Build paths
| Scenario | Run these phases | Time estimate |
| --- | --- | --- |
| ⚡ Quick smoke safety net | 1 → 2 (critical paths only) | ~2–3 h |
| 🎯 Feature-complete module | 1 → 2 → 3 → 6 | ~5–8 h |
| 🧪 Production-grade release | 1 → 2 → 3 → 4 → 5 → 6 | ~10–14 h |

*Revisit Phase 5 after every major suite addition so CI/CD stays healthy.*

---

## Phase details

### Phase 1 – Test structure
- Lay out `/tests`, shared utilities, and configuration files (pytest.ini, run_all_tests.py).
- Provide base classes, assertion helpers, and test discovery hooks.
- Ensure repeatable local runs with environment setup notes.
- **Python project:** [Test structure prompt template](test_structure/python_test_structure.md)

### Phase 2 – Test cases
- Cover happy paths, edge cases, and error handling using Arrange-Act-Assert.
- Add integration checks for service boundaries and regression tests for fixed bugs.
- Tag slow or flaky suites so CI pipelines can segment runs.
- **Python project:** [Test cases prompt template](test_cases/python_test_cases.md)

### Phase 3 – Mocks & fixtures
- Create fixtures for databases, APIs, and filesystem interactions with automatic teardown.
- Use factories/builders for deterministic test data.
- Centralize monkeypatching/mocking patterns to keep tests declarative.
- **Python project:** [Mocks & fixtures prompt template](mocks_fixtures/python_mocks_fixtures.md)

### Phase 4 – Performance testing
- Define target latency, throughput, and resource budgets before executing.
- Generate load/stress scenarios plus benchmark harnesses with percentile reporting.
- Record baselines and compare future runs automatically.
- **Python project:** [Performance testing prompt template](performance_testing/python_performance_testing.md)

### Phase 5 – Maintenance & CI/CD
- Wire suites into CI/CD (GitHub Actions, Jenkins, etc.) with parallelism and caching.
- Capture flaky test telemetry, quarantine failures, and escalate owners.
- Publish structured reports (HTML, JUnit XML, coverage badges) for visibility.
- **Python project:** [Maintenance & CI/CD prompt template](maintenance_cicd/python_maintenance_cicd.md)

### Phase 6 – Code coverage
- Measure line/branch coverage and map gaps to missing scenarios.
- Enforce thresholds (80%+ recommended) with pre-commit hooks or CI fails.
- Prioritize risk-based backlogs to raise coverage without busywork.
- **Python project:** [Code coverage prompt template](code_coverage/python_code_coverage.md)

---

## Toolkit & automations
- **Frameworks:** pytest, unittest, nose2 — pair with `pytest-cov` or `coverage.py`.
- **Mocking:** `unittest.mock`, `pytest-mock`, `responses`, `freezegun`.
- **Performance:** `pytest-benchmark`, `locust`, `k6`.
- **CI templates:** GitHub Actions workflows, Jenkins pipelines, GitLab CI YAML samples included in Phase 5 prompt.
- **Utilities:** Use provided `TestResultAggregator`, `PerformanceTimer`, and flaky detection hooks to standardize output.

---

## Sustaining quality
- Add test updates to definition-of-done; every feature needs coverage + fixtures.
- Fail the build on flaky retries after a small threshold—treat them as bugs.
- Review coverage deltas in PRs and track debt items in the testing backlog.
- Run performance suites on a schedule (nightly/weekly) to catch regressions early.

**Readiness gate:** Suite passes locally, CI green, coverage ≥ target, and no quarantined tests remaining.

---

## Support
- Browse the [repository root](../README.md) for cross-discipline templates.
- Need documentation workflows? Jump to the [documentation templates](../documentation/README.md).
- Share improvements or issues with your QA/automation lead so templates keep evolving.

*Last updated: October 2025*  
*Current templates: Python (6 phases complete)*
