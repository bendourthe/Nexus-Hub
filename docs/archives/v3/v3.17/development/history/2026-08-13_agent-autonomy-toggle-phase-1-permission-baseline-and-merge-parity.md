# Session History - v3.17.0 Phase 1: permission-baseline hardening and cross-platform merge parity

**Date**: 2026-08-13
**Plan**: [docs/releases/v3/v3.17/plans/v3.17.0-agent-autonomy-toggle.md](../../plans/v3.17.0-agent-autonomy-toggle.md)
**Phase**: 1 of 6 (not final; Phase 6 is the terminal refactor / reconciliation / CI phase)
**Branch**: `feat/v3.17.0-agent-autonomy-toggle`, created off `develop` at `5244f3cd`. Phase 1 began directly on `develop` (checkpoint `9023e6c9`, already pushed); mid-session the maintainer directed that all v3.17.0 work be separated onto its own feature branch so it cannot ride the pending v3.16.7 presentify release.
**Prior state**: checkpoint commit `9023e6c9` carried sub-tasks 1.1, 1.1b, 1.3, amendment A3 bug 2, and A3 bug 1 on the bash side only. This session closed the remainder.

## Goal

Make the shipped read-only baseline actually read-only, and make permission installation behave identically on Windows, macOS, and Linux and at both install scopes - so that a hardening reaches the users it was written to protect rather than only fresh installs on one operating system.

## What was done

### Task 1 - Parity debt: port `installer.ps1` to the shared merge helper

The checkpoint commit converted `installer.sh` to `scripts/merge_permissions.py` and left `installer.ps1` on its own native union merge. A union cannot retire an entry, so removal propagation worked on macOS and Linux and silently did nothing on Windows. This was the exact drift class the phase exists to eliminate, introduced while fixing the original instance of it - which is amendment A2's thesis demonstrated inside the phase that motivated it.

- `scripts/merge_permissions.py`: removals moved from stderr to **stdout** under a documented three-line protocol (`added:` / `removed:` / `set:`). This is what makes one calling convention possible for both shells: in Windows PowerShell 5.1, redirecting a native command's stderr wraps every line in an `ErrorRecord` and sets `$?` to false even on a clean exit, so the bash-side `2>&1 >/dev/null` idiom is unusable there. The stale docstring claiming bash keeps a `jq` fast path was corrected to describe what the code actually does and why.
- New `Merge-PermissionsViaHelper` in `installer.ps1`, carrying the same deviation comment as its bash twin. The Claude branch's ~50-line native merge, the Gemini branch's two native merges, and the Copilot branch's native scalar write were all replaced by calls to it.
- `installer.sh`: the helper's interpreter resolution was factored into `resolve_permissions_helper` (using the existing `resolve_python_executable`) plus a shared `report_permissions_helper_output`, so the new scalar mode shares them rather than duplicating. Two globals rather than one word-split string, to stay clean under the ShellCheck severity `make lint` uses.
- A3 bug 1 on the PowerShell side: the Gemini branch's `'"ReadFileTool"' -and '"allowedDomains"'` sentinel was removed. It is the twin of the bash `docker ps` sentinel and has the same effect - present in every existing user's config, so the branch returned early forever.

### Task 2 - Sub-task 1.2 remainder

- **Copilot on Git-Bash**: `MINGW*|MSYS*|CYGWIN*` added to the OS switch, resolving `$APPDATA` (via `cygpath -u` when available, else a backslash translation) to mirror `installer.ps1`'s `Join-Path $env:APPDATA "Code\User\settings.json"` exactly rather than guessing. The branch's `jq` requirement was also removed, because Git-Bash ships no `jq` - mapping the path without that change would have moved the silent skip rather than closing it. That needed a scalar write path, so `merge_permissions.py` gained `--set-true`, and the PowerShell Copilot branch was routed through it too so one implementation writes that key on both systems.
- **Workspace scope**: `install_permissions` / `Install-Permissions` gained a target-path parameter and scope resolution, and both workspace installers gained an `AUTO-APPROVE PERMISSIONS` section gated on the same platform subset as the global block. Claude Code writes `.claude/settings.local.json`; Gemini, Codex, and Copilot skip with a stated reason (see known-gaps DF-2).
- **Gitignore advisory**: both installers check `git check-ignore` at workspace scope and note it when the project does not actually ignore the file. `settings.local.json` is Claude Code's local-only convention, not a guarantee about any given repository.

### Task 3 - Sub-task 1.4: tests and CI

Three new files, 59 tests, all green:

- `tests/validators/test_validate_permission_baseline.py` (35 tests): every detected shape for both prefixes with a read-only counterpart per shape; prefix-vs-glob semantics; the alias trap (`sl` is Set-Location, not Set-Content); the shipped-config regression guard; CLI exit codes 0/1/2; the `_hardening` block not being mistaken for rules; and the cross-layer consistency test asserting - in BOTH directions - that the validator's PowerShell syntax-rejection classes match what `catalog/hooks/format-powershell-description.py` rejects.
- `tests/validators/test_merge_permissions.py` (21 tests, 1 skipped): union add, removal propagation, user-entry preservation, absent and corrupt manifest degrading to add-only, metadata stripping, backup-before-change, idempotence, no temp residue, unparseable-settings safety, the stdout protocol, and both scalar-mode behaviors.
- `tests/installer/test_permission_scope_parity.py` (19 tests): behavioral, running the REAL functions extracted from each installer (bash via `sed`, PowerShell via the AST, following `test_strict_permissions.py`). Includes the end-to-end parity assertion - same seeded config and manifest through both installers, outputs compared byte for byte.

CI needed no change: the `validate` job already runs the baseline validator as a hard gate, and both `tests` (Linux) and `tests-windows` (5.1-pinned) already run `tests/validators` and `tests/installer`, so the new files ride existing jobs per the v3.15.2 Phase 6.3 precedent. Path filters, `concurrency` cancel-in-progress, and pip caching were all confirmed present.

## Four defects the tests found

1. **`Bash(gh api *)` passed the validator** - the entry its own docstring cites as the motivating example, and the exact fixture sub-task 1.3's acceptance criterion names. Rule 3 asks only that a dual-mode tool's first argument be pinned, and `api` is a literal; but `gh api` stays dual-mode at the flag level. Fixed with a data-driven rule 3b (`UNSAFE_SUBCOMMANDS`, `DUAL_MODE_SUBCOMMANDS`), which also closes `Bash(gh repo *)` and `Bash(git branch *)`. The shipped baselines pass unchanged, because every shipped entry already pins at depth two. Recorded as known-gaps BG-2.
2. **A draft `--set-true` used dotted-path traversal.** VS Code's settings.json is FLAT - `"github.copilot.chat.codeGeneration.useInstructionFiles"` is one literal key, not five levels - so the draft would have written a nested object VS Code never reads, leaving the setting silently off. Caught before it landed, and now asserted by test.
3. **The hardening broke 14 tests of the bash description hook** - the most consequential of the four, because the breakage was already on `develop`. `catalog/hooks/tests/test_format_bash_description.py` builds its pattern list by parsing the LIVE `claude-permissions.json`, so removing `awk`, `find`, `cat`, and `echo` broke it, and any release cut from `develop` would have been red - including a v3.16.7 presentify release with no connection to permissions. Fixed by splitting the suite along what each test is actually about: seven parser-structure tests now measure against a fixed `STRUCTURAL_PATTERNS` list (their `echo` was filler), and seven genuine policy assertions are inverted with the I6 reasoning recorded inline, plus one new test guarding that the rest of the pipeline vocabulary survived. Recorded as known-gaps BG-3. A config change is a code change when a test suite reads that config, and nothing in the permission file's diff showed it.
4. **A test harness littered the repository.** `_run_sh` passed a minimal environment, so with `SystemDrive` unset a child expanded `%SystemDrive%` literally and created a directory by that name in the repo root. The harness now inherits the real environment and overrides only what it controls, and runs with `cwd` inside `tmp_path`.

A fourth was a harness artifact rather than a defect: the PowerShell stub used `Write-Output` where the real `Write-Item` uses `Write-Host`, so its strings entered the pipeline and were swallowed by the `if (Merge-PermissionsViaHelper ...)` boolean evaluation, hiding the removal reports the suite asserts on.

## Test results

- New suites: 75 tests, 74 passed, 1 skipped (the real-`jq` comparison leg; `jq` is absent on this host, so the byte-parity assertion constructs the expected output instead - it runs against real `jq` in CI).
- `tests/validators` + `tests/installer`: 978 passed, 17 skipped, 1 failed.
- `catalog/hooks/tests/test_format_bash_description.py`: 163 passed after the BG-3 fix (14 were failing before it).
- Full `tests` + `catalog/hooks/tests` run before the BG-3 fix: 3428 passed, 54 skipped, 18 failed - 14 of them the BG-3 breakage in the file above.
- The single failure is `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`, the pre-existing v3.15.0 WN-1 environmental `tar` quirk in the Windows Git-Bash development environment. The plan's dependency section predicted it would recur during installer work. This phase touched neither the bootstrap scripts nor the tarball path; CI is authoritative.
- Validators: permission baseline PASS on both shipped configs, no-personal-paths PASS, unicode-safety 0 errors (1049 pre-existing warnings, none in files touched here), supply-chain IOC scan PASS.
- `bash -n` clean, `shellcheck --severity=warning` clean, `installer.ps1` AST parse clean.
- `make` is unavailable on this host, so the `make validate` / `make lint` / `make test` steps were run as their underlying commands.

## Deviations

- **The `jq` fast path was dropped rather than kept** (logged at the bash call site in the checkpoint commit, and now also in the helper's docstring). Sub-task 1.2 asked to retain `jq` when present. With removal propagation living in the Python helper, retaining `jq` would mean a host WITH `jq` keeps retired mutation-capable entries while a host without it has them removed - reintroducing, inside a single installer, exactly the divergence this phase eliminates.
- **`merge_permissions.py` gained `--set-true`**, which is beyond sub-task 1.2's literal text (it asked only to map the Git-Bash path). Confirmed with the maintainer before applying, on the grounds that the mapped path is unreachable in practice without it.

## Next steps

- Phase 2: autonomy capability model and per-platform lever verification. Its documentation sweep should also pick up known-gaps NI-2 (whether Gemini's matcher splits compound commands) and DF-2 (whether each platform has a project-scoped permission path at all).
- Phase 4.1 already schedules hands-on verification against a real Claude Code build; NI-1's output-redirection probe should ride that session.
