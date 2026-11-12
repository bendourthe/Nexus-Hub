# Settings 0.4.0 Live Effort Delivery

Local delivery record for the compact responsive selector and native live-effort bridge. Covers the built VSIX, native readback and protocol checks, installed payloads, review fixes, and the remaining user-owned editor verification.

Qualification correction: the user's subsequent editor test failed immediate picker synchronization. The native backend evidence below remains valid, but it must not be read as proof that existing Claude labels or Codex draft labels update immediately. See the [0.4.1 editor follow-up](settings-041-editor-followup.md). The original two VS Code windows had unbridged Codex processes, which the aggregate acknowledgment count failed to identify.

## Result

Settings 0.4.0 is packaged and installed in VS Code, Cursor and Antigravity. Its shared preference updates connected Claude Code and Codex native sessions for their next request. A response already executing retains its current effort. The initial executable connection requires an editor reload; a connection notice can require a further reload if a vendor process started before the launch setting was updated. Copilot and the native Cursor and Antigravity agents remain unsupported effort surfaces listed in the footer.

The effort labels switch from the wide stepped bar to two columns below 280 px and one column below 180 px. The five-line hover contains one effort line, two named guardrail lines, session timing and links. Existing guardrail behavior is retained; this delivery changes effort transport and presentation.

## Artifact

- VSIX: `Nexus-Hub-worktrees/settings-codex-followup-20261105-artifacts/nexus-hub-settings-0.4.0-final.vsix`.
- SHA-256: `63d1b9afd9270f60f28200283bfef6fb8ab71eb59f40bab8122351577766085b`.
- Archive: 25 entries, including 23 extension payload files.
- All compiled runtime files and assets match the source build. The packager changes only the expected README link prefixes and license filename.
- Each editor reports `nexus-hub.nexus-hub-settings@0.4.0`; all 23 installed payload files match the VSIX, allowing the editor's added manifest metadata.
- Receipts: `package-040-receipt.json`, `install-040-delivery.json`, and `installed-040-payload-verification.json` beside the VSIX.

## Verification

| Boundary | Fresh evidence | Limit |
|---|---|---|
| Extension suite | 345 passed, 1 skipped across 15 files; statements 88.45%, branches 84.78%, functions 88.74%, lines 92.97% | Unit and process checks do not establish interactive editor behavior |
| Windows launcher and native sessions | 12/12 changes through the compiled C# launcher and shipped Node relay | No model prompt or inference turn was sent |
| Claude 2.1.318 | Same native process reports Low, Medium, High, Extra high, Max; Ultra reports `effort=xhigh` and `ultracode=true` | Next request, not an already-running response |
| Codex 0.164.0-alpha.11.1 | Same loaded thread emits real settings notifications for all six values, including `max` and `ultra`, on `gpt-6.1-sol` | Mapping is model-capability dependent |
| New and existing native requests | Protocol tests replace stale explicit effort in `turn/start`, thread start/resume/fork and collaboration-mode settings while deep-comparing preserved permissions, sandbox and input | Request transformation tested without submitting an inference request |
| Responsive panel | 14 browser screenshots at 140, 180, 220, 280, 320, 420 and 900 px, light and dark; label bounds and endpoint persistence pass | Browser rendering, not installed-editor visual proof |
| Installed editors | Three registrations and three complete payload comparisons | Interactive connected-session behavior remains user-owned |

Final native evidence: Documents `nx live effort launcher proof final4/native-report.json`. Suite evidence: `coverage-040-delivery.log` beside the VSIX. Responsive evidence: Documents `nx-settings-narrow-live-20261105/smoke-report.json`.

Earlier failed native reruns are retained in Documents `nx live effort launcher proof final`, `final2` and `final3`. They exposed a same-native-mapping status issue and a Windows status-file replacement race. The final source reuses an already acknowledged mapping and retries transient status replacement for at most one second. Final native readback and metadata both pass all twelve changes. Native startup can perform vendor background maintenance despite the private inference endpoint; the proof makes no zero-outbound-network claim.

## Review

The bounded bridge review used correctness, maintainability, testing, project standards, security, reliability, API contract, adversarial and agent-native lenses. Concrete findings were reconciled before delivery: later custom launch settings are preserved; file-based Claude settings remain in private files rather than exposing secrets in arguments; startup failures leave Settings available; newer selections survive stale failure or timeout; model capabilities are reconciled after pending updates; nested collaboration effort is enforced; and live status branches have regression tests. The Windows pipe flush correction is covered by an open-stdin process test and native proof. Findings below confidence 75 did not enter the fix list; no unresolved review finding is claimed closed by inspection alone.

| Considered candidate | Location | Reason not reported |
|---|---|---|
| Permission broadening | Native protocol relay | Effort-only fields change; permission, sandbox and input fields are preserved |
| Shell injection | Native process helper and C# launcher | Shell execution is disabled and Windows arguments are explicitly quoted |
| More provider classes | Protocol owner | Additional abstraction would add complexity without user benefit for two current providers |
| Human-only effort action | CLI and extension commands | Existing `settings set effort` and named extension commands already expose the action |
| Hook sibling requirement | Extension-local verification script | The sibling rule applies to catalog shell hooks; no such hook changed |

## Handoff

The user requested packaging and installation and will verify the editors. Reload the editor to activate 0.4.0, follow any remaining connection reload notice, then change the shared effort with an existing Claude agent, an existing Codex chat and an ordinary new chat open. A composer can retain a cached label until its next native request; the bridge governs that request. The panel's connected/applied counts are native acknowledgments from bridged processes, not a count of every editor process.

No editor was reloaded during this delivery, no native permissions or guardrail preferences were changed, and the saved user effort remains Max. Native Cursor, Antigravity and Copilot effort adapters, interactive editor verification and remote publication remain open. This is local installed delivery, not a repository release or a fully qualified editor matrix.
