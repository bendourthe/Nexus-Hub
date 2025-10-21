# Claude Code Skills

This directory contains specialized Claude Code skills that provide task-specific expertise based on the comprehensive templates available in this repository.

## What are Claude Skills?

Claude Skills are markdown files (SKILL.md) that tell Claude how to perform specific tasks. Each skill includes:
- **YAML frontmatter** with skill metadata (name, description, version)
- **Detailed instructions** for completing the task
- **Optional resources** like scripts, templates, or data files

Skills are token-efficient: only a short description is loaded initially, with full details loaded when needed.

## Available Skills

### System Prompt Configuration Skills
| Skill | Description | Languages |
|-------|-------------|-----------|
| [setup-python-system-prompt](setup-python-system-prompt/) | Configure comprehensive Python development system prompt | Python |
| [setup-javascript-system-prompt](setup-javascript-system-prompt/) | Configure comprehensive JavaScript/TypeScript system prompt | JavaScript, TypeScript |
| [setup-java-system-prompt](setup-java-system-prompt/) | Configure comprehensive Java development system prompt | Java |
| [setup-csharp-system-prompt](setup-csharp-system-prompt/) | Configure comprehensive C# development system prompt | C# |
| [setup-go-system-prompt](setup-go-system-prompt/) | Configure comprehensive Go development system prompt | Go |
| [setup-c-system-prompt](setup-c-system-prompt/) | Configure comprehensive C development system prompt | C |
| [setup-cpp-system-prompt](setup-cpp-system-prompt/) | Configure comprehensive C++ development system prompt | C++ |

### Code Review Skills
| Skill | Description | Languages |
|-------|-------------|-----------|
| [code-review-context-analysis](code-review-context-analysis/) | Analyze project context and understand codebase structure | All 7 languages |
| [code-review-quality](code-review-quality/) | Review code quality, style, and maintainability | All 7 languages |
| [code-review-security](code-review-security/) | Perform comprehensive security vulnerability assessment | All 7 languages |
| [code-review-performance](code-review-performance/) | Analyze performance bottlenecks and optimization opportunities | All 7 languages |
| [code-review-testing](code-review-testing/) | Evaluate test coverage and quality | All 7 languages |
| [code-review-final-report](code-review-final-report/) | Generate consolidated code review report | All 7 languages |

### Code Cleanup Skills
| Skill | Description | Languages |
|-------|-------------|-----------|
| [cleanup-python](cleanup-python/) | Remove dead code, consolidate duplicates, modernize Python code | Python |
| [cleanup-javascript](cleanup-javascript/) | Clean up unused imports, modernize to ES6+, optimize JavaScript/TypeScript | JavaScript, TypeScript |
| [cleanup-java](cleanup-java/) | Remove unused code, modernize to streams/lambdas, clean Java projects | Java |
| [cleanup-csharp](cleanup-csharp/) | Clean unused usings, apply modern C# features, optimize .NET code | C# |
| [cleanup-go](cleanup-go/) | Apply idiomatic Go patterns, remove debug statements, clean Go modules | Go |
| [cleanup-c](cleanup-c/) | Detect memory leaks, apply MISRA-C/CERT-C, clean embedded C code | C |
| [cleanup-cpp](cleanup-cpp/) | Modernize to modern C++, apply RAII, use smart pointers | C++ |

### Documentation Skills
| Skill | Description | Languages |
|-------|-------------|-----------|
| [generate-docstrings](generate-docstrings/) | Generate comprehensive docstrings for all public interfaces | All 7 languages |
| [add-strategic-comments](add-strategic-comments/) | Add strategic comments explaining complex logic | All 7 languages |
| [create-user-documentation](create-user-documentation/) | Generate README, installation guides, tutorials | All 7 languages |
| [create-technical-docs](create-technical-docs/) | Document architecture, ADRs, design decisions | All 7 languages |
| [generate-api-docs](generate-api-docs/) | Create complete API reference documentation | All 7 languages |
| [generate-sbom](generate-sbom/) | Generate Software Bill of Materials for compliance | All 7 languages |

### Test Development Skills
| Skill | Description | Languages |
|-------|-------------|-----------|
| [setup-test-infrastructure](setup-test-infrastructure/) | Establish test frameworks and directory structure | All 7 languages |
| [generate-test-cases](generate-test-cases/) | Create comprehensive unit, integration, and e2e tests | All 7 languages |
| [create-mocks-fixtures](create-mocks-fixtures/) | Implement mocking strategies and test data factories | All 7 languages |
| [performance-testing](performance-testing/) | Create load tests, stress tests, and benchmarks | All 7 languages |
| [setup-ci-cd-testing](setup-ci-cd-testing/) | Integrate tests into CI/CD with quality gates | All 7 languages |
| [analyze-code-coverage](analyze-code-coverage/) | Analyze coverage gaps and achieve 80%+ target | All 7 languages |

## How to Use Claude Skills

### Method 1: Automatic Detection
Claude Code automatically scans for skills in the `.claude/skills/` directory of your project. Place any skill directory there, and Claude will detect it.

### Method 2: Direct Invocation
Use the skill name directly in conversation:
```
"Use the code-review-security skill to analyze this codebase"
```

### Method 3: Copy to Project
Copy any skill directory from this repository to your project's `.claude/skills/` directory:
```bash
cp -r agent_prompts/autonomous_agents/claude_code/skills/code-review-security .claude/skills/
```

## Skill Structure

Each skill follows this structure:
```
skill-name/
├── SKILL.md           # Main skill file with YAML frontmatter and instructions
└── resources/         # Optional: templates, scripts, data files
    ├── template.md
    └── helper.py
```

## Supported Languages

All skills support 7 programming languages:
- **Python** - General-purpose, data science, web development
- **JavaScript/TypeScript** - Web, Node.js, React, Angular, Vue
- **Java** - Enterprise, Spring Boot, Android
- **C#** - .NET, ASP.NET Core, Unity
- **Go** - Microservices, cloud-native applications
- **C** - Embedded systems, firmware, RTOS
- **C++** - Performance-critical, embedded, modern C++

## Creating Custom Skills

You can create custom skills based on this repository's templates:

1. **Create skill directory**: `mkdir -p .claude/skills/my-skill`
2. **Create SKILL.md** with YAML frontmatter:
```yaml
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
author: Your Name
---
```
3. **Add instructions**: Write detailed markdown instructions
4. **Optional resources**: Add supporting files to `resources/` subdirectory

## Benefits of Using Skills

- **Token Efficiency**: Only brief descriptions loaded initially
- **Reusability**: Use same skill across multiple projects
- **Consistency**: Standardized approaches to common tasks
- **Specialization**: Each skill focuses on one specific task
- **Composability**: Combine skills for complex workflows

## Version History

- **v1.0.0** (October 2025): Initial skill collection with 29 skills across 7 languages

---

*Based on ai_templates repository v0.2.5*
*Last Updated: October 2025*
