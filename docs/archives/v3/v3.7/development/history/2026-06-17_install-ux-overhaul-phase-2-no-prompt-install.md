# Session History -- v3.7.0 install-ux-overhaul Phase 2: no-prompt all-platform install + conflict-only overwrite

**Date**: 2026-06-17
**Plan**: [`docs/releases/v3/v3.7/plans/install-ux-overhaul.md`](../../plans/install-ux-overhaul.md)
**Phase**: 2 of 5 -- No-prompt all-platform install + conflict-only overwrite
**Branch**: `feat/installer-bootstrap` (off `develop`)
**Outcome**: complete. All three sub-tasks (2.1 scope/platform, 2.2 conflict-only overwrite, 2.3 tests/stabilization) closed; every locally-runnable Stability Gate item is green and the bash conflict-helper coverage is wired into the existing CI `pytest tests/installer` step (authoritative under WN-v36-1).

## Goal

Remove the interactive global/repo scope prompt and the platform-selection prompts; default to a global install across ALL supported platforms (absent ones skip-with-note); keep marker-merge for instruction files but prompt only when a real overwrite conflict is detected on a plain managed file. Add `--workspace` / `--platforms` / `--yes` (plus `--force`) for power users and CI. The only outbound call remains the project's own GitHub; no new dependency, credential, or third-party processor.

## Design fork settled with the maintainer (ask-first area)

`scripts/installer.{sh,ps1}` are an AGENTS.md ask-first area, and sub-task 2.2 had a genuine internal tension (the plan's "under `--yes`, never clobber" wording vs. Phase 3's `nexus-hub upgrade` needing files to actually refresh). Two questions were batched up front:

1. **Conflict model + `--yes` default.** Chosen: **"Diff + refresh-on-yes"** -- interactive = one end-of-run prompt naming the differing managed files (default keep); `--yes` / `--force` / non-interactive = refresh managed files to the latest silently. (Rejected: keep-on-yes, which would break the upgrade path; and manifest-hash tracking, which is a larger lift -- the bash `safe_copy` path has no last-written-hash.)
2. **`--platforms` vocabulary.** Chosen: **integration keys** (`claude, codex, gemini, antigravity2, gemini-cli, copilot, cursor, opencode, nexus-ai, aider, windsurf, kimi, qwen, openclaw`) -- the same tokens `--print-config` already uses.

## Subtasks completed

1. **2.1 -- Remove scope/platform prompts; default global + all platforms.** Removed the bash `Select [G/W]` scope prompt and the PowerShell `Select-Platforms` menu + `Get-Overwrite-Preference` (O/S/A) prompt. Scope is resolved from `--workspace` / `-Workspace` (default global). A bash `should_install <key>` guard wraps every per-provider block (and the matching legacy-4 permission installs) in `install_global` and `install_workspace`; PowerShell reuses its existing `$platforms -contains` gating fed by a new non-interactive `Resolve-Platforms`. The shared instruction-template metadata (PROJECT_NAME/OS_CONTEXT/...) was hoisted out of the Claude block so it is set even when `--platforms` excludes Claude. New flags `--workspace`/`--platforms`/`--yes`/`--force` (bash) and `-Workspace`/`-Platforms`/`-Yes`/`-Force` (PS) are parsed, validated, and threaded through the `--branch` re-exec passthrough. A non-TTY stdin implies assume-yes, so the Phase 1 `curl|bash` / `irm|iex` bootstrap drives a clean no-prompt refresh; the workspace language prompt and the PowerShell `Pause` are suppressed on that path.
2. **2.2 -- Conflict-only overwrite confirmation.** `safe_copy` / `Safe-Copy` compare on-disk content to the source: identical = silent, differing-under-refresh = overwrite now, differing-under-interactive = record into parallel conflict arrays + KEEP. A new `resolve_conflicts` / `Resolve-Conflicts` runs once after the install pass, lists the files, and asks once (default keep; on yes, overwrites the kept set). `safe_folder_copy` / `Safe-Folder-Copy` drop their prompt -- refresh = full sync (removes stale), interactive = non-destructive merge (keeps user-added extras). The workspace Copilot file routes through `safe_copy` via a temp file rather than its own inline prompt.
3. **2.3 -- Testing and stabilization.** Added `tests/installer/test_no_prompt_install.py` (static surface for both installers + bash-functional coverage of the conflict / platform helpers + early-exit flag validation). Inverted three stale `test_installer_smoke.py` guards to assert the new no-prompt behavior. Added the `[Unreleased]` CHANGELOG entry. Ran every locally-available gate green.

## Key decisions

- **Reuse `OVERWRITE_ALL` as the resolved refresh decision.** `invoke_registry_platform` already appends `--overwrite` when `OVERWRITE_ALL=true`, so resolving that flag once at startup (true under `--yes`/`--force`/non-TTY) makes the marker-merge + dedicated-file refresh "just work" through the registry path with no new plumbing.
- **A single consolidated end-of-run conflict prompt**, not per-file. Strictly better than the old per-file `[Y/N/A]` loop and exactly matches the gate's "exactly one conflict prompt listing the file".
- **Catalog trees are Nexus-owned and never trigger a conflict prompt.** They refresh on every run (full sync under refresh, non-destructive merge interactively). The conflict surface is scoped to the plain `safe_copy` single files (hooks, `mcp-servers.json`, the Copilot file) -- the files a user might actually customize.
- **Keep the `safe_copy` `confirm` parameter for signature compatibility.** ~30 call sites pass a 3rd positional arg; the value is now unused (ShellCheck SC2034-disabled in bash, `$null = $Confirm` in PS) rather than churning every call site.
- **No project version bump and no `data/` edits.** Phase 2 adds no skill/command; the version surfaces stay at canonical 3.6.0 (the v3.7.0 tag is cut by `/update release` in Phase 5).

## Troubleshooting

- **Three `test_installer_smoke.py` regression guards asserted the OLD prompt UX.** After removing the prompts, `test_installer_sh_asks_global_vs_workspace_first`, `test_installer_ps1_asks_global_vs_workspace_first`, and `test_installer_ps1_has_overwrite_request_subsection` failed (they required `Select [G/W]` and the "Overwrite Request" subsection). Resolution: inverted them to guard the NEW behavior (no scope prompt, scope resolved from the workspace flag, `Resolve-Conflicts` present, no `Get-Overwrite-Preference`) so they now prevent a regression back to prompts. Full hooks suite green afterward (441 passed, 14 jq-skips).
- **ShellCheck SC2034 on the now-unused `confirm` param.** `make lint` runs `--severity=warning`; the retained-for-compat param tripped SC2034. Resolution: a documented `# shellcheck disable=SC2034` (keeping the 4-arg call convention intact rather than editing 30 sites).

## Test results

`make`/ShellCheck-as-`make` are not on PATH on this Windows host (WN-v33-1); gates were emulated by invoking the tools directly. The bash end-to-end behavior is CI-authoritative (WN-v36-1).

- `bash -n scripts/installer.sh`: clean. `shellcheck --severity=warning scripts/installer.sh install.sh`: clean.
- `installer.ps1` PowerShell AST parse: clean. No dangling references to the removed `Select-Platforms` / `Get-Overwrite-Preference` / `"NONE"` / `"ASK"`.
- `tests/installer/test_no_prompt_install.py`: 8 static passed + 11 bash-functional skipped on Windows (WN-v36-1). The functional logic was separately verified by running the same extract-and-drive harness through Git Bash: conflict-collected-and-kept, resolve-yes-overwrites, refresh-mode-overwrites-no-conflict, and should_install-gating all PASS -- so they pass on CI ubuntu.
- `catalog/hooks/tests/`: 441 passed, 14 jq-skips (the 3 updated installer-smoke guards green).
- `tests/installer/`: 87 passed. The lone failure is the PRE-EXISTING Phase 1 `test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` -- a Windows-host `/usr/bin/tar` extraction error in the UNMODIFIED bootstrap (WN-v36-1 class); CI ubuntu is authoritative.
- `tests/integrations`: hangs on this space-containing checkout (WN-v36-1); unmodified by this phase, CI authoritative.
- `validate_unicode_safety.py`: 0 errors in the changed installers (only the pre-existing checkmark/box-drawing warnings already in `installer.ps1`). `check_version_sync.py`: all surfaces match canonical 3.6.0.

## CI/CD edits

None needed. CI already runs `pytest tests/installer` (ci.yml line 168) and lints `scripts/installer.sh install.sh`, so the new test file and installer edits are picked up automatically. The new bash-functional tests run on the ubuntu `tests` job (where bash is native).

## Deviations

- **The `confirm` parameter was retained, not removed.** Dropping it would have rewritten ~30 call sites that pass a 3rd positional argument; the value is now unused and annotated instead (minimal-diff, signature-stable).
- **`--platforms` gates the per-provider blocks and per-provider permissions, but not the genuinely cross-cutting tail** (VS Code extension, skill discovery, git commit-msg hook). Those are best-effort detect-and-skip installers; precise platform-scoping of them is unnecessary for the gate and would widen the diff.

## Known gaps / pre-existing issues surfaced (not fixed -- out of Phase 2 scope)

- **Personal-path leak in an unrelated doc.** `docs/v3/v3.8/comparisons/v3.8.0-comparison-ralph-claude-code.md:265` contained a `C:\Users\<user>` leak (committed in `51081c8`, a separate comparison doc), which fails the `validate_no_personal_paths` gate. It must be redacted before the v3.7.0 release. NOT touched here -- every changed line traces to Phase 2 (redacted in Phase 5).
- **Diff-based conflict false-positive on version bumps.** Without last-written-hash tracking on the bash path, an INTERACTIVE upgrade where Nexus (not the user) changed a hook flags it as a conflict. Accepted as the explicit "Diff + refresh-on-yes" tradeoff: the common non-interactive / `nexus-hub upgrade` path refreshes silently, and only a hand-run installer in a TTY sees the (one) prompt.
- `docs/v3/v3.7/known-gaps.md` is created in Phase 5 (sub-task 5.2); these two items should land there. Carried-forward constraints: WN-v36-1 and WN-v33-1.

## Next steps

- **Phase 3 -- `nexus-hub upgrade` checker (un-defers N4).** Ship a `nexus-hub` CLI on PATH whose `upgrade` subcommand compares installed vs latest, shows a what's-new summary, and re-runs the bootstrap. The Phase 2 non-interactive refresh path is what `upgrade` will invoke.
- **CI confirmation.** Push `feat/installer-bootstrap` and confirm the `tests` job is green on ubuntu (where the 11 bash-functional Phase 2 tests actually run) before relying on the bash conflict-behavior claim.
- **Before release (Phase 5):** redact the personal-path leak in `comparison-ralph-claude-code.md` so the `validate_no_personal_paths` gate is green.
