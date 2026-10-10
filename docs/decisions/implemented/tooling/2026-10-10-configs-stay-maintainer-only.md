# Decision: configs stay a maintainer surface

Status: implemented - `configs/` is not copied into installed trees; installs consume its effect through derived artifacts and the built-in fallback.

## Problem

`configs/platform-defaults.json` is the single source for per-platform install-time defaults, and `scripts/lib/integrations/platform_defaults.py` falls back to built-in values when the file is absent from an installed tree. AGENTS.md already calls the file a repo-internal source, but no decision closed the v3.16.0 NI-1 item (carried as v4.13 AR-30) that asked whether to distribute it.

## Decision

`configs/` remains a maintainer-only surface. Its effect reaches users through the derived core keys of `catalog/hooks/settings.json` and through install-time seeding, both regenerated from the source and guarded by `python scripts/sync_platform_defaults.py --check`, which also verifies that the offline fallback matches the source. Installed trees do not receive `configs/`.

Reopening trigger: an installed component needs to read a value that is not derived into a distributed artifact or covered by the checked fallback.

## Alternatives considered

**Copy `configs/` into installed trees.** Rejected. It would give users a second, editable copy of values that are already applied, and a user edit to it would silently diverge from the seeded settings it no longer controls.

**Leave the item open.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 7.

## Consequences

- v4.13 AR-30 (origin v3.16.0 NI-1) closes on this record.
- The fallback stays checked against the source in `make validate` and CI, so it cannot rot silently.
