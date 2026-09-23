# Trigger pilot 2 aborted attempt

**Date**: 2026-09-23
**Runner**: `scripts/run_trigger_pilot.py` on Claude Code 2.1.280
**Protocol**: [protocol.md](protocol.md)
**Disposition**: `UNMEASURED`; no description was promoted.

The isolated worktree passed its 17-check Windows fast profile before this attempt. The runner's local selector and spend tests passed 12 cases, and a staging check found four changed skill descriptions in a 96-call matrix. The command used `--ceiling 35` and a USD 0.50 per-call CLI budget.

| Printed call | Tier | Variant | Selector | Reported cost |
|---|---|---|---|---:|
| 1, `html-output-conventions` | strong | A | unknown (`None`) | USD 0.6540 |
| 2, `plan-before-code` | strong | B | unknown (`None`) | USD 0.6292 |

The two printed rows sum to USD 1.2832. This is the reported minimum, not a provider billing receipt; the CLI was interrupted before the runner wrote its aggregate JSON, and any in-flight billing at interruption is not independently established. The first printed call alone exceeded the runner's USD 0.50 reservation by USD 0.1540. The aggregate pre-call check therefore cannot guarantee a hard USD 35 ceiling using that reservation. The attempt was stopped rather than silently accepting a weaker cap or treating unknown selectors as negative selections.

Before another paid pilot, an owner must establish a provider-enforced ceiling or a proven per-call upper bound that the aggregate ledger reserves before each invocation, and prove the CLI can return observed selection under that bound. The old 96-call result remains unchanged and is not reinterpreted by this attempt.
