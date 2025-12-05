---
name: code-review-quality
description: Systematically evaluate code maintainability, readability, and adherence to best practices - identify technical debt and complexity hotspots
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Code Review
tags: [code-review, quality, maintainability, workflow, phase-2]
priority: HIGH
based_on: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
---

# Code Review Quality Assessment

Systematically evaluate code maintainability, readability, and adherence to best practices. This skill is **Phase 2** of the complete code review workflow, identifying technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## When to Use This Skill

Use this skill as **Phase 2** after completing context analysis:

- ✅ After [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md) is complete

- ✅ Evaluating code quality for existing projects

- ✅ Identifying technical debt before major features

- ✅ Assessing maintainability for team transitions

- ✅ Pre-refactoring analysis and planning

- ✅ Establishing quality baselines and metrics

- ✅ Code ownership and responsibility assessment

- ✅ Compliance with coding standards verification

**This skill is essential when**:

- You need to quantify technical debt

- You're planning refactoring initiatives

- You want to improve code maintainability

- You're establishing quality gates for CI/CD

- You need to identify complexity hotspots

## What This Skill Does

This skill implements **Phase 2: Quality Review** of the six-phase code review workflow:

### Complete Workflow
- Phase 1: [Context Analysis](../code-review-context-analysis/SKILL.md) - Project understanding

- **Phase 2: Quality Review (This Skill)** - Code maintainability assessment

- Phase 3: [Security Review](../code-review-security/SKILL.md) - Vulnerability identification

- Phase 4: [Performance Review](../code-review-performance/SKILL.md) - Bottleneck analysis

- Phase 5: [Testing Review](../code-review-testing/SKILL.md) - Test coverage evaluation

- Phase 6: [Final Report](../code-review-final-report/SKILL.md) - Consolidated findings

## Why Quality Review Matters

**Without Quality Review**:
```
Team: *writes code without quality checks*
Code: *accumulates technical debt*
Maintenance: *becomes increasingly expensive*
Result:

- ❌ High complexity makes changes risky

- ❌ Duplicated code multiplies bugs

- ❌ Poor naming hinders understanding

- ❌ Inconsistent style wastes review time

- ❌ Technical debt compounds over time

- ❌ Developer velocity decreases
```

**With Quality Review**:
```
Team: *follows quality standards*
Code: *maintains consistent quality*
Maintenance: *stays manageable*
Result:

- ✅ Low complexity enables safe changes

- ✅ DRY principle reduces bug surface

- ✅ Clear naming aids comprehension

- ✅ Consistent style speeds reviews

- ✅ Technical debt stays controlled

- ✅ Developer velocity sustained
```

## Benefits of Quality Review

### Code Maintainability
- **Easier Changes**: Simple, well-organized code is easier to modify

- **Faster Onboarding**: New developers understand code quickly

- **Reduced Bugs**: Clear code has fewer defects

- **Lower Costs**: Less time spent on maintenance

### Technical Debt Management
- **Quantified Debt**: Know exactly what needs improvement

- **Prioritized Fixes**: Address highest-impact issues first

- **Tracked Progress**: Measure debt reduction over time

- **Prevented Accumulation**: Stop new debt from forming

### Team Productivity
- **Faster Reviews**: Consistent style speeds code review

- **Less Confusion**: Clear code needs fewer explanations

- **Better Collaboration**: Standards enable teamwork

- **Knowledge Sharing**: Readable code teaches patterns

## Prerequisites

### Required
- Completion of [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md)

- Source code access

- Static analysis tools installed

- Understanding of language-specific best practices

### Recommended
- Code style guides for the language

- Complexity analysis tools

- Code duplication detectors

- Team coding standards documentation

### Knowledge
- SOLID principles

- Design patterns

- Code smells recognition

- Refactoring techniques

- Language-specific idioms

## Instructions

### Step 1: Coding Standards Assessment

**Evaluate adherence to language-specific coding standards:**

1. **Run Automated Style Checkers**

   **Python**:
   ```bash
   # PEP 8 compliance check
   pip install flake8 pylint black

   # Check style violations
   flake8 . --count --statistics

   # Comprehensive linting
   pylint src/ --exit-zero

   # Check formatting (dry run)
   black --check .
   ```

   **JavaScript/TypeScript**:
   ```bash
   # ESLint for code quality
   npm install eslint --save-dev
   npx eslint src/

   # Prettier for formatting
   npm install prettier --save-dev
   npx prettier --check "src/**/*.{js,ts,jsx,tsx}"
   ```

   **Java**:
   ```bash
   # Checkstyle for style violations
   mvn checkstyle:check

   # PMD for code quality
   mvn pmd:pmd

   # SpotBugs for bug patterns
   mvn spotbugs:check
   ```

   **Go**:
   ```bash
   # Format check
   gofmt -l .

   # Linting
   go install golang.org/x/lint/golint@latest
   golint ./...

   # Vet for suspicious constructs
   go vet ./...
   ```

   **C/C++**:
   ```bash
   # Clang-Tidy for modernization
   clang-tidy src/*.cpp

   # Clang-Format for style
   clang-format --dry-run --Werror src/*.cpp

   # Cppcheck for static analysis
   cppcheck --enable=all --suppress=missingInclude src/
   ```

   **C#**:
   ```bash
   # StyleCop for style analysis
   dotnet build /p:EnforceCodeStyleInBuild=true

   # Analyze code quality
   dotnet format --verify-no-changes
   ```

2. **Analyze Common Violations**

   Document the most frequent issues:

   - Line length violations

   - Indentation inconsistencies

   - Naming convention violations

   - Import organization issues

   - Whitespace problems

3. **Assess Consistency**

   Check for:

   - Consistent naming across codebase

   - Uniform formatting style

   - Standardized error handling

   - Common patterns usage

### Step 2: Complexity Analysis

**Identify complexity hotspots and maintainability issues:**

1. **Measure Cyclomatic Complexity**

   **Python**:
   ```bash
   pip install radon

   # Calculate complexity
   radon cc . -a -nb

   # Show functions with complexity > 10
   radon cc . -nc

   # Maintainability index
   radon mi . -nb
   ```

   **JavaScript**:
   ```bash
   npm install -g complexity-report
   cr src/**/*.js --format plain
   ```

   **Java**:
   ```bash
   # PMD complexity report
   mvn pmd:pmd

   # Check target/site/pmd.html for results
   ```

   **Go**:
   ```bash
   go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
   gocyclo -over 10 .
   ```

   **C/C++**:
   ```bash
   # Using lizard
   pip install lizard
   lizard src/ -l cpp -w
   ```

2. **Identify Large Functions/Methods**

   **All Languages**:
   ```bash
   # Find functions longer than 50 lines
   # Python
   grep -n "^def " src/**/*.py | while read line; do
       # Count lines until next function
       # Flag if > 50 lines
   done
   ```

   Look for:

   - Functions exceeding 50 lines

   - Methods with >5 parameters

   - Deep nesting (>4 levels)

   - Large classes (>300 lines)

3. **Module-Level Analysis**

   Evaluate:

   - Module cohesion (single responsibility)

   - Module coupling (dependencies)

   - Package organization

   - Circular dependencies

### Step 3: Design Quality Review

**Assess adherence to SOLID principles and design patterns:**

1. **SOLID Principles Check**

   **Single Responsibility Principle**:
   ```python
   # Bad: Class doing too much
   class UserManager:
       def create_user(self, data): pass
       def send_email(self, user): pass
       def generate_report(self, users): pass
       def backup_database(self): pass  # Wrong responsibility!

   # Good: Single responsibility
   class UserService:
       def create_user(self, data): pass
       def update_user(self, user): pass

   class EmailService:
       def send_email(self, user): pass
   ```

   **Open/Closed Principle**:
   ```java
   // Bad: Must modify class to extend
   class ReportGenerator {
       public void generateReport(String type) {
           if (type.equals("PDF")) { /* PDF logic */ }
           else if (type.equals("HTML")) { /* HTML logic */ }
           // Must modify to add new type
       }
   }

   // Good: Open for extension, closed for modification
   interface ReportFormatter {
       void format(Report report);
   }

   class PDFFormatter implements ReportFormatter {
       public void format(Report report) { /* PDF logic */ }
   }
   ```

   **Liskov Substitution Principle**:
   ```typescript
   // Bad: Derived class changes behavior
   class Bird {
       fly() { /* flying logic */ }
   }

   class Penguin extends Bird {
       fly() { throw new Error("Cannot fly"); } // Violates LSP
   }

   // Good: Proper abstraction
   interface Animal {}
   interface FlyingAnimal extends Animal {
       fly(): void;
   }
   ```

   **Interface Segregation Principle**:
   ```go
   // Bad: Fat interface
   type Worker interface {
       Work()
       Eat()
       Sleep()
       Code() // Not all workers code
   }

   // Good: Segregated interfaces
   type Worker interface {
       Work()
   }

   type Developer interface {
       Worker
       Code()
   }
   ```

   **Dependency Inversion Principle**:
   ```csharp
   // Bad: High-level depends on low-level
   public class OrderProcessor {
       private SqlDatabase database = new SqlDatabase();

       public void Process(Order order) {
           database.Save(order);  // Depends on concrete class
       }
   }

   // Good: Depend on abstractions
   public class OrderProcessor {
       private IDatabase database;

       public OrderProcessor(IDatabase database) {
           this.database = database;
       }

       public void Process(Order order) {
           database.Save(order);  // Depends on interface
       }
   }
   ```

2. **DRY Violations (Code Duplication)**

   **Python**:
   ```bash
   # Check for duplication
   pylint --disable=all --enable=duplicate-code . --min-similarity-lines=6
   ```

   **JavaScript**:
   ```bash
   npm install -g jscpd
   jscpd src/ --min-lines 5 --min-tokens 50
   ```

   **Java**:
   ```bash
   mvn pmd:cpd
   ```

3. **Design Patterns Assessment**

   Identify patterns in use:

   - **Creational**: Factory, Builder, Singleton

   - **Structural**: Adapter, Decorator, Facade

   - **Behavioral**: Observer, Strategy, Command

   Check for:

   - Appropriate pattern usage

   - Pattern misapplication

   - Over-engineering

   - Missing beneficial patterns

### Step 4: Code Smell Detection

**Identify common code smells across all languages:**

1. **Common Code Smells**

   **Long Method**:
   ```python
   # Bad: Method doing too much (>50 lines)
   def process_order(order, customer, inventory, payment):
       # 100+ lines of logic
       validate_order(order)
       check_inventory(inventory)
       process_payment(payment)
       update_customer(customer)
       send_confirmation(customer)
       update_analytics()
       # ... many more operations

   # Good: Extracted methods
   def process_order(order, customer, inventory, payment):
       self._validate_order(order)
       self._reserve_inventory(inventory)
       self._process_payment(payment)
       self._finalize_order(order, customer)
   ```

   **Long Parameter List**:
   ```java
   // Bad: Too many parameters (>5)
   public void createUser(
       String name,
       String email,
       String address,
       String phone,
       String city,
       String state,
       String zip,
       int age
   ) { }

   // Good: Parameter object
   public void createUser(UserData userData) { }
   ```

   **Large Class**:
   ```typescript
   // Bad: Class with too many responsibilities (>20 methods)
   class UserManager {
       // 50+ methods handling everything
   }

   // Good: Split responsibilities
   class UserService { }
   class UserValidator { }
   class UserRepository { }
   ```

   **Feature Envy**:
   ```go
   // Bad: Method uses data from another class excessively
   func (r *Report) GenerateTotal(order *Order) float64 {
       total := 0.0
       for _, item := range order.Items {
           total += item.Price * item.Quantity
       }
       return total - order.Discount  // Using Order data too much
   }

   // Good: Move to appropriate class
   func (o *Order) CalculateTotal() float64 {
       total := 0.0
       for _, item := range o.Items {
           total += item.Price * item.Quantity
       }
       return total - o.Discount
   }
   ```

   **Data Clumps**:
   ```cpp
   // Bad: Same parameters appearing together
   void processCoordinate(float x, float y, float z);
   void displayCoordinate(float x, float y, float z);
   void saveCoordinate(float x, float y, float z);

   // Good: Create a class/struct
   struct Coordinate {
       float x, y, z;
   };
   void processCoordinate(const Coordinate& coord);
   ```

   **Magic Numbers/Strings**:
   ```csharp
   // Bad: Magic numbers
   if (user.Age > 18 && user.Score > 750) {
       // Approve
   }

   // Good: Named constants
   const int MINIMUM_AGE = 18;
   const int MINIMUM_CREDIT_SCORE = 750;

   if (user.Age > MINIMUM_AGE && user.Score > MINIMUM_CREDIT_SCORE) {
       // Approve
   }
   ```

2. **Language-Specific Anti-Patterns**

   **Python**:
   ```python
   # Bad: Mutable default argument
   def append_to_list(item, items=[]):  # DON'T DO THIS
       items.append(item)
       return items

   # Good: Immutable default
   def append_to_list(item, items=None):
       if items is None:
           items = []
       items.append(item)
       return items

   # Bad: Bare except
   try:
       risky_operation()
   except:  # Catches everything, including KeyboardInterrupt
       pass

   # Good: Specific exception
   try:
       risky_operation()
   except ValueError as e:
       handle_error(e)
   ```

   **JavaScript**:
   ```javascript
   // Bad: Not using strict equality
   if (value == 0) { }  // Type coercion can cause bugs

   // Good: Strict equality
   if (value === 0) { }

   // Bad: Callback hell
   getData(function(a) {
       getMoreData(a, function(b) {
           getMoreData(b, function(c) {
               // Deep nesting
           });
       });
   });

   // Good: Promises or async/await
   const a = await getData();
   const b = await getMoreData(a);
   const c = await getMoreData(b);
   ```

   **Java**:
   ```java
   // Bad: Not closing resources
   FileInputStream stream = new FileInputStream("file.txt");
   // ... use stream
   stream.close();  // Might not execute if exception occurs

   // Good: Try-with-resources
   try (FileInputStream stream = new FileInputStream("file.txt")) {
       // ... use stream
   }  // Automatically closed
   ```

### Step 5: Error Handling Review

**Assess error handling quality and robustness:**

1. **Exception Handling Patterns**

   **Python**:
   ```python
   # Bad: Too broad
   try:
       process_data()
   except Exception:  # Catches too much
       pass

   # Good: Specific exceptions
   try:
       process_data()
   except ValueError as e:
       logger.error(f"Invalid data: {e}")
       raise
   except ConnectionError as e:
       logger.error(f"Connection failed: {e}")
       retry_with_backoff()
   ```

   **JavaScript**:
   ```javascript
   // Bad: Silent failure
   try {
       processData();
   } catch (e) {
       // Error swallowed
   }

   // Good: Proper error handling
   try {
       await processData();
   } catch (error) {
       logger.error('Data processing failed:', error);
       throw new DataProcessingError('Failed to process data', { cause: error });
   }
   ```

   **Java**:
   ```java
   // Bad: Generic exception
   public void process() throws Exception { }  // Too generic

   // Good: Specific exceptions
   public void process() throws IOException, ValidationException { }
   ```

2. **Resource Management**

   Check for:

   - Proper use of context managers (Python)

   - Try-with-resources (Java)

   - Using statements (C#)

   - Defer statements (Go)

   - RAII (C++)

3. **Logging and Error Messages**

   Evaluate:

   - Error messages are informative

   - Sensitive data not logged

   - Appropriate log levels used

   - Errors logged before re-throwing

### Step 6: Documentation Quality

**Assess code documentation completeness and quality:**

1. **Docstring/Comment Coverage**

   **Python**:
   ```bash
   pip install interrogate
   interrogate . -v --fail-under 80
   ```

   **JavaScript**:
   ```bash
   npm install -g documentation
   documentation lint src/**/*.js
   ```

2. **Comment Quality Check**

   Good comments explain WHY, not WHAT:
   ```python
   # Bad: States the obvious
   x = x + 1  # Increment x

   # Good: Explains reasoning
   x = x + 1  # Account for 1-based indexing in API
   ```

   Look for:

   - Commented-out code (remove it)

   - Outdated comments

   - TODO/FIXME comments

   - Missing documentation for complex logic

3. **Type Hints/Annotations**

   **Python**:
   ```bash
   pip install mypy
   mypy src/ --ignore-missing-imports
   ```

   **TypeScript**:
   ```bash
   tsc --noEmit  # Type check without compilation
   ```

### Step 7: Generate Quality Report

**Compile findings into structured report:**

```markdown
# Code Quality Review Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]

## Executive Summary

- **Overall Quality Score**: [A-F]

- **Maintainability Index**: [Score]

- **Average Complexity**: [Score]

- **Critical Issues**: [Count]

- **Technical Debt**: [Estimated hours]

## Coding Standards Compliance

### Style Violations
- **Total Violations**: [Count]

- **Most Common**: [Type] ([Count] occurrences)

- **Consistency Score**: [%]

### Top Issues
1. [Issue Type] - [Count] occurrences

2. [Issue Type] - [Count] occurrences

3. [Issue Type] - [Count] occurrences

## Complexity Analysis

### High Complexity Functions (>10)
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name]   | [path] | [score] | [count] | [refactor suggestion] |

### Large Modules (>300 lines)
| Module | Lines | Classes | Functions | Recommendation |
|--------|-------|---------|-----------|----------------|
| [path] | [count] | [count] | [count] | [split suggestion] |

## Design Quality Issues

### SOLID Violations
1. **Single Responsibility**: [Examples and impact]

2. **Open/Closed**: [Examples and impact]

3. **Liskov Substitution**: [Examples and impact]

4. **Interface Segregation**: [Examples and impact]

5. **Dependency Inversion**: [Examples and impact]

### DRY Violations
- **Duplication Found**: [Count] instances

- **Locations**: [List major duplications]

- **Consolidation Opportunities**: [Suggestions]

## Code Smells Detected

| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type]     | [file:line] | [High/Med/Low] | [details] | [suggestion] |

## Error Handling Assessment

- **Broad Exception Catching**: [Count] locations

- **Missing Resource Cleanup**: [Count] locations

- **Inadequate Error Messages**: [Count] instances

- **Silent Failures**: [Count] occurrences

## Documentation Score

- **Code Documentation**: [%] coverage

- **Type Hints**: [%] coverage

- **Comment Quality**: [Good/Fair/Poor]

- **Missing Documentation**: [List areas]

## Technical Debt Summary

### Priority 1 (Critical) - [Hours]
- [Issue and location]

### Priority 2 (High) - [Hours]
- [Issue and location]

### Priority 3 (Medium) - [Hours]
- [Issue and location]

### Priority 4 (Low) - [Hours]
- [Issue and location]

## Refactoring Recommendations

### Immediate (This Sprint)
1. [Specific refactoring with location and rationale]

### Short-term (1-2 Months)
1. [Improvement initiative with impact]

### Long-term (3-6 Months)
1. [Strategic refactoring with justification]

## Positive Patterns

- [Good practice observed]

- [Effective pattern usage]

## Next Steps

- [ ] Address critical complexity hotspots

- [ ] Implement automated quality gates

- [ ] Plan refactoring sprints for P1/P2 debt

- [ ] Establish team coding standards

- [ ] Set up pre-commit hooks

- [ ] Proceed to [Phase 3: Security Review](../code-review-security/SKILL.md)
```

## Success Criteria

- [ ] Coding standards compliance assessed

- [ ] Complexity hotspots identified

- [ ] SOLID principles evaluated

- [ ] Code smells documented

- [ ] Error handling reviewed

- [ ] Documentation quality measured

- [ ] Technical debt quantified

- [ ] Refactoring plan created

- [ ] Quality report generated

- [ ] Team ready for security review

## Related Skills

### Code Review Workflow
1. [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md)

2. **Phase 2: Quality Review (This Skill)**

3. [Phase 3: Security Review](../code-review-security/SKILL.md)

4. [Phase 4: Performance Review](../code-review-performance/SKILL.md)

5. [Phase 5: Testing Review](../code-review-testing/SKILL.md)

6. [Phase 6: Final Report](../code-review-final-report/SKILL.md)

## Additional Resources

### Quality Tools
- **Python**: pylint, flake8, black, radon, mypy

- **JavaScript**: ESLint, Prettier, JSDoc, complexity-report

- **Java**: Checkstyle, PMD, SpotBugs, SonarQube

- **Go**: golint, gofmt, go vet, staticcheck

- **C/C++**: clang-tidy, cppcheck, clang-format

- **C#**: StyleCop, FxCop, ReSharper

### Best Practices
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

- [Refactoring by Martin Fowler](https://refactoring.com/)

- [Code Complete by Steve McConnell](https://www.amazon.com/Code-Complete-Practical-Handbook-Construction/dp/0735619670)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: AI Templates Code Review Workflow
**Template Source**: `code_review/code_quality/*.md`
