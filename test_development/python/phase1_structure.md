# Phase 1: Test Structure & Organization

## Objective
Establish comprehensive test infrastructure with proper organization, utilities, and configuration.

## Setup Checklist

### Directory Structure
- [ ] `tests/` directory created at project root
- [ ] `run_all_tests.py` master test runner present
- [ ] `common.py` for shared test utilities
- [ ] `test_config.py` for pass/fail criteria and settings
- [ ] Individual test suite files properly named
- [ ] `test_data/` directory for test fixtures (if needed)
- [ ] `__init__.py` files in test directories

### Test Infrastructure Components
- [ ] `TestResultAggregator` class implemented
- [ ] `PerformanceTimer` class implemented
- [ ] `format_console_output` function implemented
- [ ] `get_pass_criteria` function implemented
- [ ] `timeout` decorator implemented
- [ ] Test suite auto-discovery mechanism
- [ ] Master summary reporting

### Configuration Setup
- [ ] `SUITE_PASS_THRESHOLD` defined (default 0.80)
- [ ] `DEFAULT_TIMEOUT` defined (default 120s)
- [ ] Per-test pass criteria configured
- [ ] Verbose output settings configured
- [ ] Test execution settings defined

### Path Configuration
- [ ] Proper sys.path setup for imports
- [ ] Source code path configured
- [ ] Test utilities path configured
- [ ] Relative imports working correctly

## Detailed Setup Prompt

```
Please help me establish comprehensive test infrastructure for my Python project.

**Project Context:**
- Project name: [PROJECT_NAME]
- Source code location: src/
- Current test status: [Starting fresh / Have some tests / Refactoring existing]

**Required Test Infrastructure:**

### 1. Directory Structure
Create the following structure:
```
tests/
├── run_all_tests.py          # Master test runner
├── common.py                  # Shared utilities
├── test_config.py            # Configuration
├── test_data/                # Test fixtures
│   └── sample_data.json
└── [feature]_tests.py        # Individual test suites
```

### 2. Master Test Runner (run_all_tests.py)
Implement a master runner that:
- Auto-discovers all test suite files matching `*_tests.py`
- Executes each suite independently
- Collects and aggregates results
- Generates master summary table
- Reports overall pass/fail status
- Measures total execution time

Expected output format:
```
====================================================================================================
====================================================================================================
                              [PROJECT] - FULL TEST SUITES RUNNER
───────────────────────────────────────────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────────────────────────────────────
Full test suites execution started at: [YYYY-MM-DD HH:MM:SS]

Starting [Test Suite Name]...
[Individual suite output]

====================================================================================================
                                    COMPLETE TEST SUITES SUMMARY
───────────────────────────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────┬──────────┬────────┐
│ Test Suite                           │  Result  │ Status │
├──────────────────────────────────────┼──────────┼────────┤
│ [Suite 1]                            │   X/Y    │   ✅   │
│ [Suite 2]                            │   X/Y    │   ✅   │
└──────────────────────────────────────┴──────────┴────────┘

Test Suites Passed:   X/Y
Individual Tests:     XX/YY
Overall Pass Rate:    Z%
Suite Pass Threshold: 80%
Total Duration:       XXXX seconds

───────────────────────────────────────────────────────────────────────────────────────────────────
FINAL TESTS STATUS: ✅  with Z% overall pass rate
====================================================================================================
====================================================================================================
```

### 3. Common Utilities (common.py)
Implement the following classes and functions:

#### TestResultAggregator
```python
class TestResultAggregator:
    """Aggregates test results for summary reporting."""
    
    def __init__(self, suite_name: str):
        """Initialize aggregator with suite name."""
        self.suite_name = suite_name
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(
        self, 
        test_name: str, 
        status: str, 
        duration: str, 
        metrics: Dict[str, Any], 
        passed: bool
    ) -> None:
        """Add a test result."""
        # Store result
        # Update counters
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        # Return aggregated results
    
    def print_summary(self) -> None:
        """Print formatted summary table."""
        # Print with proper formatting
```

#### PerformanceTimer
```python
class PerformanceTimer:
    """Timer for measuring test execution time."""
    
    def __init__(self):
        """Initialize timer."""
        self.start_time = None
        self.end_time = None
        self.running = False
    
    def start(self) -> None:
        """Start the timer."""
        # Record start time
    
    def stop(self) -> float:
        """Stop timer and return elapsed time."""
        # Calculate and return duration
    
    def reset(self) -> None:
        """Reset the timer."""
        # Clear times
```

#### format_console_output
```python
def format_console_output(
    test_number: int,
    test_name: str,
    description: str,
    metrics: Dict[str, Any],
    result_text: str,
    passed: bool
) -> str:
    """
    Format test output with proper spacing and alignment.
    
    Format:
    [TEST X] [Test Name]
    ───────────────────────────────────────────────────────────────────────────────────────────────────
    Description:            [Description text]
    [Metric Name]:          [Value]
    Result:                 [Result text] ............................ ✅/❌
    """
    # Format with 100-char separator lines
    # 20-char left-aligned labels
    # Dot padding for result line
    # Return formatted string
```

### 4. Test Configuration (test_config.py)
Implement configuration with:

```python
"""Test configuration and pass/fail criteria."""

def get_pass_criteria(test_name: str) -> dict:
    """
    Get pass/fail criteria for specific test.
    
    Define criteria for different test types:
    - Basic functionality tests
    - Performance tests
    - Load/stress tests
    - Integration tests
    - Edge case tests
    """
    criteria = {
        'basic_functionality': {
            'minimum_value': 0.95,
            'maximum_time': 5.0
        },
        'performance': {
            'max_latency': 1.0,
            'min_throughput': 100,
            'max_memory_mb': 500
        },
        'load_test': {
            'concurrent_users': 100,
            'success_rate': 0.99,
            'max_response_time': 2.0
        },
        'integration': {
            'component_connectivity': True,
            'data_consistency': True,
            'timeout': 30.0
        },
        'edge_cases': {
            'minimum_pass_rate': 0.93,  # Allow some edge case failures
            'critical_cases_pass_rate': 1.0
        }
    }
    return criteria.get(test_name, {'default': True})

# Global configuration
SUITE_PASS_THRESHOLD = 0.80  # 80% of tests must pass
DEFAULT_TIMEOUT = 120  # 2 minutes per test
VERBOSE_OUTPUT = True
PARALLEL_EXECUTION = False
MAX_WORKERS = 4

# Test data paths
TEST_DATA_DIR = "test_data"
SAMPLE_DATA_FILE = "sample_data.json"
```

### 5. Timeout Decorator
Implement timeout protection:

```python
def timeout(seconds: int = 120):
    """
    Decorator to add timeout to test methods.
    
    Prevents infinite loops and hangs in test execution.
    Creates daemon thread to run test with time limit.
    """
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
```

**Deliverables:**
1. Complete test infrastructure files (run_all_tests.py, common.py, test_config.py)
2. Proper directory structure with all required folders
3. Working auto-discovery of test suites
4. Formatted output matching organizational standards
5. Configurable pass/fail criteria for different test types
6. Documentation of infrastructure components

**Success Criteria:**
- Master test runner executes without errors
- Auto-discovery finds all test suites
- Output formatting matches exact specifications
- Timeout protection works correctly
- All utility classes function properly
- Summary tables display correctly with box-drawing characters
```

## Expected Outcomes

### Infrastructure Created
- Complete test directory structure
- Master test runner with auto-discovery
- Shared utilities for all test suites
- Configurable pass/fail criteria
- Proper path configuration

### Output Format Verified
- 100-character separator lines (═ and ─)
- Box-drawing characters for tables (┌─┬─┐, ├─┼─┤, └─┴─┘)
- Proper alignment and spacing
- ✅/❌ status indicators
- ISO format timestamps

### Configuration Complete
- Test-specific pass criteria defined
- Global thresholds configured
- Timeout values set appropriately
- Verbose output enabled
- Test data paths configured

## Common Issues to Address

### Critical Setup Issues
- **Missing sys.path configuration**: Tests can't import source code
- **Incorrect auto-discovery pattern**: Test suites not found
- **Path separators**: Windows vs Unix path handling
- **Import errors**: Circular imports or missing __init__.py
- **Timeout not working**: Threading issues or incorrect implementation

### Output Formatting Issues
- **Separator length**: Not exactly 100 characters
- **Table misalignment**: Box-drawing characters not properly aligned
- **Timestamp format**: Not using ISO format YYYY-MM-DD HH:MM:SS
- **Label width**: Not exactly 20 characters
- **Dot padding**: Incorrect spacing for result lines

### Configuration Problems
- **Pass criteria too strict**: All tests failing due to unrealistic thresholds
- **Timeout too short**: Long-running tests killed prematurely
- **Missing criteria**: Tests don't have defined pass/fail conditions
- **Type mismatches**: Criteria expecting wrong data types

## Infrastructure Validation

### Verification Steps
1. **Test Auto-Discovery**:
   ```python
   # Should find all *_tests.py files
   # Should skip __init__.py and utility files
   # Should handle nested directories
   ```

2. **Import Path Verification**:
   ```python
   # Tests should import from src/ without errors
   # Common utilities should be importable
   # Test config should be accessible
   ```

3. **Output Format Check**:
   ```python
   # Run sample test
   # Verify separator lengths
   # Check table alignment
   # Validate timestamp format
   ```

4. **Timeout Functionality**:
   ```python
   # Create test that sleeps longer than timeout
   # Verify TimeoutError raised
   # Confirm daemon thread cleanup
   ```

5. **Aggregator Functionality**:
   ```python
   # Add multiple test results
   # Verify counters update correctly
   # Check summary statistics
   # Validate table generation
   ```

## Next Steps
After completing infrastructure setup, proceed to Phase 2: Test Case Development.
