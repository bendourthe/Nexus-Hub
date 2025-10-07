# Phase 2: Test Case Development

## Objective
Develop comprehensive test cases covering functionality, edge cases, error conditions, and performance requirements.

## Test Development Checklist

### Test Suite Structure
- [ ] Test suite class inherits from `unittest.TestCase`
- [ ] Comprehensive module docstring with authors
- [ ] `TestResultAggregator` initialized in `__init__`
- [ ] `setUp()` method prepares test environment
- [ ] `tearDown()` method cleans up resources
- [ ] Tests numbered sequentially (test_01, test_02, etc.)
- [ ] Each test has descriptive docstring

### Test Coverage Categories
- [ ] Basic functionality tests (happy path)
- [ ] Edge case tests (boundaries, empty inputs, nulls)
- [ ] Error condition tests (invalid inputs, exceptions)
- [ ] Integration tests (component interactions)
- [ ] Performance tests (speed, throughput, resource usage)
- [ ] Stress tests (load handling, limits)
- [ ] Regression tests (previously fixed bugs)

### Test Implementation Standards
- [ ] `@timeout` decorator on all tests
- [ ] Try-except blocks with proper error handling
- [ ] `PerformanceTimer` for timing measurements
- [ ] Comprehensive metrics collection
- [ ] Pass/fail criteria from `test_config`
- [ ] Proper assertions with descriptive messages
- [ ] `format_console_output` for result display

### Test Independence
- [ ] Tests don't depend on execution order
- [ ] Each test can run in isolation
- [ ] No shared state between tests
- [ ] setUp creates fresh test environment
- [ ] tearDown removes all test artifacts

## Detailed Test Development Prompt

```
Please help me develop comprehensive test cases for my Python project.

**Component to Test:**
- Module/Class: [MODULE_NAME]
- Functionality: [DESCRIPTION]
- Critical operations: [LIST]
- External dependencies: [LIST]
- Performance requirements: [REQUIREMENTS]

**Test Suite Development:**

### 1. Test Suite Template
Create test suite following this structure:

```python
"""
Comprehensive test suite for [FEATURE] functionality.
Tests cover normal operations, edge cases, error conditions, and performance.

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import functools
import os
import sys
import time
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch, MagicMock

# Path setup for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from common import TestResultAggregator, PerformanceTimer, format_console_output
from test_config import get_pass_criteria, SUITE_PASS_THRESHOLD

# Import module under test
from src.core.[module] import [ClassOrFunction]


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
                raise TimeoutError(
                    f"Test {func.__name__} timed out after {seconds} seconds"
                )
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
        self.aggregator = TestResultAggregator("[Feature] Test Suite")
        self.test_data_path = os.path.join(
            os.path.dirname(__file__), 'test_data'
        )
    
    def setUp(self) -> None:
        """Set up test environment before each test."""
        # Load test configuration
        self.test_config = self._load_test_config()
        # Clean any existing test state
        self._clean_test_environment()
        # Prepare test data
        self.test_data = self._prepare_test_data()
        # Initialize mocks for external dependencies
        self.mock_dependencies = self._setup_mocks()
        # Create instance of class under test (if applicable)
        self.component = self._create_test_instance()
    
    def tearDown(self) -> None:
        """Clean up after each test."""
        # Clean up resources
        self._cleanup_resources()
        # Reset test state
        self._reset_test_state()
        # Close any open connections
        if hasattr(self, 'connections'):
            for conn in self.connections:
                conn.close()
        # Clear mocks
        if hasattr(self, 'mock_dependencies'):
            for mock in self.mock_dependencies.values():
                mock.reset_mock()
    
    # Helper methods
    def _load_test_config(self) -> Dict[str, Any]:
        """Load test configuration."""
        return {
            'timeout': 120,
            'retries': 3,
            'test_mode': True
        }
    
    def _clean_test_environment(self) -> None:
        """Clean test environment."""
        # Remove test files
        # Clear test database
        # Reset global state
        pass
    
    def _prepare_test_data(self) -> Dict[str, Any]:
        """Prepare test data."""
        return {
            'valid_input': {'key': 'value'},
            'edge_cases': [None, [], '', 0, -1],
            'large_dataset': self._generate_large_dataset()
        }
    
    def _setup_mocks(self) -> Dict[str, Mock]:
        """Setup mock objects for external dependencies."""
        return {
            'database': Mock(),
            'api_client': Mock(),
            'file_system': Mock()
        }
    
    def _create_test_instance(self) -> Any:
        """Create instance of component under test."""
        # Return initialized instance
        pass
    
    def _cleanup_resources(self) -> None:
        """Clean up test resources."""
        pass
    
    def _reset_test_state(self) -> None:
        """Reset test state."""
        pass
    
    def _generate_large_dataset(self, size: int = 10000) -> List[Dict]:
        """Generate large dataset for performance testing."""
        return [{'id': i, 'data': f'item_{i}'} for i in range(size)]
    
    def _handle_test_exception(
        self,
        test_name: str,
        description: str,
        exception: Exception,
        timer: PerformanceTimer
    ) -> None:
        """Handle test exceptions uniformly."""
        elapsed = timer.stop() if timer.running else 0
        metrics = {
            "Error": str(exception),
            "Error Type": type(exception).__name__
        }
        result_text = f"Failed with error: {str(exception)}"
        print(format_console_output(
            0, test_name, description, metrics, result_text, False
        ))
        self.aggregator.add_result(
            test_name, "❌", f"{elapsed:.3f}s", metrics, False
        )
        raise


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

### 2. Basic Functionality Tests
Implement tests for normal operations:

```python
@timeout(120)
def test_01_basic_functionality(self) -> None:
    """TEST 1: Basic functionality validation."""
    test_name = "Basic Functionality Test"
    description = "Validates core feature operations under normal conditions"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        # Arrange: Prepare test inputs
        test_input = self.test_data['valid_input']
        
        # Act: Execute the operation
        result = self.component.process(test_input)
        elapsed = timer.stop()
        
        # Assert: Verify results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'success')
        
        # Metrics collection
        metrics = {
            "Test Result": "Success",
            "Processing Time": f"{elapsed:.3f}s",
            "Records Processed": str(len(result.get('data', []))),
            "Memory Usage": self._get_memory_usage(),
            "Success Rate": "100%"
        }
        
        # Pass/fail determination
        criteria = get_pass_criteria('basic_functionality')
        passed = (
            elapsed <= criteria['maximum_time']
            and result['status'] == 'success'
        )
        result_text = (
            f"Processed successfully in {elapsed:.3f}s "
            f"(threshold: <={criteria['maximum_time']}s)"
        )
        
        print(format_console_output(
            1, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, f"Test failed: {result_text}")
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 3. Edge Case Tests
Implement boundary condition tests:

```python
@timeout(60)
def test_02_edge_cases(self) -> None:
    """TEST 2: Edge case handling."""
    test_name = "Edge Case Test"
    description = "Tests boundary conditions and extreme inputs"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        edge_cases = [
            (None, "null input"),
            ([], "empty list"),
            ([None], "list with null"),
            ("", "empty string"),
            (0, "zero value"),
            (-1, "negative value"),
            (float('inf'), "infinity"),
            (float('-inf'), "negative infinity"),
            (float('nan'), "not a number"),
            (10**9, "very large number"),
            (" " * 10000, "very long string"),
            ({'nested': {'deeply': {'value': 'here'}}}, "deeply nested"),
            ({'key': None, 'key2': []}, "mixed null/empty"),
            ([0] * 10000, "large array"),
            ("unicode: 你好世界 🌍", "unicode characters")
        ]
        
        cases_passed = 0
        cases_failed = []
        
        for test_input, case_name in edge_cases:
            try:
                result = self.component.process(test_input)
                # Verify graceful handling
                if result is not None:
                    cases_passed += 1
                else:
                    cases_failed.append((case_name, "returned None"))
            except ValueError as e:
                # Expected exception for invalid input
                cases_passed += 1
            except Exception as e:
                cases_failed.append((case_name, str(e)))
        
        elapsed = timer.stop()
        
        metrics = {
            "Cases Tested": str(len(edge_cases)),
            "Cases Passed": str(cases_passed),
            "Cases Failed": str(len(cases_failed)),
            "Processing Time": f"{elapsed:.3f}s",
            "Pass Rate": f"{(cases_passed/len(edge_cases))*100:.1f}%"
        }
        
        criteria = get_pass_criteria('edge_cases')
        passed = (cases_passed / len(edge_cases)) >= criteria['minimum_pass_rate']
        result_text = f"Passed {cases_passed}/{len(edge_cases)} edge cases"
        
        if cases_failed:
            result_text += f" (Failed: {', '.join(c[0] for c in cases_failed[:3])})"
        
        print(format_console_output(
            2, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 4. Error Condition Tests
Implement exception handling tests:

```python
@timeout(60)
def test_03_error_handling(self) -> None:
    """TEST 3: Error condition handling."""
    test_name = "Error Handling Test"
    description = "Validates proper exception handling and error messages"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        error_scenarios = [
            (
                {'invalid_key': 'value'},
                KeyError,
                "missing required key"
            ),
            (
                {'value': 'invalid_type'},
                TypeError,
                "invalid type for value"
            ),
            (
                {'value': -999},
                ValueError,
                "value out of range"
            )
        ]
        
        errors_handled_correctly = 0
        
        for test_input, expected_exception, description_text in error_scenarios:
            try:
                result = self.component.process(test_input)
                # Should have raised exception
                pass
            except expected_exception as e:
                # Correct exception raised
                self.assertIn("expected_keyword", str(e).lower())
                errors_handled_correctly += 1
            except Exception as e:
                # Wrong exception type
                self.fail(
                    f"Expected {expected_exception.__name__}, "
                    f"got {type(e).__name__}: {str(e)}"
                )
        
        elapsed = timer.stop()
        
        metrics = {
            "Scenarios Tested": str(len(error_scenarios)),
            "Correctly Handled": str(errors_handled_correctly),
            "Processing Time": f"{elapsed:.3f}s"
        }
        
        passed = errors_handled_correctly == len(error_scenarios)
        result_text = (
            f"Handled {errors_handled_correctly}/{len(error_scenarios)} "
            f"error scenarios correctly"
        )
        
        print(format_console_output(
            3, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 5. Integration Tests
Implement component interaction tests:

```python
@timeout(180)
def test_04_integration(self) -> None:
    """TEST 4: Integration with external components."""
    test_name = "Integration Test"
    description = "Tests interaction with databases, APIs, and other services"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        # Mock external service responses
        self.mock_dependencies['database'].query.return_value = [
            {'id': 1, 'data': 'test'}
        ]
        self.mock_dependencies['api_client'].fetch.return_value = {
            'status': 'success',
            'data': {'value': 42}
        }
        
        # Execute integration workflow
        result = self.component.full_workflow(
            database=self.mock_dependencies['database'],
            api=self.mock_dependencies['api_client']
        )
        
        elapsed = timer.stop()
        
        # Verify interactions
        self.mock_dependencies['database'].query.assert_called_once()
        self.mock_dependencies['api_client'].fetch.assert_called()
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'completed')
        
        metrics = {
            "Database Calls": str(self.mock_dependencies['database'].query.call_count),
            "API Calls": str(self.mock_dependencies['api_client'].fetch.call_count),
            "Processing Time": f"{elapsed:.3f}s",
            "Data Consistency": "Verified",
            "Component Connectivity": "All Connected"
        }
        
        criteria = get_pass_criteria('integration')
        passed = (
            elapsed <= criteria['timeout']
            and criteria['component_connectivity']
            and criteria['data_consistency']
        )
        result_text = f"Integration completed in {elapsed:.3f}s"
        
        print(format_console_output(
            4, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

### 6. Performance Tests
Implement speed and throughput tests:

```python
@timeout(300)
def test_05_performance(self) -> None:
    """TEST 5: Performance and scalability."""
    test_name = "Performance Test"
    description = "Measures processing speed, throughput, and resource usage"
    timer = PerformanceTimer()
    timer.start()
    
    try:
        # Generate large dataset
        large_dataset = self._generate_large_dataset(size=10000)
        
        # Measure processing performance
        process_start = time.time()
        results = []
        for item in large_dataset:
            result = self.component.process(item)
            results.append(result)
        process_time = time.time() - process_start
        
        elapsed = timer.stop()
        
        # Calculate metrics
        throughput = len(large_dataset) / process_time
        avg_latency = process_time / len(large_dataset)
        memory_usage = self._get_memory_usage()
        
        metrics = {
            "Items Processed": str(len(large_dataset)),
            "Total Time": f"{process_time:.3f}s",
            "Throughput": f"{throughput:.2f} items/s",
            "Avg Latency": f"{avg_latency*1000:.2f}ms",
            "Memory Usage": memory_usage,
            "Success Rate": f"{(len(results)/len(large_dataset))*100:.1f}%"
        }
        
        criteria = get_pass_criteria('performance')
        passed = (
            throughput >= criteria['min_throughput']
            and avg_latency <= criteria['max_latency']
        )
        result_text = (
            f"Achieved {throughput:.2f} items/s throughput "
            f"(threshold: >={criteria['min_throughput']} items/s)"
        )
        
        print(format_console_output(
            5, test_name, description, metrics, result_text, passed
        ))
        self.aggregator.add_result(
            test_name, "✅" if passed else "❌",
            f"{elapsed:.3f}s", metrics, passed
        )
        self.assertTrue(passed, result_text)
        
    except Exception as e:
        self._handle_test_exception(test_name, description, e, timer)
```

**Deliverables:**
1. Complete test suite with 5-10 comprehensive tests
2. Coverage of all critical functionality
3. Edge case and error condition handling
4. Integration and performance tests
5. Proper test isolation and cleanup
6. Comprehensive metrics collection
7. Formatted output matching standards

**Success Criteria:**
- All tests run independently
- setUp and tearDown work correctly
- Proper exception handling
- Comprehensive metrics collected
- Output formatting matches specifications
- Tests complete within timeout limits
- Pass/fail criteria properly evaluated
```

## Expected Outcomes

### Test Coverage Achieved
- Basic functionality: 100% of core operations
- Edge cases: 15+ boundary conditions
- Error handling: All exception paths
- Integration: All external dependencies
- Performance: Throughput and latency metrics

### Test Quality Standards
- Independent execution (no order dependencies)
- Proper resource cleanup
- Comprehensive assertions
- Descriptive failure messages
- Detailed metrics collection

### Documentation Complete
- Module docstring with purpose and authors
- Test docstrings with clear descriptions
- Inline comments for complex logic
- Helper method documentation

## Common Testing Patterns

### Arrange-Act-Assert Pattern
```python
# Arrange: Set up test data and environment
test_input = {'key': 'value'}
expected_output = {'status': 'success'}

# Act: Execute the operation
result = component.process(test_input)

# Assert: Verify results
self.assertEqual(result, expected_output)
```

### Mock Usage Pattern
```python
# Setup mock
mock_service = Mock()
mock_service.fetch.return_value = {'data': 'test'}

# Use mock
result = component.use_service(mock_service)

# Verify mock calls
mock_service.fetch.assert_called_once_with(expected_params)
```

### Exception Testing Pattern
```python
# Test that exception is raised
with self.assertRaises(ValueError) as context:
    component.invalid_operation()

# Verify exception message
self.assertIn('expected text', str(context.exception))
```

## Next Steps
After completing test case development, proceed to Phase 3: Mock & Fixture Management.
