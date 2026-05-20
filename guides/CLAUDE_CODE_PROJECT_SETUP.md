# Claude Code Project Setup Guide

**Complete guide for setting up new projects with the modular CLAUDE.md architecture**

[← Back to Main](../README.md) | [Claude Code Guide](CLAUDE_CODE_GUIDE.md)

---

## Table of Contents

- [Introduction](#introduction)
- [Quick Start (5 minutes)](#quick-start-5-minutes)
- [Understanding the Architecture](#understanding-the-architecture)
- [Step-by-Step Setup](#step-by-step-setup)
- [Skill Installation](#skill-installation)
- [Customization](#customization)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

<a name="introduction"></a>
## Introduction

This guide walks you through setting up a new project with the optimized, modular CLAUDE.md system specifically designed for Claude Code. The architecture preserves all instructions from comprehensive templates while achieving ~80% token efficiency through skills-based loading.

**What You'll Achieve:**
- Minimal core CLAUDE.md (~100 lines) that loads every conversation
- Skills that auto-activate based on task context
- ~80% reduction in token usage (from ~40,000 to ~4,000-8,000 tokens)
- Better instruction adherence through focused, context-relevant loading
- Preserved comprehensive instructions in modular, maintainable format

**Prerequisites:**
- Claude Code installed and configured
- Access to this Nexus-Hub repository
- Basic familiarity with Claude Code's `.claude` directory structure

---

<a name="quick-start-5-minutes"></a>
## Quick Start (5 minutes)

For experienced users who want to get started immediately:

```bash
# 1. Navigate to your project directory
cd your-project

# 2. Copy the language-specific template (e.g., Python)
cp -r /path/to/Nexus-Hub/templates/ai-instructions/CLAUDE_MD/python/* .
# Or for other languages: javascript/, java/, csharp/, go/, c/, cpp/

# 3. Start Claude Code
claude
```

Then in Claude Code, run these commands:
```
/setup-project      # Configure your CLAUDE.md (5 questions)
/import-skills      # Import additional skills from the catalog (optional)
```

The `/setup-project` wizard guides you through 5 questions to generate a polished project description for your `CLAUDE.md`.

The `/import-skills` command lets you interactively select and import skills from the Nexus-Hub catalog - choose all, by category, or specific skills.

### Available Slash Commands

Each template includes four pre-configured slash commands:

| Command | Description |
|---------|-------------|
| `/setup-project` | Interactive wizard to configure your CLAUDE.md with project name, description, features, and target users |
| `/import-skills` | Import skills from the Nexus-Hub catalog (select all, by category, or specific skills) |
| `/update-documentation` | 8-step documentation consistency audit (checks links, versions, structure, deprecated references) |
| `/upgrade-version` | 11-step semantic version upgrade assistant (updates all version references across files) |

### How Slash Commands Work

**Slash commands become available automatically** when you copy a template to your project. Here's what happens:

1. **Copy the template** - The `.claude/commands/` directory is included:
   ```bash
   cp -r python/* your-project/
   # This copies .claude/commands/*.md files
   ```

2. **Start Claude Code** - Open VS Code with Claude Code extension, or run `claude` in terminal:
   ```bash
   cd your-project
   claude
   ```

3. **Use commands** - Type the command name with `/`:
   ```
   /setup-project
   /import-skills
   ```

**Technical Details:**
- Commands are markdown files in `.claude/commands/` directory
- Claude Code automatically discovers commands in this location
- Each `.md` file becomes a `/command-name` (filename without extension)
- Commands execute as prompts that guide Claude through specific workflows

**Directory Structure After Copy:**
```
your-project/
├── CLAUDE.md                    # Core instructions
├── .claude/
│   ├── commands/                # Slash commands (auto-discovered)
│   │   ├── setup-project.md     # → /setup-project
│   │   ├── import-skills.md     # → /import-skills
│   │   ├── update-documentation.md  # → /update-documentation
│   │   └── upgrade-version.md   # → /upgrade-version
│   ├── skills/                  # Auto-activated capabilities
│   ├── context/                 # Project-specific docs
│   └── memory/                  # Persistent knowledge
```

---

<a name="understanding-the-architecture"></a>
## Understanding the Architecture

### Why Modularize?

Comprehensive CLAUDE.md templates (like `CLAUDE_comprehensive_40k.md`) contain ~1,858 lines of excellent instructions. However:

| Issue | Impact |
|-------|--------|
| ~40,000 tokens loaded every conversation | Consumes context window |
| ~150+ instructions active simultaneously | LLMs follow ~150-200 max reliably |
| Irrelevant sections always present | Dilutes focus on current task |
| No progressive loading | Same load for simple and complex tasks |

### The Solution: Skills-Based Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE.md (~100 lines)                       │
│  - Project overview                                             │
│  - Tech stack                                                   │
│  - Critical commands                                            │
│  - Key patterns (with @imports)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Skills (Auto-Activated)                       │
├───────────────────┬───────────────────┬─────────────────────────┤
│ core/             │ governance/       │ python/                 │
│ ├─interaction-    │ ├─documentation-  │ ├─project-setup         │
│ │  principles     │ │  standards      │ ├─code-standards        │
│ └─quality-        │ └─version-        │ ├─testing-framework     │
│    checklist      │    control        │ └─command-preferences   │
├───────────────────┴───────────────────┴─────────────────────────┤
│ development/                                                     │
│ ├─workflow-methodology                                           │
│ └─implementation-patterns                                        │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:**
1. **CLAUDE.md** loads every conversation (~2,000 tokens)
2. **Skills** auto-activate based on task context (~2,000-6,000 tokens as needed)
3. **Total:** ~4,000-8,000 tokens vs ~40,000 = **80% reduction**

### Claude Code Memory Hierarchy

Claude Code uses a 4-level memory hierarchy:

1. **Enterprise policies** (if applicable) - Highest priority
2. **User-level** (`~/.claude/CLAUDE.md`) - Global preferences
3. **Project-level** (`project/CLAUDE.md`) - Project-specific rules
4. **Local context** - Current task focus

Skills are discovered automatically from `.claude/skills/` directories.

---

<a name="step-by-step-setup"></a>
## Step-by-Step Setup

### Step 1: Create Project Directory Structure

```bash
mkdir my-project
cd my-project

# Create the .claude directory structure
mkdir -p .claude/skills/core
mkdir -p .claude/skills/governance
mkdir -p .claude/skills/development
mkdir -p .claude/context
mkdir -p .claude/commands
mkdir -p .claude/memory
```

### Step 2: Create the Core CLAUDE.md

Create `CLAUDE.md` in your project root with this template:

```markdown
# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: Python 3.12+
- **Package Manager**: uv (or pip with venv)
- **Linting/Formatting**: ruff
- **Testing**: pytest
- **Type Checking**: mypy

## Project Structure
```
src/                  - Application source code
├── config/           - Configuration
├── core/             - Core application logic
├── gui/              - GUI components (if applicable)
├── utils/            - Utility functions
tests/                - Test suites
├── temp/             - Temporary tests (auto-deleted)
docs/                 - Documentation
```

## Key Files
- `pyproject.toml` - Dependencies and configuration
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
uv run python src/main.py

# Testing
uv run pytest tests/

# Linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/
```

## Quick Reference

### Task Types → Focus Areas
| Task Type | Skills Activated |
|-----------|------------------|
| Bug Fix | interaction-principles, code-standards, quality-checklist |
| New Feature | project-setup, workflow-methodology, testing-framework |
| Refactoring | code-standards, implementation-patterns |
| Documentation | documentation-standards |
| Version/Git | version-control |

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on fix
- **Full Mode** (new projects): Complete architecture, full testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with tests/temp/
- Document progress in DEVLOG.md
- Follow the quality checklist before delivering code
```

### Step 3: Create Standard Project Files

Create the following files in your project root:

**pyproject.toml:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "[project-name]"
version = "0.1.0"
description = "[project description]"
authors = [{name = "Your Name", email = "your@email.com"}]
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
```

**CHANGELOG.md:**
```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.1.0] - YYYY-MM-DD
### Added
- Initial project setup
```

**DEVLOG.md:**
```markdown
# Development Log

## Current Task List

### High Priority
- [ ]

### Medium Priority
- [ ]

### Low Priority
- [ ]

## Development History

### Project Architecture
- **Initial Design**: [Decisions]
- **Tech Stack**: [Choices]

### Technical Decisions
[Key decisions and rationale]
```

---

<a name="skill-installation"></a>
## Skill Installation

### Core Skills (All Projects)

These skills apply to ALL projects regardless of language.

#### 1. interaction-principles

Create `.claude/skills/core/interaction-principles/SKILL.md`:

```yaml
---
name: interaction-principles
description: Core AI-user interaction principles including clarification protocol, teaching approach, critical analysis, efficiency guidelines, and quality assurance. Use when starting tasks, explaining approach, or when user asks about communication style.
---

# Interaction Principles

## Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements

## Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and coding concepts
- Enable learning through understanding, not copy-paste
- Reference documentation for non-obvious concepts

## Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently
- Compare alternatives and recommend best solution
- Clearly explain reasoning and trade-offs

## Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete functions
- **Refactoring**: Consolidate duplicate logic

## Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance
- If already optimal, confirm briefly with reasoning

## System Prompt Adherence
- **Periodically review these instructions** throughout long conversations
- Ensure compliance with all coding standards and workflows
- Reference specific sections when needed to maintain consistency
```

#### 2. quality-checklist

Create `.claude/skills/core/quality-checklist/SKILL.md`:

```yaml
---
name: quality-checklist
description: Pre-delivery quality assurance checklists for code, projects, code reviews, and performance. Use before completing any coding task, delivering code, finishing features, or conducting code reviews.
---

# Quality Checklist

## Before Delivering Code
- [ ] **Functionality**: Code solves the stated problem completely
- [ ] **Style Compliance**: Follows all formatting guidelines
- [ ] **Documentation**: Includes appropriate docstrings and comments
- [ ] **Error Handling**: Includes appropriate exception handling
- [ ] **Type Hints**: Public functions include type annotations
- [ ] **Testing Considerations**: Suggests testing approach
- [ ] **Performance**: Considers efficiency implications
- [ ] **Security**: No obvious security vulnerabilities
- [ ] **Educational Value**: Explanation helps user learn
- [ ] **Best Practices**: Python conventions followed
- [ ] **Maintainability**: Easy to understand and modify
- [ ] **Dependencies**: All imports necessary and documented

## Before Delivering Project Structure
- [ ] **Standard Architecture**: Uses recommended project structure
- [ ] **Complete Setup**: All essential files included
- [ ] **Version Consistency**: Version numbers match across files
- [ ] **Documentation**: README, CHANGELOG, and DEVLOG present
- [ ] **Configuration**: Proper pyproject.toml
- [ ] **Testing Framework**: Test structure and utilities included
- [ ] **Git Integration**: Appropriate .gitignore configuration
- [ ] **Virtual Environment**: Setup instructions clear
- [ ] **Dependencies**: All documented
- [ ] **Examples**: Usage examples provided

## Code Review Standards
- [ ] **Logic**: Algorithm correctness verified
- [ ] **Edge Cases**: Boundary conditions handled
- [ ] **Resources**: Files/connections properly managed
- [ ] **Memory**: Efficient usage patterns
- [ ] **Scalability**: Can handle growth requirements
- [ ] **Debugging**: Appropriate logging included
- [ ] **Reusability**: Modular function design
- [ ] **Naming**: Clear, descriptive identifiers
- [ ] **Comments**: Add value, explain reasoning
- [ ] **Coverage**: Critical paths tested

## Performance Considerations
- [ ] **Algorithms**: Optimal complexity chosen
- [ ] **Data Structures**: Appropriate for use case
- [ ] **Memory Usage**: Efficient allocation/deallocation
- [ ] **I/O Operations**: Minimized and optimized
- [ ] **Caching**: Implemented where beneficial
- [ ] **Concurrency**: Thread safety considered
- [ ] **Database**: Queries optimized
- [ ] **Network**: Minimal requests, proper handling
```

### Governance Skills

#### 3. documentation-standards

Create `.claude/skills/governance/documentation-standards/SKILL.md`:

```yaml
---
name: documentation-standards
description: Documentation templates and standards for docstrings, README, CHANGELOG, and DEVLOG files. Includes the CRITICAL rule to NEVER create separate markdown files and ALWAYS document in DEVLOG.md. Use when creating or updating documentation.
---

# Documentation Standards

## Docstring Templates

### Complex Functions
```python
def process_user_data(data, param=None) -> List[Dict[str, Any]]:
    """
    Process and validate user records according to specified rules.

    Performs data cleaning, validation against business rules, and formatting
    for downstream processing.

    Parameters:
        - data (dict): Input data.
        - param (list, optional): Additional optional parameter.

    Returns:
        - response (DataFrame): Processed data.

    Raises:
        - ValueError: When additional parameters are malformed.

    Authors:
        - Your Name (your@email.com)
    """
```

### Simple Functions
```python
def calculate_total(items: List[float]) -> float:
    """Calculate total including tax."""
```

## Documentation Best Practices

**CRITICAL: Use DEVLOG.md for ALL Development Documentation**

- **NEVER create separate markdown files** like:
  - `TROUBLESHOOTING_ISSUE.md`
  - `FIX_SUMMARY.md`
  - `NEW_FEATURE_IMPLEMENTATION.md`
  - `BUG_FIX_DETAILS.md`
  - `IMPLEMENTATION_NOTES.md`

- **ALWAYS document in DEVLOG.md**:
  - All troubleshooting steps and iterations
  - Feature implementation progress
  - Bug fixes and their resolution process
  - Test results and iterations
  - Development decisions and rationale
  - Challenges encountered and solutions

**Why DEVLOG.md Only:**
- Single source of truth for development history
- Easier to search and reference
- Prevents documentation fragmentation
- Maintains chronological development narrative
- Reduces repository clutter
```

#### 4. version-control

Create `.claude/skills/governance/version-control/SKILL.md`:

```yaml
---
name: version-control
description: Version control governance including semantic versioning, Git operations restrictions, and DEVLOG update rules. CRITICAL rules for never auto-modifying versions and never suggesting Git commands unless requested. Use when discussing versions, Git, or commits.
---

# Version Control Governance

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update pyproject.toml versions
- Change README.md versions
- Create tags/releases

### Version Protocol

1. **Assess**: "Changes might warrant version update from X.Y.Z"
2. **Request**: "Should I update to [version]? Or handle manually?"
3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs
- **Minor (Y+1.0)**: New features
- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Never suggest:
- `git add/commit/push`
- `git branch/merge`
- `git tag` or releases
- `git init`

### When Git Help IS Requested

```
Since you requested Git help:

1. Check status: git status
2. Stage: git add src/ tests/
3. Commit: git commit -m "Add [feature]"
4. Push: git push origin [branch]

Verify before running:
- Correct branch: git branch
- Clean state: git status
- Tests pass locally
```

## DEVLOG.md Updates

Safe to update without permission:
- Task lists
- Development history
- Challenges/solutions
- Technical decisions
- Troubleshooting

Never include:
- Commit hashes
- Git workflow assumptions
- Version control strategies
```

### Development Skills

#### 5. workflow-methodology

Create `.claude/skills/development/workflow-methodology/SKILL.md`:

```yaml
---
name: workflow-methodology
description: Development workflow including task breakdown methodology and the CRITICAL iterative testing protocol using tests/temp/. Use when planning complex tasks, breaking down projects, or implementing features that need testing.
---

# Development Workflow

## Task Breakdown Methodology

### When to Use Task Breakdown
**Apply systematic breakdown for:**
- Projects estimated >30 minutes
- Multi-component applications
- Complex feature implementations
- Integration tasks with dependencies
- Refactoring projects

### Analysis Phase
**Always start with:**
1. **Requirements**: Identify components and dependencies
2. **Complexity**: Determine scope and challenges
3. **Prerequisites**: List setup and tools
4. **Risk**: Identify blockers and mitigation
5. **Success Metrics**: Define measurable outcomes

### Quality Gates
- [ ] Functionality verified
- [ ] Style compliance
- [ ] Documentation complete
- [ ] Tests included
- [ ] Performance acceptable
- [ ] Security checked
- [ ] Dependencies resolved
- [ ] Error handling added

## Iterative Testing Protocol

**CRITICAL: Test-Driven Problem Solving**

When implementing new features, fixing bugs, or troubleshooting issues, follow this iterative protocol:

### 1. Create Temporary Test Scripts
- Create test files in `tests/temp/` directory
- Name descriptively: `test_feature_validation.py`, `test_bug_reproduction.py`
- Write challenging tests that thoroughly validate the solution
- Include edge cases and error conditions

### 2. Implement Solution
- Write or modify code to address the issue
- Follow all code standards and best practices
- Document approach in DEVLOG.md

### 3. Run Tests and Iterate
- Execute the temporary test script
- If tests FAIL:
  - Analyze failure reasons
  - Document iteration in DEVLOG.md
  - Modify implementation
  - Repeat until tests pass
- If tests PASS:
  - Verify solution completeness
  - Proceed to cleanup

### 4. Clean Up Temporary Tests
- **Delete all files** in `tests/temp/` after successful implementation
- Move any valuable test cases to permanent test suites if needed
- Document final solution in DEVLOG.md

**Benefits:**
- Ensures solutions actually work before claiming completion
- Documents the problem-solving process
- Prevents premature declarations of success
- Creates robust, well-tested code
- Maintains clean repository (no temporary test clutter)
```

### Language-Specific Templates

Pre-configured templates are available for multiple languages in:
`templates/ai-instructions/CLAUDE_MD/`

| Language | Directory | Key Files |
|----------|-----------|-----------|
| Python | `python/` | pyproject.toml, pytest |
| JavaScript/TypeScript | `javascript/` | package.json, Jest/Vitest |
| Java | `java/` | pom.xml, JUnit 5 |
| C# | `csharp/` | *.csproj, xUnit |
| Go | `go/` | go.mod, go test |
| C | `c/` | CMakeLists.txt, Unity |
| C++ | `cpp/` | CMakeLists.txt, Google Test |

### Additional Skills

Production-ready skills are available in `catalog/skills/`:

| Category | Skills |
|----------|--------|
| `code-cleanup/` | Language-specific cleanup (Python, JS, Java, C#, Go, C, C++) |
| `code-review/` | Context analysis, quality, security, performance, testing |
| `compliance/` | SOC 2, ISO 27001, GDPR, PCI-DSS, NIST AI RMF |
| `documentation/` | API docs, docstrings, SBOM, technical docs |
| `project-setup/` | Language-specific project initialization |
| `security/` | Dependency audit, licensing, pre-commit checks |
| `tests-generation/` | Test cases, mocks, coverage, CI/CD |
| `workflow/` | Commit workflow, TDD, version upgrade, debugging |

---

<a name="customization"></a>
## Customization

### Adding Project-Specific Skills

Create custom skills in `.claude/skills/[category]/[skill-name]/SKILL.md`:

```yaml
---
name: your-skill-name
description: Clear description of when this skill should activate. Include trigger phrases like "Use when..." to help Claude Code identify relevant contexts.
---

# Skill Title

[Your skill content here]
```

### Adding Context Files

Store architectural decisions and project-specific context in `.claude/context/`:

```markdown
# architecture.md

## Design Decisions
- Why we chose [technology X]
- Trade-offs considered

## System Architecture
[Diagrams and explanations]
```

### Creating Custom Commands

Add reusable commands in `.claude/commands/`:

```markdown
# review.md
Review the current changes for:
1. Code quality and style compliance
2. Potential bugs or edge cases
3. Performance implications
4. Security considerations
```

---

<a name="verification"></a>
## Verification

### Check Memory Loading

Run Claude Code and use the `/memory` command:

```bash
claude
/memory
```

You should see:
- `CLAUDE.md` loaded
- Skills discovered in `.claude/skills/`

### Test Skill Activation

Try these prompts to verify skills activate:

| Prompt | Expected Skill(s) |
|--------|-------------------|
| "Create a new Python project" | `python/project-setup` |
| "How should imports be organized?" | `python/code-standards` |
| "Help me write tests" | `python/testing-framework` |
| "Update the version" | `governance/version-control` |
| "Review this code" | `core/quality-checklist` |

---

<a name="troubleshooting"></a>
## Troubleshooting

### Skill Not Activating

**Problem:** Claude doesn't use a skill when expected.

**Solutions:**
1. Check skill description includes trigger phrases
2. Verify SKILL.md is in correct location (`.claude/skills/[category]/[name]/SKILL.md`)
3. Check YAML frontmatter syntax is valid
4. Run `claude --debug` to see skill loading
5. Make the description more specific with "Use when..." phrases

### Too Many Skills Loading

**Problem:** Multiple unrelated skills activating.

**Solutions:**
1. Make skill descriptions more specific
2. Add explicit "Use when..." phrases
3. Remove overlapping trigger phrases
4. Use different trigger words for different skills

### Instructions Not Being Followed

**Problem:** Claude ignores specific rules.

**Solutions:**
1. Check the relevant skill is actually loading
2. Add emphasis: "CRITICAL:", "NEVER:", "ALWAYS:"
3. Move critical rules to core CLAUDE.md (always loaded)
4. Use `/clear` between tasks to reset context
5. Reduce total instruction count (keep under 150-200 active)

### Context Window Issues

**Problem:** Running out of context in long conversations.

**Solutions:**
1. Verify skills are loading on-demand (not all at once)
2. Keep CLAUDE.md under 100 lines
3. Use `@imports` for rarely-needed content
4. Start new conversations for unrelated tasks

---

## Additional Resources

- [Claude Code Guide](CLAUDE_CODE_GUIDE.md) - General Claude Code usage
- [Subagents Guide](SUBAGENTS_GUIDE.md) - Using specialist skills effectively
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to Nexus-Hub

---

**Version:** 1.0.0
**Last Updated:** December 2025
