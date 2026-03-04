---
name: code-commit-workflow
description: Implement proper Git commit workflow with conventional commits, atomic changes, and meaningful messages. Use when committing changes, preparing pull requests, or establishing team commit standards.
---

# Code Commit Workflow

Implement a professional Git commit workflow with conventional commits, atomic changes, and meaningful commit messages that enhance project history and collaboration.

## When to Use This Skill

Use this skill when you need to:

- Commit code changes to Git
- Prepare pull requests
- Establish team commit standards
- Review commit history quality
- Write meaningful commit messages
- Ensure atomic, logical commits

**Trigger phrases**: "commit workflow", "git commit", "commit message", "conventional commits", "commit standards", "prepare PR"

## What This Skill Does

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add OAuth2 login` |
| `fix` | Bug fix | `fix(api): handle null response` |
| `docs` | Documentation | `docs: update API reference` |
| `style` | Formatting | `style: fix indentation` |
| `refactor` | Code change (no feature/fix) | `refactor: extract validation logic` |
| `test` | Adding tests | `test: add user service tests` |
| `chore` | Maintenance | `chore: update dependencies` |
| `perf` | Performance | `perf: optimize database queries` |
| `ci` | CI/CD changes | `ci: add GitHub Actions workflow` |

## Instructions

### Step 1: Review Staged Changes

Before committing, review what's being committed:

```bash
# See all changed files
git status

# See detailed changes
git diff --staged

# Check for untracked files
git status --short
```

### Step 2: Stage Logically Related Changes

Stage only related changes for atomic commits:

```bash
# Stage specific files
git add src/auth/login.ts
git add src/auth/logout.ts

# Or stage interactively
git add -p  # Review and stage hunks

# Stage all changes (use carefully)
git add .
```

### Step 3: Write Commit Message

#### Subject Line (Required)
- Start with lowercase type
- Include scope in parentheses if applicable
- Use imperative mood ("add" not "added")
- No period at end
- Max 50 characters

```
feat(auth): add password reset functionality
fix(api): handle empty response from server
docs: update installation instructions
```

#### Body (Optional but Recommended)
- Explain **what** and **why**, not how
- Separate from subject with blank line
- Each bullet point must be a single line with no line breaks or continuation lines, regardless of length. Never hard-wrap bullet text.

```
feat(auth): add password reset functionality

- Users can now request a password reset via email with a link that expires after 24 hours
- Implements the security requirement from ticket AUTH-234
```

#### Footer (Optional)
- Reference issues
- Note breaking changes
- Add trailer metadata (e.g., `Fixes #123`)

```
feat(api)!: change response format to JSON:API

BREAKING CHANGE: API responses now follow JSON:API specification.
Clients must update their response parsing logic.

Fixes #123
```

> **Rule**: Do NOT add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages.

### Step 4: Commit with Full Message

```bash
# Using editor (recommended for detailed messages)
git commit

# Using -m for simple messages
git commit -m "feat(auth): add login validation"

# Multi-line with -m
git commit -m "feat(auth): add login validation" \
           -m "Add client-side validation for email format and password strength." \
           -m "Fixes #456"
```

### Step 5: Verify Commit

```bash
# Check commit was created
git log -1 --oneline

# View full commit details
git log -1

# Verify no files left unstaged
git status
```

## Commit Message Examples

### Good Examples

```
feat(user): add profile photo upload

Allow users to upload profile photos. Supports JPEG, PNG, and GIF
formats up to 5MB. Photos are automatically resized to 200x200px.

Implements user story US-789
```

```
fix(cart): prevent duplicate items when adding quickly

Race condition caused duplicate items when users clicked "Add to Cart"
rapidly. Added debounce and server-side idempotency check.

Fixes #234
```

```
refactor(payment): extract card validation to separate module

Move credit card validation logic from PaymentService to CardValidator
class. This improves testability and allows reuse in other contexts.

No functional changes.
```

```
test(auth): add integration tests for OAuth flow

Add comprehensive tests covering:
- Successful OAuth login
- Token refresh
- Permission denied scenarios
- Rate limiting behavior

Coverage increased from 72% to 89%
```

### Bad Examples

```
# Too vague
fix bug

# Not imperative
fixed the login issue

# Too long subject
add new feature to allow users to upload their profile photos in multiple formats

# Missing type
update user model

# Doesn't explain why
refactor code
```

## Pre-Commit Checklist

Before every commit, verify:

```markdown
### Code Quality
- [ ] Code compiles/builds without errors
- [ ] No new linting warnings
- [ ] Type checking passes (if applicable)

### Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] No test regressions

### Security
- [ ] No secrets or credentials in code
- [ ] No sensitive data in comments
- [ ] Dependencies are from trusted sources

### Documentation
- [ ] Code is self-documenting or has comments
- [ ] Public API documented
- [ ] README updated if needed

### Commit Hygiene
- [ ] Changes are atomic (one logical change)
- [ ] Commit message follows convention
- [ ] No unrelated changes included
```

## Git Hooks for Enforcement

### Pre-Commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linting
npm run lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Please fix errors before committing."
    exit 1
fi

# Run tests
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix tests before committing."
    exit 1
fi

exit 0
```

### Commit Message Hook

```bash
#!/bin/sh
# .git/hooks/commit-msg

# Conventional commit regex
PATTERN="^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,50}"

if ! grep -qE "$PATTERN" "$1"; then
    echo "Invalid commit message format!"
    echo "Expected: <type>(<scope>): <subject>"
    echo "Types: feat, fix, docs, style, refactor, test, chore, perf, ci"
    exit 1
fi

exit 0
```

## Branch and PR Workflow

### Branch Naming

```
feature/AUTH-123-add-oauth-login
bugfix/BUG-456-fix-null-pointer
hotfix/SEC-789-patch-vulnerability
chore/update-dependencies
```

### Prepare for PR

```bash
# Update from main
git fetch origin
git rebase origin/main

# Squash if needed (interactive rebase)
git rebase -i origin/main

# Push (force if rebased)
git push -u origin feature/my-feature
# or
git push --force-with-lease
```

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Changes
- Added X
- Fixed Y
- Refactored Z

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)
[Add screenshots here]

## Related Issues
Closes #123
```

## Atomic Commits

### What is Atomic?

An atomic commit:
- Contains one logical change
- Can be reverted without affecting other changes
- Builds and tests pass
- Has a clear, focused message

### Splitting Large Changes

```bash
# If you have many unrelated changes staged:

# Reset staging
git reset HEAD

# Stage and commit separately
git add src/auth/*.ts
git commit -m "feat(auth): add login validation"

git add src/api/*.ts
git commit -m "refactor(api): extract error handling"

git add tests/*.ts
git commit -m "test: add auth integration tests"
```

## Quality Checklist

- [ ] Commit message follows conventional format
- [ ] Subject line is under 50 characters
- [ ] Body explains what and why
- [ ] Changes are atomic (one logical change)
- [ ] All tests pass
- [ ] No secrets in commit
- [ ] Related files are grouped together
- [ ] Breaking changes are clearly marked
- [ ] No `Co-Authored-By` or AI attribution lines in commit message

## Related Skills

- `pre-commit-checklist` - Pre-commit validation
- `security-review` - Security checks before commit
- `code-quality` - Code quality standards

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: Conventional Commits 1.0.0


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
