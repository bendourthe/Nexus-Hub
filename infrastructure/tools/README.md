# DevAI-Hub Tools

Utilities for managing, installing, and working with Claude Code skills from the DevAI-Hub repository.

## Available Tools

### 1. build_skills_catalog.py

Build a comprehensive JSON catalog of all skills in the repository.

**Usage:**
```bash
python tools/build_skills_catalog.py
```

**Output:**

- Creates `data/skills.json`

- Contains metadata for all 174+ skills

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
python tools/install_skill.py --skill setup-project
```

---

### 3. validate_skills.py

Validate skill file integrity — checks for required frontmatter fields, correct directory structure, and schema compliance.

**Usage:**
```bash
python scripts/validate_skills.py
```

**When to Run:**

- After adding or modifying a skill

- Before submitting a pull request

- As part of CI (`make validate`)

---

## Installation Workflow

> **Recommended**: Use the DevAI-Hub installer for first-time setup. It installs all skills, commands, hooks, agents, and permissions globally and per-project in one step:
> - **Windows**: double-click `install.bat` at the repository root
> - **macOS / Linux**: run `./install.sh` at the repository root
>
> Use `install_skill.py` only when you need to selectively add or refresh individual skills after the initial install.

### For New Projects

1. **Run the installer** (see above) — installs everything globally and configures your project.

2. **Add extra project-specific skills** (optional, post-install):
   ```bash
   python tools/install_skill.py --skill init-python-project
   python tools/install_skill.py --skill setup-project
   ```

3. **Configure project:**
   ```bash
   # Use the installed skills in Claude Code
   "Use the setup-project skill to configure this project"
   ```

### For Existing Projects

1. **Re-run the installer** to pick up new skills and commands added since your last install.

2. **Or selectively add skills** with `install_skill.py`:
   ```bash
   python tools/install_skill.py --category "code-cleanup"
   python tools/install_skill.py --category "code-review"
   python tools/install_skill.py --category testing
   python tools/install_skill.py --category documentation
   ```

---

## Skill Categories

| Category | Focus |
|----------|-------|
| **ai-development** | AI agents, RAG pipelines, prompt engineering, multi-provider routing |
| **architecture** | System design, DDD, event-driven, microservices, API design |
| **bug-fixing** | Bug localization, patch generation, regression analysis |
| **business-product** | Product management, technical writing, business analysis, Scrum |
| **code-cleanup** | Language-specific dead code removal and modernization (Python, JS, Go, Java, C#, C, C++) |
| **code-review** | Quality, security, performance, and testing review phases |
| **compliance** | Regulatory frameworks (GDPR, SOC2, ISO27001, PCI-DSS, CCPA, NIST AI RMF) |
| **developer-experience** | Refactoring, legacy modernization, async patterns, tooling |
| **documentation** | API docs, docstrings, strategic comments, technical and user documentation |
| **framework-specialists** | React, Next.js, Vue, Svelte, Astro, FastAPI |
| **infrastructure** | Cloud, containers, Kubernetes, CI/CD, observability, SRE, database design |
| **language-specialists** | Python, TypeScript, Go, Rust, Java, C#, C++, SQL, PowerShell |
| **orchestration** | Context management, multi-agent coordination, task orchestration |
| **project-setup** | Initialize new projects (Python, JS, Java, C#) |
| **research** | Trend research across Reddit, X, and the web |
| **security** | Dependency audits, authentication patterns, exploit and CVE analysis |
| **specialized-domains** | Android, iOS, fintech, PDF/DOCX/PPTX/XLSX generation, GLSL shaders |
| **testing** | E2E testing automation and domain contract validation |
| **tests-generation** | Unit tests, integration tests, mocks, coverage, mutation testing, fuzzing |
| **workflow** | TDD, commit workflow, debugging, session history, implementation planning |

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
python tools/install_skill.py --skill setup-project --force
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

- [ ] `update_skill.py` - Update installed skills to latest versions

- [ ] `remove_skill.py` - Uninstall skills cleanly

- [ ] `export_skills.py` - Export installed skills for sharing

- [ ] `import_skills.py` - Import skill collections

- [ ] `skill_usage_stats.py` - Track which skills are most used

---

*Tools - Part of DevAI-Hub v1.1.4*

*Last Updated: May 2026*
