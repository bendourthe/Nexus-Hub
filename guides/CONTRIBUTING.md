# Contributing to AI Templates

Thank you for your interest in contributing to AI Templates! This document provides guidelines for contributing skills, templates, tools, and documentation to make Claude Code more powerful and accessible.

## Table of Contents

- [Code of Conduct](#code-of-conduct)

- [Getting Started](#getting-started)

- [Contributing Skills](#contributing-skills)

- [Contributing Templates](#contributing-templates)

- [Contributing Tools](#contributing-tools)

- [Contributing Documentation](#contributing-documentation)

- [Quality Standards](#quality-standards)

- [Submission Process](#submission-process)

- [Testing Guidelines](#testing-guidelines)

---

## Code of Conduct

By participating in this project, you agree to:

- Be respectful and inclusive

- Provide constructive feedback

- Focus on what is best for the community

- Show empathy towards other contributors

---

## Getting Started

### Prerequisites

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   git clone https://github.com/[your-username]/devai-hub.git
   cd devai-hub
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-skill-name
   ```

3. **Set up development environment**
   ```bash
   # Install Python 3.9+
   python --version

   # Test tools work
   python infrastructure/tools/build_skills_catalog.py
   python infrastructure/tools/install_skill.py --list
   ```

---

## Contributing Skills

Skills are the core of this repository. Follow these guidelines to create high-quality Claude Code skills.

### Skill Structure

Create a new directory under `claude-skills-catalog/{category}/`:

```
claude-skills-catalog/{category}/your-skill-name/
├── SKILL.md              # Required: Main skill file
└── README.md             # Optional: Additional documentation
```

### SKILL.md Template

Follow the [official Claude Skills specification](https://code.claude.com/docs/en/skills):

```markdown
---
name: your-skill-name
description: Brief description of what the skill does AND when to use it. Include trigger phrases like "Use when..." (max 1024 characters)
---

# Skill Name

Longer description explaining what the skill does and when to use it.

## When to Use This Skill

List specific scenarios:

- ✅ Scenario 1

- ✅ Scenario 2

- ✅ Scenario 3

## What This Skill Does

Detailed explanation of functionality and approach.

### Phase 1: [First Step]
Description of what happens in this phase.

### Phase 2: [Second Step]
Description of what happens in this phase.

## How to Use

    ```
    "Use the your-skill-name skill to accomplish [task]"
    ```

## Expected Behavior

Describe what Claude will do when this skill is invoked.

## Quality Criteria

List success criteria:

- [ ] Criterion 1

- [ ] Criterion 2

## Examples

Provide real-world examples of skill usage.

## Notes

- Important considerations

- Limitations

- Best practices

## Related Skills

- [related-skill-1](../related-skill-1/SKILL.md)

- [related-skill-2](../related-skill-2/SKILL.md)
```

### Skill Categories

Choose the most appropriate category:

| Category | Purpose | Examples |
|----------|---------|----------|
| **Workflow** | Development processes | plan-before-code, test-driven-development |
| **Configuration** | Setup and customization | create-claude-md, optimize-context-usage |
| **Code Review** | Analysis and quality | code-review-security, code-review-performance |
| **Code Cleanup** | Maintenance and refactoring | cleanup-python, cleanup-javascript |
| **Documentation** | Docs generation | generate-api-docs, create-user-documentation |
| **Testing** | Test creation and setup | setup-test-infrastructure, generate-test-cases |
| **Project Init** | Project scaffolding | init-python-project, init-javascript-project |
| **Security** | Security audits | dependency-security-audit, licensing-compliance-check |
| **Migration** | Code modernization | migrate-python-2-to-3, dependency-upgrade |
| **Analysis** | Code metrics | code-complexity-analysis |

### Skill Priority Levels

- **CRITICAL**: Essential for all projects (e.g., plan-before-code)

- **HIGH**: Very useful, recommended for most projects

- **MEDIUM**: Useful for specific scenarios

- **LOW**: Nice-to-have, specialized use cases

### Naming Conventions

- Use kebab-case: `skill-name-here`

- Be descriptive and specific

- Use verbs for actions: `generate-`, `create-`, `setup-`

- Be concise but clear

**Good Examples:**

- `plan-before-code`

- `generate-api-docs`

- `cleanup-python`

**Bad Examples:**

- `my_skill` (underscore, not descriptive)

- `doStuff` (camelCase, vague)

- `python-code-cleanup-and-modernization-tool` (too long)

---

## Contributing Templates

Templates provide structured prompts for specific tasks.

### Template Categories

- **Code Review**: Multi-phase review processes

- **Code Cleanup**: Dead code removal and refactoring

- **Test Development**: Test generation and infrastructure

- **Documentation**: API docs, user guides, technical docs

### Template Structure

```markdown
# Template Title

## Purpose
What this template accomplishes.

## When to Use
Specific scenarios for this template.

## Instructions
Step-by-step process.

## Expected Output
What the user should receive.

## Quality Checklist
- [ ] Criterion 1

- [ ] Criterion 2
```

---

## Contributing Tools

Tools enhance repository functionality and user experience.

### Tool Requirements

1. **Python scripts** in `infrastructure/tools/` directory

2. **Comprehensive docstrings** with usage examples

3. **Command-line interface** using `argparse`

4. **Error handling** for common failure cases

5. **Cross-platform compatibility** (Windows, Linux, macOS)

### Tool Template

```python
"""
Tool Name - Brief description.

Detailed explanation of what this tool does.

Usage:
    python infrastructure/tools/tool_name.py --option value

Authors:

    - Your Name (your.email@example.com)
"""
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Tool description',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--option', help='Option description')
    args = parser.parse_args()

    try:
        # Tool logic here
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

---

## Contributing Documentation

### Documentation Standards

1. **Clarity**: Write for beginners and experts alike

2. **Examples**: Include practical, real-world examples

3. **Structure**: Use consistent headings and formatting

4. **Completeness**: Cover common use cases and edge cases

5. **Maintenance**: Keep documentation up-to-date with code changes

### Documentation Categories

- **README files**: Overview and quick start

- **Skill documentation**: SKILL.md files with usage

- **Tool documentation**: Tools README with examples

- **API documentation**: Reference for programmatic use

---

## Quality Standards

All contributions must meet these standards:

### Content Quality

- [ ] **Clear and concise**: Easy to understand

- [ ] **Accurate**: Technically correct

- [ ] **Complete**: Covers all necessary information

- [ ] **Tested**: Verified to work as described

- [ ] **Well-structured**: Logical organization

- [ ] **Grammatically correct**: Proper spelling and grammar

### Technical Quality

- [ ] **Follows conventions**: Naming, formatting, structure

- [ ] **Cross-platform**: Works on Windows, Linux, macOS

- [ ] **Error handling**: Graceful failure with helpful messages

- [ ] **Performance**: Efficient, no unnecessary operations

- [ ] **Security**: No vulnerabilities or unsafe practices

### Skill-Specific Quality

- [ ] **YAML frontmatter**: Complete and accurate

- [ ] **Clear purpose**: When to use section is specific

- [ ] **Detailed instructions**: Step-by-step guidance

- [ ] **Examples**: Real-world usage scenarios

- [ ] **Quality criteria**: Measurable success conditions

- [ ] **Related skills**: Links to complementary skills

---

## Submission Process

### 1. Prepare Your Contribution

- **Create or modify files** following guidelines above

- **Test thoroughly** on multiple platforms if possible

- **Update catalog** if adding/modifying skills:
  ```bash
  python infrastructure/tools/build_skills_catalog.py
  ```

### 2. Commit Changes

```bash
# Add files
git add claude-skills-catalog/{category}/your-skill-name/
git add skills.json  # If updated

# Commit with descriptive message
git commit -m "feat: Add [skill-name] skill for [purpose]"

# Push to your fork
git push origin feature/your-skill-name
```

### 3. Create Pull Request

1. Go to GitHub and create a Pull Request

2. **Title**: Clear, descriptive (e.g., "Add cleanup-rust skill")

3. **Description**: Include:

   - What you're adding/changing

   - Why it's useful

   - How you tested it

   - Related issues (if any)

**PR Template:**
```markdown
## Description
[Clear description of changes]

## Type of Change
- [ ] New skill

- [ ] New template

- [ ] New tool

- [ ] Documentation

- [ ] Bug fix

- [ ] Enhancement

## Skill/Template Details (if applicable)
- **Name**: skill-name

- **Category**: Category

- **Priority**: CRITICAL | HIGH | MEDIUM | LOW

- **Language**: Multi-language | Specific

## Testing
- [ ] Tested on Windows

- [ ] Tested on Linux

- [ ] Tested on macOS

- [ ] Updated skills.json

- [ ] Documentation updated

## Checklist
- [ ] Follows contribution guidelines

- [ ] Meets quality standards

- [ ] Includes examples

- [ ] No breaking changes
```

### 4. Review Process

1. **Maintainers review** your contribution

2. **Feedback provided** if changes needed

3. **Iterate** based on feedback

4. **Merged** once approved

---

## Testing Guidelines

### Manual Testing

**For Skills:**

1. Test skill invocation in Claude Code

2. Verify expected behavior

3. Test edge cases and error conditions

4. Check cross-language support (if applicable)

**For Tools:**

1. Test all command-line options

2. Test with invalid inputs

3. Test on different operating systems

4. Verify error messages are helpful

### Automated Testing

If adding tools, consider including tests:

```python
# tests/test_tool_name.py
import unittest
from tools.tool_name import function_to_test


class TestToolName(unittest.TestCase):
    def test_basic_functionality(self):
        result = function_to_test("input")
        self.assertEqual(result, "expected")


if __name__ == '__main__':
    unittest.main()
```

---

## Common Pitfalls to Avoid

### Skills

- ❌ Too vague: "Use this for coding"

- ❌ Too narrow: Only works for one specific framework version

- ❌ Missing frontmatter or incomplete metadata

- ❌ No examples or usage guidance

- ❌ Assumes too much prior knowledge

### Tools

- ❌ Platform-specific code without fallbacks

- ❌ Poor error messages: "Error" vs "File not found: path/to/file"

- ❌ No command-line help

- ❌ Hardcoded paths

### Documentation

- ❌ Outdated examples that no longer work

- ❌ Missing context or prerequisites

- ❌ Inconsistent formatting

- ❌ Broken links

---

## Recognition

Contributors will be:

- Listed in skill/tool author fields

- Mentioned in release notes for significant contributions

- Thanked in repository README

---

## Questions?

- **Issues**: Open an issue on GitHub for bugs or feature requests

- **Discussions**: Use GitHub Discussions for questions

- **Email**: Contact repository maintainer: benjamin.dourthe@gmail.com

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

*Thank you for making Claude Code more powerful for everyone!*

*Contributing Guidelines v1.0.0 - AI Templates v0.2.6*

*Last Updated: October 21, 2025*
