### Step 2: Configure Language-Specific Checks

#### Python - Comprehensive Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Code Formatting
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=88']

  # Import Sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']

  # Linting
  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']
        additional_dependencies: [flake8-docstrings]

  # Type Checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        args: ['--ignore-missing-imports', '--strict']
        additional_dependencies: [types-all]

  # Security Scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'src/', '-ll']

  # Secret Detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # General Checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: check-json
      - id: pretty-format-json
        args: ['--autofix']

  # Testing (fast smoke tests only)
  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest tests/quick/ -x --tb=short
        language: system
        pass_filenames: false
        always_run: true
```

#### JavaScript/TypeScript - Using Husky + lint-staged

```json
// package.json
{
  "scripts": {
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit",
    "test:quick": "jest --testPathPattern=quick --bail",
    "prepare": "husky install"
  },
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write",
      "jest --findRelatedTests --bail"
    ],
    "*.{json,md,yml}": [
      "prettier --write"
    ]
  },
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged && npm run type-check"
    }
  },
  "devDependencies": {
    "husky": "^8.0.3",
    "lint-staged": "^15.0.2",
    "eslint": "^8.52.0",
    "prettier": "^3.0.3",
    "typescript": "^5.2.2",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "eslint-plugin-security": "^1.7.1"
  }
}
```

**ESLint Configuration** (.eslintrc.json):

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:security/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "security"],
  "rules": {
    "no-console": "warn",
    "no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "security/detect-object-injection": "warn"
  }
}
```

#### Java - Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Google Java Format
  - repo: https://github.com/google/google-java-format
    rev: v1.18.1
    hooks:
      - id: google-java-format

  # SpotBugs (Security)
  - repo: local
    hooks:
      - id: spotbugs
        name: SpotBugs Security Check
        entry: mvn spotbugs:check
        language: system
        pass_filenames: false
        files: \.java$

  # Quick Unit Tests
  - repo: local
    hooks:
      - id: maven-test-quick
        name: Maven Quick Tests
        entry: mvn test -Dtest=*QuickTest
        language: system
        pass_filenames: false
```

#### Go - Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # gofmt
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-imports
      - id: go-lint
      - id: go-vet
      - id: go-staticcheck

  # Security - gosec
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-sec

  # Quick tests
  - repo: local
    hooks:
      - id: go-test-quick
        name: Go Quick Tests
        entry: go test -short ./...
        language: system
        pass_filenames: false
```

#### C# - Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # dotnet format
  - repo: local
    hooks:
      - id: dotnet-format
        name: dotnet format
        entry: dotnet format --verify-no-changes
        language: system
        files: \.(cs|vb)$
        pass_filenames: false

  # Security Analysis
  - repo: local
    hooks:
      - id: security-scan
        name: .NET Security Scan
        entry: dotnet list package --vulnerable
        language: system
        pass_filenames: false

  # Quick Unit Tests
  - repo: local
    hooks:
      - id: dotnet-test-quick
        name: Quick Unit Tests
        entry: dotnet test --filter "Category=Quick"
        language: system
        pass_filenames: false
```

#### C/C++ - Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # clang-format
  - repo: https://github.com/pre-commit/mirrors-clang-format
    rev: v17.0.4
    hooks:
      - id: clang-format
        args: ['-i']

  # cppcheck
  - repo: local
    hooks:
      - id: cppcheck
        name: cppcheck
        entry: cppcheck
        args: ['--enable=all', '--error-exitcode=1', '--inline-suppr']
        language: system
        files: \.(c|cpp|cc|cxx|h|hpp)$

  # clang-tidy
  - repo: local
    hooks:
      - id: clang-tidy
        name: clang-tidy
        entry: clang-tidy
        args: ['--fix', '--format-style=file']
        language: system
        files: \.(c|cpp|cc|cxx)$
```
