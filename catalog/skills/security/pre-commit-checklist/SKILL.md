---
name: pre-commit-checklist
description: Implement automated pre-commit quality checks including linting, formatting, type checking, tests, security scans, and commit message validation. Use when establishing team coding standards, preventing credential leaks, enforcing conventions, or implementing shift-left security.
summary_l0: "Implement pre-commit hooks for linting, security scanning, and commit validation"
overview_l1: "This skill implements automated pre-commit quality checks including linting, formatting, type checking, tests, security scans, and commit message validation. Use it when establishing team coding standards, preventing credential leaks, enforcing conventions, or implementing shift-left security. Key capabilities include pre-commit hook configuration, linter and formatter integration, type checking gates, test execution on staged files, secret detection and prevention, commit message convention enforcement (conventional commits), and multi-language hook orchestration. The expected output is a configured pre-commit setup with hooks for code quality, security, and convention enforcement. Trigger phrases: pre-commit, commit hooks, pre-commit checklist, credential leak prevention, commit validation, coding standards, shift-left security, git hooks."
---

# Pre-Commit Security and Quality Checklist

Implement comprehensive automated pre-commit quality checks that validate code before it enters version control. Prevent defects, security issues, and policy violations by catching problems at commit time through linting, formatting, type checking, unit tests, security scans, and commit message validation.

## When to Use This Skill

Use this skill when you need to:

- Establish quality gates before code enters version control
- Prevent committing secrets or sensitive data
- Enforce code style and formatting standards
- Run fast unit tests before each commit
- Validate commit message conventions
- Detect common security issues early
- Ensure type safety before commits
- Maintain consistent code quality across team
- Reduce CI/CD pipeline failures
- Implement shift-left security practices

**Trigger phrases**: "pre-commit hooks", "git hooks", "commit validation", "prevent secrets", "enforce formatting", "lint on commit", "husky setup", "pre-commit framework"

## What This Skill Does

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

| Language | Formatting | Linting | Type Check | Security |
|----------|------------|---------|------------|----------|
| Python | Black, autopep8 | Flake8, pylint | mypy, pyright | bandit |
| JavaScript | Prettier | ESLint | TypeScript | eslint-security |
| Java | google-java-format | Checkstyle | - | SpotBugs |
| C# | dotnet format | StyleCop | - | Security Code Scan |
| Go | gofmt | golint | staticcheck | gosec |
| C/C++ | clang-format | clang-tidy | - | cppcheck |

## Prerequisites

- Git repository initialized
- Package manager for target language(s)
- Bash or PowerShell (for hook scripts)
- Development environment with command-line access

## Instructions

### Step 1: Choose Pre-Commit Framework

Full walkthrough: [step-1-choose-pre-commit-framework.md](references/step-1-choose-pre-commit-framework.md) (load this step when you reach it).

### Step 2: Configure Language-Specific Checks

Full walkthrough: [step-2-configure-language-specific-checks.md](references/step-2-configure-language-specific-checks.md) (load this step when you reach it).

### Step 3: Implement Secret Detection

Full walkthrough: [step-3-implement-secret-detection.md](references/step-3-implement-secret-detection.md) (load this step when you reach it).

Users who explicitly want a fast local secret-prevention hook may add gitleaks to that hook set. `security-review` owns full repository and history audit scope and the schema-v2 scanner receipts. Do not copy that recipe here, never auto-install gitleaks, do not add it as a Nexus-Hub repository dependency, and do not fall back to a hosted secret-scanning service.

### Step 4: Configure Commit Message Validation

Full walkthrough: [step-4-configure-commit-message-validation.md](references/step-4-configure-commit-message-validation.md) (load this step when you reach it).

### Step 5: Configure Fast Unit Tests

Full walkthrough: [step-5-configure-fast-unit-tests.md](references/step-5-configure-fast-unit-tests.md) (load this step when you reach it).

### Step 6: Configure File Size and Type Checks

Full walkthrough: [step-6-configure-file-size-and-type-checks.md](references/step-6-configure-file-size-and-type-checks.md) (load this step when you reach it).

### Step 7: Complete Multi-Language Configuration

Full walkthrough: [step-7-complete-multi-language-configuration.md](references/step-7-complete-multi-language-configuration.md) (load this step when you reach it).

### Step 8: Team Adoption and CI/CD Integration

Full walkthrough: [step-8-team-adoption-and-ci-cd-integration.md](references/step-8-team-adoption-and-ci-cd-integration.md) (load this step when you reach it).

## Common Pitfalls and Solutions

Detailed guidance lives in [common-pitfalls-and-solutions.md](references/common-pitfalls-and-solutions.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI already runs these checks, so pre-commit hooks are redundant" | A secret pushed to a branch is already in git history and the remote by the time CI fails; pre-commit is the only gate that stops the credential from ever leaving the developer's machine. |
| "I will just use --no-verify this once to unblock myself" | A high `--no-verify` rate is the signal that the hooks are too slow or too noisy; routinely bypassing them defeats the gate entirely, so the fix is to tune the hooks, not to skip them. |
| "Running the full test suite on every commit guarantees quality" | A 30-second-plus pre-commit hook trains developers to bypass it; only fast smoke tests (under 10 seconds) belong here, with the comprehensive suite offloaded to CI. |
| "The hooks are configured, so every developer is protected" | Hooks live in `.git/hooks` and are not cloned; a new team member who skips `pre-commit install` has zero protection, which is why CI must enforce the same checks as a safety net. |

## Verification

- [ ] `.pre-commit-config.yaml` exists in the repository root and `pre-commit install` has run (a hook exists at `.git/hooks/pre-commit`)
- [ ] A secret-detection hook is configured with a committed baseline (e.g. `.secrets.baseline`)
- [ ] The full hook set passes on a clean tree: `pre-commit run --all-files`
- [ ] A commit-msg hook enforces the convention: `pre-commit install --hook-type commit-msg` has run
- [ ] CI runs the same checks as a safety net (a `pre-commit run --all-files` step exists in the pipeline)
- [ ] Total pre-commit run time on a typical change is under 30 seconds

## Related Skills

- [[dependency-security-audit]] -- dependency vulnerability scanning that can run as a hook
- [[code-commit-workflow]] -- git commit conventions the commit-msg hook enforces
- [[security-review]] -- deeper security audit beyond the fast pre-commit gate. It owns full-repository and history secret-scan receipts. This skill may point at gitleaks as an optional local hook for users who explicitly want fast secret prevention; do not auto-install that hook, do not copy the full `security-review` gitleaks recipe, and do not add gitleaks as a Nexus-Hub dependency.
- [[code-quality]] -- code quality assessment the linting hooks support

## Additional Resources

Detailed guidance lives in [additional-resources.md](references/additional-resources.md) (load on demand).
