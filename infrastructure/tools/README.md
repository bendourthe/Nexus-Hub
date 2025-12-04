# AI Templates - Tools

Utilities for managing, installing, and working with Claude Code skills from the AI Templates repository.

## Available Tools

### 1. build_skills_catalog.py

Build a comprehensive JSON catalog of all skills in the repository.

**Usage:**
```bash
python tools/build_skills_catalog.py
```

**Output:**
- Creates `catalogs/skills.json`
- Contains metadata for all 48+ skills
- Includes statistics, categories, and security validation

**When to Run:**
- After adding new skills
- After modifying skill metadata
- Before publishing repository updates

---

### 2. install_skill.py

Install Claude Code skills to your project's `.claude/skills/` directory.

**Usage:**

```bash
# List all available skills
python tools/install_skill.py --list

# Show skill categories
python tools/install_skill.py --categories

# Get detailed skill information
python tools/install_skill.py --info plan-before-code

# Install a specific skill
python tools/install_skill.py --skill plan-before-code

# Install all skills in a category
python tools/install_skill.py --category workflow

# Install all critical priority skills
python tools/install_skill.py --priority CRITICAL

# Install ALL skills
python tools/install_skill.py --all

# Install to specific location
python tools/install_skill.py --skill test-driven-development --destination ~/my-project

# Force overwrite existing skills
python tools/install_skill.py --skill plan-before-code --force
```

**Options:**
- `--skill, -s`: Install specific skill by name
- `--category, -c`: Install all skills in category
- `--priority, -p`: Install skills by priority (CRITICAL, HIGH, MEDIUM, LOW)
- `--all, -a`: Install all skills
- `--list, -l`: List all available skills
- `--categories`: Show all categories
- `--info, -i`: Show detailed skill information
- `--destination, -d`: Installation location (default: auto-detect)
- `--force, -f`: Overwrite existing skills
- `--repo`: Path to repository (default: auto-detect)

**Examples:**

```bash
# Quick start: Install critical skills
python tools/install_skill.py --priority CRITICAL

# Development workflow setup
python tools/install_skill.py --skill plan-before-code
python tools/install_skill.py --skill test-driven-development
python tools/install_skill.py --skill code-commit-workflow

# Complete code review toolkit
python tools/install_skill.py --category "Code Review"

# Project initialization
python tools/install_skill.py --skill init-python-project
python tools/install_skill.py --skill create-claude-md
```

---

## Installation Workflow

### For New Projects

1. **Install critical workflow skills:**
   ```bash
   python tools/install_skill.py --priority CRITICAL
   ```

2. **Add project-specific skills:**
   ```bash
   python tools/install_skill.py --skill init-python-project
   python tools/install_skill.py --skill setup-python-system-prompt
   ```

3. **Configure project:**
   ```bash
   # Use the installed skills in Claude Code
   "Use the create-claude-md skill to configure this project"
   ```

### For Existing Projects

1. **Audit and cleanup:**
   ```bash
   python tools/install_skill.py --category "Code Cleanup"
   python tools/install_skill.py --category "Code Review"
   ```

2. **Enhance testing:**
   ```bash
   python tools/install_skill.py --category Testing
   ```

3. **Improve documentation:**
   ```bash
   python tools/install_skill.py --category Documentation
   ```

---

## Skill Categories

| Category | Skills | Focus |
|----------|--------|-------|
| **Workflow** | 5 | Development processes and best practices |
| **Configuration** | 10 | Project setup and Claude customization |
| **Code Cleanup** | 7 | Remove dead code, modernize codebases |
| **Code Review** | 6 | Comprehensive code analysis workflow |
| **Documentation** | 6 | API docs, docstrings, user guides, technical docs |
| **Testing** | 2 | Test infrastructure and generation |
| **Project Init** | 4 | Initialize new projects (Python, JS, Java, C#) |
| **Security** | 3 | Audits, compliance, pre-commit checks |
| **Migration** | 4 | Upgrade dependencies, refactor, extract services |
| **Analysis** | 1 | Code complexity and quality metrics |

---

## Advanced Usage

### Batch Installation

Install multiple skill sets for complete project setup:

```bash
# Full development environment
python tools/install_skill.py --priority CRITICAL
python tools/install_skill.py --category workflow
python tools/install_skill.py --category configuration

# Quality assurance suite
python tools/install_skill.py --category "Code Review"
python tools/install_skill.py --category security
python tools/install_skill.py --category testing

# Documentation suite
python tools/install_skill.py --category documentation
```

### Custom Installation Script

Create a setup script for your team:

```bash
#!/bin/bash
# install_dev_skills.sh

echo "Installing development skills..."

# Core workflow
python tools/install_skill.py --skill plan-before-code --force
python tools/install_skill.py --skill test-driven-development --force
python tools/install_skill.py --skill debug-with-logs --force

# Project setup
python tools/install_skill.py --skill create-claude-md --force
python tools/install_skill.py --skill init-python-project --force

# Code quality
python tools/install_skill.py --category "Code Review" --force

echo "Installation complete!"
```

---

## Troubleshooting

### Skill Not Found

**Problem:** `Skill not found: xyz`

**Solution:**
1. Run `python tools/install_skill.py --list` to see available skills
2. Check spelling and use exact skill name
3. Rebuild catalog: `python tools/build_skills_catalog.py`

### Cannot Find .claude Directory

**Problem:** `Warning: No .claude directory found`

**Solution:**
1. The tool will create `.claude/skills/` in current directory
2. Or specify destination: `--destination ~/my-project`
3. Or run from project root that contains `.claude/`

### Skills Already Installed

**Problem:** `Skill 'xyz' already installed`

**Solution:**
- Use `--force` to overwrite: `python tools/install_skill.py --skill xyz --force`

### Encoding Issues (Windows)

**Problem:** Unicode/emoji errors on Windows console

**Solution:**
- Tool uses ASCII-safe markers instead of emojis
- Use `chcp 65001` to enable UTF-8 in Windows console (optional)

---

## Contributing

### Adding New Tools

1. Create script in `tools/` directory
2. Follow naming convention: `verb_noun.py`
3. Include comprehensive docstring
4. Add to this README
5. Test on multiple platforms (Windows, Linux, Mac)

### Improving Existing Tools

1. Update script with improvements
2. Rebuild catalog if metadata structure changes
3. Test all command-line options
4. Update documentation
5. Submit pull request

---

## Future Enhancements

Planned tool additions:

- [ ] `validate_skill.py` - Verify skill integrity and security
- [ ] `update_skill.py` - Update installed skills to latest versions
- [ ] `remove_skill.py` - Uninstall skills cleanly
- [ ] `export_skills.py` - Export installed skills for sharing
- [ ] `import_skills.py` - Import skill collections
- [ ] `skill_usage_stats.py` - Track which skills are most used

---

*Tools v1.0.0 - Part of AI Templates v0.2.6*

*Last Updated: October 21, 2025*
