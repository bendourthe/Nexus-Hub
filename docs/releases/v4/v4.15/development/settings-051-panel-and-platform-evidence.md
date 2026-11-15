# Nexus Hub 0.5.1 Panel and Platform Evidence

This record covers the compact panel refinement and native-provider investigation performed on 2026-11-05. Read it when checking installed UI behavior or planning an additional effort adapter. It distinguishes extension installation, visible layout verification, existing Claude/Codex behavior and unimplemented native-provider support.

## Panel

Global effort level replaces Default effort. Global effort level, Guardrails and Version use the same larger section-heading style. Apply to all sessions is right-aligned below the effort selector. Both action buttons share a compact cyan-accented style with visible keyboard focus. The installed version uses the brand title's text size and weight; its upgrade action is aligned right on the same row when space permits. Narrow rows wrap rather than overflow.

Auto-save, Saving and Saved indicators and the effort application's transient status paragraph were removed. Success notices no longer create a visual banner. Existing screen-reader status announcements remain available. Actual errors and workspace-trust limitations remain outside the effort card. Effort mapping, provider adapters, event revisions, manual session overrides and guardrail behavior were not changed.

## Verification

- Focused panel and manifest tests: 44 passed across two files. The cases cover one-write saving, keyboard effort selection, readback, busy and untrusted states, absence of transient visual effort status, and accessible success feedback.
- TypeScript compilation and package-content verification passed; the package contains all 27 required payload files.
- A genuine private VS Code 1.145.1 extension host displayed the updated panel. At normal panel width, both action buttons align right and installed version 4.14.8 shares a row with Check for upgrades. At a compact width, all six effort choices remain readable in a vertical layout. No model request or shared effort change was sent during these checks.
- Official editor CLIs registered nexus-hub.nexus-hub-settings@0.5.1 in VS Code, Cursor and Antigravity. All 27 packaged payload files matched each installed directory, allowing only installer metadata in package.json.
- All 17 compiled runtime files matched the installed 0.5.0 package byte for byte. The user's confirmation that Claude Code and Codex now work applies to that unchanged behavior; this UI pass does not claim a fresh end-to-end requalification of every agent flow.
- Pipeline files were unchanged. Working editor windows were not reloaded or closed. A reload is needed to load the newly installed presentation files.

## Native Providers

The target behavior requires three separate operations: update every open session once when Nexus changes, seed new sessions from Nexus, and preserve subsequent manual session overrides until the next Nexus change or Apply to all. A request-wide force setting or a command that changes only the focused session does not satisfy this contract.

| Provider | Installed build | Observed control | Result |
|---|---|---|---|
| Cursor native agent | 3.29.9 | cursorai.action.switchToModelSlug accepts modelIdWithParams, writes the composer default and updates the selected composer. The native model configuration service has separate per-composer setters. The working native session visibly displayed Claude Opus 5.5 Medium. | A selected-session route exists. No qualified all-session setter or safe model-parameter mapping was established. Automatic support remains unimplemented. The working session was not changed. |
| Antigravity native agent | IDE 1.107.0 | Bundled extension manifests expose no reasoning-effort setting or model/effort command. Native model selection is owned by the workbench/cascade frontend. | No qualified external live effort setter was established. Automatic support remains unimplemented. |
| GitHub Copilot | Bundled in VS Code 1.145.1 | Native per-session model configuration; registered model-picker commands. github.copilot.chat.reasoningEffortOverride is an advanced debugging setting. Its request builders prioritize that value over modelCapabilities.reasoningEffort. | The debugging override would force request effort over manual choices, so it was not enabled. No direct per-session/all-session effort command was found. The private profile requires Copilot sign-in, so no authenticated native request was tested. |

Current official [VS Code model documentation](https://code.visualstudio.com/docs/agent-customization/language-models) describes native per-session effort configuration, new conversations using the last model-specific choice, and deprecation of the older Anthropic and Responses API effort settings. This supports using the native model configuration owner rather than deprecated settings. The debugging override above was established from the installed manifest and request builders, not inferred from the documentation.

The current [Antigravity model documentation](https://antigravity.google/docs/models) describes choosing reasoning models and retaining the selected model within a conversation. Its separate CLI /effort command is not evidence of an IDE setter. The current [Cursor models documentation](https://cursor.com/docs/models-and-pricing) describes effort availability but supplies no external all-session setter. Documentation and installed-build observations are separate evidence.

These findings do not prove an adapter is impossible. A follow-up must identify each native session/configuration owner, preserve the existing model and other parameters, map only advertised effort values, and verify manual overrides plus new-session defaults in actual authenticated native sessions. No new automatic provider support is represented as installed or working by this delivery.

## Artifacts

Local qualification artifacts are under C:/Users/you/Documents/nx-ui051-qualification. The final VSIX SHA256 is a215ad75c1e51497be2f7adaf2e74615bbcef8edec92351caa67258606fc8e6e. install-final.json records official editor registration; delivery-verified.json records installed payload and unchanged-runtime checks. native-platform-inventory.json records installed versions, source hashes and bundled settings/commands; native-command-candidates.json records source candidates; host.json records actual private-host model commands and view state. No credentials or conversation transcripts were copied into these artifacts.
