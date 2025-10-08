# Docstrings & Code Documentation

Generate comprehensive docstrings for all functions, classes, and modules following organizational templates.

---

## Overview

This review focuses on creating complete docstring documentation for your Python codebase. Docstrings are the foundation of code documentation, providing inline documentation that's accessible through Python's help system and documentation generators.

---

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown

Please help me generate comprehensive docstrings for my Python project following organizational standards.
**Project Context:**
- Project name: [YOUR_PROJECT_NAME]
- Source code location: src/
- Current documentation status: [None / Partial / Needs update]
**Documentation Requirements:**
### 1. Module-Level Docstrings
For each module file, add a comprehensive module docstring:
"""
[Module name and purpose].

[Detailed description of module's functionality and role
in the application. 2-3 sentences explaining what this
module does and why it exists.]

Key Components:
    - [Component 1]: [Brief description]
    - [Component 2]: [Brief description]
    - [Component 3]: [Brief description]

Example Usage:
    from [module] import [component]
    result = [component].method()

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
~~~

**Apply to all modules in:**
- src/core/*.py
- src/utils/*.py
- src/[other directories]/*.py

---

### 2. Class Docstrings

For each class, add comprehensive documentation:

```python
class ClassName:
    """
    [Brief one-line description].
    
    [Detailed description explaining the class's purpose,
    responsibilities, and usage patterns. 2-4 sentences.]
    
    Attributes:
        attribute1: [Description of attribute1]
        attribute2: [Description of attribute2]
        attribute3: [Description of attribute3]
    
    Example:
        ```python
        obj = ClassName(param1, param2)
        result = obj.method()
        ```
    
    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

**Document all classes including:**
- Main functionality classes
- Utility classes
- Exception classes
- Data classes

---

### 3. Simple Function Docstrings

For simple functions (< 5 lines, straightforward logic):

```python
def function_name(param: Type) -> ReturnType:
    """Brief one-line description of what function does."""
```

**Examples:**
```python
def calculate_total(items: List[float]) -> float:
    """Calculate total including tax."""

def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""

def is_valid_email(email: str) -> bool:
    """Check if email address format is valid."""
```

**Apply to:**
- Simple utility functions
- Straightforward transformations
- Basic calculations
- Format conversions

---

### 4. Complex Function Docstrings

For complex functions (> 5 lines, multiple parameters, exceptions):

```python
def function_name(
    param1: Type1,
    param2: Type2,
    param3: Optional[Type3] = None
) -> ReturnType:
    """
    [Detailed description of function purpose and behavior.
    Explain what the function does, why it exists, and any
    important details about its operation.]

    Parameters:
        - param1: [Description of param1 and its role]
        - param2: [Description of param2 and its role]
        - param3: [Description of param3, including default behavior]

    Returns:
        - [Description of return value, structure, and meaning]

    Raises:
        - ExceptionType1: [When and why this exception occurs]
        - ExceptionType2: [When and why this exception occurs]

    Example:
        ```python
        result = function_name(value1, value2)
        # result contains [description]
        ```

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

**Full Example:**
```python
def process_user_data(
    records: List[Dict[str, Any]], 
    validation_rules: Dict[str, Any],
    strict_mode: bool = True
) -> List[Dict[str, Any]]:
    """
    Process and validate user data records according to specified rules.
    
    This function performs comprehensive validation, transformation, and
    sanitization of user data records. In strict mode, any validation
    failure raises an exception. In non-strict mode, invalid records
    are logged and skipped.

    Parameters:
        - records: List of user data dictionaries to process
        - validation_rules: Dictionary defining validation criteria for each field
        - strict_mode: If True, raise exception on validation failure (default: True)

    Returns:
        - List of validated and processed user data dictionaries

    Raises:
        - ValueError: If validation_rules format is invalid
        - ValidationError: If strict_mode=True and validation fails
        - DataProcessingError: If data transformation fails

    Example:
        ```python
        rules = {'email': 'email_format', 'age': 'positive_integer'}
        processed = process_user_data(raw_records, rules, strict_mode=True)
        ```

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

**Apply to:**
- Business logic functions
- Data processing functions
- API integration functions
- Complex algorithms

---

### 5. Method Docstrings

For class methods, follow the same patterns as functions but consider context:

**Simple Methods:**
```python
def get_value(self) -> Any:
    """Return current value."""
```

**Complex Methods:**
```python
def process_batch(
    self,
    items: List[Any],
    callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Process a batch of items with optional callback.
    
    This method processes items in batches for efficiency,
    applying transformations and validations defined in the
    instance configuration.

    Parameters:
        - items: List of items to process
        - callback: Optional callback invoked after each item (default: None)

    Returns:
        - Dictionary containing processing results:
          - 'processed': Number of successfully processed items
          - 'failed': Number of failed items
          - 'errors': List of error messages

    Raises:
        - ValueError: If items list is empty
        - ProcessingError: If batch processing fails

    Example:
        ```python
        processor = DataProcessor(config)
        results = processor.process_batch(items, callback=log_progress)
        print(f"Processed: {results['processed']}")
        ```
    """
```

---

### 6. Property Docstrings

For properties, document both getter and setter:

```python
@property
def value(self) -> Any:
    """Current value of the property."""
    return self._value

@value.setter
def value(self, new_value: Any) -> None:
    """
    Set new value with validation.
    
    Raises:
        - ValueError: If new_value is invalid
    """
    if not self._validate(new_value):
        raise ValueError("Invalid value")
    self._value = new_value
```

---

### 7. Special Method Docstrings

Document special methods (dunder methods):

```python
def __init__(self, config: Dict[str, Any]):
    """
    Initialize processor with configuration.
    
    Parameters:
        - config: Configuration dictionary with settings
    
    Raises:
        - ValueError: If config is missing required keys
    """

def __str__(self) -> str:
    """Return string representation for display."""

def __repr__(self) -> str:
    """Return detailed string representation for debugging."""

def __enter__(self):
    """Enter context manager, establish resources."""

def __exit__(self, exc_type, exc_val, exc_tb):
    """Exit context manager, cleanup resources."""
```

---

### 8. Exception Class Docstrings

Document custom exceptions:

```python
class ValidationError(Exception):
    """
    Raised when data validation fails.
    
    This exception is raised during data validation when input
    data does not meet required criteria or format specifications.
    
    Attributes:
        message: Error message describing validation failure
        errors: List of specific validation errors
        field: Name of field that failed validation (if applicable)
    
    Example:
        ```python
        raise ValidationError(
            "Validation failed",
            errors=['Invalid email format'],
            field='email'
        )
        ```
    """
    
    def __init__(
        self,
        message: str,
        errors: Optional[List[str]] = None,
        field: Optional[str] = None
    ):
        """
        Initialize validation error.
        
        Parameters:
            - message: Error message
            - errors: List of specific errors (optional)
            - field: Field name that failed (optional)
        """
        super().__init__(message)
        self.errors = errors or []
        self.field = field
```

---

## Guidelines

### Docstring Style
- Use triple double quotes: `"""`
- First line should be brief summary (< 80 chars)
- Blank line after summary for multi-line docstrings
- Use active voice: "Calculate total" not "Calculates total"
- Be specific and descriptive

### When to Use Simple vs Complex Templates

**Simple Template:**
- Function/method < 5 lines
- Single purpose, obvious behavior
- No exceptions raised
- 0-2 simple parameters
- Straightforward return value

**Complex Template:**
- Function/method > 5 lines
- Multiple parameters
- Raises exceptions
- Complex return values
- Non-obvious behavior
- Business logic or algorithms

### Parameter Documentation
- Describe purpose and role, not just type
- Note default values and their meaning
- Explain constraints or valid ranges
- Mention if parameter is modified

### Return Value Documentation
- Describe structure and meaning
- Explain what values mean in context
- Note possible variations (None, empty, etc.)

### Exception Documentation
- List all exceptions that can be raised
- Explain conditions that trigger each
- Include exceptions from called functions if relevant

### Examples in Docstrings
- Include for non-obvious usage
- Show typical use case
- Keep examples concise
- Use realistic variable names

---

## Deliverables

Please generate docstrings for:

1. **All module files** with module-level docstrings
2. **All classes** with comprehensive class docstrings
3. **All public functions** with appropriate template (simple or complex)
4. **All public methods** with appropriate template
5. **All properties** with getter/setter documentation
6. **All custom exceptions** with detailed documentation

**Output Format:**
- Provide updated code with docstrings added
- Group by file for easy integration
- Highlight any functions needing clarification
- Note any ambiguous behaviors requiring developer input

**Quality Checks:**
- [ ] All public APIs documented
- [ ] Complex functions use full template
- [ ] Parameters described clearly
- [ ] Return values explained
- [ ] Exceptions listed
- [ ] Examples provided where helpful
- [ ] Author attribution included

Complete and pause. Confirm all docstrings are accurate before proceeding to Phase 2.

---

## Success Criteria

- ✅ All modules have comprehensive docstrings
- ✅ All classes documented with attributes
- ✅ Simple functions use brief template
- ✅ Complex functions use detailed template
- ✅ All parameters and returns described
- ✅ All exceptions documented
- ✅ Examples included for complex functions
- ✅ Author attribution present

---

## Common Issues

### Issue: Docstring too verbose
**Solution**: Focus on essential information. Save detailed explanations for technical docs.

### Issue: Unclear parameter descriptions
**Solution**: Describe purpose and role, not just type. Explain what parameter controls or represents.

### Issue: Missing exception documentation
**Solution**: Review function body for all `raise` statements and called functions.

### Issue: No usage examples
**Solution**: Add examples for functions with non-obvious usage or complex parameters.

---

## Next Steps

After completing Phase 1, proceed to:
- **Phase 2**: Add strategic code comments explaining logic and decisions
- **Phase 3**: Create user-facing documentation (README, guides)
