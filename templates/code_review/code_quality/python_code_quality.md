---
template_id: python_code_quality
template_name: Code Quality - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: code_review
phase: code_quality
phase_number: 2
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:

  - code_review/context_analysis/python_context_analysis.md
related_templates:

  - code_review/security_review/python_security_review.md
tools:

  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:

  - code-review
  - python
---
# Python Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to Python best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/code_quality/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/code_quality/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Coding Standards

- [ ] PEP 8 compliance verified (line length, spacing, naming)

- [ ] Import organization follows standard order (stdlib, third-party, local)

- [ ] Docstring format consistent (Google, NumPy, or reStructuredText)

- [ ] Type hints used appropriately

- [ ] Consistent naming conventions (snake_case, PascalCase, UPPER_CASE)

### Code Complexity

- [ ] Functions under 50 lines (flagged if exceeded)

- [ ] Cyclomatic complexity under 10 per function

- [ ] Nesting depth under 4 levels

- [ ] Class size reasonable (<300 lines)

- [ ] Module cohesion evaluated

### Design & Architecture

- [ ] SOLID principles followed

- [ ] DRY principle applied (no significant duplication)

- [ ] Separation of concerns maintained

- [ ] Appropriate use of design patterns

- [ ] Dependency injection where beneficial

### Code Smells

- [ ] Long parameter lists identified (>5 parameters)

- [ ] Feature envy detected

- [ ] Shotgun surgery patterns flagged

- [ ] God classes or modules identified

- [ ] Dead code marked for removal

### Error Handling

- [ ] Exceptions caught at appropriate level

- [ ] Specific exceptions used (not bare `except:`)

- [ ] Error messages informative

- [ ] Resources properly cleaned up (context managers)

- [ ] Logging appropriate for debugging

### Maintainability

- [ ] Code self-documenting with clear names

- [ ] Comments explain "why" not "what"

- [ ] Magic numbers replaced with named constants

- [ ] Configuration externalized

- [ ] Hardcoded values eliminated

## Severity Classification

Use this framework to classify and prioritize all findings from the code quality review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- **Unhandled exceptions in critical paths** that could crash the application
- **Resource leaks** (unclosed files, database connections, memory leaks)
- **Data loss risks** (overwriting files without backup, destructive operations without confirmation)
- **Compliance violations** (GDPR violations, logging sensitive data, hardcoded secrets)
- **Thread safety issues** in concurrent code causing race conditions

**Code Example:**
```python
# CRITICAL: Resource leak - file never closed on exception
def read_config():
    f = open('config.json')  # ❌ No try/finally or context manager
    data = json.load(f)
    return data

# FIXED:
def read_config():
    with open('config.json') as f:  # ✅ Guarantees file closure
        return json.load(f)
```

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- **Incorrect business logic** (wrong calculations, flawed algorithms)
- **Performance bottlenecks** (O(n²) algorithms in hot paths, missing database indexes)
- **Memory inefficiency** (loading entire files into memory, inefficient data structures)
- **Breaking changes to public APIs** without deprecation warnings
- **Missing critical error handling** (network errors, API failures not caught)

**Code Example:**
```python
# HIGH: O(n²) performance issue
def find_duplicates(items):
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items):  # ❌ Nested loop for every item
            if i != j and item == other:
                duplicates.append(item)
    return duplicates

# FIXED: O(n) with set
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:  # ✅ Single pass
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- **High complexity** (cyclomatic complexity >10, functions >100 lines)
- **Code duplication** (>10 lines duplicated across modules)
- **Poor naming** (unclear variable/function names, inconsistent conventions)
- **Missing tests** (<80% coverage on critical paths)
- **Incomplete error messages** (no context for debugging)

**Code Example:**
```python
# MEDIUM: High complexity (cyclomatic complexity = 12)
def process_order(order, user, inventory, payment):  # ❌ Too many responsibilities
    if order.status == 'pending':
        if user.verified:
            if inventory.check_stock(order.items):
                if payment.validate():
                    if payment.charge(order.total):
                        inventory.reserve(order.items)
                        order.status = 'confirmed'
                        return True
    return False

# FIXED: Break into smaller functions
def process_order(order, user, inventory, payment):
    if not _can_process_order(order, user):  # ✅ Single responsibility
        return False
    if not _process_payment(payment, order.total):
        return False
    _fulfill_order(inventory, order)
    return True
```

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- **Style violations** (PEP 8 formatting, inconsistent quotes)
- **Minor performance optimizations** (using list comprehensions vs loops in non-critical code)
- **Missing docstrings** on private helper functions
- **Verbose code** that could be more concise
- **Debug statements** (print/console.log left in code)

**Code Example:**
```python
# LOW: Style and clarity issues
def calculate_total(items):
    total=0  # ❌ No space around =
    for item in items:
        total=total+item['price']  # ❌ Verbose
    return total

# FIXED:
def calculate_total(items):
    return sum(item['price'] for item in items)  # ✅ Concise and Pythonic
```

**Action Required:**
- Fix opportunistically during other work
- Batch with other low-priority changes
- Good for new contributors
- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**
- Issue affects **production environment** → escalate one level
- Issue affects **customer-facing features** → escalate one level
- Issue has **no workaround** → escalate one level
- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**
- Issue only in **test/development code** → de-escalate one level
- Issue has **easy workaround** → de-escalate one level
- Issue is **isolated to single module** → de-escalate one level
- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**
- Memory leak in production API endpoint: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix with code example

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/api/users.py:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades linearly with user count (currently 500ms for 10k users)
- Database connection held open unnecessarily during iteration
- High memory usage on server (50MB+ per request)

**Recommendation:**
Add database index on username field and use SQL LIKE query:
python
# Current (O(n) in Python)
users = User.query.all()
results = [u for u in users if query in u.username]

# Recommended (O(log n) in database)
results = User.query.filter(User.username.contains(query)).limit(50).all()


**Effort:** 2 hours (1 hour implementation, 1 hour testing)

**Priority:** Must fix before next release (response time SLA violation)
```

---

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Code Quality Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/code_quality"
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

## Review Protocol

Please perform a comprehensive code quality review of this Python project following this protocol:

## Phase 1: Coding Standards Assessment

1. **PEP 8 Compliance Check**
   ```bash
   # Run automated style checker
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

   # Or use pylint
   pylint src/ --exit-zero
   ```

2. **Style Violations Analysis**
   - Document most common violations
   - Identify patterns of non-compliance
   - Assess consistency across modules
   - Flag formatting inconsistencies

3. **Naming Convention Review**
   - Verify function names are descriptive and snake_case
   - Check class names use PascalCase
   - Confirm constants use UPPER_CASE
   - Identify unclear or abbreviated names

## Phase 2: Complexity Analysis

1. **Function-Level Complexity**
   ```bash
   # Calculate cyclomatic complexity
   radon cc . -a -nb

   # Generate maintainability index
   radon mi . -nb
   ```

2. **Identify Complexity Hotspots**
   - List functions with complexity >10
   - Flag functions longer than 50 lines
   - Identify deeply nested code (>4 levels)
   - Document complex conditional logic

3. **Module-Level Analysis**
   - Assess module size and cohesion
   - Identify modules with too many responsibilities
   - Check coupling between modules
   - Evaluate package organization

## Phase 3: Design Quality Review

1. **SOLID Principles**
   - **Single Responsibility**: Check if classes/functions have one clear purpose
   - **Open/Closed**: Evaluate extensibility without modification
   - **Liskov Substitution**: Review inheritance hierarchies
   - **Interface Segregation**: Check for lean interfaces
   - **Dependency Inversion**: Assess dependency on abstractions

2. **DRY Violations**
   ```bash
   # Check for code duplication
   pylint --disable=all --enable=duplicate-code . --min-similarity-lines=6
   ```
   - Identify duplicated logic
   - Find near-duplicate functions
   - Document consolidation opportunities

3. **Design Patterns**
   - Identify patterns in use (factory, singleton, strategy, etc.)
   - Assess pattern appropriateness
   - Flag pattern misuse or over-engineering
   - Suggest beneficial pattern applications

## Phase 4: Code Smell Detection

1. **Common Python Code Smells**
   - **Long Parameter Lists**: Functions with >5 parameters
   - **Long Methods**: Methods exceeding 50 lines
   - **Large Classes**: Classes with >300 lines or >20 methods
   - **Data Clumps**: Same groups of data appearing together
   - **Feature Envy**: Methods using data from other classes excessively

2. **Anti-Patterns**
   - God objects/classes
   - Spaghetti code
   - Lava flow (dead/obsolete code)
   - Copy-paste programming
   - Magic numbers and strings

3. **Python-Specific Issues**
   - Mutable default arguments
   - Bare `except:` clauses
   - Using `eval()` or `exec()`
   - Mixing tabs and spaces
   - Incorrect use of `is` vs `==`

## Phase 5: Error Handling & Robustness

1. **Exception Handling Review**
   - Check for broad exception catching
   - Verify appropriate exception types used
   - Assess error message quality
   - Review exception propagation strategy

2. **Resource Management**
   - Verify use of context managers (`with` statements)
   - Check for proper file/connection cleanup
   - Review memory management patterns
   - Identify potential resource leaks

3. **Defensive Programming**
   - Input validation assessed
   - Boundary condition handling reviewed
   - Edge case coverage evaluated
   - Fail-fast patterns identified

## Phase 6: Documentation Quality

1. **Docstring Coverage**
   ```bash
   # Check docstring coverage
   interrogate . -v
   ```
   - Measure module/class/function docstring presence
   - Assess docstring completeness
   - Verify parameter documentation
   - Check return value documentation

2. **Comment Quality**
   - Evaluate comment necessity and clarity
   - Flag commented-out code for removal
   - Check for TODO/FIXME/HACK comments
   - Verify comments explain "why" not "what"

3. **Type Hints**
   ```bash
   # Check type hint coverage
   mypy src/ --ignore-missing-imports
   ```
   - Assess type hint coverage
   - Verify type hint accuracy
   - Check for `Any` overuse
   - Review complex type annotations

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary

- **Overall Quality Score**: [A-F grade]

- **Maintainability Index**: [score]

- **Average Complexity**: [cyclomatic complexity]

- **Critical Issues**: [count]

- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance

- **PEP 8 Violations**: [count and severity]

- **Most Common Issues**:
  1. [Issue type] - [count] occurrences
  2. [Issue type] - [count] occurrences

- **Consistency Score**: [percentage]

### Complexity Analysis
**High Complexity Functions** (Cyclomatic Complexity >10):
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

**Large Files/Modules** (>300 lines):
| Module | Lines | Classes | Functions | Recommendation |
|--------|-------|---------|-----------|----------------|
| [path] | [count] | [count] | [count] | [split suggestion] |

### Design Quality Issues
1. **SOLID Violations**:
   - [Principle]: [specific examples and impact]

2. **DRY Violations**:
   - [Location]: [description of duplication]
   - **Consolidation Opportunity**: [suggestion]

3. **Missing Patterns**:
   - [Location]: [beneficial pattern suggestion]

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [file:line] | [High/Med/Low] | [details] | [suggestion] |

### Error Handling Assessment

- **Broad Exception Catching**: [count and locations]

- **Missing Resource Cleanup**: [locations]

- **Inadequate Input Validation**: [locations]

- **Poor Error Messages**: [examples]

### Documentation Score

- **Docstring Coverage**: [percentage]

- **Type Hint Coverage**: [percentage]

- **Comment Quality**: [Good/Fair/Poor]

- **Areas Needing Documentation**: [list]

### Technical Debt Summary
**Priority 1 (Critical)**: [Estimated hours]

- [Issue description and location]

**Priority 2 (High)**: [Estimated hours]

- [Issue description and location]

**Priority 3 (Medium)**: [Estimated hours]

- [Issue description and location]

**Priority 4 (Low)**: [Estimated hours]

- [Issue description and location]

### Refactoring Recommendations
1. **Immediate Actions** (within 1 sprint):
   - [Specific refactoring with location and rationale]

2. **Short-term Goals** (1-2 months):
   - [Improvement initiative with expected impact]

3. **Long-term Initiatives** (3-6 months):
   - [Strategic refactoring with business justification]

### Positive Patterns
Acknowledge what's done well:

- [Good practice observed and locations]

- [Effective pattern usage examples]

### Next Steps

- [ ] Address critical complexity hotspots

- [ ] Implement automated quality gates (linting, type checking)

- [ ] Plan refactoring sprints for high-priority technical debt

- [ ] Establish team coding standards documentation

- [ ] Set up pre-commit hooks for style enforcement

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:
```yaml
# Example .pre-commit-config.yaml
repos:

  - repo: https://github.com/psf/black
    rev: 24.12.0
    hooks:

      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:

      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: 1.13.0
    hooks:

      - id: mypy
```

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/code_quality/analysis_scripts
mkdir -p ${OUTPUT_DIR}/code_quality/supporting_data
```

**Save files as follows**:

- Main report → `review/code_quality/code_quality_report.md`

- Findings data → `review/code_quality/code_quality_findings.json`

- Analysis scripts → `review/code_quality/analysis_scripts/`

- Supporting data → `review/code_quality/supporting_data/`
~~~
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
