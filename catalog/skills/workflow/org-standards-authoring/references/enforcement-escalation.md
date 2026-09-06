# Organization Standards Enforcement Escalation

Use this reference when ordinary Nexus-Hub organization projections are too advisory for the organization's risk or compliance needs. Nexus-Hub writes local instructions and rules; it does not create vendor-managed policy, change an administrator dashboard, or guarantee that an agent obeys prose.

## Decision Rule

Escalate only when the organization can name a requirement that must be non-overridable or centrally administered. Keep the connected Nexus-Hub bundle as the portable source of guidance, then configure the relevant platform-native control through its documented administrative surface. Record which system is authoritative and how conflicts are resolved.

## Documented Platform Options

| Platform | Native organization option | Authority boundary | Source |
|---|---|---|---|
| Claude Code | Managed policy `CLAUDE.md`, managed settings, or company standards linked through `.claude/rules/` | Managed policy and settings are administered outside Nexus-Hub. Nexus-Hub does not write `/etc/claude-code/`, `C:\Program Files\ClaudeCode\`, or managed-settings policy. | [Claude Code memory](https://code.claude.com/docs/en/memory), [Claude Code settings](https://code.claude.com/docs/en/settings) |
| Cursor | Team Rules configured by a Team or Enterprise administrator | Team Rules are created and enforced in Cursor's administrative surface. A locally projected rule is not a Team Rule. | [Cursor rules](https://cursor.com/docs/context/rules) |
| GitHub Copilot | Organization custom instructions for eligible Business or Enterprise organizations | Organization instructions are managed in GitHub. GitHub documents personal and repository instructions as higher-priority context than organization instructions, so treat the organization layer as advisory where sets conflict. | [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) |

## Platforms Without a Native Organization Enforcement Claim

The Nexus-Hub research did not verify a built-in organization-managed enforcement layer for Codex, Gemini CLI, or Antigravity. Use their documented hierarchical instruction files and repository governance, and add hooks or permission controls only where the platform documents those mechanisms. Do not invent a priority setting or describe a repository instruction file as centrally enforced.

## Escalation Checklist

- [ ] The requirement that needs stronger enforcement is named and approved by its policy owner.
- [ ] The chosen platform documentation explicitly describes the administrative mechanism and precedence.
- [ ] The administrator, not Nexus-Hub, configures the managed platform control.
- [ ] The connected bundle and managed copy have a documented source of truth and synchronization process.
- [ ] `nexus-hub org status` continues to describe the local projection as `default` or `advisory`, never `enforced`.
- [ ] A blocking requirement is backed by a platform permission, hook, CI gate, or other documented control rather than prose alone.

## Research Basis

This guidance is derived from the verified platform table and constraints in [Nexus-Hub's organization knowledge layer research](https://github.com/bendourthe/Nexus-Hub/blob/main/docs/releases/v3/v3.17/development/org-knowledge-layer-research.md). Re-check the linked official vendor documentation before changing an enforcement design because platform capabilities and precedence can change.
