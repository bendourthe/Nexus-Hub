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
