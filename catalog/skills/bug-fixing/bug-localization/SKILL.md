---
name: bug-localization
description: Pinpoint bug locations using stack traces, error logs, code flow analysis, spectrum-based fault localization, and bisection techniques. Use when debugging failures, analyzing stack traces, tracing error origins, or narrowing down faulty code regions.
---

# Bug Localization

Systematically pinpoint the exact location of bugs in a codebase using a combination of stack trace analysis, error log correlation, code flow tracing, spectrum-based fault localization, and bisection techniques. This skill transforms vague symptoms into precise file-and-line identification.

## When to Use This Skill

Use this skill when you need to:

- Determine which file, class, or function contains a bug based on an error report
- Analyze stack traces to find the true origin of an exception (not just where it surfaced)
- Correlate multiple log entries to identify the point where behavior diverges from expectations
- Apply statistical fault localization techniques (Tarantula, Ochiai) to test suite results
- Use git bisect or delta debugging to narrow down the commit or change that introduced a defect
- Trace data flow through a system to find where values become incorrect
- Identify the root cause when an error manifests far from its origin

**Trigger phrases**: "find the bug", "localize the fault", "where is the bug", "trace the error", "analyze stack trace", "narrow down the issue", "which commit broke", "bisect the failure", "fault localization"

## What This Skill Does

### Methodology Overview

Bug localization follows a structured narrowing process that moves from broad symptom identification to precise fault location. The methodology combines multiple complementary techniques, each suited to different types of information available.

### Technique 1: Stack Trace Analysis

Stack traces are the most direct signal for localization. The skill teaches you to read them bottom-up (for languages where the root cause appears at the bottom) or top-down (for languages where it appears at the top), identify framework frames versus application frames, and distinguish the "caused by" chain to find the originating fault.

### Technique 2: Log Correlation

When stack traces are unavailable or insufficient, correlating log entries across time and components reveals the divergence point. This technique uses timestamps, request IDs, and contextual markers to reconstruct the execution timeline and identify where expected behavior stopped.

### Technique 3: Spectrum-Based Fault Localization (SBFL)

SBFL techniques use test execution data to statistically rank program elements by their suspiciousness. Elements executed primarily by failing tests (and rarely by passing tests) receive high suspiciousness scores. The two most effective formulas are Tarantula and Ochiai.

### Technique 4: Code Flow Tracing

When statistical methods are not applicable (for example, when there is only one failing test), manual or tool-assisted code flow tracing follows data from input to the point of failure, checking invariants at each step.

### Technique 5: Delta Debugging and Bisection

When a bug was introduced by a recent change, bisection (via git bisect or manual binary search) efficiently identifies the exact commit. Delta debugging extends this to isolate the minimal change within a commit that triggers the failure.

## Instructions

### Step 1: Gather and Classify Symptoms

Before attempting localization, collect all available evidence and classify the type of failure.

**Failure classification table:**

| Category | Symptoms | Primary Technique |
|----------|----------|-------------------|
| Crash / Exception | Stack trace, core dump | Stack Trace Analysis |
| Wrong Output | Incorrect values, failed assertions | Code Flow Tracing |
| Performance Degradation | Slow response, timeouts | Log Correlation + Profiling |
| Intermittent Failure | Flaky tests, race conditions | Log Correlation + Bisection |
| Regression | Previously passing test now fails | Git Bisect + Diff Analysis |

**Python: Collecting failure information**

```python
import traceback
import logging
import sys

logger = logging.getLogger(__name__)

def collect_failure_context(exception: Exception) -> dict:
    """Gather comprehensive failure context for bug localization."""
    tb = traceback.extract_tb(exception.__traceback__)

    context = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "frames": [],
        "variables_at_fault": {},
    }

    for frame_summary in tb:
        context["frames"].append({
            "file": frame_summary.filename,
            "line": frame_summary.lineno,
            "function": frame_summary.name,
            "code": frame_summary.line,
        })

    # Capture local variables from the innermost frame
    if exception.__traceback__:
        inner_frame = exception.__traceback__
        while inner_frame.tb_next:
            inner_frame = inner_frame.tb_next
        context["variables_at_fault"] = {
            k: repr(v) for k, v in inner_frame.tb_frame.f_locals.items()
            if not k.startswith("__")
        }

    return context


def classify_failure(context: dict) -> str:
    """Classify the failure type to guide localization strategy."""
    exc_type = context["exception_type"]

    crash_types = {"SegmentationFault", "SystemError", "MemoryError"}
    value_types = {"AssertionError", "ValueError", "TypeError"}
    io_types = {"ConnectionError", "TimeoutError", "FileNotFoundError"}

    if exc_type in crash_types:
        return "crash"
    elif exc_type in value_types:
        return "wrong_output"
    elif exc_type in io_types:
        return "io_failure"
    else:
        return "unknown"
```

**JavaScript: Collecting failure information**

```javascript
function collectFailureContext(error) {
  const stackLines = error.stack?.split("\n") || [];
  const frames = stackLines
    .filter(line => line.includes("at "))
    .map(line => {
      const match = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
      if (match) {
        return {
          function: match[1],
          file: match[2],
          line: parseInt(match[3], 10),
          column: parseInt(match[4], 10),
        };
      }
      const simpleMatch = line.match(/at\s+(.+?):(\d+):(\d+)/);
      if (simpleMatch) {
        return {
          function: "<anonymous>",
          file: simpleMatch[1],
          line: parseInt(simpleMatch[2], 10),
          column: parseInt(simpleMatch[3], 10),
        };
      }
      return null;
    })
    .filter(Boolean);

  return {
    errorType: error.constructor.name,
    message: error.message,
    frames,
    applicationFrames: frames.filter(
      f => !f.file.includes("node_modules") && !f.file.includes("internal/")
    ),
  };
}

function classifyFailure(context) {
  const typeMap = {
    TypeError: "wrong_output",
    RangeError: "wrong_output",
    ReferenceError: "crash",
    SyntaxError: "crash",
    AssertionError: "wrong_output",
  };
  return typeMap[context.errorType] || "unknown";
}
```

**Java: Collecting failure information**

```java
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.stream.Collectors;

public class FailureContextCollector {

    public static Map<String, Object> collectContext(Throwable throwable) {
        Map<String, Object> context = new HashMap<>();
        context.put("exceptionType", throwable.getClass().getSimpleName());
        context.put("message", throwable.getMessage());

        List<Map<String, Object>> frames = Arrays.stream(throwable.getStackTrace())
            .map(frame -> {
                Map<String, Object> f = new HashMap<>();
                f.put("class", frame.getClassName());
                f.put("method", frame.getMethodName());
                f.put("file", frame.getFileName());
                f.put("line", frame.getLineNumber());
                return f;
            })
            .collect(Collectors.toList());

        context.put("frames", frames);

        // Filter to application frames (exclude JDK and framework internals)
        List<Map<String, Object>> appFrames = frames.stream()
            .filter(f -> {
                String cls = (String) f.get("class");
                return !cls.startsWith("java.")
                    && !cls.startsWith("javax.")
                    && !cls.startsWith("sun.")
                    && !cls.startsWith("org.springframework.cglib");
            })
            .collect(Collectors.toList());
        context.put("applicationFrames", appFrames);

        // Walk the cause chain
        Throwable cause = throwable.getCause();
        if (cause != null) {
            context.put("rootCause", collectContext(cause));
        }

        return context;
    }

    public static String classifyFailure(Map<String, Object> context) {
        String type = (String) context.get("exceptionType");
        if (type.contains("NullPointer") || type.contains("ClassCast")) {
            return "wrong_output";
        } else if (type.contains("OutOfMemory") || type.contains("StackOverflow")) {
            return "crash";
        } else if (type.contains("Timeout") || type.contains("Connection")) {
            return "io_failure";
        }
        return "unknown";
    }
}
```

### Step 2: Analyze Stack Traces

Stack traces require careful reading. The goal is to separate framework noise from application fault points and follow the "caused by" chain to the root.

**Key principles for stack trace analysis:**

1. Identify the exception type and message first; they often indicate the category of bug.
2. Scan for the first application frame (skip framework and standard library frames).
3. Follow "Caused by" chains to the deepest cause; the root cause is typically the last "Caused by" entry.
4. Look for repeated frames (recursive calls) that may indicate infinite recursion.
5. Note the transition points between your code and library code; the bug is usually at the boundary.

**Python: Stack trace parser**

```python
def parse_python_traceback(traceback_text: str) -> list[dict]:
    """Parse a Python traceback string into structured frames."""
    import re
    frames = []
    pattern = r'File "(.+?)", line (\d+), in (.+?)\n\s+(.+)'

    for match in re.finditer(pattern, traceback_text):
        frames.append({
            "file": match.group(1),
            "line": int(match.group(2)),
            "function": match.group(3),
            "code": match.group(4).strip(),
        })

    return frames


def find_application_fault_point(frames: list[dict], app_root: str) -> dict | None:
    """Find the deepest application frame (most likely fault location)."""
    app_frames = [f for f in frames if app_root in f["file"]]
    if app_frames:
        # In Python tracebacks, the last frame is the deepest
        return app_frames[-1]
    return None


def find_boundary_frame(frames: list[dict], app_root: str) -> tuple[dict, dict] | None:
    """Find where application code transitions to library code."""
    for i in range(len(frames) - 1):
        current_is_app = app_root in frames[i]["file"]
        next_is_lib = app_root not in frames[i + 1]["file"]
        if current_is_app and next_is_lib:
            return (frames[i], frames[i + 1])
    return None
```

**JavaScript: Stack trace parser**

```javascript
function parseNodeStackTrace(stackText) {
  const lines = stackText.split("\n");
  const errorLine = lines[0];
  const [errorType, ...messageParts] = errorLine.split(": ");
  const message = messageParts.join(": ");

  const frames = lines.slice(1).map(line => {
    const match = line.trim().match(
      /^at\s+(?:(.+?)\s+\()?(.+?):(\d+):(\d+)\)?$/
    );
    if (!match) return null;
    return {
      function: match[1] || "<anonymous>",
      file: match[2],
      line: parseInt(match[3], 10),
      column: parseInt(match[4], 10),
      isInternal: match[2].startsWith("node:") ||
                  match[2].includes("node_modules"),
    };
  }).filter(Boolean);

  return { errorType, message, frames };
}

function findApplicationFaultPoint(frames, projectRoot) {
  const appFrames = frames.filter(
    f => f.file.startsWith(projectRoot) && !f.isInternal
  );
  // In V8 stack traces, the first frame is the deepest
  return appFrames[0] || null;
}
```

**Java: Stack trace parser**

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.List;

public class StackTraceAnalyzer {
    private static final Pattern FRAME_PATTERN = Pattern.compile(
        "\\s+at\\s+([\\w.$]+)\\.([\\w$]+)\\(([\\w.]+):(\\d+)\\)"
    );
    private static final Pattern CAUSED_BY_PATTERN = Pattern.compile(
        "Caused by:\\s+([\\w.]+):\\s*(.*)"
    );

    public record StackFrame(String className, String method,
                             String file, int line) {}

    public record CauseChain(String exceptionType, String message,
                             List<StackFrame> frames) {}

    public static List<CauseChain> parseCauseChain(String stackTrace) {
        List<CauseChain> causes = new ArrayList<>();
        String[] sections = stackTrace.split("(?=Caused by:)");

        for (String section : sections) {
            Matcher causeMatcher = CAUSED_BY_PATTERN.matcher(section);
            String exType = "primary";
            String msg = "";
            if (causeMatcher.find()) {
                exType = causeMatcher.group(1);
                msg = causeMatcher.group(2);
            }

            List<StackFrame> frames = new ArrayList<>();
            Matcher frameMatcher = FRAME_PATTERN.matcher(section);
            while (frameMatcher.find()) {
                frames.add(new StackFrame(
                    frameMatcher.group(1),
                    frameMatcher.group(2),
                    frameMatcher.group(3),
                    Integer.parseInt(frameMatcher.group(4))
                ));
            }
            causes.add(new CauseChain(exType, msg, frames));
        }
        return causes;
    }

    public static StackFrame findRootApplicationFrame(
            List<CauseChain> causes, String appPackagePrefix) {
        // Start from the deepest cause
        for (int i = causes.size() - 1; i >= 0; i--) {
            for (StackFrame frame : causes.get(i).frames()) {
                if (frame.className().startsWith(appPackagePrefix)) {
                    return frame;
                }
            }
        }
        return null;
    }
}
```

### Step 3: Correlate Log Entries

When stack traces alone are insufficient, log correlation reconstructs the execution timeline to find where behavior diverged.

**Python: Log correlation engine**

```python
import re
from datetime import datetime
from collections import defaultdict

class LogCorrelator:
    """Correlate log entries to find the divergence point."""

    TIMESTAMP_PATTERN = re.compile(
        r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    )
    LEVEL_PATTERN = re.compile(
        r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b"
    )

    def __init__(self):
        self.entries = []

    def parse_log_file(self, filepath: str, source_label: str = ""):
        """Parse a log file into structured entries."""
        with open(filepath) as f:
            for line_num, line in enumerate(f, 1):
                ts_match = self.TIMESTAMP_PATTERN.search(line)
                level_match = self.LEVEL_PATTERN.search(line)
                self.entries.append({
                    "timestamp": ts_match.group(1) if ts_match else None,
                    "level": level_match.group(1) if level_match else "UNKNOWN",
                    "message": line.strip(),
                    "source": source_label or filepath,
                    "line_number": line_num,
                })

    def find_error_context(self, window_seconds: float = 5.0) -> list[dict]:
        """Find log entries surrounding the first error."""
        error_entries = [
            e for e in self.entries
            if e["level"] in ("ERROR", "FATAL", "CRITICAL")
        ]
        if not error_entries:
            return []

        first_error = error_entries[0]
        if not first_error["timestamp"]:
            return [first_error]

        error_time = datetime.fromisoformat(first_error["timestamp"])
        context = []
        for entry in self.entries:
            if entry["timestamp"]:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                delta = abs((entry_time - error_time).total_seconds())
                if delta <= window_seconds:
                    context.append(entry)
        return sorted(context, key=lambda e: e["timestamp"] or "")

    def find_request_trace(self, request_id: str) -> list[dict]:
        """Extract all log entries for a specific request ID."""
        return [
            e for e in self.entries
            if request_id in e["message"]
        ]
```

**JavaScript: Log correlation**

```javascript
class LogCorrelator {
  constructor() {
    this.entries = [];
  }

  parseLine(line, source = "") {
    const tsMatch = line.match(
      /(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)/
    );
    const levelMatch = line.match(
      /\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b/
    );
    return {
      timestamp: tsMatch ? new Date(tsMatch[1]) : null,
      level: levelMatch ? levelMatch[1] : "UNKNOWN",
      message: line.trim(),
      source,
    };
  }

  addLogLines(lines, source = "") {
    for (const line of lines) {
      this.entries.push(this.parseLine(line, source));
    }
  }

  findErrorContext(windowMs = 5000) {
    const errors = this.entries.filter(
      e => ["ERROR", "FATAL", "CRITICAL"].includes(e.level)
    );
    if (errors.length === 0) return [];

    const firstError = errors[0];
    if (!firstError.timestamp) return [firstError];

    return this.entries
      .filter(e => {
        if (!e.timestamp) return false;
        const delta = Math.abs(e.timestamp - firstError.timestamp);
        return delta <= windowMs;
      })
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  traceRequest(requestId) {
    return this.entries.filter(e => e.message.includes(requestId));
  }
}
```

### Step 4: Apply Spectrum-Based Fault Localization

When you have a test suite with both passing and failing tests, SBFL ranks code elements by suspiciousness.

**Suspiciousness formulas:**

| Formula | Definition | Strengths |
|---------|-----------|-----------|
| Tarantula | (failed/totalFailed) / ((failed/totalFailed) + (passed/totalPassed)) | Balanced, widely studied |
| Ochiai | failed / sqrt(totalFailed * (failed + passed)) | Better empirical accuracy |
| Dstar (D*) | failed^2 / (passed + (totalFailed - failed)) | Best for large test suites |

**Python: SBFL implementation**

```python
import math
from dataclasses import dataclass

@dataclass
class CoverageData:
    """Coverage data for a single program element (line or function)."""
    element_id: str       # e.g., "src/utils.py:42"
    passed_count: int     # number of passing tests that execute this element
    failed_count: int     # number of failing tests that execute this element

def tarantula(element: CoverageData, total_passed: int, total_failed: int) -> float:
    """Compute Tarantula suspiciousness score."""
    if total_failed == 0 or total_passed == 0:
        return 0.0
    fail_ratio = element.failed_count / total_failed
    pass_ratio = element.passed_count / total_passed
    denominator = fail_ratio + pass_ratio
    if denominator == 0:
        return 0.0
    return fail_ratio / denominator

def ochiai(element: CoverageData, total_failed: int) -> float:
    """Compute Ochiai suspiciousness score."""
    total_executions = element.passed_count + element.failed_count
    denominator = math.sqrt(total_failed * total_executions)
    if denominator == 0:
        return 0.0
    return element.failed_count / denominator

def dstar(element: CoverageData, total_failed: int, star: int = 2) -> float:
    """Compute D* suspiciousness score."""
    not_failed = total_failed - element.failed_count
    denominator = element.passed_count + not_failed
    if denominator == 0:
        return float("inf") if element.failed_count > 0 else 0.0
    return (element.failed_count ** star) / denominator

def rank_suspicious_elements(
    coverage: list[CoverageData],
    total_passed: int,
    total_failed: int,
    formula: str = "ochiai",
) -> list[tuple[str, float]]:
    """Rank all program elements by suspiciousness score."""
    score_fn = {
        "tarantula": lambda e: tarantula(e, total_passed, total_failed),
        "ochiai": lambda e: ochiai(e, total_failed),
        "dstar": lambda e: dstar(e, total_failed),
    }[formula]

    scored = [(elem.element_id, score_fn(elem)) for elem in coverage]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
```

**JavaScript: SBFL implementation**

```javascript
function tarantula(failedCount, passedCount, totalFailed, totalPassed) {
  if (totalFailed === 0 || totalPassed === 0) return 0;
  const failRatio = failedCount / totalFailed;
  const passRatio = passedCount / totalPassed;
  const denom = failRatio + passRatio;
  return denom === 0 ? 0 : failRatio / denom;
}

function ochiai(failedCount, passedCount, totalFailed) {
  const totalExec = failedCount + passedCount;
  const denom = Math.sqrt(totalFailed * totalExec);
  return denom === 0 ? 0 : failedCount / denom;
}

function rankSuspiciousElements(coverageData, totalPassed, totalFailed) {
  return coverageData
    .map(elem => ({
      elementId: elem.elementId,
      tarantula: tarantula(
        elem.failedCount, elem.passedCount, totalFailed, totalPassed
      ),
      ochiai: ochiai(elem.failedCount, elem.passedCount, totalFailed),
    }))
    .sort((a, b) => b.ochiai - a.ochiai);
}
```

**Java: SBFL implementation**

```java
import java.util.*;
import java.util.stream.Collectors;

public class FaultLocalizer {
    public record CoverageElement(String elementId, int passedCount,
                                   int failedCount) {}

    public static double tarantula(CoverageElement elem,
                                    int totalPassed, int totalFailed) {
        if (totalFailed == 0 || totalPassed == 0) return 0.0;
        double failRatio = (double) elem.failedCount() / totalFailed;
        double passRatio = (double) elem.passedCount() / totalPassed;
        double denom = failRatio + passRatio;
        return denom == 0 ? 0.0 : failRatio / denom;
    }

    public static double ochiai(CoverageElement elem, int totalFailed) {
        int totalExec = elem.passedCount() + elem.failedCount();
        double denom = Math.sqrt((double) totalFailed * totalExec);
        return denom == 0 ? 0.0 : elem.failedCount() / denom;
    }

    public static List<Map.Entry<String, Double>> rankElements(
            List<CoverageElement> coverage,
            int totalPassed, int totalFailed) {
        return coverage.stream()
            .map(elem -> Map.entry(
                elem.elementId(),
                ochiai(elem, totalFailed)
            ))
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .collect(Collectors.toList());
    }
}
```

### Step 5: Use Git Bisect for Regression Localization

When a test that previously passed now fails, git bisect efficiently finds the exact commit that introduced the regression.

**Bash: Automated git bisect**

```bash
#!/usr/bin/env bash
# Automated git bisect with a test command
# Usage: ./bisect.sh <good_commit> <bad_commit> <test_command>

GOOD_COMMIT="$1"
BAD_COMMIT="$2"
TEST_CMD="$3"

git bisect start "$BAD_COMMIT" "$GOOD_COMMIT"
git bisect run sh -c "$TEST_CMD"

echo "First bad commit:"
git bisect visualize --oneline | head -1

git bisect reset
```

**Python: Programmatic bisect driver**

```python
import subprocess

def git_bisect_automated(
    good_commit: str,
    bad_commit: str,
    test_command: str,
    repo_path: str = ".",
) -> str:
    """Run git bisect and return the first bad commit hash."""
    def run(cmd: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, shell=True, cwd=repo_path,
            capture_output=True, text=True,
        )

    run(f"git bisect start {bad_commit} {good_commit}")
    result = run(f"git bisect run sh -c '{test_command}'")

    # Extract the first bad commit from bisect output
    for line in result.stdout.splitlines():
        if "is the first bad commit" in line:
            commit_hash = line.split()[0]
            run("git bisect reset")
            return commit_hash

    run("git bisect reset")
    return "unknown"
```

### Step 6: Apply Delta Debugging

Delta debugging narrows a failing input or change set to its minimal failing subset.

**Python: Delta debugging algorithm**

```python
def delta_debug(changes: list, test_fn) -> list:
    """Find the minimal subset of changes that still triggers the failure.

    Args:
        changes: List of individual changes (lines, commits, etc.).
        test_fn: Callable that returns True if the bug is still present
                 with the given subset of changes.

    Returns:
        Minimal failing subset.
    """
    n = 2
    while len(changes) >= 2:
        chunk_size = max(len(changes) // n, 1)
        chunks = [
            changes[i:i + chunk_size]
            for i in range(0, len(changes), chunk_size)
        ]

        found_smaller = False
        for chunk in chunks:
            if test_fn(chunk):
                changes = chunk
                n = 2
                found_smaller = True
                break

        if not found_smaller:
            complement_found = False
            for chunk in chunks:
                complement = [c for c in changes if c not in chunk]
                if test_fn(complement):
                    changes = complement
                    n = 2
                    complement_found = True
                    break

            if not complement_found:
                if n >= len(changes):
                    break
                n = min(n * 2, len(changes))

    return changes
```

## Best Practices

- Always start with the cheapest technique first: reading the error message and stack trace carefully costs nothing and often suffices.
- Filter out framework and library frames before analyzing stack traces; focus on your application code.
- When correlating logs, use structured logging with request IDs so that you can reconstruct per-request timelines across distributed systems.
- Combine SBFL with manual inspection: suspiciousness scores are a ranking aid, not a guarantee. Examine the top 5-10 elements manually.
- Automate git bisect with a reliable test script. A flaky test will produce incorrect bisect results.
- Document the localization process and findings so that future developers facing similar symptoms can reuse the approach.
- For intermittent bugs, collect data from multiple failure instances before attempting localization; a single instance may be misleading.
- Keep your test suite healthy: SBFL accuracy depends on having a diverse set of passing and failing tests with varied coverage patterns.

## Common Pitfalls

- **Reading stack traces from the wrong end.** Python tracebacks show the most recent call last (bottom is the fault point), while Java and JavaScript show the most recent call first (top is the fault point). Confusing this wastes significant time.
- **Stopping at the symptom instead of the cause.** A NullPointerException at line 42 does not mean line 42 is buggy; the null value may have been introduced hundreds of lines earlier. Always trace back to where the incorrect value originated.
- **Ignoring "Caused by" chains.** In Java and similar languages, the root cause is at the end of the "Caused by" chain. Fixing the outermost exception without examining the root cause leads to superficial patches.
- **Trusting SBFL scores blindly.** A suspiciousness score of 1.0 does not guarantee that the element is faulty. It means the element is statistically correlated with failure, which may be coincidental.
- **Running git bisect with a flaky test.** If the test intermittently passes on the bad commit, bisect will produce incorrect results. Verify that the test reliably fails on the known-bad commit before starting.
- **Over-relying on a single technique.** No single localization method works for every bug type. Use stack trace analysis, log correlation, SBFL, and bisection as complementary tools, not alternatives.
- **Neglecting to check environment differences.** A bug that manifests in CI but not locally may be caused by environment differences (timezone, locale, file system permissions) rather than code logic errors. Always compare environments before deep-diving into code.
- **Failing to reproduce before localizing.** Attempting to localize a bug you cannot consistently reproduce leads to speculation. Establish a reliable reproduction first, then apply localization techniques.
