---
name: context-analysis
description: Establish comprehensive understanding of project structure, architecture, dependencies, and current state before conducting detailed code review. Use as the first phase of any code review, when onboarding to a new codebase, before proposing architectural changes, or for technical due diligence.
summary_l0: "Analyze project structure, architecture, and dependencies as code review Phase 1"
overview_l1: "This skill establishes comprehensive understanding of a project before conducting detailed code review, serving as Phase 1 of the 6-phase code review methodology. Use it when beginning a comprehensive code review, onboarding to an unfamiliar codebase, understanding project architecture and design decisions, identifying technical debt before detailed review, mapping dependencies and potential risks, or planning follow-up review phases. Key capabilities include project structure mapping, architecture pattern identification, dependency graph analysis, tech stack detection, technical debt cataloging, risk area identification, and review scope planning. The expected output is a context analysis report with project overview, architecture summary, dependency map, risk assessment, and recommended review focus areas. Trigger phrases: code review, analyze codebase, understand architecture, project analysis, technical due diligence, codebase overview, onboarding."
---

# Code Review - Context Analysis

Establish comprehensive understanding of the project before conducting detailed code review. This skill is **Phase 1** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Begin a comprehensive code review
- Onboard to an unfamiliar codebase
- Understand project architecture and design decisions
- Identify technical debt before detailed review
- Map dependencies and potential risks
- Plan follow-up review phases

**Trigger phrases**: "code review", "analyze codebase", "understand architecture", "project analysis", "technical due diligence", "codebase overview", "onboarding"

## Review Mode Detection

This skill supports two modes:

- **Full Codebase**: Analyze the entire project structure, architecture, and dependencies
- **Git Changes**: Scope analysis to current git changes and their surrounding context

## What This Skill Does

### Analysis Areas

1. **Repository Discovery**
   - Directory structure analysis
   - Key files identification
   - Documentation review

2. **Architecture Understanding**
   - Entry points identification
   - Design patterns recognition
   - Module dependency mapping

3. **Dependency Analysis**
   - External dependency listing
   - Security vulnerability scan
   - Outdated package detection

4. **Build & Deployment**
   - Build system review
   - CI/CD configuration
   - Environment setup

5. **Codebase Metrics**
   - Lines of code
   - Complexity metrics
   - Code duplication

## Instructions

### Step 1: Determine Review Mode

**Full Codebase Mode:**
```bash
# Get directory structure
tree -L 3 -I 'node_modules|venv|.venv|__pycache__|target|build'

# Identify key files
ls -la

# Read documentation
cat README.md
cat CONTRIBUTING.md
```

**Git Changes Mode (Preflight):**
```bash
# Scope the changes
git status -sb
git diff --stat
git diff

# Find related modules and usages
rg "function_name" --type-add 'src:*.{py,js,ts,java,go,cs,cpp}'
```

### Edge Case Handling

- **No changes detected**: Inform the user and ask if they want to review staged changes (`git diff --cached`) or a specific commit range
- **Large diff (>500 lines)**: Summarize changes by file first, then batch analysis by module or feature area
- **Mixed concerns**: Group findings by logical feature rather than file order

### Step 2: Architecture Analysis

1. **Identify Entry Points**
   - Look for main.py, index.js, Application.java
   - Find CLI entry points
   - Locate API endpoints

2. **Map Design Patterns**
   - MVC, layered architecture
   - Repository pattern
   - Factory, singleton patterns

3. **Trace Dependencies**
   - Internal module imports
   - External library usage

4. **Identify Critical Paths**
   - Authentication and authorization flows
   - Payment or financial operations
   - Data writes and mutations
   - Network boundaries and external API calls

### Step 3: Dependency Health Check

```bash
# Python
pip-audit
pip list --outdated

# JavaScript
npm audit
npm outdated

# Java
mvn versions:display-dependency-updates
```

### Step 4: Generate Context Report

Create a report with:
- Executive summary
- Project structure
- Architecture analysis
- Dependency health
- Key findings
- Review focus recommendations

## Output Template

```markdown
# Code Review Context Analysis Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]
**Mode**: [Full Codebase / Git Changes]

## Executive Summary
- **Project Purpose**: [Description]
- **Primary Language**: [Language]
- **Architecture Style**: [Pattern]

## Project Structure
[Directory tree]

## Key Components
- Entry Points: [List]
- Core Modules: [List]
- External Interfaces: [APIs, CLI]
- Critical Paths: [Auth, payments, data writes, network]

## Dependency Health
- Total Dependencies: [Count]
- Outdated: [Count]
- Vulnerabilities: [Count]

## Key Findings
### Strengths
1. [Finding]

### Concerns
1. [Finding]

## Recommendations for Review Focus
1. [Area] - [Reason]
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I can review the diff directly without mapping the project first" | Reviewing a payment-flow change without knowing it sits behind an auth guard leads to flagging a non-issue or missing that the guard was bypassed; context is what tells you which lines are critical paths. |
| "The README describes the architecture, so I don't need to map it" | READMEs drift from reality; the documented "layered architecture" is often a god-module in practice, and only a directory and dependency scan reveals the actual structure under review. |
| "Dependency health is a separate concern from this review" | A code change that adds a call into an unpinned, known-CVE dependency is a review finding; skipping the dependency scan in Phase 1 means later phases lack the context to flag it. |
| "Skipping context analysis saves time on small changes" | A 10-line change to a shared utility can ripple across dozens of callers; without mapping usages first, the reviewer cannot scope the blast radius and approves a breaking change. |

## Verification

- [ ] Repository structure documented (directory tree captured)
- [ ] Entry points identified and listed
- [ ] Architecture patterns recognized and named
- [ ] Dependencies analyzed (count and outdated/vulnerable totals recorded)
- [ ] Dependency vulnerability scan run (`pip-audit` / `npm audit` / equivalent) with output saved
- [ ] Critical paths mapped (auth, payments, data writes, network boundaries)
- [ ] Codebase metrics collected (lines of code, complexity)
- [ ] Context report generated at the documented path with review-focus recommendations

## Related Skills

- [[code-quality]] -- Code quality + SOLID + dead code review (Phase 2), run after this context pass
- [[security-review]] -- Security analysis across the 10-domain model (Phase 3)
- [[performance-review]] -- Performance analysis (Phase 4)
- [[testing-review]] -- Test assessment (Phase 5)
- [[final-report]] -- Consolidated report with verdict (Phase 6)

---

**Version**: 2.0.0
**Last Updated**: February 2026
**Based on**: Nexus-Hub code review methodology + code-review-expert


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
