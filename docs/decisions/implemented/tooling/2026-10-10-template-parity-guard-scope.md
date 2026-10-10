# Decision: Template parity guard scope

Status: implemented - whole-template parity stays limited to the five lockstep templates; the other substantive templates are guarded block by block, not by a wider whole-file parity check.

## Problem

`scripts/check_base_template_parity.py` compares only the five lockstep templates (`base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, `base-opencode.md`). Thirteen instruction templates are substantive, so a v3.15.10 advisory (carried as v4.13 AR-50) asked whether the guard should be extended to all of them or its scope recorded as intended.

## Decision

The whole-template parity guard keeps its five-template scope. The other substantive templates (`base-google-shared.md`, the guardrails-only `base-{aider,kimi,openclaw,qwen,windsurf}.md`, `base-pi.md`, and `generic-instructions.md`) are covered by per-block validators. Each validator asserts that one platform-agnostic block is present and identical wherever it must ship, and derives its template roster from the directory, so a newly added template fails until it carries the block. At the time of this decision the per-block validators are `test_autonomy_block_rule.py`, `test_writing_discipline_rule.py`, `test_construction_discipline_rule.py`, `test_end_of_task_rule.py`, `test_attribution_ban_rule.py`, `test_session_handoff_block.py`, and `test_communication_contract_rollout.py` under `tests/validators/`, alongside `test_check_base_template_parity.py` (221 tests passing on 2026-10-10).

A new rule meant for every agent ships with its own per-block validator, following the same pattern.

## Alternatives considered

**Extend whole-template parity to all thirteen.** Rejected. The guardrails-only and Google-shared templates differ from the lockstep five by design: different section sets, `@`-includes, and no catalog surfaces. A whole-file parity check would need so many per-template exemptions that it would assert little beyond what the block validators already prove, and every exemption would hide future drift.

**Leave the scope undocumented.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 4: an unstated scope reads as an omission and keeps the gap open.

## Consequences

- v4.13 AR-50 (origin v3.15.10 parity-guard advisory) closes on this record.
- Whole-file parity applies to the lockstep five only; the other eight substantive templates are guarded only for the named blocks, so agents adding a cross-platform rule must add or extend a block validator.
- A template that should share a block but does not fails that block's validator rather than the parity script.
