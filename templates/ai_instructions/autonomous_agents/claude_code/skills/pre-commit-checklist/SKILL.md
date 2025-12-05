---
name: pre-commit-checklist
description: Implement comprehensive automated pre-commit quality checks including linting, formatting, type checking, unit tests, security scans, and commit message validation - prevent defects before they enter version control
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Security
tags: [security, quality, git-hooks, pre-commit, automation, linting, testing, CI/CD]
priority: HIGH
based_on: Git Hooks Best Practices, Pre-commit Framework, Husky, Conventional Commits
---

# Pre-Commit Security and Quality Checklist

Implement comprehensive automated pre-commit quality checks that validate code before it enters version control. Prevent defects, security issues, and policy violations by catching problems at commit time through linting, formatting, type checking, unit tests, security scans, and commit message validation.

## When to Use This Skill

Use this skill whenever you need to:

- ✅ Establish quality gates before code enters version control
- ✅ Prevent committing secrets or sensitive data
- ✅ Enforce code style and formatting standards
- ✅ Run fast unit tests before each commit
- ✅ Validate commit message conventions
- ✅ Detect common security issues early
- ✅ Ensure type safety before commits
- ✅ Maintain consistent code quality across team
- ✅ Reduce CI/CD pipeline failures
- ✅ Implement shift-left security practices

**This skill is critical when**:
- Building team coding standards
- Onboarding new developers
- Preventing security credential leaks
- Enforcing commit message conventions
- Reducing code review overhead
- Implementing DevSecOps practices

## What This Skill Does

This skill implements automated pre-commit validation:

### Core Capabilities
- **Git Hook Setup**: Install and configure pre-commit hooks
- **Code Formatting**: Automatic formatting enforcement
- **Linting**: Style and quality validation
- **Type Checking**: Static type verification
- **Unit Testing**: Fast smoke tests before commit
- **Security Scanning**: Detect secrets and vulnerabilities
- **Commit Message Validation**: Enforce conventions
- **File Size Checks**: Prevent large file commits
- **Merge Conflict Detection**: Catch unresolved conflicts

### Language Support
- Python (Black, Flake8, mypy, pytest)
- JavaScript/TypeScript (ESLint, Prettier, tsc, Jest)
- Java (Checkstyle, SpotBugs, JUnit)
- C# (dotnet format, StyleCop, xUnit)
- Go (gofmt, golint, staticcheck, go test)
- C/C++ (clang-format, clang-tidy, cppcheck)

## Why Pre-Commit Checks Matter

**Without Pre-Commit Checks**:
```
Developer: *commits code directly*
Issues Present:

- ❌ Secrets committed to repository
- ❌ Unformatted code creates noise in diffs
- ❌ Linting errors break CI pipeline
- ❌ Type errors discovered in code review
- ❌ Basic unit tests fail in CI
- ❌ Invalid commit messages make history unclear
- ❌ Large files accidentally committed

Result:
- Wasted CI/CD resources
- Delayed feedback loop (minutes/hours)
- Context switching for developers
- Increased code review burden
- Security incidents from leaked credentials
- Poor code quality in version control
```

**With Pre-Commit Checks**:
```
Developer: *attempts to commit code*
Pre-commit hooks: *run automated checks*
Issues Found:

- ✅ Secret detected and commit blocked
- ✅ Code automatically formatted
- ✅ Linting errors shown immediately
- ✅ Type errors caught before commit
- ✅ Fast tests verify basic functionality
- ✅ Commit message validated
- ✅ Large files rejected

Result:
- Fast feedback (seconds)
- Issues fixed before entering version control
- Clean CI/CD pipeline runs
- Reduced code review time
- No security credential leaks
- Consistent code quality
- Clear commit history
```

## Benefits of Pre-Commit Checks

### Quality Assurance
- **Early Detection**: Catch issues in seconds, not minutes/hours
- **Consistent Standards**: Enforce team conventions automatically
- **Clean History**: Only quality code enters version control
- **Reduced Debt**: Prevent technical debt accumulation

### Security
- **Secret Detection**: Block hardcoded credentials
- **Vulnerability Prevention**: Catch common security issues
- **Compliance**: Enforce security policies automatically
- **Supply Chain**: Validate dependency integrity

### Developer Experience
- **Fast Feedback**: Immediate results, no CI wait
- **Reduced Context Switching**: Fix issues while in flow
- **Learning Tool**: Teaches best practices automatically
- **Less Review Burden**: Fewer trivial comments

### Team Efficiency
- **CI/CD Savings**: Fewer failed pipeline runs
- **Code Review Speed**: Reviewers focus on logic, not style
- **Onboarding**: New developers learn standards quickly
- **Documentation**: Pre-commit config documents standards

## Prerequisites

### Required
- Git repository initialized
- Package manager for target language(s)
- Bash or PowerShell (for hook scripts)
- Development environment with command-line access

### Recommended
- Pre-commit framework installed (cross-language)
- CI/CD pipeline for integration
- Team agreement on standards
- Documentation of conventions

### Knowledge
- Git hooks basics
- Linting and formatting tools
- Test frameworks
- Commit message conventions

## Instructions

### Step 1: Choose Pre-Commit Framework

**Select the appropriate framework for your project:**

#### Option A: Pre-commit Framework (Recommended for Multi-language)

**Universal framework supporting all languages**

```bash
# Install pre-commit (Python-based but supports all languages)
pip install pre-commit

# Verify installation
pre-commit --version

# Create .pre-commit-config.yaml in repository root
pre-commit sample-config > .pre-commit-config.yaml

# Install hooks
pre-commit install

# Test on all files (optional)
pre-commit run --all-files
```

**Advantages**:
- Multi-language support
- Large plugin ecosystem
- Automatic tool installation
- Easy configuration
- Active community

#### Option B: Husky (JavaScript/TypeScript Projects)

**Popular in Node.js ecosystem**

```bash
# Install husky
npm install --save-dev husky

# Initialize husky
npx husky-init && npm install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm test"

# Make executable
chmod +x .husky/pre-commit
```

**Advantages**:
- Lightweight for JavaScript projects
- npm/yarn integration
- Simple setup
- JavaScript-native

#### Option C: Manual Git Hooks

**Direct git hooks for custom needs**

```bash
# Navigate to git hooks directory
cd .git/hooks

# Create pre-commit hook
cat > pre-commit << 'EOF'
#!/bin/bash
# Pre-commit quality checks

echo "Running pre-commit checks..."

# Run linting
if ! npm run lint; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Run tests
if ! npm test; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "All checks passed!"
exit 0
EOF

# Make executable
chmod +x pre-commit
```

**Advantages**:
- Full control
- No dependencies
- Customizable
- Language-agnostic

### Step 2: Configure Language-Specific Checks

**Set up checks for each language in your project:**

#### Python - Comprehensive Configuration

**Using Pre-commit Framework**:

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

**Alternative: package.json scripts** (if using npm for Python projects):

```json
{
  "scripts": {
    "format": "black src/ tests/",
    "lint": "flake8 src/ tests/",
    "type-check": "mypy src/",
    "test:quick": "pytest tests/quick/ -x",
    "pre-commit": "npm run format && npm run lint && npm run type-check && npm run test:quick"
  }
}
```

#### JavaScript/TypeScript - Comprehensive Configuration

**Using Pre-commit Framework**:

```yaml
# .pre-commit-config.yaml
repos:
  # ESLint
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.52.0
    hooks:

      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        args: ['--fix']
        additional_dependencies:

          - eslint@8.52.0
          - eslint-plugin-security@1.7.1
          - '@typescript-eslint/eslint-plugin@6.10.0'

  # Prettier
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:

      - id: prettier
        args: ['--write']

  # TypeScript Type Checking
  - repo: local
    hooks:

      - id: tsc
        name: TypeScript Type Check
        entry: npx tsc --noEmit
        language: system
        types: [ts, tsx]
        pass_filenames: false

  # Jest Quick Tests
  - repo: local
    hooks:

      - id: jest-quick
        name: Jest Quick Tests
        entry: npm run test:quick
        language: system
        pass_filenames: false
        always_run: true

  # Secret Detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:

      - id: detect-secrets
```

**Using Husky + lint-staged**:

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

#### Java - Comprehensive Configuration

**Using Pre-commit Framework**:

```yaml
# .pre-commit-config.yaml
repos:
  # Checkstyle
  - repo: https://github.com/pre-commit/mirrors-checkstyle
    rev: v10.12.5
    hooks:

      - id: checkstyle
        args: ['-c', 'checkstyle.xml']

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

**Maven pom.xml Configuration**:

```xml
<build>
    <plugins>
        <!-- Google Java Format -->
        <plugin>
            <groupId>com.spotify.fmt</groupId>
            <artifactId>fmt-maven-plugin</artifactId>
            <version>2.21.1</version>
            <executions>
                <execution>
                    <goals>
                        <goal>check</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>

        <!-- Checkstyle -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-checkstyle-plugin</artifactId>
            <version>3.3.1</version>
            <configuration>
                <configLocation>checkstyle.xml</configLocation>
            </configuration>
        </plugin>

        <!-- SpotBugs -->
        <plugin>
            <groupId>com.github.spotbugs</groupId>
            <artifactId>spotbugs-maven-plugin</artifactId>
            <version>4.8.0.0</version>
            <configuration>
                <effort>Max</effort>
                <threshold>Low</threshold>
            </configuration>
        </plugin>
    </plugins>
</build>
```

#### C# - Comprehensive Configuration

**Using Pre-commit Framework**:

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

  # StyleCop Analyzer
  - repo: local
    hooks:

      - id: stylecop
        name: StyleCop Analysis
        entry: dotnet build /p:TreatWarningsAsErrors=true
        language: system
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

**.editorconfig** (C# formatting):

```ini
root = true

[*.cs]
indent_style = space
indent_size = 4
end_of_line = crlf
charset = utf-8-bom
trim_trailing_whitespace = true
insert_final_newline = true

# Code style
dotnet_sort_system_directives_first = true
csharp_new_line_before_open_brace = all
csharp_space_after_keywords_in_control_flow_statements = true
```

#### Go - Comprehensive Configuration

**Using Pre-commit Framework**:

```yaml
# .pre-commit-config.yaml
repos:
  # gofmt
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:

      - id: go-fmt

  # goimports
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:

      - id: go-imports

  # golint
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:

      - id: go-lint

  # go vet
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:

      - id: go-vet

  # staticcheck
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:

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

**Alternative: Manual Makefile-based**:

```makefile
# Makefile
.PHONY: pre-commit
pre-commit:
	@echo "Running pre-commit checks..."
	@gofmt -l -w .
	@goimports -l -w .
	@golint ./...
	@go vet ./...
	@staticcheck ./...
	@gosec ./...
	@go test -short ./...
	@echo "All checks passed!"
```

**Git Hook** (.git/hooks/pre-commit):

```bash
#!/bin/bash
make pre-commit
```

#### C/C++ - Comprehensive Configuration

**Using Pre-commit Framework**:

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

  # CMake format
  - repo: https://github.com/cheshirekow/cmake-format-precommit
    rev: v0.6.13
    hooks:

      - id: cmake-format

  # Quick unit tests (if using CTest)
  - repo: local
    hooks:

      - id: ctest-quick
        name: CTest Quick Tests
        entry: ctest -L quick
        language: system
        pass_filenames: false
```

**.clang-format** configuration:

```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
AllowShortFunctionsOnASingleLine: Empty
```

### Step 3: Implement Secret Detection

**Prevent accidental credential commits:**

#### Using detect-secrets (Recommended)

```bash
# Install
pip install detect-secrets

# Generate baseline (initial scan)
detect-secrets scan > .secrets.baseline

# Add to pre-commit config
```

```yaml
# .pre-commit-config.yaml
repos:

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:

      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json
```

**Workflow**:
1. Initial scan creates baseline of existing "secrets" (false positives)
2. Pre-commit hook compares new changes against baseline
3. New secrets are blocked
4. Update baseline when adding legitimate patterns

**Update baseline** when adding legitimate patterns:

```bash
# Audit and update baseline
detect-secrets audit .secrets.baseline

# Mark false positives
# Press 'y' for true positives, 'n' for false positives

# Regenerate baseline
detect-secrets scan --baseline .secrets.baseline
```

#### Using TruffleHog

```bash
# Install
pip install truffleHog

# Add to pre-commit as local hook
```

```yaml
# .pre-commit-config.yaml
repos:

  - repo: local
    hooks:

      - id: trufflehog
        name: TruffleHog Secret Scan
        entry: trufflehog filesystem . --json --fail
        language: system
        pass_filenames: false
```

#### Using git-secrets (AWS)

```bash
# Install git-secrets
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
make install

# Initialize in repository
cd /path/to/repo
git secrets --install

# Add AWS secret patterns
git secrets --register-aws

# Add custom patterns
git secrets --add 'api[_-]?key.*["\'][a-zA-Z0-9]{32,}["\']'
```

**Common Secret Patterns to Detect**:

```regex
# API Keys
api[_-]?key.*["\'][a-zA-Z0-9]{32,}["\']

# AWS Keys
AKIA[0-9A-Z]{16}

# Private Keys
-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----

# Passwords
password.*["\'][^"\']{8,}["\']

# Tokens
(access|auth|bearer)[_-]?token.*["\'][a-zA-Z0-9\-_]{20,}["\']

# Database URLs with credentials
(postgres|mysql|mongodb):\/\/[^:]+:[^@]+@

# Generic secrets
(secret|passwd|credential).*["\'][^"\']{12,}["\']
```

### Step 4: Configure Commit Message Validation

**Enforce commit message conventions:**

#### Conventional Commits Standard

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(auth): add OAuth2 authentication
fix(api): resolve null pointer exception in user endpoint
docs(readme): update installation instructions
test(user): add unit tests for user service
```

#### Using commitlint

```bash
# Install commitlint
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Create configuration
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Install commit-msg hook
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit $1'
```

**commitlint.config.js** (custom rules):

```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'test',
        'chore',
        'revert'
      ]
    ],
    'subject-case': [2, 'never', ['upper-case']],
    'subject-max-length': [2, 'always', 100],
    'body-max-line-length': [2, 'always', 200],
    'footer-max-line-length': [2, 'always', 200]
  }
};
```

#### Using Pre-commit Framework

```yaml
# .pre-commit-config.yaml
repos:

  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:

      - id: conventional-pre-commit
        stages: [commit-msg]
        args: []
```

**Install commit-msg hook**:

```bash
pre-commit install --hook-type commit-msg
```

#### Manual Bash Script

```bash
# .git/hooks/commit-msg
#!/bin/bash

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# Conventional commits pattern
pattern='^(feat|fix|docs|style|refactor|test|chore|revert)(\(.+\))?: .{1,100}'

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "ERROR: Commit message does not follow Conventional Commits format"
    echo ""
    echo "Format: <type>(<scope>): <subject>"
    echo ""
    echo "Examples:"
    echo "  feat(auth): add OAuth2 authentication"
    echo "  fix(api): resolve null pointer exception"
    echo "  docs(readme): update installation instructions"
    echo ""
    exit 1
fi

exit 0
```

### Step 5: Configure Fast Unit Tests

**Run quick smoke tests before committing:**

#### Python - Pytest Configuration

```ini
# pytest.ini
[pytest]
markers =
    quick: marks tests as quick (deselect with '-m "not quick"')
    slow: marks tests as slow

# Run only quick tests in pre-commit
addopts = -m quick --tb=short -x
```

**Mark tests**:

```python
import pytest

@pytest.mark.quick
def test_user_creation():
    """Quick test: user creation works."""
    user = User("test@example.com")
    assert user.email == "test@example.com"

@pytest.mark.slow
def test_database_migration():
    """Slow test: full database migration."""
    # This test takes 30 seconds, skip in pre-commit
    migrate_database()
    assert check_migration_complete()
```

**Pre-commit configuration**:

```yaml
# .pre-commit-config.yaml
repos:

  - repo: local
    hooks:

      - id: pytest-quick
        name: Quick Unit Tests
        entry: pytest -m quick --tb=short -x
        language: system
        pass_filenames: false
        always_run: true
```

#### JavaScript - Jest Configuration

```javascript
// jest.config.js
module.exports = {
  testMatch: [
    '**/tests/**/*.test.js',
    '**/__tests__/**/*.js'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/tests/slow/'  // Exclude slow tests
  ],
  // Quick tests timeout
  testTimeout: 5000  // 5 seconds max per test
};
```

**Package.json**:

```json
{
  "scripts": {
    "test": "jest",
    "test:quick": "jest --testPathPattern=quick --bail --maxWorkers=2",
    "test:slow": "jest tests/slow/",
    "test:watch": "jest --watch"
  }
}
```

**Pre-commit with lint-staged**:

```json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "jest --findRelatedTests --bail"
    ]
  }
}
```

#### Java - Maven Quick Tests

```xml
<!-- pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.2.1</version>
            <configuration>
                <!-- Run only quick tests in pre-commit -->
                <groups>quick</groups>
                <excludedGroups>slow,integration</excludedGroups>
            </configuration>
        </plugin>
    </plugins>
</build>
```

**Test annotation**:

```java
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Tag("quick")
@Test
public void testUserCreation() {
    User user = new User("test@example.com");
    assertEquals("test@example.com", user.getEmail());
}

@Tag("slow")
@Test
public void testDatabaseMigration() {
    // Takes 30 seconds, skip in pre-commit
    migrateDatabase();
    assertTrue(checkMigrationComplete());
}
```

#### Go - Quick Tests

```go
// user_test.go
package user

import "testing"

// Quick test (no special flag needed)
func TestUserCreation(t *testing.T) {
    user := NewUser("test@example.com")
    if user.Email != "test@example.com" {
        t.Errorf("Expected email test@example.com, got %s", user.Email)
    }
}

// Slow test (skip with -short flag)
func TestDatabaseMigration(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping slow test in short mode")
    }
    // Long-running test
    migrateDatabase()
    if !checkMigrationComplete() {
        t.Error("Migration incomplete")
    }
}
```

**Pre-commit hook**:

```bash
# Run quick tests only
go test -short ./...
```

### Step 6: Configure File Size and Type Checks

**Prevent accidentally committing large or inappropriate files:**

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

      # XML validation
      - id: check-xml

      # TOML validation
      - id: check-toml

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

**Custom file type checks**:

```yaml
# .pre-commit-config.yaml
repos:

  - repo: local
    hooks:
      # Prevent committing .env files
      - id: check-env-files
        name: Check for .env files
        entry: 'bash -c "! git diff --cached --name-only | grep -E \"\\.env$\"'
        language: system

      # Prevent committing node_modules
      - id: check-node-modules
        name: Check for node_modules
        entry: 'bash -c "! git diff --cached --name-only | grep \"node_modules\""'
        language: system

      # Check file permissions
      - id: check-executables-have-shebangs
        name: Check executables have shebangs
        entry: check-executables-have-shebangs
        language: python
```

### Step 7: Implement Comprehensive Pre-Commit Hook

**Complete example integrating all checks:**

#### Complete .pre-commit-config.yaml (Multi-language Project)

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
      - id: check-xml
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

  # ===== Local Hooks (Language-Specific Tests) =====
  - repo: local
    hooks:
      # Python quick tests
      - id: pytest-quick
        name: Python Quick Tests
        entry: pytest -m quick --tb=short -x
        language: system
        pass_filenames: false
        types: [python]

      # JavaScript quick tests
      - id: jest-quick
        name: JavaScript Quick Tests
        entry: npm run test:quick
        language: system
        pass_filenames: false
        types: [javascript, jsx, ts, tsx]

      # TypeScript type check
      - id: tsc
        name: TypeScript Type Check
        entry: npx tsc --noEmit
        language: system
        types: [ts, tsx]
        pass_filenames: false

      # Java quick tests
      - id: maven-test-quick
        name: Java Quick Tests
        entry: mvn test -Dtest=*QuickTest
        language: system
        types: [java]
        pass_filenames: false

      # Go quick tests
      - id: go-test-quick
        name: Go Quick Tests
        entry: go test -short ./...
        language: system
        types: [go]
        pass_filenames: false

      # C# quick tests
      - id: dotnet-test-quick
        name: C# Quick Tests
        entry: dotnet test --filter "Category=Quick"
        language: system
        types: [c#]
        pass_filenames: false
```

### Step 8: Team Adoption and CI/CD Integration

**Ensure team-wide adoption and pipeline integration:**

#### Team Onboarding

**README.md Addition**:

```markdown
## Development Setup

### Pre-commit Hooks

This project uses automated pre-commit hooks to ensure code quality and security.

**Installation** (one-time setup):

```bash
# Install pre-commit framework
pip install pre-commit

# Install hooks for this repository
pre-commit install
pre-commit install --hook-type commit-msg

# Test installation (optional)
pre-commit run --all-files
```

**What Gets Checked**:
- ✅ Code formatting (Black, Prettier, etc.)
- ✅ Linting (Flake8, ESLint, etc.)
- ✅ Type checking (mypy, TypeScript)
- ✅ Security scanning (bandit, secret detection)
- ✅ Quick unit tests
- ✅ Commit message format
- ✅ File size limits
- ✅ Merge conflict detection

**Bypassing Hooks** (use sparingly):

```bash
# Skip all pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "message"

# Better: Fix the issues instead
```

**Troubleshooting**:

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Clear cache if hooks fail unexpectedly
pre-commit clean

# Run specific hook manually
pre-commit run <hook-id> --all-files
```
```

#### CI/CD Pipeline Integration

**Enforce same checks in CI/CD to catch bypassed hooks:**

**GitHub Actions**:

```yaml
# .github/workflows/quality-checks.yml
name: Quality Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install pre-commit
        run: pip install pre-commit

      - name: Run pre-commit on all files
        run: pre-commit run --all-files
```

**GitLab CI**:

```yaml
# .gitlab-ci.yml
stages:

  - quality

pre-commit-checks:
  stage: quality
  image: python:3.11
  before_script:

    - pip install pre-commit
  script:

    - pre-commit run --all-files
  only:

    - merge_requests
    - main
```

**Jenkins**:

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Quality Checks') {
            steps {
                sh '''
                    pip install pre-commit
                    pre-commit run --all-files
                '''
            }
        }
    }
}
```

### Step 9: Monitor and Maintain Pre-Commit Configuration

**Keep hooks updated and effective:**

#### Regular Maintenance Tasks

**Monthly Tasks**:

```bash
# Update hook versions
pre-commit autoupdate

# Test updated hooks
pre-commit run --all-files

# Commit updated configuration
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

**Quarterly Tasks**:

1. **Review hook effectiveness**:
   - Are hooks catching real issues?
   - Are there too many false positives?
   - Should we add new checks?

2. **Audit bypass rate**:
   ```bash
   # Check for commits with --no-verify
   git log --all --grep="--no-verify" --oneline
   ```

3. **Team feedback**:
   - Survey team on hook usefulness
   - Identify pain points
   - Adjust configuration

4. **Performance tuning**:
   - Measure hook execution time
   - Optimize slow hooks
   - Consider parallel execution

#### Performance Optimization

**If hooks are slow**:

```yaml
# .pre-commit-config.yaml
# Run heavy checks in parallel
default_stages: [commit]

repos:
  # Fast hooks run always
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:

      - id: trailing-whitespace
      - id: end-of-file-fixer

  # Slow hooks run in parallel
  - repo: local
    hooks:

      - id: tests
        name: Unit Tests
        entry: make test-quick
        language: system
        pass_filenames: false
        # Run in parallel with other hooks
```

**Use `pass_filenames: false` judiciously**:
- Reduces overhead for tools that scan entire project
- But may run on unchanged files

**Conditional execution**:

```yaml
repos:

  - repo: local
    hooks:

      - id: expensive-check
        name: Expensive Check
        entry: expensive-check
        language: system
        # Only run if specific files changed
        files: ^src/critical/
```

## Multi-Language Support

This skill provides pre-commit automation for:

### Python
- **Formatting**: Black, autopep8
- **Linting**: Flake8, pylint, ruff
- **Type Checking**: mypy, pyright
- **Security**: bandit, safety
- **Testing**: pytest (quick tests)

### JavaScript/TypeScript
- **Formatting**: Prettier, standardjs
- **Linting**: ESLint with plugins
- **Type Checking**: TypeScript compiler
- **Security**: ESLint security plugin
- **Testing**: Jest (related tests)

### Java
- **Formatting**: Google Java Format, Prettier Java
- **Linting**: Checkstyle, PMD
- **Security**: SpotBugs, Find Security Bugs
- **Testing**: JUnit (quick tests)

### C#
- **Formatting**: dotnet format, StyleCop
- **Linting**: Roslyn analyzers
- **Security**: Security Code Scan
- **Testing**: xUnit (filtered tests)

### Go
- **Formatting**: gofmt, goimports
- **Linting**: golint, staticcheck
- **Security**: gosec
- **Testing**: go test -short

### C/C++
- **Formatting**: clang-format
- **Linting**: clang-tidy, cppcheck
- **Security**: flawfinder, cppcheck
- **Testing**: CTest (quick label)

## Common Pitfalls and Solutions

### Pitfall 1: Hooks Too Slow

**Problem**: Pre-commit takes >30 seconds, frustrating developers.

**Solution**:
- Run only quick tests (< 5 seconds total)
- Use `lint-staged` to check only changed files
- Offload comprehensive checks to CI/CD
- Parallelize independent checks

```yaml
# Good: Fast focused checks
repos:

  - repo: local
    hooks:

      - id: quick-test
        entry: pytest tests/unit/quick/ -x --tb=line
        # Only essential quick tests
```

### Pitfall 2: False Positives Block Commits

**Problem**: Legitimate code flagged incorrectly.

**Solution**:
- Tune linting rules to reduce noise
- Add exclusions for generated code
- Update secret detection baseline
- Provide clear bypass instructions for exceptional cases

```yaml
# Exclude generated files
- id: flake8
  exclude: ^(migrations/|generated/|.*_pb2\.py$)
```

### Pitfall 3: Developers Bypassing Hooks

**Problem**: Team uses `--no-verify` frequently.

**Solution**:
- Investigate why hooks are being bypassed
- Fix underlying issues (speed, false positives)
- Enforce checks in CI/CD (safety net)
- Educate team on importance
- Make bypass rate visible (metrics)

```bash
# Block bypass in CI/CD
# GitHub Actions will fail if code doesn't pass pre-commit
```

### Pitfall 4: Hooks Not Installed

**Problem**: New team members forget to install hooks.

**Solution**:
- Add setup to onboarding documentation
- Include in README prominently
- Add installation check to CI/CD
- Use `husky` which auto-installs for JavaScript projects

```yaml
# CI job to verify hooks are installed
- name: Check pre-commit installed
  run: |
    if ! git config --get core.hooksPath | grep -q ".husky"; then
      echo "Pre-commit hooks not installed!"
      exit 1
    fi
```

### Pitfall 5: Outdated Hook Configurations

**Problem**: Hook versions become outdated, miss new checks.

**Solution**:
- Schedule monthly `pre-commit autoupdate`
- Subscribe to security advisories for tools
- Review changelogs for new features
- Automate updates with Dependabot

```yaml
# .github/dependabot.yml
updates:

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Success Criteria

- [ ] Pre-commit framework installed and configured
- [ ] Code formatting automated for all languages
- [ ] Linting enforced with appropriate rules
- [ ] Type checking enabled (TypeScript, Python, etc.)
- [ ] Secret detection preventing credential leaks
- [ ] Quick unit tests running (<10 seconds)
- [ ] Commit message validation enforcing conventions
- [ ] File size and type checks preventing inappropriate commits
- [ ] Team trained on pre-commit workflow
- [ ] CI/CD pipeline enforces same checks
- [ ] Documentation updated with setup instructions
- [ ] Performance optimized (total time <30 seconds)
- [ ] False positive rate acceptable (<5%)
- [ ] Bypass rate monitored and low (<10%)
- [ ] Regular maintenance scheduled

## Related Skills

### Security Skills
- [Code Review Security](../code-review-security/SKILL.md) - Deep security audit
- [Dependency Security Audit](../dependency-security-audit/SKILL.md) - Dependency vulnerabilities

### Quality Skills
- [Code Review Quality](../code-review-quality/SKILL.md) - Code quality assessment
- [Test-Driven Development](../test-driven-development/SKILL.md) - TDD practices

### Workflow Skills
- [Code Commit Workflow](../code-commit-workflow/SKILL.md) - Git commit best practices

## Additional Resources

### Pre-commit Frameworks
- [Pre-commit Framework](https://pre-commit.com/) - Multi-language framework
- [Husky](https://typicode.github.io/husky/) - JavaScript/TypeScript
- [Lefthook](https://github.com/evilmartians/lefthook) - Fast Git hooks manager

### Commit Message Standards
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Commitlint](https://commitlint.js.org/)
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)

### Secret Detection
- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)
- [git-secrets](https://github.com/awslabs/git-secrets)
- [Gitleaks](https://github.com/gitleaks/gitleaks)

### Code Quality Tools
- [Black](https://black.readthedocs.io/) - Python formatter
- [ESLint](https://eslint.org/) - JavaScript linter
- [Prettier](https://prettier.io/) - Universal formatter
- [Checkstyle](https://checkstyle.org/) - Java style checker

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Git Hooks Best Practices, Pre-commit Framework, Husky, Conventional Commits
