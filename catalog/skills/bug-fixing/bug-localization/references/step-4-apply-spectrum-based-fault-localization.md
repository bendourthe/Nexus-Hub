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
