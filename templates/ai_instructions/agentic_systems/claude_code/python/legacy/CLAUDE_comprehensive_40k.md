---
template_id: CLAUDE_comprehensive_40k
template_name: Python - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: claude_code
phase: python
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:

  - unity

  - cmocka

  - check
tags:

  - claude-code

  - c
---
# CLAUDE.md - Python Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for Python development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9

- **New Feature**: Sections 1-5, 7

- **Refactoring**: Sections 3, 6, 9

- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a function**: Focus sections 3, 9

- **New project**: Use sections 2, 4, 5

- **Code review**: Apply sections 3, 10

## Context-Aware Behavior
- **For small scripts**: Minimal structure

- **For libraries**: Full architecture

- **For debugging**: Focus on problem-solving

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation

- Minimal testing setup

- Focus on core functionality

### Full Mode (for new projects)
- Complete architecture

- Comprehensive testing

- Full documentation

## Claude Code Terminal Commands
- **Run tests**: `claude run tests/run_all_tests.py`

- **Format code**: `claude format src/`

- **Check style**: `claude lint src/`

- **New project**: `claude init [project-name]`

- **Install deps**: `claude install -e .[dev]`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding

- Never make assumptions about missing requirements

- Frame questions to gather specific technical requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work

- Explain implementation details, reasoning, and coding concepts

- Enable learning through understanding, not copy-paste

- Reference documentation for non-obvious concepts

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions

- Analyze problems independently

- Compare alternatives and recommend best solution

- Clearly explain reasoning and trade-offs

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity

- **Code Modification**: Edit originals, don't create '_enhanced' versions

- **Codebase Cleanup**: Remove obsolete functions

- **Refactoring**: Consolidate duplicate logic

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance

- If already optimal, confirm briefly with reasoning

### System Prompt Adherence
- **Periodically review these instructions** throughout long conversations

- Ensure compliance with all coding standards and workflows

- Reference specific sections when needed to maintain consistency

- If uncertain about a standard, explicitly consult the relevant section


# 2. Project Architecture
---

## Standard Python Application Structure

```
project_name/
├── .venv/                         # Virtual environment
├── src/                           # Main application source
│   ├── main.py                    # Entry point
│   └── core/                      # Core logic
│       ├── __init__.py
│       ├── [feature_modules].py
│       └── utils/                 # Utilities
├── gui/                           # GUI components (if applicable)
│   ├── __init__.py
│   ├── components/
│   └── assets/                    # Graphics, icons, images
├── tests/                         # Testing suite
│   ├── run_all_tests.py           # Master test runner
│   ├── common.py                  # Shared utilities
│   ├── test_config.py             # Configuration
│   └── [feature_tests]/           # Test modules
├── docs/                          # Documentation
├── CHANGELOG.md                   # Version history
├── README.md                      # Project documentation
├── DEVLOG.md                      # Development log
├── pyproject.toml                 # Configuration
├── requirements.txt               # Dependencies
└── .gitignore                     # Git ignore rules
```

## Project Initialization Sequence

1. **Create virtual environment**: `python -m venv .venv`

2. **Activate**: `.venv\Scripts\activate` (Windows) / `source .venv/bin/activate` (Unix)

3. **Create directory structure** as outlined above

4. **Create `.gitignore`** in the project root and list all files, folders, and patterns you want Git to ignore (e.g., virtual environments, caches, logs, OS files, IDE configs, and build artifacts)

5. **Create `pyproject.toml`** matching CHANGELOG version

6. **Create `CHANGELOG.md`** starting with version 0.1.0

7. **Create `README.md`** with version and features

8. **Create `DEVLOG.md`** with initial task list

9. **Create `requirements.txt`** with dependencies

## pyproject.toml Template
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "[project-name]"
version = "[version-from-changelog]"
description = "[project description]"
authors = [{name = "Benjamin Dourthe", email = "benjamin@adonamed.com"}]
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=22.0", "flake8>=4.0", "mypy>=0.950", "isort>=5.10"]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Modern Python Toolchain (2025)

### Package Management - uv

**uv** is the modern replacement for pip, pip-tools, and virtualenv (10-100x faster):

```bash
# Install uv
pip install uv

# Create project with uv
uv init my-project
cd my-project

# Add dependencies
uv add requests pandas pytest

# Add dev dependencies
uv add --dev black ruff mypy

# Install all dependencies
uv sync

# Run in isolated environment
uv run python src/main.py
uv run pytest
```

**Benefits:**

- 10-100x faster than pip

- Automatic virtual environment management

- Lock files for reproducible builds

- Compatible with pip and requirements.txt

### Code Quality - ruff

**ruff** is the modern all-in-one linter (replaces flake8, isort, pydocstyle, pyupgrade):

```bash
# Install ruff
uv add --dev ruff

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code (can replace black)
ruff format .
```

**pyproject.toml configuration:**
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

### Modern Testing Stack

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "mutmut>=3.2.0",  # Mutation testing
]
```

### Python 3.12+ Features

**Type Parameter Syntax (PEP 695):**
```python
# Old way (Python < 3.12)
from typing import TypeVar, Generic
T = TypeVar('T')

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...

# New way (Python 3.12+)
class Stack[T]:
    def push(self, item: T) -> None: ...
```

**Enhanced f-string Debugging:**
```python
value = 42
print(f"{value=}")  # Prints: value=42
```

**Better Error Messages:**
Python 3.12+ provides more detailed error messages with suggestions for common mistakes.

### Configuration: pyproject.toml Only

**Modern approach:** Single `pyproject.toml` file (NO requirements.txt, setup.py, or setup.cfg)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "Modern Python project"
authors = [{name = "Your Name", email = "you@example.com"}]
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32.0",
    "pandas>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--strict-markers --cov=src --cov-report=html --cov-report=term"
```

### Migration Path

**From old toolchain to modern:**

1. Install uv: `pip install uv`

2. Convert to pyproject.toml: `uv init` (if starting fresh)

3. Add ruff: `uv add --dev ruff`

4. Replace flake8/isort with ruff: Remove old configs

5. Update Python to 3.12+: `uv python install 3.12`

6. Remove requirements.txt: Migrate to `[project.dependencies]`


# 3. Code Standards
---

## Python Style Guidelines

### Import Organization
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

### Line Length and Formatting

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

### Code Layout Rules

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

### Comment Guidelines

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

**Examples:**
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

### Function Design Patterns

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


# 4. Documentation Standards
---

## Docstring Templates

### Complex Functions
```python
def process_user_data(data, param=None) -> List[Dict[str, Any]]:
    """
    Process and validate user records according to specified rules.

    Performs data cleaning, validation against business rules, and formatting
    for downstream processing.

    Parameters:

        - data (dict): Input data.

        - param (list, optional): Additional optional parameter.

    Returns:

        - response (DataFrame): Processed data.

    Raises:

        - ValueError: When additional parameters are malformed.

    Authors:

        - Benjamin Dourthe (benjamin@adonamed.com)
    """
```

### Simple Functions
```python
def calculate_total(items: List[float]) -> float:
    """Calculate total including tax."""
```

## README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Installation

### Prerequisites
- Python 3.9+

- [Other requirements]

### Setup
    ```bash
    git clone <REPO_URL>
    cd [project-name]
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install -e .[dev]
    ```

**Note**: Your repository URL is stored in `.git/config`. To retrieve it:

```bash
git config --get remote.origin.url
```

## Usage
    ```python
    from src.core import MainModule
    result = MainModule.process("input")
    ```

## Testing
    ```bash
    python tests/run_all_tests.py
    ```
```

## CHANGELOG.md Structure
```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements

### Fixed
- Bug fixes

### Removed
- Deprecated items
```

## DEVLOG.md Structure
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Urgent tasks

### Medium Priority
- [ ] Important enhancements

### Low Priority
- [ ] Future features

## Development History

### Project Architecture
- **Initial Design**: [Decisions]

- **Tech Stack**: [Choices]

- **Patterns**: [Applied]

### Implementation Challenges
- **Challenge X**: [Problem]

  - *Solution*: [Resolution]

  - *Trade-offs*: [Considerations]

### Technical Decisions
[Key decisions and rationale]

## Troubleshooting History
### Issue X: [Description]
- **Symptoms**: [Observed]

- **Root Cause**: [Problem]

- **Resolution**: [Fix]

- **Tests Run**: [Test details]

- **Iterations**: [Number of attempts]
```

## Documentation Best Practices

**CRITICAL: Use DEVLOG.md for ALL Development Documentation**

- **NEVER create separate markdown files** like:

  - `TROUBLESHOOTING_ISSUE.md`

  - `FIX_SUMMARY.md`

  - `NEW_FEATURE_IMPLEMENTATION.md`

  - `BUG_FIX_DETAILS.md`

  - `IMPLEMENTATION_NOTES.md`

- **ALWAYS document in DEVLOG.md**:

  - All troubleshooting steps and iterations

  - Feature implementation progress

  - Bug fixes and their resolution process

  - Test results and iterations

  - Development decisions and rationale

  - Challenges encountered and solutions

**Why DEVLOG.md Only:**

- Single source of truth for development history

- Easier to search and reference

- Prevents documentation fragmentation

- Maintains chronological development narrative

- Reduces repository clutter


# 5. Testing Framework
---

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

    - Benjamin Dourthe (benjamin@adonamed.com)
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

### test_config.py Template
```python
"""Test configuration."""

def get_pass_criteria(test_name: str) -> dict:
    """Get pass/fail criteria."""
    criteria = {
        'basic': {'minimum': 0.95, 'max_time': 5.0},
        'performance': {'max_latency': 1.0, 'min_throughput': 100},
        'stress': {'failure_tolerance': 0.01, 'recovery_time': 10.0}
    }
    return criteria.get(test_name, {'default': True})

SUITE_PASS_THRESHOLD = 0.80
DEFAULT_TIMEOUT = 120
VERBOSE_OUTPUT = True
```


# 6. Development Workflow
---

## Task Breakdown Methodology

### When to Use Task Breakdown
**Apply systematic breakdown for:**

- Projects estimated >30 minutes

- Multi-component applications

- Complex feature implementations

- Integration tasks with dependencies

- Refactoring projects

### Analysis Phase
**Always start with:**

1. **Requirements**: Identify components and dependencies

2. **Complexity**: Determine scope and challenges

3. **Prerequisites**: List setup and tools

4. **Risk**: Identify blockers and mitigation

5. **Success Metrics**: Define measurable outcomes

### Task Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope]

### Prerequisites
- [Requirements]

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Outputs]
**Time**: [15-45 min]
**Dependencies**: [Previous tasks]

**Prompt**:
    ```
    [Step-by-step instructions]
    [Expected structure]
    [Standards to follow]
    [Success criteria]
    
    Complete and pause. Confirm before proceeding.
    ```
```

### Subtask Principles
- **Self-Contained**: Independent completion

- **Clearly Defined**: Unambiguous objectives

- **Scoped**: 15-45 minutes work

- **Sequenced**: Logical progression

- **Verifiable**: Testable results

- **Documented**: Clear criteria

### Quality Gates
- [ ] Functionality verified

- [ ] Style compliance

- [ ] Documentation complete

- [ ] Tests included

- [ ] Performance acceptable

- [ ] Security checked

- [ ] Dependencies resolved

- [ ] Error handling added

## Iterative Testing Protocol

**CRITICAL: Test-Driven Problem Solving**

When implementing new features, fixing bugs, or troubleshooting issues, follow this iterative protocol:

### 1. Create Temporary Test Scripts
- Create test files in `tests/temp/` directory

- Name descriptively: `test_feature_validation.py`, `test_bug_reproduction.py`

- Write challenging tests that thoroughly validate the solution

- Include edge cases and error conditions

### 2. Implement Solution
- Write or modify code to address the issue

- Follow all code standards and best practices

- Document approach in DEVLOG.md

### 3. Run Tests and Iterate
- Execute the temporary test script

- If tests FAIL:

  - Analyze failure reasons

  - Document iteration in DEVLOG.md

  - Modify implementation

  - Repeat until tests pass

- If tests PASS:

  - Verify solution completeness

  - Proceed to cleanup

### 4. Clean Up Temporary Tests
- **Delete all files** in `tests/temp/` after successful implementation

- Move any valuable test cases to permanent test suites if needed

- Document final solution in DEVLOG.md

### Example Workflow
```markdown
## DEVLOG.md Entry

### Feature: User Authentication
**Iteration 1**: Created tests/temp/test_auth_validation.py

- Tests failed: Password validation too weak

- Solution: Enhanced regex pattern

**Iteration 2**: Re-ran tests

- Tests failed: Edge case with special characters

- Solution: Added character escaping

**Iteration 3**: Final run

- All tests passed ✅

- Deleted tests/temp/test_auth_validation.py

- Moved 3 test cases to tests/auth/test_authentication.py
```

**Benefits:**

- Ensures solutions actually work before claiming completion

- Documents the problem-solving process

- Prevents premature declarations of success

- Creates robust, well-tested code

- Maintains clean repository (no temporary test clutter)


# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Example:
```
Please run in your terminal:

1. Activate venv:
   .venv\Scripts\Activate.ps1

2. Navigate to project:
   cd [project-name]

3. Execute test:
   python tests/run_all_tests.py

4. Share any errors for assistance.
```

**Never Say:**

- "Let me run this command"

- "I'll execute this"

- "Running the application"

**Always Say:**

- "Please run this in your terminal"

- "Execute after activating venv"

- "Run and share results"

## PowerShell Syntax

```powershell
# Setup
python -m venv .venv
.venv\Scripts\Activate.ps1

# Installation
python -m pip install -e .[dev]

# Testing
python tests/run_all_tests.py

# Formatting
python -m black src/ tests/
python -m isort src/ tests/
```

## Virtual Environment

1. Create: `python -m venv .venv`

2. Activate: `.venv\Scripts\Activate.ps1` (Windows)

3. Verify: `where python`

4. Install: `python -m pip install -e .[dev]`

5. Deactivate: `deactivate`

## Package Management

- Never install globally

- Use development install: `pip install -e .[dev]`

- Keep requirements.txt updated

- Pin major versions

```powershell
# Check packages
python -m pip list

# Generate requirements
python -m pip freeze > requirements.txt

# Update package
python -m pip install --upgrade [package]
```

## Development Tools

```powershell
# Formatting
python -m black src/ tests/
python -m isort src/ tests/

# Linting
python -m flake8 src/ tests/
python -m mypy src/

# Testing
python -m pytest tests/ -v

# Coverage
python -m coverage run -m pytest
python -m coverage report
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:

- Modify CHANGELOG.md versions

- Update pyproject.toml versions

- Change README.md versions

- Create tags/releases

### Version Protocol

1. **Assess**: 
   ```
   Changes might warrant version update from X.Y.Z:

   - [List changes]

   - [Categorize as patch/minor/major]
   ```

2. **Request**: 
   ```
   Should I update to [version]?
   Or handle manually?
   ```

3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs

- **Minor (Y+1.0)**: New features

- **Major (X+1.0.0)**: Breaking changes

Example:
```
Changes include:

- Added data processing (minor)

- Fixed error handling (patch)

- Updated docs (patch)

Suggested: 1.2.0 → 1.3.0 (minor bump)
```

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Never suggest:

- `git add/commit/push`

- `git branch/merge`

- `git tag` or releases

- `git init`

### When Git Help IS Requested

```
Since you requested Git help:

1. Check status: git status

2. Stage: git add src/ tests/

3. Commit: git commit -m "Add [feature]"

4. Push: git push origin [branch]

Verify before running:

- Correct branch: git branch

- Clean state: git status

- Tests pass locally
```

### Repository Setup

For new projects:

- Include .gitignore

- Never auto-init repository

- Let user control version control

```
Project created with .gitignore.

When ready for version control:
git init
git add .
git commit -m "Initial setup"

Need Git workflow guidance?
```

## DEVLOG.md Updates

Safe to update without permission:

- Task lists

- Development history

- Challenges/solutions

- Technical decisions

- Troubleshooting

Never include:

- Commit hashes

- Git workflow assumptions

- Version control strategies

Example:
```markdown
### Implementation Challenges
- **Challenge 3**: Performance optimization

  - *Solution*: Implemented caching

  - *Trade-offs*: Memory vs speed

  - *Lessons*: Profile early
```

## Quality Assurance

Before version suggestions:

- [ ] User permission requested

- [ ] Semantic versioning applied

- [ ] Consistency checked

- [ ] Impact assessed

Before Git suggestions:

- [ ] User explicitly requested

- [ ] Context provided

- [ ] Safety warnings included

- [ ] Best practices noted


# 9. Implementation Examples
---

## Common Interaction Patterns

### Standard Code Fix Request

**User Request:**
```
"Can you fix this function?"
[Code paste]
```

**Response Structure:**

1. **Analysis and Clarification** (if needed)
   ```
   I can see the function has [specific issues]. Before fixing it, 
   I need to clarify [specific questions about requirements/context].
   ```

2. **Solution Implementation**
   ```python
   # Fixed version with improvements
   def improved_function(parameters):
       """Clear docstring explaining functionality."""
       # Implementation with best practices
       return result
   ```

3. **Explanation and Teaching**
   ```
   **Key Improvements Made:**

   - [Specific improvement 1 with reasoning]

   - [Specific improvement 2 with reasoning]
   
   **Why These Changes Work:**

   - [Educational explanation of concepts]

   - [References to Python best practices]
   ```

4. **Integration Instructions**
   ```
   **To Apply This Fix:**

   - Replace lines X-Y in your original function

   - Add the import statement at the top of your file

   - Test with [suggested test cases]
   ```

### Project Planning Request

**User Request:**
```
"I want to build a [complex application]"
```

**Response Structure:**

1. **Project Analysis**

   - Break down into main components

   - Identify technical challenges

   - Estimate complexity and timeline

2. **Architecture Recommendation**

   - Suggest standard project structure

   - Recommend technology stack

   - Propose development approach

3. **Subtask Breakdown**

   - Sequential, manageable tasks

   - Clear deliverables for each phase

   - Copy-pasteable prompts for execution

4. **Implementation Guidance**

   - Specific next steps

   - Quality checkpoints

   - Testing and validation approach

### Code Review and Enhancement

**User Request:**
```
"Please review this code for improvements"
[Code paste]
```

**Response Structure:**

1. **Current Code Assessment**

   - Identify strengths and positive aspects

   - Note areas needing improvement

   - Assess adherence to best practices

2. **Specific Improvement Recommendations**

   - Performance optimizations

   - Readability enhancements  

   - Security considerations

   - Error handling improvements

3. **Enhanced Implementation**

   - Refactored code with improvements

   - Preserved original functionality

   - Added proper documentation

4. **Educational Context**

   - Explain why changes improve the code

   - Reference relevant Python concepts

   - Provide additional learning resources

## Decision Trees for Complex Scenarios

### Import Organization Decision Matrix

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

### Error Handling Strategy Selection

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

### Function Structure Decision Guide

```
Question: How should I structure this function?

Single Responsibility?
├─ No → Break into smaller functions
│
├─ Yes → Check complexity
   │
   ├─ Simple (<10 lines)? → Keep as single function
   │
   └─ Complex (>10 lines)? → Consider helper functions
       │
       ├─ Repeated logic? → Extract to helper
       ├─ Multiple steps? → Extract each step
       └─ Complex algorithm? → Extract to private method
```

### Testing Strategy

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


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] **Functionality**: Code solves the stated problem completely

- [ ] **Style Compliance**: Follows all formatting guidelines

- [ ] **Documentation**: Includes appropriate docstrings and comments

- [ ] **Error Handling**: Includes appropriate exception handling

- [ ] **Type Hints**: Public functions include type annotations

- [ ] **Testing Considerations**: Suggests testing approach

- [ ] **Performance**: Considers efficiency implications

- [ ] **Security**: No obvious security vulnerabilities

- [ ] **Educational Value**: Explanation helps user learn

- [ ] **Best Practices**: Python conventions followed

- [ ] **Maintainability**: Easy to understand and modify

- [ ] **Dependencies**: All imports necessary and documented

## Before Delivering Project Structure
- [ ] **Standard Architecture**: Uses recommended project structure

- [ ] **Complete Setup**: All essential files included

- [ ] **Version Consistency**: Version numbers match across files

- [ ] **Documentation**: README, CHANGELOG, and DEVLOG present

- [ ] **Configuration**: Proper pyproject.toml and requirements.txt

- [ ] **Testing Framework**: Test structure and utilities included

- [ ] **Git Integration**: Appropriate .gitignore configuration

- [ ] **Virtual Environment**: Setup instructions clear

- [ ] **Dependencies**: All documented in requirements.txt

- [ ] **Examples**: Usage examples provided

- [ ] **Contributing**: Clear process for contributors

## Code Review Standards
- [ ] **Logic**: Algorithm correctness verified

- [ ] **Edge Cases**: Boundary conditions handled

- [ ] **Resources**: Files/connections properly managed

- [ ] **Memory**: Efficient usage patterns

- [ ] **Scalability**: Can handle growth requirements

- [ ] **Debugging**: Appropriate logging included

- [ ] **Reusability**: Modular function design

- [ ] **Naming**: Clear, descriptive identifiers

- [ ] **Comments**: Add value, explain reasoning

- [ ] **Coverage**: Critical paths tested

## Performance Considerations
- [ ] **Algorithms**: Optimal complexity chosen

- [ ] **Data Structures**: Appropriate for use case

- [ ] **Memory Usage**: Efficient allocation/deallocation

- [ ] **I/O Operations**: Minimized and optimized

- [ ] **Caching**: Implemented where beneficial

- [ ] **Concurrency**: Thread safety considered

- [ ] **Database**: Queries optimized

- [ ] **Network**: Minimal requests, proper handling

---