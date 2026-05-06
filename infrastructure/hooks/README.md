# Automation Hooks for Claude Code

Hooks enable automated workflows that trigger skills and actions at specific points in your development process.

## What are Hooks?

Hooks are automated triggers that execute specific actions when certain events occur. They integrate skills with your development workflow for consistent quality and automation.

## Hook Types

### 1. Git Hooks
Triggered by Git operations

### 2. File Hooks
Triggered by file system changes

### 3. Development Hooks
Triggered by development events

---

## Available Hooks

### Git Hooks

#### pre-commit

**Purpose:** Run checks before allowing a commit

**Location:** `.git/hooks/pre-commit`

**Template:**
```bash
#!/bin/bash
# Pre-commit hook for Claude Code quality checks

echo "Running pre-commit checks..."

# Run pre-commit checklist skill
claude-code --skill pre-commit-checklist

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ Pre-commit checks failed. Commit aborted."
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
```

**Skills to use:**

- `pre-commit-checklist`

- `code-complexity-analysis`

- `licensing-compliance-check`

---

#### pre-push

**Purpose:** Run comprehensive checks before pushing

**Location:** `.git/hooks/pre-push`

**Template:**
```bash
#!/bin/bash
# Pre-push hook for comprehensive testing

echo "Running pre-push validation..."

# Run all code review phases
claude-code --skill code-review-quality
claude-code --skill code-review-security
claude-code --skill code-review-testing

# Run tests
python -m pytest tests/ || exit 1

echo "✅ Pre-push validation passed"
exit 0
```

**Skills to use:**

- `code-review-*` (all review skills)

- `dependency-security-audit`

- `generate-test-cases`

---

#### post-commit

**Purpose:** Actions after successful commit

**Location:** `.git/hooks/post-commit`

**Template:**
```bash
#!/bin/bash
# Post-commit hook for documentation updates

# Update documentation if code changed
if git diff-tree --no-commit-id --name-only -r HEAD | grep -q "src/"; then
    claude-code --skill generate-docstrings
    claude-code --skill add-strategic-comments
fi

exit 0
```

**Skills to use:**

- `generate-docstrings`

- `add-strategic-comments`

- `create-technical-docs`

---

### File Hooks

#### on-file-save

**Purpose:** Actions when files are saved

**Implementation:** Via IDE/editor configuration

**VSCode Example** (`.vscode/settings.json`):
```json
{
  "runOnSave.commands": [
    {
      "match": "\\.py$",
      "command": "claude-code --skill cleanup-python",
      "runIn": "terminal"
    },
    {
      "match": "\\.js$",
      "command": "claude-code --skill cleanup-javascript",
      "runIn": "terminal"
    }
  ]
}
```

**Skills to use:**

- `cleanup-*` (language-specific)

- `generate-docstrings`

---

### Development Hooks

#### on-test-run

**Purpose:** Actions after test execution

**Template** (`tests/hooks/post_test.py`):
```python
"""Post-test hook for coverage and documentation."""
import subprocess
import sys


def main():
    """Execute post-test actions."""
    # Measure coverage
    result = subprocess.run(['claude-code', '--skill', 'measure-code-coverage'])

    # Update test documentation if coverage < 80%
    if result.returncode != 0:
        subprocess.run(['claude-code', '--skill', 'generate-test-cases'])

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

**Skills to use:**

- `measure-code-coverage`

- `generate-test-cases`

- `setup-test-infrastructure`

---

#### on-build-success

**Purpose:** Actions after successful build

**Template** (in CI/CD):
```yaml
# .github/workflows/build.yml
name: Build
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v2

      - name: Build
        run: npm run build

      - name: Generate documentation
        if: success()
        run: |
          claude-code --skill generate-api-docs
          claude-code --skill create-user-documentation
          claude-code --skill generate-sbom
```

**Skills to use:**

- `generate-api-docs`

- `create-user-documentation`

- `generate-sbom`

---

## Hook Installation

### Manual Installation

1. **Create hook file:**
   ```bash
   touch .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

2. **Add hook content** (use templates above)

3. **Test hook:**
   ```bash
   ./.git/hooks/pre-commit
   ```

---

### Automated Installation

Use the installation script:

```bash
# Install all hooks
python tools/install_hooks.py --all

# Install specific hook
python tools/install_hooks.py --hook pre-commit

# Install by category
python tools/install_hooks.py --category git
```

---

## Hook Configurations

### Configuration File

Create `.claude/hooks.json`:

```json
{
  "hooks": {
    "pre-commit": {
      "enabled": true,
      "skills": [
        "pre-commit-checklist",
        "code-complexity-analysis"
      ],
      "timeout": 300,
      "fail_on_error": true
    },
    "pre-push": {
      "enabled": true,
      "skills": [
        "code-review-security",
        "dependency-security-audit"
      ],
      "timeout": 600,
      "fail_on_error": true
    },
    "post-commit": {
      "enabled": false,
      "skills": [
        "generate-docstrings"
      ],
      "timeout": 120,
      "fail_on_error": false
    }
  }
}
```

---

## Hook Workflows

### Workflow 1: Quality Gate

**Pre-commit:**

1. Run `pre-commit-checklist`

2. Check code complexity

3. Verify licensing compliance

**Pre-push:**

1. Full code review (all phases)

2. Security audit

3. Test suite execution

---

### Workflow 2: Documentation Automation

**Post-commit:**

1. Generate/update docstrings

2. Add strategic comments

3. Update technical docs

**Post-push:**

1. Generate API documentation

2. Update user guides

3. Create SBOM

---

### Workflow 3: Continuous Quality

**On file save:**

1. Code cleanup (language-specific)

2. Format code

3. Update inline docs

**On test run:**

1. Measure coverage

2. Generate missing tests

3. Update test docs

---

## Best Practices

### Do's

✅ **Start light** - Begin with simple hooks, add complexity gradually
✅ **Fast feedback** - Keep pre-commit hooks under 30 seconds
✅ **Selective triggers** - Only run necessary checks per hook
✅ **Clear messages** - Provide helpful output when hooks fail
✅ **Escape hatches** - Allow bypassing with `--no-verify` for emergencies

### Don'ts

❌ **Don't block unnecessarily** - Avoid failing commits for warnings
❌ **Don't run everything** - Pre-commit shouldn't run full test suite
❌ **Don't ignore failures** - Investigate and fix hook failures
❌ **Don't duplicate** - If CI handles it, hook doesn't need to
❌ **Don't hardcode paths** - Use relative paths and env variables

---

## Troubleshooting

### Hook Not Executing

**Problem:** Git hook doesn't run

**Solutions:**

1. Check file is executable: `chmod +x .git/hooks/pre-commit`

2. Verify shebang line: `#!/bin/bash` or `#!/usr/bin/env python`

3. Test directly: `./.git/hooks/pre-commit`

---

### Hook Takes Too Long

**Problem:** Pre-commit hook times out or is too slow

**Solutions:**

1. Run only fast checks pre-commit

2. Move slow checks to pre-push or CI

3. Use caching for expensive operations

4. Run checks on changed files only

---

### Hook Fails Unexpectedly

**Problem:** Hook fails but unsure why

**Solutions:**

1. Add debug output: `set -x` in bash scripts

2. Check error messages carefully

3. Test skill independently

4. Verify all dependencies installed

---

## Hook Templates by Use Case

### For Solo Developer

**Pre-commit:** Quick syntax/lint checks
**Pre-push:** Basic test run
**Post-commit:** None (manual docs)

```bash
# Minimal pre-commit
#!/bin/bash
python -m flake8 src/
exit $?
```

---

### For Team Development

**Pre-commit:** Style, complexity, license checks
**Pre-push:** Full review, security, tests
**Post-commit:** Auto-documentation

```bash
# Team pre-commit
#!/bin/bash
claude-code --skill pre-commit-checklist
claude-code --skill code-complexity-analysis
claude-code --skill licensing-compliance-check
```

---

### For Enterprise

**Pre-commit:** Comprehensive quality gates
**Pre-push:** Security + compliance audits
**Post-commit:** Full documentation pipeline

```bash
# Enterprise pre-push
#!/bin/bash
claude-code --skill code-review-security
claude-code --skill dependency-security-audit
claude-code --skill licensing-compliance-check
python -m pytest tests/ --cov --cov-report=html
```

---

## Integration with CI/CD

Hooks complement CI/CD, not replace it:

| Check | Hook | CI/CD |
|-------|------|-------|
| Syntax errors | ✅ Pre-commit | ✅ Build |
| Code style | ✅ Pre-commit | ✅ Lint job |
| Unit tests | ❌ (too slow) | ✅ Test job |
| Integration tests | ❌ | ✅ Test job |
| Security scan | ⚠️ Pre-push | ✅ Security job |
| Documentation | ✅ Post-commit | ✅ Deploy docs |

---

## Advanced Hook Patterns

### Conditional Execution

```bash
#!/bin/bash
# Only run on Python files
if git diff --cached --name-only | grep -q "\.py$"; then
    claude-code --skill cleanup-python
fi
```

### Parallel Execution

```bash
#!/bin/bash
# Run multiple skills in parallel
claude-code --skill code-review-quality &
PID1=$!
claude-code --skill code-review-security &
PID2=$!

wait $PID1 $PID2
```

### Smart Caching

```bash
#!/bin/bash
# Cache results for unchanged files
HASH=$(git diff --cached | md5sum)
if [ -f ".cache/$HASH" ]; then
    echo "Using cached results"
    exit 0
fi

claude-code --skill pre-commit-checklist
echo $HASH > ".cache/$HASH"
```

---

## Git Guardrails (PreToolUse Hook)

### Overview

The git guardrails hook prevents AI agents from executing destructive git commands. It uses Claude Code's `PreToolUse` event to intercept Bash commands before execution and block dangerous patterns.

**Installed by**: The DevAI-Hub installer (both global and workspace).

**Location**: `.claude/hooks/git-guardrails.sh`

**Configuration**: `.claude/settings.json` (hooks section)

### How It Works

1. Before each Bash tool call, Claude Code pipes JSON to `git-guardrails.sh` via stdin
2. The script extracts the command from `tool_input.command`
3. The command is checked against a list of dangerous regex patterns
4. If matched: the script writes a `BLOCKED` message to stderr and exits with code 2
5. If not matched: the script exits with code 0 (allow)

Claude Code sees the `BLOCKED` message and adapts its approach automatically.

### Blocked Commands (Defaults)

| Command | Risk |
|---------|------|
| `git push --force` / `-f` | Overwrites remote history |
| `git push --force-with-lease` | Overwrites remote history |
| `git reset --hard` | Discards all uncommitted work |
| `git clean -f` / `-fd` | Permanently deletes untracked files |
| `git branch -D` | Force-deletes branch without merge check |
| `git checkout .` / `git checkout -- .` | Discards all working tree changes |
| `git restore .` | Discards all working tree changes |
| `git stash drop` / `git stash clear` | Permanently loses stashed work |
| `rm -rf .git` | Destroys the entire repository |

### Customizing Blocked Patterns

Edit `.claude/hooks/git-guardrails.sh` and modify the `DANGEROUS_PATTERNS` array:

```bash
DANGEROUS_PATTERNS=(
  'git\s+push\s+.*--force:::Force push overwrites remote history'
  # Add or remove patterns here
  # Format: 'extended_regex:::description'
)
```

For example, to allow `git push --force-with-lease` (some teams consider this safe enough):

```bash
# Remove this line from DANGEROUS_PATTERNS:
# 'git\s+push\s+.*--force-with-lease:::Force-with-lease push overwrites remote history'
```

### Verifying It Works

Ask Claude Code to run a blocked command:

```
> Run git push --force origin main
```

You should see:

```
BLOCKED: 'git push --force origin main' matches dangerous git pattern.
Force push overwrites remote history. The user has prevented you from doing this.
```

### Settings Configuration

The hook is configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/git-guardrails.sh"
          }
        ]
      }
    ]
  }
}
```

### Temporarily Disabling

To temporarily disable the guardrails (e.g., for a legitimate force-push), remove the hook entry from `.claude/settings.json` and restore it after. Do not delete the hook script itself.

---

## Usage Display (Stop Hook)

### Overview

The usage display hook shows your Claude Code usage limits (session, weekly, and Sonnet-only percentages) directly in the CLI after each conversation turn. It uses Claude Code's `Stop` event to display a compact, color-coded summary when any metric exceeds 50%.

This complements two other usage monitoring features:

- **VS Code Extension** (`extensions/claude-usage-monitor/`): Dashboard and status bar for VS Code users.
- **`/check-usage` Command** (`catalog/commands/check-usage.md`): On-demand detailed report with model-switching recommendations.

**Installed by**: The DevAI-Hub installer (both global and workspace).

**Location**: `.claude/hooks/usage-display.sh`

**Requirements**: `curl` and `jq` (fails silently without them).

### How It Works

1. When Claude Code finishes a response (Stop event), it triggers `usage-display.sh`
2. The script checks for a cached API response (`~/.claude/.usage-cache.json`)
3. If the cache is stale (older than 5 minutes), it reads credentials from `~/.claude/.credentials.json` and calls the Anthropic usage API
4. Usage percentages are parsed: session (`five_hour`), weekly all-models (`seven_day`), weekly Sonnet-only (`seven_day_sonnet`)
5. If all metrics are below 50%, the hook exits silently
6. Otherwise, it outputs a compact one-line summary to stderr with color-coded percentages

### Example Output

When usage is above the threshold:

```
Usage: Session 72% | Weekly 15% | Sonnet 3%  (Session resets in 28m)
```

Colors: green (<50%), yellow (50-75%), orange (75-90%), red (90%+).

### Configuration

The hook is configured in `.claude/settings.json` alongside other hooks:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/usage-display.sh"
          }
        ]
      }
    ]
  }
}
```

### Customizing Behavior

Edit `.claude/hooks/usage-display.sh` to adjust:

- **`DISPLAY_THRESHOLD`** (default: `50`): Minimum percentage before the hook displays output. Set to `0` to always show.
- **`CACHE_TTL_SECONDS`** (default: `300`): How long to use cached data before fetching again.

### Graceful Degradation

The hook is designed to never interfere with your workflow:

- **No curl or jq**: Exits silently (code 0)
- **No credentials file**: Exits silently
- **Expired token**: Exits silently
- **Network error**: 3-second timeout, then exits silently
- **API error**: Exits silently
- **All metrics healthy**: Exits silently (below threshold)

### Temporarily Disabling

Remove the `Stop` hook entry from `.claude/settings.json`. The hook script can remain on disk.

---

*Hooks System - Part of DevAI-Hub v1.1.5*

*Last Updated: May 2026*
