### Step 5: Use Git Bisect for Regression Localization

When a test that previously passed now fails, git bisect efficiently finds the exact commit that introduced the regression.

**Bash: Automated git bisect**

```bash
#!/usr/bin/env bash
# Automated git bisect with a test command
# Usage: ./bisect.sh <good_commit> <bad_commit> <test_command>

GOOD_COMMIT="$1"
BAD_COMMIT="$2"
TEST_CMD="$3"

git bisect start "$BAD_COMMIT" "$GOOD_COMMIT"
git bisect run sh -c "$TEST_CMD"

echo "First bad commit:"
git bisect visualize --oneline | head -1

git bisect reset
```

**Python: Programmatic bisect driver**

```python
import subprocess

def git_bisect_automated(
    good_commit: str,
    bad_commit: str,
    test_command: str,
    repo_path: str = ".",
) -> str:
    """Run git bisect and return the first bad commit hash."""
    def run(cmd: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, shell=True, cwd=repo_path,
            capture_output=True, text=True,
        )

    run(f"git bisect start {bad_commit} {good_commit}")
    result = run(f"git bisect run sh -c '{test_command}'")

    # Extract the first bad commit from bisect output
    for line in result.stdout.splitlines():
        if "is the first bad commit" in line:
            commit_hash = line.split()[0]
            run("git bisect reset")
            return commit_hash

    run("git bisect reset")
    return "unknown"
```
