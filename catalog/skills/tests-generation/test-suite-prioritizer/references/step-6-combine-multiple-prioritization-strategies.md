### Step 6: Combine Multiple Prioritization Strategies

**Python:**
```python
from dataclasses import dataclass


@dataclass
class CompositeScore:
    test_name: str
    failure_score: float
    risk_score: float
    coverage_efficiency: float
    execution_time: float


class CompositePrioritizer:
    """Combine multiple prioritization signals into a single ordering."""

    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "failure": 0.40,   # Recent failure history
            "risk": 0.25,      # Business risk of covered modules
            "coverage": 0.20,  # Coverage efficiency (coverage per second)
            "speed": 0.15,     # Execution speed (faster tests first)
        }

    def compute_composite_score(self, scores: CompositeScore) -> float:
        """Weighted combination of all prioritization signals."""
        # Normalize execution time (invert: shorter is better)
        speed_score = 1.0 / max(scores.execution_time, 0.01)
        max_speed = 1.0 / 0.01  # Normalize to 0-1
        speed_normalized = min(speed_score / max_speed, 1.0)

        return (
            self.weights["failure"] * scores.failure_score
            + self.weights["risk"] * scores.risk_score
            + self.weights["coverage"] * scores.coverage_efficiency
            + self.weights["speed"] * speed_normalized
        )

    def prioritize(self, test_scores: list[CompositeScore]) -> list[str]:
        """Return test names sorted by composite priority (highest first)."""
        scored = [
            (ts.test_name, self.compute_composite_score(ts))
            for ts in test_scores
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored]


# Usage
scores = [
    CompositeScore("test_login", failure_score=0.8, risk_score=0.9,
                   coverage_efficiency=0.5, execution_time=0.3),
    CompositeScore("test_signup", failure_score=0.2, risk_score=0.9,
                   coverage_efficiency=0.7, execution_time=1.2),
    CompositeScore("test_color_theme", failure_score=0.0, risk_score=0.1,
                   coverage_efficiency=0.3, execution_time=0.1),
    CompositeScore("test_payment", failure_score=0.5, risk_score=1.0,
                   coverage_efficiency=0.8, execution_time=2.5),
]

prioritizer = CompositePrioritizer()
ordered = prioritizer.prioritize(scores)
print("Prioritized order:")
for i, name in enumerate(ordered, 1):
    print(f"  {i}. {name}")
```
