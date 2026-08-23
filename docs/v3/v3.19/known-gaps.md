# Known Gaps - v3.19

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-23

v3.19.0 is finalized. v3.19.1 (agent-memory substrate) is reconciled for release: remaining items are deferred carry-forwards, not unfinished phase work.

## v3.19.1

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 0 |
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

##### DF-3 - Accidental-commit guard for a relocated store is documentation-only

- **Source phase**: Phase 6 - Known-gaps reconciliation (comparison risk R3)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` (sub-task 3.4 / 6.3)
- **Reason**: The default root is `~/.nexus-hub/memory/`, and `extensions/nexus-memory/gitignore.recommended` ships the ignore pattern. Sub-task 3.4 did not add a secret-scan hook matcher for a store that a user relocates into a repository.
- **Suggested next step**: If relocated-root commits become a real incident, add a secret-scan / large-file-guard matcher for `entries.log` and `tree/level_*` rather than expanding the default root.

##### DF-4 - Memory content remains plaintext at rest

- **Source phase**: Phase 6 - Known-gaps reconciliation (comparison risk R2)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` (sub-task 6.3)
- **Reason**: Confidentiality at rest is addressed by a user-scoped default, a relocation warning, and [[egress-redaction]] before shared artifacts. The log is still plaintext. Encryption would add a key-management surface the plan did not take on.
- **Suggested next step**: Reconsider only if a user-facing threat model requires at-rest encryption; do not add a key or a network KMS.

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
| PA-1 | Whole-tree three-part policy audit | Phase 6 | Dated 2026-08-23. See Final Policy Audit below. |

### Final Decisions

| Candidate | Disposition | Reason |
|---|---|---|
| Encrypt the memory log at rest | Deferred as DF-4, not implemented | Adds key management without reducing the documented relocation and egress risks. |
| Hook the secret-scan path for relocated stores | Deferred as DF-3, not implemented | Default root is already outside the repo; the ignore pattern covers the relocate case. |

### Final Policy Audit - 2026-08-23

- Audited every file this plan added or modified for HTTP clients (`httpx`, `requests`, `urllib`, `aiohttp`), URL constants, and secret-shaped environment reads (`API_KEY`, `TOKEN`, credential `getenv`).
- `extensions/nexus-memory/src/` imports only stdlib and local modules. A source-scan test forbids network modules on every path, including error and recovery.
- Phase 1 helpers (`scripts/lib/output_paging.py`, `scripts/lib/self_naming.py`) and the budget guard import no network module. `tiktoken` is optional and local-only.
- The extension README line `zero outbound calls, zero API keys, zero model downloads` is present and true.
- The `already-local` row for `nexus-memory` in `docs/policy/mcp-reverse-engineering-matrix.md` is accurate.
- Layout audit: `extensions/nexus-memory/` matches sibling extension layout. The Phase 1 paging helper lives once under `scripts/lib/` and is imported, not copied. No empty directories, duplicates, or docs-tree moves were required.
- Network-blocked CI: `.github/workflows/nexus-memory.yml` `test-network-blocked` runs the full suite in Docker `--network none`. The multi-OS locking matrix remains merge-gated.

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
