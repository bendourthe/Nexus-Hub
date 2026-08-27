# Session History -- v3.7.0 install-ux-overhaul Phase 3: `nexus-hub upgrade` checker + CLI on PATH

**Date**: 2026-06-17
**Plan**: [`docs/releases/v3/v3.7/plans/install-ux-overhaul.md`](../../plans/install-ux-overhaul.md)
**Phase**: 3 of 5 -- `nexus-hub upgrade` checker (un-defers N4 / DF-v36-1)
**Branch**: `feat/installer-bootstrap` (off `develop`)
**Outcome**: complete. All three sub-tasks (3.1 CLI on PATH, 3.2 `upgrade` subcommand, 3.3 un-defer N4 + tests) closed; every locally-runnable Stability Gate item is green and the CLI suite is wired into the existing CI `pytest tests/installer` step (authoritative under WN-v36-1).

## Goal

Ship a `nexus-hub` CLI on PATH whose `upgrade` subcommand compares the installed version against the latest on the project's own GitHub, shows a what's-new summary, and offers an in-place upgrade (re-running the Phase 1 bootstrap). Un-defer N4 (deferred low-ROI in v3.6.0 as DF-v36-1; reprioritized for the install-UX overhaul). The version check is the only new outbound call and it targets the project's own GitHub; no new dependency, credential, or third-party processor.

## Model-routing pre-flight

The plan recommends a strong reasoning tier at high effort for Phase 3 (new outbound version check; idempotent re-install). The session is on Opus 4.8 (strongest tier) at high effort, so the re-confirmation agreed with the plan and no switch was applied.

## Architecture decision

A stdlib-only Python CLI core (`scripts/nexus_hub_cli.py`, the NI-v24-1 single-`.py`-no-`.ps1` convention) behind thin native launchers (`scripts/nexus-hub` POSIX, `scripts/nexus-hub.cmd` Windows). Two forces drove the choice over pure shell:

1. The core installers already run from any complete tree (plan Appendix A), so `upgrade` only has to re-invoke the Phase 1 bootstrap rather than add new installer plumbing.
2. Bash cannot be fully run on the Windows dev host (WN-v36-1: a space in the checkout path). A Python core is directly pytest-able on every platform; a pure-shell upgrade would be near-untestable locally.

## Subtasks completed

1. **3.1 -- CLI on PATH.** Both installers gained `install_cli_launcher` / `Install-CliLauncher`, called right after templates. Each writes `~/.nexus-hub/VERSION` from the canonical version constant (bash `printf`; PS `Set-Content -Encoding ascii -NoNewline`, no BOM), copies `nexus_hub_cli.py` into `~/.nexus-hub/scripts/` (registered by name in BOTH installers per the installer-aware rule), installs the launcher into `~/.nexus-hub/bin/` (POSIX shim chmod +x; Windows `.cmd`), and prints a best-effort PATH hint. `--version` reads the VERSION marker (BOM-tolerant via utf-8-sig) with a plugin.json fallback for a standalone tree.
2. **3.2 -- `upgrade` subcommand.** Reads the installed version, fetches the latest `.claude-plugin/plugin.json` version and the matching `CHANGELOG.md` block from the project's own GitHub (a `fetch_text` helper preferring `curl`, falling back to `wget`, then stdlib `urllib`; a `file://` source is read directly), compares semver numerically, and prints up-to-date / behind+what's-new. On confirmation it re-runs the Phase 1 bootstrap (`curl|bash` / `irm|iex`); offline / fetch-failure returns a clear message + non-zero exit with no partial state. `--yes` and a `NEXUS_HUB_UPGRADE_DRY_RUN` seam support non-interactive and test use.
3. **3.3 -- Un-defer N4 + tests.** The reverse-engineering matrix gained an "Adopted in v3.7.0" row (upstream `specify self upgrade` named only in the Rationale column per the Attribution Rule); `docs/v3/v3.6/known-gaps.md` moved DF-v36-1 to Resolved with the summary counts updated. `tests/installer/test_upgrade_cli.py` (24 cases) imports the CLI core and drives it as a subprocess against a local `file://` fixture via env seams. Added the `[Unreleased]` CHANGELOG entry.

## Key decisions

- **Python CLI core + thin native launchers**, not pure shell -- for cross-platform testability under WN-v36-1 and because the heavy logic (semver compare, JSON parse, CHANGELOG extraction) is far cleaner in one stdlib `.py` than in two parallel shell scripts.
- **The VERSION marker is deliberately NOT a `check_version_sync` surface.** It is written from the canonical `NEXUS_HUB_VERSION` / `$script:NexusHubVersion` and never hand-edited, so adding it to the guard would only create a redundant 7th surface; the CLI reads the version dynamically rather than hardcoding any semver.
- **PATH wiring is print-only; it NEVER auto-edits a shell rc file or the user's PATH.** Phase 2 made installs no-prompt, and a no-prompt install must not silently mutate the environment. The hint prints the exact line to add plus a direct-run fallback. (The Windows hint uses the safe user-PATH append, not `setx PATH "...;%PATH%"`, which can truncate/corrupt PATH.)
- **`upgrade` re-runs the existing bootstrap** rather than re-implementing fetch/extract/install -- the bootstrap is already idempotent and re-runnable (plan design default 3), so the upgrade is one outbound call to check + a bootstrap re-run, no new install plumbing.
- **No project version bump and no `data/` edits.** Phase 3 adds no skill/command; version surfaces stay at canonical 3.6.0 (the v3.7.0 tag is cut by `/update release` in Phase 5).

## Troubleshooting

- **ShellCheck SC2088 on an intentional display-only tilde.** The PATH-hint stores `~/.zshrc` / `~/.bashrc` as literal text to show the user; ShellCheck flagged "tilde does not expand in quotes". Resolution: a scoped `# shellcheck disable=SC2088` with a comment explaining it is display text, not a path -- the literal tilde is the intended output. ShellCheck clean afterward.
- **Potential BOM in the PowerShell-written VERSION file.** PowerShell 5.1 `Set-Content -Encoding utf8` writes a BOM; a leading BOM survives `str.strip()` and would corrupt `--version`. Resolution: write the marker as `-Encoding ascii -NoNewline` (the version is pure-ASCII semver, no BOM) AND read it with `utf-8-sig` in the CLI defensively, so either side is robust.

## Test results

`make` is not on PATH on this Windows host (WN-v33-1); gates were emulated by invoking the tools directly. The bash end-to-end behavior is CI-authoritative (WN-v36-1).

- `tests/installer/test_upgrade_cli.py`: **24/24 passed** (version reading incl. BOM + plugin.json fallback + unknown; numeric semver compare; CHANGELOG exact + Unreleased-skipping fallback; `file://` fetch + offline FetchError; upgrade end-to-end up-to-date / behind+skip / behind+confirmed-dry-run / offline; no-outbound-beyond-GitHub; both installers' launcher wiring). Runs entirely on the Python interpreter -- no bash, so WN-v36-1 does not bite.
- `catalog/hooks/tests/test_installer_smoke.py`: 51/52. The lone failure is `test_installer_sh_bash_syntax_clean`, which invokes WSL `bash.EXE` and returns 127 on the space-containing checkout path (WN-v36-1). `bash -n scripts/installer.sh` is independently clean via Git Bash; the script-coverage guard (`nexus_hub_cli.py` in both installers) and the PS AST parse both pass.
- `tests/validators`: 199/200. The lone failure is the pre-existing `test_session_query_extract.py::test_discover_obsidian_vault_marker` -- the same WN-v36-1 WSL-bash-space-path class, untouched by this phase.
- `shellcheck --severity=warning scripts/installer.sh install.sh scripts/nexus-hub`: clean. `bash -n` clean on all three. `python -m py_compile scripts/nexus_hub_cli.py`: clean. `installer.ps1` AST parse: clean.
- `check_version_sync.py`: all surfaces match canonical 3.6.0. `validate_unicode_safety.py`: 0 errors. Bundle-audit / base-template-parity / workflow-security / supply-chain-IOC validators: all exit 0.
- Live smoke: `nexus-hub --version` -> `nexus-hub 3.6.0` (reads the VERSION marker); `nexus-hub --help` shows the `version` / `upgrade` subcommands.

## CI/CD edits

None needed. CI already runs `pytest tests/installer` and lints `scripts/installer.sh install.sh`, so the new CLI test file and installer edits are picked up automatically. The Phase 5 CI matrix will exercise the bootstrap (and `nexus-hub --version`) end-to-end on real runners.

## Known gaps / pre-existing issues surfaced (not fixed -- out of Phase 3 scope)

- **`validate_no_personal_paths` is red on 3 PRE-EXISTING `C:\Users\<name>` leaks** committed in Phase 1/2 docs: `docs/DEVLOG.md` (the Phase 2 entry that quotes the leak path), `docs/v3/v3.8/comparisons/v3.8.0-comparison-ralph-claude-code.md:265`, and `docs/archive/v3/v3.7/development/history/2026-06-17_install-ux-overhaul-phase-2-no-prompt-install.md:62`. The check was green at v3.6.0 (WN-v33-1 evidence), so this is a v3.7.0 regression introduced before Phase 3. None of the 3 files is in the Phase 3 diff; they should be redacted in Phase 5 (sub-task 5.2) before the release. (This history file uses `<name>` placeholders so it adds no new leak.)
- `docs/v3/v3.7/known-gaps.md` is created in Phase 5 (sub-task 5.2); the personal-path-redaction item should land there. Carried-forward constraints: WN-v36-1 and WN-v33-1.

## Next steps

- **Phase 4 -- Interactive guide + docs redesign.** Rewrite the guide's Setup page around "open a terminal" + the one-line `curl|bash` / `irm|iex` command (with the `wget` fallback and copy buttons), drop the download/unzip/`cd` instructions, and add a one-line `nexus-hub upgrade` mention to the README Quick Start.
- **CI confirmation.** Push `feat/installer-bootstrap` and confirm the `tests` job is green on ubuntu.
- **Before release (Phase 5):** redact the 3 personal-path leaks so `validate_no_personal_paths` is green, and create `docs/v3/v3.7/known-gaps.md`.
