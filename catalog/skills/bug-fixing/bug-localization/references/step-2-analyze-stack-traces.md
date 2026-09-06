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
