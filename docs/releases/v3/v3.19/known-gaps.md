# Known Gaps - v3.19

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-24

v3.19.0 through v3.19.2 are released. v3.19.1 shipped, then the artifact round-trip failed: `MANIFEST.sha256` was generated before the gap-closure commit, so `nexus-hub verify` against the published `v3.19.1` tarball reports FAIL. Do not retag. v3.19.2 regenerated the manifest; the published `v3.19.2` tarball verifies PASS (1274 files). Remaining open items are v3.19.2 DF-2, DF-3, and DF-4 (docs-convention scope, semantic-reformatter coverage, signed-execution study). They stay here for the next `/plan` ingest.

## v3.19.2

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-2 - Docs convention checker covers only the active minor

- **Source phase**: Phase 2 (triggering confidence and eval discipline, task 2.3)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 2 / link-integrity checker)
- **Why deferred**: A first pass over the whole `docs/` tree reported 141 missing relative targets, almost all in historical minors and policy matrices. Gating them in this patch would bury the new checker under archaeology. The guard therefore scans `docs/v3/v3.19/` in a repo checkout (tests still scan a tmp `docs/` tree that has no `v3.19`).
- **Suggested next step**: either repair historical links in a dedicated docs PR, or keep the active-minor scope and record older trees as grandfathered.

##### DF-3 - Semantic reformatters cover a named short list, not ~60 command handlers

- **Source phase**: Phase 4 (compressor and hook depth, task 4.3)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 4 / semantic reformatters)
- **Why deferred**: A dedicated command-output compressor in this class ships on the order of 60 handlers. Matching that set in one patch would dominate the release and still miss the long tail. This release ships git status, pytest/vitest/jest failures-only, and ruff/eslint/tsc grouped-by-file, each with a 60% token-reduction fixture, and documents the rest as a coverage gap.
- **Suggested next step**: add handlers only for commands whose fixtures miss the 60% bar in real sessions; do not chase handler-count parity.

##### DF-4 - Signed execution contracts stay a design study

- **Source phase**: Phase 5 (compressor polish and session mining, task 5.4)
- **Plan reference**: `docs/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md` (Phase 5 / signed-execution-contract study)
- **Why deferred**: A local single-user agent already has a 0/1/2/3 rewrite decision subordinated to host deny. Cryptographic signatures would add key material without blocking anything host settings cannot already refuse. Study: `docs/v3/v3.19/design/signed-execution-contract-study.md` (**# DEVIATION**: plan cited `docs/v3/v3.18/design/`). Recommendation: defer crypto; optionally adopt capability-id + TTL as an unsigned convention later.
- **Suggested next step**: revisit only if Nexus-Hub grows a multi-executor or remote-runner surface.

#### Bugs / Regressions

None.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

##### DF-1 - Tagged `checksums.txt` hashes unpublished until the GitHub Release existed

- **Source phase**: Phase 1 (supply-chain hardening, task 1.1)
- **Resolved**: 2026-08-23 post-tag. Hashes for `Nexus-Hub-3.19.2.tar.gz` and `.zip` are in `checksums.txt` and attached to the GitHub Release. The `v3.19.2` tag was not rewritten.
- **Evidence**: `python scripts/verify_install.py --root <extracted tarball>` reported `verify: PASS` (1274 files).

## v3.19.1

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 4 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 0 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

None.

#### Bugs / Regressions

None. BG-1 (published v3.19.1 tarball failed `nexus-hub verify`) is resolved below: v3.19.2 regenerated the manifest and the published tarball verifies PASS.

#### Warnings

None.

#### Missing Tests / Coverage Gaps

None.

#### Quality-Gate Gaps

None.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| PA-1 | Whole-tree three-part policy audit | Phase 6 | Dated 2026-08-23. See Final Policy Audit below. |
| DF-1 | OpenCode live tool-output truncation is UNVERIFIED | Gap-closure pass | First-party source on the official repository publishes live defaults of 50 KiB and 2,000 lines (`packages/opencode/src/tool/truncate.ts`). MATCH. Looser than the safe default. |
| DF-2 | Remaining install targets have no dated truncation evidence | Gap-closure pass | Copilot (20,480 bytes), Qwen (25,000 / 1,000), Kimi MCP (100,000), OpenClaw (16,000), and Aider (no silent cap) are now MATCH. Windsurf and Nexus-AI remain table-UNVERIFIED after a dated search and inherit the default; that is a finished classification, not a deferred investigation. |
| DF-3 | Accidental-commit guard for a relocated store is documentation-only | Gap-closure pass | `memory-store-guard.{sh,ps1}` blocks Write, Edit, and `git add` / `git commit` of store artifacts inside a git working tree. Tests cover both implementations. |
| DF-4 | Memory content remains plaintext at rest | Gap-closure pass | POSIX owner-only permissions (`0700` / `0600`), in-repo create/append refusal, store marker, and the DF-3 hook. Encryption and a key or network KMS were declined. Residual: a reader who already has that user's filesystem access can still read the plaintext log, the same as other `~/.nexus-hub/` files. |
| WN-1 | Claude Code settings page is JS-rendered | Gap-closure pass | Official static pages now document `BASH_MAX_OUTPUT_LENGTH` default 30000: [env-vars](https://code.claude.com/docs/en/env-vars) and [tools-reference](https://code.claude.com/docs/en/tools-reference). |
| BG-1 | Published v3.19.1 tarball fails `nexus-hub verify` | v3.19.2 | Manifest regenerated; published `v3.19.2` tarball verifies PASS (1274 files). Do not retag `v3.19.1`. |

### Final Decisions

| Candidate | Disposition | Reason |
|---|---|---|
| Encrypt the memory log at rest | Declined, not deferred | Adds a key-management surface. Confidentiality is addressed by a user-scoped default, POSIX owner-only files, in-repo refusal, the accidental-commit hook, and [[egress-redaction]] before shared artifacts. |
| Guess truncation numbers for Windsurf and Nexus-AI | Declined | No first-party live tool-output page after the 2026-08-23 second pass. UNVERIFIED rows do not move the default. |
| Keep the 20,000-byte paging default after OpenClaw MATCH | Declined | The safe default is the minimum across MATCH rows. OpenClaw's documented live default is 16,000 characters for models below a 100K-token window. |

### Final Policy Audit - 2026-08-23

- Audited every file this plan added or modified for HTTP clients (`httpx`, `requests`, `urllib`, `aiohttp`), URL constants, and secret-shaped environment reads (`API_KEY`, `TOKEN`, credential `getenv`).
- `extensions/nexus-memory/src/` imports only stdlib and local modules. A source-scan test forbids network modules on every path, including error and recovery. `subprocess` is used only to ask local `git` whether a path is inside a working tree.
- Phase 1 helpers (`scripts/lib/output_paging.py`, `scripts/lib/self_naming.py`) and the budget guard import no network module. `tiktoken` is optional and local-only.
- The extension README line `zero outbound calls, zero API keys, zero model downloads` is present and true.
- The `already-local` row for `nexus-memory` in `docs/policy/mcp-reverse-engineering-matrix.md` is accurate.
- Layout audit: `extensions/nexus-memory/` matches sibling extension layout. The Phase 1 paging helper lives once under `scripts/lib/` and is imported, not copied. No empty directories, duplicates, or docs-tree moves were required.
- Network-blocked CI: `.github/workflows/nexus-memory.yml` `test-network-blocked` runs the full suite in Docker `--network none`. The multi-OS locking matrix remains merge-gated.
- Gap-closure pass: output-truncation table restamped; helper default lowered 20,000 to 16,000; `memory-store-guard` registered on `Write|Edit|Bash`; store refuses in-repo roots unless `NEXUS_MEMORY_ALLOW_IN_REPO=1`.

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
