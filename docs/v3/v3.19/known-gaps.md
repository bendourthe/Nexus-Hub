# Known Gaps - v3.19

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-22

Phases 1 through 7 are complete with no open implementation, regression, warning, test, or quality-gate gap.

## v3.19.0

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

None.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | None | - | - |

### Final Decisions

| Candidate | Disposition | Reason |
|---|---|---|
| Live-model A/B evaluation | Dropped, not deferred | Calling a hosted model would violate the zero-API-keys and zero-outbound guarantees. The deterministic local harness remains the release gate. |
| Download-based embedding acquisition | Dropped, not deferred | Downloading weights would violate the zero-model-downloads and zero-outbound guarantees. Dense retrieval accepts only user-supplied, pre-placed local weights. |
| Additional non-code context providers | Documented extension point | The shipped Markdown provider proves the local provider contract. Other ecosystems can be added through that contract when a concrete local use case exists; they are not omissions or release commitments. |

### Final Policy Audit - 2026-08-22

- Audited every file added or modified by the code-intelligence plan for HTTP clients, URL constants, download helpers, and secret-shaped environment reads.
- All matches are either test fixtures that prove the ban, loopback-only network guards, policy documentation, or pre-existing sanctioned installer and help URLs; no plan-owned runtime path can make an outbound call, read an API key, or download a model.
- The full `nexus-code-search` suite passes under both supported MCP SDK lines: 368 passed and 1 optional-parser case skipped under the local MCP 1.27 environment; 369 passed under fresh MCP 2.0 in the Docker `--network none` CI-equivalent environment.
- The exact README statement `zero outbound calls, zero API keys, zero model downloads` remains present and true.
- The `already-local` classification in `docs/policy/mcp-reverse-engineering-matrix.md` remains accurate and requires no amendment.
