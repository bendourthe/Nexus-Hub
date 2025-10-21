# Quick Start Guide: Set Up a New Project with Claude Code

**Goal**: Get a new project up and running with Claude Code superpowers in 5 minutes.

---

## What You'll Get

After following this guide, your project will have:

✅ **Complete project structure** (src/, tests/, docs/, etc.)
✅ **CLAUDE.md configuration** - Claude understands your project standards
✅ **48 production-ready skills** - Powerful commands for development
✅ **Testing infrastructure** - Ready to write tests immediately
✅ **Documentation templates** - Professional docs from day one
✅ **Git hooks** - Automated quality checks

---

## Prerequisites

- Python 3.9+ installed
- Git installed
- Claude Code installed ([Get it here](https://claude.ai/claude-code))
- 5 minutes of your time

---

## Step-by-Step Setup

### 1. Create Your Project

```bash
# Create your new project directory
mkdir my-awesome-project
cd my-awesome-project

# Initialize git
git init

# Create initial README
echo "# My Awesome Project" > README.md
git add README.md
git commit -m "Initial commit"
```

### 2. Get AI Templates (Temporary)

```bash
# Go up one level
cd ..

# Clone the AI templates repository
git clone https://github.com/bdourthe/ai_templates.git

# You'll delete this later - it's just for installation
```

### 3. Install Claude Code Skills

```bash
cd ai_templates

# Install essential skills (takes ~10 seconds)
python tools/install_skill.py --priority CRITICAL --destination ../my-awesome-project
python tools/install_skill.py --skill init-python-project --destination ../my-awesome-project
python tools/install_skill.py --category "Code Review" --destination ../my-awesome-project
```

**What just happened?**
- Installed 3 CRITICAL workflow skills (plan-before-code, test-driven-development, etc.)
- Installed Python project initialization skill
- Installed 6 code review skills for quality assurance

### 4. Initialize Your Project Structure

```bash
# Go to your project
cd ../my-awesome-project

# Start Claude Code
claude
```

**In Claude Code, type:**
```
Use the init-python-project skill to create 'my-awesome-project'
```

**Claude will:**
- Create src/, tests/, docs/ directories
- Generate pyproject.toml with proper configuration
- Create .gitignore with sensible defaults
- Set up testing framework (pytest)
- Create requirements.txt
- Generate initial documentation

### 5. Configure Claude for Your Project

**Still in Claude Code, type:**
```
Use the create-claude-md skill to configure this project as a Python web API
```

**Claude will:**
- Generate a comprehensive CLAUDE.md file
- Include your project structure
- Document bash commands
- Set coding standards
- Configure development workflow

### 6. Verify Everything Works

```bash
# Check your project structure
ls -la

# You should see:
# .claude/          (skills directory)
# src/              (source code)
# tests/            (test infrastructure)
# docs/             (documentation)
# CLAUDE.md         (Claude configuration)
# pyproject.toml    (project config)
# requirements.txt  (dependencies)
# .gitignore
# README.md
```

### 7. Start Developing with Superpowers!

**Back in Claude Code:**

```
"Use the plan-before-code skill to design a user authentication system"

"Use the test-driven-development skill to implement user registration"

"Use the code-review-security skill to audit the authentication code"

"Use the generate-api-docs skill to document the API endpoints"
```

### 8. Clean Up (Optional)

```bash
# Remove the temporary ai_templates clone
cd ..
rm -rf ai_templates

# Or keep it if you want to install more skills later
```

---

## What's Next?

### Explore Your Skills

```bash
# See what skills you have
ls .claude/skills/

# Read about a skill
cat .claude/skills/plan-before-code/SKILL.md
```

### Install More Skills

If you kept ai_templates:
```bash
cd ../ai_templates
python tools/install_skill.py --list
python tools/install_skill.py --skill generate-docstrings --destination ../my-awesome-project
```

### Set Up Git Hooks

```bash
# Copy pre-commit hook template
cp ../ai_templates/hooks/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Now every commit will run quality checks!
```

### Customize CLAUDE.md

Edit `CLAUDE.md` to add:
- Project-specific conventions
- Team coding standards
- Custom bash commands
- Architecture decisions
- Domain knowledge

---

## Common Scenarios

### Scenario: JavaScript/React Project

```bash
# Step 3 alternative:
python tools/install_skill.py --priority CRITICAL --destination ../my-project
python tools/install_skill.py --skill init-javascript-project --destination ../my-project
python tools/install_skill.py --skill cleanup-javascript --destination ../my-project

# Step 4: In Claude Code:
"Use the init-javascript-project skill to create a React application"
```

### Scenario: Existing Project (Add Skills)

```bash
# In your existing project directory
cd my-existing-project

# Install skills directly
python ../ai_templates/tools/install_skill.py --priority CRITICAL

# In Claude Code:
"Use the create-claude-md skill to configure this existing project"
```

### Scenario: Team Project with Standards

```bash
# Install comprehensive tooling
python tools/install_skill.py --category workflow --destination ../team-project
python tools/install_skill.py --category "Code Review" --destination ../team-project
python tools/install_skill.py --category Security --destination ../team-project

# In Claude Code:
"Use the create-claude-md skill with team standards:
- PEP 8 compliance required
- 80% test coverage minimum
- Security scans on all PRs
- Automated documentation generation"
```

---

## Troubleshooting

### "Python not found"

**Solution:** Install Python 3.9+ from [python.org](https://python.org)

### "Claude command not found"

**Solution:** Install Claude Code from [claude.ai/claude-code](https://claude.ai/claude-code)

### "No .claude directory found"

**Solution:** The tool creates it automatically. If you see this warning, it just means you're creating a new setup (this is normal).

### "Skill already installed"

**Solution:** Use `--force` flag to overwrite:
```bash
python tools/install_skill.py --skill plan-before-code --destination ../my-project --force
```

### "Wrong directory structure"

**Solution:** Make sure you're in the ai_templates directory when running install commands:
```bash
cd ai_templates
pwd  # Should show .../ai_templates
python tools/install_skill.py --list
```

---

## Tips & Best Practices

### Tip 1: Start with Critical Skills

Don't install all 48 skills immediately. Start with:
- `--priority CRITICAL` (3 skills)
- `init-[language]-project` (1 skill)
- `Code Review` category (6 skills)

Install more as you need them.

### Tip 2: Use the Web Browser

Visit [https://bdourthe.github.io/ai_templates/](https://bdourthe.github.io/ai_templates/) to:
- Browse all skills visually
- Read descriptions before installing
- Copy installation commands

### Tip 3: Customize CLAUDE.md

The generated CLAUDE.md is a template. Edit it to add:
- Your team's specific standards
- Project-specific conventions
- Domain knowledge
- Common bash commands

### Tip 4: Keep ai_templates Clone

Don't delete the ai_templates clone immediately. Keep it around to:
- Install additional skills later
- Update skills when new versions release
- Reference documentation

### Tip 5: Commit .claude/skills to Git

**Do this:**
```bash
git add .claude/
git commit -m "Add Claude Code skills"
```

Your team members will get the same skills when they clone the repo!

---

## Next Steps

1. **Read the skills documentation**: [Skills README](agent_prompts/autonomous_agents/claude_code/skills/README.md)
2. **Explore integrations**: [MCP Setup Guide](integrations/README.md)
3. **Set up hooks**: [Automation Hooks](hooks/README.md)
4. **Contribute**: [Contributing Guide](CONTRIBUTING.md)

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/bdourthe/ai_templates/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bdourthe/ai_templates/discussions)
- **Email**: benjamin@adonamed.com

---

**You're all set! Happy coding with Claude! 🚀**

*Quick Start Guide v1.0.0 - Part of AI Templates v0.2.7*

*Last Updated: October 21, 2025*
