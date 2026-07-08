# Plan -- Install-UX Overhaul (v3.7.0)

**Project**: Nexus-Hub
**Version**: v3.7.0
**Slug**: install-ux-overhaul
**Plan Type**: Feature / Enhancement (installer + interactive guide)
**Created**: 2026-06-17
**Goal anchor (memory)**: `nexus-hub-v37-installer-ux`
**Goal**: Make Nexus-Hub installable and upgradable with a single copy-paste terminal command on macOS, Linux, and Windows -- no download, no unzip, no `cd` -- with robust dependency prechecks, an all-platform no-prompt install, conflict-only overwrite confirmation, and a built-in upgrade checker. No paid code-signing; no new third-party data processor (the only outbound calls are to the project's own GitHub, the same posture the installer already has).

## Overview

Today the install path is "download the repo, unzip, open a terminal, `cd` into the folder, run `./install.sh`". That is too much friction for non-technical users, and the interactive guide currently over-promises (it implies double-clicking `install.sh` works on macOS/Linux, which Finder/most file managers do not do). The v3.6.0 Spec Kit re-comparison deferred a self-upgrade CLI (N4 / DF-v36-1) as low-ROI; the maintainer has since reprioritized it as part of a single coherent install-UX overhaul.

The target experience is the industry-standard one-line bootstrap (Homebrew / rustup / uv pattern): the user opens a terminal and pastes ONE command that downloads the catalog and installs it. This is the cleanest path that needs **no paid code-signing** (it sidesteps Gatekeeper/SmartScreen entirely, since nothing downloaded is double-clicked). The same mechanism powers a `nexus-hub upgrade` checker.

The work is sequenced crux-first: the self-fetching bootstrap + dependency prechecks land first (the highest-risk, highest-value slice), then the no-prompt all-platform install flow, then the upgrade checker, then the guide/docs redesign, then cross-platform verification and release. Every outbound call is to the project's own GitHub; no new dependency, credential, or third-party processor is introduced.

**Hard testing constraint (carried from v3.6.0 WN-v36-1)**: bash cannot be fully run on the Windows dev host (the dev checkout path contains a space, and `bash.EXE` mis-resolves it). All bash-path verification therefore leans on CI (ubuntu) plus a manual smoke test on a real Mac. The PowerShell path is AST-checked locally and verified on CI / a Windows runner. No phase may claim "done" on the bootstrap without a green CI run and a recorded Mac smoke test.

## Design defaults (assumptions -- adjust before Phase 1 if any are wrong)

These are defaulted from the maintainer's stated requirements plus standard practice. They are called out so they can be corrected before implementation rather than discovered mid-build.

1. **Fetch source = `main`.** The bootstrap downloads from `https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/...` and the catalog tarball from the `main` branch. Rationale: `main` is the installable branch (only release merges land there), so it always equals the latest tagged release; this avoids per-release URL churn in the guide. The upgrade checker compares the installed version against `main`'s `.claude-plugin/plugin.json`.
2. **Fetch mechanism = tarball, not `git clone`.** Download `https://github.com/bendourthe/Nexus-Hub/archive/refs/heads/main.tar.gz` (curl, with a `wget` fallback) and extract with `tar`. Rationale: no `git` dependency required on the user's machine; smaller surface than a clone.
3. **Catalog source lands in `~/.nexus-hub/src`** (then the existing installer runs from there and writes to `~/.nexus-hub/` and the per-platform locations as today). The bootstrap is idempotent and re-runnable (this is also what `nexus-hub upgrade` invokes).
4. **`nexus-hub` CLI installed to `~/.nexus-hub/bin/nexus-hub`** with a PATH hint printed on first install (and best-effort shell-rc append behind a confirmation). Subcommands: `nexus-hub upgrade` (and `--version`).
5. **Default scope = global, all platforms, no prompts.** `--workspace <path>`, `--platforms <list>`, and `--yes` flags remain for power users / non-interactive CI. Absent platforms skip-with-note (the `IntegrationBase` subclasses already do this).
6. **Branch**: `feat/installer-bootstrap` off `develop`; integrate back to `develop`; release to `main` at the end (develop+main model).

## Constitution Check

*GATE: informational only.*

No constitution file found at docs/v3/v3.7/constitution.md (nor docs/constitution.md) -- skipping, same as v3.6.0. The governing principle remains the MCP Registry Policy (reverse-engineer-first; no third-party data processor). This plan honors it: the only outbound calls are to the project's own GitHub (installer/upgrader fetch), introducing no new third-party processor, credential, or dependency. `curl | bash` runs the project's own script from the project's own repo -- the standard, audited bootstrap posture.

## Definition of Done (observable)

- [ ] `curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash` installs Nexus-Hub on a clean macOS/Linux machine with no prior clone (verified on CI ubuntu + a Mac smoke test).
- [ ] `irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex` installs on Windows PowerShell with no prior clone.
- [ ] Running any install command with a missing required tool prints a clear, actionable message (what is missing + how to install it) and exits non-zero -- never a cryptic failure. A curl-less Linux box is offered the `wget` variant.
- [ ] Install configures ALL supported platforms with no global/repo or platform prompts; absent platforms skip-with-note; `--workspace` / `--platforms` / `--yes` flags still work.
- [ ] Re-install preserves user edits (marker-merge) and prompts only when real overwrite conflicts are detected, naming the files.
- [ ] `nexus-hub upgrade` reports installed vs latest, shows a short what's-new summary, and offers to upgrade (re-running the bootstrap).
- [ ] The interactive guide's Setup page leads with "open a terminal" (per-OS how-to) + the single command (with the wget fallback), and no longer instructs download/unzip/cd.
- [ ] `make validate && make lint && make test` green; the bootstrap verified by a CI job and a recorded Mac smoke test.
- [ ] No new outbound call beyond the project's own GitHub; no new dependency, credential, or third-party processor.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Self-fetching bootstrap + dependency prechecks | `install.sh` / `install.ps1` become dual-mode (in-repo or standalone curl/irm); precheck tools and fail gracefully; download + extract + run installer | Strong reasoning tier, high effort (cross-platform shell, network path, hard to test locally) |
| 2 | No-prompt all-platform install + conflict-only overwrite | Remove scope/platform prompts; default global + all platforms (absent skip-with-note); marker-merge retained; prompt once only on detected conflicts; `--workspace`/`--platforms`/`--yes` flags | Strong reasoning tier, high effort (installer control-flow change, ask-first area) |
| 3 | `nexus-hub upgrade` checker (un-defers N4) | `nexus-hub` CLI on PATH; compares installed vs latest, shows what's-new, offers upgrade; matrix + known-gaps updated to un-defer N4 | Strong reasoning tier, high effort (new outbound version check; idempotent re-install) |
| 4 | Interactive guide + docs redesign | Setup page leads with per-OS terminal + one command (+ wget fallback, copy buttons); README Quick Start + AGENTS installer docs rewritten | Strong reasoning tier, medium effort (docs; reuse the v3.6.0 copy-button system) |
| 5 | Cross-platform verification + release | CI matrix runs the bootstrap end-to-end; recorded Mac smoke test; full validate/lint/test; then `/update release` for v3.7.0 | Strong reasoning tier, high effort (release gate hinges on real cross-platform proof) |

Live model enumeration was not performed at planning time; recommendations are platform-agnostic tier intent plus the current session model (Opus 4.8) and will be re-confirmed by `/implement` per phase. Phases 1-3 and 5 default to high effort under the no-degradation guarantee (cross-platform installer code, a network bootstrap, and a release gate that depends on real-machine verification are all high-risk).

---

## Phase 1: Self-fetching bootstrap + dependency prechecks

**Goal**: Make `install.sh` and `install.ps1` dual-mode so `curl -fsSL .../install.sh | bash` and `irm .../install.ps1 | iex` work from a clean machine, with dependency prechecks that fail gracefully.
**Prerequisites**: None.
**Stability Gate**: A CI ubuntu job runs the standalone bootstrap end-to-end (no pre-existing clone) and lands a working `~/.nexus-hub/`; a missing-tool simulation exits non-zero with a clear message; the PowerShell path passes AST + a standalone run on a Windows/CI runner; `bash -n` / PSScriptAnalyzer clean.

### Sub-tasks

#### 1.1 -- Specify the bootstrap contract and precheck list

**Prompt**:
> Read the current `install.sh`, `install.bat`, `scripts/installer.sh`, and `scripts/installer.ps1`. Document (in the plan's working notes) exactly how the installer is invoked today and what it assumes about CWD / repo presence. Define the standalone-mode contract: (a) detect in-repo vs standalone (e.g., presence of `./scripts/installer.sh` next to the script); (b) the required-tool precheck list per OS (macOS/Linux: a downloader -- `curl` OR `wget` -- plus `tar`, and the installer's own deps such as `python3`; Windows: PowerShell 5.1+, `tar` or `Expand-Archive`); (c) the exact fetch URL (`main` tarball) and extract target (`~/.nexus-hub/src`). Note the WN-v36-1 testing constraint.

#### 1.2 -- Implement the dual-mode bootstrap

**Prompt**:
> Rewrite `install.sh` to be dual-mode: if run inside the repo, behave as today; if run standalone (piped via `curl|bash`), first run the dependency precheck (fail with a clear "missing X -- install with Y" message and non-zero exit if a required tool is absent; prefer `curl`, fall back to `wget`), then download the `main` tarball, extract to `~/.nexus-hub/src`, and exec the extracted `scripts/installer.sh` passing through any args. Mirror the same logic in `install.ps1` for the `irm|iex` path (precheck PowerShell version + extraction tool, download via `Invoke-WebRequest`, extract, run `scripts/installer.ps1`). Keep both POSIX-safe / PS 5.1-safe. Follow the bash safety rules (`set -euo pipefail`, errors to stderr) and the PowerShell conventions. Do NOT remove the in-repo path (the existing clone-and-run workflow must keep working). These are installer entry points (AGENTS.md ask-first area) -- keep the diff focused and reviewable.

#### 1.3 -- Testing and stabilization

**Prompt**:
> Add a CI job (in `.github/workflows/ci.yml`) that exercises the standalone bootstrap on ubuntu end-to-end against the checked-out tree (simulate `curl|bash` by running `bash install.sh` from a temp dir with no repo, pointing the fetch at the local tree or a test tarball), asserting `~/.nexus-hub/` is populated. Add a missing-tool test (PATH-shadow `curl`/`wget`/`tar`) asserting a non-zero exit + clear message. Add a pytest/static check for the precheck logic where feasible. Verify `bash -n install.sh` and PowerShell AST parse of `install.ps1` are clean locally. Record the Mac smoke-test step as a manual checklist item (WN-v36-1). Run `make validate` / `make lint`. Then `/generate-session-history`.

---

## Phase 2: No-prompt all-platform install + conflict-only overwrite

**Goal**: Remove the interactive global/repo + platform-selection prompts; default to a global install of all supported platforms (absent ones skip-with-note); keep marker-merge but prompt only when a real overwrite conflict is detected.
**Prerequisites**: None (independent of Phase 1, but sequenced after so the bootstrap exists to exercise it).
**Stability Gate**: A non-interactive install (no stdin) completes with no prompts and configures all detected/known platforms; absent platforms skip-with-note (no error); a re-install over a user-modified managed file triggers exactly one conflict prompt listing the file; `--workspace` / `--platforms` / `--yes` flags behave; tests cover the no-prompt path and the conflict-detection branch.

### Sub-tasks

#### 2.1 -- Remove scope/platform prompts; default global + all platforms

**Prompt**:
> In `scripts/installer.sh` and `scripts/installer.ps1`, replace the interactive scope (`Select [G/W]`) and platform-selection prompts with: default = global install across ALL supported platforms, no prompt. Absent platforms must skip-with-note (reuse the existing IntegrationBase skip behavior). Add/confirm `--workspace <path>` (workspace install), `--platforms <comma-list>` (subset), and `--yes`/non-interactive flags for power users and CI. Preserve all existing install logic (hooks, settings.json merge, per-platform files); only the prompting/branching changes. Keep the legacy migration prompt behavior decision explicit.

#### 2.2 -- Conflict-only overwrite confirmation

**Prompt**:
> Keep marker-merge as the write mechanism (user edits outside Nexus-Hub markers always survive). Replace the per-file `Overwrite? [Y/N/A]` prompt with conflict-only behavior: detect the set of managed files whose on-disk content Nexus-Hub would overwrite OUTSIDE its managed markers (i.e., a real user customization at risk), and if any exist, print the list and ask once for confirmation; if none, proceed silently. Under `--yes`, default to the safe action (merge, never clobber) and report. Add tests for the no-conflict (silent) path and the conflict (single prompt, files listed) path.

#### 2.3 -- Testing and stabilization

**Prompt**:
> Add tests (pytest + the installer smoke patterns) covering: a fully non-interactive install produces no prompt and configures all platforms; an absent platform skips-with-note (no error); a re-install over a user-edited managed file raises exactly one conflict prompt naming the file; `--workspace` / `--platforms` / `--yes` are honored. Run `make test` / `make validate` / `make lint`; verify the bootstrap from Phase 1 still drives this flow. Then `/generate-session-history`.

---

## Phase 3: `nexus-hub upgrade` checker (un-defers N4 / DF-v36-1)

**Goal**: Ship a `nexus-hub` CLI on PATH whose `upgrade` subcommand compares the installed version against the latest on GitHub, shows a what's-new summary, and offers to upgrade in place.
**Prerequisites**: Phase 1 (the bootstrap is what `upgrade` re-runs).
**Stability Gate**: `nexus-hub --version` reports the installed version; `nexus-hub upgrade` correctly detects up-to-date vs behind against a fixture/live `main` `plugin.json`, prints CHANGELOG highlights when behind, and on confirmation re-runs the bootstrap; the version check is the only new outbound call and it targets the project's own GitHub; the matrix + known-gaps are updated to un-defer N4.

### Sub-tasks

#### 3.1 -- Install a `nexus-hub` CLI on PATH

**Prompt**:
> Have the installer write a small `nexus-hub` launcher to `~/.nexus-hub/bin/nexus-hub` (POSIX) and a `.ps1`/`.cmd` shim for Windows, and print a clear PATH hint (best-effort, confirmed shell-rc append optional). The launcher dispatches subcommands; implement `--version` (reads the installed `~/.nexus-hub/.../plugin.json` or a written VERSION file) first.

#### 3.2 -- `upgrade` subcommand

**Prompt**:
> Implement `nexus-hub upgrade`: read the installed version, fetch the latest `.claude-plugin/plugin.json` version and the top CHANGELOG section from `raw.githubusercontent.com/bendourthe/Nexus-Hub/main/...` (one outbound call to the project's own GitHub -- prefer `curl`, fall back to `wget`; precheck per Phase 1), compare semver, and: if up-to-date, say so; if behind, print a short what's-new summary (the latest CHANGELOG block) and offer to upgrade (on yes, re-run the bootstrap). Handle offline / fetch-failure gracefully (clear message, non-zero, no partial state). Reinforce in code comments that this is the only new outbound call and it goes to the project's own repo.

#### 3.3 -- Un-defer N4 + testing

**Prompt**:
> Update `docs/policy/mcp-reverse-engineering-matrix.md` and `docs/v3/v3.6/known-gaps.md` DF-v36-1 to reflect that N4 (self-upgrade) is now adopted in v3.7.0 (was deferred low-ROI; reprioritized). Add tests covering: up-to-date detection, behind detection with what's-new output, the offline/fetch-failure path, and a no-new-outbound-beyond-GitHub assertion. Run `make test` / `make validate` / `make lint`. Then `/generate-session-history`.

---

## Phase 4: Interactive guide + docs redesign

**Goal**: Redesign the guide's Setup page and the README/AGENTS install docs around the one-command flow.
**Prerequisites**: Phases 1-3 (so the documented commands actually work).
**Stability Gate**: The Setup page leads with per-OS "open a terminal" guidance + the single command (with the `wget` fallback and copy buttons via the existing `[data-copy]` system) and no longer instructs download/unzip/cd; README Quick Start and the AGENTS installer-aware section match the new flow; no doc presents the old download-first flow as current.

### Sub-tasks

#### 4.1 -- Setup-page redesign in the interactive guide

**Prompt**:
> Rewrite the Setup page of `guides/interactive-guide/nexus-hub-guide.html`: Step 1 "Open a terminal" with a per-OS how-to (macOS: Spotlight -> Terminal; Windows: Start -> PowerShell; Linux: Ctrl+Alt+T / your terminal). Step 2 "Run one command" -- the `curl|bash` (macOS/Linux, with the `wget` fallback variant) and `irm|iex` (Windows) commands, each with a copy-to-clipboard button via the existing `[data-copy]` injector. Remove the download/unzip/`cd` instructions and the misleading "double-click install.sh" claim. Keep the "three questions" mockup only if still accurate after Phase 2 (it is not -- update it to reflect the no-prompt flow and the conflict-only confirmation). Refresh the banner version to v3.7.0.

#### 4.2 -- README + AGENTS install docs

**Prompt**:
> Rewrite the README "Quick Start" to the one-command flow (open terminal -> paste command), with the wget fallback and a one-line `nexus-hub upgrade` mention. Update the AGENTS.md installer-aware-changes section if the bootstrap changes any distribution assumptions. Keep counts and version handled by the `version` step at release. ASCII-only, Markdown style guide.

#### 4.3 -- Testing and stabilization

**Prompt**:
> Verify the guide HTML is well-formed (tag balance, the new `[data-copy]` blocks get copy buttons, no broken anchors) and unicode-safe (ASCII-only). Run `make validate` / `make lint`. Confirm no doc still shows the download-first flow as current. Then `/generate-session-history`.

---

## Phase 5: Cross-platform verification + release readiness

**Goal**: Prove the bootstrap works on real platforms, then ship v3.7.0.
**Prerequisites**: Phases 1-4 complete.
**Stability Gate**: A CI matrix runs the bootstrap end-to-end on at least ubuntu (and macOS/Windows runners if available); a Mac manual smoke test is recorded; full `make validate && make lint && make test` green; then `/update release` ships v3.7.0.

### Sub-tasks

#### 5.1 -- CI matrix + Mac smoke test

**Prompt**:
> Extend CI to run the standalone bootstrap end-to-end on ubuntu (and macOS / Windows runners if available on the plan), asserting a populated `~/.nexus-hub/` and a working `nexus-hub --version`. Record a manual Mac smoke-test checklist (run the real `curl|bash` one-liner on a Mac, confirm install + `nexus-hub upgrade`), since bash cannot be fully run on the Windows dev host (WN-v36-1). Capture results.

#### 5.2 -- Known-gaps + release readiness

**Prompt**:
> Create `docs/v3/v3.7/known-gaps.md` for any deferred items / warnings. Resolve open items, then run `/update release` for v3.7.0 (docs + devlog + gitignore + version bump 3.6.0 -> 3.7.0 + changelog + commit + tag + push, with its own confirmation gates). Never tag or push without confirmation.

#### 5.3 -- Testing and stabilization

**Prompt**:
> Final full gate: `make validate && make lint && make test` green (run via direct equivalents on the Windows host per WN-v33-1; CI authoritative for the bash bootstrap). Confirm DoD items all checked. Then `/generate-session-history` for Phase 5 and the v3.7.0 overhaul as a whole.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none -- no constitution file; no violations) | | |

---

### Phase Exit Checklists

Each phase: all sub-tasks done; the phase Stability Gate met; `make validate` / `make lint` / (where relevant) `make test` green via the documented direct equivalents; the bootstrap/installer changes verified on CI (authoritative for bash); session history generated; no new outbound call beyond the project's own GitHub, and no new dependency, credential, or third-party processor.

---

## Appendix A -- Phase 1 working notes (bootstrap contract)

Recorded during sub-task 1.1 from a read of the current `install.sh`, `install.bat`, `scripts/installer.sh`, and `scripts/installer.ps1`.

### How the installer is invoked today

- **`install.sh`** (repo root) -- thin delegate. Resolves its own directory via `${BASH_SOURCE[0]}`, then `exec`s `<dir>/scripts/installer.sh "$@"`. Assumes it lives next to a `scripts/` folder (i.e. inside a checkout). Fails with "Installer script not found" if `scripts/installer.sh` is absent. `set -e` only.
- **`install.bat`** (repo root) -- one line: `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\installer.ps1"`. Same in-repo assumption (`%~dp0` is the .bat's own dir). Not pipeable; cannot be `irm | iex`'d. Left unchanged in Phase 1 (the in-repo Windows path still works through it).
- **`scripts/installer.sh`** -- the core installer. `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`, `REPO_ROOT="$(dirname "$SCRIPT_DIR")"`. Everything it copies is addressed as `$REPO_ROOT/catalog/...`, `$REPO_ROOT/scripts/...`, etc. So **the only thing the core installer needs is to be sitting in a complete checkout tree** -- it does not care about CWD. Flags: `--enterprise`, `--branch <name>` (shallow-clones a pushed branch into `~/.nexus-hub/branches/<token>/` and re-execs with `NEXUS_HUB_BRANCH_RESOLVED=1`), `--print-config <key>`, `--check` / `--dry-run`, `init`, `-h`/`--help`. Interactive scope prompt `Select [G/W]` (EOF on stdin -> empty -> defaults to Global). Python is resolved via `resolve_python_executable` (tries `python3`/`python`/`py`).
- **`scripts/installer.ps1`** -- the Windows core. `$repoRoot = Resolve-Path "$PSScriptRoot\.."`. Same `$RepoRoot\catalog\...` addressing. Mirrors the bash flags as PowerShell params (`-Enterprise`, `-Branch`, `-PrintConfig`, `-Check`, `init`). Same `Select [G/W]` prompt.

**Key consequence**: the core installers already run correctly from *any* complete checkout tree (this is exactly what `--branch` relies on -- it re-execs the core installer from a clone in `~/.nexus-hub/branches/...`). The bootstrap therefore only has to *materialize such a tree* and hand off; no change to the core installers is needed in Phase 1.

### Standalone-mode contract (implemented in Phase 1)

- **In-repo vs standalone detection**: resolve the entry script's own directory; if `<dir>/scripts/installer.{sh,ps1}` exists, run in-repo (today's behavior). Otherwise (including the `curl|bash` / `irm|iex` case where the script is read from stdin and has no on-disk dir), run standalone. `NEXUS_HUB_FORCE_STANDALONE=1` forces standalone for testing.
- **Required-tool precheck (fail fast, non-zero, actionable)**:
    - macOS/Linux: a downloader (`curl` OR `wget`) + `tar` + a Python interpreter (`python3`/`python`/`py`). Prefer `curl`; fall back to `wget`.
    - Windows: PowerShell 5.1+ + an extractor (`tar` OR `Expand-Archive`) + a Python interpreter. Downloader is the built-in `Invoke-WebRequest`.
- **Fetch**: tarball (not `git clone`, so no `git` dependency) from `https://github.com/<repo>/archive/refs/heads/<ref>.tar.gz` (default `<repo>=bendourthe/Nexus-Hub`, `<ref>=main`). Windows falls back to the `.zip` archive when only `Expand-Archive` is available.
- **Extract target**: `~/.nexus-hub/src` (override `NEXUS_HUB_SRC`). The download is GitHub-shaped (single top dir `Nexus-Hub-<ref>/`), so bash uses `tar --strip-components=1`; the destination is wiped and recreated each run so the bootstrap is idempotent and re-runnable (this is also what `nexus-hub upgrade` will invoke in Phase 3).
- **Hand-off**: `exec`/invoke `<src>/scripts/installer.{sh,ps1}` passing through any args.
- **Testing seams (internal env vars)**: `NEXUS_HUB_REF`, `NEXUS_HUB_REPO`, `NEXUS_HUB_TARBALL` (local path or URL -- bypasses URL construction), `NEXUS_HUB_SRC`, `NEXUS_HUB_FORCE_STANDALONE=1`, `NEXUS_HUB_PRECHECK_ONLY=1` (run the precheck then exit, no fetch).

### WN-v36-1 testing constraint (carried forward)

bash cannot be fully run on the Windows dev host (the dev checkout path contains a space and `bash.EXE` mis-resolves it). All bash-path end-to-end verification therefore leans on CI (ubuntu); the PowerShell path is AST-checked locally; a real-Mac smoke test of the `curl|bash` one-liner is a recorded manual checklist item (see Phase 5). `bash -n` / static pytest checks are run locally where the space-in-path does not bite.
