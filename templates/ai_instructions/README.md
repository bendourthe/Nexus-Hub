# AI Agent Prompts for Agentic Coding

This directory contains standardized system prompts (also known as Rules or Instructions) and **Claude Code Skills** specifically engineered for agentic coding across different AI platforms. These resources ensure consistent, high-quality code generation and maintain organizational software development standards.

## 🆕 Claude Code Skills Framework

**60 production-ready skills** for autonomous agentic coding workflows!

Skills provide task-specific expertise with token-efficient loading and natural language invocation.

**[→ View All Skills](../../catalogs/claude_skills/)**

### Quick Start
```
"Use the plan-before-code skill to design this feature"
"Use the init-python-project skill to create 'my-app'"
"Generate unit tests for my authentication module"
```

### Skill Categories
- **Workflow** - plan-before-code, test-driven-development, code-commit-workflow
- **Code Review** - security review, performance review, quality analysis
- **Tests Generation** - unit tests, integration tests, mutation testing
- **Documentation** - API docs, docstrings, user documentation
- **Code Cleanup** - Python, JavaScript, Java, C#, Go, C, C++
- **Compliance** - SOC 2, ISO 27001, GDPR, AI governance
- **Project Setup** - Python, JavaScript, Java, C# project initialization
- **Security** - dependency audits, licensing compliance

**[Complete Skills Catalog →](../../catalogs/claude_skills/)**

## 📁 Repository Structure

```
ai_instructions/
├── agentic_systems/                            # Prompts for autonomous coding agents
│   └── claude_code/
│       ├── python/                            # Modular skills-based templates
│       │   ├── CLAUDE.md                      # Core instructions (~60 lines)
│       │   ├── .claude/skills/                # Auto-activated skills
│       │   └── legacy/                        # Legacy monolithic templates
│       ├── javascript/                        # JavaScript/TypeScript templates
│       ├── java/                              # Java/Spring Boot templates
│       ├── csharp/                            # C#/.NET templates
│       ├── go/                                # Go templates
│       ├── c/                                 # C templates
│       └── cpp/                               # C++ templates
├── coding_assistants/                          # Prompts for coding assistants (GitHub Copilot)
│   ├── python/
│   │   └── copilot-instructions.md             # Consolidated template (~20k characters)
│   ├── javascript/
│   │   └── copilot-instructions.md
│   ├── java/
│   │   └── copilot-instructions.md
│   ├── csharp/
│   │   └── copilot-instructions.md
│   ├── go/
│   │   └── copilot-instructions.md
│   ├── c/
│   │   └── copilot-instructions.md
│   └── cpp/
│       └── copilot-instructions.md
├── GLOBAL_generalized_system_prompt_15k.md     # General-purpose assistants (non-coding, ~15k tokens)
└── README.md                                   # This file
```

### 📊 Available Language Templates

#### Autonomous Agents (Claude Code)

| Language | Template | Token Efficiency |
|----------|----------|------------------|
| **Python** | [python/](agentic_systems/claude_code/python/) | ~4k-8k (skills-based) |
| **JavaScript** | [javascript/](agentic_systems/claude_code/javascript/) | ~4k-8k (skills-based) |
| **Java** | [java/](agentic_systems/claude_code/java/) | ~4k-8k (skills-based) |
| **C#** | [csharp/](agentic_systems/claude_code/csharp/) | ~4k-8k (skills-based) |
| **Go** | [go/](agentic_systems/claude_code/go/) | ~4k-8k (skills-based) |
| **C** | [c/](agentic_systems/claude_code/c/) | ~4k-8k (skills-based) |
| **C++** | [cpp/](agentic_systems/claude_code/cpp/) | ~4k-8k (skills-based) |

> **Note**: Legacy monolithic templates (40k comprehensive, 20k condensed) available in each language's `legacy/` directory.

#### Coding Assistants (GitHub Copilot)

| Language | Instructions |
|----------|-------------|
| **Python** | [copilot-instructions.md](coding_assistants/python/copilot-instructions.md) |
| **JavaScript** | [copilot-instructions.md](coding_assistants/javascript/copilot-instructions.md) |
| **Java** | [copilot-instructions.md](coding_assistants/java/copilot-instructions.md) |
| **C#** | [copilot-instructions.md](coding_assistants/csharp/copilot-instructions.md) |
| **Go** | [copilot-instructions.md](coding_assistants/go/copilot-instructions.md) |
| **C** | [copilot-instructions.md](coding_assistants/c/copilot-instructions.md) |
| **C++** | [copilot-instructions.md](coding_assistants/cpp/copilot-instructions.md) |

> **One consolidated template per language** (~20k characters) covering project setup, code standards, testing, and documentation.

## 🎯 Purpose

Having standardized and version-controlled prompts helps ensure that your organization's software development:

- **Maintains consistency** across all AI-assisted coding sessions

- **Follows well-established guidelines** and best practices

- **Maximizes code quality** and reliability

- **Reduces technical debt** through consistent patterns

- **Improves team collaboration** with shared coding standards

## 🤖 Platform Setup Instructions

### Generalized AI Assistants (Multimodal / Non-Coding)
- Use `GLOBAL_generalized_system_prompt_15k.md` when you need consistent guidance for task-oriented assistants that are not tied to software development or a specific programming language.

- Paste the instructions into the assistant's system prompt area (e.g., "Custom Instructions," "Rules," or "Profile" fields) before starting a session.

- Combine with domain-specific briefs on a per-project basis for best results.

### GitHub Copilot

**Setup in VS Code (3 steps):**

1. Create `.github` folder in your project root

2. Create `copilot-instructions.md` file inside `.github`

3. Copy the content from your language template (e.g., `coding_assistants/python/copilot-instructions.md`)

### Claude Code (Autonomous Agent)

1. **Copy template to project:**
   ```bash
   cp -r agentic_systems/claude_code/python/* your-project/
   ```

2. **Start Claude Code and run setup wizard:**
   ```bash
   cd your-project && claude
   ```
   Then run `/setup-project` to interactively configure your project.

3. **Available slash commands:**
   | Command | Description |
   |---------|-------------|
   | `/setup-project` | Interactive wizard to configure CLAUDE.md with project details |
   | `/import-skills` | Import skills from the ai-templates catalog |
   | `/update-documentation` | 8-step documentation consistency audit |
   | `/upgrade-version` | 11-step semantic version upgrade assistant |

4. **Optional customization:**
   - Update `.claude/context/architecture.md` with architectural decisions
   - Copy additional skills from `catalogs/claude_skills/`

## 📊 Template Versions

### Coding Assistant Templates (~20k characters)
- **One template per language**: Balanced approach combining comprehensive and condensed guidance
- **Best for**: All project sizes, from quick tasks to complex development
- **Format**: `copilot-instructions.md` for GitHub Copilot auto-discovery

### Claude Code Skills-Based Templates (~4-8k per session)
- **Modular loading**: Only relevant skills loaded per task
- **Best for**: Autonomous agentic coding workflows
- **Format**: `.claude/skills/` directory structure

## 🚀 Getting Started

1. **Choose Your Platform**: Select the AI coding platform you're using

2. **Pick Your Version**: Choose between comprehensive or condensed based on your needs

3. **Follow Setup Instructions**: Use the platform-specific setup guide above

4. **Test Integration**: Run a simple coding task to verify the prompt is active

5. **Customize if Needed**: Adapt the prompts to your specific organizational requirements

## 🛠 Customization

These prompts are designed to be:

- **Modular**: Easy to adapt sections for specific needs

- **Extensible**: Add organization-specific guidelines

- **Language-Agnostic**: Core principles apply beyond Python

To customize:

1. Fork or copy the relevant prompt file

2. Modify sections specific to your organization's standards

3. Test thoroughly with your typical development workflows

4. Version control your customizations

## 📈 Benefits

Using these standardized prompts provides:

- **Consistent Code Quality**: All AI-generated code follows the same high standards

- **Reduced Review Time**: Code adheres to established patterns and practices

- **Better Documentation**: Automatic generation of clear, maintainable documentation

- **Security Awareness**: Built-in security best practices and vulnerability prevention

- **Performance Optimization**: Guidance for efficient, scalable code generation

- **Testing Standards**: Consistent approach to test-driven development

## 🔄 Version Control & Updates

- **Track Changes**: All prompt modifications are version controlled

- **Team Synchronization**: Ensure all team members use the same prompt versions

- **Continuous Improvement**: Regular updates based on evolving best practices

- **A/B Testing**: Compare different prompt versions for effectiveness

## 📝 Contributing

To contribute improvements:

1. Test changes thoroughly with your AI platform

2. Document the reasoning for modifications

3. Ensure compatibility across different use cases

4. Submit changes with clear commit messages

## 🔧 Troubleshooting

**Common Issues**:

- **Token Limits**: Use condensed versions for platforms with stricter limits

- **Platform Compatibility**: Some features may need adjustment per platform

- **Performance**: Monitor AI response quality and adjust prompt complexity as needed

**Best Practices**:

- Start with comprehensive versions, then optimize if needed

- Regularly review and update prompts based on team feedback

- Test prompts with various project types and complexities

- Maintain backup versions when making significant changes

## 📄 License

These prompts are designed for organizational use and can be customized according to your specific needs and licensing requirements.

---

*Last Updated: December 2025*