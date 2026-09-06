### Step 7: Complete Multi-Language Configuration

```yaml
# .pre-commit-config.yaml
# Comprehensive pre-commit configuration for multi-language project

default_language_version:
  python: python3.11
  node: 18.18.0

repos:
  # ===== General Checks =====
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']

  # ===== Secret Detection =====
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json

  # ===== Python =====
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        args: ['--ignore-missing-imports']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-ll']

  # ===== JavaScript/TypeScript =====
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.52.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        args: ['--fix']

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier

  # ===== Commit Message =====
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]

  # ===== Local Hooks (Tests) =====
  - repo: local
    hooks:
      # Python quick tests
      - id: pytest-quick
        name: Python Quick Tests
        entry: pytest -m quick --tb=short -x
        language: system
        pass_filenames: false
        types: [python]

      # TypeScript type check
      - id: tsc
        name: TypeScript Type Check
        entry: npx tsc --noEmit
        language: system
        types: [ts, tsx]
        pass_filenames: false
```
