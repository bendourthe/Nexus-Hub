# Known Gaps - v3.19

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-23

v3.19.0 is finalized. v3.19.1 (agent-memory substrate) is in progress. Phase 1 recorded the UNVERIFIED truncation surfaces so Phase 6 can carry them forward. Phase 4 replaced the integration-prose stub with the always-loaded instructions (218 tokens / 500) and added no new open items.

## v3.19.1

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-1 - OpenCode live tool-output truncation is UNVERIFIED

- **Source phase**: Phase 1 - Output-safety foundation
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` (sub-task 1.1)
- **Reason**: Official OpenCode pages document a model-response token cap and a 2,000-character bound during session compaction, not a live per-tool-call truncation limit. The plan forbids guessing. The safe default therefore excludes OpenCode.
- **Suggested next step**: Re-fetch OpenCode docs (or measure locally) in a later pass; if a live cap is published and is tighter than 20,000 bytes / 256 lines, lower the helper defaults and re-stamp the policy file.

##### DF-2 - Remaining install targets have no dated truncation evidence

- **Source phase**: Phase 1 - Output-safety foundation
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` (sub-task 1.1)
- **Reason**: GitHub Copilot, Qwen Code, Kimi Code CLI, Aider, Windsurf, OpenClaw, and Nexus-AI have no first-party tool-output truncation page in the 2026-08-23 pass. They inherit the safe default.
- **Suggested next step**: Same as DF-1, per surface, when a first-party number appears.

#### Bugs / Regressions

None.

#### Warnings

##### WN-1 - Claude Code settings page is JS-rendered

- **Source phase**: Phase 1 - Output-safety foundation
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` (sub-task 1.1)
- **Reason**: The 2026-08-23 fetch of `https://code.claude.com/docs/en/settings` did not expose the environment-variable table as static Markdown. The MATCH classification for the 30,000-character middle-truncation default rests on the official docs issue that quotes that table.
- **Suggested next step**: Re-fetch with a renderer that executes the page, or cite a newly static official table if Anthropic publishes one.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | None | - | - |

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
