### Step 4: Implement Risk-Based Ordering

**Python:**
```python
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleRiskProfile:
    module_path: str
    business_criticality: float   # 0.0 to 1.0
    defect_density: float         # bugs per KLOC
    change_frequency: float       # commits per month
    complexity: float             # cyclomatic complexity average


class RiskBasedPrioritizer:
    """Prioritize tests by the risk score of the modules they cover."""

    def __init__(self, risk_profiles: list[ModuleRiskProfile],
                 test_to_modules: dict):
        """
        Args:
            risk_profiles: Risk profile for each module.
            test_to_modules: Mapping from test name to list of modules it covers.
        """
        self.risk_scores = {}
        for profile in risk_profiles:
            score = (
                profile.business_criticality * 0.4
                + profile.defect_density * 0.25
                + profile.change_frequency * 0.2
                + profile.complexity * 0.15
            )
            self.risk_scores[profile.module_path] = score

        self.test_to_modules = test_to_modules

    def test_risk_score(self, test_name: str) -> float:
        """Calculate the aggregate risk score for a test based on the modules it covers."""
        modules = self.test_to_modules.get(test_name, [])
        if not modules:
            return 0.0
        return max(self.risk_scores.get(m, 0.0) for m in modules)

    def prioritize(self, test_names: list[str]) -> list[str]:
        """Return tests ordered by risk score (highest risk first)."""
        scored = [(name, self.test_risk_score(name)) for name in test_names]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored]


def compute_change_frequency(repo_path: str, module_path: str,
                              months: int = 3) -> float:
    """Count commits touching a module in the last N months."""
    since = f"{months} months ago"
    result = subprocess.run(
        ["git", "log", f"--since={since}", "--oneline", "--", module_path],
        capture_output=True, text=True, cwd=repo_path,
    )
    return len(result.stdout.strip().splitlines())
```
