# Test Generation Command

Generate comprehensive tests for the specified code.

## Test Generation Process

1. **Analyze the Code**
   - Identify all public functions/methods
   - Note input parameters and return types
   - Identify dependencies and side effects

2. **Create Test Categories**
   - **Happy Path**: Normal operation tests
   - **Edge Cases**: Boundary conditions
   - **Error Cases**: Exception handling
   - **Integration**: Component interactions

3. **Generate Test File**
   - Create in `tests/temp/` for validation first
   - Follow project testing framework conventions
   - Include proper setup and teardown

## Test Template
```python
"""
Test suite for [module/function name].

Tests cover normal operations, edge cases, and error conditions.
"""
import pytest
from src.[module] import [function_or_class]


class Test[ClassName]:
    """Tests for [ClassName]."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

    def test_[happy_path_scenario](self):
        """Test normal operation."""
        # Arrange
        # Act
        # Assert
        pass

    def test_[edge_case](self):
        """Test boundary condition."""
        pass

    def test_[error_case](self):
        """Test error handling."""
        with pytest.raises([ExpectedException]):
            pass
```

## Arguments
If `$ARGUMENTS` is provided, generate tests for that specific file or function.
Otherwise, generate tests for the most recently discussed code.

## Output
1. Test file with comprehensive test cases
2. Instructions to run the tests
3. Expected coverage analysis
