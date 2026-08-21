---
name: semantic-bug-detector
description: Detect semantic bugs (logic errors, incorrect assumptions, race conditions) beyond syntactic checks. Use when reviewing code for logic errors, identifying off-by-one mistakes, finding null safety issues, detecting race conditions, or verifying invariants.
summary_l0: "Detect logic errors, race conditions, and invariant violations beyond syntax checks"
overview_l1: "This skill detects semantic bugs that pass compilation and linting but produce incorrect behavior at runtime, including logic flow analysis, type confusion detection, off-by-one errors, null safety analysis, race condition identification, and invariant violation detection. Use it when reviewing code for logic errors compilers cannot catch, finding off-by-one errors in loops and boundaries, detecting null/undefined safety issues, finding type-confusion bugs from silent coercion, identifying race conditions in concurrent code, or verifying invariants (preconditions, postconditions, loop invariants). Key capabilities include control flow path analysis, boundary condition verification, null propagation tracking, type coercion detection, concurrency hazard identification, and invariant assertion generation. The expected output is a categorized bug report with location, severity, explanation, and suggested fix for each detected semantic issue. Trigger phrases: check for logic errors, find semantic bugs, detect off-by-one, null safety review, race condition detection, find logic flaws, check invariants, semantic analysis, detect concurrency bugs."
---

# Semantic Bug Detector

Detect semantic bugs that pass compilation and linting but produce incorrect behavior at runtime. This skill covers logic flow analysis, type confusion detection, off-by-one error detection, null safety analysis, race condition identification, and invariant violation detection.

## When to Use This Skill

Use this skill when you need to:

- Review code for logic errors that compilers and linters cannot catch
- Identify off-by-one errors in loops, array accesses, and boundary conditions
- Detect null/undefined safety issues before they cause runtime crashes
- Find type confusion bugs where values are silently coerced or misinterpreted
- Identify race conditions and concurrency bugs in multi-threaded or async code
- Verify that code invariants (preconditions, postconditions, loop invariants) are maintained
- Audit code for incorrect assumptions about data formats, ranges, or ordering

**Trigger phrases**: "check for logic errors", "find semantic bugs", "detect off-by-one", "null safety review", "race condition detection", "find logic flaws", "check invariants", "semantic analysis", "detect concurrency bugs"

## What This Skill Does

### Methodology Overview

Semantic bug detection operates at a higher level than syntax checking. While compilers verify that code is well-formed and linters check style, semantic analysis verifies that code does what the developer intended. This skill applies six complementary detection techniques:

1. **Logic Flow Analysis** -- Trace the logical paths through code to find unreachable branches, inverted conditions, missing cases, and incorrect boolean logic.
2. **Type Confusion Detection** -- Identify cases where values of one type are silently treated as another (string-to-number coercion, lossy casts, enum misuse).
3. **Off-by-One Detection** -- Examine loop bounds, array indices, range calculations, and boundary conditions for fencepost errors.
4. **Null Safety Analysis** -- Find code paths where null or undefined values can reach operations that require non-null values.
5. **Race Condition Identification** -- Detect shared mutable state accessed without synchronization, time-of-check-to-time-of-use (TOCTOU) patterns, and async ordering issues.
6. **Invariant Violation Detection** -- Verify that preconditions, postconditions, and loop invariants hold across all code paths.

### Bug Category Reference

| Category | Severity | Detection Difficulty | Common Languages |
|----------|----------|---------------------|-----------------|
| Off-by-one | Medium | Medium | All |
| Null dereference | High | Low-Medium | Java, C#, JavaScript, Python |
| Type confusion | Medium-High | High | JavaScript, Python |
| Race condition | Critical | Very High | All (concurrent code) |
| Logic inversion | Medium | Medium | All |
| Invariant violation | High | High | All |
| Integer overflow | High | Medium | C, C++, Java |
| Incorrect comparison | Medium | Low | JavaScript, Python |

## Instructions

### Step 1: Logic Flow Analysis

Trace the logical structure of code to find errors in conditions, branches, and control flow.

**Common logic flow bugs:**

- Inverted conditions (`if (x > 0)` when `if (x < 0)` was intended)
- Missing `else` branches or missing `default` cases in switch statements
- Short-circuit evaluation side effects
- Dead code after unconditional returns
- Incorrect operator precedence in compound conditions

**Python: Logic flow analyzer**

```python
import ast
from dataclasses import dataclass

@dataclass
class LogicFlowIssue:
    file: str
    line: int
    category: str
    description: str
    severity: str

class LogicFlowAnalyzer(ast.NodeVisitor):
    """Detect logic flow issues in Python code."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[LogicFlowIssue] = []

    def visit_If(self, node: ast.If):
        # Check for tautologies and contradictions
        if isinstance(node.test, ast.Compare):
            self._check_tautological_comparison(node)

        # Check for missing else on exhaustive conditions
        if not node.orelse:
            self._check_missing_else(node)

        # Check for dead code after return in if body
        self._check_dead_code_after_return(node)

        self.generic_visit(node)

    def _check_tautological_comparison(self, node: ast.If):
        """Detect always-true or always-false comparisons."""
        test = node.test
        if isinstance(test, ast.Compare) and len(test.ops) == 1:
            left = test.left
            right = test.comparators[0]
            # Check x == x (always true)
            if (isinstance(left, ast.Name) and isinstance(right, ast.Name)
                    and left.id == right.id):
                self.issues.append(LogicFlowIssue(
                    file=self.filename,
                    line=node.lineno,
                    category="tautological_comparison",
                    description=f"Comparison '{left.id} == {right.id}' is always True",
                    severity="medium",
                ))

    def _check_missing_else(self, node: ast.If):
        """Flag if statements that may need an else clause."""
        # Heuristic: if the if body contains a return, an else might be needed
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                self.issues.append(LogicFlowIssue(
                    file=self.filename,
                    line=node.lineno,
                    category="missing_else",
                    description="If statement with return but no else clause; "
                                "consider whether the else case is handled",
                    severity="info",
                ))
                break

    def _check_dead_code_after_return(self, node: ast.If):
        """Detect code that appears after an unconditional return."""
        body = node.body
        for i, stmt in enumerate(body):
            if isinstance(stmt, ast.Return) and i < len(body) - 1:
                self.issues.append(LogicFlowIssue(
                    file=self.filename,
                    line=body[i + 1].lineno,
                    category="dead_code",
                    description="Code after return statement is unreachable",
                    severity="high",
                ))

    def visit_BoolOp(self, node: ast.BoolOp):
        """Check for suspicious boolean operations."""
        # Check for duplicate operands: x or x, x and x
        names = []
        for value in node.values:
            if isinstance(value, ast.Name):
                names.append(value.id)
        if len(names) != len(set(names)):
            self.issues.append(LogicFlowIssue(
                file=self.filename,
                line=node.lineno,
                category="duplicate_boolean_operand",
                description="Boolean operation contains duplicate operands",
                severity="medium",
            ))
        self.generic_visit(node)


def analyze_logic_flow(source_code: str, filename: str = "<input>") -> list[LogicFlowIssue]:
    """Analyze Python source code for logic flow issues."""
    tree = ast.parse(source_code)
    analyzer = LogicFlowAnalyzer(filename)
    analyzer.visit(tree)
    return analyzer.issues
```

**JavaScript: Logic flow analysis patterns**

```javascript
/**
 * Common logic flow bug patterns to check during code review.
 * These are patterns that eslint and TypeScript may not catch.
 */

// BUG PATTERN 1: Incorrect equality comparison
// JavaScript's == performs type coercion; use === instead
function checkEqualityBugs(code) {
  const issues = [];
  const lines = code.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Detect == null (should usually be === null || === undefined)
    if (/[^=!]=\s*null\b/.test(line) && !/===\s*null/.test(line)) {
      // Note: == null intentionally catches both null and undefined
      // This is a common pattern, but should be deliberate
      issues.push({
        line: i + 1,
        category: "loose_equality",
        description: "Using == null; verify this is intentional (catches both null and undefined)",
        severity: "info",
      });
    }

    // Detect = in conditions (assignment instead of comparison)
    if (/if\s*\([^=]*[^=!<>]=[^=]/.test(line)) {
      issues.push({
        line: i + 1,
        category: "assignment_in_condition",
        description: "Possible assignment (=) in condition instead of comparison (=== or ==)",
        severity: "high",
      });
    }
  }

  return issues;
}

// BUG PATTERN 2: Unreachable code after return/throw
function checkUnreachableCode(code) {
  const issues = [];
  const lines = code.split("\n");

  for (let i = 0; i < lines.length - 1; i++) {
    const line = lines[i].trim();
    const nextLine = lines[i + 1].trim();

    if (
      (line.startsWith("return ") || line.startsWith("throw ")) &&
      nextLine &&
      !nextLine.startsWith("}") &&
      !nextLine.startsWith("//") &&
      !nextLine.startsWith("case ") &&
      !nextLine.startsWith("default:")
    ) {
      issues.push({
        line: i + 2,
        category: "unreachable_code",
        description: "Code after return/throw is unreachable",
        severity: "high",
      });
    }
  }

  return issues;
}

// BUG PATTERN 3: Missing break in switch
function checkSwitchFallthrough(code) {
  const issues = [];
  const caseRegex = /case\s+.+:/g;
  const breakRegex = /\bbreak\b|\breturn\b|\bthrow\b/;
  const lines = code.split("\n");

  let inCase = false;
  let caseStartLine = 0;
  let hasTerminator = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    if (/^case\s/.test(line) || line === "default:") {
      if (inCase && !hasTerminator) {
        issues.push({
          line: caseStartLine,
          category: "switch_fallthrough",
          description: "Case block without break, return, or throw (possible fallthrough bug)",
          severity: "medium",
        });
      }
      inCase = true;
      caseStartLine = i + 1;
      hasTerminator = false;
    }

    if (breakRegex.test(line)) {
      hasTerminator = true;
    }
  }

  return issues;
}
```

**Java: Logic flow analysis**

```java
import java.util.*;
import java.util.regex.*;

public class LogicFlowAnalyzer {
    public record Issue(int line, String category,
                        String description, String severity) {}

    public static List<Issue> analyzeJavaSource(String sourceCode) {
        List<Issue> issues = new ArrayList<>();
        String[] lines = sourceCode.split("\n");

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            int lineNum = i + 1;

            // Check for assignment in condition
            if (Pattern.matches(".*if\\s*\\([^=]*[^=!<>]=[^=].*", line)) {
                issues.add(new Issue(lineNum, "assignment_in_condition",
                    "Possible assignment in condition instead of comparison",
                    "high"));
            }

            // Check for unreachable code after return
            if ((line.startsWith("return ") || line.startsWith("throw "))
                    && i + 1 < lines.length) {
                String nextLine = lines[i + 1].trim();
                if (!nextLine.isEmpty() && !nextLine.startsWith("}")
                        && !nextLine.startsWith("case ")
                        && !nextLine.startsWith("//")) {
                    issues.add(new Issue(lineNum + 1, "unreachable_code",
                        "Code after return/throw is unreachable", "high"));
                }
            }

            // Check for String comparison with ==
            if (Pattern.matches(".*\\w+\\s*==\\s*\".*\".*", line)
                    || Pattern.matches(".*\".*\"\\s*==\\s*\\w+.*", line)) {
                issues.add(new Issue(lineNum, "string_reference_comparison",
                    "Comparing String with == instead of .equals()",
                    "high"));
            }

            // Check for empty catch blocks
            if (line.startsWith("catch") && i + 1 < lines.length
                    && lines[i + 1].trim().equals("}")) {
                issues.add(new Issue(lineNum, "empty_catch",
                    "Empty catch block silently swallows exception",
                    "high"));
            }
        }

        return issues;
    }
}
```

### Step 2: Off-by-One Detection

Off-by-one errors are among the most common semantic bugs. They occur at boundaries: loop limits, array indices, range ends, and string positions.

**Common off-by-one patterns:**

| Pattern | Bug | Fix |
|---------|-----|-----|
| `for i in range(len(arr))` accessing `arr[i+1]` | Index out of bounds on last iteration | `range(len(arr) - 1)` |
| `for (int i = 0; i <= arr.length; i++)` | Index out of bounds | `i < arr.length` |
| `substring(0, str.length() - 1)` | Drops last character unintentionally | Verify intent; use `str.length()` if full string needed |
| `arr[arr.length]` | Index out of bounds | `arr[arr.length - 1]` |
| Inclusive vs exclusive range confusion | Wrong number of iterations or elements | Document whether ranges are inclusive or exclusive |

**Python: Off-by-one detector**

```python
import ast

class OffByOneDetector(ast.NodeVisitor):
    """Detect potential off-by-one errors in Python code."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[dict] = []

    def visit_For(self, node: ast.For):
        """Check for loops for off-by-one risks."""
        # Check range() calls
        if isinstance(node.iter, ast.Call):
            func = node.iter
            if isinstance(func.func, ast.Name) and func.func.id == "range":
                self._check_range_obo(node, func)
        self.generic_visit(node)

    def _check_range_obo(self, for_node: ast.For, range_call: ast.Call):
        """Check range() for off-by-one patterns."""
        args = range_call.args

        if len(args) >= 2:
            # range(start, stop) -- check if stop is a len() call
            stop = args[1]
            if isinstance(stop, ast.Call) and isinstance(stop.func, ast.Name):
                if stop.func.id == "len":
                    # range(x, len(arr)) is correct for 0-based indexing
                    pass

            # Check for range(1, len(arr)) when 0-based access expected
            start = args[0]
            if isinstance(start, ast.Constant) and start.value == 1:
                self.issues.append({
                    "line": for_node.lineno,
                    "category": "range_start_one",
                    "description": "range() starts at 1; verify this is intentional "
                                   "(Python uses 0-based indexing)",
                    "severity": "medium",
                })

    def visit_Subscript(self, node: ast.Subscript):
        """Check array subscript access for off-by-one risks."""
        # Check for arr[len(arr)] (should be arr[len(arr) - 1])
        if isinstance(node.slice, ast.Call):
            if (isinstance(node.slice.func, ast.Name)
                    and node.slice.func.id == "len"):
                self.issues.append({
                    "line": node.lineno,
                    "category": "index_equals_length",
                    "description": "Accessing arr[len(arr)] will raise IndexError; "
                                   "last element is arr[len(arr) - 1]",
                    "severity": "high",
                })
        self.generic_visit(node)


def detect_off_by_one(source_code: str, filename: str = "<input>") -> list[dict]:
    """Detect off-by-one errors in Python source code."""
    tree = ast.parse(source_code)
    detector = OffByOneDetector(filename)
    detector.visit(tree)
    return detector.issues
```

**JavaScript: Off-by-one detector**

```javascript
function detectOffByOne(code) {
  const issues = [];
  const lines = code.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    // Pattern: for (... i <= arr.length ...) -- should be < not <=
    const forLeMatch = line.match(
      /for\s*\(.+\b(\w+)\s*<=\s*(\w+)\.length\b/
    );
    if (forLeMatch) {
      issues.push({
        line: lineNum,
        category: "loop_bound_inclusive",
        description: `Loop uses '<= ${forLeMatch[2]}.length' which will access ` +
          `index ${forLeMatch[2]}.length (out of bounds). Use '< ${forLeMatch[2]}.length'`,
        severity: "high",
      });
    }

    // Pattern: arr[arr.length] -- should be arr[arr.length - 1]
    const lengthAccessMatch = line.match(/(\w+)\[(\w+)\.length\]/);
    if (lengthAccessMatch && lengthAccessMatch[1] === lengthAccessMatch[2]) {
      issues.push({
        line: lineNum,
        category: "index_equals_length",
        description: `Accessing ${lengthAccessMatch[1]}[${lengthAccessMatch[1]}.length] ` +
          "is out of bounds. Use .length - 1 for the last element",
        severity: "high",
      });
    }

    // Pattern: slice(0, -1) when the intent may be to include the last element
    if (/\.slice\(\s*0\s*,\s*-1\s*\)/.test(line)) {
      issues.push({
        line: lineNum,
        category: "slice_excludes_last",
        description: "slice(0, -1) excludes the last element. " +
          "Verify this is intentional",
        severity: "info",
      });
    }

    // Pattern: substring(0, str.length - 1) dropping last character
    if (/\.substring\(\s*0\s*,\s*\w+\.length\s*-\s*1\s*\)/.test(line)) {
      issues.push({
        line: lineNum,
        category: "substring_drops_last",
        description: "substring(0, str.length - 1) drops the last character. " +
          "Verify this is intentional",
        severity: "info",
      });
    }
  }

  return issues;
}
```

### Step 3: Null Safety Analysis

Detect code paths where null, None, undefined, or similar sentinel values can reach operations that do not handle them.

**Python: Null safety analyzer**

```python
import ast

class NullSafetyAnalyzer(ast.NodeVisitor):
    """Detect potential None-related bugs in Python code."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[dict] = []
        self.nullable_vars: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function parameters and their None potential."""
        # Check for parameters with None defaults
        defaults = node.args.defaults
        args = node.args.args
        num_defaults = len(defaults)
        num_args = len(args)

        for i, default in enumerate(defaults):
            if isinstance(default, ast.Constant) and default.value is None:
                arg_index = num_args - num_defaults + i
                arg_name = args[arg_index].arg
                self.nullable_vars.add(arg_name)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Track assignments that may introduce None."""
        # Check for x = dict.get(key) (returns None if key missing)
        if isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr == "get":
                # Only one default arg means it defaults to None
                if len(node.value.args) <= 1 and not node.value.keywords:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.nullable_vars.add(target.id)

        # Check for x = None
        if isinstance(node.value, ast.Constant) and node.value.value is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.nullable_vars.add(target.id)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Check attribute access on potentially None variables."""
        if isinstance(node.value, ast.Name) and node.value.id in self.nullable_vars:
            self.issues.append({
                "line": node.lineno,
                "category": "null_dereference",
                "description": f"Attribute access '.{node.attr}' on "
                               f"'{node.value.id}' which may be None",
                "severity": "high",
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check method calls on potentially None variables."""
        if isinstance(node.func, ast.Attribute):
            obj = node.func.value
            if isinstance(obj, ast.Name) and obj.id in self.nullable_vars:
                self.issues.append({
                    "line": node.lineno,
                    "category": "null_method_call",
                    "description": f"Method call '.{node.func.attr}()' on "
                                   f"'{obj.id}' which may be None",
                    "severity": "high",
                })
        self.generic_visit(node)


def analyze_null_safety(source_code: str, filename: str = "<input>") -> list[dict]:
    """Analyze Python code for null safety issues."""
    tree = ast.parse(source_code)
    analyzer = NullSafetyAnalyzer(filename)
    analyzer.visit(tree)
    return analyzer.issues
```

**JavaScript: Null safety patterns**

```javascript
function analyzeNullSafety(code) {
  const issues = [];
  const lines = code.split("\n");
  const nullableVars = new Set();

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const lineNum = i + 1;

    // Track variables that may be null/undefined
    const nullAssign = line.match(
      /(?:const|let|var)\s+(\w+)\s*=\s*(?:null|undefined)\s*;/
    );
    if (nullAssign) {
      nullableVars.add(nullAssign[1]);
    }

    // Track .find() results (returns undefined if not found)
    const findResult = line.match(
      /(?:const|let|var)\s+(\w+)\s*=\s*\w+\.find\(/
    );
    if (findResult) {
      nullableVars.add(findResult[1]);
    }

    // Track Map.get() results
    const mapGet = line.match(
      /(?:const|let|var)\s+(\w+)\s*=\s*\w+\.get\(/
    );
    if (mapGet) {
      nullableVars.add(mapGet[1]);
    }

    // Check for property access on nullable variables
    for (const varName of nullableVars) {
      const accessPattern = new RegExp(
        `\\b${varName}\\.(\\w+)`, "g"
      );
      const accessMatch = accessPattern.exec(line);
      if (accessMatch) {
        // Check if there is a null guard before this access
        const beforeAccess = lines.slice(Math.max(0, i - 3), i + 1).join("\n");
        const hasGuard =
          beforeAccess.includes(`if (${varName}`) ||
          beforeAccess.includes(`if (!${varName}`) ||
          beforeAccess.includes(`${varName}?.`) ||
          beforeAccess.includes(`${varName} &&`);

        if (!hasGuard) {
          issues.push({
            line: lineNum,
            category: "null_dereference",
            description: `Property access '.${accessMatch[1]}' on '${varName}' ` +
              "which may be null/undefined. Use optional chaining (?.) or add a guard",
            severity: "high",
          });
        }
      }
    }
  }

  return issues;
}
```

**Java: Null safety analyzer**

```java
import java.util.*;
import java.util.regex.*;

public class NullSafetyAnalyzer {
    public record NullIssue(int line, String category,
                             String description, String severity) {}

    private final Set<String> nullableVars = new HashSet<>();

    public List<NullIssue> analyze(String sourceCode) {
        List<NullIssue> issues = new ArrayList<>();
        String[] lines = sourceCode.split("\n");

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            int lineNum = i + 1;

            // Track null assignments
            Matcher nullAssign = Pattern.compile(
                "(\\w+)\\s+(\\w+)\\s*=\\s*null\\s*;"
            ).matcher(line);
            if (nullAssign.find()) {
                nullableVars.add(nullAssign.group(2));
            }

            // Track Map.get() results (can return null)
            Matcher mapGet = Pattern.compile(
                "(\\w+)\\s+(\\w+)\\s*=\\s*\\w+\\.get\\("
            ).matcher(line);
            if (mapGet.find()) {
                nullableVars.add(mapGet.group(2));
            }

            // Track methods that may return null
            Matcher findFirst = Pattern.compile(
                "(\\w+)\\s+(\\w+)\\s*=.*\\.findFirst\\(\\)\\.orElse\\(null\\)"
            ).matcher(line);
            if (findFirst.find()) {
                nullableVars.add(findFirst.group(2));
            }

            // Check for method calls on nullable variables without null check
            for (String varName : nullableVars) {
                if (line.contains(varName + ".") && !line.contains("null")) {
                    // Look for a null check in surrounding lines
                    boolean hasGuard = false;
                    for (int j = Math.max(0, i - 3); j <= i; j++) {
                        String surrounding = lines[j].trim();
                        if (surrounding.contains("if (" + varName + " != null")
                                || surrounding.contains("if (" + varName + " == null")
                                || surrounding.contains("Objects.requireNonNull(" + varName)) {
                            hasGuard = true;
                            break;
                        }
                    }
                    if (!hasGuard) {
                        issues.add(new NullIssue(lineNum, "null_dereference",
                            "Method call on '" + varName + "' which may be null. " +
                            "Add a null check or use Optional",
                            "high"));
                    }
                }
            }
        }

        return issues;
    }
}
```

### Step 4: Race Condition Identification

Detect concurrency bugs including unsynchronized shared state, TOCTOU patterns, and async ordering issues.

**Python: Race condition detector**

```python
import ast
from dataclasses import dataclass

@dataclass
class RaceConditionIssue:
    line: int
    category: str
    description: str
    severity: str

class RaceConditionDetector(ast.NodeVisitor):
    """Detect potential race conditions in Python code."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[RaceConditionIssue] = []
        self.shared_state_writes: dict[str, list[int]] = {}
        self.in_async = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        old_async = self.in_async
        self.in_async = True
        self.generic_visit(node)
        self.in_async = old_async

    def visit_Assign(self, node: ast.Assign):
        """Track writes to shared state."""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                # Writing to self.x in an async context is a potential race
                if (isinstance(target.value, ast.Name)
                        and target.value.id == "self" and self.in_async):
                    attr_name = f"self.{target.attr}"
                    if attr_name not in self.shared_state_writes:
                        self.shared_state_writes[attr_name] = []
                    self.shared_state_writes[attr_name].append(node.lineno)

                    if len(self.shared_state_writes[attr_name]) > 1:
                        self.issues.append(RaceConditionIssue(
                            line=node.lineno,
                            category="unsynchronized_shared_write",
                            description=f"Multiple async writes to '{attr_name}' "
                                        "without synchronization",
                            severity="high",
                        ))
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """Detect TOCTOU patterns (check-then-act without lock)."""
        # Check for patterns like: if os.path.exists(f): ... open(f) ...
        if self._is_file_existence_check(node.test):
            for child in ast.walk(node):
                if self._is_file_operation(child):
                    self.issues.append(RaceConditionIssue(
                        line=node.lineno,
                        category="toctou",
                        description="Time-of-check-to-time-of-use: file existence "
                                    "check followed by file operation is vulnerable "
                                    "to race conditions",
                        severity="high",
                    ))
                    break
        self.generic_visit(node)

    def _is_file_existence_check(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            return node.func.attr in ("exists", "isfile", "isdir")
        return False

    def _is_file_operation(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id in ("open", "remove", "unlink")
        return False
```

**JavaScript: Async race condition patterns**

```javascript
function detectAsyncRaceConditions(code) {
  const issues = [];
  const lines = code.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const lineNum = i + 1;

    // Pattern: Forgetting to await an async function
    if (/(?:const|let|var)\s+\w+\s*=\s*\w+\.\w+\(/.test(line) && !line.includes("await")) {
      // Check if the function is likely async by looking for async in context
      const context = lines.slice(Math.max(0, i - 10), i).join("\n");
      if (context.includes("async ") && !line.includes("then(")) {
        issues.push({
          line: lineNum,
          category: "missing_await",
          description: "Assignment from function call without await inside async function. " +
            "If the function is async, the result will be a Promise, not the resolved value",
          severity: "high",
        });
      }
    }

    // Pattern: forEach with async callback (does not await)
    if (/\.forEach\(\s*async/.test(line)) {
      issues.push({
        line: lineNum,
        category: "async_foreach",
        description: "Array.forEach() does not await async callbacks. " +
          "Use for...of or Promise.all(arr.map(async ...)) instead",
        severity: "high",
      });
    }

    // Pattern: Multiple state updates without batching
    if (/setState|dispatch|commit/.test(line)) {
      const nextLine = i + 1 < lines.length ? lines[i + 1].trim() : "";
      if (/setState|dispatch|commit/.test(nextLine)) {
        issues.push({
          line: lineNum,
          category: "unbatched_state_updates",
          description: "Consecutive state updates may cause race conditions " +
            "or unnecessary re-renders. Consider batching",
          severity: "medium",
        });
      }
    }

    // Pattern: Shared mutable variable in closure
    if (/let\s+(\w+)\s*=/.test(line)) {
      const varName = line.match(/let\s+(\w+)/)[1];
      const remainingCode = lines.slice(i + 1).join("\n");
      const inCallback = new RegExp(
        `(?:setTimeout|setInterval|addEventListener|on\\w+)\\s*\\([^)]*${varName}`
      ).test(remainingCode);
      if (inCallback) {
        issues.push({
          line: lineNum,
          category: "shared_mutable_closure",
          description: `Mutable variable '${varName}' is captured by an async callback. ` +
            "The value may change between when the callback is created and when it executes",
          severity: "medium",
        });
      }
    }
  }

  return issues;
}
```

**Java: Race condition detector**

```java
import java.util.*;
import java.util.regex.*;

public class RaceConditionDetector {
    public record RaceIssue(int line, String category,
                             String description, String severity) {}

    public static List<RaceIssue> detect(String sourceCode) {
        List<RaceIssue> issues = new ArrayList<>();
        String[] lines = sourceCode.split("\n");
        boolean inSynchronized = false;
        Set<String> sharedFields = new HashSet<>();

        // First pass: identify shared mutable fields
        for (String line : lines) {
            String trimmed = line.trim();
            // Non-final, non-volatile fields are potentially unsafe
            if (trimmed.matches(".*(?:private|protected|public)\\s+(?!final|static final)\\w+\\s+\\w+\\s*[;=].*")
                    && !trimmed.contains("volatile")) {
                Matcher m = Pattern.compile("(\\w+)\\s*[;=]").matcher(trimmed);
                if (m.find()) {
                    sharedFields.add(m.group(1));
                }
            }
        }

        // Second pass: detect unsafe access patterns
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            int lineNum = i + 1;

            if (line.contains("synchronized")) {
                inSynchronized = true;
            }
            if (line.equals("}") && inSynchronized) {
                inSynchronized = false;
            }

            // Check for check-then-act outside synchronized
            if (!inSynchronized && line.startsWith("if (") && line.contains("!= null")) {
                Matcher m = Pattern.compile("if\\s*\\((\\w+)\\s*!=\\s*null\\)").matcher(line);
                if (m.find()) {
                    String varName = m.group(1);
                    if (sharedFields.contains(varName)) {
                        issues.add(new RaceIssue(lineNum, "check_then_act",
                            "Check-then-act on shared field '" + varName +
                            "' outside synchronized block is vulnerable to race conditions",
                            "critical"));
                    }
                }
            }

            // Check for compound operations on shared state without synchronization
            if (!inSynchronized) {
                for (String field : sharedFields) {
                    if (line.contains(field + "++") || line.contains(field + "--")
                            || line.contains(field + " += ") || line.contains(field + " -= ")) {
                        issues.add(new RaceIssue(lineNum, "compound_operation",
                            "Compound operation on shared field '" + field +
                            "' is not atomic. Use AtomicInteger or synchronize",
                            "critical"));
                    }
                }
            }

            // Check for double-checked locking without volatile
            if (line.contains("if (") && line.contains("== null")) {
                Matcher m = Pattern.compile("if\\s*\\((\\w+)\\s*==\\s*null\\)").matcher(line);
                if (m.find()) {
                    String varName = m.group(1);
                    if (sharedFields.contains(varName)) {
                        // Look for synchronized block after this check
                        boolean hasSyncBlock = false;
                        for (int j = i + 1; j < Math.min(i + 5, lines.length); j++) {
                            if (lines[j].trim().contains("synchronized")) {
                                hasSyncBlock = true;
                                break;
                            }
                        }
                        if (hasSyncBlock) {
                            // This looks like double-checked locking
                            issues.add(new RaceIssue(lineNum, "double_checked_locking",
                                "Double-checked locking on '" + varName +
                                "' requires the field to be volatile",
                                "critical"));
                        }
                    }
                }
            }
        }

        return issues;
    }
}
```

### Step 5: Invariant Violation Detection

Verify that preconditions, postconditions, and loop invariants hold throughout the code.

**Python: Invariant checker**

```python
from functools import wraps
from typing import Callable

def precondition(*conditions: Callable):
    """Decorator that checks preconditions before function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for condition in conditions:
                result = condition(*args, **kwargs)
                if not result:
                    raise AssertionError(
                        f"Precondition violated for {func.__name__}: "
                        f"{condition.__doc__ or condition.__name__}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def postcondition(*conditions: Callable):
    """Decorator that checks postconditions after function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for condition in conditions:
                check = condition(result, *args, **kwargs)
                if not check:
                    raise AssertionError(
                        f"Postcondition violated for {func.__name__}: "
                        f"{condition.__doc__ or condition.__name__}"
                    )
            return result
        return wrapper
    return decorator


# Example usage
def non_negative_amount(amount, **kwargs):
    """Amount must be non-negative"""
    return amount >= 0

def balance_non_negative(result, amount, **kwargs):
    """Balance must remain non-negative after withdrawal"""
    return result >= 0

@precondition(non_negative_amount)
@postcondition(balance_non_negative)
def withdraw(amount, balance=0):
    return balance - amount


class InvariantChecker:
    """Runtime invariant checking for detecting semantic bugs."""

    def __init__(self):
        self.violations: list[dict] = []

    def check_loop_invariant(
        self,
        invariant_fn: Callable,
        description: str,
        context: dict,
    ) -> bool:
        """Check a loop invariant and record violations."""
        result = invariant_fn(context)
        if not result:
            self.violations.append({
                "type": "loop_invariant",
                "description": description,
                "context": context,
            })
        return result

    def check_data_invariant(
        self,
        data: any,
        invariant_fn: Callable,
        description: str,
    ) -> bool:
        """Check a data structure invariant."""
        result = invariant_fn(data)
        if not result:
            self.violations.append({
                "type": "data_invariant",
                "description": description,
                "data_snapshot": repr(data)[:200],
            })
        return result


# Example: checking a sorted list invariant
def is_sorted(lst):
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))

checker = InvariantChecker()

def insert_sorted(lst, value):
    """Insert a value while maintaining sorted order."""
    # Precondition: list must be sorted
    checker.check_data_invariant(lst, is_sorted, "Input list must be sorted")

    # Find insertion point
    i = 0
    while i < len(lst) and lst[i] < value:
        i += 1
    lst.insert(i, value)

    # Postcondition: list must still be sorted
    checker.check_data_invariant(lst, is_sorted, "Output list must remain sorted")
    return lst
```

**JavaScript: Invariant checker**

```javascript
function precondition(conditionFn, description) {
  return function (target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args) {
      if (!conditionFn.apply(this, args)) {
        throw new Error(
          `Precondition violated for ${propertyKey}: ${description}`
        );
      }
      return originalMethod.apply(this, args);
    };
    return descriptor;
  };
}

function postcondition(conditionFn, description) {
  return function (target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args) {
      const result = originalMethod.apply(this, args);
      if (!conditionFn.call(this, result, ...args)) {
        throw new Error(
          `Postcondition violated for ${propertyKey}: ${description}`
        );
      }
      return result;
    };
    return descriptor;
  };
}

// Without decorators (plain function wrapper approach)
function withInvariant(fn, { pre, post, preDesc, postDesc }) {
  return function (...args) {
    if (pre && !pre(...args)) {
      throw new Error(`Precondition violated for ${fn.name}: ${preDesc}`);
    }
    const result = fn.apply(this, args);
    if (post && !post(result, ...args)) {
      throw new Error(`Postcondition violated for ${fn.name}: ${postDesc}`);
    }
    return result;
  };
}

// Example usage
const safeDivide = withInvariant(
  function divide(a, b) {
    return a / b;
  },
  {
    pre: (a, b) => b !== 0,
    preDesc: "Divisor must not be zero",
    post: (result) => Number.isFinite(result),
    postDesc: "Result must be a finite number",
  }
);
```

### Step 6: Combine Detectors into a Unified Analysis

Run all detectors together and produce a prioritized report.

**Python: Unified semantic analysis**

```python
def run_full_semantic_analysis(source_code: str, filename: str) -> dict:
    """Run all semantic bug detectors and return a unified report."""
    results = {
        "filename": filename,
        "logic_flow": analyze_logic_flow(source_code, filename),
        "off_by_one": detect_off_by_one(source_code, filename),
        "null_safety": analyze_null_safety(source_code, filename),
        "total_issues": 0,
        "critical_count": 0,
        "high_count": 0,
    }

    all_issues = (
        results["logic_flow"]
        + results["off_by_one"]
        + results["null_safety"]
    )

    results["total_issues"] = len(all_issues)
    results["critical_count"] = sum(
        1 for i in all_issues
        if (i.severity if hasattr(i, "severity") else i.get("severity")) == "critical"
    )
    results["high_count"] = sum(
        1 for i in all_issues
        if (i.severity if hasattr(i, "severity") else i.get("severity")) == "high"
    )

    return results
```

## Best Practices

- Run semantic analysis on every pull request, not just when bugs are suspected. Many semantic bugs are easier to prevent than to find after the fact.
- Combine automated detection with manual review. Automated tools catch common patterns, but experienced developers catch subtle logic errors that no tool can detect.
- Use precondition and postcondition checks in development and testing builds, but consider disabling them in production for performance-sensitive paths.
- Document invariants explicitly in code comments or assertion statements. An invariant that exists only in a developer's mind will eventually be violated.
- Pay special attention to boundary conditions: empty collections, zero values, maximum values, null inputs, and single-element collections. These are where off-by-one and null safety bugs cluster.
- For race condition detection, prefer designs that eliminate shared mutable state (immutable data, message passing, actor model) over designs that rely on correct synchronization.
- When reviewing code for semantic bugs, read the code as if you were an adversarial tester trying to break it. Ask "what happens if this value is null?" and "what happens if this collection is empty?" at every step.
- Maintain a catalog of semantic bug patterns specific to your codebase and language. Each time a semantic bug is found and fixed, add its pattern to the catalog so it can be detected automatically in the future.

## Common Pitfalls

- **Assuming the compiler catches logic errors.** Compilers verify syntax and type safety (in statically typed languages), not whether your algorithm is correct. A function that compiles and runs without errors can still produce wrong results.
- **Ignoring implicit type coercion.** In JavaScript, `"5" + 3` yields `"53"` (string concatenation), not `8`. In Python, `True + 1` yields `2`. These coercions are language-defined behavior, not errors, but they are a rich source of semantic bugs.
- **Treating absence of errors as correctness.** A function that silently returns a wrong value is harder to detect than one that throws an exception. Prefer "fail loudly" designs with explicit assertions over silent fallbacks.
- **Overlooking edge cases in boolean logic.** De Morgan's laws (`not (A and B)` equals `not A or not B`) are frequently applied incorrectly. Complex conditions with mixed `and`/`or` operators are prone to precedence errors.
- **Underestimating race condition complexity.** Race conditions can be extremely difficult to reproduce because they depend on timing. A test that passes 99% of the time can still harbor a critical race condition. Use race condition detectors, stress tests, and formal analysis tools (such as ThreadSanitizer) rather than relying on test pass rates.
- **Relying on a single detection technique.** No single technique catches all semantic bugs. Logic flow analysis misses race conditions; null safety analysis misses off-by-one errors. Use all available techniques together for comprehensive coverage.
- **Not verifying assumptions about external APIs.** If your code assumes that an API returns a non-null value but the documentation says it may return null, you have a semantic bug waiting to happen. Always verify your assumptions against documentation and test with edge-case inputs.
- **Assuming that "it works on my machine" means correctness.** Semantic bugs often depend on data, timing, or environment. A function that works correctly with your test data may fail with different input values, larger datasets, or concurrent access.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code compiles and passes linting, so it's correct" | Linters and type checkers verify syntax and type safety, not algorithmic correctness; a function that always returns the first element of a list instead of the minimum compiles cleanly and passes all linters. |
| "Off-by-one errors are trivial and easy to spot" | Off-by-one errors in loop bounds and array indices are among the most common bugs in production systems; they are invisible to static analysis and often manifest only with specific input sizes or boundary values. |
| "We run the test suite, which covers logic errors" | Tests cover paths explicitly written by developers; semantic bugs live in the paths developers did not think to test -- null inputs, zero values, empty collections, and boundary conditions that were assumed impossible. |
| "Race conditions only occur in high-throughput systems" | Check-Then-Act race conditions in balance checks and permission verifications have been exploited with two simultaneous browser tabs at zero scale; concurrency is not a prerequisite for race condition bugs. |
| "Type coercion issues only matter in dynamically typed languages" | Static languages have their own coercion hazards: integer overflow in Java/C# silently wraps to negative values, implicit numeric promotions in C change signedness, and Go's integer division silently truncates decimals. |
| "Invariant checking is theoretical and rarely finds bugs in practice" | Explicit precondition and postcondition assertions (even as comments) have been shown in code review studies to surface incorrect assumptions about function contracts that would otherwise remain latent bugs. |

## Verification

- [ ] All loop bounds and array index operations reviewed for off-by-one conditions with boundary inputs (0, 1, n-1, n)
- [ ] Null/undefined propagation traced for all inputs that reach the reviewed code from external sources
- [ ] Concurrency hazards checked: any shared state accessed from multiple goroutines/threads/async tasks is identified
- [ ] Type coercion risk assessed: implicit conversions in conditions and arithmetic expressions reviewed
- [ ] At least one property-based or parameterized test added for each logic-heavy function to cover non-obvious inputs
- [ ] Semantic bug report produced with location, severity, explanation, and suggested fix for each detected issue

## Related Skills

- [[bug-localization]] -- pinpoints the file and line for a semantic bug this skill surfaces
- [[bug-to-patch-generator]] -- generates the fix for a detected logic error
- [[edge-case-generator]] -- produces the boundary inputs this skill checks off-by-one conditions against
- [[property-based-test-generator]] -- generates the property-based tests the Verification step calls for
- [[code-quality]] -- broader maintainability review that complements semantic-defect detection
