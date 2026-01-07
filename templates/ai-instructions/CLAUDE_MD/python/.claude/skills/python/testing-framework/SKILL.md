---
name: python-testing-framework
description: Complete Python testing framework including test structure (run_all_tests.py, common.py, test_config.py), test implementation templates with timeout decorator, and CRITICAL test output formatting requirements with exact spacing, tables, and visual elements. Use when writing tests, setting up testing, or formatting test output.
---

# Python Testing Framework

## Test Structure

1. **run_all_tests.py**: Auto-detect suites, comprehensive reporting
2. **common.py**: Shared utilities, aggregation, timing
3. **test_config.py**: Pass/fail criteria, settings
4. **Individual suites**: Feature-specific tests

## Test Implementation Template

```python
"""
[Test Suite Description]

Comprehensive test suite for [feature/module] functionality.
Tests cover normal operations, edge cases, and error conditions.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import functools
import os
import sys
import unittest
from typing import Any, Dict, List, Optional

# Path setup for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from common import TestResultAggregator, PerformanceTimer, format_console_output
from test_config import get_pass_criteria


def timeout(seconds: int = 120):
    """Decorator to add timeout to test methods."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            result = [None]
            exception = [None]
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                raise TimeoutError(f"Test {func.__name__} timed out after {seconds} seconds")
            if exception[0]:
                raise exception[0]
            return result[0]
        return wrapper
    return decorator


class FeatureTestSuite(unittest.TestCase):
    """Comprehensive test suite for [Feature] functionality."""

    def __init__(self, methodName: str = 'runTest'):
        """Initialize test suite with result aggregation."""
        super().__init__(methodName)
        self.aggregator = TestResultAggregator("Feature Test Suite")

    def setUp(self) -> None:
        """Set up test environment before each test."""
        # Initialize test environment
        # Clean up any existing state
        # Prepare test data
        pass

    def tearDown(self) -> None:
        """Clean up after each test."""
        # Clean up resources
        # Reset state
        # Close connections
        pass

    @timeout(120)
    def test_01_basic_functionality(self) -> None:
        """TEST 1: Basic functionality validation."""
        test_name = "Basic Functionality Test"
        description = "Validates core feature operations under normal conditions"
        timer = PerformanceTimer()
        timer.start()
        try:
            # Test implementation
            result_value = self._perform_basic_test()
            elapsed = timer.stop()
            # Metrics collection
            metrics = {
                "Test Result": f"{result_value}",
                "Processing Time": f"{elapsed:.3f}s",
                "Memory Usage": "Within limits",
                "Success Rate": "100%"
            }
            # Pass/fail determination
            criteria = get_pass_criteria('basic_functionality')
            passed = result_value >= criteria['minimum_value']
            result_text = f"Achieved {result_value} (threshold: {criteria['minimum_value']})"
            print(format_console_output(1, test_name, description, metrics, result_text, passed))
            self.aggregator.add_result(test_name, "✅" if passed else "❌", f"{elapsed:.3f}s", metrics, passed)
            self.assertTrue(passed, f"Test failed: {result_text}")
        except Exception as e:
            elapsed = timer.stop()
            metrics = {"Error": str(e)}
            result_text = f"Failed with error: {str(e)}"
            print(format_console_output(1, test_name, description, metrics, result_text, False))
            self.aggregator.add_result(test_name, "❌", f"{elapsed:.3f}s", metrics, False)
            raise

    def _perform_basic_test(self) -> Any:
        """Helper method for basic test operations."""
        # Implementation details
        return True


if __name__ == '__main__':
    unittest.main()
```

## Test Output Format

**CRITICAL**: All test output must follow this exact formatting structure with precise spacing, alignment, and visual elements.

### Master Test Runner Header
```
====================================================================================================
====================================================================================================
                              [APPLICATION NAME] - FULL TEST SUITES RUNNER
───────────────────────────────────────────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────────────────────────────────────
Full test suites execution started at: [YYYY-MM-DD HH:MM:SS]

Starting [Test Suite Name]...
```

### Test Suite Header
```
====================================================================================================
                            [APPLICATION NAME] - [TEST SUITE NAME]
───────────────────────────────────────────────────────────────────────────────────────────────────
Test started at: [YYYY-MM-DD HH:MM:SS]
```

### Individual Test Format
```
[TEST X] [Test Name]
───────────────────────────────────────────────────────────────────────────────────────────────────
Description:            [Detailed description of what this test validates]
[Metric Name 1]:        [Value with units/format]
[Metric Name 2]:        [Value with units/format]
[Metric Name 3]:        [Value with units/format]
[Additional Metrics]:   [As many as needed for comprehensive reporting]
Result:                 [Descriptive result summary with dot padding] ............................ ✅/❌
```

### Test Suite Summary Table
```
───────────────────────────────────────────────────────────────────────────────────────────────────
                                [TEST NAME] SUMMARY
───────────────────────────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────┬──────────┬────────┐
│ Test Name                            │  Result  │ Status │
├──────────────────────────────────────┼──────────┼────────┤
│ [Test Name 1]                        │   X/Y    │   ✅   │
│ [Test Name 2]                        │   X/Y    │   ❌   │
│ [Test Name 3]                        │   X/Y    │   ✅   │
└──────────────────────────────────────┴──────────┴────────┘

Tests Passed:        X/Y
Pass Threshold:      Z%
Test Duration:       XXX seconds
───────────────────────────────────────────────────────────────────────────────────────────────────
TEST STATUS: ✅/❌  with X% tests passed
====================================================================================================
```

### Master Summary Table (All Test Suites)
```
====================================================================================================
                                    COMPLETE TEST SUITES SUMMARY
───────────────────────────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────┬──────────┬────────┐
│ Test Suite                           │  Result  │ Status │
├──────────────────────────────────────┼──────────┼────────┤
│ [Test Suite Name 1]                  │   X/Y    │   ✅   │
│ [Test Suite Name 2]                  │   X/Y    │   ❌   │
│ [Test Suite Name 3]                  │   X/Y    │   ✅   │
└──────────────────────────────────────┴──────────┴────────┘

Test Suites Passed:   X/Y
Individual Tests:     XX/YY
Overall Pass Rate:    Z%
Suite Pass Threshold: 80%
Total Duration:       XXXX seconds

───────────────────────────────────────────────────────────────────────────────────────────────────
FINAL TESTS STATUS: ✅/❌  with Z% overall pass rate
====================================================================================================
====================================================================================================
```

### Formatting Requirements
- **Separators**: 100 chars of `═` for major, `─` for minor
- **Tables**: Use box-drawing: `┌─┬─┐`, `├─┼─┤`, `└─┴─┘`
- **Icons**: ✅ for pass, ❌ for fail
- **Dots**: Use `.` for result padding
- **Labels**: 20-char width, left-aligned
- **Time**: ISO format `YYYY-MM-DD HH:MM:SS`
- **Output**: Always use `flush=True`

## test_config.py Template

```python
"""Test configuration."""

def get_pass_criteria(test_name: str) -> dict:
    """Get pass/fail criteria."""
    criteria = {
        'basic': {'minimum': 0.95, 'max_time': 5.0},
        'basic_functionality': {'minimum_value': 0.95},
        'performance': {'max_latency': 1.0, 'min_throughput': 100},
        'stress': {'failure_tolerance': 0.01, 'recovery_time': 10.0}
    }
    return criteria.get(test_name, {'default': True})

SUITE_PASS_THRESHOLD = 0.80
DEFAULT_TIMEOUT = 120
VERBOSE_OUTPUT = True
```

## common.py Template

```python
"""Common test utilities."""
import time
from typing import Any, Dict, List


class PerformanceTimer:
    """Timer for measuring test performance."""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start the timer."""
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop the timer and return elapsed time."""
        self.end_time = time.time()
        return self.end_time - self.start_time


class TestResultAggregator:
    """Aggregate test results for reporting."""

    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self.results: List[Dict] = []

    def add_result(
        self,
        test_name: str,
        status: str,
        duration: str,
        metrics: Dict[str, Any],
        passed: bool
    ):
        """Add a test result."""
        self.results.append({
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'metrics': metrics,
            'passed': passed
        })

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        return {
            'suite_name': self.suite_name,
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0
        }


def format_console_output(
    test_number: int,
    test_name: str,
    description: str,
    metrics: Dict[str, Any],
    result_text: str,
    passed: bool
) -> str:
    """Format test output for console display."""
    separator = "─" * 100
    status_icon = "✅" if passed else "❌"

    lines = [
        f"[TEST {test_number}] {test_name}",
        separator,
        f"Description:            {description}",
    ]

    for metric_name, metric_value in metrics.items():
        lines.append(f"{metric_name}:".ljust(24) + str(metric_value))

    # Calculate dot padding
    result_prefix = f"Result:                 {result_text} "
    dot_count = 100 - len(result_prefix) - 2
    dots = "." * max(dot_count, 3)

    lines.append(f"Result:                 {result_text} {dots} {status_icon}")

    return "\n".join(lines)
```

## Testing Decision Tree

```
Question: What testing approach should I use?

Unit Testing?
├─ Pure functions? → Simple assertions
├─ Dependencies? → Mock objects
├─ Database? → Test database
└─ API? → Mock responses

Integration Testing?
├─ Multiple components? → End-to-end
├─ Workflows? → Scenario tests
└─ Performance? → Load tests

Edge Cases?
├─ Boundaries? → Test limits
├─ Errors? → Test exceptions
└─ Concurrent? → Thread safety
```

## Pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--strict-markers --cov=src --cov-report=html --cov-report=term"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```
