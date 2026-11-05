# Settings Extension Redesign

This local extension delivery implements the user's 2026-11-04 request: one shared default effort selector, working main guardrail switches, a compact dashboard and status bar, and the original cyan Nexus logo on every surface. It targets extension version 0.2.0 and installation in the active VS Code profile, not a Nexus-Hub repository release.

## Scope

- Reuse the settings engine, ownership records, reset behavior, workspace trust checks and confirmation flow.
- Store the desired shared effort independently of platform-specific effective values. Write supported native configuration and report overrides or unsupported coverage honestly.
- Expose Git safety, secret scanning, edit preservation, large-file warnings and Git bypass-flag protection as real switches. Preserve existing host permission-mode behavior and all current user values during installation.
- Use one original Nexus mark for the extension, dashboard, sidebar and status-bar glyph. The glyph is necessarily monochrome in VS Code's status bar.
- Keep platform selectors, models, attribution settings and verbose diagnostic tables out of the main panel and hover.
- Deliver updated settings-engine and hook consumers with backups and verified hashes, then install the packaged extension. Installation changes no guardrail or effort preference by itself.

## Phase 1: Implementation

Recommended model tier: frontier. Recommended effort level: high. Recommended verification effort: high. The session's current model is retained because a live model switch is unavailable through this host.

- [x] T001: Implement shared effort persistence and override-aware native writes with readback and reset regressions.
- [x] T002: Implement guardrail configuration controls and Bash/PowerShell hook consumers, with allow/block and malformed-configuration regressions.
- [x] T003: Replace the platform matrix with one autosaving effort selector and working guardrail switches, with keyboard, trust, confirmation and status-bar regressions.
- [x] T004: Restore the original Nexus icon consistently, update the extension version and build an installable package.

## Phase 2: Verification and Delivery

- [ ] T005: Run affected Python and extension tests, coverage, package integrity, focused security review and the repository fast checks.
- [ ] T006: Exercise the rendered panel and installed configuration consumers end to end in a scratch profile; inspect narrow/wide and light/dark rendering.
- [ ] T007: Reconcile documentation and evidence, commit the verified local result, back up and deliver runtime consumers, then install and verify the active extension package.

## Plan Delta

The old settings plan is already implemented and does not meet the current user request. This is a new local delivery, not a reopening or completion claim for the signed v4.15 minor run. The primary checkout has an unrelated MANIFEST.sha256 edit and remains untouched. Work continues in the existing isolated worktree at ../Nexus-Hub-worktrees/settings-icons-20261104, on feat/settings-redesign-20261104. The earlier icon-only changes belong to this session and are being replaced at the user's direction.

## Queue Assessment

The live queue was enumerated at entry. The original v4.15 run and the model-adaptive harness plan may overlap hooks and settings metadata, so this delivery uses an isolated worktree and does not publish or merge around their owners. No queued plan is started by this request. Each implementation slice has exclusive file ownership and is reconciled before delivery.

## CI Impact

Existing hook, settings-engine and extension test selections cover the affected modules. No pipeline change is part of this delivery. Any missing coverage discovered during qualification is recorded with its observed result before installation.

## Completion Boundary

Success means the new panel behaves as requested in a real editor, the effort and guardrail controls change their consuming configuration or hook behavior in scratch exercises, the approved package and runtime consumers are installed with verified hashes, and the local changes are committed. Remote publication, repository version bumps, repository releases, and removal of unrelated branches or worktrees are excluded. No PLAN COMPLETE or MINOR COMPLETE verdict is claimed without the authoritative checker.
