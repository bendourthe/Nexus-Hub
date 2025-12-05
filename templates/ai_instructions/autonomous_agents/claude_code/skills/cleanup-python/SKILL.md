---
name: cleanup-python
description: Remove dead code, consolidate duplicates, and modernize Python codebases for improved maintainability
version: 1.0.0
author: Benjamin Dourthe
language: Python
category: Code Cleanup
tags: [python, cleanup, refactoring, modernization, dead-code]
template_source: code_cleanup/python_cleanup.md
---

# Python Code Cleanup

Systematically identify and remove dead code, consolidate duplicate logic, and modernize legacy Python patterns to maintain a lean, current, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused imports, functions, classes, and modules
- Consolidate duplicate code and near-duplicate implementations
- Modernize legacy Python patterns (Python 2 to 3, old idioms to modern)
- Clean up debug statements and commented code
- Optimize import organization and code structure
- Prepare codebase for new features or refactoring
- Reduce technical debt before major releases

## What This Skill Does

This skill performs comprehensive Python code cleanup:

### 1. Dead Code Detection
- **Unused Imports**: Identifies and removes unused import statements
- **Unused Functions**: Finds functions never called in codebase
- **Unused Classes**: Detects classes without instantiation
- **Unused Variables**: Identifies variables assigned but never used
- **Unreachable Code**: Finds code after return/break/continue statements
- **Empty Blocks**: Detects empty functions, classes, or try/except blocks

### 2. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks for consolidation
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Copy-Paste Detection**: Finds code copied across modules
- **Consolidation Strategy**: Recommends refactoring approach

### 3. Code Modernization
- **Python 2 to 3**: Updates legacy Python 2 patterns
- **Type Hints**: Adds modern type annotations where missing
- **F-strings**: Converts old-style string formatting to f-strings
- **Pathlib**: Modernizes os.path to pathlib.Path
- **Context Managers**: Converts manual resource handling to with statements
- **Comprehensions**: Replaces verbose loops with list/dict/set comprehensions
- **Modern Idioms**: Applies contemporary Python patterns

### 4. Debug Statement Cleanup
- **Print Statements**: Removes debug print statements
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items
- **Import pdb**: Removes debugger imports
- **Temporary Variables**: Identifies debug-only variables

### 5. Import Organization
- **Standard Library**: Groups and sorts standard imports
- **Third-Party**: Organizes external dependencies with headers
- **Local Imports**: Structures local module imports
- **Unused Removal**: Eliminates unnecessary imports
- **Duplicate Imports**: Consolidates repeated imports

### 6. Code Simplification
- **Complex Conditionals**: Simplifies nested if/else statements
- **Excessive Nesting**: Reduces deeply nested code
- **Long Functions**: Identifies candidates for decomposition
- **Magic Numbers**: Converts literals to named constants
- **Redundant Code**: Removes unnecessary operations

## Prerequisites

- Python codebase to clean up
- Version control (git) for safe cleanup with rollback capability
- Test suite for regression verification (recommended)
- Backup of codebase or committed state

## Instructions

### Step 1: Prepare for Cleanup

1. **Commit Current State**:
   ```bash
   git add .
   git commit -m "Pre-cleanup snapshot"
   ```

2. **Create Cleanup Branch** (recommended):
   ```bash
   git checkout -b code-cleanup
   ```

3. **Run Existing Tests** (if available):
   ```bash
   pytest tests/
   # or
   python -m unittest discover
   ```

4. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-python skill to analyze and clean up this Python codebase.
Focus on:

1. Removing all unused imports and functions
2. Consolidating duplicate code
3. Modernizing to Python 3.9+ patterns
4. Removing debug statements
5. Organizing imports properly

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code with usage analysis
2. **Duplication Report** - Duplicate code locations with consolidation strategy
3. **Modernization Opportunities** - Legacy patterns to update
4. **Risk Assessment** - Impact analysis for each cleanup operation
5. **Implementation Plan** - Ordered steps with dependencies

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

The skill will execute cleanup in safe phases:

**Phase 1: Low-Risk Cleanup**
- Remove unused imports
- Clean debug print statements
- Remove commented code
- Organize imports

**Phase 2: Code Modernization**
- Update f-strings
- Apply pathlib
- Add type hints
- Modernize idioms

**Phase 3: Structural Changes**
- Consolidate duplicates
- Remove dead functions
- Simplify complex code
- Extract constants

**Phase 4: Verification**
- Run tests after each phase
- Verify no functionality changes
- Document any issues

### Step 5: Test After Cleanup

1. **Run Full Test Suite**:
   ```bash
   pytest tests/ -v
   # or
   python tests/run_all_tests.py
   ```

2. **Manual Testing** (if no automated tests):
   - Test critical user workflows
   - Verify application starts correctly
   - Check key features still work

3. **Static Analysis**:
   ```bash
   python -m flake8 src/
   python -m mypy src/
   python -m black --check src/
   ```

### Step 6: Review and Commit

1. **Review Changes**:
   ```bash
   git diff
   ```

2. **Stage and Commit** (in logical chunks):
   ```bash
   git add src/
   git commit -m "Remove unused imports and functions"

   git add src/
   git commit -m "Modernize string formatting to f-strings"

   git add src/
   git commit -m "Consolidate duplicate validation logic"
   ```

3. **Merge to Main** (when satisfied):
   ```bash
   git checkout main
   git merge code-cleanup
   git push
   ```

## Cleanup Categories and Examples

### Category 1: Unused Imports
**Before:**
```python
import os
import sys
import json
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

def process_data(data):
    return json.loads(data)
```

**After:**
```python
import json

def process_data(data):
    return json.loads(data)
```

### Category 2: Debug Statements
**Before:**
```python
def calculate_total(items):
    print(f"DEBUG: items = {items}")
    total = sum(items)
    print(f"DEBUG: total = {total}")
    return total
```

**After:**
```python
def calculate_total(items):
    return sum(items)
```

### Category 3: String Formatting Modernization
**Before:**
```python
message = "Hello, %s! You have %d messages." % (name, count)
message = "Hello, {}! You have {} messages.".format(name, count)
```

**After:**
```python
message = f"Hello, {name}! You have {count} messages."
```

### Category 4: Path Operations
**Before:**
```python
import os
config_path = os.path.join(os.path.dirname(__file__), "config", "settings.json")
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)
```

**After:**
```python
from pathlib import Path
config_path = Path(__file__).parent / "config" / "settings.json"
if config_path.exists():
    config = json.loads(config_path.read_text())
```

### Category 5: Resource Management
**Before:**
```python
f = open("data.txt", "r")
data = f.read()
f.close()
```

**After:**
```python
with open("data.txt", "r") as f:
    data = f.read()
```

### Category 6: Duplicate Code Consolidation
**Before:**
```python
def validate_user(user):
    if not user.get("name"):
        return False
    if not user.get("email"):
        return False
    if "@" not in user.get("email", ""):
        return False
    return True

def validate_admin(admin):
    if not admin.get("name"):
        return False
    if not admin.get("email"):
        return False
    if "@" not in admin.get("email", ""):
        return False
    return True
```

**After:**
```python
def validate_account(account):
    """Validate user or admin account data."""
    if not account.get("name"):
        return False
    if not account.get("email"):
        return False
    if "@" not in account.get("email", ""):
        return False
    return True

validate_user = validate_account
validate_admin = validate_account
```

## Output Structure

The skill generates organized output in `cleanup_report/`:

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md       # Reusable cleanup checklist
│   └── modernization_guide.md     # Python modernization patterns
├── assets/
│   ├── duplication_graph.png      # Visual duplication analysis
│   └── complexity_heatmap.png     # Code complexity visualization
└── exports/
    ├── cleanup_report.md           # Comprehensive cleanup report
    ├── dead_code_list.md           # Dead code candidates
    ├── duplication_analysis.md     # Duplicate code analysis
    ├── modernization_plan.md       # Modernization strategy
    └── risk_assessment.md          # Impact and risk analysis
```

## Safety Measures

### 1. Version Control Required
- Always commit before cleanup
- Create dedicated cleanup branch
- Commit changes in logical phases

### 2. Test Coverage
- Run tests before cleanup (baseline)
- Run tests after each phase
- Document any test failures immediately

### 3. Incremental Approach
- Apply changes in small batches
- Verify after each batch
- Don't proceed if tests fail

### 4. Risk Assessment
- High-risk changes reviewed manually
- Critical paths tested thoroughly
- Rollback plan documented

### 5. Documentation
- Document all changes in commit messages
- Update DEVLOG.md with cleanup history
- Note any behavioral changes

## Common Issues and Solutions

### Issue: Tests Fail After Cleanup
**Solution**:

1. Review git diff for the failing area
2. Use `git checkout -- <file>` to revert specific files
3. Re-run tests to isolate issue
4. Apply cleanup more granularly

### Issue: False Positive for "Unused" Code
**Solution**:

- Check for dynamic imports (importlib)
- Verify reflection/introspection usage
- Look for string-based references
- Keep code if uncertain

### Issue: Import Organization Breaks Code
**Solution**:

- Check for circular imports
- Verify import order dependencies
- Keep original organization if needed
- Document special requirements

### Issue: Modernization Changes Behavior
**Solution**:

- Review Python version compatibility
- Check for subtle semantic differences
- Test edge cases thoroughly
- Revert if behavior changes

## Success Criteria

After using this skill, your codebase should have:

- [ ] All unused imports removed
- [ ] No debug print statements
- [ ] No commented-out code (except strategic comments)
- [ ] Duplicate code consolidated where appropriate
- [ ] Modern Python patterns applied (f-strings, pathlib, type hints)
- [ ] Imports organized properly (stdlib → third-party → local)
- [ ] All tests passing
- [ ] Cleanup documented in DEVLOG.md
- [ ] Changes committed to version control

## Related Skills

- `setup-python-system-prompt`: Establish standards before cleanup
- `code-review-quality`: Review code quality after cleanup
- `generate-test-cases`: Create tests for newly consolidated code
- `generate-docstrings`: Document cleaned-up code

## Tools and Libraries

### Static Analysis Tools
- **flake8**: Linting and style checking
- **pylint**: Comprehensive code analysis
- **mypy**: Type checking
- **black**: Code formatting
- **isort**: Import sorting

### Duplication Detection
- **pyflakes**: Unused code detection
- **vulture**: Dead code finder
- **radon**: Code complexity metrics
- **jscpd**: Copy-paste detection

### Installation
```bash
pip install flake8 pylint mypy black isort vulture radon
```

## Additional Resources

- [Python Code Quality Tools](https://realpython.com/python-code-quality/)
- [Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html)
- [Python Anti-Patterns](https://docs.quantifiedcode.com/python-anti-patterns/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/python_cleanup.md
