---
name: create-custom-command
description: Create custom slash commands for Claude Code to automate repetitive tasks. Use when establishing team workflows, automating code reviews, creating project-specific commands, or standardizing development processes.
summary_l0: "Create custom slash commands for Claude Code to automate repetitive workflows"
overview_l1: "This skill creates custom slash commands for Claude Code to automate repetitive tasks. Use it when establishing team workflows, automating code reviews, creating project-specific commands, or standardizing development processes. Key capabilities include slash command YAML frontmatter design, phased command structure with instructions, argument and parameter configuration, command template creation, team workflow standardization, and command testing and validation. The expected output is ready-to-use custom slash command files with proper frontmatter, instructions, and parameter definitions. Trigger phrases: custom command, slash command, automate workflow, create command, Claude Code command, team workflow, standardize process."
---

# Create Custom Commands

Create custom slash commands for Claude Code to automate repetitive tasks and establish consistent workflows across your team.

## When to Use This Skill

Use this skill when you need to:

- Automate repetitive Claude Code interactions
- Establish team-wide workflows
- Create project-specific commands
- Standardize code review processes
- Build custom documentation generators
- Create onboarding commands

**Trigger phrases**: "create custom command", "slash command", "claude command", "automate workflow", "custom /command"

## What This Skill Does

Creates reusable slash commands stored in `.claude/commands/` that can be invoked with `/command-name` in Claude Code.

### Command File Structure

```
project/
├── .claude/
│   └── commands/
│       ├── review.md           # /review command
│       ├── test.md             # /test command
│       ├── document.md         # /document command
│       └── onboard.md          # /onboard command
```

## Instructions

### Step 1: Create Commands Directory

```bash
mkdir -p .claude/commands
```

### Step 2: Create Command Files

Each `.md` file in `.claude/commands/` becomes a slash command.

#### Example: Code Review Command

```markdown
<!-- .claude/commands/review.md -->
# Code Review Command

Review the provided code for:

## Quality Checks
1. **Code Style**: Check for consistent formatting, naming conventions
2. **Best Practices**: Identify anti-patterns and suggest improvements
3. **Error Handling**: Verify proper exception handling
4. **Performance**: Look for potential bottlenecks

## Security Checks
1. Input validation
2. SQL injection vulnerabilities
3. XSS vulnerabilities
4. Hardcoded secrets

## Output Format
Provide findings in this format:

### Summary
Brief overview of the code quality.

### Issues Found
| Severity | Location | Issue | Suggestion |
|----------|----------|-------|------------|
| High/Medium/Low | file:line | Description | Fix |

### Recommendations
Prioritized list of improvements.
```

#### Example: Test Generation Command

```markdown
<!-- .claude/commands/test.md -->
# Generate Tests Command

Generate comprehensive tests for the provided code:

## Test Types
1. **Unit Tests**: Test individual functions/methods
2. **Edge Cases**: Test boundary conditions
3. **Error Cases**: Test error handling
4. **Integration**: Test component interactions

## Requirements
- Use the project's testing framework
- Follow AAA pattern (Arrange, Act, Assert)
- Aim for 80%+ code coverage
- Include meaningful test descriptions

## Output
Provide complete, runnable test code with:
- Test file structure
- All imports
- Setup/teardown if needed
- Descriptive test names
```

#### Example: Documentation Command

```markdown
<!-- .claude/commands/document.md -->
# Documentation Generator

Generate documentation for the provided code:

## Documentation Types

### For Functions/Methods
```
/**
 * Brief description
 *
 * @param {type} name - Description
 * @returns {type} Description
 * @throws {Error} When condition
 * @example
 * // Usage example
 */
```

### For Classes
- Purpose and responsibility
- Constructor parameters
- Public methods
- Usage examples

### For Modules
- Overview
- Exports
- Dependencies
- Example usage

## Output Format
Provide documentation in the language's standard format.
```

#### Example: Onboarding Command

```markdown
<!-- .claude/commands/onboard.md -->
# Codebase Onboarding

Provide a comprehensive overview of this codebase:

## Analysis Required

### 1. Project Structure
- Directory layout and purpose of each folder
- Key files and their roles
- Configuration files

### 2. Architecture
- Overall architecture pattern (MVC, microservices, etc.)
- Main components and their interactions
- Data flow

### 3. Technology Stack
- Languages and frameworks
- Key dependencies
- Development tools

### 4. Entry Points
- Main application entry
- API endpoints
- CLI commands

### 5. Getting Started
- Setup instructions
- Environment requirements
- Running locally
- Running tests

### 6. Key Concepts
- Domain-specific terminology
- Important patterns used
- Common conventions

## Output
Provide a structured onboarding guide a new developer can follow.
```

#### Example: PR Description Command

```markdown
<!-- .claude/commands/pr.md -->
# Generate PR Description

Analyze the current changes and generate a PR description:

## Required Information

1. **Summary**: One-line description of changes
2. **Motivation**: Why these changes are needed
3. **Changes Made**: Bullet list of modifications
4. **Testing**: How changes were tested
5. **Screenshots**: If UI changes (placeholder)
6. **Breaking Changes**: If any
7. **Related Issues**: Link to tickets

## Output Format

```markdown
## Summary
[One line summary]

## Motivation
[Why this change is needed]

## Changes
- [Change 1]
- [Change 2]
- [Change 3]

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots
[Add screenshots if UI changes]

## Breaking Changes
[List any breaking changes or "None"]

## Related Issues
Closes #[issue-number]
```
```

### Step 3: Use Commands with Arguments

Commands can accept arguments after the command name:

```markdown
<!-- .claude/commands/fix.md -->
# Fix Issue Command

Analyze and fix the issue described: $ARGUMENTS

## Process
1. Understand the issue from the description
2. Locate relevant code
3. Identify root cause
4. Implement fix
5. Verify fix doesn't break existing functionality

## Output
- Explanation of the issue
- Root cause analysis
- Code changes with explanation
- Verification steps
```

Usage: `/fix the login button doesn't work on mobile`

### Step 4: Create Parameterized Commands

```markdown
<!-- .claude/commands/scaffold.md -->
# Scaffold Component

Create a new component with the following parameters:

**Name**: $ARGUMENTS

## Generate
1. Component file (`{name}.tsx`)
2. Styles file (`{name}.module.css`)
3. Test file (`{name}.test.tsx`)
4. Story file (`{name}.stories.tsx`)

## Component Template
```tsx
import styles from './{name}.module.css';

interface {Name}Props {
  // Define props
}

export function {Name}({ }: {Name}Props) {
  return (
    <div className={styles.container}>
      {/* Implementation */}
    </div>
  );
}
```

## Test Template
```tsx
import { render, screen } from '@testing-library/react';
import { {Name} } from './{name}';

describe('{Name}', () => {
  it('renders correctly', () => {
    render(<{Name} />);
    // Add assertions
  });
});
```
```

Usage: `/scaffold UserProfile`

### Step 5: Team-Wide Commands

Create commands for team workflows:

```markdown
<!-- .claude/commands/standup.md -->
# Daily Standup Helper

Analyze recent changes to prepare standup notes:

## Look For
1. **Git commits** from the last 24 hours
2. **Modified files** and their purpose
3. **TODO comments** added or resolved
4. **Test coverage** changes

## Output Format

### Yesterday
- [What was completed]

### Today
- [Planned work]

### Blockers
- [Any impediments]

### Notes
- [Additional context]
```

```markdown
<!-- .claude/commands/release.md -->
# Prepare Release

Prepare release notes and checklist:

## Gather
1. All commits since last tag
2. New features (feat commits)
3. Bug fixes (fix commits)
4. Breaking changes
5. Dependencies updated

## Output

### Release v[X.Y.Z] Notes

#### New Features
- [Feature 1]
- [Feature 2]

#### Bug Fixes
- [Fix 1]
- [Fix 2]

#### Breaking Changes
- [Change 1]

#### Migration Guide
[If breaking changes, provide migration steps]

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Release notes written
- [ ] Stakeholders notified
```

## Description Style: Combat Undertriggering

The description field at the top of a command's Markdown file (or, equivalently, the description that goes into a skill's YAML frontmatter) is what the AI agent scans when deciding whether to trigger this command. Claude has a measurable tendency to **under-trigger** when the description is narrow, clean, or implicit. The fix is not a longer description -- it is a **pushy** description: list the trigger phrases AND the skip phrases explicitly so the agent cannot rationalize its way past them.

### Rules

- **List trigger phrases verbatim.** If the user is likely to say "build me a dashboard", "show internal metrics", "visualize the data", put those exact phrases in the description.
- **Add a SKIP clause.** Use `SKIP: ...` or `Do NOT use for: ...` to fence off look-alike requests the command should not handle. This is what stops over-triggering after you make the description pushier.
- **Cover synonyms and adjacent intents.** A description for a "dashboard" command should also cover "internal metrics", "data visualization", "company data display" -- not just the literal word "dashboard".
- **Lead with the action, then the trigger surface.** First sentence states what the command does; second sentence lists when to invoke it; third sentence (if needed) lists when to skip.

### Before / After example

**Before** (narrow, agent under-triggers):

> "How to build a dashboard."

**After** (pushy, agent triggers reliably without false positives):

> "How to build a dashboard. Make sure to use this command whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard'. SKIP: standalone chart generation (use chart-builder), one-off data exports (use data-export), or read-only status pages without filtering controls."

The "After" form trades 6 words for 60. Those 60 words pay for themselves the first time the agent would have skipped a relevant invocation under the "Before" form.

### Cross-reference

This rule applies identically to **skill descriptions** in `catalog/skills/<cat>/<name>/SKILL.md` frontmatter. See AGENTS.md "Adding a New Skill -> Write SKILL.md" for the same rule applied to skills.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The description is short and clean, so it'll trigger fine." | Claude undertriggers on narrow descriptions. Explicit trigger phrases beat poetic brevity. The agent reads the description literally; it does not infer adjacent intents. |
| "Listing skip phrases is overkill." | Without `SKIP:` clauses, every pushier description widens the false-positive surface. Skip clauses are how you make the description pushier without making it noisier. |
| "The agent will figure out from the body what the command does." | The body is tier 2 (loaded after the trigger fires). The description is tier 1 (always loaded). If the description does not trigger, the body never gets read. |

## Command Best Practices

### Do's

```markdown
# Good: Clear structure
## Steps
1. First, do X
2. Then, do Y
3. Finally, do Z

## Output Format
[Clear specification of expected output]
```

### Don'ts

```markdown
# Bad: Vague instructions
Do the thing.

# Bad: No output format
Review the code.
```

### Include Context

```markdown
# Good: Project-specific context
This project uses:
- React with TypeScript
- Jest for testing
- Tailwind for styling

Follow existing patterns in src/components/.
```

## Verification

- [ ] The command file exists at `.claude/commands/<name>.md` and is non-empty
- [ ] The file states a single clear purpose in its opening line
- [ ] An Output Format section defines what the command produces
- [ ] Every argument the command consumes is documented in the body
- [ ] Invoking `/<name>` twice on the same input produces the same structure
- [ ] The command body has been reviewed by at least one other team member

## Advanced: Command Composition

Reference other commands:

```markdown
<!-- .claude/commands/full-review.md -->
# Full Code Review

Perform a comprehensive review combining multiple checks:

1. First, run quality checks as defined in /review
2. Then, generate tests as defined in /test
3. Finally, update documentation as defined in /document

Provide a combined report with all findings.
```

## Skill-Authoring Methodology (bundled references)

Writing a command or a skill body is the cold-start phase; writing a *discipline-enforcing* one (a gate that must resist rationalization under pressure) needs a test-first methodology before you ever run an empirical eval. Three bundled references under `references/` cover that methodology. Read them when authoring a skill whose job is to make the agent do the harder, correct thing (verify before claiming done, investigate root cause before patching, get a design approved before coding), not merely teach a capability.

- `references/tdd-for-skills.md` - the RED-GREEN-REFACTOR loop for skill authoring: run the pressure scenario WITHOUT the skill and capture rationalizations verbatim (RED), write the skill to rebut them (GREEN), close the new loopholes the agent finds (REFACTOR), plus the Iron Law ("no skill without a failing baseline first") and how this complements the empirical `skill-eval-loop`.
- `references/pressure-testing.md` - how to construct scenarios that apply real, combined pressure (time, sunk cost, authority, exhaustion, social, pragmatic), the meta-testing question ("how could the skill have been written so the disciplined action was the only acceptable answer?"), and the signals that a discipline skill is bulletproof.
- `references/persuasion-principles.md` - the research-backed framing (Cialdini 2021; Meincke et al. 2025) behind why gates and rationalization tables work, which principles to use (authority, commitment, scarcity, social proof, unity) and which to AVOID for compliance (liking and reciprocity, which produce sycophancy), with a principle-by-skill-type table.

These three feed directly into the `skill-eval-loop` iteration phase: the baseline run that TDD-for-skills uses to mine rationalizations is the same paired control `skill-eval-loop` uses to measure marginal value.

## Related Skills

- `plan-before-code` - Planning commands
- `code-quality` - Review commands
- `test-structure` - Testing commands
- `[[skill-eval-loop]]` - the empirical iteration loop that measures and hardens the draft this skill's authoring methodology produces

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: Claude Code Custom Commands Documentation


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
