### Step 2: Implement Test Impact Analysis (Code Change Correlation)

**Python:**
```python
import subprocess
import json
from pathlib import Path


class TestImpactAnalyzer:
    """Select tests based on which source files changed."""

    def __init__(self, coverage_map_file: str = ".coverage_map.json"):
        self.coverage_map_file = Path(coverage_map_file)
        self.coverage_map = {}  # {source_file: [test_file1, test_file2, ...]}

    def build_coverage_map(self):
        """Build a mapping from source files to the tests that cover them.

        Run this after a full test suite execution with coverage enabled.
        """
        # Parse coverage.py JSON report
        coverage_data = json.loads(Path("coverage.json").read_text())

        file_to_tests = {}
        for test_file, file_data in coverage_data.get("files", {}).items():
            executed_lines = file_data.get("executed_lines", [])
            for source_file in file_data.get("contexts", {}).keys():
                if source_file not in file_to_tests:
                    file_to_tests[source_file] = set()
                file_to_tests[source_file].add(test_file)

        self.coverage_map = {k: list(v) for k, v in file_to_tests.items()}
        self.coverage_map_file.write_text(json.dumps(self.coverage_map, indent=2))

    def load_coverage_map(self):
        """Load a previously built coverage map."""
        if self.coverage_map_file.exists():
            self.coverage_map = json.loads(self.coverage_map_file.read_text())
        return self

    def get_changed_files(self, base_ref: str = "main") -> list[str]:
        """Get the list of files changed relative to the base branch."""
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, "HEAD"],
            capture_output=True, text=True,
        )
        return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]

    def select_tests(self, changed_files: list[str] = None) -> list[str]:
        """Select tests that are impacted by the changed files."""
        if changed_files is None:
            changed_files = self.get_changed_files()

        selected_tests = set()
        for changed_file in changed_files:
            # Direct mapping
            if changed_file in self.coverage_map:
                selected_tests.update(self.coverage_map[changed_file])
            # Check for partial path matches (e.g., src/module.py matches module.py)
            for source_file, tests in self.coverage_map.items():
                if changed_file.endswith(source_file) or source_file.endswith(changed_file):
                    selected_tests.update(tests)

        if not selected_tests:
            # If no mapping found, run all tests as a safety net
            return None  # Indicates "run everything"

        return sorted(selected_tests)


# Usage: select and run only impacted tests
analyzer = TestImpactAnalyzer().load_coverage_map()
changed = analyzer.get_changed_files()
selected = analyzer.select_tests(changed)
if selected:
    print(f"Running {len(selected)} impacted tests (out of full suite)")
    # pytest {' '.join(selected)}
else:
    print("No coverage map match; running full suite")
```

**JavaScript:**
```javascript
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

class TestImpactAnalyzer {
  constructor(coverageMapFile = ".coverage_map.json") {
    this.coverageMapFile = coverageMapFile;
    this.coverageMap = {};
  }

  loadCoverageMap() {
    try {
      this.coverageMap = JSON.parse(
        fs.readFileSync(this.coverageMapFile, "utf-8")
      );
    } catch {
      this.coverageMap = {};
    }
    return this;
  }

  getChangedFiles(baseRef = "main") {
    const output = execSync(`git diff --name-only ${baseRef} HEAD`, {
      encoding: "utf-8",
    });
    return output
      .trim()
      .split("\n")
      .filter((f) => f.length > 0);
  }

  selectTests(changedFiles = null) {
    if (!changedFiles) {
      changedFiles = this.getChangedFiles();
    }

    const selectedTests = new Set();
    for (const changedFile of changedFiles) {
      const tests = this.coverageMap[changedFile];
      if (tests) {
        tests.forEach((t) => selectedTests.add(t));
      }
    }

    if (selectedTests.size === 0) {
      return null; // Run everything
    }

    return [...selectedTests].sort();
  }
}

// Usage:
const analyzer = new TestImpactAnalyzer().loadCoverageMap();
const selected = analyzer.selectTests();
if (selected) {
  console.log(`Running ${selected.length} impacted tests`);
  // Execute: jest ${selected.join(' ')}
} else {
  console.log("Running full test suite");
}
```
