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
