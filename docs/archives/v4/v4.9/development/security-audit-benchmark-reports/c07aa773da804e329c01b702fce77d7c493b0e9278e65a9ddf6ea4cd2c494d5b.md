# Application audit benchmark

Two predeclared observational attempts. Execution is self-attested; local artifact bytes and ledger consistency are verified. No process attestation or external anchor exists. Omitted host launches and answer access outside declared inputs cannot be discovered.

Candidate: `c07aa773da804e329c01b702fce77d7c493b0e9278e65a9ddf6ea4cd2c494d5b`.

Plan digest: `7c81be97cfdaf3f71dc32fbc31fefeb3df5bc215c3854fe800c310131cac4e2f`. Subject digest: `778bc859fdfc688bcc3c2e8bce10beaae6e80b55c2ef7a0d95d10f733314b9b4`.

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

The local ledger contains exactly two terminal entries and two evaluator-owned outcomes. Its final hash is `7e555e03c8df038ad6ea772d0e903d714d565066569e834adda5512dac482e7b`. Each outcome is recomputed before rendering; attempt-ledger.jsonl is only a derived projection.

Both attempts declare separate source, cache, artifact, and index state. Owned temporary roots are cleaned and original source digests are unchanged. The frozen answer map remains only in the separate local answer archive for future verification; it is excluded from declared host inputs and tracked host artifacts. The corpus is inert syntax and was never executed. Structural remediation is not functional preservation. Characterization misses and unavailable outcomes are informational and do not establish application safety.
