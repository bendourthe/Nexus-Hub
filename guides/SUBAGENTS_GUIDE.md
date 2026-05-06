# Subagents & Specialist Skills Guide

> **Make AI assistants work smarter, not harder** - Use the right expert for each task.

This guide helps you leverage specialist skills to get better results from Claude Code. Think of skills as domain experts you can call upon when you need deep expertise in a specific area.

---

## Quick Start (30 seconds)

### Copy a skill to your project:

```bash
# 1. Pick a skill from the catalog
# 2. Copy it to your project's .claude/skills/ folder
cp catalog/skills/infrastructure/kubernetes-expert/SKILL.md .claude/skills/
```

### Use it naturally:

```
"Help me optimize my Kubernetes deployment for high availability"
```

Claude will automatically activate `kubernetes-expert` based on keywords in your request.

---

## Table of Contents

1. [Understanding Skills](#understanding-skills)
2. [Skill Categories](#skill-categories)
3. [When to Use What](#when-to-use-what)
4. [Common Workflows](#common-workflows)
5. [Best Practices](#best-practices)
6. [FAQ](#faq)

---

## Understanding Skills

### What are Skills?

Skills are **modular instruction sets** that give Claude Code deep expertise in specific domains. Instead of a single monolithic prompt, skills load only when relevant - reducing token usage by up to 80%.

```
Traditional Approach          Skills Approach
┌─────────────────────┐       ┌─────────────────────┐
│ Giant prompt with   │       │ Base instructions   │
│ everything:         │       └──────────┬──────────┘
│ - K8s info          │                  │
│ - SQL info          │       ┌──────────┴──────────┐
│ - Go info           │       │ Activated on-demand │
│ - Terraform info    │       ├───────────┬─────────┤
│ - etc...            │       │ kubernetes│ sql     │
│                     │       │ -expert   │ -expert │
│ 50,000+ tokens      │       └───────────┴─────────┘
└─────────────────────┘       ~5,000 tokens per skill
```

### How Skills Activate

Skills have **trigger phrases** that Claude recognizes:

| Skill | Trigger Phrases |
|-------|-----------------|
| `kubernetes-expert` | "kubernetes", "k8s", "helm", "pod", "deployment" |
| `sql-expert` | "SQL", "database query", "optimize query", "index" |
| `terraform-specialist` | "terraform", "infrastructure as code", "IaC" |
| `go-expert` | "golang", "goroutine", "channel", "go interface" |

When you say *"Help me optimize my SQL query"*, Claude knows to apply the `sql-expert` skill.

### Skill Anatomy

Every skill follows the same structure:

```markdown
---
name: skill-name
description: What this skill does and when to use it
---

# Skill Name

## When to Use This Skill
[Specific scenarios]

## What This Skill Does
[Capabilities]

## Instructions
### Step 1: ...
### Step 2: ...

## Best Practices
[Guidelines]

## Quality Checklist
[Verification steps]
```

---

## Skill Categories

### Infrastructure (4 skills) - HIGH PRIORITY

For DevOps, cloud, and deployment tasks.

| Skill | Use When... | Example Request |
|-------|-------------|-----------------|
| **kubernetes-expert** | Deploying containers, managing clusters | *"Set up a HA Kubernetes deployment"* |
| **terraform-specialist** | Writing IaC, managing cloud resources | *"Create Terraform modules for AWS VPC"* |
| **cicd-architect** | Building pipelines, automating deployments | *"Design a GitHub Actions workflow"* |
| **cloud-architect** | Designing cloud solutions, multi-cloud | *"Plan a serverless architecture on AWS"* |

### Orchestration (3 skills) - USE FOR COMPLEX TASKS

For coordinating multi-step work.

| Skill | Use When... | Example Request |
|-------|-------------|-----------------|
| **task-coordinator** | Breaking down large implementations | *"Help me plan this feature implementation"* |
| **context-manager** | Working with large codebases | *"I need to understand how auth works across these 20 files"* |
| **workflow-orchestrator** | Chaining multiple operations | *"Run security review, then performance test, then deploy"* |

### Developer Experience (3 skills)

For improving code quality and managing dependencies.

| Skill | Use When... | Example Request |
|-------|-------------|-----------------|
| **refactoring-expert** | Improving code structure | *"Refactor this class to follow SOLID principles"* |
| **legacy-modernizer** | Upgrading old code/frameworks | *"Migrate from Express 4 to Express 5"* |
| **dependency-manager** | Updating packages, fixing vulnerabilities | *"Audit and upgrade my npm dependencies"* |

### Language Specialists (3 skills)

For language-specific deep expertise.

| Skill | Use When... | Example Request |
|-------|-------------|-----------------|
| **rust-expert** | Ownership, lifetimes, error handling | *"Help me fix this borrow checker error"* |
| **go-expert** | Concurrency, channels, idioms | *"Implement a worker pool with goroutines"* |
| **sql-expert** | Query optimization, schema design | *"Optimize this slow query"* |

---

## When to Use What

### Decision Flowchart

```
What are you working on?
│
├── Deployment/Infrastructure?
│   ├── Containers/K8s → kubernetes-expert
│   ├── Cloud resources → terraform-specialist / cloud-architect
│   └── CI/CD pipelines → cicd-architect
│
├── Code Quality?
│   ├── Restructuring code → refactoring-expert
│   ├── Upgrading framework → legacy-modernizer
│   └── Package updates → dependency-manager
│
├── Database?
│   └── Queries, schemas, performance → sql-expert
│
├── Language-Specific?
│   ├── Rust ownership/lifetimes → rust-expert
│   └── Go concurrency → go-expert
│
└── Complex Multi-Step Task?
    ├── Need to plan → task-coordinator
    ├── Large codebase → context-manager
    └── Chain operations → workflow-orchestrator
```

### Task Type Matrix

| Your Task | Primary Skill | Supporting Skills |
|-----------|---------------|-------------------|
| Fix a bug | `refactoring-expert` | `context-manager` |
| New feature | `task-coordinator` | language-specific |
| Refactoring | `refactoring-expert` | `legacy-modernizer` |
| Deploy to K8s | `kubernetes-expert` | `cicd-architect` |
| Optimize DB | `sql-expert` | - |
| Framework upgrade | `legacy-modernizer` | `dependency-manager` |
| Security audit | `dependency-manager` | infrastructure skills |

---

## Common Workflows

### Workflow 1: Full-Stack Feature Implementation

**Scenario**: Build a new user authentication feature.

```
Step 1: Plan (task-coordinator)
"Help me break down implementing OAuth2 login"

Step 2: Backend (sql-expert + language skill)
"Design the database schema for user sessions"
"Implement the Go authentication service"

Step 3: Infrastructure (kubernetes-expert + cicd-architect)
"Create K8s secrets for OAuth credentials"
"Add the auth service to our CI/CD pipeline"

Step 4: Review (workflow-orchestrator)
"Run security review on the auth implementation"
```

### Workflow 2: Legacy System Modernization

**Scenario**: Upgrade a Node.js app from Express 3 to Express 5.

```
Step 1: Audit (dependency-manager)
"Audit all dependencies for the Express upgrade path"

Step 2: Plan (legacy-modernizer)
"Create a migration plan from Express 3 to Express 5"

Step 3: Execute (refactoring-expert)
"Refactor middleware to Express 5 patterns"

Step 4: Verify (context-manager)
"Verify all routes still work after migration"
```

### Workflow 3: Database Performance Optimization

**Scenario**: Speed up slow queries in production.

```
Step 1: Analyze (sql-expert)
"Analyze the execution plan for this query:
SELECT * FROM orders WHERE created_at > '2024-01-01'"

Step 2: Optimize (sql-expert)
"Recommend indexes for the orders table"

Step 3: Implement (sql-expert)
"Write the migration to add the covering index"

Step 4: Verify
"Explain the new execution plan after indexing"
```

### Workflow 4: Kubernetes Deployment

**Scenario**: Deploy a microservice to production K8s.

```
Step 1: Design (kubernetes-expert)
"Design a deployment for my Python API with:
- 3 replicas minimum
- Health checks
- Resource limits
- Rolling updates"

Step 2: Security (kubernetes-expert)
"Add network policies and RBAC"

Step 3: CI/CD (cicd-architect)
"Create a GitHub Actions workflow for K8s deployment"

Step 4: Infrastructure (terraform-specialist)
"Write Terraform to provision the EKS cluster"
```

---

## Best Practices

### DO

**Be specific about your context**
```
Good: "Optimize this PostgreSQL query for a table with 10M rows"
Bad:  "Make my query faster"
```

**Mention the technology stack**
```
Good: "Help me with Go error handling using the errors package"
Bad:  "How do I handle errors"
```

**Combine skills for complex tasks**
```
Good: "First analyze the codebase (context-manager), then plan the refactoring (task-coordinator)"
```

**Use trigger phrases naturally**
```
Good: "I need to optimize my Kubernetes pod resource limits"
      (triggers kubernetes-expert automatically)
```

### DON'T

**Don't use too many skills at once**
```
Bad: "Use kubernetes-expert, terraform-specialist, cicd-architect, and sql-expert to..."
(Information overload - pick the most relevant one)
```

**Don't skip the planning step for big tasks**
```
Bad: "Just implement the entire auth system"
Good: "Help me plan the auth system first, then we'll implement step by step"
```

**Don't ignore the quality checklist**
```
Each skill has a quality checklist at the end - use it to verify your work.
```

---

## Installing Skills

### Method 1: Copy Individual Skills

```bash
# Create the skills directory in your project
mkdir -p .claude/skills

# Copy specific skills you need
cp catalog/skills/infrastructure/kubernetes-expert/SKILL.md .claude/skills/
cp catalog/skills/language-specialists/go-expert/SKILL.md .claude/skills/
```

### Method 2: Copy Entire Categories

```bash
# Copy all infrastructure skills
cp -r catalog/skills/infrastructure .claude/skills/

# Copy all orchestration skills
cp -r catalog/skills/orchestration .claude/skills/
```

### Method 3: Reference from Central Location

In your project's `CLAUDE.md`:

```markdown
## Skills Reference
See: @../ai-templates/catalog/skills/ for available skills
```

---

## FAQ

### Q: How many skills should I use at once?

**A:** Generally 1-2 primary skills per conversation. Skills are designed to be activated automatically based on context. If you need multiple domains, work through them sequentially.

### Q: Do skills work with all AI assistants?

**A:** These skills are optimized for Claude Code but follow standard markdown formatting that works with most AI coding assistants.

### Q: How do I know which skill activated?

**A:** You can ask Claude: *"Which skills are you currently using?"* or look for patterns from the skill instructions in the responses.

### Q: Can I modify skills for my project?

**A:** Yes! Copy the skill to your `.claude/skills/` directory and customize it. Add project-specific patterns, remove irrelevant sections, or adjust best practices.

### Q: What's the difference between a skill and a subagent?

**A:**
- **Skill**: Instructions that enhance Claude's responses (what you see here)
- **Subagent**: An independent AI instance with its own context window (used in multi-agent systems)

The skills in this repo can function as either - they're instructions that can guide a main assistant or be loaded into a specialized subagent.

### Q: How do orchestration skills work with other skills?

**A:** Orchestration skills help coordinate complex work:

| Orchestration Skill | How It Helps |
|---------------------|--------------|
| `task-coordinator` | Breaks work into steps, suggests which skills to use |
| `context-manager` | Maintains awareness across files, synthesizes information |
| `workflow-orchestrator` | Chains multiple skills with quality gates |

Example:
```
User: "I need to migrate from MongoDB to PostgreSQL"

task-coordinator might respond:
1. Analyze current MongoDB schema (context-manager)
2. Design PostgreSQL schema (sql-expert)
3. Write migration scripts
4. Update application code
5. Test and verify
```

---

## Skill Reference Card

Print this for quick reference:

```
┌──────────────────────────────────────────────────────────────────┐
│                    SKILLS QUICK REFERENCE                         │
├──────────────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE          │ ORCHESTRATION                          │
│ ├─ kubernetes-expert    │ ├─ task-coordinator (planning)        │
│ ├─ terraform-specialist │ ├─ context-manager (large codebases)  │
│ ├─ cicd-architect       │ └─ workflow-orchestrator (chaining)   │
│ └─ cloud-architect      │                                        │
├─────────────────────────┼────────────────────────────────────────┤
│ DEVELOPER EXPERIENCE    │ LANGUAGE SPECIALISTS                   │
│ ├─ refactoring-expert   │ ├─ rust-expert (ownership, lifetimes) │
│ ├─ legacy-modernizer    │ ├─ go-expert (concurrency, channels)  │
│ └─ dependency-manager   │ └─ sql-expert (queries, optimization) │
└──────────────────────────────────────────────────────────────────┘

TRIGGER PHRASES:
• Kubernetes: k8s, helm, pod, deployment, kubectl
• Terraform: IaC, infrastructure as code, HCL, module
• CI/CD: pipeline, GitHub Actions, GitLab CI, deploy
• SQL: query, database, index, schema, PostgreSQL/MySQL

WORKFLOW:
1. Describe your task naturally
2. Mention relevant technologies
3. Claude activates appropriate skills
4. Follow the quality checklist to verify
```

---

## Advanced: Custom Agent Configuration

Claude Code supports creating custom agents with dedicated YAML frontmatter configuration. Agents are more powerful than skills because they run as independent subprocesses with their own tool allowlists, model selection, and memory scope.

### Creating a Custom Agent

Place agent definitions in `.claude/agents/`:

```yaml
---
name: my-custom-agent
description: Short description of what this agent does
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
model: claude-sonnet-4-6
color: blue
memory: project
skills:
  - plan-before-code
  - code-quality
---

# Agent Instructions

Detailed instructions for the agent go here in markdown.
The agent receives these instructions as its system prompt.
```

### Agent Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique agent identifier |
| `description` | Yes | Short description (shown in agent list) |
| `tools` | No | Allowed tools (defaults to all) |
| `model` | No | Model override for this agent |
| `color` | No | Status line color indicator |
| `memory` | No | Memory scope: `user`, `project`, or `local` |
| `skills` | No | Skills preloaded into the agent context |
| `hooks` | No | Agent-specific lifecycle hooks |

### Built-in vs Custom Agents

| Built-in Agent | Purpose | Custom Alternative |
|---------------|---------|-------------------|
| `general-purpose` | Multi-step tasks with all tools | Full-access agent with project-specific instructions |
| `Explore` | Fast codebase search (read-only) | Research agent with additional context skills |
| `Plan` | Design implementation plans | Architecture agent with domain-specific patterns |

### Memory Scopes

Agents can maintain persistent memory across conversations:

| Scope | Location | Shared | Use Case |
|-------|----------|--------|----------|
| `user` | `~/.claude/agent-memory/` | Across all projects | Personal preferences, global patterns |
| `project` | `.claude/agent-memory/` | With team (committed) | Project conventions, architecture decisions |
| `local` | `.claude/agent-memory-local/` | Not shared (gitignored) | Local experiments, temporary notes |

Memory files follow the same 200-line auto-injection limit as CLAUDE.md. Agents automatically create topic-specific files when content exceeds this limit.

### Command-Agent-Skill Orchestration Pattern

The most powerful pattern for complex tasks chains three tiers:

```
Command (Entry Point)
    |
    v
Agent (Orchestrator)
    |
    +---> Skill A (Specialist)
    |
    +---> Skill B (Specialist)
    |
    v
Output (Artifacts)
```

**How it works**:
1. A **command** (`.claude/commands/`) provides the entry point and user-facing interface
2. The command triggers an **agent** (`.claude/agents/`) that orchestrates the workflow
3. The agent activates **skills** (`.claude/skills/`) as specialized tools for each phase
4. The agent produces output artifacts (code, docs, reports)

**Example**: A "full feature" command triggers a planning agent that uses `plan-before-code`, `code-quality`, and `unit-tests` skills in sequence with quality gates between phases.

This pattern is formalized in the `cross-model-orchestrator` and `workflow-orchestrator` skills.

---

## Next Steps

1. **Browse the catalog**: `catalog/skills/CATALOG.md`
2. **Try a skill**: Copy `kubernetes-expert` and ask about K8s
3. **Combine skills**: Use `task-coordinator` to plan complex work
4. **Create a custom agent**: Add a `.claude/agents/my-agent.md` file
5. **Use RPI workflow**: Try `research-plan-implement` for structured feature development
6. **Customize**: Modify skills for your specific needs

**See also**: [SESSION_LIFECYCLE_DECISIONS.md](SESSION_LIFECYCLE_DECISIONS.md) - the "will I need this tool output again?" test for deciding when to delegate to a subagent vs run in the main session.

---

**Version**: v1.1.1
**Last Updated**: May 2026
**Part of**: [DevAI-Hub](../README.md)
