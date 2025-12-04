---
template_id: python_code_coverage
template_name: Code Coverage - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: test_development
phase: code_coverage
phase_number: 6
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:
  - test_development/performance_testing/python_performance_testing.md
related_templates:
  - test_development/maintenance_cicd/python_maintenance_cicd.md
tools:
  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:
  - test-development
  - python
---
# Python Code Coverage Analysis

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                          ► │ ● CURRENT
│ Phase 7: Maintenance & CI/CD                       ► │ [NEXT]
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 5 (Performance Testing) should be completed first
**Next Step:** Phase 7 (Maintenance & CI/CD)

---


## Objective
Implement comprehensive code coverage measurement, analyze coverage gaps, establish coverage goals, create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage (80%+ target).

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/code_coverage/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/code_coverage/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Coverage Setup

- [ ] Coverage.py installed and configured

- [ ] pytest-cov integration enabled

- [ ] Coverage configuration file created

- [ ] HTML report generation configured

- [ ] CI/CD coverage reporting set up

### Coverage Analysis

- [ ] Current coverage baseline measured

- [ ] Coverage gaps identified and prioritized

- [ ] Critical paths coverage verified

- [ ] Edge cases coverage assessed

- [ ] Untested code documented

### Coverage Goals

- [ ] Target coverage defined (80%+ recommended)

- [ ] Coverage thresholds set by module

- [ ] Critical path coverage requirements established

- [ ] Coverage improvement plan created

- [ ] Timeline for improvements defined

### Coverage Integration

- [ ] Coverage gates in CI/CD configured

- [ ] Coverage reports automated

- [ ] Coverage trends tracked

- [ ] Coverage regression prevention enabled

- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Code Coverage Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/code_coverage"
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

Please implement comprehensive code coverage measurement and improvement for this Python project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Coverage Setup and Configuration

### Install Coverage Tools

```bash
pip install coverage pytest-cov
```

### Configure Coverage

**Create `.coveragerc` or add to `pyproject.toml`**:

**.coveragerc**:
```ini
[run]
# Source packages to measure
source = src

# Files to omit from coverage
omit =
    */tests/*
    */test_*.py
    */__init__.py
    */setup.py
    */conftest.py
    */.venv/*
    */venv/*

# Enable branch coverage
branch = True

# Parallel mode for pytest-xdist
parallel = True

[report]
# Precision for coverage percentage
precision = 2

# Show lines that weren't executed
show_missing = True

# Skip files with 100% coverage (optional)
skip_covered = False

# Skip empty files
skip_empty = True

# Fail if coverage below threshold
fail_under = 80

# Sort by coverage percentage
sort = Cover

# Ignore specific lines
exclude_lines =
    # Standard pragma
    pragma: no cover

    # Don't complain about missing debug code
    def __repr__
    def __str__

    # Don't complain if tests don't hit defensive assertion code
    raise AssertionError
    raise NotImplementedError

    # Don't complain if non-runnable code isn't run
    if __name__ == .__main__.:

    # Don't complain about abstract methods
    @(abc\.)?abstractmethod

    # Don't complain about type checking blocks
    if TYPE_CHECKING:

    # Don't complain about ellipsis in protocols
    \.\.\.

[html]
# Directory for HTML report
directory = htmlcov

# Title for HTML report
title = Code Coverage Report

[xml]
# Output file for XML report (for CI/CD)
output = coverage.xml

[paths]
# Map paths for coverage combining
source =
    src/
    */site-packages/
```

**Alternative: pyproject.toml configuration**:
```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "@abstractmethod",
    "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"
```

### Integrate with pytest

**Add to pytest.ini or pyproject.toml**:
```ini
[pytest]
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-branch
    --cov-fail-under=80
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generate coverage report
coverage report

# Generate HTML report
coverage html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Analyze Coverage Report

**Terminal output example**:
```
Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
src/__init__.py               2      0      0      0   100%
src/core/auth.py             45      8     16      3    78%   23-25, 45-48, 67
src/core/database.py         67     12     22      5    79%   89-95, 112-115
src/core/utils.py            34      2      8      1    92%   45, 67
src/services/user.py         89     25     30      8    67%   45-67, 89-102
---------------------------------------------------------------------
TOTAL                       237     47     76     17    76%
```

### Identify Coverage Gaps

**Create coverage gap analysis**:

```python
# scripts/analyze_coverage.py
"""Analyze coverage gaps and prioritize improvements."""
import json
import sys
from pathlib import Path

def analyze_coverage_gaps():
    """Analyze coverage.json and identify critical gaps."""
    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print("Run: coverage json to generate coverage.json")
        return

    data = json.loads(coverage_file.read_text())

    gaps = []
    for file_path, file_data in data['files'].items():
        coverage = file_data['summary']['percent_covered']
        missing_lines = file_data['missing_lines']

        if coverage < 80:
            gaps.append({
                'file': file_path,
                'coverage': coverage,
                'missing_lines': len(missing_lines),
                'priority': 'high' if coverage < 50 else 'medium'
            })

    # Sort by coverage (lowest first)
    gaps.sort(key=lambda x: x['coverage'])

    print("\n" + "="*70)
    print("Coverage Gap Analysis")
    print("="*70)

    print("\nFiles Below 80% Coverage:\n")
    print(f"{'File':<40} {'Coverage':<12} {'Missing':<10} {'Priority'}")
    print("-"*70)

    for gap in gaps:
        print(f"{gap['file']:<40} {gap['coverage']:>6.1f}% {gap['missing_lines']:>7} {gap['priority']:>10}")

    print(f"\nTotal files needing improvement: {len(gaps)}")

if __name__ == '__main__':
    analyze_coverage_gaps()
```

Run analysis:
```bash
# Generate JSON coverage data
coverage json

# Analyze gaps
python scripts/analyze_coverage.py
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public APIs <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | Internal helpers <80% coverage | Test when modified |

### Identify Critical Paths

```python
# scripts/identify_critical_paths.py
"""Identify critical code paths requiring coverage."""
import ast
from pathlib import Path

class CriticalPathAnalyzer(ast.NodeVisitor):
    """Analyze code to identify critical paths."""

    def __init__(self):
        self.critical_functions = []

    def visit_FunctionDef(self, node):
        """Identify critical functions."""
        # Public functions
        if not node.name.startswith('_'):
            self.critical_functions.append({
                'name': node.name,
                'line': node.lineno,
                'reason': 'Public API'
            })

        # Functions with error handling
        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
        if has_try:
            self.critical_functions.append({
                'name': node.name,
                'line': node.lineno,
                'reason': 'Error handling'
            })

        # Functions with external calls
        has_external = any(
            isinstance(n, ast.Call) and
            isinstance(n.func, ast.Attribute) and
            n.func.attr in ['get', 'post', 'query', 'execute']
            for n in ast.walk(node)
        )
        if has_external:
            self.critical_functions.append({
                'name': node.name,
                'line': node.lineno,
                'reason': 'External dependency'
            })

        self.generic_visit(node)

def analyze_file(file_path):
    """Analyze a Python file for critical paths."""
    code = Path(file_path).read_text()
    tree = ast.parse(code)

    analyzer = CriticalPathAnalyzer()
    analyzer.visit(tree)

    return analyzer.critical_functions

# Usage
for py_file in Path('src').rglob('*.py'):
    critical = analyze_file(py_file)
    if critical:
        print(f"\n{py_file}:")
        for func in critical:
            print(f"  Line {func['line']}: {func['name']} ({func['reason']})")
```

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```python
"""
Add tests for basic functionality of uncovered code.

Focus on main execution paths first.
"""

# Uncovered function
def calculate_discount(price, customer_type):
    if customer_type == "premium":
        return price * 0.20
    elif customer_type == "regular":
        return price * 0.10
    else:
        return 0

# Add basic coverage tests
def test_calculate_discount_premium():
    """Test premium customer discount."""
    discount = calculate_discount(100, "premium")
    assert discount == 20

def test_calculate_discount_regular():
    """Test regular customer discount."""
    discount = calculate_discount(100, "regular")
    assert discount == 10

def test_calculate_discount_other():
    """Test other customer types."""
    discount = calculate_discount(100, "guest")
    assert discount == 0
```

### Strategy 2: Cover Edge Cases

```python
"""Add tests for boundary conditions and edge cases."""

def test_calculate_discount_zero_price():
    """Test discount with zero price."""
    discount = calculate_discount(0, "premium")
    assert discount == 0

def test_calculate_discount_negative_price():
    """Test discount with negative price."""
    discount = calculate_discount(-100, "premium")
    assert discount == -20  # Or should raise ValueError?

def test_calculate_discount_large_price():
    """Test discount with very large price."""
    discount = calculate_discount(1_000_000, "premium")
    assert discount == 200_000

def test_calculate_discount_empty_customer_type():
    """Test discount with empty customer type."""
    discount = calculate_discount(100, "")
    assert discount == 0

def test_calculate_discount_none_customer_type():
    """Test discount with None customer type."""
    discount = calculate_discount(100, None)
    assert discount == 0
```

### Strategy 3: Cover Error Paths

```python
"""Add tests for error handling and exceptional conditions."""

# Function with error handling
def load_user_data(user_id):
    try:
        data = database.query(f"SELECT * FROM users WHERE id={user_id}")
        if not data:
            raise ValueError("User not found")
        return parse_user(data)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise
    except ValueError as e:
        logger.warning(f"Invalid user: {e}")
        return None

# Tests covering error paths
def test_load_user_data_database_error(mock_database):
    """Test handling of database error."""
    mock_database.query.side_effect = DatabaseError("Connection failed")

    with pytest.raises(DatabaseError):
        load_user_data(123)

def test_load_user_data_user_not_found(mock_database):
    """Test handling of missing user."""
    mock_database.query.return_value = None

    result = load_user_data(999)

    assert result is None

def test_load_user_data_parse_error(mock_database):
    """Test handling of parse error."""
    mock_database.query.return_value = {"invalid": "data"}

    with pytest.raises(ValueError):
        load_user_data(123)
```

### Strategy 4: Cover Branch Conditions

```python
"""Ensure all branches of conditional logic are tested."""

def get_shipping_cost(weight, destination, express=False):
    base_cost = weight * 2.5

    if destination == "international":
        base_cost *= 3
    elif destination == "remote":
        base_cost *= 1.5

    if express:
        base_cost *= 2

    return base_cost

# Tests covering all branches
def test_shipping_domestic_standard():
    """Test domestic standard shipping."""
    cost = get_shipping_cost(10, "domestic", express=False)
    assert cost == 25.0

def test_shipping_domestic_express():
    """Test domestic express shipping."""
    cost = get_shipping_cost(10, "domestic", express=True)
    assert cost == 50.0

def test_shipping_international_standard():
    """Test international standard shipping."""
    cost = get_shipping_cost(10, "international", express=False)
    assert cost == 75.0

def test_shipping_international_express():
    """Test international express shipping."""
    cost = get_shipping_cost(10, "international", express=True)
    assert cost == 150.0

def test_shipping_remote_standard():
    """Test remote standard shipping."""
    cost = get_shipping_cost(10, "remote", express=False)
    assert cost == 37.5

def test_shipping_remote_express():
    """Test remote express shipping."""
    cost = get_shipping_cost(10, "remote", express=True)
    assert cost == 75.0
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Generate all report types
pytest --cov=src \
    --cov-report=html \
    --cov-report=xml \
    --cov-report=term-missing \
    --cov-report=json

# Reports generated:
# - htmlcov/index.html (browsable HTML)
# - coverage.xml (for CI/CD)
# - coverage.json (for analysis)
# - Terminal output (quick view)
```

### Coverage Badge

```bash
# Install coverage-badge
pip install coverage-badge

# Generate badge
coverage-badge -o coverage.svg -f

# Add to README.md
# ![Coverage](coverage.svg)
```

### Track Coverage Over Time

```python
# scripts/track_coverage.py
"""Track coverage metrics over time."""
import json
from datetime import datetime
from pathlib import Path

def record_coverage():
    """Record current coverage to history."""
    coverage_file = Path("coverage.json")
    history_file = Path("coverage_history.json")

    if not coverage_file.exists():
        print("No coverage.json found")
        return

    coverage_data = json.loads(coverage_file.read_text())
    total_coverage = coverage_data['totals']['percent_covered']

    # Load history
    history = []
    if history_file.exists():
        history = json.loads(history_file.read_text())

    # Add current record
    history.append({
        'date': datetime.now().isoformat(),
        'coverage': total_coverage,
        'statements': coverage_data['totals']['num_statements'],
        'missing': coverage_data['totals']['missing_lines']
    })

    # Save history
    history_file.write_text(json.dumps(history, indent=2))

    print(f"Coverage recorded: {total_coverage:.1f}%")

if __name__ == '__main__':
    record_coverage()
```

### Coverage Diff for PRs

```python
# scripts/coverage_diff.py
"""Show coverage changes in pull request."""
import json
import sys
from pathlib import Path

def coverage_diff(base_coverage_file, current_coverage_file):
    """Compare coverage between base and current."""
    base = json.loads(Path(base_coverage_file).read_text())
    current = json.loads(Path(current_coverage_file).read_text())

    base_total = base['totals']['percent_covered']
    current_total = current['totals']['percent_covered']
    diff = current_total - base_total

    print(f"\n{'='*70}")
    print("Coverage Diff")
    print(f"{'='*70}")
    print(f"Base coverage:    {base_total:.2f}%")
    print(f"Current coverage: {current_total:.2f}%")
    print(f"Difference:       {diff:+.2f}%")

    # File-level changes
    print(f"\n{'='*70}")
    print("Coverage Changes by File")
    print(f"{'='*70}")

    changes = []
    for file_path in current['files']:
        if file_path in base['files']:
            base_cov = base['files'][file_path]['summary']['percent_covered']
            current_cov = current['files'][file_path]['summary']['percent_covered']
            file_diff = current_cov - base_cov

            if abs(file_diff) > 0.1:  # Show changes > 0.1%
                changes.append({
                    'file': file_path,
                    'diff': file_diff,
                    'current': current_cov
                })

    if changes:
        changes.sort(key=lambda x: x['diff'])
        for change in changes:
            symbol = "📈" if change['diff'] > 0 else "📉"
            print(f"{symbol} {change['file']}: {change['diff']:+.1f}% (now {change['current']:.1f}%)")
    else:
        print("No significant coverage changes")

    # Exit with error if coverage decreased
    if diff < -0.5:
        print(f"\n❌ Coverage decreased by {abs(diff):.2f}%")
        sys.exit(1)
    elif diff < 0:
        print(f"\n⚠️  Coverage decreased slightly by {abs(diff):.2f}%")
    else:
        print(f"\n✅ Coverage maintained or improved")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python coverage_diff.py <base_coverage.json> <current_coverage.json>")
        sys.exit(1)

    coverage_diff(sys.argv[1], sys.argv[2])
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-report=term

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=80

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

      - name: Generate coverage badge
        if: github.ref == 'refs/heads/main'
        run: |
          pip install coverage-badge
          coverage-badge -o coverage.svg -f

      - name: Commit badge
        if: github.ref == 'refs/heads/main'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add coverage.svg
          git diff --quiet && git diff --staged --quiet || git commit -m "Update coverage badge"
          git push
```

### Coverage Regression Prevention

```yaml
# Add to existing workflow

- name: Check for coverage regression
  run: |
    # Download base coverage from main branch
    git fetch origin main
    git show origin/main:coverage.json > ${OUTPUT_DIR}/exports/base_coverage.json

    # Compare with current
    python scripts/coverage_diff.py base_coverage.json coverage.json
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary

- **Overall Coverage**: [percentage]

- **Line Coverage**: [percentage]

- **Branch Coverage**: [percentage]

- **Function Coverage**: [percentage]

- **Total Statements**: [count]

- **Missing Lines**: [count]

### Coverage by Module
| Module | Coverage | Missing | Priority |
|--------|----------|---------|----------|
| src/core/auth.py | 78% | 12 lines | High |
| src/services/user.py | 67% | 25 lines | Critical |
| src/utils/helpers.py | 92% | 3 lines | Low |

### Critical Coverage Gaps
1. **src/services/user.py** (67% coverage)
   - **Missing**: Error handling paths (lines 45-67)
   - **Priority**: Critical - core business logic
   - **Action**: Add tests for error scenarios

2. **src/core/auth.py** (78% coverage)
   - **Missing**: Edge cases (lines 23-25, 45-48)
   - **Priority**: High - security-critical
   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):

- [ ] Add error handling tests for user service

- [ ] Cover authentication edge cases

- [ ] Test database connection failures

**Sprint 2** (Target: 80% → 85%):

- [ ] Add branch coverage for conditionals

- [ ] Test input validation thoroughly

- [ ] Cover integration scenarios

**Sprint 3** (Target: 85% → 90%):

- [ ] Add performance edge cases

- [ ] Cover concurrent operations

- [ ] Test all error messages

### Coverage Reports Generated

- **HTML Report**: `htmlcov/index.html`

- **XML Report**: `coverage.xml` (for CI/CD)

- **JSON Report**: `coverage.json` (for analysis)

- **Badge**: `coverage.svg` (for README)

### Coverage Thresholds

- **Minimum Overall**: 80%

- **Critical Modules**: 90%

- **New Code**: 100%

- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented

- [ ] Coverage measured on every test run

- [ ] HTML reports for detailed analysis

- [ ] Coverage tracked over time

- [ ] Regression prevention in CI/CD

- [ ] Critical paths prioritized

- [ ] Team coverage goals established

### Next Steps

- [ ] Fix identified coverage gaps

- [ ] Set up coverage dashboard

- [ ] Schedule coverage review meetings

- [ ] Document coverage standards

- [ ] Integrate coverage diff in PRs

- [ ] Track coverage trends monthly

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

1. **Complete coverage configuration** (`.coveragerc` or `pyproject.toml`)
2. **Current coverage analysis** with gaps identified
3. **Prioritized improvement plan** with specific actions
4. **Test implementations** to fill critical gaps
5. **Coverage reporting infrastructure** (HTML, XML, JSON, badges)
6. **CI/CD integration** with coverage gates
7. **Coverage tracking scripts** for trends
8. **Coverage diff tools** for PR reviews
9. **Team documentation** on coverage standards
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
