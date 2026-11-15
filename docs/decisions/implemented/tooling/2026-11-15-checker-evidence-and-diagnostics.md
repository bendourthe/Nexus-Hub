# Decision: Checker evidence and diagnostics

Status: implemented - Captured evidence bytes are never repaired, supported release headings and ledger roots read equivalently, blocked detail is a bounded local observation, and archive movement waits for unresolved live references. Publication and integration keep their own gates.

## Problem

Consumer repositories hit false checker failures and lost captured log bytes to automatic Unicode repair. Blocked runs offered no bounded way to see which approval items were uncovered, and an archive could report success while live configuration paths stopped resolving.

While the work waited, standalone pull requests changed the same modules: a blocked-detail gap notice, residual-reference reporting with batched moves, an approval summary that omits a zero-task Time row, and a stricter per-member rule loader. The paused branch had to meet them.

## Decision

Protect every file under an `evidence` directory from `--fix`, scanning it but never rewriting its bytes. Accept exact-version H1 and H2 changelog headings, plain or linked, outside fences. Resolve ledger roots strictly so relative, absolute and short-name forms agree and a missing root fails explicitly.

Report item-specific approval coverage without granting authority. Keep develop's request-scoped gap ids and the plan's `--item` form side by side.

Make `check-minor --detail` and `minor_close.py status --detail` one bounded local observation (ten seconds, 32 controller candidates, two MiB per input, 100 findings) that never writes completion. It replaces the earlier detail branch, and keeps that branch's visible result: a `diagnostic gaps.minor` stderr notice, now read from the verified findings.

Block archive movement on unresolved supported live references and keep develop's residual-reference notice for the rest. Show no Time row for zero-task phases unless release-only time remains.

## Alternatives considered

| Option | Benefit | Cost and decision |
|---|---|---|
| Keep develop's detail branch and drop the bounded observation | Smallest merge | Detail would run the full evaluation and its hosting queries, and the plan's limits would not hold; rejected |
| Drop the gap notice when replacing the branch | Simpler output | Removes landed consumer-visible behavior with tests behind it; rejected |
| Compute the notice with a second ledger read in the parent process | Matches the old code path | Reads ledgers without the size bound; rejected |
| Repair evidence but keep a backup | No lost bytes | The original bytes stop being the evidence; rejected |
| Rewrite live JSON and attribute references during archive | No manual repair | Rewrites sealed receipts and consumer configuration; rejected |
| Parse archive references with a general language parser | Fewer missed cases | New dependency and scope far beyond the defect; rejected |
| Add a bounded local observation and keep landed output | Honors the plan limits and the landed behavior | Two stub-based tests changed to stub the new collector; selected |

## Consequences

The Unicode wording `PRESERVED <path>: preserved evidence; findings are reported without repair.` is shared with develop. The completion contract's Local Diagnostic Detail section states the stderr notice.

The merge changed two develop mock tests in `tests/validators/test_consumer_checker_handoff.py` so they stub the detail collector rather than the removed call path. The real command-line tests in `test_consumer_checker_workflow.py` pass unchanged.

Deferred policy branches stay deferred: historical-ledger relief, structured baseline evidence, record recreation, cleanup thresholds, prompt capture and sibling-worktree mutation. The operational protocol lives in the [completion contract](../../../../catalog/skills/workflow/implement-phase/references/completion-contract.md), and the release record is [v4.15.4-last-phase-evidence.md](../../../releases/v4/v4.15/development/v4.15.4-last-phase-evidence.md).
