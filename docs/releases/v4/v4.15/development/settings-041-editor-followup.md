# Settings 0.4.1 Editor Follow-Up

Follow-up to the user's failed live-effort test after restarting VS Code. Separates native effort, bridge connection, visible picker state and the updated status hover. Immediate picker synchronization remains incomplete.

## Reproduction

The user changed Max to Medium. Existing Claude and Codex labels stayed unchanged; a new Claude tab showed Medium, while ordinary Codex New Chat still showed Extra High. Read-only inspection found five Claude bridge records with native Medium acknowledged, but both existing VS Code extension hosts launched Codex directly from its vendor directory. There were no Codex bridge records for those windows. The global Codex executable setting had been installed after those native processes started. The old aggregate status incorrectly implied full application from the Claude records alone.

The existing Claude tab was then tested with Nexus Medium to High. Its native bridge records acknowledged High while the same visible model control remained Medium. Opening another Claude tab had previously refreshed the older tab's cached label. Native Claude's exported activation API returns no effort-control interface; the model display is maintained in the vendor's private UI state. No vendor files were changed.

A separate VS Code window used the already configured bridge and initially displayed Medium in Codex. A disposable empty workspace under `settings-codex-followup-20261105-artifacts/settings-041-ui-workspace` was created and trusted only for testing. The prompt `Reply exactly OK. Do not use tools.` completed. With that conversation still open, changing Nexus to High produced native acknowledgment and a visibly updated `GPT-6.1 Sol High` picker. Ordinary New Chat also initially displayed High. Changing Nexus back to Medium left the unsent composer at High, and another ordinary New Chat also showed High. This reproduces the draft-cache limitation rather than establishing a complete new-chat UI fix. The user's saved preference was restored to Medium.

## Changes

- The hover has one Nexus Hub Settings title, an Effort Level section with a compact read-only cyan stepped bar, and a Guardrails section with named states. The bar has six fixed labels, one selected position and theme-aware text colors. It uses the same native HTML/SVG mechanism as the usage-monitor hovers, not HTML inputs.
- The Windows launcher records the actual extension-host parent ID. Status readers accept only records from their own editor host, after checking that the native and relay processes still exist.
- A bounded read-only process probe detects direct Claude or Codex children of the current extension host. Those children bypass the bridge and produce a named connection notice. An installed but unopened provider alone does not count as an unbridged native process.
- Native acknowledgment wording no longer claims that every editor picker refreshed. The footer explains cached labels without adding an always-on unsupported-editor warning.

## Verification

- Compilation passes.
- Focused launcher, panel and hover tests pass, including a real direct `codex.exe` test process and real Windows parent-ID readback.
- The full suite passes 354 tests with one skip; coverage is 89.26% statements, 86.12% branches, 88.97% functions and 93.81% lines. Log: `settings-codex-followup-20261105-artifacts/coverage-041.log`.
- The modified Windows launcher and shipped relay pass 12/12 native effort changes in the same Claude process and the same loaded Codex thread. Evidence: Documents `nx live effort 041 proof/native-report.json`. This submits no inference turns and remains native-control evidence.
- Actual editor observations above are separate from that native-control proof. The test workspace's first request completed with `OK`; no tool action was requested.

## Limits

Immediate refresh of the existing Claude picker and a Codex unsent draft is still open. The inspected vendor commands and exported APIs provide no external effort-picker refresh action. Automatically replacing tabs risks losing drafts and interrupting work; patching vendor bundles would create an unsupported integration. Neither is included in this delivery. The backend next-request enforcement and Codex's connected existing-conversation notification path do not remove this visible UI limitation.

Primary API reference for the hover renderer: [VS Code MarkdownString](https://code.visualstudio.com/api/references/vscode-api#MarkdownString). The installed vendor source and actual editor observations establish the picker limitation; no third-party report substitutes for those observations.
