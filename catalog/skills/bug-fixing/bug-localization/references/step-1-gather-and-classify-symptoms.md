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
