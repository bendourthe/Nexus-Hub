### Step 6: Configure File Size and Type Checks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # File size check (max 1MB)
      - id: check-added-large-files
        args: ['--maxkb=1000']

      # Prevent committing to main/master
      - id: no-commit-to-branch
        args: ['--branch', 'main', '--branch', 'master']

      # Check for merge conflicts
      - id: check-merge-conflict

      # Check file encoding
      - id: check-case-conflict
      - id: mixed-line-ending
        args: ['--fix=lf']

      # Prevent committing private keys
      - id: detect-private-key

      # YAML validation
      - id: check-yaml
        args: ['--safe']

      # JSON validation
      - id: check-json

      # Trailing whitespace
      - id: trailing-whitespace
        args: ['--markdown-linebreak-ext=md']

      # End of file fixer
      - id: end-of-file-fixer

      # Check Python syntax
      - id: check-ast

      # Check for debugger statements
      - id: debug-statements
```
