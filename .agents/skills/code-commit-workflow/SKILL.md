---
name: code-commit-workflow
description: Implement proper Git commit workflow with conventional commits, atomic changes, and meaningful messages. Use when committing changes, preparing pull requests, or establishing team commit standards. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Create atomic conventional commits with canonical documentation paths"
overview_l1: "This skill implements proper Git commit workflow with conventional commits, atomic changes, and meaningful messages. Use it when committing changes, preparing pull requests, or establishing team commit standards. Key capabilities include conventional commit message formatting, atomic change grouping, meaningful commit message writing, interactive staging guidance, commit history organization, pull request preparation, branch strategy implementation, and team commit standard enforcement. The expected output is well-structured Git commits with conventional format, atomic scope, and meaningful messages that enable clear project history. Trigger phrases: commit workflow, conventional commits, commit message, atomic commit, pull request, Git workflow, commit standards, meaningful commits. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Code Commit Workflow

Implement a professional Git commit workflow with conventional commits, atomic changes, and meaningful commit messages that enhance project history and collaboration.

When a commit carries version-bound documentation, stage it from `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`; closed snapshots belong under `docs/archives/`. Treat legacy path changes as migration work and keep them atomic with reference repair.

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

## Plan-Context Mode (invoked by `/implement`)

The Instructions below are the GENERIC one-off commit workflow and are unchanged: stage what belongs together, write a sectioned message, verify before committing. Everything in this section applies ONLY when this skill is invoked from a plan phase by `[[implement-phase]]`. Outside that context, ignore it.

### The commit unit is the phase, not the sub-task

Accumulate changes across the whole phase, validate them together, and create exactly ONE commit at the phase boundary. Do not commit per sub-task.

This is not a relaxation of atomicity; it is a different unit of atomicity. A plan phase is the smallest independently revertible unit the plan defines, because its sub-tasks are written to be completed together and its exit checklist gates on all of them. Committing per sub-task produces a history whose intermediate states never passed the phase gate, so `git revert` on any one of them leaves a tree the plan never validated.

The exception is explicit: when the plan itself defines separate independently revertible units inside a phase, honor that. The plan is the authority on its own granularity.

### Non-final plan commits stay LOCAL

A non-final phase commit is not pushed. No push, no pull request, no remote CI.

The reason is cost and signal together. Pushing per phase starts a full pipeline run for each phase, so a seven-phase plan pays seven times for six runs that validate work the plan itself says is incomplete. Worse, those runs go red for expected reasons, and a team that sees expected red checks stops reading red checks.

A user who explicitly asks to push a non-final phase is making a deliberate exception. State the cost in one line and do what they ask; the default is removed, not their authority.

### The final plan commit is the only one that publishes

The final phase creates its commit, obtains explicit approval, and pushes ONCE. That push is the plan's first remote event and the integration pull request is its first comprehensive validation, run against the merge result rather than the branch tip.

### Correction work after a red required check

A red check REOPENS the final phase. It does not authorize a re-run and it does not authorize a fresh commit stream.

1. Classify the failure.
2. Reproduce it LOCALLY. A check that cannot be reproduced locally is itself the finding: an environment difference, a missing local dependency, or an interpreter version floor. Nexus-Hub has shipped that exact defect, where a green local run on a newer interpreter proved nothing about the older one that gated the merge.
3. Apply the narrow fix and re-run the local gate.
4. Then EITHER amend the final commit (when the branch history should read as one clean phase) OR add ONE narrowly scoped stabilization commit (when the fix is worth its own entry in the history, or when the branch has already been reviewed). Never both, and never a series.
5. Push again with approval.

Never re-run a red check without a local reproduction. A re-run without one is a guess, and a guess that happens to go green has taught nobody anything.

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
- **Sectioned-bullet structure (CRITICAL for non-trivial commits)**: After the subject line and a 1-2 sentence intro paragraph, organize the body as **labeled sections with bullets**, NOT as multiple flowing paragraphs separated by blank lines. Each section header ends in a colon and groups bullets by component, module, or theme (e.g., `Reporting package (`src/reporting/`):`, `Packaging and paths:`, `Desktop UI:`). Always treat **Tests** and **Known gaps** / **Deviations** as their own dedicated sections at the end. For trivial 1-2 file commits, a single short paragraph body is fine; for any commit touching multiple components, use sectioned bullets.
- **Why grouped sections beat flowing paragraphs**: a multi-paragraph body forces reviewers to scan dense prose to find the change for a specific component. Grouped bullets put section headers in scannable position, let reviewers jump to the package they care about, and make the structure of the change visible at a glance.
- **No hard-wrapping (CRITICAL)**: every paragraph and every bullet point in the body and footer MUST be written as a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). Let the editor or terminal handle visual wrapping. Blank lines still separate sections, paragraphs, and bullets; the rule applies *within* each paragraph or bullet, never *between* them. The subject line is the only exception (its 50-character cap is a hard limit, not a wrap).
- **Whitespace**: exactly one blank line between sections; never two or more. Within a section, bullets are contiguous (no blank lines between them).
- Use ASCII characters only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.

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

Worked good and bad examples for every commit type: [`references/commit-message-examples.md`](references/commit-message-examples.md).

The rule they illustrate, in one line: the subject says WHAT changed in the imperative mood under 72 characters, and the body says WHY it changed and what a reader would otherwise have to reconstruct from the diff.

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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Commit messages don't matter for a solo project" | Solo project history becomes a multi-developer history the moment the project is open-sourced, onboarded a contractor, or diagnosed six months later by the original author; vague messages like "fix stuff" make git bisect useless. |
| "Atomic commits slow down development" | Non-atomic commits that bundle unrelated changes make every future revert destructive -- reverting a bug fix to unblock deployment also reverts an unrelated migration, causing data loss or schema mismatch. |
| "I will commit each sub-task so the history is granular" | In plan context the phase is the revertible unit: its sub-tasks are written to complete together and its exit checklist gates on all of them. Per-sub-task commits produce intermediate states that never passed the phase gate, so reverting one leaves a tree the plan never validated. Honor a finer granularity only when the plan itself defines it. |
| "Pushing each phase keeps the branch backed up" | A remote branch is a backup; a remote PIPELINE RUN is a bill. If the goal is durability, push a branch with no CI trigger or use a local mirror. Pushing into a validation trigger to get a backup pays for six runs of knowingly incomplete work to solve a problem that is not about CI. |
| "The remote check failed but a re-run will probably fix it" | Then the check is flaky and that is the finding, or it is real and the re-run wastes a run. Either way, reproduce it locally first. A check that cannot be reproduced locally means the local gate has a hole, which is worth more than the green re-run. |
| "We'll check for secrets in the PR review" | PR review catches secrets intermittently; pre-commit hooks (`detect-secrets`, `gitleaks`) catch them deterministically before they enter git history, where they persist even after force-push removal and require history rewriting. |
| "Conventional commit format is rigid and unnecessary" | Automated changelog generation, semantic versioning bumps, and release notes tools (`standard-version`, `semantic-release`) all depend on conventional commit format; without it, every release requires manual changelog curation. |
| "Breaking changes don't need special marking if reviewers are careful" | API consumers depend on automated tooling that parses `BREAKING CHANGE:` footers to block auto-updates; unmarked breaking changes bypass these safeguards and silently break downstream consumers. |
| "Wrapping the commit body at 72 columns is the standard convention" | Hard-wrapping was a workaround for terminals that could not soft-wrap; modern Git tooling, GitHub, GitLab, IDE diff views, and `git log` all soft-wrap on display, and hard-wrapped source breaks copy-paste into changelogs and review comments because the line breaks survive the round-trip. The user's rule is one source line per paragraph or bullet; the renderer handles visual wrapping. |
| "This bullet is too long, I should break it into two lines for readability" | Visual readability is the renderer's job, not the source's. A bullet broken into a continuation line stops being a single bullet to most Markdown and Git UIs; the second line is parsed as a new paragraph or as part of the bullet's "looser" rendering. Keep the source as one line; if it is genuinely too long to follow, split it into two separate bullets with distinct points. |
| "Flowing paragraphs read better than bulleted lists for prose-heavy commits" | Reviewers don't read commit bodies linearly - they scan for the component or theme they care about. A multi-paragraph flowing body forces them to read every paragraph to find the part touching their package; a sectioned-bullet body lets them jump straight to the labeled header. The "prose-heavy" framing also fights against `git log --oneline` follow-up reads where only the section headers fit on screen. Use sectioned bullets for any commit touching multiple components; a single short paragraph is fine only for trivial 1-2 file commits. |

## Verification

- [ ] Commit message follows conventional commit format: `<type>(<scope>): <description>` with valid type
- [ ] All tests pass at the commit point: `git stash && npm test` / `pytest -q` exits with code 0
- [ ] `git diff --staged` shows only changes related to the single logical change described in the commit message
- [ ] No secrets present: pre-commit hook (`detect-secrets` or `gitleaks`) exits with code 0
- [ ] Breaking changes are marked with `BREAKING CHANGE:` footer or `!` in the type field
- [ ] No `Co-Authored-By` or AI attribution lines appear in the commit message
- [ ] No Unicode punctuation in commit message (no em-dashes, en-dashes, curly quotes, ellipsis): these cause encoding corruption on Windows
- [ ] No hard-wrapped paragraphs or bullets in body/footer: spot-check by viewing the message with `git show --no-patch HEAD` and confirming each paragraph and bullet renders as one source line (no mid-paragraph newlines except blank-line paragraph separators)

## Related Skills

- [[pre-commit-checklist]] -- runs the lint/secret/test gate before this skill stages and commits
- [[security-review]] -- security checks to clear before a commit touches sensitive code paths
- [[code-quality]] -- the quality standards a commit should already satisfy before it is recorded

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
