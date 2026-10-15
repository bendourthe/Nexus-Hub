### Step 1: Implement Failure History Prioritization

**Python:**
```python
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class TestExecutionRecord:
    test_name: str
    passed: bool
    duration_seconds: float
    timestamp: datetime


@dataclass
class FailureHistoryPrioritizer:
    """Prioritize tests based on their recent failure history."""

    history_file: Path
    history: dict = field(default_factory=dict)

    def load(self):
        """Load execution history from disk."""
        if self.history_file.exists():
            raw = json.loads(self.history_file.read_text())
            self.history = raw
        return self

    def save(self):
        """Persist execution history to disk."""
        self.history_file.write_text(json.dumps(self.history, indent=2, default=str))

    def record(self, result: TestExecutionRecord):
        """Record a test execution result."""
        if result.test_name not in self.history:
            self.history[result.test_name] = {
                "runs": [],
                "total_runs": 0,
                "total_failures": 0,
            }
        entry = self.history[result.test_name]
        entry["runs"].append({
            "passed": result.passed,
            "duration": result.duration_seconds,
            "timestamp": result.timestamp.isoformat(),
        })
        entry["total_runs"] += 1
        if not result.passed:
            entry["total_failures"] += 1
        # Keep only last 100 runs
        entry["runs"] = entry["runs"][-100:]

    def failure_score(self, test_name: str, window: int = 20) -> float:
        """Calculate a failure priority score (higher = more likely to fail).

        Score components:
        - Recent failure rate (last `window` runs)
        - Recency bonus (failures in the last 5 runs score higher)
        - Failure streak bonus (consecutive recent failures)
        """
        entry = self.history.get(test_name)
        if not entry or not entry["runs"]:
            return 0.5  # Unknown tests get medium priority

        recent_runs = entry["runs"][-window:]
        recent_failures = sum(1 for r in recent_runs if not r["passed"])
        failure_rate = recent_failures / len(recent_runs)

        # Recency bonus: failures in last 5 runs
        last_5 = entry["runs"][-5:]
        recent_failure_count = sum(1 for r in last_5 if not r["passed"])
        recency_bonus = recent_failure_count * 0.1

        # Streak bonus: consecutive failures from the most recent run
        streak = 0
        for r in reversed(entry["runs"]):
            if not r["passed"]:
                streak += 1
            else:
                break
        streak_bonus = min(streak * 0.05, 0.25)

        return min(failure_rate + recency_bonus + streak_bonus, 1.0)

    def prioritize(self, test_names: list[str]) -> list[str]:
        """Return test names sorted by failure priority (highest first)."""
        scored = [(name, self.failure_score(name)) for name in test_names]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored]


# Usage in a pytest plugin
def pytest_collection_modifyitems(config, items):
    """Reorder tests by failure history priority."""
    prioritizer = FailureHistoryPrioritizer(
        Path(".test_history.json")
    ).load()

    test_names = [item.nodeid for item in items]
    ordered_names = prioritizer.prioritize(test_names)

    name_to_index = {name: i for i, name in enumerate(ordered_names)}
    items.sort(key=lambda item: name_to_index.get(item.nodeid, len(ordered_names)))
```

**JavaScript (Jest custom sequencer):**
```javascript
// test-sequencer.js
const Sequencer = require("@jest/test-sequencer").default;
const fs = require("fs");
const path = require("path");

const HISTORY_FILE = path.join(process.cwd(), ".test_history.json");

class FailureHistorySequencer extends Sequencer {
  constructor() {
    super();
    this.history = this.loadHistory();
  }

  loadHistory() {
    try {
      return JSON.parse(fs.readFileSync(HISTORY_FILE, "utf-8"));
    } catch {
      return {};
    }
  }

  failureScore(testPath) {
    const entry = this.history[testPath];
    if (!entry || !entry.runs || entry.runs.length === 0) {
      return 0.5;
    }

    const recent = entry.runs.slice(-20);
    const failureRate = recent.filter((r) => !r.passed).length / recent.length;

    const last5 = entry.runs.slice(-5);
    const recentFailures = last5.filter((r) => !r.passed).length;
    const recencyBonus = recentFailures * 0.1;

    return Math.min(failureRate + recencyBonus, 1.0);
  }

  sort(tests) {
    return [...tests].sort((a, b) => {
      const scoreA = this.failureScore(a.path);
      const scoreB = this.failureScore(b.path);
      return scoreB - scoreA;
    });
  }
}

module.exports = FailureHistorySequencer;

// jest.config.js:
// module.exports = {
//   testSequencer: "./test-sequencer.js",
// };
```

**Java (JUnit 5 with custom test order):**
```java
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.MethodOrdererContext;
import org.junit.jupiter.api.TestMethodOrder;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Custom method orderer that prioritizes tests by failure history.
 */
public class FailureHistoryOrderer implements MethodOrderer {

    private static final Path HISTORY_FILE = Path.of(".test_history.json");
    private Map<String, Map<String, Object>> history;

    @Override
    public void orderMethods(MethodOrdererContext context) {
        loadHistory();
        context.getMethodDescriptors().sort((a, b) -> {
            double scoreA = failureScore(a.getMethod().getName());
            double scoreB = failureScore(b.getMethod().getName());
            return Double.compare(scoreB, scoreA);
        });
    }

    private void loadHistory() {
        try {
            if (Files.exists(HISTORY_FILE)) {
                var mapper = new ObjectMapper();
                history = mapper.readValue(
                        HISTORY_FILE.toFile(),
                        mapper.getTypeFactory().constructMapType(
                                HashMap.class, String.class, Map.class)
                );
            } else {
                history = new HashMap<>();
            }
        } catch (IOException e) {
            history = new HashMap<>();
        }
    }

    private double failureScore(String testName) {
        var entry = history.get(testName);
        if (entry == null) return 0.5;

        @SuppressWarnings("unchecked")
        var runs = (List<Map<String, Object>>) entry.get("runs");
        if (runs == null || runs.isEmpty()) return 0.5;

        var recent = runs.subList(Math.max(0, runs.size() - 20), runs.size());
        long failures = recent.stream()
                .filter(r -> !(boolean) r.get("passed"))
                .count();
        return (double) failures / recent.size();
    }
}

// Usage:
// @TestMethodOrder(FailureHistoryOrderer.class)
// class MyTest { ... }
```
