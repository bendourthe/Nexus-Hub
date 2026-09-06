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
