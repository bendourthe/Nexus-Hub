---
name: using-nexus-hub
description: "Orient an AI session to Nexus-Hub's skill catalog, commands, and hooks in under 2 minutes. Use whenever a session starts in a Nexus-Hub repo, when a user asks \"how do I find a skill?\" or \"what can you do here?\", when orienting a new agent platform (Claude Code, OpenAI Codex, Gemini, GitHub Copilot, Cursor, GitHub CLI) to the catalog, or when the SessionStart hook fires. Loaded automatically by SessionStart but also worth triggering on demand whenever an agent appears unaware of the local skill set. SKIP: external skill marketplaces unrelated to this repo, generic \"how do I use AI?\" questions, or onboarding to a different catalog."
summary_l0: "Orient an AI session to Nexus-Hub's skill catalog, commands, and hooks in under 2 minutes"
overview_l1: "This meta-skill orients an AI coding session to Nexus-Hub -- explaining how 182 skills are organized, how to find the right skill, how 32 commands work, and what the hook system does. It is loaded automatically at session start via the SessionStart hook so every new session begins with catalog awareness. Use it manually when a session lacks context about the catalog, when onboarding a new AI assistant to the project, or when the agent needs a quick reminder of available capabilities. This skill does not teach how to use individual skills -- it teaches how to navigate the catalog and trigger the right skill for the task at hand."
---

# Using Nexus Hub

Nexus-Hub provides 182 curated skills, 32 commands, and 13 hooks for your AI coding assistant. This file explains how to navigate and use the catalog.

## What Is a Skill?

A **skill** is a structured instruction file (SKILL.md) that activates domain-specific expertise in the AI. Skills are not tools or scripts -- they are high-quality prompts that guide the AI through a specific engineering task with best practices, step-by-step instructions, and quality gates.

Skills are invoked implicitly (the AI recognizes the task type) or explicitly (you reference the skill by name or use a command).

## How Skills Are Organized

Skills are grouped into 22 domain categories:

| Category | What's there |
|---|---|
| **ai-development** | Agent architecture, billing safeguards, context engineering, prompt engineering, RAG |
| **architecture** | API design, C4 decomposition, DDD, event-driven, microservices |
| **bug-fixing** | Bug localization, reproduction tests, root cause analysis, semantic bug detection |
| **business-product** | Business analysis, product management, scrum, technical writing |
| **code-cleanup** | Language-specific cleanup (C, C++, C#, Go, Java, JS, Python) + code simplification |
| **code-review** | Security review, performance review, intent-based review, quality analysis |
| **compliance** | GDPR, SOC2, ISO 27001, ISO 42001, NIST AI RMF, PCI DSS, CCPA |
| **developer-experience** | Frontend UI, spec-driven development, idea refinement, refactoring, migration |
| **documentation** | API docs, docstrings, SBOM, strategic comments, technical docs |
| **framework-specialists** | React, Next.js, FastAPI, Vue, Svelte, Astro deep expertise |
| **infrastructure** | Cloud, CI/CD, containers, Kubernetes, Terraform, SRE, observability |
| **language-specialists** | C++, C#, Go, Java, JavaScript, PowerShell, Python, Rust, SQL, TypeScript |
| **orchestration** | Multi-agent coordination, context management, workflow automation |
| **project-setup** | Initialize C#, Java, JS, Python projects |
| **research** | Trend research with Reddit, X, and web |
| **security** | Auth patterns, CVE analysis, dependency audit, license compliance |
| **specialized-domains** | Android, iOS, fintech, document generation, graphics |
| **testing** | E2E automation, browser DevTools testing, domain contract validation |
| **tests-generation** | Unit, integration, E2E, property-based, mutation, fuzz, BDD tests |
| **workflow** | Spec-driven development, plan-before-code, TDD, incremental implementation, shipping |

## How to Find the Right Skill

**Option 1 -- Use a command:**
```
/skills search <keyword>
```
Searches the full skill catalog by keyword and returns the top matches with summaries.

**Option 2 -- Browse the index:**
The full skill list is at `data/SKILL_INDEX.md`. Each row shows: skill name, category, and a one-line summary.

**Option 3 -- Describe the task:**
If you describe what you want to accomplish, the AI will match it to the appropriate skill automatically. The skill descriptions include trigger phrases designed for this purpose.

## How Commands Work

Commands are slash commands (`.claude/commands/*.md`) that you invoke with a `/` prefix. They are distinct from skills -- commands are workflows that often invoke one or more skills behind the scenes.

Key commands:

| Command | What it does |
|---|---|
| `/skills search` | Find skills by keyword |
| `/commands` | List all available commands (the cheatsheet) |
| `/describe` | Full codebase analysis with Mermaid diagrams |
| `/review` | Senior-level code review (scope-able) |
| `/implement` | Execute one phase of an implementation plan |
| `/session wrap-up` | Capture session history and clean up |
| `/test` | Generate comprehensive test coverage |
| `/review security` | Full security audit with remediation |

Run `/commands` (or `/skills list`) to see all commands with descriptions.

## How Hooks Protect the Session

Nexus-Hub installs 13 hooks that run automatically around tool calls:

| When | Hook | What it does |
|---|---|---|
| Session start | `session-start.sh` | Injects this catalog orientation |
| Before any Bash command | `format-bash-description.py` | Enforces formatted tool descriptions |
| Before any Bash command | `require-description.sh` | Blocks commands without descriptions |
| Before any Bash command | `git-guardrails.sh` | Blocks destructive git commands without confirmation |
| Before Write/Edit | `secret-scan.sh` | Blocks if secrets detected in output |
| Before Write | `large-file-guard.sh` | Warns if writing large files |
| Before Write/Edit | `escalation-trigger.sh` | Escalates risky changes to human |
| After Write/Edit | `auto-format-on-write.sh` | Auto-formats code on save |
| After Write/Edit | `lint-on-write.sh` | Auto-lints on save |
| Session end | `usage-display.sh` | Shows token usage |
| Session end | `notify-on-complete.sh` | Desktop notification |
| Session end | `session-summary.sh` | Session summary |
| Session end | `auto-devlog.sh` | Updates DEVLOG.md |

You do not need to interact with hooks directly -- they run in the background.

## Recommended Starting Points by Task Type

| Task | Start here |
|---|---|
| New feature from scratch | `idea-refine` → `spec-driven-development` → `plan-before-code` → `incremental-implementation` |
| Code review | `/review` command or `code-quality` + `security-review` skills |
| Bug fix | `bug-localization` → `bug-to-patch-generator` |
| Deployment | `shipping-and-launch` |
| Security audit | `/review security` or `security-review` skill |
| Test coverage | `/test` or `unit-tests` + `integration-test-generator` |
| Refactoring | `plan-before-code` → `refactoring-expert` → `behavior-preservation-checker` |
| AI agent development | `ai-agent-development` → `context-engineering` → `prompt-engineering` |
| Confirm you understood a session | `session-teach-back` |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just do the task directly instead of looking for a skill" | Skipping skill discovery means re-deriving a workflow the catalog already encodes; the relevant skill carries the verification gate and rationalization rebuttals you would otherwise miss. |
| "I read the skill index once, I do not need to search again" | The index lists 230+ skills; relying on memory leads to picking a near-match instead of the right skill, so search by task intent each time rather than recalling a name. |
| "Hooks are just noise, I can ignore the warnings" | The secret-scan and git-guardrails hooks block real failure modes (committed credentials, destructive git); treating their output as noise is how a secret reaches the remote. |

## Verification

- [ ] The task was matched against the skill index before starting (a candidate skill was named or "no skill applies" was concluded explicitly)
- [ ] If a skill applies, it was loaded at L1 then L2 before acting
- [ ] The chosen starting point matches a row in the Recommended Starting Points table for the task type
- [ ] Hook warnings surfaced during the session were addressed, not ignored

## Related Skills

- [[plan-before-code]] -- start here for any non-trivial implementation
- [[idea-refine]] -- clarify before you specify
- [[spec-driven-development]] -- specify before you build
- [[incremental-implementation]] -- build one step at a time
