# Session History -- agentic-setup-adoption, Phase 6 (skill-native conventions and refinements)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 6 of 8 -- Skill-native conventions and refinements
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Adopt the five remaining skill-native refinements from the comparison: the doc-header summary convention + self-healing (2), the run-the-app verb (3), the persona-owned-docs binding (6), the session worksheet handoff + git tags (7), and the helper-script authoring skill (9).

## What was done

### 6.1 Doc-header summary convention + self-healing (point 2)

New `catalog/style-guides/doc-headers.md`: front-load every durable SYSTEM doc (architecture, policy, reference, runbook) with a dense, greppable summary in its first few lines, analogous to a SKILL.md's `summary_l0` / `overview_l1`. Referenced from AGENTS.md's Markdown-style section. `documentation-consistency` gained Step 9 (check the header presence + the self-healing drift rule: a header that no longer matches the system is flagged and corrected in the same change).

### 6.2 Run-the-app verb in the five base templates (point 3)

Added an identical `## Run and Verify` section to all five lockstep templates (`base-claude/codex/cursor/gemini/opencode.md`) via a programmatic insertion anchored on the invariant Branching bullet (byte-identical across the five). The verb: actually run the app and observe the change end-to-end before claiming it works, do not rely on tests / type-checks / a clean build alone; cross-references `verification-before-completion`. Registered `Run and Verify` in `check_base_template_parity.py` as both a REQUIRED heading and an INVARIANT section, so a future edit to a subset of the five is now caught (Option B - enforced, not just added). Parity re-run: 5/5, no drift.

### 6.3 Session worksheet handoff + git tags (point 7)

`session-history` gained a "Mid-Task Handoff Worksheet and Git Tags" section: a committed worksheet detailed enough that a different agent could resume mid-task, tagged `worksheet/<slug>` so a specific in-progress state is retrievable by name.

### 6.4 Helper-script authoring skill (point 9)

New `catalog/skills/developer-experience/helper-script-authoring/SKILL.md`: spot a recurring multi-step incantation, encapsulate it as a robust and DISCOVERABLE `tools/` / `bin/` script (header comment, `--help`, a `tools/README.md` line), and keep building the collection. Distinguished from `create-custom-command` (slash commands) and `mcp-builder` (MCP servers). Registered across `skills.json` (272 skills), `SKILL_INDEX.md` (+1 row, total 272), and `marketplace.json` (developer-experience 31 -> 32).

### 6.5 Persona-owned docs (point 6) + phase validation

`multi-agent-code-review` gained a "Persona-Owned Docs" section: each reviewer persona owns and maintains the doc area it reviews against (maintainability -> naming/structure conventions, security -> the security checklist, ...), so the standard a persona enforces and the doc it maintains are the same artifact.

## Deviations

- **6.2 was made enforceable (Option B)**, not just added: rather than dropping the verb into each conventions section untracked, it is a new shared section registered in the parity checker as required + invariant, so lockstep drift is caught mechanically.
- **Programmatic insertion for the 5 templates + 4 existing-file blocks**: byte-identical multi-file inserts anchored on stable lines, to guarantee the parity checker's byte-identity requirement (a hand-edit across 5 files risks drift).

## Validation

- `skills.json`: valid, 272 skills, no dupes, helper-script-authoring present. Bundle audit: PASS (0 errors). `marketplace.json`: valid.
- `check_base_template_parity.py`: 5/5 present, no drift (the new invariant section holds).
- All Phase 6 insertions ASCII-clean (the em-dash warnings in `session-history` lines 222+ are pre-existing content shifted by the insertion, not introduced here). `tests/skills` unaffected (35 passed).
- Quality gate: GO.

## Next steps

- Phase 7: end-of-shift full-validation orchestrator (`end-of-shift-validation` skill composing tests, perf gate, visual regression, commit sweep, false-confidence audit, review, and repair - depends on Phases 1-4, so it sequences here).
