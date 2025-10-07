# Phase 6: Code Coverage Analysis & Improvement

Systematic assessment and optimization of test coverage to ensure comprehensive testing across your codebase.

---

## 📋 Overview

This phase focuses on measuring, analyzing, and improving code coverage to identify untested code paths, ensure critical functionality is covered, and establish coverage standards for ongoing development.

### Objectives

- **Measure Coverage**: Generate comprehensive coverage reports for your test suite
- **Identify Gaps**: Find untested code paths, branches, and edge cases
- **Prioritize Tests**: Focus on critical functionality and high-risk areas
- **Set Standards**: Establish coverage thresholds and quality gates
- **Continuous Monitoring**: Integrate coverage into CI/CD pipelines
- **Improve Quality**: Add targeted tests to reach coverage goals

### Deliverables

- Coverage configuration files (`.coveragerc`, `pyproject.toml`)
- Comprehensive coverage reports (terminal, HTML, XML, JSON)
- Coverage gap analysis and recommendations
- Targeted tests addressing coverage gaps
- CI/CD coverage enforcement workflows
- Coverage badges and documentation

### Time Investment

**1-2 hours** for initial coverage analysis and gap identification
**2-4 hours** for comprehensive coverage improvement to 80%+ coverage
**30 minutes** for CI/CD integration and automation

---

## 🎯 Phase Workflow

### Step 1: Install Coverage Tools

```powershell
# Install coverage.py
python -m pip install coverage[toml]

# Install additional tools (optional)
python -m pip install pytest-cov       # pytest integration
python -m pip install diff-cover       # diff coverage for PRs
python -m pip install coverage-badge   # generate coverage badges
```

### Step 2: Configure Coverage

Create `.coveragerc` or add to `pyproject.toml`:

**Option A: .coveragerc File**
```ini
[run]
# Measure coverage for these source files
source = src/

# Run tests in parallel (if supported)
parallel = True

# Include branch coverage (not just line coverage)
branch = True

# Omit files from coverage
omit =
    */tests/*
    */test_*.py
    */__init__.py
    */migrations/*
    */venv/*
    */.venv/*
    */site-packages/*

[report]
# Fail if coverage is below threshold
fail_under = 80.0

# Show missing line numbers
show_missing = True

# Skip covered files in report
skip_covered = False

# Skip empty files
skip_empty = True

# Precision for coverage percentage
precision = 2

# Sort report by coverage percentage
sort = Cover

# Exclude lines from coverage
exclude_lines =
    # Standard pragmas
    pragma: no cover
    
    # Defensive programming
    raise AssertionError
    raise NotImplementedError
    
    # Abstract methods
    @abstractmethod
    
    # Type checking blocks
    if TYPE_CHECKING:
    if typing.TYPE_CHECKING:
    
    # Debug code
    if __name__ == .__main__.:
    
    # Platform-specific code
    if sys.platform
    
    # Deprecated code
    @deprecated
    warnings.warn

[html]
# HTML report directory
directory = htmlcov

# Title for HTML report
title = Test Coverage Report

[xml]
# XML report for CI/CD tools
output = coverage.xml

[json]
# JSON report for programmatic access
output = coverage.json
show_contexts = True
```

**Option B: pyproject.toml Configuration**
```toml
[tool.coverage.run]
source = ["src"]
branch = true
parallel = true
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/.venv/*",
]

[tool.coverage.report]
fail_under = 80.0
show_missing = true
skip_covered = false
skip_empty = true
precision = 2
sort = "Cover"
exclude_lines = [
    "pragma: no cover",
    "raise AssertionError",
    "raise NotImplementedError",
    "@abstractmethod",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.coverage.html]
directory = "htmlcov"
title = "Test Coverage Report"

[tool.coverage.xml]
output = "coverage.xml"

[tool.coverage.json]
output = "coverage.json"
show_contexts = true
```

### Step 3: Run Coverage Analysis

```powershell
# Run tests with coverage
python -m coverage run -m pytest tests/

# Or using run_all_tests.py
python -m coverage run tests/run_all_tests.py

# Generate terminal report
python -m coverage report

# Generate detailed HTML report
python -m coverage html

# Generate XML report (for CI/CD)
python -m coverage xml

# Generate JSON report (for programmatic access)
python -m coverage json

# Open HTML report in browser
start htmlcov/index.html  # Windows
```

### Step 4: Analyze Coverage Reports

**Terminal Report Analysis:**
```
Name                        Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------
src/__init__.py                 0      0      0      0   100%
src/main.py                    45      5     12      2    85%   23-27, 45
src/core/processor.py          120     15     30      5    85%   67-75, 102-110
src/core/database.py            85      2     18      1    96%   145-146
src/core/utils.py               52      0     12      0   100%
src/gui/components.py           95     25     20      8    68%   Multiple ranges
-------------------------------------------------------------------------
TOTAL                          397     47     92     16    85%
```

**Key Metrics:**
- **Stmts**: Total executable statements
- **Miss**: Statements not executed during tests
- **Branch**: Total branch points (if/else, loops)
- **BrPart**: Partially covered branches (one path tested, not both)
- **Cover**: Overall coverage percentage
- **Missing**: Line numbers of uncovered code

**HTML Report Features:**
- Line-by-line highlighting (green = covered, red = uncovered, yellow = partial)
- Branch coverage visualization
- File-by-file navigation
- Sortable columns
- Search functionality

### Step 5: Identify Coverage Gaps

**Critical Areas to Analyze:**

1. **Low Coverage Modules** (<70% coverage)
   - Identify files with insufficient testing
   - Prioritize based on criticality and complexity

2. **Missing Branch Coverage**
   - Find if/else statements with only one path tested
   - Locate error handling not covered by tests
   - Identify edge cases in conditionals

3. **Untested Functions**
   - List functions with 0% coverage
   - Assess if functions are actually used (dead code?)
   - Prioritize public API functions

4. **Partial Coverage Patterns**
   - Exception handling blocks
   - Input validation logic
   - Boundary conditions
   - Cleanup/teardown code

**Generate Coverage Gap Report:**
```python
"""
Script to analyze coverage and generate gap report.

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def load_coverage_data(json_path: str = "coverage.json") -> Dict:
    """Load coverage data from JSON report."""
    with open(json_path, 'r') as f:
        return json.load(f)

def identify_low_coverage_files(
    coverage_data: Dict, 
    threshold: float = 70.0
) -> List[Tuple[str, float]]:
    """Identify files below coverage threshold."""
    low_coverage = []
    files = coverage_data.get('files', {})
    
    for filepath, data in files.items():
        summary = data.get('summary', {})
        coverage = summary.get('percent_covered', 0)
        
        if coverage < threshold:
            low_coverage.append((filepath, coverage))
    
    return sorted(low_coverage, key=lambda x: x[1])

def identify_missing_branches(coverage_data: Dict) -> List[Tuple[str, int, str]]:
    """Identify partially covered branches."""
    missing_branches = []
    files = coverage_data.get('files', {})
    
    for filepath, data in files.items():
        for line_num, contexts in data.get('missing_lines', {}).items():
            missing_branches.append((
                filepath, 
                int(line_num), 
                'Missing line coverage'
            ))
        
        for line_num, branches in data.get('executed_branches', {}).items():
            if len(branches) < 2:  # Partial branch coverage
                missing_branches.append((
                    filepath, 
                    int(line_num), 
                    'Partial branch coverage'
                ))
    
    return sorted(missing_branches, key=lambda x: (x[0], x[1]))

def generate_gap_report(coverage_json: str = "coverage.json") -> None:
    """Generate comprehensive coverage gap report."""
    coverage_data = load_coverage_data(coverage_json)
    
    print("=" * 100)
    print("                          CODE COVERAGE GAP ANALYSIS")
    print("─" * 100)
    
    # Overall statistics
    totals = coverage_data.get('totals', {})
    print(f"\nOverall Coverage: {totals.get('percent_covered', 0):.2f}%")
    print(f"Total Statements: {totals.get('num_statements', 0)}")
    print(f"Missing Statements: {totals.get('missing_lines', 0)}")
    print(f"Total Branches: {totals.get('num_branches', 0)}")
    print(f"Partial Branches: {totals.get('num_partial_branches', 0)}")
    
    # Low coverage files
    print("\n" + "─" * 100)
    print("LOW COVERAGE FILES (<70%)")
    print("─" * 100)
    
    low_coverage = identify_low_coverage_files(coverage_data, 70.0)
    if low_coverage:
        for filepath, coverage in low_coverage:
            print(f"  {filepath:<60} {coverage:>6.2f}%")
    else:
        print("  ✅ No files below 70% coverage threshold")
    
    # Missing branches
    print("\n" + "─" * 100)
    print("MISSING/PARTIAL BRANCH COVERAGE")
    print("─" * 100)
    
    missing_branches = identify_missing_branches(coverage_data)
    if missing_branches:
        current_file = None
        for filepath, line_num, issue in missing_branches[:20]:  # Top 20
            if filepath != current_file:
                print(f"\n  {filepath}:")
                current_file = filepath
            print(f"    Line {line_num}: {issue}")
        
        if len(missing_branches) > 20:
            print(f"\n  ... and {len(missing_branches) - 20} more issues")
    else:
        print("  ✅ Full branch coverage achieved")
    
    print("\n" + "=" * 100)

if __name__ == '__main__':
    generate_gap_report()
```

**Usage:**
```powershell
# Generate JSON coverage report
python -m coverage json

# Run gap analysis
python tests/coverage_gap_analysis.py
```

### Step 6: Add Targeted Tests

**Strategy for Improving Coverage:**

1. **Prioritize by Risk and Criticality**
   - Core business logic: Must have 90%+ coverage
   - Data processing: 85%+ coverage
   - Error handling: 80%+ coverage
   - UI/presentation: 70%+ coverage acceptable

2. **Focus on Uncovered Branches**
   ```python
   # Example: Testing both branches of conditional
   def test_validation_success(self):
       """Test validation with valid input."""
       result = validator.validate(valid_data)
       self.assertTrue(result.is_valid)
   
   def test_validation_failure(self):
       """Test validation with invalid input."""
       result = validator.validate(invalid_data)
       self.assertFalse(result.is_valid)
       self.assertIn("error", result.messages)
   ```

3. **Test Exception Paths**
   ```python
   def test_error_handling_network_failure(self):
       """Test behavior when network request fails."""
       mock_client = Mock()
       mock_client.request.side_effect = NetworkError("Connection timeout")
       
       with self.assertRaises(ServiceUnavailableError):
           service.fetch_data(mock_client)
   
   def test_error_handling_invalid_response(self):
       """Test behavior when API returns invalid data."""
       mock_client = Mock()
       mock_client.request.return_value = {"invalid": "format"}
       
       with self.assertRaises(ValidationError):
           service.fetch_data(mock_client)
   ```

4. **Cover Edge Cases**
   ```python
   def test_edge_cases(self):
       """Test boundary conditions and edge cases."""
       edge_cases = [
           (None, "null input"),
           ([], "empty list"),
           ([None], "list with null"),
           ("", "empty string"),
           (0, "zero value"),
           (-1, "negative value"),
           (sys.maxsize, "max integer"),
           (float('inf'), "infinity"),
           (float('nan'), "not a number"),
       ]
       
       for input_value, description in edge_cases:
           with self.subTest(case=description):
               # Test each edge case
               result = processor.handle(input_value)
               self.assertIsNotNone(result, f"Failed on {description}")
   ```

5. **Test Private Methods (Selectively)**
   ```python
   # Only test private methods with complex logic
   def test_private_complex_calculation(self):
       """Test internal calculation logic."""
       processor = DataProcessor()
       # Access private method for testing complex logic
       result = processor._calculate_weighted_average([1, 2, 3], [0.5, 0.3, 0.2])
       self.assertAlmostEqual(result, 1.7, places=2)
   ```

### Step 7: Exclude Legitimate Gaps

**When to Use Coverage Pragmas:**

```python
# Defensive programming - should never happen
def process_data(data: Optional[Dict]) -> Dict:
    """Process data with type safety."""
    if data is None:  # pragma: no cover
        raise AssertionError("Unexpected None - should be caught earlier")
    return transform(data)

# Abstract methods - tested in implementations
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    @abstractmethod  # pragma: no cover
    def process(self, data: Any) -> Any:
        """Process data - implemented by subclasses."""
        pass

# Platform-specific code
import sys

if sys.platform == 'win32':  # pragma: no cover
    # Windows-specific code
    pass
elif sys.platform == 'darwin':  # pragma: no cover
    # macOS-specific code
    pass
else:  # pragma: no cover
    # Linux/other platforms
    pass

# Debug/development code
def debug_info(data: Dict) -> None:  # pragma: no cover
    """Print debug information - development only."""
    import pprint
    pprint.pprint(data)

# Type checking blocks
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .types import ComplexType

# Deprecated code paths
import warnings

def old_function():  # pragma: no cover
    """Deprecated function kept for backwards compatibility."""
    warnings.warn("Use new_function instead", DeprecationWarning)
    return legacy_logic()
```

**Best Practices:**
- Use `pragma: no cover` sparingly and with good reason
- Document why coverage is excluded
- Review pragmas during code reviews
- Revisit pragmas periodically to ensure they're still valid

### Step 8: Set Coverage Thresholds

**Recommended Thresholds:**

```python
# test_config.py
COVERAGE_THRESHOLDS = {
    # Overall project threshold
    'overall': 80.0,
    
    # By module type
    'core': 90.0,           # Critical business logic
    'api': 85.0,            # API endpoints
    'database': 85.0,       # Data access layer
    'utils': 80.0,          # Utility functions
    'gui': 70.0,            # UI components (acceptable lower)
    'scripts': 60.0,        # One-off scripts (acceptable lower)
    
    # By coverage type
    'line_coverage': 80.0,
    'branch_coverage': 75.0,
}

def check_coverage_thresholds(coverage_data: Dict) -> bool:
    """
    Validate coverage meets minimum thresholds.
    
    Returns:
        True if all thresholds met, False otherwise
    """
    overall_coverage = coverage_data['totals']['percent_covered']
    
    if overall_coverage < COVERAGE_THRESHOLDS['overall']:
        print(f"❌ Overall coverage {overall_coverage:.2f}% below threshold {COVERAGE_THRESHOLDS['overall']}%")
        return False
    
    # Check individual modules
    files = coverage_data.get('files', {})
    failures = []
    
    for filepath, data in files.items():
        module_type = determine_module_type(filepath)
        threshold = COVERAGE_THRESHOLDS.get(module_type, COVERAGE_THRESHOLDS['overall'])
        coverage = data['summary']['percent_covered']
        
        if coverage < threshold:
            failures.append(f"{filepath}: {coverage:.2f}% < {threshold}%")
    
    if failures:
        print("❌ Coverage threshold failures:")
        for failure in failures:
            print(f"  - {failure}")
        return False
    
    print(f"✅ All coverage thresholds met ({overall_coverage:.2f}%)")
    return True

def determine_module_type(filepath: str) -> str:
    """Determine module type from filepath."""
    if 'core' in filepath:
        return 'core'
    elif 'api' in filepath:
        return 'api'
    elif 'database' in filepath or 'db' in filepath:
        return 'database'
    elif 'utils' in filepath:
        return 'utils'
    elif 'gui' in filepath or 'ui' in filepath:
        return 'gui'
    elif 'scripts' in filepath:
        return 'scripts'
    return 'overall'
```

### Step 9: Integrate with CI/CD

**GitHub Actions Workflow:**

```yaml
# .github/workflows/coverage.yml
name: Code Coverage

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  coverage:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
        pip install coverage[toml] pytest-cov
    
    - name: Run tests with coverage
      run: |
        coverage run -m pytest tests/
        coverage report
        coverage xml
        coverage html
    
    - name: Check coverage threshold
      run: |
        coverage report --fail-under=80
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true
    
    - name: Archive coverage HTML report
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/
    
    - name: Comment coverage on PR
      if: github.event_name == 'pull_request'
      uses: py-cov-action/python-coverage-comment-action@v3
      with:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Jenkins Pipeline:**

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv .venv'
                sh '.venv/bin/pip install -e .[dev]'
                sh '.venv/bin/pip install coverage[toml]'
            }
        }
        
        stage('Test with Coverage') {
            steps {
                sh '.venv/bin/coverage run -m pytest tests/'
                sh '.venv/bin/coverage report'
                sh '.venv/bin/coverage xml'
                sh '.venv/bin/coverage html'
            }
        }
        
        stage('Coverage Check') {
            steps {
                script {
                    def result = sh(
                        script: '.venv/bin/coverage report --fail-under=80',
                        returnStatus: true
                    )
                    if (result != 0) {
                        error('Coverage below 80% threshold')
                    }
                }
            }
        }
        
        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
                
                cobertura coberturaReportFile: 'coverage.xml'
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'coverage.xml,htmlcov/**', allowEmptyArchive: true
        }
    }
}
```

**GitLab CI:**

```yaml
# .gitlab-ci.yml
coverage:
  stage: test
  image: python:3.9
  script:
    - pip install -e .[dev]
    - pip install coverage[toml]
    - coverage run -m pytest tests/
    - coverage report
    - coverage xml
    - coverage html
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 30 days
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Step 10: Monitor Coverage Over Time

**Coverage Trend Tracking:**

```python
"""
Track coverage trends over time.

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class CoverageTracker:
    """Track and analyze coverage trends."""
    
    def __init__(self, db_path: str = "coverage_history.db"):
        """Initialize coverage tracker with database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Create database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coverage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                commit_hash TEXT,
                branch TEXT,
                overall_coverage REAL NOT NULL,
                line_coverage REAL NOT NULL,
                branch_coverage REAL NOT NULL,
                num_statements INTEGER NOT NULL,
                num_missing INTEGER NOT NULL,
                num_branches INTEGER NOT NULL,
                num_partial_branches INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                filepath TEXT NOT NULL,
                coverage REAL NOT NULL,
                statements INTEGER NOT NULL,
                missing INTEGER NOT NULL,
                FOREIGN KEY (history_id) REFERENCES coverage_history(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_coverage(
        self, 
        coverage_json: str = "coverage.json",
        commit_hash: str = None,
        branch: str = None
    ) -> None:
        """Record coverage data point."""
        with open(coverage_json, 'r') as f:
            data = json.load(f)
        
        totals = data['totals']
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO coverage_history (
                timestamp, commit_hash, branch,
                overall_coverage, line_coverage, branch_coverage,
                num_statements, num_missing, 
                num_branches, num_partial_branches
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, commit_hash, branch,
            totals['percent_covered'],
            totals.get('percent_covered_display', totals['percent_covered']),
            totals.get('covered_branches', 0) / max(totals.get('num_branches', 1), 1) * 100,
            totals['num_statements'],
            totals['missing_lines'],
            totals['num_branches'],
            totals['num_partial_branches']
        ))
        
        history_id = cursor.lastrowid
        
        # Record per-file coverage
        for filepath, file_data in data['files'].items():
            summary = file_data['summary']
            cursor.execute("""
                INSERT INTO file_coverage (
                    history_id, filepath, coverage, statements, missing
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                history_id,
                filepath,
                summary['percent_covered'],
                summary['num_statements'],
                summary['missing_lines']
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Coverage recorded: {totals['percent_covered']:.2f}%")
    
    def generate_trend_report(self, days: int = 30) -> None:
        """Generate coverage trend report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, overall_coverage, line_coverage, branch_coverage
            FROM coverage_history
            WHERE datetime(timestamp) >= datetime('now', ? || ' days')
            ORDER BY timestamp
        """, (f'-{days}',))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No coverage data available")
            return
        
        print("=" * 100)
        print(f"                    COVERAGE TREND REPORT (Last {days} Days)")
        print("─" * 100)
        
        print(f"\n{'Date':<20} {'Overall':<10} {'Line':<10} {'Branch':<10} {'Trend'}")
        print("─" * 100)
        
        prev_coverage = None
        for timestamp, overall, line, branch in rows:
            date = timestamp.split('T')[0]
            
            trend = ""
            if prev_coverage:
                diff = overall - prev_coverage
                if diff > 0:
                    trend = f"↑ +{diff:.2f}%"
                elif diff < 0:
                    trend = f"↓ {diff:.2f}%"
                else:
                    trend = "→"
            
            print(f"{date:<20} {overall:>6.2f}%    {line:>6.2f}%    {branch:>6.2f}%    {trend}")
            prev_coverage = overall
        
        # Calculate statistics
        coverages = [row[1] for row in rows]
        avg = sum(coverages) / len(coverages)
        min_cov = min(coverages)
        max_cov = max(coverages)
        
        print("─" * 100)
        print(f"Average: {avg:.2f}%  |  Min: {min_cov:.2f}%  |  Max: {max_cov:.2f}%")
        print("=" * 100)

# Usage
tracker = CoverageTracker()
tracker.record_coverage(commit_hash="abc123", branch="main")
tracker.generate_trend_report(days=30)
```

### Step 11: Generate Coverage Badge

**Create Coverage Badge for README:**

```powershell
# Install coverage-badge
python -m pip install coverage-badge

# Generate badge
coverage-badge -o coverage.svg

# Or with custom colors
coverage-badge -o coverage.svg -f
```

**Add to README.md:**
```markdown
![Coverage](coverage.svg)

# Or with dynamic badge from Codecov/Coveralls
![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)
```

---

## 📊 Coverage Quality Standards

### Coverage Targets

**By Project Phase:**
- **Initial Development**: 60%+ (focus on core functionality)
- **Beta/Testing**: 75%+ (expand to edge cases)
- **Production**: 80%+ (comprehensive coverage)
- **Critical Systems**: 90%+ (financial, healthcare, security)

**By Code Category:**
- **Business Logic**: 90%+ required
- **API Endpoints**: 85%+ required
- **Data Processing**: 85%+ required
- **Utilities**: 80%+ required
- **UI Components**: 70%+ acceptable
- **Scripts/Tools**: 60%+ acceptable

### Coverage Types

1. **Line Coverage**: Percentage of code lines executed
2. **Branch Coverage**: Percentage of decision branches tested (both true/false)
3. **Function Coverage**: Percentage of functions called
4. **Statement Coverage**: Percentage of statements executed

**Best Practice**: Branch coverage is more meaningful than line coverage alone.

### Quality Metrics

**Beyond Coverage Percentage:**

- **Test quality**: Do tests actually validate behavior?
- **Edge case coverage**: Are boundary conditions tested?
- **Error path coverage**: Are exceptions and errors handled?
- **Integration coverage**: Are component interactions tested?
- **Mutation testing**: Would tests catch introduced bugs?

---

## 🎓 Copy-Paste Prompts

### Prompt 1: Initial Coverage Setup

```
Set up code coverage analysis for my Python project using coverage.py:

1. Create coverage configuration in pyproject.toml with:
   - Source directory: src/
   - Branch coverage enabled
   - 80% minimum threshold
   - Exclude: tests/, __init__.py, venv/
   - Exclude lines: pragma: no cover, abstractmethod, TYPE_CHECKING, if __name__

2. Create coverage gap analysis script (tests/coverage_gap_analysis.py) that:
   - Loads coverage.json data
   - Identifies files below 70% coverage
   - Lists missing/partial branch coverage
   - Generates formatted report

3. Add coverage commands to tests/run_all_tests.py or create separate script

4. Generate initial coverage report and identify top 5 gaps

Project structure:
[Provide your project structure]

Follow organizational standards for:
- No inline comments
- Explain "why" not "what"
- Complete docstrings
- Type hints
```

### Prompt 2: Targeted Test Addition

```
Add tests to improve coverage for [specific module/function]:

Current coverage: [X]%
Target coverage: [Y]%

Focus areas identified:
1. [Uncovered function/branch]
2. [Missing error handling]
3. [Edge cases not tested]

Requirements:
- Follow existing test suite structure (test_01, test_02 pattern)
- Use TestResultAggregator and PerformanceTimer
- Include timeout decorator
- Test both success and failure paths
- Cover edge cases: None, empty, invalid input
- Comprehensive docstrings

Current test file:
[Paste existing test file or structure]

Module to test:
[Paste module code or signature]
```

### Prompt 3: CI/CD Coverage Integration

```
Integrate code coverage into CI/CD pipeline:

Platform: [GitHub Actions / GitLab CI / Jenkins]

Requirements:
1. Run tests with coverage on every PR and main branch push
2. Generate coverage reports (terminal, XML, HTML)
3. Enforce 80% minimum coverage threshold
4. Upload coverage to Codecov/Coveralls
5. Post coverage summary as PR comment
6. Archive HTML report as artifact
7. Fail build if coverage drops below threshold

Current workflow file:
[Paste existing workflow if any]

Project uses:
- Python [version]
- Test framework: [pytest / unittest]
- Dependencies: [list key dependencies]
```

### Prompt 4: Coverage Trend Tracking

```
Create coverage trend tracking system:

1. SQLite database schema for:
   - Coverage history (timestamp, commit, branch, percentages)
   - Per-file coverage tracking

2. CoverageTracker class with methods:
   - record_coverage(coverage_json, commit_hash, branch)
   - generate_trend_report(days)
   - identify_coverage_regressions()
   - export_trends_csv()

3. Integration with CI/CD to record coverage after each run

4. Weekly report showing:
   - Coverage trends (last 30 days)
   - Files with declining coverage
   - Overall trajectory

Follow organizational standards with complete docstrings and type hints.
```

---

## ✅ Success Criteria

### Phase Complete When:

- [ ] Coverage tools installed and configured
- [ ] Coverage configuration file created (.coveragerc or pyproject.toml)
- [ ] Initial coverage report generated (80%+ or documented gaps)
- [ ] Coverage gap analysis completed
- [ ] Targeted tests added for critical uncovered code
- [ ] Coverage thresholds defined and documented
- [ ] CI/CD integration configured with coverage enforcement
- [ ] Coverage badge added to README
- [ ] Coverage trend tracking established (optional)
- [ ] Team educated on coverage standards

### Quality Indicators:

- **Comprehensive**: Both line and branch coverage measured
- **Actionable**: Gap analysis identifies specific improvements
- **Automated**: Coverage runs on every commit/PR
- **Enforced**: CI/CD fails on coverage regressions
- **Visible**: Coverage metrics easily accessible
- **Maintained**: Regular review of coverage trends

---

## 📚 Additional Resources

### Coverage Tools

- **coverage.py**: https://coverage.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **Codecov**: https://codecov.io/
- **Coveralls**: https://coveralls.io/

### Best Practices

- **Google Testing Blog**: https://testing.googleblog.com/
- **Martin Fowler on Test Coverage**: https://martinfowler.com/bliki/TestCoverage.html
- **Python Testing Guide**: https://docs.python-guide.org/writing/tests/

### Advanced Topics

- **Mutation Testing**: Testing test quality with mutmut or pytest-mutate
- **Differential Coverage**: Coverage for changed lines only (diff-cover)
- **Coverage Visualization**: SonarQube, Code Climate
- **Property-Based Testing**: Hypothesis for comprehensive input coverage

---

*This phase completes the test development protocol by ensuring your test suite provides comprehensive coverage and maintains quality over time.*
