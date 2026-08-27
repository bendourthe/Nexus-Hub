# Session History - Code-Intelligence Hardening Phase 2: Search-Routing Guard

**Date**: 2026-08-22
**Branch**: `feat/v3.19.0-code-intelligence-hardening`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md`](../../plans/v3.19.0-code-intelligence-hardening.md)
**Phase**: 2 - Search-routing guard
**Environment**: Windows 11, PowerShell, Git Bash, Python 3.12.10, pytest, ShellCheck; GNU Make unavailable, so `make test`, `make validate`, and `make lint` were executed as their constituent commands
**Outcome**: Nexus-Hub now installs an advisory `PreToolUse` hook that routes broad `Grep`, `Glob`, and conservative Bash search calls toward the local `nexus-code-search` index while preserving `Read`, unrelated commands, malformed-input fail-open behavior, explicit disable controls, and native-search fallbacks. The Bash and PowerShell implementations have matching behavior, open no network connection, read no credential, and block only when the user explicitly sets hard-block mode.

## 1. Starting State and Routing

- **Starting commit**: `023d0250` (`feat(code-search): add tool profiles`)
- **Branch state**: clean feature branch after the Phase 1 local-only commit
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: the active Codex session remained at or above the planned tier, so no model downshift was made

Phase 2 was kept separate from Phase 1 and Phase 3 so the hook contract, documentation, test evidence, and commit remain independently reviewable.

## 2. What Was Implemented

### 2.1 - Cross-shell routing guard

- Added `code-search-routing.sh` without `set -e`, so parser or helper failures cannot abort the caller.
- Added a PowerShell sibling using native `ConvertFrom-Json` parsing and the same matching and exit-code behavior.
- Redirected `Grep` to `search_code` and `Glob` to `code_search` with copyable local-index call hints.
- Matched direct or piped `grep` / `rg` Bash searches and non-destructive `find` commands using name, path, or regex predicates.
- Treated `cat` as search only when it feeds `grep` or `rg`; plain file reads remain silent.
- Excluded `Read` explicitly because it is required by the edit-safety contract.

### 2.2 - Fail-open controls

- Default mode writes an advisory message to stderr and exits 0.
- `NEXUS_CODE_SEARCH_ROUTING=block` returns 2 only for a matched search call.
- `NEXUS_DISABLED_HOOKS=code-search-routing` and `NEXUS_HOOK_PROFILE=minimal` suppress the hook entirely.
- `NEXUS_CODE_SEARCH_ROUTING_DEBUG=1` reports local classification decisions without changing default allow behavior.
- Empty, malformed, or incomplete stdin exits 0 without output.

### 2.3 - Registration and documentation

- Registered the hook in the `PreToolUse` chain for `Grep|Glob|Bash`.
- Kept installer code unchanged because both installers already copy `catalog/hooks/` recursively.
- Added the behavior, controls, authority boundary, and registration example to the Claude Code settings reference.

## 3. Tests and Troubleshooting

The focused test module runs every behavioral assertion against both shell implementations. It covers every routed tool shape, unrelated and destructive Bash commands, the `Read` exclusion, soft and hard modes, both disable controls, malformed input, debug output, a proxy-blocked environment, and static rejection of network-client or URL primitives.

The first Bash-focused run exposed a host portability issue: Git Bash did not have `jq`, so its parser failed open and produced no advisory. The shell hook now prefers `jq` when present and otherwise uses a local `python3` or `python` JSON parser. If none is installed it still fails open. The final focused and full hook suites pass on both implementations.

Two lint-launch issues were environmental rather than product defects. PowerShell initially passed the complete shell-file list as one native argument, and Bash resolved a Windows npm shim that lacked Node inside WSL. Re-running with native PowerShell argument splatting invoked the installed ShellCheck correctly and the complete catalog passed.

## 4. Verification

| Gate | Result |
|---|---|
| Focused routing tests | 40 passed |
| New routing tests plus generic sibling parity | 312 passed |
| Full `catalog/hooks/tests/` suite | 1,073 passed, 36 skipped |
| Full `make test` equivalent | 43 skill-server passed; 304 code-search passed, 1 skipped; 29 web-fetch passed; 89 skill-scanner passed; 215 context-compressor passed; 2,904 root passed, 28 skipped |
| Full catalog ShellCheck | Pass, including `code-search-routing.sh` |
| PowerShell AST and sibling behavior | Pass through the full hook suite |
| JSON, bundle, quality, routing, permission, installer, security, and workflow validators | Pass |
| Required checks, docs, decisions, registry, version, template, model-profile, platform-contract, and defaults validators | Pass |
| Compression accuracy gate | Pass: CCR 100.0%, signatures 100.0%, reduction 45.8% |
| Git diff hygiene | `git diff --check` passed; pytest caches remain ignored |

## 5. CI/CD and Post-Phase Review

No CI edit was needed. The stable aggregate workflow must remain always-on for protected-branch required checks, but it already classifies changed paths, cancels stale runs, caches pip downloads, runs the full hook suite on Linux and Windows, parses every PowerShell hook, and ShellChecks every catalog shell script. A separate hook-only workflow would duplicate runners without improving coverage.

The docs cleanup audit classifies all eleven final v3.19 artifacts as active and proposes no move or deletion. The v3.19 known-gaps ledger records zero open items. `docs/DEVLOG.md` remains unchanged because it is a one-line-per-release index and v3.19.0 is not released yet.

## 6. Files Changed

| File | Change |
|---|---|
| `catalog/hooks/code-search-routing.sh` | Fail-open Bash routing guard |
| `catalog/hooks/code-search-routing.ps1` | Native PowerShell parity implementation |
| `catalog/hooks/tests/test_code_search_routing.py` | Cross-shell matching, controls, malformed-input, and offline tests |
| `catalog/hooks/settings.json` | `PreToolUse` registration |
| `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md` | User-facing behavior and controls |
| `docs/todos.md` | Phase 2 progress tracking |
| `docs/v3/v3.19/plans/v3.19.0-code-intelligence-hardening.md` | Phase 2 completion checklist |
| `docs/v3/v3.19/known-gaps.md` | Zero-gap reconciliation through Phase 2 |
| `docs/v3/v3.19/docs-cleanup-report.md` | Eleven-artifact active-scope audit |
| `docs/v3/v3.19/development/history/2026-08-22_code-intelligence-hardening-phase-2-search-routing-guard.md` | This history |

## 7. Next Step

Phase 3 adds a documented, deterministic, round-trippable compact response encoding for `nexus-code-search`. It must engage only when it meets the configured savings threshold and must fall back to JSON on every encoding or decoding failure.
