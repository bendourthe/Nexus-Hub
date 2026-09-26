# Rendered-context baseline -- v4.13.3

**Covers**: the estimated token size of what a model receives from each lockstep instruction file, as rendered fresh and as installed on one development machine, with the skill-index share and candidate Legacy Instruction Block counts. **Read by**: whoever implements v4.13.3 Phases 4-5, v4.16.0, or v4.17.3 and needs a "before" number to compare against. **Key topics**: estimated tokens, skill-index share, duplicate skill index, legacy spans, redaction.

**Measured on**: 2026-09-25
**Revision**: `feat/v4.13.3-adoption-agent-practice-and-harness-token-efficiency` after Phase 2 (`5479cdc8`), with the Phase 3 scripts uncommitted
**Plan**: [v4.13.3-adoption-agent-practice-and-harness-token-efficiency](../plans/v4.13.3-adoption-agent-practice-and-harness-token-efficiency.md), sub-task 3.4

All token counts are ESTIMATED with the stdlib regex estimator in `scripts/check_memory_integration_budget.py` (word runs plus standalone punctuation). They track relative size well and are not a vendor tokenizer count.

## Commands

Fresh renders went into a throwaway home, run from outside the repository so no project-local surface was written. Cursor has no global Markdown instruction file, so it was rendered at workspace scope into a throwaway git repository.

```bash
T=/c/tmp/nhbase
HOME="$T" USERPROFILE="$(cygpath -w "$T")" python scripts/lib/integrations/runner.py install \
    --scope global --target "$T" --integrations claude,codex,cursor,gemini,opencode --instruction-only --quiet
HOME="$T" USERPROFILE="$(cygpath -w "$T")" python scripts/lib/integrations/runner.py install \
    --scope workspace --target "$T/ws" --integrations cursor --instruction-only --quiet
python scripts/measure_rendered_context.py --redact --json --path <each rendered or installed file>
```

## Fresh render (all five lockstep templates)

| Platform | File | Est. tokens | Words | Skill index tokens | Index share | Index rows | `**Total:` lines | Legacy spans |
|---|---|---|---|---|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | 18051 | 8717 | 14585 | 80.8% | 337 | 1 | 0 |
| Codex | `~/.codex/AGENTS.md` | 17447 | 8420 | 14585 | 83.6% | 337 | 1 | 0 |
| Cursor | `<workspace>/AGENTS.md` | 17395 | 8389 | 14585 | 83.8% | 337 | 1 | 0 |
| Gemini | `~/.gemini/GEMINI.md` | 17425 | 8410 | 14585 | 83.7% | 337 | 1 | 0 |
| OpenCode | `~/.config/opencode/AGENTS.md` | 17392 | 8389 | 14585 | 83.9% | 337 | 1 | 0 |

The skill index is 81-84% of every freshly rendered file, and the behavioral guidance around it is about 2800-3500 estimated tokens. That share is what Phase 5's pointer targets.

## Installed state (one development machine)

These numbers come from ONE machine that has run many installs across versions, so they show what accumulation can look like, not a typical user. Output was redacted: the home directory is `~` and headings no template shipped appear as `user section #n`.

| Platform | File | Est. tokens | Skill index tokens | Index share | Index rows | `**Total:` lines | Candidate spans (lines, est. tokens) | Kept lines | Duplicate headings |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | 28639 | 23461 | 81.9% | 545 | 2 | 3-37 (228), 39-330 (10305) | 2 | 15 |
| Codex | `~/.codex/AGENTS.md` | 27342 | 23453 | 85.8% | 545 | 2 | 3-282 (9905) | 1 | 11 |
| Gemini | `~/.gemini/GEMINI.md` | 1919 | 0 | 0% | 0 | 0 | none | 1 | 0 |
| OpenCode | `~/.config/opencode/AGENTS.md` | 17380 | 14585 | 83.9% | 337 | 1 | none | 0 | 0 |

The Claude and Codex files each carry a full pre-marker install above the managed block: an older 206-skill index plus the template sections it came with, which is why each shows two `**Total:` lines and 11-15 duplicate headings. The candidate spans hold about 10500 (Claude) and 9900 (Codex) estimated tokens, roughly a third of each file. In the Claude file the leftover is split around two kept lines the fingerprint set does not recognize, which is the interleaved layout the Phase 3 detector keeps by construction. The installed Gemini file holds no skill index on this machine; that file was not re-investigated here, because the fresh render above is the baseline Phase 5 compares against.

## What was not measured

The other eight substantive templates (`base-google-shared.md`, the guardrails-only five, `base-pi.md`, `generic-instructions.md`) were skipped. The plan makes them optional; the lockstep five carry the skill index, which is the dominant cost.

## Skill-Index Pointer saving (Phase 5, 2026-09-25)

Every registered integration was installed at global scope into three throwaway homes (detection roots pre-created so detection-gated platforms install): the committed Phase 4 tree with `NEXUS_HUB_SKILL_INDEX` unset, the Phase 5 tree unset, and the Phase 5 tree with `NEXUS_HUB_SKILL_INDEX=pointer`. The eleven instruction files are byte-identical between the first two once each run's home path and directory-name project heading are normalized, so the unset default changes nothing.

| Instruction file | Est. tokens, full index | Est. tokens, pointer | Saved | `**Total:` lines (full / pointer) |
|---|---|---|---|---|
| `~/.claude/CLAUDE.md` | 18051 | 3538 | 14513 | 1 / 0 |
| `~/.codex/AGENTS.md` | 17447 | 2934 | 14513 | 1 / 0 |
| `~/.config/opencode/AGENTS.md` | 17392 | 2881 | 14511 | 1 / 0 |
| `~/.copilot/copilot-instructions.md` | 17447 | 2934 | 14513 | 1 / 0 |
| `~/.qwen/QWEN.md` | 17273 | 2760 | 14513 | 1 / 0 |
| `~/.openclaw/workspace/AGENTS.md` | 17273 | 17273 | 0 | 1 / 1 |
| `~/.pi/agent/AGENTS.md` | 17273 | 17273 | 0 | 1 / 1 |
| `~/.nexus-ai/catalog/NEXUS_AI.md` | 18035 | 18035 | 0 | 1 / 1 |

The pointer removes 99.5% of the index's estimated 14585 tokens on each eligible file (the plan's floor is 90%). Files without a skill index at all (`~/.gemini/GEMINI.md`, `~/.gemini/antigravity/rules.md`, `~/.codeium/windsurf/memories/global_rules.md`) are unchanged under both values.

### Resolved eligibility

Eligibility is derived at render time from the `skill_read_paths` facts in `docs/policy/platform-read-contracts.json` and the installed destinations, never stored. With every VERIFIED path holding an installed skills tree:

| Scope | Eligible | Not eligible (no VERIFIED path for the scope) |
|---|---|---|
| global | antigravity2, claude, codex, copilot, cursor, gemini-cli, hermes, opencode, qwen, windsurf | aider, antigravity, gemini, kimi, nexus-ai, openclaw, pi |
| workspace | antigravity2, claude, codex, copilot, cursor, gemini-cli, hermes, opencode, qwen, windsurf | aider, antigravity, gemini, kimi, nexus-ai, openclaw, pi |

A VERIFIED path with no installed tree is not eligible (full index). Copilot's global `~/.claude/skills` path is UNVERIFIED as of the 2026-09-25 re-fetch, so a Copilot install is eligible only through `~/.copilot/skills` or `~/.agents/skills`; in the all-integrations run above, Codex's `~/.agents/skills` supplied that tree, which the runner's pointer-mode second pass picks up regardless of install order.
