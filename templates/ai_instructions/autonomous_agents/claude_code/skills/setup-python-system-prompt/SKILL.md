---
name: setup-python-system-prompt
description: Configure comprehensive Python development system prompt for Claude Code with best practices, standards, and workflows
version: 1.0.0
author: Benjamin Dourthe
language: Python
category: Configuration
tags: [python, setup, system-prompt, configuration, standards]
---

# Setup Python System Prompt

Configure Claude Code with comprehensive Python development standards, best practices, and workflows optimized for production-quality code generation.

## When to Use This Skill

Use this skill when you need to:

- Set up a new Python project with Claude Code

- Configure Claude Code for Python development

- Apply comprehensive Python development standards

- Establish consistent coding practices across Python projects

- Optimize Claude Code for Python-specific workflows

## What This Skill Does

This skill helps you configure Claude Code with:

1. **Python Development Standards**

   - PEP 8 compliance and Black formatting (88 char lines)

   - Import organization (stdlib → third-party → local)

   - Type hints and modern Python patterns

   - Function design and naming conventions

2. **Project Architecture Guidelines**

   - Standard project structure (src/, tests/, docs/)

   - Virtual environment setup and management

   - Configuration files (pyproject.toml, requirements.txt)

   - Documentation structure (README, CHANGELOG, DEVLOG)

3. **Testing Framework**

   - Comprehensive test structure and patterns

   - Test output formatting requirements

   - Performance timing and result aggregation

   - Pass/fail criteria configuration

4. **Development Workflow**

   - Task breakdown methodology

   - Iterative testing protocol

   - Quality gates and checklists

   - Version control best practices

5. **Code Quality Standards**

   - Docstring templates (complex and simple)

   - Comment guidelines (no meta-commentary)

   - Error handling patterns

   - Performance considerations

## Prerequisites

- Claude Code installed and configured

- Python 3.9+ installed

- Basic understanding of Python development

- Project directory created (or ready to create new project)

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**

- Best for: Complex projects, enterprise development, full-stack applications

- Features: Complete architectural guidance, extensive best practices, detailed error handling

- Token count: ~40,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/python/CLAUDE_comprehensive_40k.md`

**Condensed Version (~20k tokens)**

- Best for: Quick development, prototyping, smaller projects

- Features: Essential guidelines, core best practices, streamlined workflow

- Token count: ~20,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/python/CLAUDE_condensed_20k.md`

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the Python system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your project root directory

2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/python/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/python/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```
3. Claude Code will automatically detect and load this file

#### Method B: Session-Based Configuration

Start Claude Code with the system prompt:
```bash
# For comprehensive version
claude --system-prompt ./path/to/CLAUDE_comprehensive_40k.md

# For condensed version
claude --system-prompt ./path/to/CLAUDE_condensed_20k.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to:

1. **Create a simple Python function** and observe if it follows the standards:
   ```
   "Create a function that calculates the fibonacci sequence"
   ```

   Expected behavior:

   - Type hints included

   - Docstring present

   - PEP 8 compliant

   - No inline comments unless necessary

2. **Request project structure** and verify it matches standards:
   ```
   "Show me the recommended project structure for a Python CLI application"
   ```

   Expected behavior:

   - Includes src/, tests/, docs/ directories

   - Shows pyproject.toml and requirements.txt

   - Includes CHANGELOG.md, README.md, DEVLOG.md

3. **Ask about testing** and confirm it knows the framework:
   ```
   "How should I structure my tests for this project?"
   ```

   Expected behavior:

   - Mentions run_all_tests.py, common.py, test_config.py

   - Describes test output formatting requirements

   - Explains pass/fail criteria configuration

### Step 4: Customize for Your Organization (Optional)

If you need to add organization-specific standards:

1. Open the CLAUDE.md file in your project

2. Add a new section at the end:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - [Your custom standards]

   - [Internal tool preferences]

   - [Compliance requirements]
   ```
3. Save and restart Claude Code session

### Step 5: Commit to Version Control

Add the CLAUDE.md to your repository so team members have consistent configuration:

```bash
git add CLAUDE.md
git commit -m "Add Claude Code Python system prompt configuration"
git push
```

## Key Features of the Python System Prompt

### 1. Import Organization
Automatically organizes imports in the correct order:

1. Standard library (alphabetically sorted)

2. Third-party libraries (grouped by function with headers)

3. Local application imports (alphabetically sorted)

### 2. Code Standards
- **Line length**: 88 characters (Black standard)

- **Functions**: One blank line between functions

- **Classes**: Two blank lines between classes

- **Comments**: Above code, explain "why" not "what"

- **No change-tracking comments**: Prevents "changed value to 12" style comments

### 3. Testing Framework
- Master test runner with auto-detection

- Comprehensive test output formatting (100-char separators, box-drawing tables)

- Performance timing for all tests

- Configurable pass/fail criteria

### 4. Documentation Standards
- Complex function docstrings with parameters, returns, raises, authors

- Simple function docstrings for straightforward functions

- README.md structure with installation and usage

- CHANGELOG.md following Keep a Changelog format

- DEVLOG.md for development history (single source of truth)

### 5. Development Workflow
- Task breakdown for projects >30 minutes

- Iterative testing protocol (create temp tests, iterate until pass, cleanup)

- Quality gates before delivery

- Version control best practices

### 6. Command Preferences
- **Critical**: Never run commands in chat, always request user execution

- PowerShell syntax for Windows environments

- Virtual environment activation and management

- Package management best practices

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: Standards Not Being Followed
**Solution**: Explicitly reference the standard in your request:
```
"Following the import organization standard in CLAUDE.md, organize the imports in this file"
```

### Issue: Need Different Standards for Subproject
**Solution**: Create a project-specific CLAUDE.md in the subproject directory with overrides

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with Python system prompt (CLAUDE.md in project root)

- [ ] Verified configuration by testing function generation

- [ ] Confirmed project structure knowledge

- [ ] Validated testing framework understanding

- [ ] Optionally customized for organization-specific needs

- [ ] Committed CLAUDE.md to version control for team consistency

## Related Skills

- `generate-docstrings`: Use after setup to document existing Python code

- `setup-test-infrastructure`: Establish testing framework following system prompt standards

- `code-review-quality`: Review Python code quality against configured standards

- `cleanup-python`: Clean up Python code following configured standards

## Additional Resources

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)

- [Black Code Formatter](https://black.readthedocs.io/)

- [Python Type Hints](https://docs.python.org/3/library/typing.html)

- [pytest Documentation](https://docs.pytest.org/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
