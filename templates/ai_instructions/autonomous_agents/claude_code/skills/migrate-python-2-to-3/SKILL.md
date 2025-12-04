---
template_id: SKILL
template_name: Migrate-Python-2-To-3 - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: migrate-python-2-to-3
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:
  - skills
  - generic
---
# migrate-python-2-to-3

---
category: migration-refactoring
priority: MEDIUM
languages: [python]
requires_user_input: true
estimated_duration: 2-6 hours
---

## Overview

Systematically migrate Python 2 codebase to Python 3, handling syntax changes, library updates, and modernization opportunities while maintaining functionality.

## When to Use This Skill

- Migrating legacy Python 2 applications to Python 3
- Modernizing codebases that need Python 3 features
- Preparing projects for Python 2 end-of-life
- Upgrading applications to use latest libraries
- Converting projects to support type hints and async/await

## Prerequisites

- Python 2 and Python 3 installed for comparison testing
- Comprehensive test suite (recommended)
- Version control with clean working directory
- Backup of original codebase
- List of all dependencies and their Python 3 compatibility

## Step-by-Step Instructions

### Phase 1: Assessment and Planning

#### Step 1: Analyze Current Codebase

```bash
# Find all Python files
find . -name "*.py" -type f > python_files.txt

# Count lines of code
find . -name "*.py" -exec wc -l {} + | tail -1

# Check Python version requirements
python2 --version
python3 --version
```

**Create migration inventory:**

```python
"""
Migration Assessment Report

Project: [project_name]
Total Python files: [count]
Total lines of code: [count]
Current Python version: 2.7.x
Target Python version: 3.9+

Critical Dependencies:
- [dependency]: Python 3 compatible? [yes/no]
- [dependency]: Alternative needed? [yes/no]

High-Risk Areas:
- Unicode/string handling
- Dictionary iteration
- Integer division
- Print statements
- Exception syntax

Estimated Migration Time: [hours]
"""
```

#### Step 2: Check Dependency Compatibility

```bash
# Install caniusepython3
pip install caniusepython3

# Check if dependencies support Python 3
caniusepython3 -r requirements.txt

# List outdated packages
pip list --outdated
```

**Document findings:**

```markdown
## Dependency Migration Plan

### Compatible Dependencies
| Package | Python 2 Version | Python 3 Version | Action |
|---------|-----------------|------------------|--------|
| requests | 2.25.1 | 2.31.0 | Update |
| numpy | 1.16.6 | 1.24.3 | Update |

### Incompatible Dependencies
| Package | Python 2 Version | Alternative | Notes |
|---------|-----------------|-------------|-------|
| MySQL-python | 1.2.5 | PyMySQL/mysqlclient | Drop-in replacement |
| pycrypto | 2.6.1 | pycryptodome | Modern fork |

### Dependencies Requiring Code Changes
- ConfigParser → configparser (module renamed)
- urllib2 → urllib.request (restructured)
- StringIO → io.StringIO (moved)
```

#### Step 3: Run 2to3 Analysis

```bash
# Analyze without making changes
python3 -m lib2to3 --print-function .

# Generate detailed diff
python3 -m lib2to3 -w -n . > migration_changes.diff

# Save original files
python3 -m lib2to3 . --output-dir=migrated_code
```

**Review 2to3 suggested changes:**

Common transformations:
- `print` statements → `print()` function
- `xrange()` → `range()`
- `dict.iteritems()` → `dict.items()`
- `unicode()` → `str()`
- Exception syntax: `except E, e:` → `except E as e:`
- Integer division: `/` → `//` (when needed)

### Phase 2: Automated Migration

#### Step 4: Apply Safe Automatic Changes

**Strategy: Incremental migration**

```bash
# Create migration branch
git checkout -b python3-migration

# Apply print function transformation
python3 -m lib2to3 -f print -w .

# Test after each transformation
python3 -m pytest tests/

# Commit after successful tests
git add .
git commit -m "Convert print statements to print() function"
```

**Apply transformations incrementally:**

```bash
# 1. Print function
python3 -m lib2to3 -f print -w .

# 2. Import fixes
python3 -m lib2to3 -f imports -f imports2 -w .

# 3. Exception handling
python3 -m lib2to3 -f except -w .

# 4. Dictionary methods
python3 -m lib2to3 -f dict -w .

# 5. Iterator methods
python3 -m lib2to3 -f itertools -f itertools_imports -w .

# 6. Type conversions
python3 -m lib2to3 -f types -w .

# 7. All remaining fixes
python3 -m lib2to3 -w .
```

#### Step 5: Update Import Statements

**Before (Python 2):**

```python
import ConfigParser
import urllib2
import urlparse
from StringIO import StringIO
import cPickle as pickle
import Queue
import thread
import __builtin__
```

**After (Python 3):**

```python
import configparser
import urllib.request
import urllib.parse
from io import StringIO
import pickle
import queue
import _thread
import builtins
```

**Use compatibility library (six) for dual support:**

```python
import six
from six.moves import configparser
from six.moves.urllib.request import urlopen
from six.moves import queue

# String type checking
if six.PY2:
    string_types = basestring
else:
    string_types = str

# Check if item is string
if isinstance(value, string_types):
    process(value)
```

### Phase 3: Manual Code Updates

#### Step 6: Fix String and Unicode Handling

**Python 2 vs Python 3 strings:**

```python
# Python 2
regular_string = "Hello"          # bytes
unicode_string = u"Hello"         # unicode
byte_string = b"Hello"            # bytes (2.6+)

# Python 3
regular_string = "Hello"          # str (unicode)
byte_string = b"Hello"            # bytes

# Migration strategy
# BEFORE (Python 2)
def process_text(text):
    if isinstance(text, unicode):
        text = text.encode('utf-8')
    return text.upper()

# AFTER (Python 3)
def process_text(text):
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    return text.upper()
```

**File I/O changes:**

```python
# Python 2 - binary mode by default
with open('file.txt', 'r') as f:
    data = f.read()  # Returns bytes

# Python 3 - text mode by default with encoding
with open('file.txt', 'r', encoding='utf-8') as f:
    data = f.read()  # Returns str

# For binary data
with open('image.png', 'rb') as f:
    data = f.read()  # Returns bytes in both versions

# Migration example
# BEFORE
def read_config(filename):
    with open(filename) as f:
        return f.read()

# AFTER
def read_config(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()
```

#### Step 7: Update Dictionary Iteration

**Python 2 dictionary methods:**

```python
# Python 2
d = {'a': 1, 'b': 2, 'c': 3}

# Returns lists
keys = d.keys()           # ['a', 'b', 'c']
values = d.values()       # [1, 2, 3]
items = d.items()         # [('a', 1), ('b', 2), ('c', 3)]

# Returns iterators (Python 2.7+)
keys_iter = d.iterkeys()
values_iter = d.itervalues()
items_iter = d.iteritems()
```

**Python 3 dictionary methods:**

```python
# Python 3
d = {'a': 1, 'b': 2, 'c': 3}

# Returns view objects (dict_keys, dict_values, dict_items)
keys = d.keys()           # dict_keys(['a', 'b', 'c'])
values = d.values()       # dict_values([1, 2, 3])
items = d.items()         # dict_items([('a', 1), ('b', 2), ('c', 3)])

# No iterkeys/itervalues/iteritems - use keys/values/items directly
```

**Migration patterns:**

```python
# Pattern 1: Need list? Convert explicitly
# BEFORE
for key in d.keys():  # Returns list in Py2
    if key in other_dict:
        process(key)

# AFTER
for key in list(d.keys()):  # Convert to list if needed
    if key in other_dict:
        process(key)

# Better: Direct iteration (works in both)
for key in d:
    if key in other_dict:
        process(key)

# Pattern 2: Multiple iterations
# BEFORE
keys = d.iterkeys()  # Iterator in Py2

# AFTER
keys = iter(d.keys())  # Convert to iterator if needed
# Or just iterate directly: for key in d:

# Pattern 3: Dictionary iteration in loops
# BEFORE
for k, v in d.iteritems():
    print k, v

# AFTER
for k, v in d.items():
    print(k, v)
```

#### Step 8: Fix Integer Division

```python
# Python 2 behavior
result = 5 / 2      # Returns 2 (integer division)
result = 5.0 / 2    # Returns 2.5 (float division)
result = 5 // 2     # Returns 2 (floor division)

# Python 3 behavior
result = 5 / 2      # Returns 2.5 (true division)
result = 5 // 2     # Returns 2 (floor division)

# Migration strategies
# Strategy 1: Use future import for Python 2 compatibility
from __future__ import division

# Strategy 2: Update division operations
# BEFORE
def calculate_average(total, count):
    return total / count  # Integer division in Py2

# AFTER
def calculate_average(total, count):
    return total / count  # True division in Py3
    # Or use // for floor division if that's desired

# Strategy 3: Be explicit
def integer_divide(a, b):
    return a // b  # Works same in both versions

def float_divide(a, b):
    return float(a) / float(b)  # Works in both versions
```

#### Step 9: Update Exception Handling

```python
# Python 2 syntax
try:
    risky_operation()
except ValueError, e:  # Comma syntax
    print "Error:", e
except (TypeError, KeyError), e:  # Multiple exceptions
    print "Type or Key error"
finally:
    cleanup()

# Python 3 syntax
try:
    risky_operation()
except ValueError as e:  # 'as' keyword
    print("Error:", e)
except (TypeError, KeyError) as e:  # Multiple exceptions
    print("Type or Key error")
finally:
    cleanup()

# Raising exceptions
# Python 2
raise ValueError, "Invalid value"
raise ValueError("Invalid value")  # Also works

# Python 3 (only this form)
raise ValueError("Invalid value")

# Re-raising with context
# Python 2
try:
    operation()
except Exception as e:
    raise CustomError("Failed"), None, sys.exc_info()[2]

# Python 3
try:
    operation()
except Exception as e:
    raise CustomError("Failed") from e
```

### Phase 4: Modernization

#### Step 10: Add Type Hints

```python
# Basic type hints (Python 3.5+)
from typing import List, Dict, Optional, Union, Tuple, Set

def process_items(items: List[str], count: int = 10) -> Dict[str, int]:
    """Process items and return frequency dictionary."""
    result: Dict[str, int] = {}
    for item in items[:count]:
        result[item] = result.get(item, 0) + 1
    return result

# Complex type hints
from typing import Callable, Any, TypeVar, Generic

T = TypeVar('T')

class DataProcessor(Generic[T]):
    """Generic data processor."""

    def __init__(self, transformer: Callable[[T], T]) -> None:
        self.transformer = transformer

    def process(self, items: List[T]) -> List[T]:
        return [self.transformer(item) for item in items]

# Optional and Union types
def find_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Find user by ID, returns None if not found."""
    # Implementation
    return None

def parse_value(value: Union[int, str]) -> int:
    """Parse value as integer."""
    if isinstance(value, str):
        return int(value)
    return value
```

#### Step 11: Use Modern String Formatting

```python
# Old style (works in both)
message = "Hello %s, you have %d messages" % (name, count)

# format() method (Python 2.6+)
message = "Hello {}, you have {} messages".format(name, count)
message = "Hello {name}, you have {count} messages".format(name=name, count=count)

# f-strings (Python 3.6+) - RECOMMENDED
message = f"Hello {name}, you have {count} messages"

# Complex f-string examples
user = {'name': 'Alice', 'age': 30}
info = f"User {user['name']} is {user['age']} years old"

# With expressions
total = f"Total: ${sum(prices):.2f}"

# With format specifiers
value = 42.123456
formatted = f"Value: {value:>10.2f}"  # Right-align, 2 decimals
```

#### Step 12: Implement Async/Await (Optional)

```python
# Converting callback-based code to async/await
# BEFORE (synchronous or callback-based)
def fetch_data(url):
    response = requests.get(url)
    return response.json()

def process_multiple_urls(urls):
    results = []
    for url in urls:
        data = fetch_data(url)
        results.append(data)
    return results

# AFTER (async/await - Python 3.5+)
import asyncio
import aiohttp

async def fetch_data(session, url):
    async with session.get(url) as response:
        return await response.json()

async def process_multiple_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Run async function
results = asyncio.run(process_multiple_urls(urls))

# More complex async patterns
async def process_with_semaphore(urls, max_concurrent=5):
    """Limit concurrent requests."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_limited(url):
        async with semaphore:
            return await fetch_data(session, url)

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_limited(url) for url in urls]
        return await asyncio.gather(*tasks)
```

### Phase 5: Testing and Validation

#### Step 13: Run Comprehensive Tests

```bash
# Install Python 3 test dependencies
pip3 install -r requirements-test.txt

# Run test suite
python3 -m pytest tests/ -v --cov=src --cov-report=html

# Run with multiple Python versions using tox
cat > tox.ini << EOF
[tox]
envlist = py36,py37,py38,py39

[testenv]
deps = pytest
       pytest-cov
commands = pytest tests/ -v
EOF

tox

# Compare test results between Python 2 and 3
python2 -m pytest tests/ > py2_results.txt
python3 -m pytest tests/ > py3_results.txt
diff py2_results.txt py3_results.txt
```

#### Step 14: Manual Testing and Validation

```python
"""
Manual Testing Checklist

1. Core Functionality
   - [ ] Main workflows execute correctly
   - [ ] Data processing produces same results
   - [ ] API endpoints respond as expected
   - [ ] Database operations work correctly

2. Edge Cases
   - [ ] Empty input handling
   - [ ] Large dataset processing
   - [ ] Concurrent operations
   - [ ] Error conditions

3. Integration Points
   - [ ] External API calls
   - [ ] File system operations
   - [ ] Database connections
   - [ ] Third-party libraries

4. Performance
   - [ ] Response times acceptable
   - [ ] Memory usage reasonable
   - [ ] No resource leaks
   - [ ] Comparable to Python 2 version

5. Data Integrity
   - [ ] Unicode data handled correctly
   - [ ] Binary data preserved
   - [ ] File encoding correct
   - [ ] Database encoding correct
"""

# Create validation script
def validate_migration():
    """Run validation checks after migration."""
    import sys
    import json

    print(f"Python version: {sys.version}")

    # Test 1: String handling
    test_string = "Hello 世界"
    assert isinstance(test_string, str)
    assert len(test_string.encode('utf-8')) > len(test_string)
    print("✓ String handling correct")

    # Test 2: Division
    assert 5 / 2 == 2.5
    assert 5 // 2 == 2
    print("✓ Division behavior correct")

    # Test 3: Dictionary iteration
    d = {'a': 1, 'b': 2}
    keys = d.keys()
    assert not isinstance(keys, list)
    print("✓ Dictionary views working")

    # Test 4: Exception handling
    try:
        raise ValueError("test")
    except ValueError as e:
        assert str(e) == "test"
    print("✓ Exception handling correct")

    # Test 5: Import checks
    import configparser
    import urllib.request
    from io import StringIO
    print("✓ All imports successful")

    print("\n✅ All validation checks passed!")

if __name__ == '__main__':
    validate_migration()
```

#### Step 15: Performance Comparison

```python
import timeit
import sys
import statistics

def benchmark_migration():
    """Compare performance between Python 2 and 3."""

    results = {}

    # Test 1: Dictionary iteration
    setup = "d = {i: i*2 for i in range(10000)}"

    test_keys = "list(d.keys())"
    time_keys = timeit.timeit(test_keys, setup, number=1000)
    results['dict_keys'] = time_keys

    test_items = "list(d.items())"
    time_items = timeit.timeit(test_items, setup, number=1000)
    results['dict_items'] = time_items

    # Test 2: String operations
    setup = "s = 'test string' * 1000"
    test_str = "s.upper()"
    time_str = timeit.timeit(test_str, setup, number=1000)
    results['string_ops'] = time_str

    # Test 3: List comprehensions
    test_comp = "[i*2 for i in range(1000)]"
    time_comp = timeit.timeit(test_comp, number=1000)
    results['list_comp'] = time_comp

    print(f"\nPerformance Benchmark (Python {sys.version_info.major}.{sys.version_info.minor})")
    print("=" * 60)
    for test, time in results.items():
        print(f"{test:20} {time:10.6f} seconds")

    return results

if __name__ == '__main__':
    benchmark_migration()
```

### Phase 6: Deployment and Documentation

#### Step 16: Update Configuration and Documentation

```python
# Update setup.py
setup(
    name='your_package',
    version='2.0.0',
    python_requires='>=3.6',  # Specify Python 3 requirement
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    # ... rest of setup
)
```

```yaml
# Update .travis.yml or GitHub Actions
language: python
python:
  - "3.6"
  - "3.7"
  - "3.8"
  - "3.9"

install:
  - pip install -r requirements.txt
  - pip install -r requirements-test.txt

script:
  - pytest tests/ -v --cov=src
```

```markdown
# Update README.md

## Python 3 Migration

This project has been migrated from Python 2 to Python 3.

### Breaking Changes
- Minimum Python version: 3.6+
- New dependency: [package] (replaces [old_package])
- API changes: [list specific changes]

### Migration Guide for Users
1. Update Python to 3.6 or higher
2. Update dependencies: `pip install -r requirements.txt`
3. Review [MIGRATION.md] for API changes
4. Run tests to verify compatibility

### For Developers
- See [MIGRATION.md] for complete migration details
- All new code must use Python 3 features
- Type hints are encouraged
- Use f-strings for formatting
```

## Expected Outcomes

After completing this migration:

1. **Codebase fully Python 3 compatible**
   - All syntax updated to Python 3
   - Dependencies compatible with Python 3
   - Tests passing on Python 3.6+

2. **Modern Python features available**
   - Type hints for better IDE support
   - Async/await for concurrent operations
   - f-strings for readable formatting
   - Modern standard library modules

3. **Improved code quality**
   - Explicit string/byte handling
   - Consistent exception handling
   - Better Unicode support
   - Cleaner syntax

4. **Future-proof codebase**
   - Compatible with latest Python versions
   - Access to new language features
   - Security updates and support
   - Better performance characteristics

## Success Criteria

- [ ] All Python 2 syntax replaced with Python 3
- [ ] All imports updated to Python 3 modules
- [ ] String/byte handling corrected throughout
- [ ] Integer division behavior verified
- [ ] Exception handling uses 'as' keyword
- [ ] All tests passing on Python 3.6+
- [ ] No Python 2 dependencies remaining
- [ ] Documentation updated with Python 3 requirements
- [ ] Performance comparable or better than Python 2
- [ ] Type hints added to public APIs (optional)
- [ ] CI/CD updated for Python 3
- [ ] Deployment scripts updated

## Common Pitfalls

1. **Incomplete string/byte conversion**
   - Problem: Mixing str and bytes types
   - Solution: Be explicit about encoding/decoding

2. **Dictionary iteration assumptions**
   - Problem: Code assumes lists from .keys()/.values()
   - Solution: Convert to list explicitly if needed

3. **Integer division surprises**
   - Problem: Expected integer division, got float
   - Solution: Use // for floor division

4. **Dependency incompatibility**
   - Problem: Old package doesn't support Python 3
   - Solution: Find maintained alternative or fork

5. **File encoding issues**
   - Problem: Files opened without encoding specification
   - Solution: Always specify encoding='utf-8'

## Related Skills

- **dependency-upgrade**: Upgrade project dependencies safely
- **setup-python-project**: Initialize new Python projects
- **add-typing**: Add type hints to Python code
- **refactor-for-testability**: Improve code testability
- **code-complexity-analysis**: Analyze and reduce complexity

## Additional Resources

### Official Documentation
- [Python 3 What's New](https://docs.python.org/3/whatsnew/)
- [Porting Python 2 to Python 3](https://docs.python.org/3/howto/pyporting.html)
- [2to3 Documentation](https://docs.python.org/3/library/2to3.html)

### Tools
- [python-modernize](https://github.com/PyCQA/modernize)
- [six](https://six.readthedocs.io/)
- [python-future](http://python-future.org/)
- [caniusepython3](https://pypi.org/project/caniusepython3/)

### Migration Guides
- [Conservative Python 3 Porting Guide](https://portingguide.readthedocs.io/)
- [The Hitchhiker's Guide to Python 3](https://python-3-patterns-idioms-test.readthedocs.io/)
- [Dropping Python 2 Support](https://python3statement.org/)

### Best Practices
- [PEP 8 - Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 3107 - Function Annotations](https://www.python.org/dev/peps/pep-3107/)

---

**Note**: This migration process can be time-consuming for large codebases. Plan for adequate testing time and consider running Python 2 and Python 3 versions in parallel during the transition period.
