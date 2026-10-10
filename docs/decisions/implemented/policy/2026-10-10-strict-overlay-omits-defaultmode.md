# Decision: The strict permissions overlay omits defaultMode

Status: implemented - `claude-permissions-strict.json` permanently leaves `defaultMode` out, so Claude Code keeps its own default permission mode.

## Problem

The strict Claude permissions overlay omits `defaultMode`, originally pending verification of the setting's value set (v3.15.6 DF-3, carried as v4.13 AR-54). The omission was tested but never decided, so it read as unfinished work.

## Decision

The overlay never writes `defaultMode`. Its purpose is to add allow and deny rules; the permission mode is the user's choice, and when the key is absent Claude Code applies its own default, which is the behavior the overlay wants. The existing test `tests/installer/test_strict_permissions.py::test_overlay_omits_defaultmode` keeps the omission enforced.

Reopening trigger: the overlay gains a purpose that requires a specific permission mode, such as a hardened profile that must start in plan mode.

## Alternatives considered

**Write `defaultMode: "default"`.** Rejected. It adds a key whose effect equals its absence, and it would overwrite a mode the user chose deliberately.

**Leave the item open until the value set is verified.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 7: the omission is correct whatever the value set is.

## Consequences

- v4.13 AR-54 (origin v3.15.6 DF-3) closes on this record.
- The test docstring now cites this decision rather than a pending verification.
