# Session History -- v3.7.0 install-ux-overhaul Phase 1: self-fetching bootstrap + dependency prechecks

**Date**: 2026-06-17
**Plan**: [`docs/releases/v3/v3.7/plans/install-ux-overhaul.md`](../../plans/install-ux-overhaul.md)
**Phase**: 1 of 5 -- Self-fetching bootstrap + dependency prechecks
**Branch**: `feat/installer-bootstrap` (off `develop`)
**Outcome**: complete. All three sub-tasks (1.1 contract, 1.2 implementation, 1.3 tests/stabilization) closed; every locally-runnable Stability Gate item is green and the bash end-to-end gate is wired into CI (authoritative under WN-v36-1).

## Goal

Make the repo-root `install.sh` and a new `install.ps1` dual-mode so a clean machine can install Nexus-Hub with a single piped command -- `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` (macOS/Linux) and `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex` (Windows) -- with dependency prechecks that fail fast and clearly, while the existing in-repo clone-and-run workflow keeps working unchanged. The only outbound call is to the project's own GitHub; no new dependency, credential, or third-party processor.

## Subtasks completed

1. **1.1 -- Specify the bootstrap contract and precheck list.** Read `install.sh`, `install.bat`, `scripts/installer.sh`, `scripts/installer.ps1` and recorded the findings as "Appendix A -- Phase 1 working notes (bootstrap contract)" in the plan. Key finding: the core installers already run correctly from *any* complete checkout tree (this is exactly what `--branch` relies on -- it re-execs the core installer from a clone under `~/.nexus-hub/branches/`), so the bootstrap only has to *materialize* such a tree and hand off; no change to the core installers was needed. Documented the in-repo-vs-standalone detection, the required-tool precheck list per OS, the tarball fetch URL + `~/.nexus-hub/src` extract target, and the internal testing env-var seams.
2. **1.2 -- Implement the dual-mode bootstrap.** Rewrote `install.sh` (`#!/usr/bin/env bash`, `set -euo pipefail`) and created `install.ps1`. Detection is filesystem-based: resolve the script's own dir and check for a sibling `scripts/installer.{sh,ps1}`; if present, in-repo (delegate as before); otherwise standalone. Standalone path: precheck a downloader (`curl`/`wget` or `Invoke-WebRequest`), an extractor (`tar`/`Expand-Archive`), and a Python interpreter; download the `main` tarball from the project's own GitHub; extract (bash `tar --strip-components=1`; PowerShell `tar` or `Expand-Archive`-then-flatten) to `~/.nexus-hub/src` (wiped + recreated for idempotence); then `exec`/invoke the extracted core installer with all args passed through. The bash precheck is builtins-only (`command -v`, `printf`, `$OSTYPE`) so it reports cleanly even with an empty PATH. `install.bat` was left pointing at `scripts/installer.ps1` (the in-repo path still works); the new `install.ps1` is the `irm|iex` target.
3. **1.3 -- Testing and stabilization.** Added `tests/installer/test_bootstrap.py` (static surface, precheck-only success, missing-tool failure, standalone extract + hand-off with arg passthrough, in-repo delegation, and a "no new outbound host" assertion). Added a CI `bootstrap` job to `.github/workflows/ci.yml` that runs the bash standalone install end-to-end on ubuntu against a `git archive` tarball of the checkout, asserts the missing-tool path exits non-zero with a clear message, and AST-parses + precheck-runs `install.ps1` via `pwsh`. Added the `[Unreleased]` CHANGELOG entry. Ran every locally-available gate green.

## Key decisions

- **The bootstrap lives in the root entry points, not the core installers.** `scripts/installer.{sh,ps1}` are unchanged. The root `install.sh` / `install.ps1` are the only files that gained dual-mode logic, because they are the curl/irm targets and the core installers already work from any checkout tree.
- **Filesystem detection over a `--standalone` flag.** A piped script has no on-disk dir (`BASH_SOURCE[0]` empty / `$PSScriptRoot` empty), so "is there a sibling `scripts/installer.*`?" cleanly distinguishes the two modes and degrades correctly for the one case we cannot control (stdin). `NEXUS_HUB_FORCE_STANDALONE=1` forces standalone for testing.
- **Builtins-only bash precheck.** Using only `command -v`/`printf`/`$OSTYPE` (no external `uname`) makes "simulate a missing tool" a one-liner (`PATH='' ... install.sh`) and guarantees a clean error message even when nothing is on PATH. `resolve_script_dir` is made `set -e`-safe (`... || return 0` / trailing `|| true`) so a benign resolution failure never aborts the script.
- **Env-var seams for network-free CI.** `NEXUS_HUB_TARBALL` (local path or URL), `NEXUS_HUB_SRC`, `NEXUS_HUB_REF`, `NEXUS_HUB_REPO`, `NEXUS_HUB_FORCE_STANDALONE`, `NEXUS_HUB_PRECHECK_ONLY` let CI and pytest exercise the real download/extract/exec path deterministically with zero network dependency.
- **Tarball, not `git clone`.** Per the plan's design defaults: no `git` dependency on the user's machine, smaller surface. Windows falls back to the `.zip` archive when only `Expand-Archive` is available.
- **No project version bump and no `data/` edits.** Phase 1 adds no skill/command; the version surfaces stay at canonical 3.6.0 (the v3.7.0 tag is cut by `/update release` in Phase 5).

## Troubleshooting

- **bash functional tests ran the real installer on the Windows host.** First test run, the four bash functional tests invoked the full interactive `scripts/installer.sh` (the `Select [G/W]` and `Install Node.js?` prompts appeared) and a `UnicodeDecodeError` surfaced in the subprocess reader. Root cause: `shutil.which("bash")` on this host resolves to the WSL launcher (`C:\Windows\System32\bash.exe`), which translates the CWD and does **not** forward arbitrary Windows env vars across the WSL boundary -- so `NEXUS_HUB_FORCE_STANDALONE` was not honored and the in-repo path ran. This is exactly WN-v36-1. Fix: skip the bash functional tests on `win32` (citing WN-v36-1) and let CI (ubuntu, native bash) be authoritative; also pinned `encoding="utf-8", errors="replace"` on all `subprocess.run` calls so ANSI/banner bytes never trip the cp1252 default decoder. After the fix: 5 passed, 4 skipped in 1.31s.

## Test results

`make`/ShellCheck are not on PATH on this Windows host (WN-v33-1); gates were emulated by invoking the tools directly. The bash end-to-end install is verified on CI (WN-v36-1), not locally.

- `bash -n install.sh`: clean. ShellCheck (`--severity=warning install.sh`): clean (shellcheck was available locally this session).
- `install.ps1` PowerShell AST parse: clean. Standalone extract + hand-off + arg passthrough verified locally under Windows PowerShell 5.1 (the target version) against a stub tarball; precheck-only success verified.
- `tests/installer/test_bootstrap.py`: 5 passed, 4 skipped (bash functional tests skip on Windows per WN-v36-1).
- `validate_workflow_security.py` (ci.yml touched): OK. `ci.yml` YAML parse: OK.
- `validate_unicode_safety.py`: 0 errors (1051 pre-existing warnings in other files; none in this phase's files). `validate_no_personal_paths.py`: exit 0.
- `check_version_sync.py`: all six surfaces match canonical 3.6.0. `check_base_template_parity.py`: 5/5 present (no template changed).

## CI/CD edits

Added a new `bootstrap` job to `.github/workflows/ci.yml` (ubuntu): builds a GitHub-shaped tarball with `git archive --prefix=Nexus-Hub-main/`, runs the bash standalone bootstrap end-to-end (asserting a populated `~/.nexus-hub/`), runs the missing-tool simulation (asserting non-zero exit + a curl/wget message), and AST-parses + precheck-runs `install.ps1` via `pwsh`. The new `tests/installer/test_bootstrap.py` is auto-discovered by the existing `pytest tests/installer` step. `install.sh` was already in the shellcheck job's lint set. No installer copy-step edit was needed -- the root entry points are not distributed artifacts.

## Deviations

- **`install.bat` left unchanged.** It still delegates to `scripts/installer.ps1` (the in-repo path); the new `install.ps1` is purely the `irm|iex` bootstrap target. Changing `.bat` was out of scope and would add risk for no benefit.
- **bash end-to-end not run locally.** Per WN-v36-1 the bash path is CI-authoritative; the CI `bootstrap` job is the gate. The Mac `curl|bash` smoke test remains a Phase 5 manual checklist item.

## Known gaps

No new gaps introduced. `docs/v3/v3.7/known-gaps.md` is created in Phase 5 (sub-task 5.2). Carried-forward constraints: WN-v36-1 (bash not fully runnable on the Windows dev host -- bash path verified on CI + a Phase 5 Mac smoke test) and WN-v33-1 (local `make`/ShellCheck not always on PATH -- validators run directly).

## Next steps

- **Phase 2 -- No-prompt all-platform install + conflict-only overwrite.** Remove the `Select [G/W]` and platform-selection prompts; default to a global install across all supported platforms (absent ones skip-with-note); keep marker-merge but prompt only on a detected real overwrite conflict; add `--workspace` / `--platforms` / `--yes`. The bootstrap from this phase will drive that flow.
- **CI confirmation.** Push `feat/installer-bootstrap` and confirm the new `bootstrap` job is green on ubuntu before relying on the bash end-to-end claim (the local host cannot run it -- WN-v36-1).
