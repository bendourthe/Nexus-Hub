---
name: bug-to-patch-generator
description: Generate code patches from bug reports, error messages, and failing tests. Use when converting bug descriptions into fixes, creating patches from error output, or automating fix generation from test failures.
---

# Bug-to-Patch Generator

Transform bug reports, error messages, and failing test output into targeted code patches that fix the underlying issue, pass all existing tests, and include safeguards against regression.

## When to Use This Skill

Use this skill when you need to:

- Convert a bug report (from an issue tracker, user report, or automated alert) into a concrete code fix
- Generate a patch from a failing test or assertion error
- Translate an error message or stack trace into the minimum code change required
- Produce a patch that fixes the bug while preserving all existing passing tests
- Automate the fix-validate-commit cycle for well-defined defects
- Generate candidate patches for review when the root cause is already identified

**Trigger phrases**: "generate a patch", "fix this bug", "create a fix for", "patch from error", "convert bug report to fix", "auto-fix", "generate fix from test failure", "bug to patch"

## What This Skill Does

### Methodology Overview

The bug-to-patch pipeline follows five stages:

1. **Bug Report Analysis** -- Extract the essential facts from the report: expected behavior, actual behavior, reproduction steps, environment details, and any attached logs or stack traces.
2. **Root Cause Identification** -- Narrow down the faulty code region using the localization techniques described in the bug-localization skill, then identify the specific logical or syntactic error.
3. **Patch Generation** -- Produce one or more candidate patches that address the root cause. Each patch should be minimal (changing only what is necessary) and well-explained.
4. **Patch Validation** -- Run the failing test (and the full regression suite) against each candidate patch to confirm the fix and detect unintended side effects.
5. **Regression Prevention** -- Add or strengthen tests to ensure the specific bug cannot recur silently.

### Patch Quality Criteria

A high-quality patch satisfies all of the following:

| Criterion | Description |
|-----------|-------------|
| Correctness | The patch fixes the reported bug and the previously failing test now passes |
| Minimality | The patch changes only what is necessary; no unrelated modifications |
| Safety | All previously passing tests continue to pass |
| Clarity | The patch includes comments or commit message text explaining why the change was made |
| Testability | A new or updated test covers the exact failure scenario |

## Instructions

### Step 1: Parse the Bug Report

Extract structured information from the bug report. Not all fields will be present in every report; extract what is available.

**Python: Bug report parser**

```python
from dataclasses import dataclass, field
import re

@dataclass
class BugReport:
    title: str = ""
    description: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    reproduction_steps: list[str] = field(default_factory=list)
    error_message: str = ""
    stack_trace: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    affected_files: list[str] = field(default_factory=list)
    severity: str = "medium"

def parse_bug_report(text: str) -> BugReport:
    """Parse a semi-structured bug report into a BugReport object."""
    report = BugReport()

    # Extract sections by common headers
    section_pattern = re.compile(
        r"(?:^|\n)##?\s*([\w\s]+?)[:.\n]",
        re.IGNORECASE,
    )
    sections = {}
    matches = list(section_pattern.finditer(text))
    for i, match in enumerate(matches):
        key = match.group(1).strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[key] = text[start:end].strip()

    report.title = sections.get("title", text.split("\n")[0][:120])
    report.description = sections.get("description", "")
    report.expected_behavior = sections.get("expected behavior", "")
    report.actual_behavior = sections.get("actual behavior", "")
    report.error_message = sections.get("error message", "")
    report.stack_trace = sections.get("stack trace", "")

    steps_text = sections.get("steps to reproduce", "")
    if steps_text:
        report.reproduction_steps = [
            s.strip().lstrip("0123456789.) ")
            for s in steps_text.split("\n")
            if s.strip()
        ]

    return report


def extract_error_signature(report: BugReport) -> str:
    """Extract a normalized error signature for matching against known patterns."""
    if report.error_message:
        # Remove variable parts (file paths, line numbers, memory addresses)
        normalized = re.sub(r"0x[0-9a-fA-F]+", "<addr>", report.error_message)
        normalized = re.sub(r"line \d+", "line <N>", normalized)
        normalized = re.sub(r'["\'].+?["\']', "<str>", normalized)
        return normalized
    return ""
```

**JavaScript: Bug report parser**

```javascript
class BugReport {
  constructor() {
    this.title = "";
    this.description = "";
    this.expectedBehavior = "";
    this.actualBehavior = "";
    this.reproductionSteps = [];
    this.errorMessage = "";
    this.stackTrace = "";
    this.environment = {};
    this.affectedFiles = [];
    this.severity = "medium";
  }
}

function parseBugReport(text) {
  const report = new BugReport();
  const sectionRegex = /(?:^|\n)#{1,2}\s*([\w\s]+?)[:.\n]/gi;
  const sections = {};

  const matches = [...text.matchAll(sectionRegex)];
  for (let i = 0; i < matches.length; i++) {
    const key = matches[i][1].trim().toLowerCase();
    const start = matches[i].index + matches[i][0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    sections[key] = text.slice(start, end).trim();
  }

  report.title = sections["title"] || text.split("\n")[0].slice(0, 120);
  report.description = sections["description"] || "";
  report.expectedBehavior = sections["expected behavior"] || "";
  report.actualBehavior = sections["actual behavior"] || "";
  report.errorMessage = sections["error message"] || "";
  report.stackTrace = sections["stack trace"] || "";

  const stepsText = sections["steps to reproduce"] || "";
  if (stepsText) {
    report.reproductionSteps = stepsText
      .split("\n")
      .filter(s => s.trim())
      .map(s => s.trim().replace(/^\d+[.)]\s*/, ""));
  }

  return report;
}

function extractErrorSignature(report) {
  if (!report.errorMessage) return "";
  return report.errorMessage
    .replace(/0x[0-9a-fA-F]+/g, "<addr>")
    .replace(/line \d+/g, "line <N>")
    .replace(/['"][^'"]+['"]/g, "<str>");
}
```

**Java: Bug report parser**

```java
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class BugReportParser {
    public record BugReport(
        String title,
        String description,
        String expectedBehavior,
        String actualBehavior,
        List<String> reproductionSteps,
        String errorMessage,
        String stackTrace,
        Map<String, String> environment,
        String severity
    ) {}

    public static BugReport parse(String text) {
        Map<String, String> sections = new LinkedHashMap<>();
        Pattern sectionPattern = Pattern.compile(
            "(?:^|\\n)#{1,2}\\s*([\\w\\s]+?)[:.\\n]",
            Pattern.CASE_INSENSITIVE
        );
        Matcher matcher = sectionPattern.matcher(text);
        List<int[]> positions = new ArrayList<>();
        List<String> keys = new ArrayList<>();

        while (matcher.find()) {
            keys.add(matcher.group(1).trim().toLowerCase());
            positions.add(new int[]{matcher.end(), 0});
        }
        for (int i = 0; i < positions.size(); i++) {
            int end = (i + 1 < positions.size())
                ? positions.get(i + 1)[0] - keys.get(i + 1).length() - 3
                : text.length();
            sections.put(keys.get(i), text.substring(positions.get(i)[0], end).trim());
        }

        List<String> steps = new ArrayList<>();
        String stepsText = sections.getOrDefault("steps to reproduce", "");
        if (!stepsText.isEmpty()) {
            for (String line : stepsText.split("\\n")) {
                String trimmed = line.trim();
                if (!trimmed.isEmpty()) {
                    steps.add(trimmed.replaceFirst("^\\d+[.)\\s]*", ""));
                }
            }
        }

        return new BugReport(
            sections.getOrDefault("title", text.split("\\n")[0]),
            sections.getOrDefault("description", ""),
            sections.getOrDefault("expected behavior", ""),
            sections.getOrDefault("actual behavior", ""),
            steps,
            sections.getOrDefault("error message", ""),
            sections.getOrDefault("stack trace", ""),
            Map.of(),
            "medium"
        );
    }
}
```

### Step 2: Identify the Root Cause

Using the parsed bug report, narrow down the root cause to a specific code location and defect type.

**Common defect type mapping:**

| Error Signature Pattern | Likely Defect Type | Typical Fix Strategy |
|-------------------------|--------------------|----------------------|
| NullPointerException / TypeError: Cannot read properties of null | Missing null check | Add guard clause or fix initialization |
| IndexError / ArrayIndexOutOfBoundsException | Off-by-one or unchecked bounds | Fix loop bounds or add bounds check |
| KeyError / undefined is not a function | Missing key or wrong property name | Fix the key name or add existence check |
| AssertionError: expected X but got Y | Logic error in computation | Trace computation, fix formula or condition |
| TimeoutError / connection refused | Resource unavailability | Add retry logic, fix connection parameters |

**Python: Root cause identifier**

```python
def identify_root_cause(report: BugReport) -> dict:
    """Analyze the bug report to determine the root cause category."""
    cause = {
        "category": "unknown",
        "confidence": 0.0,
        "suggested_fix_type": "manual_inspection",
        "target_location": None,
    }

    error = report.error_message.lower()
    trace = report.stack_trace

    # Pattern matching against known root cause categories
    patterns = [
        ("nonetype", "null_reference", "add_null_check", 0.8),
        ("keyerror", "missing_key", "add_key_check_or_fix_name", 0.85),
        ("indexerror", "off_by_one", "fix_bounds", 0.7),
        ("typeerror", "type_mismatch", "fix_type_handling", 0.6),
        ("assertionerror", "logic_error", "fix_computation", 0.5),
        ("zerodivisionerror", "division_by_zero", "add_zero_check", 0.9),
        ("filenotfounderror", "missing_resource", "fix_path_or_create", 0.8),
        ("timeout", "resource_timeout", "add_retry_or_fix_config", 0.6),
    ]

    for pattern, category, fix_type, confidence in patterns:
        if pattern in error:
            cause["category"] = category
            cause["confidence"] = confidence
            cause["suggested_fix_type"] = fix_type
            break

    # Extract target location from stack trace
    if trace:
        import re
        file_line = re.search(r'File "(.+?)", line (\d+)', trace)
        if file_line:
            cause["target_location"] = {
                "file": file_line.group(1),
                "line": int(file_line.group(2)),
            }

    return cause
```

### Step 3: Generate Candidate Patches

Produce one or more patches that address the identified root cause. Each patch should be minimal and self-explanatory.

**Python: Patch generator**

```python
from dataclasses import dataclass

@dataclass
class Patch:
    file_path: str
    original_lines: list[str]
    patched_lines: list[str]
    start_line: int
    explanation: str
    confidence: float

def generate_null_check_patch(
    file_path: str,
    lines: list[str],
    fault_line: int,
    variable_name: str,
) -> Patch:
    """Generate a patch that adds a null/None check before the fault line."""
    indent = len(lines[fault_line - 1]) - len(lines[fault_line - 1].lstrip())
    indent_str = " " * indent

    original = lines[fault_line - 1: fault_line]
    patched = [
        f"{indent_str}if {variable_name} is None:\n",
        f"{indent_str}    raise ValueError("
        f"\"Expected {variable_name} to be non-None\")\n",
        lines[fault_line - 1],
    ]

    return Patch(
        file_path=file_path,
        original_lines=original,
        patched_lines=patched,
        start_line=fault_line,
        explanation=(
            f"Add a guard clause to check that '{variable_name}' is not None "
            f"before it is used on line {fault_line}. This prevents the "
            f"NoneType error and provides a clear error message."
        ),
        confidence=0.8,
    )


def generate_bounds_check_patch(
    file_path: str,
    lines: list[str],
    fault_line: int,
    collection_name: str,
    index_expr: str,
) -> Patch:
    """Generate a patch that adds bounds checking before an index access."""
    indent = len(lines[fault_line - 1]) - len(lines[fault_line - 1].lstrip())
    indent_str = " " * indent

    original = lines[fault_line - 1: fault_line]
    patched = [
        f"{indent_str}if {index_expr} < 0 or {index_expr} >= len({collection_name}):\n",
        f"{indent_str}    raise IndexError("
        f"f\"Index {{{index_expr}}} out of range for "
        f"{collection_name} of length {{len({collection_name})}}\")\n",
        lines[fault_line - 1],
    ]

    return Patch(
        file_path=file_path,
        original_lines=original,
        patched_lines=patched,
        start_line=fault_line,
        explanation=(
            f"Add bounds checking for '{collection_name}[{index_expr}]' "
            f"before the access on line {fault_line}."
        ),
        confidence=0.75,
    )


def apply_patch(file_path: str, patch: Patch) -> None:
    """Apply a patch to a file."""
    with open(file_path) as f:
        lines = f.readlines()

    start = patch.start_line - 1
    end = start + len(patch.original_lines)
    lines[start:end] = patch.patched_lines

    with open(file_path, "w") as f:
        f.writelines(lines)
```

**JavaScript: Patch generator**

```javascript
class Patch {
  constructor(filePath, startLine, originalLines, patchedLines, explanation) {
    this.filePath = filePath;
    this.startLine = startLine;
    this.originalLines = originalLines;
    this.patchedLines = patchedLines;
    this.explanation = explanation;
  }

  toDiff() {
    const header = `--- a/${this.filePath}\n+++ b/${this.filePath}\n`;
    const hunk = `@@ -${this.startLine},${this.originalLines.length} +${this.startLine},${this.patchedLines.length} @@\n`;
    const removals = this.originalLines.map(l => `-${l}`).join("\n");
    const additions = this.patchedLines.map(l => `+${l}`).join("\n");
    return `${header}${hunk}${removals}\n${additions}`;
  }
}

function generateNullCheckPatch(filePath, lines, faultLine, variableName) {
  const originalLine = lines[faultLine - 1];
  const indent = originalLine.match(/^(\s*)/)[1];

  const original = [originalLine];
  const patched = [
    `${indent}if (${variableName} == null) {\n`,
    `${indent}  throw new TypeError(\`Expected ${variableName} to be non-null\`);\n`,
    `${indent}}\n`,
    originalLine,
  ];

  return new Patch(
    filePath,
    faultLine,
    original,
    patched,
    `Add null check for '${variableName}' before usage on line ${faultLine}.`
  );
}

function generateBoundsCheckPatch(filePath, lines, faultLine, arrayName, indexExpr) {
  const originalLine = lines[faultLine - 1];
  const indent = originalLine.match(/^(\s*)/)[1];

  const original = [originalLine];
  const patched = [
    `${indent}if (${indexExpr} < 0 || ${indexExpr} >= ${arrayName}.length) {\n`,
    `${indent}  throw new RangeError(\`Index \${${indexExpr}} out of bounds for ${arrayName}\`);\n`,
    `${indent}}\n`,
    originalLine,
  ];

  return new Patch(filePath, faultLine, original, patched,
    `Add bounds check for '${arrayName}[${indexExpr}]' on line ${faultLine}.`);
}
```

**Java: Patch generator**

```java
import java.util.*;
import java.io.*;
import java.nio.file.*;

public class PatchGenerator {
    public record Patch(
        String filePath,
        int startLine,
        List<String> originalLines,
        List<String> patchedLines,
        String explanation,
        double confidence
    ) {}

    public static Patch generateNullCheckPatch(
            String filePath, List<String> lines,
            int faultLine, String variableName) {
        String original = lines.get(faultLine - 1);
        String indent = original.substring(0, original.indexOf(original.trim()));

        List<String> originals = List.of(original);
        List<String> patched = List.of(
            indent + "if (" + variableName + " == null) {",
            indent + "    throw new NullPointerException(\"" +
                variableName + " must not be null\");",
            indent + "}",
            original
        );

        return new Patch(filePath, faultLine, originals, patched,
            "Add null check for '" + variableName +
            "' before usage on line " + faultLine, 0.8);
    }

    public static void applyPatch(Patch patch) throws IOException {
        List<String> lines = new ArrayList<>(
            Files.readAllLines(Path.of(patch.filePath()))
        );

        int start = patch.startLine() - 1;
        int end = start + patch.originalLines().size();

        List<String> before = lines.subList(0, start);
        List<String> after = lines.subList(end, lines.size());

        List<String> result = new ArrayList<>(before);
        result.addAll(patch.patchedLines());
        result.addAll(after);

        Files.write(Path.of(patch.filePath()), result);
    }
}
```

### Step 4: Validate the Patch

Every patch must be validated against the failing test and the full regression suite.

**Python: Patch validation pipeline**

```python
import subprocess
import tempfile
import shutil

class PatchValidator:
    """Validate a patch against the test suite."""

    def __init__(self, project_root: str, test_command: str):
        self.project_root = project_root
        self.test_command = test_command

    def validate(self, patch: Patch) -> dict:
        """Apply the patch in a temporary copy and run tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy the project
            work_dir = shutil.copytree(
                self.project_root, f"{tmpdir}/project",
                ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"),
            )

            # Apply the patch
            target = f"{work_dir}/{patch.file_path}"
            with open(target) as f:
                lines = f.readlines()
            start = patch.start_line - 1
            end = start + len(patch.original_lines)
            lines[start:end] = patch.patched_lines
            with open(target, "w") as f:
                f.writelines(lines)

            # Run the specific failing test
            failing_result = subprocess.run(
                self.test_command,
                shell=True, cwd=work_dir,
                capture_output=True, text=True, timeout=120,
            )

            # Run the full regression suite
            regression_result = subprocess.run(
                f"{self.test_command} --full",
                shell=True, cwd=work_dir,
                capture_output=True, text=True, timeout=300,
            )

            return {
                "failing_test_fixed": failing_result.returncode == 0,
                "regression_suite_passed": regression_result.returncode == 0,
                "failing_output": failing_result.stdout + failing_result.stderr,
                "regression_output": regression_result.stdout + regression_result.stderr,
            }
```

**JavaScript: Patch validation**

```javascript
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

function validatePatch(projectRoot, patch, testCommand) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "patch-validate-"));

  try {
    // Copy project (excluding node_modules and .git)
    execSync(`rsync -a --exclude node_modules --exclude .git "${projectRoot}/" "${tmpDir}/"`);

    // Apply patch
    const targetFile = path.join(tmpDir, patch.filePath);
    const lines = fs.readFileSync(targetFile, "utf-8").split("\n");
    const start = patch.startLine - 1;
    const end = start + patch.originalLines.length;
    const patched = [
      ...lines.slice(0, start),
      ...patch.patchedLines,
      ...lines.slice(end),
    ];
    fs.writeFileSync(targetFile, patched.join("\n"));

    // Install dependencies
    execSync("npm ci --ignore-scripts", { cwd: tmpDir, stdio: "pipe" });

    // Run failing test
    let failingTestFixed = false;
    try {
      execSync(testCommand, { cwd: tmpDir, stdio: "pipe", timeout: 60000 });
      failingTestFixed = true;
    } catch {
      failingTestFixed = false;
    }

    // Run full suite
    let regressionPassed = false;
    try {
      execSync("npm test", { cwd: tmpDir, stdio: "pipe", timeout: 120000 });
      regressionPassed = true;
    } catch {
      regressionPassed = false;
    }

    return { failingTestFixed, regressionPassed };
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}
```

### Step 5: Add Regression Prevention Tests

After validating the patch, add a test that specifically covers the bug scenario to prevent future regression.

**Python: Regression test generator**

```python
def generate_regression_test(
    report: BugReport,
    fix_description: str,
    module_name: str,
    function_name: str,
) -> str:
    """Generate a regression test for the fixed bug."""
    test_name = f"test_regression_{report.title.lower().replace(' ', '_')[:50]}"

    return f'''
def {test_name}():
    """Regression test for: {report.title}

    Bug: {report.actual_behavior}
    Expected: {report.expected_behavior}
    Fix: {fix_description}
    """
    # Arrange: Set up the exact conditions from the bug report
    # TODO: Fill in the specific setup from reproduction steps

    # Act: Perform the operation that triggered the bug
    result = {module_name}.{function_name}()  # TODO: Add actual arguments

    # Assert: Verify the expected behavior (not the buggy behavior)
    assert result is not None, "Result should not be None after fix"
    # TODO: Add specific assertion matching expected behavior
'''
```

**JavaScript: Regression test generator**

```javascript
function generateRegressionTest(report, fixDescription, modulePath, functionName) {
  const testName = `should not regress: ${report.title.slice(0, 60)}`;

  return `
describe("Regression: ${report.title.slice(0, 50)}", () => {
  it("${testName}", () => {
    // Bug: ${report.actualBehavior}
    // Expected: ${report.expectedBehavior}
    // Fix: ${fixDescription}

    // Arrange: Set up the exact conditions from the bug report
    const module = require("${modulePath}");

    // Act: Perform the operation that triggered the bug
    const result = module.${functionName}(); // TODO: Add actual arguments

    // Assert: Verify the expected behavior
    expect(result).not.toBeNull();
    expect(result).not.toBeUndefined();
    // TODO: Add specific assertion matching expected behavior
  });
});
`;
}
```

**Java: Regression test generator**

```java
public class RegressionTestGenerator {

    public static String generate(
            String bugTitle, String actualBehavior,
            String expectedBehavior, String fixDescription,
            String className, String methodName) {

        String testMethodName = "testRegression_" +
            bugTitle.replaceAll("[^a-zA-Z0-9]", "_").substring(0, Math.min(50, bugTitle.length()));

        return String.format("""
            @Test
            @DisplayName("Regression: %s")
            void %s() {
                // Bug: %s
                // Expected: %s
                // Fix: %s

                // Arrange: Set up the exact conditions from the bug report
                var instance = new %s();

                // Act: Perform the operation that triggered the bug
                var result = instance.%s(); // TODO: Add actual arguments

                // Assert: Verify the expected behavior
                assertNotNull(result, "Result should not be null after fix");
                // TODO: Add specific assertion matching expected behavior
            }
            """,
            bugTitle, testMethodName, actualBehavior,
            expectedBehavior, fixDescription, className, methodName
        );
    }
}
```

## Best Practices

- Always generate the minimal patch. Resist the temptation to refactor surrounding code while fixing a bug; that belongs in a separate commit.
- Produce multiple candidate patches when the root cause has ambiguity. Rank them by confidence and present the top candidates for human review.
- Validate every patch in an isolated environment. Never trust a patch that has only been visually inspected; run the tests.
- Write the regression test before applying the final patch. This confirms that the test actually fails without the fix (test-driven bug fixing).
- Include a clear explanation in the patch (as code comments or commit message) that links back to the bug report identifier.
- Preserve the original error behavior in your regression test assertions. The test should assert the correct behavior, but also document what the buggy behavior was so future readers understand the purpose of the test.
- When a patch introduces new dependencies or imports, verify that those dependencies are available in all target environments.
- Keep patch metadata (file path, line range, explanation) in a structured format so that automated tools can process and apply them.

## Common Pitfalls

- **Fixing the symptom instead of the cause.** Adding a null check at the crash site may hide a deeper initialization bug. Always trace back to where the incorrect value originated before deciding where to patch.
- **Generating overly broad patches.** A patch that rewrites an entire function to fix a one-line bug is risky and hard to review. Keep changes focused on the defect.
- **Skipping regression test validation.** A patch that fixes the failing test but breaks three other tests is worse than no patch. Always run the full suite.
- **Ignoring edge cases in the fix.** If a bug was caused by an unhandled null, ensure the fix also handles other degenerate inputs (empty strings, zero values, empty collections) if they share the same code path.
- **Not linking the patch to the bug report.** Future maintainers need to understand why a change was made. Include the bug report identifier in the commit message and in a code comment near the fix.
- **Applying patches without understanding the root cause.** If you cannot explain why the bug occurred, your patch may be masking the real problem. Invest time in root cause analysis before generating fixes.
- **Forgetting to handle the patch in the context of concurrent changes.** If the target file has been modified since the bug was reported, the patch may not apply cleanly. Always rebase or verify against the latest version of the code before committing.
- **Trusting automated patch generation without review.** Machine-generated patches can be syntactically correct but semantically wrong. Every patch should undergo human review before merging.
