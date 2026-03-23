---
name: agent-access-policy
description: Configure file-level access controls for AI coding agents using Claude Code's native permission system. Provides templates and configuration snippets for restricting which files and directories each agent can modify based on task scope. Use when delegating work to agents and wanting to enforce least-privilege access.
summary_l0: "Configure least-privilege file access controls for AI coding agents"
overview_l1: "This skill configures file-level access controls for AI coding agents using Claude Code's native permission system, providing templates and configuration snippets for restricting file and directory modification by task scope. Use it when delegating work to agents and wanting to enforce least-privilege access, preventing agents from modifying files outside their task scope, or setting up multi-agent environments with clear write boundaries. Key capabilities include permission policy template creation, directory-level access restriction, task-scope-based permission assignment, read-only versus read-write distinction, glob pattern-based path filtering, and multi-agent write-scope ownership configuration. The expected output is agent access policy configurations with file/directory permissions scoped to each agent's task. Trigger phrases: agent access, file permissions, agent scope, least privilege, write access, agent restrictions, permission policy, agent boundaries."
---

# Agent File Access Policy

Configure granular file-level access controls for AI coding agents. Rather than giving agents unrestricted access to the entire codebase, this skill provides templates and configuration patterns for restricting each agent's write access to only the files relevant to its task. This implements the principle of least privilege for AI agents.

## When to Use This Skill

Use this skill when:

- Delegating tasks to AI agents and wanting to limit their blast radius
- Setting up a multi-model workflow where each model should only modify specific areas
- Working in a codebase with sensitive areas (auth, payments, infrastructure) that should not be modified without explicit approval
- Onboarding a new team member or agent to a large codebase with clear ownership boundaries
- You want to prevent accidental modifications to files outside the task scope

**Trigger phrases**: "agent permissions", "file access control", "restrict agent access", "least privilege", "agent boundaries", "limit write access", "agent scope", "file access policy", "permission template"

## What This Skill Does

- **Policy Templates**: Ready-to-use `.claude/settings.json` configurations for common agent roles
- **Path Pattern Library**: Glob patterns for restricting access by area (frontend, backend, infra, etc.)
- **Role-Based Configurations**: Pre-built policies for common agent roles (frontend developer, backend developer, reviewer, infrastructure engineer)
- **Escalation Integration**: Works with the `escalation-trigger` hook to warn or block access to sensitive paths

## Instructions

### Step 1: Define Agent Roles and Scope

Identify the agent's task and determine the minimum set of files it needs to modify.

**Role-to-Scope Mapping Template:**

| Agent Role | Read Access | Write Access | Blocked Areas |
|-----------|------------|-------------|---------------|
| Frontend developer | Entire repo | `src/components/`, `src/pages/`, `src/styles/`, `tests/frontend/` | `src/api/`, `infrastructure/`, `migrations/` |
| Backend developer | Entire repo | `src/api/`, `src/services/`, `src/models/`, `tests/api/` | `src/components/`, `infrastructure/`, `migrations/` |
| Test writer | Entire repo | `tests/`, `__tests__/`, `*.test.*`, `*.spec.*` | `src/` (read-only), `infrastructure/` |
| Infrastructure engineer | Entire repo | `infrastructure/`, `Dockerfile*`, `docker-compose*`, `.github/workflows/` | `src/` (read-only) |
| Read-only reviewer | Entire repo | None | All files (read-only) |
| Bug fixer (scoped) | Entire repo | Specific files listed in the bug report | Everything else |

### Step 2: Configure Claude Code Permissions

Claude Code supports path-based permissions in `.claude/settings.json`. Use these templates to restrict agent access.

**Template A: Frontend-Only Agent**

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(npm test*)",
      "Bash(npm run lint*)",
      "Bash(npx tsc*)",
      "Write(src/components/**)",
      "Write(src/pages/**)",
      "Write(src/styles/**)",
      "Write(src/hooks/**)",
      "Write(tests/frontend/**)",
      "Write(tests/__snapshots__/**)",
      "Edit(src/components/**)",
      "Edit(src/pages/**)",
      "Edit(src/styles/**)",
      "Edit(src/hooks/**)",
      "Edit(tests/frontend/**)"
    ],
    "deny": [
      "Write(src/api/**)",
      "Write(src/services/**)",
      "Write(infrastructure/**)",
      "Write(migrations/**)",
      "Write(.github/**)",
      "Edit(src/api/**)",
      "Edit(src/services/**)",
      "Edit(infrastructure/**)"
    ]
  }
}
```

**Template B: Backend-Only Agent**

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(pytest*)",
      "Bash(python -m pytest*)",
      "Bash(ruff check*)",
      "Bash(mypy*)",
      "Write(src/api/**)",
      "Write(src/services/**)",
      "Write(src/models/**)",
      "Write(src/utils/**)",
      "Write(tests/api/**)",
      "Write(tests/services/**)",
      "Edit(src/api/**)",
      "Edit(src/services/**)",
      "Edit(src/models/**)",
      "Edit(src/utils/**)",
      "Edit(tests/api/**)",
      "Edit(tests/services/**)"
    ],
    "deny": [
      "Write(src/components/**)",
      "Write(src/pages/**)",
      "Write(infrastructure/**)",
      "Write(migrations/**)",
      "Write(.github/**)",
      "Edit(src/components/**)",
      "Edit(src/pages/**)",
      "Edit(infrastructure/**)"
    ]
  }
}
```

**Template C: Test Writer (Read-Only Source, Write Tests Only)**

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(pytest*)",
      "Bash(npm test*)",
      "Write(tests/**)",
      "Write(__tests__/**)",
      "Edit(tests/**)",
      "Edit(__tests__/**)"
    ],
    "deny": [
      "Write(src/**)",
      "Edit(src/**)",
      "Write(infrastructure/**)",
      "Edit(infrastructure/**)"
    ]
  }
}
```

**Template D: Scoped Bug Fix Agent**

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(pytest*)",
      "Bash(npm test*)",
      "Write(src/services/payment_processor.py)",
      "Write(tests/services/test_payment_processor.py)",
      "Edit(src/services/payment_processor.py)",
      "Edit(tests/services/test_payment_processor.py)"
    ],
    "deny": []
  }
}
```

### Step 3: Combine with Escalation Trigger Hook

For defense in depth, combine file access policies with the `escalation-trigger` hook. The hook provides a second layer of protection by warning or blocking writes to sensitive paths.

**Recommended layered configuration:**

1. **Claude Code permissions** (primary enforcement): restrict Write/Edit to allowed paths
2. **Escalation trigger hook** (advisory layer): warn when writes target sensitive patterns even within allowed paths

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/escalation-trigger.sh"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/escalation-trigger.sh"
          }
        ]
      }
    ]
  }
}
```

### Step 4: Apply Policy for Multi-Model Workflows

When using the `cross-model-orchestrator` skill, apply different access policies to each model role:

| Role | Access Policy |
|------|--------------|
| Planner | Read-only (no Write/Edit permissions) |
| Reviewer | Read-only (no Write/Edit permissions) |
| Implementer | Write access to source and test files only |
| Verifier | Write access to test files only (can add verification tests) |
| Breaker | Write access to test files only (can add adversarial tests) |

**Implementation**: create separate `.claude/settings.json` files for each role (e.g., `.claude/settings.planner.json`, `.claude/settings.implementer.json`) and specify the appropriate config when launching each model session.

## Best Practices

- **Default to least privilege**: start with read-only access and add write permissions only for the specific paths the agent needs
- **Use glob patterns, not individual files**: `Write(src/api/**)` is maintainable; listing every file is not
- **Combine enforcement and advisory layers**: use Claude Code permissions for enforcement and the escalation trigger hook for additional visibility
- **Scope by task, not by role**: the scoped bug fix template (Template D) is often more appropriate than broad role-based access; narrow the scope to the specific files in the task description
- **Review denied access attempts**: if an agent frequently hits permission boundaries, it may indicate the task scope was too narrow or the agent is trying to solve a cross-cutting concern
- **Document the policy**: include a comment in the settings file explaining why each path is allowed or denied, so the next person (or agent) understands the rationale

## Related Skills

- `cross-model-orchestrator` - Multi-model workflows where each role gets different access
- `escalation-trigger` (hook) - Advisory hook for sensitive path detection
- `component-boundary-identifier` - Identify architectural boundaries for access policy design
- `quality-gate-definitions` - Define gates that check for unauthorized file modifications

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Least-privilege principle, Claude Code permission system, defense-in-depth patterns
