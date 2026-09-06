---
name: cicd-integration
description: Configure test automation in CI/CD pipelines with quality gates, parallel execution, and reporting. Use when setting up GitHub Actions, GitLab CI, Jenkins, Azure DevOps, or other CI/CD systems for automated testing, test parallelization, and continuous quality assurance.
summary_l0: "Configure test automation in CI/CD with quality gates and parallel execution"
overview_l1: "This skill configures test automation in CI/CD pipelines with quality gates, parallel execution, and reporting. Use it when setting up GitHub Actions, GitLab CI, Jenkins, Azure DevOps, or other CI/CD systems for automated testing, parallelizing test execution, or implementing continuous quality assurance. Key capabilities include CI/CD pipeline configuration for test execution, test parallelization across runners, quality gate enforcement (coverage thresholds, test pass rates), test result reporting and visualization, test artifact management, flaky test handling in CI, and multi-stage test pipelines (unit, integration, E2E). The expected output is CI/CD pipeline configurations with test automation, quality gates, and reporting integration. Trigger phrases: CI/CD testing, test automation pipeline, GitHub Actions tests, test parallelization, quality gates, test reporting, continuous testing."
---

# CI/CD Integration for Testing

Configure comprehensive test automation in CI/CD pipelines with quality gates, parallel execution, caching, and reporting. This skill implements **Phase 6** of the 8-phase testing methodology.

## When to Use This Skill

Use this skill when you need to:

- Set up automated testing in CI/CD
- Configure GitHub Actions for testing
- Set up GitLab CI test pipelines
- Implement quality gates
- Enable parallel test execution
- Configure test result reporting
- Set up test caching for speed

**Trigger phrases**: "CI/CD tests", "GitHub Actions tests", "automated testing pipeline", "quality gates", "test automation", "GitLab CI tests", "Jenkins testing", "parallel tests"

## What This Skill Does

### CI/CD Components

1. **Test Automation**
   - Automated test execution on the integration pull request (never on an ordinary feature-branch push)
   - Multiple test types (unit, integration, e2e)
   - Environment-specific testing

2. **Quality Gates**
   - Coverage thresholds
   - Test pass requirements
   - Linting and formatting checks

3. **Optimization**
   - Parallel test execution
   - Dependency caching
   - Test result caching

4. **Reporting**
   - Test result summaries
   - Coverage reports
   - Failure notifications

### Platform-Specific Examples

#### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

# Lifecycle contract (see [[cicd-architect]] Step 4): an ordinary feature-branch
# push runs NOTHING. The integration pull request is the one comprehensive gate,
# and it validates the synthetic MERGE RESULT. A `push` trigger on the same
# protected branches would re-run this identical tree after the merge, at full
# price, and discover nothing.
#
# Post-merge work (smoke, publication, provenance) belongs in a separate,
# minimal workflow. Release packaging belongs in a release workflow.
on:
  pull_request:
    branches: [main, develop]
  merge_group:
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  # ==================== PYTHON TESTS ====================
  python-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check .
          black --check .
          mypy src/

      - name: Run unit tests
        run: |
          pytest tests/unit -v \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=test-results/unit.xml

      - name: Run integration tests
        run: |
          pytest tests/integration -v \
            --junitxml=test-results/integration.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: true

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: test-results/

  # ==================== JAVASCRIPT TESTS ====================
  javascript-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['18', '20']

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Run type checking
        run: npm run type-check

      - name: Run unit tests
        run: npm test -- --coverage --ci

      - name: Upload coverage
        uses: codecov/codecov-action@v4

  # ==================== QUALITY GATE ====================
  quality-gate:
    needs: [python-tests, javascript-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Download all test results
        uses: actions/download-artifact@v4

      - name: Check test results
        run: |
          echo "All tests passed - quality gate check complete"

  # ==================== E2E TESTS ====================
  e2e-tests:
    needs: quality-gate
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup environment
        run: |
          cp .env.test .env
          docker-compose up -d

      - name: Wait for services
        run: |
          sleep 10
          curl --retry 10 --retry-delay 3 http://localhost:3000/health

      - name: Run E2E tests
        run: |
          npm run test:e2e

      - name: Stop services
        if: always()
        run: docker-compose down
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - quality
  - e2e

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  NPM_CONFIG_CACHE: "$CI_PROJECT_DIR/.cache/npm"

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/
    - node_modules/
    - .venv/

# ==================== LINT ====================
lint:python:
  stage: lint
  image: python:3.11
  before_script:
    - pip install ruff black mypy
  script:
    - ruff check .
    - black --check .
    - mypy src/

lint:javascript:
  stage: lint
  image: node:20
  before_script:
    - npm ci
  script:
    - npm run lint
    - npm run type-check

# ==================== TESTS ====================
test:python:
  stage: test
  image: python:3.11
  parallel:
    matrix:
      - PYTHON_VERSION: ['3.10', '3.11', '3.12']
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest tests/unit -v --cov=src --cov-report=xml --junitxml=report.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    when: always
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test:javascript:
  stage: test
  image: node:20
  before_script:
    - npm ci
  script:
    - npm test -- --ci --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

# ==================== QUALITY GATE ====================
quality:check:
  stage: quality
  needs:
    - test:python
    - test:javascript
  script:
    - echo "Quality gate passed"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# ==================== E2E ====================
e2e:tests:
  stage: e2e
  needs:
    - quality:check
  image: docker:latest
  services:
    - docker:dind
  variables:
    DOCKER_HOST: tcp://docker:2376
  before_script:
    - docker-compose up -d
    - sleep 15
  script:
    - docker-compose run app npm run test:e2e
  after_script:
    - docker-compose down
```

#### Jenkins (Jenkinsfile)

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        NODE_VERSION = '20'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint') {
            parallel {
                stage('Python Lint') {
                    agent {
                        docker { image 'python:3.11' }
                    }
                    steps {
                        sh 'pip install ruff black mypy'
                        sh 'ruff check .'
                        sh 'black --check .'
                    }
                }
                stage('JavaScript Lint') {
                    agent {
                        docker { image 'node:20' }
                    }
                    steps {
                        sh 'npm ci'
                        sh 'npm run lint'
                    }
                }
            }
        }

        stage('Test') {
            parallel {
                stage('Python Tests') {
                    agent {
                        docker { image 'python:3.11' }
                    }
                    steps {
                        sh 'pip install -e ".[dev]"'
                        sh 'pytest tests/ -v --cov=src --junitxml=results.xml'
                    }
                    post {
                        always {
                            junit 'results.xml'
                            publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                        }
                    }
                }
                stage('JavaScript Tests') {
                    agent {
                        docker { image 'node:20' }
                    }
                    steps {
                        sh 'npm ci'
                        sh 'npm test -- --ci --coverage'
                    }
                    post {
                        always {
                            junit 'junit.xml'
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def coverage = readFile('coverage.xml')
                    if (!coverage.contains('line-rate="0.8')) {
                        error "Coverage below 80% threshold"
                    }
                }
            }
        }

        stage('E2E Tests') {
            when {
                branch 'main'
            }
            steps {
                sh 'docker-compose up -d'
                sh 'sleep 15'
                sh 'npm run test:e2e'
            }
            post {
                always {
                    sh 'docker-compose down'
                }
            }
        }
    }

    post {
        failure {
            emailext subject: "Build Failed: ${env.JOB_NAME}",
                     body: "Check console output at ${env.BUILD_URL}",
                     recipientProviders: [developers()]
        }
    }
}
```

## Lifecycle Conformance (mandatory)

This skill wires a test suite, its coverage thresholds, and its quality gates into a pipeline. It does NOT define the lifecycle, the trigger topology, the runner policy, the required-check design, or the report schema. Those are owned once, by `[[cicd-architect]]`, and this skill invokes and conforms to that canonical policy rather than maintaining its own defaults.

Invoke `[[cicd-architect]]` before generating any pipeline file. Then generate thin provider orchestration over repository-native profiles, under these constraints:

1. **Call profiles; do not inline a command list.** The authoritative test commands live in the repository as the `fast`, `full`, and `platform` profiles, runnable by a developer with no CI provider present. A pipeline that re-declares them has created a second source of truth, and the two will drift silently.

2. **Match the event to the work.** Local tests run during phases. The complete remote gate runs once, when the finished branch is published for integration. Post-merge work is minimal. Scheduled extended validation runs only when it tests the tree against a world that has changed. Release packaging runs only on the release event.

3. **Ordinary feature-branch pushes run nothing.** This is the single largest cost defect in generated test pipelines, and it is worth stating plainly rather than leaving it implied by the trigger list.

4. **Parse real coverage.** A gate that echoes "passed" without reading a number cannot fail. Read the value, compare it to the documented threshold, and fail the build below it.

5. **Publish reports unconditionally.** Upload test results, coverage, and any SARIF with `if: always()` (or the provider's equivalent) and an explicit short retention period, and append the run summary to the provider's native summary surface. A red run that reports nothing is only actionable by the person who caused it.

6. **Expose exactly one aggregate required check.** It runs unconditionally and its verdict is an allowlist over dependency results. Never require a per-matrix-leg context.

7. **Cache and scope for cost.** Cache keyed to a lockfile or manifest; concurrency that cancels superseded validation; change scoping expressed as a job-level condition, never as a workflow-level path filter.

8. **Require no external reporting service.** Every artifact above is produced by the same local run a developer can reproduce.

## Prerequisites

- Tests written and passing locally
- CI/CD platform access
- Repository configuration permissions
- Understanding of deployment workflow

## Instructions

### Step 1: Choose CI/CD Platform

1. **Evaluate Options**
   - GitHub Actions (GitHub repos)
   - GitLab CI (GitLab repos)
   - Jenkins (self-hosted)
   - Azure DevOps (Microsoft ecosystem)

2. **Configure Access**
   - Repository permissions
   - Secrets management
   - Environment variables

### Step 2: Configure Test Pipeline

1. **Define Stages**
   - Lint/format checks
   - Unit tests
   - Integration tests
   - E2E tests (optional)

2. **Set Up Caching**
   - Dependencies
   - Build artifacts
   - Test results

3. **Configure Parallelization**
   - Matrix builds
   - Parallel jobs
   - Sharded tests

### Step 3: Implement Quality Gates

1. **Coverage Thresholds**
   - Minimum line coverage
   - Branch coverage
   - Per-file thresholds

2. **Test Requirements**
   - All tests must pass
   - No regressions allowed
   - Performance thresholds

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Tests pass locally, so the pipeline is just a formality." | Local runs use the developer's cached deps and OS; a missing `npm ci` lockfile or a Linux-only path bug surfaces only when the CI runner starts from a clean checkout. |
| "A quality gate that only echoes 'passed' is good enough for now." | A gate that never reads the coverage number cannot fail; a regression that drops coverage from 85% to 40% sails through a stub gate and ships untested code. |
| "Running every test serially is simpler than configuring a matrix." | Serial suites push CI feedback past 20 minutes, so developers stop waiting and merge on red; parallel matrix jobs are what keep the gate enforceable. |
| "Trigger on push and pull_request so nothing slips through." | Under a pull-request-only merge policy those are the same tree, so the push run re-validates what the pull request already proved and is billed again at full price. Worse, it is usually the run where the expensive OS legs are enabled, so the redundant run costs MORE than the useful one. |
| "Duplicating the test commands in the pipeline is clearer than calling a script." | Two lists drift, and the drift is silent in the direction that matters: a check dropped from the pipeline still passes locally, so nobody notices until it was needed. One list, called from both places. |
| "Flaky E2E tests can stay in the main pipeline; we will just re-run." | A flaky job that blocks merges trains the team to click 'retry until green', which silently masks a real intermittent failure the next time it fires. |

## Verification

- [ ] The pipeline triggers on the integration `pull_request` (plus `merge_group` where supported) and NOT on a push to the same protected branches, so the merge result is not validated twice.
- [ ] No ordinary feature-branch push starts this workflow.
- [ ] Every pipeline step calls a repository-native profile rather than declaring its own command list.
- [ ] Exactly one aggregate required check exists, it runs unconditionally, and no per-matrix-leg name is required.
- [ ] The quality-gate job reads an actual coverage value and fails the build when it is below the documented threshold.
- [ ] Test results and coverage artifacts are uploaded and visible on a failed run (`if: always()` set on upload steps).
- [ ] A deliberately failing test causes the pipeline to report a red status (gate is not a no-op).
- [ ] Dependency caching is configured so a second run is faster than a cold run.

## Related Skills

- [[test-structure]] -- sets up the test infrastructure this pipeline executes (Phase 1)
- [[code-coverage]] -- defines the coverage thresholds the quality gate enforces (Phase 7)
- [[performance-testing]] -- supplies the load tests this skill schedules in a later stage (Phase 5)
- [[cd-pipeline-generator]] -- generates the deployment stages that run after this gate is green
- [[cicd-architect]] -- the canonical lifecycle, profiles, trigger topology, required-check design, and report schema this skill conforms to; invoke it before generating any pipeline file
- [[flaky-test-detector]] -- diagnoses the intermittent failures that destabilize CI runs

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates tests_generation/maintenance_cicd/


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
