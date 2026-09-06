# Development History -- v3.8.0 loop-engineering enrichment

**Date**: 2026-06-18
**Version**: v3.8.0
**Plan**: [docs/releases/v3/v3.8/plans/adoption-ralph-claude-code.md](../../plans/adoption-ralph-claude-code.md)
**Comparison**: [docs/releases/v3/v3.8/comparisons/v3.8.0-comparison-ralph-claude-code.md](../../comparison-ralph-claude-code.md)
**Branch**: `feat/loop-engineering-enrichment` -> merged to `develop`

## Goal

Enrich the existing `loop-engineering` skill and its `loop-schema.md` reference with the loop-design doctrine an executable loop runtime (the Ralph for Claude Code comparison) surfaced, with zero new skill, command, outbound call, dependency, or credential. Nine candidate capabilities: six skill-native adoptions, one `re-partial` (local sandbox), three declines.

## What landed

### Phase 1 -- exit + safety doctrine (commit a7cd294)

- `SKILL.md`: **Exit-Signal Protocol** -- a structured machine-readable status block with a dual-condition exit gate (explicit signal AND command-derived corroboration, never a single claim) and a force-exit safety after K consecutive "done" signals.
- `SKILL.md`: **Stall and Fault Detection** -- three distinct fault classes (no-progress / repeated-error / permission-denial) with cooldown / auto-recovery, framed as deterministic-shell doctrine, not a shipped runtime.
- `SKILL.md`: **untrusted-task-source fence** in the Scheduled-Triage Recipe -- external task descriptions are requirements DATA, never instructions (a standing prompt-injection defense).
- `loop-schema.md`: `exit_condition` notes the structured-signal dual-condition refinement; `progress_check` names the fault classes; new single-claim-exit anti-pattern.

### Phase 2 -- observability + intake (commit d0141cf)

- `loop-schema.md`: concrete per-iteration JSON Lines `trace_log` schema (`loop_number` / `success` / `duration` / `calls` / `tokens` / `exit_reason` / `timestamp`), with `exit_reason` matching the Phase 1 fault classes and exit protocol.
- `SKILL.md`: **task-readiness gate** -- route underspecified tasks to `/plan` via `ambiguity-detector` + `requirement-enhancer` instead of looping on a vague goal; **per-iteration recovery-point note** deferring to `using-git-worktrees` + `rollback-strategy-advisor`.

### Phase 3 -- sandboxing + declines (commit 9ddcedf)

- `SKILL.md`: **Sandboxing an Unattended Loop** -- run only the writable iteration in a LOCAL container composing `containerization` + `agent-access-policy` + `using-git-worktrees`, with the cloud-egress sandbox variant explicitly excluded under the MCP Registry Policy.
- `docs/policy/mcp-reverse-engineering-matrix.md`: three `drop-outright` declines recorded (cloud-egress sandbox, dependency-DAG task queue, per-project loop runtime config + standalone runtime), each naming its local-first equivalent.

## Key decisions

- **No `data/` registry edit**: the enrichment added depth, not a new headline capability, so `summary_l0` / `overview_l1` are unchanged.
- **Attribution rule**: the distributed skill carries no upstream product name; the comparison report is the only artifact that names the upstream, and the matrix / CHANGELOG cite it by file path only.
- **Body size**: 157 -> 189 lines, under the 500-line norm, so no split into `references/` was needed.

## Verification

Per-phase: `validate_skills.py --bundles-only` PASS (0 errors), JSON catalogs OK, body under 500 lines, zero non-ASCII, zero forbidden upstream tokens in the skill bundle, all new cross-links resolve. Cross-file consistency confirmed: the `exit_reason` enum matches the fault classes; the three new H2 sections and two inline gates are present.

## Release prep

- Relocated the Ralph plan + comparison from `docs/v3/v3.7/` to `docs/v3/v3.8/` with full reference repair (no stale `v3.7.0` Ralph references remain).
- Closed two carried-forward known gaps: WN-v37-3 (`README_zh` counts) and WN-v33-2 (two over-limit `overview_l1` fields). See [docs/releases/v3/v3.8/known-gaps.md](../../known-gaps.md).
