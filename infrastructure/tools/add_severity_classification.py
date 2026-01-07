"""
Add severity classification framework to all code review templates.

This script adds a comprehensive severity classification section to all code
review templates to help users prioritize findings.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import os
import re
from pathlib import Path
from typing import Dict

# Language-specific severity classification templates
SEVERITY_TEMPLATES = {
    'csharp': '''## Severity Classification

Use this framework to classify and prioritize all findings from the code quality review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- **Unmanaged resource disposal** (unclosed database connections, file streams)
- **Thread safety violations** (race conditions in concurrent code)
- **SQL injection vulnerabilities** (unsanitized user input)
- **Memory leaks** (event handlers not unsubscribed, static references)
- **NullReferenceExceptions** in critical paths

**Code Example:**
```csharp
// CRITICAL: Resource leak - connection never disposed
public List<User> GetUsers()
{
    var conn = new SqlConnection(connectionString);  // ❌ No using statement
    var cmd = new SqlCommand("SELECT * FROM Users", conn);
    conn.Open();
    var reader = cmd.ExecuteReader();
    return MapUsers(reader);
}

// FIXED:
public List<User> GetUsers()
{
    using (var conn = new SqlConnection(connectionString))  // ✅ Auto-dispose
    using (var cmd = new SqlCommand("SELECT * FROM Users", conn))
    {
        conn.Open();
        using (var reader = cmd.ExecuteReader())
        {
            return MapUsers(reader);
        }
    }
}
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
- **Performance bottlenecks** (O(n²) algorithms, missing database indexes)
- **Memory inefficiency** (large collections in memory, boxing/unboxing)
- **Breaking API changes** without deprecation
- **Missing error handling** (empty catch blocks, swallowed exceptions)

**Code Example:**
```csharp
// HIGH: O(n²) performance issue
public List<int> FindDuplicates(List<int> items)
{
    var duplicates = new List<int>();
    for (int i = 0; i < items.Count; i++)
    {
        for (int j = 0; j < items.Count; j++)  // ❌ Nested loop
        {
            if (i != j && items[i] == items[j])
                duplicates.Add(items[i]);
        }
    }
    return duplicates;
}

// FIXED: O(n) with HashSet
public List<int> FindDuplicates(List<int> items)
{
    var seen = new HashSet<int>();
    var duplicates = new HashSet<int>();
    foreach (var item in items)  // ✅ Single pass
    {
        if (seen.Contains(item))
            duplicates.Add(item);
        seen.Add(item);
    }
    return duplicates.ToList();
}
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
- **High complexity** (cyclomatic complexity >10, methods >100 lines)
- **Code duplication** (>10 lines duplicated across classes)
- **Poor naming** (unclear variable/method names)
- **Missing tests** (<80% coverage on critical paths)
- **Overly broad exception handling** (catching Exception instead of specific types)

**Code Example:**
```csharp
// MEDIUM: High complexity
public bool ProcessOrder(Order order, User user,
                        Inventory inventory, Payment payment)  // ❌ Too complex
{
    if (order.Status == "pending")
    {
        if (user.IsVerified)
        {
            if (inventory.CheckStock(order.Items))
            {
                if (payment.Validate())
                {
                    if (payment.Charge(order.Total))
                    {
                        inventory.Reserve(order.Items);
                        order.Status = "confirmed";
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

// FIXED: Early returns
public bool ProcessOrder(Order order, User user,
                        Inventory inventory, Payment payment)
{
    if (order.Status != "pending") return false;  // ✅ Guard clauses
    if (!user.IsVerified) return false;
    if (!inventory.CheckStock(order.Items)) return false;
    if (!payment.Validate() || !payment.Charge(order.Total)) return false;

    inventory.Reserve(order.Items);
    order.Status = "confirmed";
    return true;
}
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
- **Style violations** (formatting, naming conventions)
- **Minor optimizations** (LINQ usage, string interpolation)
- **Missing XML documentation** on public methods
- **Verbose code** that could use modern C# features
- **Console.WriteLine** left in production code

**Code Example:**
```csharp
// LOW: Verbosity
public double CalculateTotal(List<Item> items)
{
    double total = 0.0;  // ❌ Verbose
    for (int i = 0; i < items.Count; i++)
        total += items[i].Price;
    return total;
}

// FIXED:
public double CalculateTotal(List<Item> items) =>
    items.Sum(item => item.Price);  // ✅ Concise LINQ
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
- Connection leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in unit test: **LOW → Ignore** (test code only)
- Duplicated logic across 15 services: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix with code example

**6. Effort Estimate:** Time to fix (hours/days)

---

''',
    # Add 'go', 'c', 'cpp' templates here (similar structure)
}


def get_generic_severity_template() -> str:
    """Return a generic severity classification template that works for all languages."""
    return '''## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- Security vulnerabilities (SQL injection, XSS, authentication bypass)
- Resource leaks (unclosed connections, file handles, memory leaks)
- Data loss risks (destructive operations without validation)
- Thread safety violations (race conditions, deadlocks)
- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- Incorrect business logic (wrong calculations, flawed algorithms)
- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)
- Memory inefficiency (loading large datasets into memory unnecessarily)
- Breaking API changes without deprecation
- Missing critical error handling (network errors, API failures not caught)

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- High complexity (cyclomatic complexity >10, functions >100 lines)
- Code duplication (>10 lines duplicated across modules)
- Poor naming (unclear variable/function names, inconsistent conventions)
- Missing tests (<80% coverage on critical paths)
- Incomplete error messages (no context for debugging)

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- Style violations (linting warnings, formatting issues)
- Minor performance optimizations (in non-critical code paths)
- Missing documentation on helper functions
- Verbose code that could be more concise
- Debug statements left in code

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
- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades with user count (currently 500ms for 10k users)
- High memory usage (50MB+ per request)
- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:
- Add database index on search fields
- Use database LIKE/ILIKE queries
- Implement pagination (limit results to 50)
- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---

'''


def get_severity_content(language: str, phase: str) -> str:
    """Generate language and phase-appropriate severity classification."""
    # Use generic template that works for all languages and phases
    return get_generic_severity_template()


def add_severity_to_file(filepath: Path) -> bool:
    """Add severity classification to a code review template."""
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if severity classification already exists
    if "## Severity Classification" in content:
        print(f"SKIP: Already has severity classification: {filepath.name}")
        return False

    # Find insertion point (before "## Prompt Template")
    match = re.search(r'^## Prompt Template', content, re.MULTILINE)
    if not match:
        print(f"WARNING: No 'Prompt Template' section found: {filepath.name}")
        return False

    insertion_point = match.start()

    # Extract language from filename
    language = filepath.stem.split('_')[0]  # e.g., 'python' from 'python_code_quality.md'

    # Generate severity content
    severity_content = get_severity_content(language, filepath.parent.name)

    # Insert severity classification
    new_content = content[:insertion_point] + severity_content + "\n" + content[insertion_point:]

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"SUCCESS: Added severity classification: {filepath.name}")
    return True


def main():
    """Add severity classification to all code review templates."""
    base_path = Path(__file__).parent.parent.parent / 'templates' / 'development' / 'codebase-review'

    if not base_path.exists():
        print(f"ERROR: Code review directory not found: {base_path}")
        return

    # Phases that need severity classification
    phases = [
        'code_quality',
        'context_analysis',
        'security_review',
        'performance_review',
        'testing_review',
        'final_report'
    ]

    # Languages to process
    languages = ['python', 'javascript', 'java', 'csharp', 'go', 'c', 'cpp']

    total = 0
    updated = 0
    skipped = 0

    print("=" * 70)
    print("Adding Severity Classification to Code Review Templates")
    print("=" * 70)
    print()

    for phase in phases:
        phase_path = base_path / phase
        if not phase_path.exists():
            print(f"WARNING: Phase directory not found: {phase}")
            continue

        print(f"\nProcessing phase: {phase}")
        print("-" * 70)

        for lang in languages:
            filepath = phase_path / f"{lang}_{phase}.md"
            if filepath.exists():
                total += 1
                result = add_severity_to_file(filepath)
                if result:
                    updated += 1
                else:
                    skipped += 1
            else:
                print(f"WARNING: File not found: {filepath.name}")

    print()
    print("=" * 70)
    print(f"Summary:")
    print(f"  Total files processed: {total}")
    print(f"  Files updated: {updated}")
    print(f"  Files skipped (already have classification): {skipped}")
    print("=" * 70)


if __name__ == '__main__':
    main()
