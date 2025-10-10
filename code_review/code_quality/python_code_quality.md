# Python Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to Python best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── code_quality/
    ├── code_quality_report.md
    ├── code_quality_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:

- Create `review/code_quality/` directory in repository root if it doesn't exist

- All review outputs (reports, findings, scripts, data) go in the phase-specific directory

**Expected Outputs**:

- `code_quality_report.md` - Main findings and recommendations

- `code_quality_findings.json` - Structured data for tooling integration

- `analysis_scripts/` - Any scripts generated during analysis

- `supporting_data/` - Raw data, logs, profiling results, scan outputs

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

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Code Quality Review

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
    rev: 24.1.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p review/code_quality/analysis_scripts
mkdir -p review/code_quality/supporting_data
```

**Save files as follows**:

- Main report → `review/code_quality/code_quality_report.md`

- Findings data → `review/code_quality/code_quality_findings.json`

- Analysis scripts → `review/code_quality/analysis_scripts/`

- Supporting data → `review/code_quality/supporting_data/`
~~~
