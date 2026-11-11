# Settings Live Effort Plan

This bounded local-delivery plan adds live effort control to already-open Claude Code and Codex sessions in the locally installed editors, while retaining the requested compact hover. One editor reload connects the process bridge; later preference changes apply to existing sessions on the next request without interrupting a response already running.

## Scope

- Keep the five-line hover with one effort line and named guardrail states.
- Use the existing executable-wrapper settings for Claude Code and Codex, without modifying vendor files or changing permission settings.
- Relay native protocol traffic transparently, apply acknowledged live effort changes, and enforce the saved Nexus effort on subsequent native requests, including ordinary new-chat requests.
- Preserve existing launch settings, unrelated preferences and drafts. Store the bridge in the Nexus-Hub user directory so extension updates do not remove its executable target.
- Install and qualify the built extension in available local editors. Keep unsupported native Cursor, Antigravity and Copilot effort controls as footer compatibility information.

## Phase 1

- [x] Implement the protocol bridge, native Windows launcher and editor-configuration integration with preserved originals.
- [x] Prove native live effort updates in existing Claude SDK processes and loaded Codex threads, including mapping and acknowledgment failures.
- [x] Verify ordinary new requests use the current preference even when the client sends an older explicit effort; verify permissions and unrelated fields remain intact.
- [x] Install the final package in VS Code, Cursor and Antigravity and compare all installed runtime assets with the VSIX.
- [x] Update the progress tracker and evidence, run attribution and required local checks, and create one local delivery commit.
- [x] Exercise the installed editor flow after the user's failed test. Native Claude effort changes, its existing picker stays stale, and unbridged Codex processes need a connection reload. A connected Codex conversation visibly updates; ordinary new-chat draft labels can remain cached. These results are recorded as partial behavior, not full live UI qualification.
- [ ] Finish immediate picker synchronization through a verified vendor interface. No external setter or refresh command was found in the installed Claude or Codex extension APIs; vendor bundles, private databases and user tabs are preserved.

CI impact: extension compilation, tests, package-content checks and native protocol tests cover the new runtime. This plan does not change CI pipeline files or authorize remote publication.

## Evidence

Before implementation, bundled Claude 2.1.318 accepted `apply_flag_settings` for two different effort levels in one running process and reported the corresponding applied values through `get_settings`. Bundled Codex 0.164.0-alpha.11.1 accepted `thread/settings/update` twice for one loaded thread. The probes used disposable configuration and local-only endpoints, with no model turns. Results are under Documents `nx-live-effort-native-proof`. Final qualification must also inspect the resulting notifications and actual configured-wrapper flow; request acceptance alone is not the final gate.

The final Windows launcher/native relay proof passes all six changes in each same running native session. The final suite passes 345 tests with one skip. The [delivery record](settings-040-live-effort-delivery.md) distinguishes native readback, protocol request enforcement, installed payload proof and the user-owned editor check. No remote publication or full editor qualification is claimed.
