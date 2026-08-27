# Session History - Interface-Craft Skills Phase 3: layout-and-spacing and interface-copy

**Date**: 2026-08-23
**Branch**: `feat/v3.20.2-interface-craft-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.2-interface-craft-skills.md`](../../plans/v3.20.2-interface-craft-skills.md)
**Phase**: 3 - layout-and-spacing and interface-copy (A5, A4)
**Outcome**: Two more cluster skills registered. Catalog 316 -> 318. Ownership handoffs to accessibility-engineering, web-typography, frontend-ui-engineering, writing-editing, anti-slop-editing, and internal-comms are named, not restated. Ready for Phase 4.

## What Was Implemented

- `layout-and-spacing`: grouping, spacing scale, start-edge alignment, progressive disclosure, breakpoints, logical properties. References: `grouping-and-alignment.md`, `adaptive-breakpoints.md`.
- `interface-copy`: in-product microcopy with SKIP fencing docs, anti-slop, and internal comms. Reference: `empty-error-and-confirm.md`.
- Both registered by hand (index, skills.json, marketplace 35, bundles module). Matrix rows added. Trigger cases for both; interface-copy positives packed with `empty-state` / `confirmation` / `validation` after a 1.15x margin miss against `write me a README`.

## Tests

- `validate_skills.py --bundles-only`: PASS (318)
- `check_registry_entries.py --check --strict`: PASS
- `run_trigger_evals.py --gate`: PASS after the interface-copy prompt rewrite

## Ownership check

Grep of the two new skills found no restated contrast ratios, `outline: none` rules, or heading-rank rules. Layout mentions `line-clamp` only as a handoff to `web-typography`. Interface-copy mentions `aria-describedby` only as a handoff to `accessibility-engineering`.

## Next

Phase 4: `web-typography` and `color-systems`.
