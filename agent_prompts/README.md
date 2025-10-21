# AI Agent Prompts for Agentic Coding

This directory contains standardized system prompts (also known as Rules or Instructions) and **Claude Code Skills** specifically engineered for agentic coding across different AI platforms. These resources ensure consistent, high-quality code generation and maintain organizational software development standards.

## 🆕 Claude Code Skills Framework

**NEW**: 6 production-ready skills for autonomous agentic coding workflows!

Skills provide task-specific expertise with token-efficient loading and natural language invocation.

**[→ View All Skills Documentation](autonomous_agents/claude_code/skills/README.md)**

### Quick Start
```
"Use the plan-before-code skill to design this feature"
"Use the init-python-project skill to create 'my-app'"
"Use the create-claude-md skill to configure this project"
```

### Available Skills
- `plan-before-code` 🔥 - Anthropic's #1 best practice workflow
- `create-claude-md` 🔥 - Generate CLAUDE.md configuration
- `init-python-project` - Initialize complete Python projects
- `setup-python-system-prompt` - Configure Python standards
- `cleanup-python` - Modernize Python codebases
- `generate-api-docs` - Generate API documentation

**[Complete Skills Documentation →](autonomous_agents/claude_code/skills/)**

## 📁 Repository Structure

```
agent_prompts/
├── autonomous_agents/                          # Prompts for autonomous coding agents
│   └── claude_code/
│       ├── skills/                            # ← NEW: Claude Code Skills
│       │   ├── README.md                      #   Complete skills documentation
│       │   ├── plan-before-code/             #   🔥 Anthropic best practice
│       │   ├── create-claude-md/             #   🔥 CLAUDE.md generator
│       │   ├── init-python-project/          #   Project initialization
│       │   ├── setup-python-system-prompt/   #   Python standards
│       │   ├── cleanup-python/               #   Code modernization
│       │   └── generate-api-docs/            #   API documentation
│       ├── python/
│       │   ├── CLAUDE_comprehensive_40k.md     # Full-featured prompt (~40k tokens)
│       │   └── CLAUDE_condensed_20k.md         # Streamlined version (~20k tokens)
│       ├── javascript/
│       │   ├── CLAUDE_comprehensive_35k.md
│       │   └── CLAUDE_condensed_20k.md
│       ├── java/
│       │   ├── CLAUDE_comprehensive_35k.md
│       │   └── CLAUDE_condensed_20k.md
│       ├── csharp/
│       │   ├── CLAUDE_comprehensive_35k.md
│       │   └── CLAUDE_condensed_20k.md
│       ├── go/
│       │   ├── CLAUDE_comprehensive_35k.md
│       │   └── CLAUDE_condensed_20k.md
│       ├── c/
│       │   ├── CLAUDE_comprehensive_35k.md
│       │   └── CLAUDE_condensed_20k.md
│       └── cpp/
│           ├── CLAUDE_comprehensive_35k.md
│           └── CLAUDE_condensed_20k.md
├── coding_assistants/                          # Prompts for coding assistants
│   ├── python/
│   │   ├── GLOBAL_comprehensive_35k.md         # Full-featured prompt (~35k tokens)
│   │   └── GLOBAL_condensed_15k.md             # Lightweight version (~15k tokens)
│   ├── javascript/
│   │   ├── GLOBAL_comprehensive_35k.md
│   │   └── GLOBAL_condensed_15k.md
│   ├── java/
│   │   ├── GLOBAL_comprehensive_35k.md
│   │   └── GLOBAL_condensed_15k.md
│   ├── csharp/
│   │   ├── GLOBAL_comprehensive_35k.md
│   │   └── GLOBAL_condensed_15k.md
│   ├── go/
│   │   ├── GLOBAL_comprehensive_35k.md
│   │   └── GLOBAL_condensed_15k.md
│   ├── c/
│   │   ├── GLOBAL_comprehensive_35k.md
│   │   └── GLOBAL_condensed_15k.md
│   └── cpp/
│       ├── GLOBAL_comprehensive_35k.md
│       └── GLOBAL_condensed_15k.md
├── GLOBAL_generalized_system_prompt_15k.md     # General-purpose assistants (non-coding, ~15k tokens)
└── README.md                                   # This file
```

### 📊 Available Language Templates

#### Autonomous Agents (Claude Code)

| Language | Comprehensive | Condensed | Token Count |
|----------|--------------|-----------|-------------|
| **Python** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/python/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/python/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **JavaScript** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/javascript/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/javascript/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **Java** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/java/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/java/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **C#** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/csharp/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/csharp/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **Go** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/go/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/go/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **C** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/c/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/c/CLAUDE_condensed_20k.md) | ~35k / ~20k |
| **C++** | [CLAUDE_comprehensive_35k.md](autonomous_agents/claude_code/cpp/CLAUDE_comprehensive_35k.md) | [CLAUDE_condensed_20k.md](autonomous_agents/claude_code/cpp/CLAUDE_condensed_20k.md) | ~35k / ~20k |

#### Coding Assistants (General Purpose)

| Language | Comprehensive | Condensed | Token Count |
|----------|--------------|-----------|-------------|
| **Python** | [GLOBAL_comprehensive_35k.md](coding_assistants/python/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/python/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **JavaScript** | [GLOBAL_comprehensive_35k.md](coding_assistants/javascript/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/javascript/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **Java** | [GLOBAL_comprehensive_35k.md](coding_assistants/java/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/java/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **C#** | [GLOBAL_comprehensive_35k.md](coding_assistants/csharp/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/csharp/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **Go** | [GLOBAL_comprehensive_35k.md](coding_assistants/go/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/go/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **C** | [GLOBAL_comprehensive_35k.md](coding_assistants/c/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/c/GLOBAL_condensed_15k.md) | ~35k / ~15k |
| **C++** | [GLOBAL_comprehensive_35k.md](coding_assistants/cpp/GLOBAL_comprehensive_35k.md) | [GLOBAL_condensed_15k.md](coding_assistants/cpp/GLOBAL_condensed_15k.md) | ~35k / ~15k |

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

1. **Via VS Code Settings**:
   - Open VS Code settings (`Ctrl+,` or `Cmd+,`)
   - Search for "copilot instructions"
   - Add the content from `coding_assistants/python/GLOBAL_comprehensive_35k.md`

2. **Via Copilot Chat**:
   - Open Copilot Chat panel
   - Use the `/` command followed by your custom instructions
   - Reference the appropriate prompt file for your project

### Cursor

1. **Global Settings**:
   - Go to File > Preferences > Cursor Settings
   - Click on "Rules & Memories" tab on the left panel
   - Click on "User Rules"
   - Paste content from `coding_assistants/python/GLOBAL_comprehensive_35k.md`

2. **Project-Specific**:
   - Create a `.cursorrules` file in your project root
   - Copy the appropriate prompt content into this file

### Windsurf

1. **Global Rules Setup**:
   - Open Cascade chat on the right side of the interface
   - Click the Customizations icon in the top right corner of Cascade
   - Navigate to Customizations > Rules
   - Click "Edit global_windsurf.md"
   - Paste content from `coding_assistants/python/GLOBAL_comprehensive_35k.md`

2. **Per-Session Setup**:
   - Start a new coding session
   - Load the appropriate prompt file as context
   - Reference throughout your session

### Claude Code (Autonomous Agent)

1. **Direct Integration**:
   ```bash
   claude config set system-prompt path/to/CLAUDE_comprehensive_35k.md
   ```

2. **Session-Based**:
   ```bash
   claude --system-prompt ./autonomous_agents/claude_code/python/CLAUDE_comprehensive_35k.md
   ```

### Codex CLI

1. **Configuration File**:
   - Create or edit `~/.codex/config.yaml`
   - Add system prompt reference:
   ```yaml
   system_prompt_file: "path/to/autonomous_agents/claude_code/python/CLAUDE_comprehensive_35k.md"
   ```

2. **Command Line**:
   ```bash
   codex --system-prompt ./autonomous_agents/claude_code/python/CLAUDE_comprehensive_35k.md
   ```

### GitHub Copilot CLI

1. **Environment Variable**:
   ```bash
   export COPILOT_SYSTEM_PROMPT="$(cat ./coding_assistants/python/GLOBAL_comprehensive_35k.md)"
   gh copilot suggest
   ```

2. **Config File**:
   - Create `~/.github-copilot/config.yml`
   - Add system prompt path reference

## 📊 Prompt Versions

### Comprehensive Versions (~35k tokens)
- **Best for**: Complex projects, enterprise development, full-stack applications
- **Features**: Complete architectural guidance, extensive best practices, detailed error handling
- **Use when**: Maximum code quality and consistency is required

### Condensed Versions (15k-20k tokens)
- **Best for**: Quick development, prototyping, smaller projects
- **Features**: Essential guidelines, core best practices, streamlined workflow
- **Use when**: Token efficiency is important or working within limits
- **General-purpose option**: `GLOBAL_generalized_system_prompt_15k.md` delivers broad guidance for assistants that are not dedicated to coding tasks.

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

*Last Updated: September 2025*