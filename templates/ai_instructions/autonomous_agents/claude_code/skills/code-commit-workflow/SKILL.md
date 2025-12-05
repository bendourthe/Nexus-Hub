---
name: code-commit-workflow
description: Guide through proper Git commit workflow with best practices for atomic commits and clear messages
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Workflow
tags: [workflow, git, commits, version-control, best-practice, collaboration]
priority: HIGH
---

# Code Commit Workflow

Guide developers through a proper Git commit workflow that produces clean, reviewable history with atomic commits and clear, meaningful commit messages.

## When to Use This Skill

Use this skill when:
- ✅ Preparing to commit changes to version control
- ✅ Working on features that span multiple files
- ✅ Making changes that should be split into logical commits
- ✅ Collaborating with a team (clean history matters)
- ✅ Preparing code for pull request review
- ✅ Following conventional commit standards
- ✅ Ensuring traceability of changes
- ✅ Building professional development habits

## What This Skill Does

This skill provides a systematic approach to committing code that results in:

### 1. Atomic Commits
- Each commit represents **one logical change**
- Commits can be understood, reviewed, and reverted independently
- No mixing of unrelated changes
- Clear separation of concerns

### 2. Clear Commit Messages
- Descriptive, meaningful commit messages
- Follows conventional commit format
- Explains **why** changes were made, not just **what**
- Provides context for future maintainers

### 3. Clean History
- Reviewable git history
- Easy to trace when and why changes occurred
- Simplified debugging with `git bisect`
- Professional development practices

### 4. Team Collaboration
- Consistent commit style across team
- Easy code review process
- Clear documentation of changes
- Traceability for project management

## Atomic Commit Principles

### What is an Atomic Commit?

An atomic commit is a **single, self-contained change** that:
- ✅ Has one clear purpose
- ✅ Can be understood without other commits
- ✅ Doesn't break the build
- ✅ Can be reverted safely if needed

### Examples of Atomic vs. Non-Atomic Commits

**❌ Non-Atomic (Bad)**:
```
Commit: "Various changes"
Files changed: 15 files

- Added user authentication
- Fixed bug in payment processing
- Refactored database queries
- Updated documentation
- Changed CSS styling
```
**Problems**:

- Impossible to review effectively
- Can't revert one change without others
- No clear purpose
- Vague commit message

**✅ Atomic (Good)**:
```
Commit 1: "feat: add JWT authentication for user login"
Files: src/auth/jwt.py, tests/test_auth.py

- Implements JWT token generation
- Adds token validation middleware

Commit 2: "fix: handle edge case in payment refund calculation"
Files: src/payments/refund.py, tests/test_refund.py

- Fixes division by zero for partial refunds

Commit 3: "refactor: optimize database queries with connection pooling"
Files: src/db/connection.py, config/database.yml

Commit 4: "docs: add API authentication documentation"
Files: docs/api/authentication.md

Commit 5: "style: update button styling to match design system"
Files: static/css/buttons.css
```
**Benefits**:

- Each commit has clear purpose
- Easy to review individually
- Can cherry-pick or revert specific changes
- Clear, searchable history

## Prerequisites

### Required
- Git installed and configured
- Understanding of basic Git commands
- Working directory with Git repository initialized

### Recommended
- Git GUI tool (GitKraken, SourceTree, VS Code Git, etc.)
- Pre-commit hooks configured
- Linting and formatting tools set up
- CI/CD pipeline for automated testing

### Knowledge
- Basic Git concepts (staging, commits, branches)
- Command line basics
- Conventional commit format (optional but recommended)

## Instructions

### Step 1: Review Your Changes

Before committing, understand what you've changed:

```bash
# See all modified files
git status

# See detailed changes
git diff

# See staged changes
git diff --cached
```

**Ask yourself**:
- What did I change?
- Can I group these changes into logical units?
- Should any changes be split into separate commits?

### Step 2: Stage Changes Selectively

Don't use `git add .` blindly. Stage changes for each atomic commit:

**Option A: Stage Entire Files** (when all changes in a file belong together):
```bash
# Stage specific files
git add src/auth/jwt.py tests/test_auth.py

# Check what's staged
git diff --cached
```

**Option B: Stage Partial Files** (when file has unrelated changes):
```bash
# Interactive staging
git add -p src/user_service.py

# Git will show hunks and ask for each:
# y - stage this hunk
# n - don't stage this hunk
# s - split into smaller hunks
# q - quit
```

**Option C: Stage Individual Lines** (using GUI):
- Use VS Code, GitKraken, or SourceTree
- Select specific lines to stage
- Create precise commits

**Example Interactive Session**:
```bash
$ git add -p src/user_service.py

diff --git a/src/user_service.py b/src/user_service.py
@@ -15,6 +15,10 @@ def create_user(data):
     user = User(**data)

+    # Add email validation
+    if not validate_email(user.email):
+        raise ValueError("Invalid email")
     user.save()

Stage this hunk [y,n,q,a,d,s,e,?]? y

@@ -45,3 +49,7 @@ def update_user(user_id, data):
     user.save()
+

+    # TODO: Add audit logging
+    log_user_update(user_id, data)

Stage this hunk [y,n,q,a,d,s,e,?]? n
```

### Step 3: Write a Clear Commit Message

Use the **Conventional Commits** format:

```
<type>(<scope>): <short description>

<body - optional but recommended>

<footer - optional>
```

#### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: add user profile page` |
| `fix` | Bug fix | `fix: correct tax calculation rounding` |
| `docs` | Documentation only | `docs: update API authentication guide` |
| `style` | Code style/formatting | `style: format code with Black` |
| `refactor` | Code refactoring | `refactor: extract email validation to utility` |
| `test` | Adding/updating tests | `test: add unit tests for payment gateway` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `perf` | Performance improvement | `perf: optimize database query with index` |
| `ci` | CI/CD changes | `ci: add automated deployment` |
| `build` | Build system changes | `build: configure webpack optimization` |
| `revert` | Revert previous commit | `revert: rollback authentication changes` |

#### Commit Message Template

**Basic Format**:
```
feat(auth): add JWT token refresh endpoint

Add endpoint to refresh JWT tokens without re-authentication.
Tokens expire after 15 minutes but can be refreshed for 7 days.

Closes #123
```

**Breakdown**:
- **Type**: `feat` (new feature)
- **Scope**: `auth` (authentication module)
- **Subject**: "add JWT token refresh endpoint" (what was done)
- **Body**: Explains why and provides context
- **Footer**: References issue/ticket

#### Good vs. Bad Commit Messages

**❌ Bad Commit Messages**:
```
git commit -m "fix"
git commit -m "WIP"
git commit -m "stuff"
git commit -m "updated files"
git commit -m "changes"
git commit -m "asdfasdf"
git commit -m "fixed the thing"
```

**✅ Good Commit Messages**:
```
git commit -m "fix: prevent division by zero in refund calculation

When processing partial refunds with zero quantity items,
the calculation would crash. Add validation to skip zero
quantity items before performing division.

Fixes #456"

git commit -m "feat(api): add pagination to user list endpoint

Implement cursor-based pagination for /api/users endpoint
to improve performance with large datasets. Default page
size is 50, maximum is 200.

Closes #789"

git commit -m "refactor: extract validation logic to shared utility

Move email and phone validation from UserService to new
ValidationUtil class. This allows reuse across multiple
services and improves testability.

No behavior change - existing tests pass."
```

### Step 4: Commit Your Changes

**Template Command**:
```bash
git commit -m "type(scope): short description

Longer explanation of the change and why it was necessary.
Explain the problem being solved, not just the solution.

Closes #issue-number"
```

**Example**:
```bash
git commit -m "feat(auth): implement JWT authentication

Add JSON Web Token (JWT) authentication to replace basic auth.
JWTs provide stateless authentication and improved security
through short-lived tokens with refresh capability.

- Generate JWT tokens on successful login
- Validate tokens on protected endpoints
- Implement token refresh endpoint
- Add unit tests for token generation and validation

Closes #234"
```

### Step 5: Verify Your Commit

Check that your commit looks correct:

```bash
# See the commit you just made
git log -1 -p

# See commit message and stats
git show HEAD

# See commit in one-line format
git log --oneline -5
```

**Verify**:
- [ ] Commit message is clear and descriptive
- [ ] Only intended changes are included
- [ ] No debug code, console.logs, or temporary changes
- [ ] No sensitive information (API keys, passwords)
- [ ] Tests still pass

### Step 6: Run Tests Before Pushing

**Always test before pushing**:

```bash
# Run your test suite
npm test           # JavaScript
pytest             # Python
mvn test           # Java
dotnet test        # C#
go test ./...      # Go
make test          # C/C++

# Run linting
npm run lint       # JavaScript
flake8 src/        # Python
mvn checkstyle:check  # Java
```

**If tests fail**:
```bash
# Amend the commit with fixes
git add <fixed-files>
git commit --amend --no-edit

# Or amend with new message
git commit --amend -m "Updated commit message"
```

### Step 7: Push to Remote

Push your commits to the remote repository:

```bash
# Push to current branch
git push

# Push new branch
git push -u origin feature/new-feature

# Force push (use with caution!)
git push --force-with-lease
```

**⚠️ Warning**: Never force push to `main`/`master` or shared branches!

### Step 8: Create Pull Request (If Applicable)

If working on a feature branch:

```bash
# Using GitHub CLI
gh pr create --title "feat: add user authentication" --body "Description of changes"

# Or use web interface
# Navigate to repository and click "New Pull Request"
```

**Pull Request Template**:
```markdown
## Description
Brief description of what this PR does.

## Changes
- List of changes made
- Organized by commit

## Testing
- How was this tested?
- Test coverage added/updated?

## Screenshots (if applicable)
Visual evidence of changes

## Checklist
- [ ] Tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented if present)

Closes #issue-number
```

## Commit Workflow Patterns

### Pattern 1: Feature Branch Workflow

**Process**:
```bash
# 1. Create feature branch
git checkout -b feature/user-authentication

# 2. Make changes and commit atomically
git add src/auth/jwt.py tests/test_auth.py
git commit -m "feat(auth): add JWT token generation"

git add src/middleware/auth_middleware.py
git commit -m "feat(auth): add authentication middleware"

git add src/routes/auth_routes.py
git commit -m "feat(auth): add login and logout endpoints"

# 3. Push feature branch
git push -u origin feature/user-authentication

# 4. Create pull request for review
gh pr create

# 5. Merge to main after approval
```

### Pattern 2: Commit Amending (for recent commits)

**Fix the last commit**:
```bash
# Made a typo in commit message
git commit --amend -m "New commit message"

# Forgot to add a file
git add forgotten_file.py
git commit --amend --no-edit

# Update commit with additional changes
git add updated_file.py
git commit --amend
```

**⚠️ Warning**: Only amend commits that haven't been pushed or shared!

### Pattern 3: Interactive Rebase (for cleaning history)

**Clean up multiple commits before pushing**:
```bash
# View last 5 commits
git log --oneline -5

# Interactive rebase
git rebase -i HEAD~5

# In the editor:
# pick abc1234 feat: add user model
# squash def5678 fix: typo in user model
# reword ghi9012 refactor: improve validation
# pick jkl3456 docs: add user model documentation

# Save and close editor
```

**Rebase commands**:
- `pick` - keep commit as-is
- `reword` - keep commit but edit message
- `edit` - pause to amend commit
- `squash` - combine with previous commit
- `fixup` - squash but discard commit message
- `drop` - remove commit

**⚠️ Warning**: Never rebase commits that have been pushed to shared branches!

### Pattern 4: Stashing Work in Progress

**Save work without committing**:
```bash
# Stash current changes
git stash

# Stash with descriptive message
git stash save "WIP: authentication feature"

# List stashes
git stash list

# Apply stash
git stash apply

# Apply and remove stash
git stash pop

# Apply specific stash
git stash apply stash@{2}
```

## Advanced Techniques

### Technique 1: Signed Commits

**Set up GPG signing**:
```bash
# Generate GPG key
gpg --full-generate-key

# List GPG keys
gpg --list-secret-keys --keyid-format=long

# Configure Git to use GPG key
git config --global user.signingkey YOUR_KEY_ID

# Sign commits automatically
git config --global commit.gpgsign true

# Sign a specific commit
git commit -S -m "feat: add feature"
```

### Technique 2: Co-authored Commits

**Credit multiple contributors**:
```bash
git commit -m "feat: implement search feature

Implemented full-text search with Elasticsearch.

Co-authored-by: Jane Doe <jane@example.com>
Co-authored-by: John Smith <john@example.com>"
```

### Technique 3: Commit Templates

**Set up commit message template**:
```bash
# Create template file
cat > ~/.gitmessage << 'EOF'
# type(scope): subject (max 50 chars)
# |<----  Using a Maximum Of 50 Characters  ---->|


# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|


# Provide links or keys to any relevant tickets, articles or other resources
# Example: Closes #23

# --- COMMIT END ---
# Type can be
#    feat     (new feature)
#    fix      (bug fix)
#    refactor (refactoring code)
#    style    (formatting, missing semicolons, etc; no code change)
#    docs     (changes to documentation)
#    test     (adding or refactoring tests; no production code change)
#    chore    (updating grunt tasks etc; no production code change)
# --------------------
# Remember to
#   - Capitalize the subject line
#   - Use the imperative mood in the subject line
#   - Do not end the subject line with a period
#   - Separate subject from body with a blank line
#   - Use the body to explain what and why vs. how
#   - Can use multiple lines with "-" for bullet points in body
EOF

# Configure Git to use template
git config --global commit.template ~/.gitmessage
```

### Technique 4: Git Hooks for Quality

**Pre-commit hook example** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash

# Run linting
echo "Running linter..."
npm run lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Please fix errors before committing."
    exit 1
fi

# Run tests
echo "Running tests..."
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix before committing."
    exit 1
fi

# Check for console.log
if git diff --cached --name-only | xargs grep -n "console.log" --with-filename; then
    echo "Found console.log statements. Remove them before committing."
    exit 1
fi

echo "Pre-commit checks passed!"
exit 0
```

## Common Pitfalls and Solutions

### Pitfall 1: Committing Everything at Once

**Problem**: `git add .` and commit all changes together.

**Solution**: Review changes with `git diff`, stage selectively with `git add -p`.

### Pitfall 2: Vague Commit Messages

**Problem**: Messages like "fix", "update", "changes".

**Solution**: Use conventional commits format, explain **why** changes were made.

### Pitfall 3: Mixing Concerns in One Commit

**Problem**: Bug fix + feature + refactoring in one commit.

**Solution**: Create atomic commits - one logical change per commit.

### Pitfall 4: Committing Sensitive Information

**Problem**: Accidentally commit API keys, passwords, or secrets.

**Solution**:
```bash
# Remove from last commit (before push)
git rm --cached sensitive_file.txt
git commit --amend

# Remove from history (after push - requires force push!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch sensitive_file.txt" \
  --prune-empty --tag-name-filter cat -- --all

# Better: Use tools like git-secrets to prevent commits
git secrets --install
git secrets --register-aws
```

### Pitfall 5: Breaking the Build

**Problem**: Commit breaks tests or prevents project from building.

**Solution**: Always run tests before committing. Use pre-commit hooks.

## Multi-Language Commit Examples

### Python Example

```bash
# Stage Python files for authentication feature
git add src/auth/jwt_service.py tests/test_jwt_service.py

git commit -m "feat(auth): implement JWT token service

Add JWTService class to handle token generation, validation,
and refresh operations. Uses PyJWT library with RS256 algorithm.

- Generate access tokens (15 min expiry)
- Generate refresh tokens (7 day expiry)
- Validate token signatures and expiry
- Extract user claims from tokens

Includes comprehensive unit tests with 95% coverage.

Closes #145"
```

### JavaScript Example

```bash
# Stage JavaScript files for API endpoint
git add src/api/controllers/userController.js tests/userController.test.js

git commit -m "feat(api): add user profile update endpoint

Implement PATCH /api/users/:id endpoint to allow users to
update their profile information. Validates input and ensures
users can only update their own profiles.

- Add validation middleware for user input
- Implement authorization check
- Add integration tests
- Update API documentation

Closes #256"
```

### Java Example

```bash
# Stage Java files for service layer
git add src/main/java/com/example/service/OrderService.java \
        src/test/java/com/example/service/OrderServiceTest.java

git commit -m "feat(order): implement order cancellation service

Add OrderService.cancelOrder() method to handle order cancellations
with inventory rollback. Includes transaction management to ensure
data consistency.

- Validate order can be cancelled (not shipped)
- Update order status to CANCELLED
- Rollback inventory quantities
- Send cancellation notification
- Add unit and integration tests

Closes #378"
```

## Success Criteria

- [ ] Each commit represents **one logical change**
- [ ] Commit messages follow **conventional commits** format
- [ ] Commit messages explain **why**, not just **what**
- [ ] No commits mix **unrelated changes**
- [ ] All commits include **relevant tests**
- [ ] Tests **pass** before pushing
- [ ] No **sensitive information** in commits
- [ ] No **debug code** or console.logs in commits
- [ ] Commit history is **clean and reviewable**
- [ ] Pull requests have **clear descriptions**

## Related Skills

- [`plan-before-code`](../plan-before-code/SKILL.md) - Plan changes before committing
- [`test-driven-development`](../test-driven-development/SKILL.md) - Write tests with commits
- [`code-review-quality`](../code-review-quality/SKILL.md) - Review commits before PR
- [`pre-commit-checklist`](../pre-commit-checklist/SKILL.md) - Quality gates before commits
- [`create-claude-md`](../create-claude-md/SKILL.md) - Configure project standards

## Additional Resources

### Git Best Practices
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message convention
- [Git Best Practices](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [Pro Git Book](https://git-scm.com/book/en/v2) - Complete Git guide

### Tools
- [pre-commit](https://pre-commit.com/) - Git hooks framework
- [commitlint](https://commitlint.js.org/) - Lint commit messages
- [husky](https://typicode.github.io/husky/) - Git hooks for JavaScript
- [git-secrets](https://github.com/awslabs/git-secrets) - Prevent committing secrets

### Workflows
- [GitHub Flow](https://guides.github.com/introduction/flow/) - Simple branching model
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) - Feature branch workflow
- [Trunk Based Development](https://trunkbaseddevelopment.com/) - Continuous integration approach

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Git best practices, Conventional Commits specification
