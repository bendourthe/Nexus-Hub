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
