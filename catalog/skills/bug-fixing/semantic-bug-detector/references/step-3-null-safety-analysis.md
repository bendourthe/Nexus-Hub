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
