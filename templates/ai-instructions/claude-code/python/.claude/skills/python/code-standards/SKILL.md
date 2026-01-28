---
name: python-code-standards
description: Python code style guidelines including import organization rules, line length and formatting, code layout rules, comment guidelines (including prohibited patterns), and function design patterns. Use when writing Python code, organizing imports, reviewing style, or asking about PEP 8 and formatting conventions.
---

# Python Code Standards

## Import Organization

**Always place imports at the top of files in this exact order:**

1. **Standard library imports** (alphabetically sorted)
2. **Third-party library imports** (grouped by functionality with headers)
3. **Local application imports** (alphabetically sorted)

**Example:**
```python
# Standard library
import functools
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Data processing
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Web framework
from flask import Flask, request, jsonify
from flask_cors import CORS

# Testing
import pytest
from unittest.mock import Mock, patch

# Local imports
from src.core.database import DatabaseManager
from src.core.processors import DataProcessor
from src.core.utils import format_response, validate_input
from src.core.validators import SchemaValidator
```

**Rules:**
- Each section separated by blank line
- Alphabetized within each section
- Never place imports inside functions/classes unless absolutely necessary for lazy loading
- Use absolute imports for local modules
- Group third-party imports by functionality with comment headers

## Line Length and Formatting

**General Rules:**
- **Standard limit**: 88 characters (Black formatter standard)
- **Acceptable exceptions**:
  - Long URLs or file paths
  - Import statements with many items
  - Complex string literals
  - Function signatures with many parameters (use multi-line format)

**Multi-line Formatting:**
```python
# Function signatures with many parameters
def complex_function(
    parameter_one: str,
    parameter_two: int,
    parameter_three: Optional[Dict[str, Any]] = None,
    parameter_four: Union[List[str], None] = None,
    parameter_five: bool = False,
) -> List[str]:
    """Function with multiple parameters properly formatted."""

# Long strings
error_message = (
    "This is a very long error message that needs to be split "
    "across multiple lines for better readability and to comply "
    "with the 88 character line length limit."
)

# Complex conditionals
if (condition_one and condition_two
    and (condition_three or condition_four)
    and not condition_five):
    process_complex_logic()

# Dictionary/List comprehensions
filtered_data = {
    key: value
    for key, value in original_data.items()
    if value > threshold and key.startswith('valid_')
}
```

## Code Layout Rules

**Function and Class Structure:**
- **One blank line** between function/method definitions
- **Two blank lines** between class definitions
- **Group related statements** closely together

### Compact Code Block Formatting

**Within functions/methods - NO empty lines between code blocks:**
- Comments should directly precede their associated code (no blank line before comment)
- Group related statements without blank line separators

**Empty lines ARE allowed:**
- **One blank line** between function/method definitions
- **Two blank lines** between class definitions
- Before/after major section headers marked with: `# ----------- #`

**Example - Preferred (compact):**
```python
def process_signals(ra_signal, la_signal, baseline_ptt, sample_rate):
    """Process and align cardiac signals."""
    # Normalize signals to 0-1 range
    ra_norm = normalize_data(ra_signal)
    la_norm = normalize_data(la_signal)
    # Apply negative PTT to align LA with RA
    la_aligned = apply_fractional_delay(la_signal, -baseline_ptt, sample_rate)
    la_aligned_norm = normalize_data(la_aligned)
    # Get cardiac cycle indices
    ra_cycles = results.loc['cycles_characteristics', ra_col]
    la_cycles = results.loc['cycles_characteristics', la_col]
    # Extract beat start indices
    ra_cycle_indices = [start for start, end in ra_cycles['indices']]
    la_cycle_indices = [start for start, end in la_cycles['indices']]
    # Calculate per-beat PTT
    per_beat_ptt_ms = []
    for ra_time in ra_beat_times_s:
        # Find closest LA beat time
        closest_idx = np.argmin([abs(la - ra_time) for la in la_beat_times_s])
        ptt_ms = (la_beat_times_s[closest_idx] - ra_time) * 1000
        per_beat_ptt_ms.append(ptt_ms)
    return per_beat_ptt_ms
```

**Example - Avoid (too many blank lines):**
```python
def process_signals(ra_signal, la_signal, baseline_ptt, sample_rate):
    """Process and align cardiac signals."""
    # Normalize signals to 0-1 range
    ra_norm = normalize_data(ra_signal)
    la_norm = normalize_data(la_signal)

    # Apply negative PTT to align LA with RA  <-- unnecessary blank line
    la_aligned = apply_fractional_delay(la_signal, -baseline_ptt, sample_rate)
```

**Class Structure Example:**
```python
class DataProcessor:
    """Process and validate data with caching."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize processor with configuration."""
        self.config = config
        self.cache = {}
        self.validator = SchemaValidator()

    def process_data(self, data: List[Dict]) -> List[Dict]:
        """Process input data efficiently."""
        cleaned_data = self._remove_nulls(data)
        normalized_data = self._normalize_values(cleaned_data)
        validated_data = self._validate_records(normalized_data)
        return validated_data

    def _remove_nulls(self, records: List[Dict]) -> List[Dict]:
        """Remove null values from records."""
        return [r for r in records if r is not None]

    def _normalize_values(self, records: List[Dict]) -> List[Dict]:
        """Normalize numerical values to standard range."""
        for record in records:
            record['value'] = float(record.get('value', 0))
            record['score'] = min(max(record.get('score', 0), 0), 100)
        return records


class ValidationError(Exception):
    """Custom exception for validation failures."""

    def __init__(self, message: str, errors: List[str]):
        """Initialize with message and error list."""
        super().__init__(message)
        self.errors = errors
```

## Comment Guidelines

**Placement and Style:**
- **Above code blocks**: Comments explain why, not just what
- **No inline comments**: Avoid same-line comments unless extremely clear and necessary
- **No meta-commentary**: Don't document editing history in comments
- **No change tracking**: Never add comments like "changed value to 12" or "updated parameter"
- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Prohibited Comment Patterns:**
```python
# BAD: Don't document changes
result = calculate(12)  # Changed from 10 to 12
value = new_value  # Updated to use new_value instead of old_value

# GOOD: Explain reasoning
result = calculate(12)  # Use 12 to match API rate limit threshold
value = new_value  # Cache invalidation requires fresh value
```

**Good Comment Examples:**
```python
# Use binary search for O(log n) performance on sorted data
# This is critical for large datasets (>10k items)
result = binary_search(sorted_list, target)

# Cache results to avoid expensive API calls during batch processing
# API rate limit is 100 calls/minute, caching prevents exceeding it
if key not in self.cache:
    self.cache[key] = expensive_api_call(key)

# Implement exponential backoff for rate-limited APIs
# Start with 1 second, double each retry up to 32 seconds max
for attempt in range(max_retries):
    wait_time = min(2 ** attempt, 32)
    time.sleep(wait_time)

# Use thread pool for I/O-bound operations
# Testing showed 4x performance improvement with 8 threads
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(process_item, item) for item in items]
```

## Function Design Patterns

**Naming Conventions:**
- **Public functions**: `snake_case` with descriptive names
- **Private functions**: `_snake_case` with underscore prefix
- **Constants**: `UPPER_CASE` with underscores
- **Classes**: `PascalCase` for all classes
- **Type aliases**: `PascalCase` for custom types

**Structure Guidelines:**
- **Single responsibility**: Each function does one thing well
- **Predictable interfaces**: Consistent parameter patterns
- **Type hints**: Use for all public functions
- **Error handling**: Explicit exception handling with meaningful messages
- **Return early**: Use guard clauses for validation
- **Default parameters**: Place after required parameters

**Example:**
```python
# Constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Type aliases
UserData = Dict[str, Any]
ProcessResult = Optional[List[UserData]]


def process_user_request(
    user_id: str,
    data: UserData,
    timeout: int = DEFAULT_TIMEOUT,
    validate: bool = True,
) -> ProcessResult:
    """
    Process a user request with optional validation.

    Parameters:
        - user_id (str): Unique user identifier
        - data (UserData): Request data to process
        - timeout (int): Request timeout in seconds
        - validate (bool): Whether to validate input

    Returns:
        - ProcessResult: Processed data or None on failure

    Raises:
        - ValueError: When user_id is empty
        - ValidationError: When data fails validation
    """
    # Guard clauses for early return
    if not user_id:
        raise ValueError("user_id cannot be empty")

    if validate and not _validate_data(data):
        raise ValidationError("Data validation failed", [])

    # Main processing logic
    result = _process_internal(user_id, data, timeout)
    return result


def _validate_data(data: UserData) -> bool:
    """Validate user data against schema."""
    required_fields = ['name', 'email']
    return all(field in data for field in required_fields)


def _process_internal(
    user_id: str,
    data: UserData,
    timeout: int,
) -> ProcessResult:
    """Internal processing implementation."""
    # Implementation details
    return [data]
```

## Decision Tree: Import Organization

```
Question: Where should this import go?

Standard Library? → Section 1 (alphabetically)
│
├─ Third-Party? → Section 2 (grouped by function)
│  │
│  ├─ Data Science? → Group with numpy, pandas
│  ├─ Web Framework? → Group with flask, django
│  └─ Testing? → Group with pytest, unittest
│
└─ Local Module? → Section 3 (alphabetically)
   │
   ├─ Core Module? → from src.core import...
   ├─ Utilities? → from src.utils import...
   └─ Tests? → from tests import...
```

## Decision Tree: Error Handling

```
Question: How should I handle this error?

Recoverable Error?
├─ Yes → Use try/except with specific exception
│  │
│  ├─ Log and continue? → Use logging with continue
│  ├─ Retry possible? → Implement retry logic
│  └─ Default value? → Return safe default
│
└─ No → Let exception propagate
   │
   ├─ Add context? → Raise new exception with context
   ├─ Clean up needed? → Use try/finally
   └─ Critical error? → Log error and exit gracefully
```
