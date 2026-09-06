# Session History -- v3.7.0 install-ux-overhaul Phase 4: interactive guide + docs redesign

**Date**: 2026-06-17
**Plan**: [`docs/releases/v3/v3.7/plans/install-ux-overhaul.md`](../../plans/install-ux-overhaul.md)
**Phase**: 4 of 5 -- Interactive guide + docs redesign
**Branch**: `feat/installer-bootstrap` (off `develop`)
**Outcome**: complete. All three sub-tasks (4.1 guide Setup page, 4.2 README + AGENTS, 4.3 verification) closed; the Stability Gate is met and every locally-runnable validator is green for the changed files.

## Goal

Redesign every user-facing install doc around the v3.7.0 one-line bootstrap shipped in Phases 1-3, so the documentation matches the installer's actual behavior: the Setup page of the interactive guide leads with "open a terminal" + the single command (with the `wget` fallback and copy buttons) and no longer instructs download/unzip/`cd` or "double-click `install.sh`"; the README Quick Start and the AGENTS installer-aware section match the new flow; and no current-facing doc presents the old download-first flow as current. Docs-only -- no new outbound call, dependency, credential, or third-party processor.

## Model-routing pre-flight

The plan recommends a strong reasoning tier at medium effort for this docs phase. The session is on Opus 4.8 (strongest tier), so the re-confirmation agreed with the plan and no switch was applied (no-degradation guarantee).

## Subtasks completed

1. **4.1 -- Setup-page redesign (`guides/interactive-guide/nexus-hub-guide.html`).** Split the single "Launch the installer" step into Step 1 **Open a terminal** (a 3-card per-OS how-to: macOS Spotlight -> Terminal, Windows Start -> PowerShell, Linux Ctrl+Alt+T, using the existing `grid-3` + `.kbd` styles) and Step 2 **Run one command** (two `term--standalone` blocks -- the `curl -fsSL .../install.sh | bash` macOS/Linux command with a `wget -qO-` fallback line, and the `irm .../install.ps1 | iex` Windows command -- each a `[data-copy]` `cmd-line` decorated by the existing copy-button injector, with `overflow-wrap:anywhere` so the long URL wraps inside the flex row). Removed the Download-ZIP/unzip paragraph, the misleading "double-click `install.sh`" claim, and the two old install cards. Replaced the now-false "three quick questions" mockup (the scope / overwrite / providers prompts removed in Phase 2) with a "No questions asked" section: three cards for the no-prompt defaults (global; every detected assistant, absent ones skip-with-note; marker-merge protects edits), a single accurate end-of-run conflict-prompt terminal mockup, and the `--workspace` / `--platforms` / `--yes` power-user flags. Refreshed the banner label (v3.6.0 -> v3.7.0), the welcome line (v3.3.1 -> v3.7.0), and the condensed run-output version (v3.3.4 -> v3.7.0); changed "Keep it current" to lead with `nexus-hub upgrade`; and updated the recap "Getting started" install block to the same one-command form. The two following step badges renumbered (What lands where 2->3, One catalog every platform 3->4) to keep a clean 1-2-3-4 sequence.
2. **4.2 -- README + AGENTS (`README.md`, `AGENTS.md`).** Rewrote the README "Quick Start" from the 5-step clone/double-click/drag-drop flow to the one-command flow: per-OS bootstrap commands in fenced code blocks, the `wget` fallback, a no-prompt explanation, the power-user flags, a "prefer to clone first?" note that the in-repo `./install.sh` / `install.bat` path still works, and a "Keeping it current" subsection leading with `nexus-hub upgrade`. The New-Project-Workflow "Project setup" install step now links to the new Quick Start anchor. Added an "Entry points (v3.7.0 install-UX overhaul)" note to the AGENTS.md installer-aware-changes section documenting that the root `install.sh` / `install.ps1` are dual-mode (precheck + fetch the `main` tarball to `~/.nexus-hub/src` + hand off) and that the core `scripts/installer.{sh,ps1}` are unchanged, so the distribution channels / copy rules below are unaffected; `nexus-hub upgrade` re-runs the same idempotent bootstrap. (CLAUDE.md imports AGENTS.md via `@AGENTS.md`, so no separate CLAUDE.md edit was needed.) Counts and the version label are deliberately left for `/update release` in Phase 5 per the plan.
3. **4.3 -- Verification and stabilization.** Confirmed the guide HTML parses cleanly and is tag-balanced (div 610/610, section 18/18, p 117/117, svg 23/23), all 5 `[data-copy]` blocks are present (each gets a copy button), all three bootstrap commands are present, and every static `data-go` nav target resolves to a `data-page`. Beyond the named scope, aligned two more current-facing docs that still presented the old flow as current -- `llms.txt` (the LLM-facing install summary) and the Chinese `README_zh.md` Quick Start + workflow step -- removing their download-first / double-click instructions, since the gate is "no doc presents the old download-first flow as current". Added the `[Unreleased]` CHANGELOG entry under a new `### Changed` subsection.

## Key decisions

- **Two step badges, not one.** The plan frames the install as "Step 1 Open a terminal" + "Step 2 Run one command", so the guide now uses two distinct step badges (and the later two renumber). This reads as a clean numbered sequence and matches the plan's intent better than cramming both into one badge.
- **Reuse the existing `[data-copy]` injector verbatim.** The v3.6.0 copy-button system attaches a button to any `[data-copy]` element and copies the attribute value (not the visible text), so the rendered line can show a `$` / `>` prompt glyph while the copied value is the bare command. No JS change was needed -- only new `cmd-line` markup.
- **`overflow-wrap:anywhere` over `word-break:break-word`** on the long-URL command lines: "anywhere" reduces the flex item's min-content size so the item can actually shrink and wrap inside the `display:flex` `cmd-line`; "break-word" does not affect min-content sizing and would force horizontal overflow.
- **Keep the in-repo path documented as a secondary option.** Phase 1 preserved the clone-and-run workflow, so the README and `llms.txt` note that `./install.sh` / `install.bat` still work -- a secondary fallback, not the primary/current flow, which satisfies the gate while staying accurate.
- **No count / version edits.** The plan assigns count and version-label changes to `/update release` in Phase 5; the stale README/README_zh counts were left untouched (every changed line traces to the Phase 4 gate).
- **Aligned `llms.txt` + `README_zh.md` install lines** because the 4.3 gate says "no doc" presents the old flow as current, and both are current-facing. Archived/history/plan docs (immutable records) and `infrastructure/tools/README.md` (a contributor dev-tooling doc where the in-repo path is correct) were left untouched.

## Troubleshooting

- **A session note nearly re-introduced a personal-path leak.** The first draft of the DEVLOG entry quoted the standing leak as the literal `C:\Users\<name>` (with the real username), which would have added a fresh `validate_no_personal_paths` finding -- the same trap the Phase 3 history avoided with `<name>` placeholders. Fixed by writing the path with a `<name>` placeholder in the DEVLOG and this history file before running the gate.

## Test results

`make` is unavailable on this Windows host (WN-v33-1), so the relevant gates ran via the documented direct equivalents -- ALL GREEN for the changed files. This is a docs-only phase, so the HTML/doc validators are the test surface (no `make test` is warranted -- no code or tests were added).

- Guide HTML: inline `html.parser` parse without exception; container-tag balance div 610/610, section 18/18, p 117/117, svg 23/23; 5 `[data-copy]` blocks; all three bootstrap commands present; static `data-go` nav targets all resolve (the only "unresolved" hits are JS template-literal artifacts inside the inline `<script>`).
- `validate_unicode_safety.py`: 0 errors, 1051 warnings -- identical to the Phase 1 baseline, so the changed files (including the Chinese `README_zh.md`) added no new non-ASCII errors or warnings.
- `validate_no_personal_paths.py`: 3 findings, all PRE-EXISTING Phase 1/2 doc leaks (`docs/DEVLOG.md`, `docs/v3/v3.8/comparisons/v3.8.0-comparison-ralph-claude-code.md:265`, the Phase 2 history file); none in any Phase 4 file. The guide's run-output `C:\Users\you` is a generic placeholder the validator does not flag.
- `check_version_sync.py`: all surfaces match canonical 3.6.0 (the README.md / AGENTS.md edits did not disturb the version markers; the bump is Phase 5).
- `check_base_template_parity.py`: 5/5 present (no `base-*.md` template was touched).

## CI/CD edits

None needed. This phase adds no script, test, or hook; the docs changes carry no CI surface beyond the validators already run by `make validate` / CI.

## Deviations

- **Scope widened to `llms.txt` + `README_zh.md`.** The plan names the guide + README + AGENTS, but the 4.3 gate ("no doc presents the old download-first flow as current") required aligning these two additional current-facing docs. Both edits are confined to the install-flow lines.
- **`README_zh.md` only partially modernized.** Only its install-flow lines were corrected; its broader staleness (post-install bullets citing ~187 skills / 34 commands / 13 hooks / 10 agents from a much older release) was left untouched to keep every changed line traceable to the Phase 4 gate. A full re-translation pass is logged below for Phase 5.

## Known gaps / pre-existing issues surfaced (not fixed -- out of Phase 4 scope)

- **3 standing personal-path leaks** in `docs/DEVLOG.md` (the Phase 2/3 entries quoting the leak path), `docs/v3/v3.8/comparisons/v3.8.0-comparison-ralph-claude-code.md:265`, and the Phase 2 history file -- to be redacted in sub-task 5.2 before release.
- **`README_zh.md` is broadly stale** beyond the install flow (wrong catalog counts, old command names). A full re-translation pass should be logged in `docs/v3/v3.7/known-gaps.md` (created in Phase 5).
- Carried-forward constraints: WN-v36-1 (bash not fully runnable on the Windows dev host) and WN-v33-1 (local `make` / ShellCheck not always on PATH; validators run directly).

## Next steps

- **Phase 5 -- Cross-platform verification + release readiness.** Extend CI to run the standalone bootstrap end-to-end and a `nexus-hub --version` check; record the Mac `curl|bash` smoke test; create `docs/v3/v3.7/known-gaps.md` (logging the 3 personal-path redactions and the README_zh re-translation); resolve open items; then `/update release` for v3.7.0 (docs + devlog + gitignore + version bump 3.6.0 -> 3.7.0 + changelog + commit + tag + push, with its own confirmation gates).
- **CI confirmation.** Push `feat/installer-bootstrap` and confirm the `tests` job is green on ubuntu.
