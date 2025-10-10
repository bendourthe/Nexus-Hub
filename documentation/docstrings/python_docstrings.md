# Python Docstring Generation

## Objective
Generate comprehensive, standards-compliant docstrings for all public interfaces (modules, classes, functions) that clearly document purpose, parameters, return values, exceptions, and provide usage examples.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/docstrings/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/docstrings/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Module-Level Documentation
- [ ] Module purpose and scope clearly explained
- [ ] Key classes and functions listed
- [ ] Dependencies and requirements noted
- [ ] Usage examples provided for module imports
- [ ] Author information included

### Class Documentation
- [ ] Class purpose and responsibility documented
- [ ] All public attributes described with types
- [ ] Constructor parameters documented
- [ ] Class-level examples provided
- [ ] Inheritance relationships explained

### Function/Method Documentation
- [ ] Function purpose clearly stated
- [ ] All parameters documented with types and descriptions
- [ ] Return values documented with types
- [ ] Exceptions raised documented
- [ ] Side effects and state changes noted
- [ ] Usage examples for complex functions

### Type Hints Integration
- [ ] Docstrings complement (not duplicate) type hints
- [ ] Complex types explained in docstrings
- [ ] Type constraints and validation documented
- [ ] Generic type usage clarified

### Documentation Style
- [ ] Consistent style throughout codebase (Google/NumPy/Sphinx)
- [ ] Formatting conventions followed
- [ ] Code examples properly formatted
- [ ] Cross-references to related functions/classes

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Docstring Generation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/docstrings"
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

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please generate comprehensive docstrings for this Python project following this protocol:

## Phase 1: Analysis & Style Selection

1. **Analyze Existing Code**
   - Inventory all modules, classes, and public functions
   - Identify existing docstring patterns and style
   - Note any special documentation requirements

2. **Determine Docstring Style**
   Please use the following docstring style: [Google/NumPy/Sphinx/reStructuredText]

   If not specified, use **Google style** (most readable and widely adopted).

3. **Review Type Hints**
   - Check existing type annotations
   - Ensure docstrings complement (not duplicate) type hints
   - Document complex types requiring additional explanation

## Phase 2: Module-Level Docstrings

For each module, create comprehensive docstrings including:

### Module Docstring Template
```python
"""
[One-line summary of module purpose]

[Detailed description of module functionality, scope, and use cases.
Include key concepts, main responsibilities, and intended usage.]

Typical usage example:

    from package.module import MainClass

    instance = MainClass(param1, param2)
    result = instance.process()

Key Classes:
    - ClassName1: [Brief description]
    - ClassName2: [Brief description]

Key Functions:
    - function_name1: [Brief description]
    - function_name2: [Brief description]

Dependencies:
    - numpy>=1.20.0: [Why it's needed]
    - requests: [What it's used for]

Authors:
    - [Name] ([email])

Version:
    [version number]

License:
    [license information]
"""
```

## Phase 3: Class Docstrings

For each class, document:

### Class Docstring Template (Google Style)
```python
class ExampleClass:
    """
    [One-line summary of class purpose]

    [Detailed description of class responsibility, behavior, and usage.
    Explain what problems this class solves and how it fits into the
    overall architecture.]

    Attributes:
        attribute_name (type): Description of what this attribute represents
            and how it's used. Can span multiple lines if needed.
        another_attr (Optional[str]): Description including default behavior.

    Example:
        Basic usage example showing common patterns:

            >>> obj = ExampleClass(param1="value")
            >>> result = obj.process()
            >>> print(result)
            'processed_value'

    Note:
        Important information about usage, limitations, or behavior.

    Warning:
        Critical warnings about misuse or edge cases.
    """
```

### Alternative: NumPy Style
```python
class ExampleClass:
    """
    [One-line summary]

    [Detailed description]

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int, optional
        Description of param2 (default is 0)

    Attributes
    ----------
    attr1 : list
        Description of attr1

    Examples
    --------
    >>> obj = ExampleClass("test", 42)
    >>> obj.process()
    'result'

    See Also
    --------
    RelatedClass : Related functionality
    """
```

## Phase 4: Function/Method Docstrings

For each function and method, document:

### Function Docstring Template (Google Style)
```python
def complex_function(param1: str, param2: int, param3: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    [One-line summary of what function does]

    [Detailed description of function behavior, algorithm, and usage.
    Explain the problem it solves and any important implementation details.]

    Args:
        param1 (str): Description of param1. Include constraints, expected
            format, or valid values. Can span multiple lines.
        param2 (int): Description of param2. Explain what the parameter
            controls or represents.
        param3 (Optional[List[str]], optional): Description of optional param.
            Defaults to None. Explain behavior when None vs when provided.

    Returns:
        Dict[str, Any]: Description of return value structure. For complex
            returns, document the dictionary keys and their meanings:
            {
                'status': str - Success/failure status
                'data': Any - The processed result
                'metadata': dict - Additional information
            }

    Raises:
        ValueError: When param1 is empty or invalid format.
        TypeError: When param2 is not an integer.
        CustomException: When [specific condition] occurs.

    Example:
        Basic usage:

            >>> result = complex_function("input", 42)
            >>> print(result['status'])
            'success'

        Advanced usage with optional parameter:

            >>> items = ["a", "b", "c"]
            >>> result = complex_function("input", 42, items)
            >>> result['data']
            ['processed_a', 'processed_b', 'processed_c']

    Note:
        This function modifies [state/global variable/etc] as a side effect.
        Consider [alternative approach] for [use case].

    See Also:
        related_function: Similar functionality with different approach
        AnotherClass.method: Used internally by this function
    """
```

### Simple Function Template
```python
def simple_function(value: int) -> int:
    """Multiply value by 2 and return result.

    Args:
        value: The integer to multiply.

    Returns:
        The value multiplied by 2.
    """
```

## Phase 5: Special Cases

### Property Docstrings
```python
@property
def computed_value(self) -> float:
    """The computed value based on internal state.

    This property calculates [description] using [method].
    Computed lazily and cached for performance.

    Returns:
        The computed float value.

    Note:
        Accessing this property triggers [side effect if any].
    """
```

### Async Function Docstrings
```python
async def async_operation(url: str) -> Dict:
    """Asynchronously fetch and process data from URL.

    This coroutine performs [description] by [method].

    Args:
        url: The endpoint URL to fetch from.

    Returns:
        Dict containing the processed response data.

    Raises:
        aiohttp.ClientError: If network request fails.
        asyncio.TimeoutError: If operation exceeds timeout.

    Example:
        >>> result = await async_operation("https://api.example.com/data")
        >>> print(result['status'])
    """
```

### Generator/Iterator Docstrings
```python
def data_generator(start: int, end: int) -> Iterator[int]:
    """Generate sequence of integers from start to end.

    Args:
        start: First integer in sequence.
        end: Last integer in sequence (inclusive).

    Yields:
        int: Next integer in the sequence.

    Example:
        >>> for num in data_generator(1, 5):
        ...     print(num)
        1
        2
        3
        4
        5
    """
```

### Decorator Docstrings
```python
def retry_on_failure(max_attempts: int = 3):
    """Decorator that retries function on failure.

    Wraps function to automatically retry up to max_attempts times
    if an exception is raised.

    Args:
        max_attempts: Maximum number of retry attempts.

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @retry_on_failure(max_attempts=5)
        ... def unstable_function():
        ...     # Function that might fail
        ...     pass
    """
```

## Phase 6: Docstring Quality Checks

Verify each docstring meets these criteria:

### Completeness
- [ ] Purpose clearly stated
- [ ] All parameters documented
- [ ] Return value documented
- [ ] Exceptions documented
- [ ] Examples provided for non-trivial functions

### Clarity
- [ ] Uses clear, concise language
- [ ] Avoids jargon or explains technical terms
- [ ] Follows consistent tense (present tense for descriptions)
- [ ] No redundant information with type hints

### Examples
- [ ] Examples are runnable (use >>> doctest format when possible)
- [ ] Examples cover common use cases
- [ ] Complex functions have multiple examples
- [ ] Examples demonstrate edge cases or important patterns

### Formatting
- [ ] Consistent style throughout codebase
- [ ] Proper indentation and line breaks
- [ ] Code blocks properly formatted
- [ ] Cross-references use proper syntax

## Phase 7: Documentation Generation

After docstrings are complete:

1. **Generate API Documentation**
   ```bash
   # Using Sphinx
   sphinx-apidoc -o docs/api src/
   sphinx-build -b html docs/ docs/_build/

   # Using pdoc
   pdoc --html --output-dir docs/ src/

   # Using pydoc
   pydoc -w module_name
   ```

2. **Verify Docstring Coverage**
   ```bash
   # Check docstring coverage
   interrogate -v src/

   # Generate coverage report
   interrogate --generate-badge docs/
   ```

3. **Run Doctests**
   ```bash
   # Test examples in docstrings
   python -m doctest src/module.py -v

   # Or using pytest
   pytest --doctest-modules src/
   ```

## Output Format

Please provide docstrings in this format:

### File-by-File Report
```markdown
## Module: src/package/module.py

### Module Docstring
[Generated module docstring]

### Class: ClassName
[Generated class docstring]

### Function: function_name
[Generated function docstring]

---
```

### Summary Report
```markdown
## Docstring Generation Summary

**Files Processed**: [count]
**Modules Documented**: [count]
**Classes Documented**: [count]
**Functions Documented**: [count]
**Properties Documented**: [count]

**Docstring Style**: [Google/NumPy/Sphinx]
**Type Hint Integration**: [Complete/Partial/None]
**Examples Added**: [count]

**Coverage Metrics**:
- Module coverage: [X%]
- Class coverage: [X%]
- Function coverage: [X%]
- Overall coverage: [X%]

**Quality Checks**:
- [ ] All public interfaces documented
- [ ] Consistent style throughout
- [ ] Examples provided where appropriate
- [ ] Type hints complemented (not duplicated)
- [ ] Doctests pass successfully
```

## Docstring Style Guide Reference

### Google Style (Recommended)
- Most readable and widely adopted
- Clear section headers (Args, Returns, Raises, etc.)
- Simple, clean formatting
- Good for both humans and documentation generators

### NumPy Style
- Popular in scientific computing
- More structured with underlines
- Better for complex mathematical functions
- Standard in NumPy, SciPy, pandas ecosystems

### Sphinx/reStructuredText Style
- Native to Sphinx documentation generator
- More verbose with directives
- Powerful cross-referencing capabilities
- Standard for large documentation projects

## Best Practices

1. **Write for Humans First**
   - Docstrings are primarily for developers, not just tools
   - Use clear, natural language
   - Explain concepts, don't just describe syntax

2. **Complement Type Hints**
   - Don't repeat type information from hints
   - Explain constraints, validation, or complex type usage
   - Document expected formats or patterns

3. **Provide Context**
   - Explain why, not just what
   - Link to related functions/classes
   - Note performance considerations or side effects

4. **Keep Examples Simple**
   - Start with basic usage
   - Add complex examples only if needed
   - Make examples copy-paste runnable

5. **Maintain Consistency**
   - Use same style throughout project
   - Follow team conventions
   - Update docstrings when code changes

## Tools & Validation

```yaml
# Recommended tools for docstring quality
tools:
  - interrogate: # Docstring coverage measurement
      threshold: 95

  - pydocstyle: # Docstring style checker
      convention: google  # or numpy, pep257

  - darglint: # Docstring/signature agreement
      strictness: full

  - sphinx: # Documentation generation
      extensions:
        - sphinx.ext.autodoc
        - sphinx.ext.napoleon  # Google/NumPy style support
        - sphinx.ext.doctest
```

## Common Mistakes to Avoid

1. **Don't duplicate type hints in prose**
   - Bad: `param1 (str): param1 is a string that...`
   - Good: `param1: The identifier used to...`

2. **Don't use imperative mood**
   - Bad: `Calculate the sum...`
   - Good: `Calculates the sum...` or `The sum of...`

3. **Don't omit important details**
   - Document side effects
   - Explain non-obvious behavior
   - Note performance implications

4. **Don't write overly verbose docstrings**
   - Be concise but complete
   - Avoid redundant phrases
   - Get to the point quickly

5. **Don't forget to update docstrings**
   - Keep in sync with code changes
   - Update examples when behavior changes
   - Remove obsolete information

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/docstrings/generated_docs
mkdir -p ${OUTPUT_DIR}/docstrings/templates
mkdir -p ${OUTPUT_DIR}/docstrings/assets
mkdir -p ${OUTPUT_DIR}/docstrings/exports
```

**Save files as follows**:


- Templates → `documentation/docstrings/templates/`

- Assets → `documentation/docstrings/assets/`

- Exports → `documentation/docstrings/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).
~~~

## Output Format Specifications

The generated docstrings should:
- Follow the selected style guide consistently (Google/NumPy/Sphinx)
- Include all required sections based on function complexity
- Provide runnable examples using doctest format where appropriate
- Complement existing type hints without redundancy
- Use clear, concise language suitable for the target audience
- Include proper cross-references to related functionality
- Pass style checkers (pydocstyle, darglint)
- Generate properly formatted API documentation (Sphinx, pdoc)
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
