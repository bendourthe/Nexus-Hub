# Content Guide: Writing Skills and Commands for DevAI-Hub

This guide explains how to write high-quality skills and slash commands for the DevAI-Hub catalog. Follow these conventions to ensure your content integrates cleanly with the installer, the skills catalog, and the skill search command.

---

## Content Types

| Type | Entry File | Purpose | Size |
|------|-----------|---------|------|
| **Skill** | `SKILL.md` | Behavioral instruction — tells the AI *how* to behave in a context | Ideally < 300 lines; use reference files for large skills |
| **Command** | `<name>.md` | User-invoked slash command — defines a structured multi-step workflow | Any length; organize into numbered phases |

---

## Skill Format

### Directory structure

Every skill lives in its own directory inside a category:

```
catalog/skills/<category>/<skill-name>/
├── SKILL.md          ← required: entry point
└── agents/           ← optional: multi-agent sub-skill files
    ├── researcher.md
    └── implementer.md
```

For large skills (entry point > 300 lines), move detailed reference material into a `references/` sub-directory and link to it from `SKILL.md`:

```
catalog/skills/<category>/<skill-name>/
├── SKILL.md                    ← concise entry point (< 300 lines)
└── references/
    ├── detailed-patterns.md    ← fetched on demand
    └── examples.md
```

This keeps the skill discoverable without bloating the agent's context window every time the skill triggers.

### SKILL.md frontmatter

Every `SKILL.md` must begin with YAML frontmatter:

```yaml
---
name: human-readable-skill-name
description: >
  One or two sentences describing when this skill activates and what it does.
  Written from the agent's perspective: "Use this skill when..."
agents:
  - name: agent-role
    description: What this agent's job is within the skill
---
```

Required fields: `name`, `description`.
Optional fields: `agents` (list of agent roles used inside the skill).

### SKILL.md body structure

```markdown
# Skill Title

One-sentence statement of what this skill does.

## When to Use This Skill

Describe the trigger conditions. What user request or context causes this skill to activate?

## Step 1 — [Action Name]

Concrete instructions for the first step. Use code blocks for commands or output examples.

## Step 2 — [Action Name]

...

## Output Format

Describe the expected output format, if applicable.

## Notes

- Any caveats, edge cases, or constraints.
- Reference files: [detailed-patterns.md](references/detailed-patterns.md) — load if you need more depth on X.
```

### Writing effective skill content

**Do:**
- Write in second person ("You will...", "Ask the user...")
- Use numbered steps for sequential actions
- Include concrete examples with code blocks
- Keep the entry point ≤ 300 lines; move deep reference material to `references/`
- State when the skill is NOT appropriate (prevents misfire)

**Do not:**
- Include language-specific content that should be language-agnostic
- Duplicate content already in another skill — reference it instead
- Write in first person from the user's perspective

---

## Command Format

### File location

```
catalog/commands/<command-name>.md
```

The command name must match the slash command the user invokes: `/command-name`.

### Command frontmatter

```yaml
---
description: One-sentence description shown in the command picker.
---
```

### Command body structure

```markdown
# Command Title

Brief description of what this command does and when to use it.

## Steps

### Step 1 — [Phase Name]

Instructions for this phase.

### Step 2 — [Phase Name]

...

## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times**:

1. **Analyze**: Review the generated output.
2. **Refine**: Fix any issues found.
3. **Stop**: If you are confident the result is excellent, or if you have reached the maximum iteration count.
```

---

## Category Reference

Place new skills in the most specific matching category. If none fits, contact a maintainer before creating a new category.

| Category | Skill Types |
|---|---|
| `ai-development` | AI agents, prompt engineering, RAG |
| `architecture` | System design, API design, DDD, microservices |
| `bug-fixing` | Bug localization, patch generation, root cause analysis |
| `code-cleanup` | Language-specific cleanup and formatting |
| `code-review` | Multi-phase review (security, performance, quality, testing) |
| `compliance` | Regulatory frameworks (SOC2, GDPR, ISO, NIST, PCI-DSS) |
| `developer-experience` | Refactoring, tech debt, legacy code, code translation |
| `documentation` | Technical docs, API docs, docstrings, SBOM |
| `framework-specialists` | React, Next.js, FastAPI, etc. |
| `infrastructure` | CI/CD, cloud, Kubernetes, Terraform, databases |
| `language-specialists` | Go, Rust, SQL, etc. |
| `orchestration` | Context management, token optimization, multi-agent coordination |
| `project-initialization` | Project scaffolding by language |
| `research` | Trend research, competitive analysis |
| `security` | Dependency audit, CVE analysis, authentication patterns |
| `testing` | Unit, integration, E2E, mutation, property-based, fuzzing |
| `workflow` | Development workflow patterns (commit, debug, TDD, etc.) |

---

## Naming Conventions

- **Directory names**: `kebab-case` (e.g., `code-review-security`, `unit-tests`)
- **Skill names in frontmatter**: `kebab-case` matching the directory name
- **Command file names**: `kebab-case` matching the slash command name
- **Category directories**: `kebab-case` (e.g., `code-review`, `developer-experience`)

---

## Adding a Skill to the Catalog

After placing your `SKILL.md` in the correct directory, run the catalog builder to update `skills.json`:

```bash
python tools/build_skills_catalog.py
```

Or let the pre-commit hook rebuild it automatically on your next commit. The CI workflow will validate the resulting `skills.json` on every PR.

---

## Progressive Disclosure Pattern

For large skills (entry point would exceed ~300 lines), apply progressive disclosure:

1. Keep `SKILL.md` to a concise overview: purpose, trigger conditions, key steps (< 300 lines total).
2. Move detailed reference material (exhaustive examples, edge case tables, long configuration blocks) into `references/<topic>.md`.
3. Link to reference files at the end of the relevant step in `SKILL.md`:

```markdown
## Step 3 — Configure the Pipeline

Set up the pipeline with the following structure. For full configuration options, see [references/pipeline-config.md](references/pipeline-config.md).
```

This pattern ensures the skill is always fast to load while keeping comprehensive documentation accessible on demand.

---

## Submission Checklist

Before opening a PR:

- [ ] `SKILL.md` has valid YAML frontmatter (`name`, `description`)
- [ ] Entry point is ≤ 300 lines (or uses `references/` for overflow)
- [ ] Skill is placed in the correct category directory
- [ ] `pre-commit run --all-files` passes locally
- [ ] Skill has been manually tested in Claude Code
- [ ] Command (if applicable) has been run end-to-end
