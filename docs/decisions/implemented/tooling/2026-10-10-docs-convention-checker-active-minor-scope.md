# Decision: Docs convention checker scans the active minor only

Status: implemented - `check_docs_conventions.py` keeps its active-minor scope and older minors and archives are grandfathered; historical link repair is not a gate.

## Problem

`scripts/check_docs_conventions.py` scans only the active minor's documentation tree. When it was introduced (v3.19.2), a whole-tree pass found 141 missing relative targets, almost all in historical minors and policy matrices. The choice between repairing that history and recording it as grandfathered was deferred (v3.19.2 DF-2, carried as v4.13 AR-42).

## Decision

The checker scans the active minor only. Closed minors, `docs/archives/`, and other historical trees are grandfathered: their links are not gated, and a broken historical link is fixed only when someone is already editing that document for another reason. Living documentation outside the release trees is covered by its own checks (for example `documentation-consistency` and the handbook preconditions), not by widening this script.

## Alternatives considered

**Repair every historical link and widen the gate.** Rejected. It is a large one-off edit of frozen records whose value is their historical accuracy, and archived documents are not re-read by agents in normal work.

**Widen the scan but report history as advisory only.** Rejected. A permanent wall of advisory findings trains readers to ignore the checker's output.

**Leave the decision pending.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 4.

## Consequences

- v4.13 AR-42 (origin v3.19.2 DF-2) closes on this record, together with a docstring correction in the checker.
- A new broken link in the active minor still fails the gate.
- Reopening trigger: archived documents become an input that agents or tooling consume routinely, so that a broken historical link causes a real failure.
