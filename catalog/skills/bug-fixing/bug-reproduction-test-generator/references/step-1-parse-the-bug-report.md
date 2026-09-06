### Step 1: Parse the Bug Report

Extract structured information from the bug report to guide test generation.

**Python: Bug report to test specification**

```python
from dataclasses import dataclass, field
import re

@dataclass
class TestSpecification:
    """Structured specification extracted from a bug report."""
    bug_id: str = ""
    title: str = ""
    module_under_test: str = ""
    function_under_test: str = ""
    input_values: dict = field(default_factory=dict)
    expected_output: str = ""
    actual_output: str = ""
    error_type: str = ""
    error_message: str = ""
    preconditions: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)

def extract_test_spec(bug_report_text: str) -> TestSpecification:
    """Extract a test specification from a bug report."""
    spec = TestSpecification()

    # Extract bug ID from common formats
    id_match = re.search(r"(?:BUG|ISSUE|TICKET)[- #](\d+)", bug_report_text, re.IGNORECASE)
    if id_match:
        spec.bug_id = id_match.group(1)

    # Extract expected vs actual behavior
    expected_match = re.search(
        r"(?:expected|should)\s*(?:behavior|result|output)?[:\s]+(.+?)(?:\n|$)",
        bug_report_text, re.IGNORECASE,
    )
    if expected_match:
        spec.expected_output = expected_match.group(1).strip()

    actual_match = re.search(
        r"(?:actual|instead|but)\s*(?:behavior|result|output)?[:\s]+(.+?)(?:\n|$)",
        bug_report_text, re.IGNORECASE,
    )
    if actual_match:
        spec.actual_output = actual_match.group(1).strip()

    # Extract error information
    error_match = re.search(
        r"((?:Error|Exception|TypeError|ValueError|KeyError|NullPointer)\w*)[:\s]+(.+?)(?:\n|$)",
        bug_report_text,
    )
    if error_match:
        spec.error_type = error_match.group(1)
        spec.error_message = error_match.group(2).strip()

    # Extract code references
    file_match = re.search(r"(?:in|at|file)\s+[`'\"]?(\w+\.(?:py|js|java|ts))[`'\"]?", bug_report_text, re.IGNORECASE)
    if file_match:
        spec.module_under_test = file_match.group(1)

    func_match = re.search(r"(?:function|method|def)\s+[`'\"]?(\w+)[`'\"]?", bug_report_text, re.IGNORECASE)
    if func_match:
        spec.function_under_test = func_match.group(1)

    return spec


def generate_test_name(spec: TestSpecification) -> str:
    """Generate a descriptive test name from the specification."""
    parts = ["test"]
    if spec.bug_id:
        parts.append(f"bug_{spec.bug_id}")
    if spec.function_under_test:
        parts.append(spec.function_under_test)
    if spec.error_type:
        parts.append(f"raises_{spec.error_type.lower()}")
    elif spec.actual_output:
        sanitized = re.sub(r"[^a-zA-Z0-9]", "_", spec.actual_output[:30])
        parts.append(f"returns_{sanitized}")
    return "_".join(parts)
```

**JavaScript: Bug report to test specification**

```javascript
class TestSpecification {
  constructor() {
    this.bugId = "";
    this.title = "";
    this.moduleUnderTest = "";
    this.functionUnderTest = "";
    this.inputValues = {};
    this.expectedOutput = "";
    this.actualOutput = "";
    this.errorType = "";
    this.errorMessage = "";
    this.preconditions = [];
    this.environment = {};
  }
}

function extractTestSpec(bugReportText) {
  const spec = new TestSpecification();

  const idMatch = bugReportText.match(/(?:BUG|ISSUE|TICKET)[- #](\d+)/i);
  if (idMatch) spec.bugId = idMatch[1];

  const expectedMatch = bugReportText.match(
    /(?:expected|should)\s*(?:behavior|result|output)?[:\s]+(.+?)(?:\n|$)/i
  );
  if (expectedMatch) spec.expectedOutput = expectedMatch[1].trim();

  const actualMatch = bugReportText.match(
    /(?:actual|instead|but)\s*(?:behavior|result|output)?[:\s]+(.+?)(?:\n|$)/i
  );
  if (actualMatch) spec.actualOutput = actualMatch[1].trim();

  const errorMatch = bugReportText.match(
    /((?:Error|Exception|TypeError|RangeError)\w*)[:\s]+(.+?)(?:\n|$)/
  );
  if (errorMatch) {
    spec.errorType = errorMatch[1];
    spec.errorMessage = errorMatch[2].trim();
  }

  const fileMatch = bugReportText.match(
    /(?:in|at|file)\s+[`'"]?(\w+\.(?:js|ts|jsx|tsx))[`'"]?/i
  );
  if (fileMatch) spec.moduleUnderTest = fileMatch[1];

  const funcMatch = bugReportText.match(
    /(?:function|method)\s+[`'"]?(\w+)[`'"]?/i
  );
  if (funcMatch) spec.functionUnderTest = funcMatch[1];

  return spec;
}

function generateTestName(spec) {
  const parts = [];
  if (spec.bugId) parts.push(`bug ${spec.bugId}`);
  if (spec.functionUnderTest) parts.push(spec.functionUnderTest);
  if (spec.errorType) {
    parts.push(`throws ${spec.errorType}`);
  } else if (spec.actualOutput) {
    parts.push(`returns incorrect result`);
  }
  return parts.join(" - ") || "reproduction test";
}
```

**Java: Bug report to test specification**

```java
import java.util.regex.*;
import java.util.*;

public class TestSpecExtractor {
    public record TestSpecification(
        String bugId,
        String title,
        String moduleUnderTest,
        String functionUnderTest,
        String expectedOutput,
        String actualOutput,
        String errorType,
        String errorMessage,
        List<String> preconditions
    ) {}

    public static TestSpecification extract(String bugReportText) {
        String bugId = extractPattern(
            bugReportText, "(?i)(?:BUG|ISSUE|TICKET)[- #](\\d+)"
        );
        String expected = extractPattern(
            bugReportText,
            "(?i)(?:expected|should)\\s*(?:behavior|result|output)?[:\\s]+(.+?)(?:\\n|$)"
        );
        String actual = extractPattern(
            bugReportText,
            "(?i)(?:actual|instead|but)\\s*(?:behavior|result|output)?[:\\s]+(.+?)(?:\\n|$)"
        );
        String errorType = extractPattern(
            bugReportText,
            "((?:Error|Exception|NullPointer|ClassCast)\\w*)[:\\s]"
        );
        String errorMessage = extractPattern(
            bugReportText,
            "(?:Error|Exception|NullPointer|ClassCast)\\w*[:\\s]+(.+?)(?:\\n|$)"
        );
        String module = extractPattern(
            bugReportText,
            "(?i)(?:in|at|class)\\s+[`'\"]?(\\w+(?:\\.\\w+)*)[`'\"]?"
        );
        String function = extractPattern(
            bugReportText,
            "(?i)(?:function|method)\\s+[`'\"]?(\\w+)[`'\"]?"
        );

        return new TestSpecification(
            bugId != null ? bugId : "",
            "", module != null ? module : "",
            function != null ? function : "",
            expected != null ? expected.trim() : "",
            actual != null ? actual.trim() : "",
            errorType != null ? errorType : "",
            errorMessage != null ? errorMessage.trim() : "",
            List.of()
        );
    }

    private static String extractPattern(String text, String regex) {
        Matcher m = Pattern.compile(regex).matcher(text);
        return m.find() ? m.group(1) : null;
    }

    public static String generateTestMethodName(TestSpecification spec) {
        StringBuilder name = new StringBuilder("test");
        if (!spec.bugId().isEmpty()) {
            name.append("Bug").append(spec.bugId()).append("_");
        }
        if (!spec.functionUnderTest().isEmpty()) {
            name.append(spec.functionUnderTest()).append("_");
        }
        if (!spec.errorType().isEmpty()) {
            name.append("Throws").append(
                spec.errorType().replace("Exception", ""));
        } else {
            name.append("ReturnsExpectedResult");
        }
        return name.toString();
    }
}
```
