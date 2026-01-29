---
name: context-analysis
description: Establish comprehensive understanding of project structure, architecture, dependencies, and current state before conducting detailed code review. Use as the first phase of any code review, when onboarding to a new codebase, before proposing architectural changes, or for technical due diligence.
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

### Step 1: Repository Discovery

```bash
# Get directory structure
tree -L 3 -I 'node_modules|venv|.venv|__pycache__|target|build'

# Identify key files
ls -la

# Read documentation
cat README.md
cat CONTRIBUTING.md
```

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

## Quality Checklist

- [ ] Repository structure documented
- [ ] Entry points identified
- [ ] Architecture patterns recognized
- [ ] Dependencies analyzed
- [ ] Vulnerabilities checked
- [ ] Metrics collected
- [ ] Context report generated

## Related Skills

- `code-quality` - Code quality review (Phase 2)
- `security-review` - Security analysis (Phase 3)
- `performance-review` - Performance analysis (Phase 4)
- `testing-review` - Test assessment (Phase 5)
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/context_analysis/
