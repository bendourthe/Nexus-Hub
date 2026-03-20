# Contributing to DevAI-Hub

Thank you for your interest in contributing to DevAI-Hub. This guide explains how to add new skills, commands, hooks, and templates to the project.

## Getting Started

1. Clone the repository
2. Read [CLAUDE.md](CLAUDE.md) for project conventions and critical rules
3. Browse existing skills in [catalog/skills/](catalog/skills/) to understand the format
4. Check the [comparison reports](docs/) for adoption candidates already identified

## What You Can Contribute

| Contribution Type | Location | Format |
|---|---|---|
| **Skills** | `catalog/skills/<category>/<skill-name>/SKILL.md` | YAML frontmatter + Markdown |
| **Commands** | `catalog/commands/<command-name>.md` | YAML frontmatter + phased Markdown |
| **Hooks** | `catalog/hooks/` | Shell scripts |
| **Agents** | `catalog/agents/<agent-name>.md` | YAML frontmatter + Markdown |
| **Language Templates** | `templates/ai-instructions/` | Markdown with `{{PLACEHOLDER}}` syntax |
| **Context Templates** | `catalog/context/` | Markdown |

## Adding a New Skill

### 1. Choose the Right Category

| Category | When to Use |
|---|---|
| `language-specialists` | Deep expertise for a specific programming language |
| `framework-specialists` | Framework-specific patterns (React, FastAPI, Spring Boot) |
| `infrastructure` | Cloud, containers, CI/CD, observability, SRE |
| `orchestration` | Context management, task coordination, multi-agent workflows |
| `code-review` | Code quality, security review, performance review |
| `testing` / `tests-generation` | Test generation, coverage, mutation testing |
| `security` | Dependency audits, authentication patterns, exploit analysis |
| `compliance` | Regulatory frameworks (GDPR, SOC2, ISO27001) |
| `documentation` | API docs, technical docs, user docs, comments |
| `developer-experience` | Refactoring, legacy modernization, tooling, async patterns |
| `workflow` | Development process (TDD, commit workflow, debugging) |
| `architecture` | System design, DDD, event-driven, microservices |
| `ai-development` | AI agents, RAG, prompt engineering |
| `bug-fixing` | Bug localization, patch generation |
| `code-cleanup` | Language-specific dead code removal |
| `project-setup` | Project initialization templates |
| `business-product` | Product management, technical writing, business analysis |
| `research` | Trend research, competitive analysis |

If your skill does not fit an existing category, propose a new one in your pull request description.

### 2. Create the Skill File

Create `catalog/skills/<category>/<skill-name>/SKILL.md` with this structure:

```yaml
---
name: skill-name
description: What the skill does AND when to use it (max 1024 chars)
---
```

```markdown
# Skill Title

[One-paragraph introduction]

## When to Use This Skill

Use this skill for:

- [Use case 1]
- [Use case 2]

**Trigger phrases**: "keyword1", "keyword2", "keyword3"

## What This Skill Does

Provides expertise including:

- **Area 1**: Details
- **Area 2**: Details

## Instructions

### Step 1: [Topic]

[Explanation with code examples]

### Step 2: [Topic]

... (minimum 5 steps, target 7)

## Best Practices

- [Practice 1]
- [Practice 2]

## Common Patterns

### Pattern 1: [Name]

[Code example]

## Quality Checklist

- [ ] [Check 1]
- [ ] [Check 2]

## Related Skills

- `skill-name` - Brief description

---

**Version**: 1.0.0
**Last Updated**: [Month Year]
**Based on**: [Source, if adapted from external project]

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
```

### 3. Quality Standards

- **Depth**: Target 400-800 lines per skill. Each step should include multiple code examples.
- **Specificity**: One capability per skill. Do not create generic "do everything" skills.
- **Triggers**: Include trigger phrases in the description so Claude can auto-activate the skill.
- **Cross-references**: Link related skills in the "Related Skills" section.
- **Code examples**: Use realistic, production-quality code. Include both positive examples and anti-patterns.
- **Language**: Use professional teaching tone. Place punctuation outside quotation marks. No em-dashes.

### 4. Update the Catalog

After creating your skill:

1. Add an entry to `data/skills.json` with all required fields
2. Update `catalog/skills/README.md` if you created a new category
3. Verify the JSON is valid: `python -c "import json; json.load(open('data/skills.json'))"`

## Adding a New Command

Commands live in `catalog/commands/` as single Markdown files with YAML frontmatter. See existing commands for the format. Commands are user-invocable via slash syntax (e.g., `/command-name`).

## Commit Message Format

Follow the conventional commit format used in this repository:

```
type(scope): short description

Longer explanation if needed.
```

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`

Do not add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures.

## Pull Request Process

1. Create a branch from `main`
2. Make your changes following the standards above
3. Verify all JSON catalogs are valid
4. Submit a PR with:
   - A clear title (under 70 characters)
   - Description of what was added and why
   - If adapted from an external source, credit the source in the skill's "Based on" field

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Questions?

Open an issue or check existing [comparison reports](docs/) for context on planned additions.
