### Step 3: Implement Coverage-Based Prioritization

**Python:**
```python
from dataclasses import dataclass


@dataclass
class TestCoverageInfo:
    test_name: str
    covered_lines: set  # {(file, line_number), ...}
    duration_seconds: float


class CoverageBasedPrioritizer:
    """Prioritize tests to maximize cumulative coverage gain per unit time."""

    def __init__(self, test_coverage: list[TestCoverageInfo]):
        self.test_coverage = test_coverage

    def prioritize_greedy(self) -> list[str]:
        """Greedy algorithm: at each step, select the test that covers the
        most uncovered lines per second of execution time."""
        remaining = list(self.test_coverage)
        covered = set()
        ordered = []

        while remaining:
            best = None
            best_score = -1

            for tc in remaining:
                new_coverage = tc.covered_lines - covered
                if tc.duration_seconds > 0:
                    score = len(new_coverage) / tc.duration_seconds
                else:
                    score = len(new_coverage) * 1000  # Instant tests score very high

                if score > best_score:
                    best_score = score
                    best = tc

            if best is None or best_score <= 0:
                # Remaining tests add no new coverage; append in original order
                ordered.extend(tc.test_name for tc in remaining)
                break

            ordered.append(best.test_name)
            covered |= best.covered_lines
            remaining.remove(best)

        return ordered

    def coverage_at_position(self, ordered: list[str], position: int) -> float:
        """Calculate cumulative coverage percentage at a given position in the ordering."""
        all_lines = set()
        for tc in self.test_coverage:
            all_lines |= tc.covered_lines

        covered = set()
        test_map = {tc.test_name: tc for tc in self.test_coverage}
        for name in ordered[:position]:
            if name in test_map:
                covered |= test_map[name].covered_lines

        return len(covered) / max(len(all_lines), 1) * 100


# Example usage
tests = [
    TestCoverageInfo("test_login", {("auth.py", 1), ("auth.py", 2), ("auth.py", 3)}, 0.5),
    TestCoverageInfo("test_signup", {("auth.py", 1), ("auth.py", 10), ("auth.py", 11)}, 0.8),
    TestCoverageInfo("test_logout", {("auth.py", 20), ("auth.py", 21)}, 0.2),
    TestCoverageInfo("test_profile", {("user.py", 1), ("user.py", 2)}, 1.5),
]

prioritizer = CoverageBasedPrioritizer(tests)
ordered = prioritizer.prioritize_greedy()
print("Prioritized order:", ordered)
for i in range(1, len(ordered) + 1):
    cov = prioritizer.coverage_at_position(ordered, i)
    print(f"  After {i} tests: {cov:.1f}% coverage")
```
