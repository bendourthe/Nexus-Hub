# Cross-Project Comparison: DevAI-Hub vs. andrej-karpathy-skills

**Version**: v0.9.4
**Generated**: 2026-04-09T00:00:00Z
**Analyzer**: Claude Code -- compare-project command
**External Source**: https://github.com/forrestchang/andrej-karpathy-skills
**Source Type**: Repository

---

## Section 1: Executive Summary

DevAI-Hub (v0.9.4) and forrestchang/andrej-karpathy-skills are both Claude Code skill plugins, but they occupy completely different points on the scope spectrum: DevAI-Hub is a comprehensive engineering-lifecycle catalog (186 skills, 33 commands, 13 hooks, multi-platform) while andrej-karpathy-skills is a deliberately minimal behavioral ruleset (1 skill, 0 commands, 0 hooks) distilling four LLM coding failure modes identified by Andrej Karpathy.

The comparison surfaces **3 adoption candidates**, all of which are targeted additions to existing DevAI-Hub artifacts rather than new skills — the external project's principles are already substantially covered by existing DevAI-Hub skills and base template rules. The most valuable gap is a missing proactive "state assumptions before acting" behavioral rule in `base-claude.md`; the existing rule only triggers reactively on detected ambiguity. The second gap is a compact self-check formulation ("every changed line traces to the request") that reinforces DevAI-Hub's already-good surgical-changes rules. The third gap is a "senior engineer test" simplicity heuristic worth adding to the `code-simplification` skill.

DevAI-Hub's infrastructure, breadth, and tooling are decisively stronger across every measurable dimension. The recommendation is **minimal, targeted adoption**: two rule additions to `base-claude.md` and one heuristic addition to `code-simplification`. No new skill is needed because the 4 Karpathy principles are fully covered by existing DevAI-Hub skills (`ambiguity-detector`, `code-simplification`, `spec-driven-development`, `incremental-implementation`, `plan-before-code`).

---

## Section 2: Project Profiles

| Attribute | DevAI-Hub | andrej-karpathy-skills |
|---|---|---|
| **Author/Owner** | Benjamin Dourthe ([benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)) | forrestchang |
| **Version** | 0.9.4 (2026-04-07) | 1.0.0 |
| **License** | MIT | MIT |
| **Stars** | N/A (private/early) | 10.3k |
| **Tagline** | "Production-Grade Brain Upgrades for Your AI Coding Assistant" | "Behavioral guidelines to reduce common LLM coding mistakes, derived from Andrej Karpathy's observations" |
| **Core Philosophy** | Depth-first catalog covering every engineering domain with specialized skills, commands, and hooks | Minimal behavioral ruleset addressing four specific LLM failure modes |
| **Scale** | 186 skills, 33 commands, 13 hooks, 10 agents | 1 skill, 0 commands, 0 hooks |
| **Total files** | ~1,200+ | 5 |
| **Distribution** | Shell + PowerShell installers; MCP server; `claude plugin install` | `claude plugin install` marketplace only |
| **IDE Support** | Claude Code, GitHub Copilot, Gemini, OpenAI Codex, Cursor, OpenCode | Claude Code only |
| **Runtime Infrastructure** | MCP server (Python), VS Code extension (TypeScript), Makefile | None (pure documentation) |
| **CI/CD** | 2 GitHub workflows (validation + CodeQL) + pre-commit + Dependabot | None |
| **Plugin config** | `.claude-plugin/plugin.json` + `marketplace.json` | `.claude-plugin/plugin.json` + `marketplace.json` |
| **EXAMPLES.md** | No dedicated examples file | Yes — before/after for all 4 principles |

---

## Section 3: Technology Stack Comparison

| Layer | DevAI-Hub | andrej-karpathy-skills | Notes |
|---|---|---|---|
| **Skill content** | Markdown with YAML frontmatter (name, description, summary_l0, overview_l1) | Markdown with YAML frontmatter (name, description) | DevAI-Hub has richer metadata for MCP discovery |
| **Scripting** | Bash, Python, PowerShell | None | DevAI-Hub has 13 hooks + build scripts |
| **Build system** | Makefile (validate, lint, build-catalog, test, clean) | None | DevAI-Hub only |
| **Package manager** | npm (VS Code ext), pip (MCP server), hatchling | None | DevAI-Hub only |
| **Test framework** | pytest (1,077 LOC across hook tests + MCP server tests) | None | DevAI-Hub only |
| **Linting** | ShellCheck, commitizen, pre-commit hooks | None | DevAI-Hub only |
| **CI/CD** | ci.yml (validation) + codeql.yml (security) | None | DevAI-Hub only |
| **Secret detection** | `secret-scan.sh` hook | None | DevAI-Hub only |
| **Dependency scanning** | Dependabot + CodeQL | None | DevAI-Hub only |
| **Distribution** | Installer scripts + `claude plugin install` | `claude plugin install` | Both use plugin marketplace |
| **Primary language** | Markdown + Python + Bash | Markdown | External is documentation-only |

---

## Section 4: AI Assistant Configuration Comparison

### Plugin Marketplace

Both projects use the `.claude-plugin/` convention with `plugin.json` and `marketplace.json`. DevAI-Hub's configuration references all 186 skills and 33 commands; the external project's configuration references 1 skill.

| Attribute | DevAI-Hub | andrej-karpathy-skills |
|---|---|---|
| `plugin.json` skills path | `./catalog/skills` | `./skills` |
| `plugin.json` commands path | `./.claude/commands` | None |
| `marketplace.json` keywords | ai-skills, claude-code, cursor, gemini, copilot, ... | guidelines, best-practices, coding, karpathy |
| Category | (multi-domain) | workflow |

### Hooks

DevAI-Hub has 13 hook scripts (PreToolUse, PostToolUse, SessionStart, Stop) covering: bash description enforcement, git guardrails, secret scanning, large file guards, auto-formatting, lint-on-write, usage monitoring, session summaries, and auto-devlog.

The external project has no hooks.

### Skill Anatomy

DevAI-Hub's skills use 4-field YAML frontmatter (`name`, `description`, `summary_l0`, `overview_l1`) enabling progressive disclosure and MCP search. The external project's single SKILL.md uses only `name` and `description`. No structural gap to address.

### Instruction Templates

DevAI-Hub ships 5 platform-specific base instruction templates (Claude, Gemini, Codex, Cursor, OpenCode) plus a generic template. The external project has one CLAUDE.md at the repo root used as a direct drop-in.

---

## Section 5: Skills and Capabilities Gap Analysis

### 5a. Present in External, Missing in Current

The external project's single skill (`karpathy-guidelines`) bundles four behavioral principles:

| External Principle | DevAI-Hub Equivalent | Gap |
|---|---|---|
| Think Before Coding | `ambiguity-detector`, `spec-driven-development`; base-claude.md: "Ask clarifying questions before coding if requirements are ambiguous" | Rule is reactive ("if ambiguous"); external version is proactive ("state assumptions before acting, name your confusion") |
| Simplicity First | `code-simplification`; base-claude.md: "Don't add features... beyond what was asked" | Missing the "senior engineer test" heuristic and "200 lines → 50 lines" concrete threshold |
| Surgical Changes | base-claude.md: "Don't add docstrings/comments/type annotations to code you didn't change"; "Don't add features beyond what was asked" | No compact self-check rule ("every changed line must trace to the request") |
| Goal-Driven Execution | `spec-driven-development`, `incremental-implementation`, `plan-before-code` | Well covered; no meaningful gap |

The external project also includes an **EXAMPLES.md** with concrete before/after illustrations of all 4 principles. DevAI-Hub has no equivalent dedicated examples file (though individual skills include usage examples inline).

### 5b. Present in Current, Missing in External

DevAI-Hub's strengths that the external project does not approach:

- 185 additional skills across 21 domain categories
- 33 workflow commands
- 13 hook scripts with a 61-test suite
- Multi-platform support (5 platforms)
- MCP server for skill discovery
- VS Code usage monitor extension
- Full CI/CD pipeline (validation, CodeQL, Dependabot)
- Permission system (5 platform profiles)
- Comprehensive documentation (10+ guides, 50+ doc files)
- Installer scripts for Windows/macOS/Linux
- AGENTS.md agent contribution guide
- Language-specific coding rules (bash, python, go, typescript)

### 5c. Present in Both, Quality Comparison

| Area | DevAI-Hub | andrej-karpathy-skills | Winner |
|---|---|---|---|
| Behavioral simplicity rules | Spread across multiple skills and base template | Unified in one SKILL.md + CLAUDE.md | External (more focused) |
| Goal-driven/test-first approach | `spec-driven-development` (comprehensive) | Brief mention in principle 4 | DevAI-Hub |
| Before/after examples | Inline within each skill | Dedicated EXAMPLES.md | External (more discoverable) |
| Assumption management | `ambiguity-detector` (deep, systematic) | "Think Before Coding" rule (brief, memorable) | DevAI-Hub for depth; external for behavioral memorability |
| Plugin marketplace config | Full `.claude-plugin/` with rich metadata | Minimal `.claude-plugin/` | DevAI-Hub |

---

## Section 6: Commands and Automation Comparison

### 6a. Commands Gap

DevAI-Hub: 33 slash commands covering the full engineering lifecycle.
External: 0 commands.

No adoption candidates.

### 6b. CI/CD and Hooks Gap

DevAI-Hub: 2 GitHub workflows, 13 hook scripts, pre-commit configuration, Dependabot.
External: No CI/CD, no hooks, no pre-commit.

No adoption candidates.

---

## Section 7: Documentation and Developer Experience Comparison

| Aspect | DevAI-Hub | andrej-karpathy-skills |
|---|---|---|
| README | Quick start, 3 install paths, featured skills, usage monitoring | Problem statement, 4 principles, 2 install methods, success indicators |
| Installation | 30-second shell/PowerShell installer OR `claude plugin install` | `claude plugin install` OR curl CLAUDE.md |
| Setup effort | Medium (full installer with platform prompts) | Very low (single file or one command) |
| EXAMPLES.md | None | Yes — before/after for all 4 principles |
| Guides | 10+ specialized guides | None |
| Contributing | CONTRIBUTING.md + CODE_OF_CONDUCT.md + AGENTS.md | None |
| Project templates | 4 (Django, Go, Next.js, Rust) | None |
| Onboarding | setup-project command, interactive installers | README only |

The external project's **EXAMPLES.md** is worth noting: a dedicated before/after illustration file is a simple, high-signal documentation pattern. DevAI-Hub's individual skills include examples, but there is no equivalent consolidated reference for the most common behavioral pitfalls.

---

## Section 8: Testing and Security Posture Comparison

| Dimension | DevAI-Hub | andrej-karpathy-skills |
|---|---|---|
| Test framework | pytest | None |
| Test LOC | 1,077 | 0 |
| Hook tests | 61 test cases (test_format_bash_description.py) | N/A |
| MCP server tests | catalog loading, search, config validation | N/A |
| Coverage tooling | Not configured | N/A |
| Secret detection | `secret-scan.sh` pre-write hook | None |
| SAST | GitHub CodeQL workflow | None |
| Dependency scanning | Dependabot (npm, pip, GitHub Actions) | None |
| Permission system | 5 platform permission profiles | None |
| Security policy | SECURITY.md (7-day SLA for critical) | None |
| Bash linting | ShellCheck (severity=warning) in CI | None |

---

## Section 9: Structural and Architectural Differences

The external project uses a **flat, minimal structure** — 5 files, shallow directory tree, no catalog, no metadata, no build system. This is by design: the project is meant to be a single-file drop-in for any Claude Code project.

DevAI-Hub uses a **deep catalog structure** — skills organized by domain category, each with YAML frontmatter for MCP discoverability, a JSON index for programmatic access, and a Makefile for catalog validation. This architecture enables features the external project cannot have: MCP search, plugin marketplace with 186 skills, skill bundles, and command orchestration.

These are not competing approaches to the same problem — they serve different purposes. The external project's minimal footprint is a feature for quick behavioral overlay; DevAI-Hub's depth is a feature for comprehensive engineering capability.

One notable architectural difference: the external project's CLAUDE.md is designed to be **merged directly** into a project's own CLAUDE.md, making it composable. DevAI-Hub's installer places skills and commands into `.claude/` directories, which is more powerful but less trivially composable.

---

## Section 10: Adoption Plan

### P0 — Immediate (High Value, Low Effort)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Add "state assumptions explicitly" rule to `base-claude.md` | CLAUDE.md principle 1: "Think Before Coding" — present multiple interpretations, name confusion before proceeding | `templates/ai-instructions/base-claude.md` Critical Rules section (after line 43) | Low — 1 line | None | Very low — additive rule, no conflicts |

### P1 — Short-term (Medium Value, Low Effort)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Add "every changed line traces to the request" self-check rule | SKILL.md principle 3: "Surgical Changes" — "every changed line should trace directly to the user's request" | `templates/ai-instructions/base-claude.md` Critical Rules section | Low — 1 line | P0 complete | Very low — reinforces existing rules |
| Add "Simplicity Heuristic" subsection to `code-simplification` skill | SKILL.md principle 2: "Simplicity First" — "senior engineer test", "200 → 50 line" threshold | `catalog/skills/code-cleanup/code-simplification/SKILL.md` after Complexity Assessment section | Low — ~8 lines | None | None |

### P2 — Medium-term (Low Value, Low Effort)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Sync `.claude-plugin/marketplace.json` stats to v0.9.4 counts | Current state: stats show 184 skills, 32 commands | `.claude-plugin/marketplace.json` lines 29-30 | Trivial | None | None |

### P3 — Backlog (Not Recommended)

| What | Reason Not to Adopt |
|---|---|
| Create new unified behavioral skill | All 4 principles already covered by: `ambiguity-detector`, `code-simplification`, `spec-driven-development`, `incremental-implementation`, `plan-before-code`. New skill would be redundant. |
| Create EXAMPLES.md at repo root | Individual skills already contain inline examples. A root-level file would drift from skill-level content and add maintenance burden. |
| Simplify to external project's file structure | DevAI-Hub's catalog architecture enables MCP discoverability, plugin marketplace, and orchestration. Simplifying structure would remove these capabilities. |

---

## Section 11: Implementation Sequence

The 3 adoption items are independent — no ordering dependencies between them. They can be implemented in a single session.

```
[base-claude.md Gap 1] ──→ immediate, no deps
[base-claude.md Gap 2] ──→ same session as Gap 1, same file
[code-simplification Gap 3] ──→ separate file, same session
[marketplace.json P2] ──→ trivial, any time
```

Recommended order (single pass, minimize context switching by file):
1. Edit `templates/ai-instructions/base-claude.md` — add both Critical Rules in one edit
2. Edit `catalog/skills/code-cleanup/code-simplification/SKILL.md` — add Simplicity Heuristic
3. Edit `.claude-plugin/marketplace.json` — sync stats

Total estimated time: < 15 minutes.

---

## Section 12: Risks and Considerations

**No significant risks.** All adoption items are additive, not replacement.

**The two base-claude.md additions** reinforce existing rules rather than contradicting them. The existing "Don't add features beyond what was asked" cluster (lines 55-58) is well-established; the new rules add precision without introducing conflicts.

**The code-simplification heuristic** is a memorable mental model that complements the existing cyclomatic complexity thresholds; no risk of conflict.

**Not recommended for adoption:**
- A new unified behavioral skill: would create maintenance duplication with 5 existing skills that already cover the same ground. When the external project's principles are examined individually, each maps cleanly to an existing DevAI-Hub skill with better depth and examples.
- Adopting the external project's minimal structure: the external project's power comes from being small enough to drop into any project's CLAUDE.md directly. DevAI-Hub's power comes from breadth and tooling. These are orthogonal design points; copying the minimal structure would be a regression.

**External project's popularity (10.3k stars)** reflects strong market validation of the four Karpathy principles as a useful behavioral overlay. This is an argument for making DevAI-Hub's existing coverage of these principles more explicit and discoverable (which the base-claude.md additions accomplish), not for creating duplicate content.
