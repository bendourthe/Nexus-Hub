# Phase 2: Code Quality & Standards Review

## Objective
Evaluate code quality, adherence to style guidelines, and implementation of best practices.

## Review Checklist

### Import Organization
- [ ] All imports at top of files (not inside functions/classes)
- [ ] Standard library imports first (alphabetically sorted)
- [ ] Third-party imports second (grouped by functionality with headers)
- [ ] Local application imports last (alphabetically sorted)
- [ ] Each section separated by blank line
- [ ] Absolute imports used for local modules
- [ ] No unused imports

### Code Formatting
- [ ] Line length respects 88-character limit (Black standard)
- [ ] Acceptable exceptions properly handled (URLs, file paths)
- [ ] Multi-line function signatures properly formatted
- [ ] Long strings properly split across lines
- [ ] Complex conditionals properly formatted
- [ ] Dictionary/list comprehensions properly formatted

### Code Layout
- [ ] No empty lines inside function/method bodies
- [ ] One blank line between function/method definitions
- [ ] Two blank lines between class definitions
- [ ] Related statements grouped closely together
- [ ] Consistent indentation (4 spaces)

### Comment Quality
- [ ] Comments placed above code blocks
- [ ] Comments explain "why," not just "what"
- [ ] No inline comments (unless absolutely necessary)
- [ ] No meta-commentary about editing history
- [ ] Comments focus on logic, reasoning, and non-obvious behavior
- [ ] All comments add value

### Naming Conventions
- [ ] Public functions use `snake_case`
- [ ] Private functions use `_snake_case` with underscore prefix
- [ ] Constants use `UPPER_CASE`
- [ ] Classes use `PascalCase`
- [ ] Type aliases use `PascalCase`
- [ ] Descriptive, meaningful names throughout

### Function Design
- [ ] Single responsibility principle followed
- [ ] Predictable interfaces with consistent parameter patterns
- [ ] Type hints on all public functions
- [ ] Explicit error handling with meaningful messages
- [ ] Guard clauses used for validation
- [ ] Default parameters placed after required parameters
- [ ] Functions are appropriately sized (<50 lines ideally)

### Documentation
- [ ] Complex functions have comprehensive docstrings
  - Purpose description
  - Parameters documented
  - Returns documented
  - Exceptions documented
  - Author information included
- [ ] Simple functions have concise docstrings
- [ ] Classes have descriptive docstrings
- [ ] Module-level docstrings present

## Detailed Review Prompt

```
Please perform a comprehensive code quality and standards review:

**Import Organization Analysis:**
1. Check each Python file's imports:
   - Verify imports are at the top of files
   - Confirm three-section organization:
     * Standard library (alphabetically sorted)
     * Third-party (grouped by functionality with comment headers)
     * Local application (alphabetically sorted)
   - Ensure blank lines separate sections
   - Verify no unused imports
   - Check for absolute imports for local modules

Example correct format:
```python
# Standard library
import functools
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Data processing
import pandas as pd
import numpy as np

# Testing
import pytest
from unittest.mock import Mock

# Local imports
from src.core.database import DatabaseManager
from src.core.utils import format_response
```

**Code Formatting Review:**
1. Line length compliance:
   - Flag lines exceeding 88 characters (unless justified exceptions)
   - Check multi-line function signatures are properly formatted
   - Verify long strings are properly split
   - Review complex conditionals for proper formatting

2. Code layout assessment:
   - Verify no empty lines inside function bodies
   - Check one blank line between functions
   - Confirm two blank lines between classes
   - Ensure related statements are grouped together

**Comment Quality Assessment:**
1. Evaluate each comment:
   - Positioned above code blocks (not inline)
   - Explains "why" and reasoning, not obvious "what"
   - No editing history or meta-commentary
   - Adds genuine value to understanding

2. Flag problematic patterns:
   - Obvious comments that don't add value
   - Inline comments that clutter code
   - Outdated or misleading comments

**Naming Convention Audit:**
Review all identifiers for compliance:
- Functions: snake_case (public), _snake_case (private)
- Constants: UPPER_CASE
- Classes: PascalCase
- Type aliases: PascalCase
- Check for descriptive, meaningful names

**Function Design Evaluation:**
For each function, assess:
1. Single responsibility (does one thing well)
2. Type hints on public functions
3. Error handling (explicit with meaningful messages)
4. Guard clauses for validation
5. Parameter ordering (required before defaults)
6. Appropriate size and complexity

**Documentation Completeness:**
Review docstrings for:
1. Complex functions: comprehensive format with Parameters, Returns, Raises, Authors
2. Simple functions: concise purpose statement
3. Classes: clear description
4. Modules: overview docstring

**Deliverables:**
Provide a structured report with:
- Import organization issues and corrections
- Code formatting violations with specific line numbers
- Comment quality assessment with recommendations
- Naming convention violations with suggested fixes
- Function design concerns with refactoring suggestions
- Documentation gaps with priority levels
- Overall code quality score (Excellent/Good/Needs Improvement/Poor)
```

## Expected Outcomes

### Pass Criteria
- 95%+ compliance with import organization standards
- 90%+ line length compliance
- All public functions have type hints
- Meaningful docstrings on complex functions
- Consistent naming conventions throughout
- No obvious code quality issues

### Common Issues to Flag
- Imports inside functions/classes
- Inconsistent import organization
- Lines exceeding 88 characters without justification
- Missing type hints on public functions
- Inline comments cluttering code
- Inconsistent naming conventions
- Functions violating single responsibility principle
- Missing or inadequate docstrings
- Unused imports or variables

## Code Examples for Reference

### Correct Import Organization
```python
# Standard library
import functools
import os
from typing import Any, Dict, List

# Data processing
import pandas as pd
import numpy as np

# Local imports
from src.core.utils import helper_function
```

### Proper Function Documentation
```python
def process_user_data(
    records: List[Dict], 
    rules: Dict[str, Any]
) -> List[Dict]:
    """
    Process and validate records according to rules.

    Parameters:
        - records: Raw data records
        - rules: Validation rules

    Returns:
        - Processed records

    Raises:
        - ValueError: Invalid rules
        - DataError: Processing failed

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

### Correct Comment Style
```python
# Use binary search for O(log n) performance on sorted data
# This is critical for large datasets (>10k items)
result = binary_search(sorted_list, target)
```

## Next Steps
After completing this phase, proceed to Phase 3: Security & Error Handling Review.
