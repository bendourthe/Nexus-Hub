# Python Test Maintenance & CI/CD Integration

## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/maintenance_cicd/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/maintenance_cicd/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### CI/CD Configuration
- [ ] GitHub Actions/GitLab CI pipeline configured
- [ ] Test stages defined (unit, integration, e2e)
- [ ] Parallel execution enabled
- [ ] Test result reporting set up
- [ ] Artifact storage configured

### Quality Gates
- [ ] Code coverage threshold enforced (80%+)
- [ ] Test pass rate requirement set (100%)
- [ ] Performance regression checks enabled
- [ ] Security scanning integrated
- [ ] Deployment gates configured

### Test Maintenance
- [ ] Flaky test detection implemented
- [ ] Test execution time monitoring enabled
- [ ] Obsolete test cleanup process established
- [ ] Test documentation maintained
- [ ] Test data management automated

### Pre-commit Hooks
- [ ] Code formatting checks (Black)
- [ ] Linting (flake8, pylint)
- [ ] Type checking (mypy)
- [ ] Fast test subset execution
- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Test Maintenance & CI/CD Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/maintenance_cicd"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${OUTPUT_DIR}/` prefix
- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

Please implement comprehensive test automation and maintenance infrastructure for this Python project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 mypy isort

      - name: Check formatting with Black
        run: black --check src/ tests/

      - name: Check imports with isort
        run: isort --check-only src/ tests/

      - name: Lint with flake8
        run: |
          flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

      - name: Type check with mypy
        run: mypy src/ --ignore-missing-imports

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-xdist

      - name: Run unit tests
        run: |
          pytest tests/unit/ \
            -v \
            -n auto \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=junit/test-results-${{ matrix.python-version }}.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unit-tests
          name: codecov-${{ matrix.python-version }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: junit/test-results-*.xml

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/integration/ \
            -v \
            --cov=src \
            --cov-report=xml \
            --cov-append

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: integration-tests

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety

      - name: Run Bandit security scan
        run: bandit -r src/ -f json -o ${OUTPUT_DIR}/exports/bandit-report.json || true

      - name: Check dependencies for vulnerabilities
        run: safety check --json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, security]
    steps:
      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:
  - lint
  - test
  - quality
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

before_script:
  - python -m pip install --upgrade pip
  - pip install -r requirements.txt

lint:
  stage: lint
  image: python:3.11
  script:
    - pip install black flake8 mypy isort
    - black --check src/ tests/
    - isort --check-only src/ tests/
    - flake8 src/ tests/ --max-line-length=88
    - mypy src/ --ignore-missing-imports

unit-tests:
  stage: test
  image: python:3.11
  script:
    - pip install pytest pytest-cov pytest-xdist
    - pytest tests/unit/ -v -n auto --cov=src --cov-report=xml --cov-report=term
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - coverage.xml

integration-tests:
  stage: test
  image: python:3.11
  services:
    - postgres:14
    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: postgresql://postgres:testpass@postgres:5432/testdb
  script:
    - pip install pytest pytest-cov
    - pytest tests/integration/ -v --cov=src --cov-report=xml
  artifacts:
    paths:
      - coverage.xml

quality-gate:
  stage: quality
  image: python:3.11
  script:
    - pip install coverage
    - coverage report --fail-under=80
  needs:
    - unit-tests
    - integration-tests
```

## Phase 2: Quality Gates Configuration

### Coverage Thresholds

**Configure in `pytest.ini`**:
```ini
[pytest]
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers

[coverage:run]
source = src
omit =
    */tests/*
    */test_*.py
    */__init__.py

[coverage:report]
precision = 2
skip_empty = True
fail_under = 80
show_missing = True

[coverage:html]
directory = htmlcov
```

### Test Pass Rate Gate

```python
# tests/conftest.py
"""Configure pytest with quality gates."""
import pytest

def pytest_sessionfinish(session, exitstatus):
    """Enforce 100% test pass rate."""
    if exitstatus != 0:
        print("\n❌ Quality Gate Failed: Some tests did not pass")
        print("All tests must pass before merge.")
    else:
        print("\n✅ Quality Gate Passed: All tests passed")

def pytest_terminal_summary(terminalreporter):
    """Display test summary with pass rate."""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    total = passed + failed

    if total > 0:
        pass_rate = (passed / total) * 100
        print(f"\n{'='*60}")
        print(f"Test Pass Rate: {pass_rate:.1f}% ({passed}/{total})")
        print(f"{'='*60}")

        if pass_rate < 100:
            print("⚠️  WARNING: Not all tests passed")
```

### Performance Regression Gate

```python
# tests/benchmarks/conftest.py
"""Performance regression gate."""
import pytest
import json
from pathlib import Path

BASELINE_FILE = Path("tests/benchmarks/baseline.json")
REGRESSION_THRESHOLD = 0.10  # 10% slower fails

def pytest_benchmark_compare_machine_info(config, benchmarkinfo):
    """Load baseline for comparison."""
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}

@pytest.hookimpl(hookwrapper=True)
def pytest_benchmark_scale_unit(config, unit, benchmarks, best, worst, sort):
    """Check for performance regressions."""
    yield

    if not BASELINE_FILE.exists():
        # First run - save baseline
        baseline = {bench.name: bench.stats.mean for bench in benchmarks}
        BASELINE_FILE.write_text(json.dumps(baseline, indent=2))
        return

    # Compare with baseline
    baseline = json.loads(BASELINE_FILE.read_text())
    regressions = []

    for bench in benchmarks:
        if bench.name in baseline:
            baseline_mean = baseline[bench.name]
            current_mean = bench.stats.mean
            regression = (current_mean - baseline_mean) / baseline_mean

            if regression > REGRESSION_THRESHOLD:
                regressions.append({
                    'name': bench.name,
                    'baseline': baseline_mean,
                    'current': current_mean,
                    'regression': f"{regression*100:.1f}%"
                })

    if regressions:
        print("\n❌ Performance Regression Detected:")
        for reg in regressions:
            print(f"  {reg['name']}: {reg['regression']} slower")
        pytest.fail("Performance regression gate failed")
```

## Phase 3: Pre-commit Hooks

### Install Pre-commit

```bash
pip install pre-commit
```

### Configure Pre-commit Hooks

**Create `.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=88']

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=88']

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203,W503']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--ignore-missing-imports']

  - repo: local
    hooks:
      - id: pytest-fast
        name: Run fast tests
        entry: pytest
        language: system
        pass_filenames: false
        args: ['-m', 'not slow', 'tests/unit/', '-v', '--tb=short']
        always_run: true
```

### Install Hooks

```bash
# Install the git hook scripts
pre-commit install

# Run against all files (optional)
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### Custom Pre-commit Hook for Coverage

```python
# scripts/check_coverage.py
"""Pre-commit hook to check test coverage."""
import sys
import subprocess

def main():
    """Check that coverage is above threshold."""
    result = subprocess.run(
        ['pytest', 'tests/unit/', '--cov=src', '--cov-report=term-missing', '-q'],
        capture_output=True,
        text=True
    )

    # Parse coverage from output
    for line in result.stdout.split('\n'):
        if 'TOTAL' in line:
            parts = line.split()
            coverage = int(parts[-1].rstrip('%'))

            if coverage < 80:
                print(f"❌ Coverage too low: {coverage}% (minimum: 80%)")
                return 1

            print(f"✅ Coverage: {coverage}%")
            return 0

    print("❌ Could not determine coverage")
    return 1

if __name__ == '__main__':
    sys.exit(main())
```

Add to `.pre-commit-config.yaml`:
```yaml
  - repo: local
    hooks:
      - id: check-coverage
        name: Check test coverage
        entry: python scripts/check_coverage.py
        language: system
        pass_filenames: false
        always_run: true
```

## Phase 4: Test Parallelization

### Configure pytest-xdist

```bash
pip install pytest-xdist
```

**Run tests in parallel**:
```bash
# Auto-detect CPU cores
pytest -n auto

# Specific number of workers
pytest -n 4

# Load balancing by test module
pytest -n auto --dist loadscope

# Load balancing by test file
pytest -n auto --dist loadfile
```

### Optimize for CI

```ini
# pytest.ini
[pytest]
addopts =
    -n auto
    --dist loadscope
    --maxfail=5
    --tb=short
```

### Handle Non-Thread-Safe Tests

```python
import pytest

@pytest.mark.xdist_group("serial")
def test_database_migration():
    """Tests that must run serially."""
    pass

@pytest.mark.xdist_group("serial")
def test_singleton_resource():
    """Another test in same serial group."""
    pass
```

## Phase 5: Flaky Test Management

### Detect Flaky Tests

```bash
# Run tests multiple times to detect flakiness
pip install pytest-flaky pytest-rerunfailures

# Rerun failures automatically
pytest --reruns 3 --reruns-delay 1

# Mark known flaky tests
pytest -m flaky
```

### Mark Flaky Tests

```python
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api_call():
    """Test that occasionally fails due to network."""
    response = call_external_api()
    assert response.status_code == 200

# Or use pytest-rerunfailures
@pytest.mark.flaky(reruns=3)
def test_timing_sensitive():
    """Test with timing issues."""
    result = time_sensitive_operation()
    assert result.success
```

### Track Flaky Tests

```python
# conftest.py
"""Track flaky test occurrences."""
import pytest
from collections import defaultdict

flaky_tests = defaultdict(int)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track test reruns."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and hasattr(report, 'wasxfail'):
        flaky_tests[item.nodeid] += 1

def pytest_sessionfinish(session):
    """Report flaky tests at end."""
    if flaky_tests:
        print("\n⚠️  Flaky Tests Detected:")
        for test, count in sorted(flaky_tests.items(), key=lambda x: x[1], reverse=True):
            print(f"  {test}: failed {count} times")
```

### Fix Flaky Tests

```python
# Common flaky test issues and fixes

# BAD - Time-dependent test
def test_cache_expiration():
    cache.set("key", "value", ttl=1)
    time.sleep(1.1)  # Flaky - exact timing
    assert cache.get("key") is None

# GOOD - Mock time
from unittest.mock import patch
from datetime import datetime, timedelta

def test_cache_expiration():
    with patch('myapp.cache.datetime') as mock_dt:
        start = datetime(2024, 1, 1, 12, 0, 0)
        mock_dt.now.return_value = start

        cache.set("key", "value", ttl=1)

        # Advance time
        mock_dt.now.return_value = start + timedelta(seconds=2)

        assert cache.get("key") is None

# BAD - Order-dependent test
test_results = []

def test_create_user():
    user = create_user("alice")
    test_results.append(user.id)

def test_get_user():
    # Depends on test_create_user running first!
    user_id = test_results[0]
    user = get_user(user_id)

# GOOD - Independent tests
@pytest.fixture
def created_user():
    """Each test gets its own user."""
    user = create_user("alice")
    yield user
    delete_user(user.id)

def test_get_user(created_user):
    user = get_user(created_user.id)
    assert user.username == "alice"
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```python
# conftest.py
"""Monitor slow tests."""
import pytest

SLOW_TEST_THRESHOLD = 1.0  # seconds

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track slow tests."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.duration > SLOW_TEST_THRESHOLD:
        print(f"\n⚠️  Slow test: {item.nodeid} ({report.duration:.2f}s)")

def pytest_terminal_summary(terminalreporter):
    """Report slowest tests."""
    reports = terminalreporter.stats.get('passed', [])
    reports.extend(terminalreporter.stats.get('failed', []))

    slow_tests = [
        (r.nodeid, r.duration)
        for r in reports
        if hasattr(r, 'duration') and r.duration > SLOW_TEST_THRESHOLD
    ]

    if slow_tests:
        print(f"\n{'='*60}")
        print("Slowest Tests:")
        for test, duration in sorted(slow_tests, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {duration:.2f}s: {test}")
        print(f"{'='*60}")
```

### Cleanup Obsolete Tests

```bash
# Find tests not run recently (using git)
git log --all --format=%H -- tests/ | while read commit; do
    git show $commit:tests/ --name-only
done | sort | uniq -u

# Find tests with no assertions
grep -r "def test_" tests/ | while read -r line; do
    file=$(echo $line | cut -d: -f1)
    if ! grep -q "assert" $file; then
        echo "No assertions: $file"
    fi
done
```

### Document Test Purpose

```python
"""
Test suite for user authentication.

Purpose:
    Validate user login, logout, and session management.

Coverage:
    - Valid credential login
    - Invalid credential handling
    - Session token generation and validation
    - Multi-factor authentication
    - Password reset flow

Maintenance Notes:
    - Update test_valid_login() if authentication logic changes
    - mock_email_service fixture required for password reset tests
    - Tests use in-memory database for speed

Last Review: 2024-01-15
Reviewed By: alice@example.com
"""
```

## Phase 7: Test Result Reporting

### JUnit XML Reports

```bash
# Generate JUnit XML for CI integration
pytest --junitxml=junit/test-results.xml

# With multiple test types
pytest tests/unit/ --junitxml=junit/unit-results.xml
pytest tests/integration/ --junitxml=junit/integration-results.xml
```

### HTML Reports

```bash
pip install pytest-html

pytest --html=report.html --self-contained-html
```

### Custom Test Report

```python
# conftest.py
"""Generate custom test report."""
import json
from datetime import datetime

def pytest_sessionfinish(session):
    """Generate JSON test report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total': session.testscollected,
        'passed': len(session.testscollected - session.testsfailed),
        'failed': session.testsfailed,
        'duration': session.duration,
        'tests': []
    }

    for item in session.items:
        if hasattr(item, 'report'):
            report['tests'].append({
                'name': item.nodeid,
                'outcome': item.report.outcome,
                'duration': item.report.duration
            })

    with open('test-report.json', 'w') as f:
        json.dump(report, f, indent=2)
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary
- **Platform**: [GitHub Actions/GitLab CI/Jenkins]
- **Pipeline Stages**: [list stages]
- **Parallel Execution**: [enabled/disabled, worker count]
- **Test Types Automated**: [unit, integration, e2e]
- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |

### Pre-commit Hooks Configured
- [ ] Code formatting (Black)
- [ ] Import sorting (isort)
- [ ] Linting (flake8)
- [ ] Type checking (mypy)
- [ ] Fast test execution
- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics
- **Total Tests**: [count]
- **Average Execution Time**: [duration]
- **Parallel Workers**: [count]
- **Tests per Second**: [rate]
- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │Security │
                │  Gate   │       │  Scan   │
                └─────────┘       └─────────┘
```

### Best Practices Implemented
- [ ] All tests automated in CI/CD
- [ ] Quality gates prevent regressions
- [ ] Pre-commit hooks catch issues early
- [ ] Parallel execution for speed
- [ ] Flaky tests tracked and fixed
- [ ] Test maintenance schedule established

### Next Steps
- [ ] Monitor and optimize slow tests
- [ ] Fix identified flaky tests
- [ ] Review and update obsolete tests
- [ ] Enhance test documentation
- [ ] Set up test result dashboard
- [ ] Schedule regular test maintenance reviews

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)
2. **Quality gate implementation** with thresholds
3. **Pre-commit hook configuration** with all checks
4. **Test parallelization setup** for faster execution
5. **Flaky test detection and tracking** system
6. **Test maintenance procedures** and documentation
7. **Test reporting infrastructure** with dashboards
8. **Execution metrics and monitoring** setup
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**
- [ ] All directories created successfully
- [ ] All files saved in correct subdirectories
- [ ] No files created in repository root
- [ ] Directory structure matches expected layout
