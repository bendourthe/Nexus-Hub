# End-of-Task Summary Rule (v3.15.10)

**Status**: locked for v3.15.10 Phase 2
**Date**: 2026-08-04
**Applies to**: all 12 substantive templates under `templates/ai-instructions/`

## The rule, verbatim

This body is byte-identical in every template. The five lockstep files are additionally guarded by `scripts/check_base_template_parity.py`, which carries the heading in both `REQUIRED_HEADINGS` and `INVARIANT_SECTIONS`, so a future divergence fails validation rather than rotting.

```markdown
## End-of-Task Summary
- End every completed task with a short closing summary, even when the change was small
- **Completed**: what actually changed, in one or two lines (files, behavior, or decisions)
- **Next**: the concrete next step, or state plainly that nothing is outstanding
- State blocked, skipped, or deferred work explicitly rather than omitting it
- Keep it scannable and factual: do not restate the conversation or add preamble
- Output-minimization rules never apply to this summary: suppress verbose logs, never the closing summary
```

## Why this is instruction text and not a hook or a skill

**A hook cannot do it.** By the time a `Stop` hook fires, the agent has already finished generating. A hook can only print its own text; it cannot cause the agent to write a summary. This is settled, not open for revisiting.

**A skill would under-trigger.** Skills are selected by matching a `description` against the current task. The requirement is that this happens on *every* completed task, and Claude has a measurable tendency to under-trigger on narrow or implicit descriptions (the reason AGENTS.md mandates deliberately pushy skill descriptions). A rule that must always apply cannot depend on trigger matching.

That leaves always-loaded instruction text, which is why this rule pays a permanent token cost and is therefore kept to six bullets.

## Why the Output Minimization carve-out is load-bearing

Eleven of the twelve templates already carry an `## Output Minimization` section instructing the agent to suppress verbose output, prefer quiet flags, and summarize rather than echo logs. Without an explicit carve-out, a reader (human or model) can resolve "always write a closing summary" against "suppress output" in either direction, and will do so inconsistently across sessions.

The final bullet resolves it by naming the rule *class* rather than a specific heading. That phrasing was chosen deliberately: `generic-instructions.md` has no `## Output Minimization` section, so naming the heading would leave a dangling reference in one of the twelve while naming the class reads correctly in all of them. It also keeps the body byte-identical everywhere, which the parity guard requires.

## Coverage

| Target | Files | Notes |
|---|---|---|
| Lockstep five | `base-claude`, `base-codex`, `base-cursor`, `base-gemini`, `base-opencode` | Bodies must stay byte-identical; guarded |
| Google family | `base-google-shared` | Covers Antigravity 1.0, Antigravity 2.0, and Gemini CLI via `@base-google-shared.md`, and Antigravity CLI **transitively** through `@base-antigravity-20.md` (a two-hop include chain, verified 2026-08-04) |
| Guardrails-only | `base-aider`, `base-kimi`, `base-openclaw`, `base-qwen`, `base-windsurf` | No slash or skills surface, but they do carry instruction text |
| Fallback | `generic-instructions` | Different structure; the section sits after Global Style rather than after Output Minimization |

`base-gemini.md` is standalone and does **not** include `base-google-shared.md`, so it needs its own copy and there is no duplication risk. AGENTS.md's instruction to "edit all 5 in lockstep" is incomplete: 16 template files exist, 12 of them substantive.

## Insertion point

In the eleven files that have it, the section goes immediately after `## Output Minimization`, so the carve-out sits adjacent to the rule it qualifies. In `generic-instructions.md` it goes after `## Global Style & Communication Preferences`.

The templates use a compact heading style with no blank line between a heading and its first bullet. The new section matches that local convention rather than the generated-Markdown style guide, because consistency inside the file is what a reader sees.

## Platforms this reaches that notifications cannot

GitHub Copilot has no hook surface and OpenCode's `plugins/` is a JS/TS Bun runtime, so neither can receive the v3.15.10 notification hooks. Both do carry an instruction file, so both are fully covered by this rule. That asymmetry is the reason the two deliverables in this release are separate: one is bounded by hook support, the other only by having an instruction surface.
