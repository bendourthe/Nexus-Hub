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
