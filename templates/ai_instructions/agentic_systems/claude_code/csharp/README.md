# C# Project Template for Claude Code

A complete, modular template for C#/.NET projects using Claude Code with optimized instruction loading.

## Quick Start

1. **Copy this directory** to your project root
2. **Start Claude Code** and run the setup wizard
3. **Optionally** update `.claude/context/architecture.md` with your architecture

```bash
# Copy the template
cp -r csharp/* your-project/

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
csharp/
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
│   │   └── development/                # Development workflow skills
│   │       ├── workflow-methodology/   # Task breakdown & iterative testing
│   │       └── implementation-patterns/ # Response patterns & decision trees
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

## Skills Auto-Activation

Skills are loaded **only when relevant** based on your request:

| Your Request | Skills Activated |
|--------------|------------------|
| "Create a new ASP.NET Core project" | `project-setup` (if added) |
| "Fix this method" | `interaction-principles`, `code-standards` |
| "Write tests for this" | `testing-framework`, `workflow-methodology` |
| "Update the version" | `version-control` |
| "Review this code" | `quality-checklist`, `implementation-patterns` |

## Adding Language-Specific Skills

To add C#-specific skills, create:

```
.claude/skills/csharp/
├── project-setup/SKILL.md        # .NET project structure, .csproj
├── code-standards/SKILL.md       # C# conventions, StyleCop
├── testing-framework/SKILL.md    # xUnit/NUnit, Moq configuration
└── command-preferences/SKILL.md  # dotnet CLI commands
```

## Token Efficiency

| Approach | Tokens/Conversation |
|----------|---------------------|
| Comprehensive CLAUDE.md | ~40,000 |
| This modular template | ~4,000-8,000 |

**~80% reduction** in token consumption.

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

## Version

- **Template Version**: 1.0.0
- **Last Updated**: December 2025
