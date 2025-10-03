# AI Prompts for Agentic Coding

This repository contains standardized system prompts (also known as Rules or Instructions) specifically engineered for agentic coding across different AI platforms. These prompts ensure consistent, high-quality code generation and maintain organizational software development standards.

## 📁 Repository Structure

```
ai_prompts/
├── autonomous_agents/          # Prompts for autonomous coding agents
│   └── claude_code/
│       └── python/
│           ├── CLAUDE_comprehensive_35k.md    # Full-featured prompt (~35k tokens)
│           └── CLAUDE_condensed_20k.md       # Streamlined version (~20k tokens)
├── coding_assistants/          # Prompts for coding assistants
│   └── python/
│       ├── GLOBAL_comprehensive_35k.md       # Full-featured prompt (~35k tokens)
│       └── GLOBAL_condensed_15k.md          # Lightweight version (~15k tokens)
└── README.md                   # This file
```

## 🎯 Purpose

Having standardized and version-controlled prompts helps ensure that your organization's software development:
- **Maintains consistency** across all AI-assisted coding sessions
- **Follows well-established guidelines** and best practices
- **Maximizes code quality** and reliability
- **Reduces technical debt** through consistent patterns
- **Improves team collaboration** with shared coding standards

## 🤖 Platform Setup Instructions

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