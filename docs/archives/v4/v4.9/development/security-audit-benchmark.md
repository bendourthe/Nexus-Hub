# Application audit benchmark

Two predeclared observational attempts. Execution is self-attested; local artifact bytes and ledger consistency are verified. No process attestation or external anchor exists. Omitted host launches and answer access outside declared inputs cannot be discovered.

Candidate: `bd37a8b8e91ba5c28001d068445a6b3e65a97fada223e5c7b1441ab6bdb3506c`.

Plan digest: `94ab1b0054ede1330323496fe38037e0bf9c991e7ddb574d5e58c3cdb210c397`. Subject digest: `1bdbc22f8b3a46e5dd898ad5e37d3ed0641c7a8df4ede106f990e365dd295ed7`.

| Attempt | Workers | Outcome | Code search |
| --- | --- | --- | --- |
| sequential | 1 | PRE_SCORING_UNAVAILABLE | UNAVAILABLE |
| concurrent-four | 4 | PRE_SCORING_UNAVAILABLE | UNAVAILABLE |

## Characterization targets

| Attempt | Target | Observed | State |
| --- | --- | --- | --- |
| sequential | seed_recall (90) | unavailable | unscorable |
| sequential | blocking_recall (100) | unavailable | unscorable |
| sequential | location_accuracy (90) | unavailable | unscorable |
| sequential | blocking_location_accuracy (100) | unavailable | unscorable |
| sequential | routing_coverage (100) | unavailable | unscorable |
| sequential | required_stage_completeness (100) | unavailable | unscorable |
| sequential | closure_completeness (100) | unavailable | unscorable |
| sequential | artifact_consistency (100) | unavailable | unscorable |
| sequential | benign_high_critical (0) | unavailable | unscorable |
| concurrent-four | seed_recall (90) | unavailable | unscorable |
| concurrent-four | blocking_recall (100) | unavailable | unscorable |
| concurrent-four | location_accuracy (90) | unavailable | unscorable |
| concurrent-four | blocking_location_accuracy (100) | unavailable | unscorable |
| concurrent-four | routing_coverage (100) | unavailable | unscorable |
| concurrent-four | required_stage_completeness (100) | unavailable | unscorable |
| concurrent-four | closure_completeness (100) | unavailable | unscorable |
| concurrent-four | artifact_consistency (100) | unavailable | unscorable |
| concurrent-four | benign_high_critical (0) | unavailable | unscorable |

## Evidence and limits

The local ledger contains exactly two terminal entries and two evaluator-owned outcomes. Its final hash is `21cfc32b955b23f657f9edf7c21e01e9c7cba0c4d93f40eb746fb52c6ed646b1`. Each outcome is recomputed before rendering; attempt-ledger.jsonl is only a derived projection.

Both attempts declare separate source, cache, artifact, and index state. Owned temporary roots are cleaned and original source digests are unchanged. The frozen answer map remains only in the separate local answer archive for future verification; it is excluded from declared host inputs and tracked host artifacts. The corpus is inert syntax and was never executed. Structural remediation is not functional preservation. Characterization misses and unavailable outcomes are informational and do not establish application safety.
