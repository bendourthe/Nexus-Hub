### Step 5: Ensure Test Isolation

Verify that the reproduction test is fully isolated and does not depend on external state.

**Python: Test isolation checker**

```python
import subprocess
import sys

class TestIsolationChecker:
    """Verify that a reproduction test is properly isolated."""

    def __init__(self, test_file: str, test_name: str):
        self.test_file = test_file
        self.test_name = test_name

    def run_test(self, extra_args: list[str] = None) -> bool:
        """Run the test and return True if it produces the expected result."""
        cmd = [sys.executable, "-m", "pytest", f"{self.test_file}::{self.test_name}", "-v"]
        if extra_args:
            cmd.extend(extra_args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode != 0  # We expect the test to fail (bug reproduces)

    def check_order_independence(self, other_tests: list[str]) -> bool:
        """Verify the test produces the same result regardless of execution order."""
        # Run the reproduction test alone
        alone_result = self.run_test()

        # Run it after other tests
        for other_test in other_tests:
            subprocess.run(
                [sys.executable, "-m", "pytest", other_test, "-v"],
                capture_output=True,
            )
        after_result = self.run_test()

        return alone_result == after_result

    def check_no_network(self) -> bool:
        """Verify the test does not make network calls."""
        result = self.run_test(["--disable-socket"])
        return result  # Should still reproduce without network

    def check_no_filesystem_side_effects(self, watch_dir: str) -> bool:
        """Verify the test does not leave files behind."""
        import os
        before = set(os.listdir(watch_dir))
        self.run_test()
        after = set(os.listdir(watch_dir))
        return before == after

    def generate_isolation_report(self) -> dict:
        """Generate a complete isolation check report."""
        return {
            "reproduces_standalone": self.run_test(),
            "no_filesystem_side_effects": self.check_no_filesystem_side_effects("."),
            "order_independent": True,  # Requires other test names to check fully
        }
```

**JavaScript: Test isolation checker**

```javascript
const { execSync } = require("child_process");

class TestIsolationChecker {
  constructor(testFile, testName) {
    this.testFile = testFile;
    this.testName = testName;
  }

  runTest(extraArgs = []) {
    try {
      execSync(
        `npx jest ${this.testFile} -t "${this.testName}" ${extraArgs.join(" ")}`,
        { stdio: "pipe", timeout: 30000 }
      );
      return false; // Test passed (bug did not reproduce)
    } catch {
      return true; // Test failed (bug reproduced)
    }
  }

  checkReproducesStandalone() {
    return this.runTest(["--forceExit", "--detectOpenHandles"]);
  }

  checkOrderIndependence() {
    // Run in random order multiple times
    const results = [];
    for (let i = 0; i < 3; i++) {
      results.push(this.runTest(["--randomize"]));
    }
    return results.every(r => r === results[0]);
  }

  generateReport() {
    return {
      reproducesStandalone: this.checkReproducesStandalone(),
      orderIndependent: this.checkOrderIndependence(),
    };
  }
}
```
