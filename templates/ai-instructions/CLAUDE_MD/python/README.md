# Python Project Template for Claude Code

A complete, modular template for Python projects using Claude Code with optimized instruction loading.

## Quick Start

1. **Copy this directory** to your project root
2. **Start Claude Code** and run the setup wizard
3. **Optionally** update `.claude/context/architecture.md` with your architecture

```bash
# Copy the template
cp -r python/* your-project/

# Navigate and start
cd your-project
claude
```

Then run the interactive setup wizard:
```
/setup-project
```

This will guide you through 5 questions and generate a polished project description for your `CLAUDE.md`.

## Directory Structure

```
python/
├── CLAUDE.md                           # Minimal core instructions (~60 lines)
│
├── .claude/
│   ├── skills/                         # Auto-activated capabilities
│   │   ├── core/                       # Universal skills
│   │   │   ├── interaction-principles/ # How Claude communicates
│   │   │   └── quality-checklist/      # Pre-delivery checks
│   │   │
│   │   ├── governance/                 # Governance skills
│   │   │   ├── documentation-standards/ # Doc templates
│   │   │   └── version-control/        # Git and versioning rules
│   │   │
│   │   ├── development/                # Development workflow skills
│   │   │   ├── workflow-methodology/   # Task breakdown & iterative testing
│   │   │   └── implementation-patterns/ # Response patterns & decision trees
│   │   │
│   │   └── python/                     # Python-specific skills
│   │       ├── project-setup/          # Directory structure, pyproject.toml
│   │       ├── code-standards/         # Import organization, formatting
│   │       ├── testing-framework/      # Test structure, output formatting
│   │       └── command-preferences/    # PowerShell syntax, venv management
│   │
│   ├── context/                        # Project-specific reference docs
│   │   └── architecture.md             # System architecture
│   │
│   ├── commands/                       # User-invoked slash commands
│   │   ├── setup-project.md            # /setup-project - Configure CLAUDE.md
│   │   ├── import-skills.md            # /import-skills - Import from catalog
│   │   ├── update-documentation.md     # /update-documentation - Doc audit
│   │   └── upgrade-version.md          # /upgrade-version - Version upgrade
│   │
│   └── memory/                         # Persistent project knowledge
│       └── decisions.md                # Architecture Decision Records
│
└── legacy/                             # Legacy monolithic templates
    ├── CLAUDE_comprehensive_40k.md     # Full legacy format
    └── CLAUDE_condensed_20k.md         # Condensed legacy format
```

## How It Works

### Skills Auto-Activation

Skills are loaded **only when relevant** based on your request:

| Your Request | Skills Activated |
|--------------|------------------|
| "Create a new Python project" | `python/project-setup` |
| "Fix this function" | `core/interaction-principles`, `python/code-standards` |
| "Write tests for this" | `python/testing-framework`, `development/workflow-methodology` |
| "Update the version" | `governance/version-control` |
| "Review this code" | `core/quality-checklist`, `development/implementation-patterns` |

### Token Efficiency

| Approach | Tokens/Conversation |
|----------|---------------------|
| Comprehensive CLAUDE.md | ~40,000 |
| This modular template | ~4,000-8,000 |

**~80% reduction** in token consumption with **better instruction adherence**.

## Customization

### Updating CLAUDE.md

Edit the placeholder values in `CLAUDE.md`:
- `[Your Project Name]` → Your actual project name
- `[2-3 sentence description]` → Project description
- Adjust tech stack as needed

### Adding Project Context

Update `.claude/context/architecture.md` with:
- System architecture overview
- Component descriptions
- Data flow diagrams
- Design decisions

### Recording Decisions

Use `.claude/memory/decisions.md` to track:
- Architecture Decision Records (ADRs)
- Pattern decisions
- Technical trade-offs

## Skills Reference

### Core Skills (Universal)
- **interaction-principles**: Clarification protocol, teaching approach, critical analysis
- **quality-checklist**: Pre-delivery checks for code and projects

### Governance Skills (Universal)
- **documentation-standards**: Docstring templates, README/CHANGELOG/DEVLOG structure
- **version-control**: Semantic versioning, Git operation restrictions

### Development Skills (Universal)
- **workflow-methodology**: Task breakdown, iterative testing protocol
- **implementation-patterns**: Response patterns, decision trees

### Python Skills (Language-Specific)
- **project-setup**: Directory structure, pyproject.toml, uv/ruff toolchain
- **code-standards**: Import organization, formatting, naming conventions
- **testing-framework**: Test structure, output formatting, pytest config
- **command-preferences**: PowerShell syntax, virtual environment management

## Legacy Files

The `legacy/` directory contains the original monolithic templates:
- `CLAUDE_comprehensive_40k.md` - Full 1,858-line legacy format
- `CLAUDE_condensed_20k.md` - Condensed legacy format

These are preserved for backward compatibility but superseded by the skills-based architecture.

## Available Slash Commands

Each template includes pre-configured slash commands:

| Command | Description |
|---------|-------------|
| `/setup-project` | Interactive wizard to configure CLAUDE.md with project name, description, features, and target users |
| `/import-skills` | Import skills from the ai-templates catalog (select all, by category, or specific skills) |
| `/update-documentation` | 8-step documentation consistency audit (checks links, versions, structure, deprecated references) |
| `/upgrade-version` | 11-step semantic version upgrade assistant (updates all version references across files) |

### How Commands Become Available

**Commands work automatically** after copying the template:

1. **Copy template** → `.claude/commands/*.md` files are included
2. **Open VS Code** with Claude Code extension (or run `claude` in terminal)
3. **Type `/command-name`** → Claude Code discovers and executes commands

Commands are markdown files in `.claude/commands/` that Claude Code auto-discovers. Each `.md` file becomes a `/command-name` slash command.

## Related Resources

- [Claude Code Project Setup Guide](../../../../guides/CLAUDE_CODE_PROJECT_SETUP.md)
- [Claude Code Guide](../../../../guides/CLAUDE_CODE_GUIDE.md)
- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

## Version

- **Template Version**: 1.0.0
- **Last Updated**: December 2025
- **Based on**: CLAUDE_comprehensive_40k.md (all 10 sections preserved)
