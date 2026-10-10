# Decision: Hermes stays registry-only

Status: implemented - Hermes remains a registered integration installed on explicit request through the integration runner; neither installer installs it by default.

## Problem

Hermes has a registered adapter (`scripts/lib/integrations/hermes.py`, imported in `__init__.py`) and verified read paths in `docs/policy/platform-read-contracts.md`, but `scripts/installer.sh` and `scripts/installer.ps1` never invoke it. The same obligation was recorded three times (v3.15.2 DF-2, v3.16.0 NI-6, v3.17.0 DF-4, carried as v4.13 AR-05) without a decision between wiring it and declaring the current shape intended.

## Decision

Hermes stays registry-only. It is installed only when a user asks for it through the integration runner (`python scripts/lib/integrations/runner.py install --integrations hermes`), which applies the same seeding, ownership tracking, doctor, repair, and teardown as every other registered platform. The default installers do not detect or install it.

Reopening trigger: Hermes gains enough users that default detection is worth an installer arm, contract checks, and installer smoke coverage, or its vendor documents a detection marker comparable to the other default platforms.

## Alternatives considered

**Wire Hermes into both installers now.** Rejected for this minor. A default arm needs a detection rule, contract checks, and installer smoke tests on every host; that is platform onboarding, not a gap repair, and it would touch both installers for a platform with no requested default install.

**Remove the adapter.** Rejected. The adapter is verified against the vendor's skills documentation and works through the runner; removing it would discard working, tested behavior.

**Leave the item open.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 7.

## Consequences

- v4.13 AR-05 (origins v3.15.2 DF-2, v3.16.0 NI-6, v3.17.0 DF-4) closes on this record.
- Users who want Hermes run the integration runner explicitly; documentation describing default installs stays accurate.
- A future proposal to install Hermes by default must add the detection rule, contract checks, and smoke tests together.
