# Settings 0.4.2 Live UI Plan

Correct the repeated live-effort mismatch in native Claude Code and Codex tabs and route the Codex editor-title button to new editor tabs. Native process acknowledgments alone do not satisfy this phase; the existing visible controls must follow Nexus without opening replacement tabs.

## Scope

- Add reversible, exact-version adapters for the installed Claude 2.1.318 and Codex 26.1021.22027 UI state owners. Develop and test against disposable copies first. Preserve vendor originals and reject unexpected file hashes.
- Call Claude's existing settings apply/readback/state-update method and Codex's existing model-and-effort setter. Only effort changes; keep each selected model, permissions, sandbox and service tier.
- Synchronize open composers, existing conversations and newly created tabs. Map levels from the active Codex model's advertised capabilities; Claude Ultra remains Ultracode.
- Change the Codex editor-title menu from its sidebar command to its existing new-panel command, retaining the Codex icon. Remove the redundant Settings-panel new-agent workaround.
- Verify setters, preservation, repeat installation and restoration deterministically, then exercise unchanged native tabs and ordinary New Chat through the real editor. Install only a qualified candidate.

## Phase 1

- [x] Build and test the pinned UI adapters in private copies.
- [x] Integrate native UI synchronization and tab behavior into Nexus Settings.
- [ ] Verify actual native controls across repeated effort changes without replacement sessions.
- [x] Package, install in available editors and update evidence.

Source delivery: 0.4.2 installed in three editors, with 364 passing tests, 12 native protocol changes and two distinct native Codex editor tabs observed through the actual editor API. The source is saved as one local delivery commit. Visible live-effort verification remains open while Windows is locked; installation does not close that gate. [Evidence](settings-042-native-ui-evidence.md).

CI impact: extension tests, compilation, packaging and native UI integration checks. No pipeline edit or remote publication. Construction ceiling: two version-pinned adapters and one shared synchronization owner; no general extension-host instrumentation, credential handling or OS click automation.
