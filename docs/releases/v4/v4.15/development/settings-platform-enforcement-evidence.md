# Settings Platform Enforcement Evidence

This record covers the local Settings 0.3.0 delivery: compact effort and hover layout, native effort mappings and reconciliation, five guardrail switches, editor installation and observed limits. It is a bounded extension delivery, not a Nexus-Hub release or a whole-minor completion claim.

## Result

Settings 0.3.0 is installed in Visual Studio Code, Cursor and Antigravity IDE. Each active registration points to the same build, and 18 packaged payload files per editor match the VSIX byte for byte. All 55 delivered settings-engine and hook runtime files match the final source. The user's saved Ultra choice and guardrail choices are preserved. The installed engine reports Ultra as Claude native `max` and Codex native `xhigh`, with both `matches_default` values true and both states `in-effect`.

The effort card has no redundant selected-value label and a measured 6-pixel heading gap. The native Markdown hover has four short lines without simulated controls or image tables. A grid gives the effort labels sufficient hit-area width while preserving the track endpoints. [Dark panel](settings-platform-enforcement/panel-dark-420.png) and [narrow light panel](settings-platform-enforcement/panel-light-320.png) show the rendered result.

## Platform Matrix

| Surface | Effort observation | Guardrail observation |
|---|---|---|
| Claude CLI 2.1.283 | Six choices read back through native `/effort status`; conflicting inherited effort does not beat the settings environment | 21 installed hook protocol cases pass |
| Claude VS Code extension 2.1.318 | Uses the shared Claude setting; existing launch overrides synchronize through the real host configuration API | Existing native registrations retained; installed hooks verified |
| Codex CLI 0.136.0 | Six choices accepted by native app-server `config/read`; raw `ultra` rejection retained | 21 installed hook protocol cases pass |
| Codex VS Code extension 26.1021.22027 | Installed source reads the same config and filters model-supported effort; compatible mapping avoids rejected `max` and `ultra` client values | Existing native registrations retained; installed hooks verified |
| GitHub Copilot 0.73.0 | Open: per-model picker persists settings, but public model API omits supported effort enums and a setter | 21 installed native-adapter cases pass |
| Cursor 3.24.18 | Open: no verified writable global native-agent effort control | Four native pre-tool guards plus post-tool edit ledger; 21 installed cases pass |
| Antigravity IDE 2.6.0 | Open: no verified writable native IDE effort control; CLI controls are separate | Existing enabled registrations retained; corrected native adapter passes 21 installed cases |

Sources and write admissions are linked in the [proof matrix](settings-platform-enforcement-proof.md). Current sources include [Copilot model configuration](https://code.visualstudio.com/docs/agent-customization/language-models), [Cursor hooks](https://cursor.com/docs/hooks) and [Antigravity hooks](https://antigravity.google/docs/hooks). Absence of a writable effort control is the outcome of the installed-source and current-documentation audit, not a claim that no future vendor API can provide one.

## Verification

| Check | Fresh result |
|---|---|
| Settings engine | 397 passed, 3 declared skips; subsequent six deletion-repair regressions pass in the 51-case mapping/shared selection and 96-case resolver selection |
| Catalog admission | 30 passed |
| Extension suite | 303 passed, 1 skipped; statements 97.06%, branches 90.71%, functions 94.32%, lines 98.79% |
| Final grid/layout scope | 93 passed; seven browser actions and six screenshots; measured 6-pixel gap |
| Visual detector | Zero findings and zero allowlisted at widths 320, 420 and 900 |
| Hook/Cursor composite | 260 passed, zero skips |
| Antigravity adapter scope | 67 passed, zero skips, including six real-child regressions |
| Installer helper delivery | 10 passed, including all editors, absent VS Code and isolated Cursor installation failure |
| CLI/Antigravity integration scope | 45 passed, 11 declared skips |
| Native configuration consumers | Six Claude and six Codex selections read back; no model request sent |
| Installed hook protocols | 105 passed, 21 per client; private home/store, installed edit helper and inert payload commands |
| Editor hosts | Trusted and untrusted activation pass in all three real installed editors; panel opens; real configuration writes preserve unrelated environment entries |
| Repository checks | All 18 fast checks pass; final eight hygiene checks pass; 14 platform contracts match |
| Package | 19 required files verified; final ZIP integrity and installed payload hashes pass |

Overlapping selections are not summed as independent tests. The full extension run precedes the final CSS-only grid correction; its affected 93-case UI selection, browser exercise and detector were rerun afterward. The engine's six late deletion regressions are retained as focused evidence rather than being mislabeled as another full-suite run.

## Functional Exercises

The real panel drives the actual settings CLI in a disposable home. Max and Ultra persist the shared choice while writing Claude native `max` and Codex native `xhigh`. A warning switch is toggled off and on and the real large-file hook changes its output accordingly. Runtime console and geometry checks are clean.

The native Claude probe runs `/effort status` against engine-written configuration, including an intentionally conflicting inherited effort. The native Codex probe initializes its installed app server and calls `config/read`. Neither probe sends a model prompt. Model metadata alone was insufficient: the native Codex parser rejected a value that its cache advertised.

Installed protocol tests invoke the actual script and wrapper paths for Claude, Codex, Copilot, Cursor and Antigravity. They cover on/off behavior, malformed settings, malformed payloads, the edit read/change/write ledger and independent Git bypass protection. Payload commands are inspected as data and never executed. These are native-protocol consumer tests, not authenticated model tool calls.

## Corrections

The first Antigravity installed check allowed a dangerous command because the adapter retained case-only duplicate keys such as `Cwd` and `cwd`. Windows PowerShell rejects those JSON objects. Canonicalizing argument and edit-chunk keys removes the duplicate copies; failing PowerShell regressions and successful reruns are retained.

The first Cursor read-only host check inherited the product's disabled workspace-trust default. Explicitly enabling trust in the scratch profile produced the required trusted/read-only pair. The harness now asserts host exit codes, installed version, trust, read-only state and required interaction steps before it can succeed.

Review also found transient reconciliation failures suppressing retries and Claude environment-key deletion being mistaken for an equivalent persistent fallback. Both have regressions and corrections. Editor environment overrides now cover every local workspace folder; native engine project-file reconciliation remains limited to the first active local folder.

## Delivery

The sibling `settings-platforms-0.3.0-artifacts` directory holds the sealed `nexus-hub-settings-0.3.0-delivered.vsix`, installation report, final hash verification, native-protocol report and retained failed attempts. Native loader reports are retained in sibling `settings-native-codex-44gw1eee` and Documents `nx-effort-proof`. Real editor-host reports are in Documents `nx-settings-v030-code`, `nx-settings-v030-cursor2` and `nx-settings-v030-agy`. The first Cursor report is retained separately.

Runtime originals and follow-up originals are backed up under `~/.nexus-hub/backups/settings-platforms-20261104-0.3.0/`, with a machine-readable receipt. Runtime delivery preserved all five configuration hashes before intentional synchronization. The subsequent `configuration-before-sync` backup records applying the existing Ultra choice to the corrected native settings; it preserves the desired preference and all guardrail choices. The implementation is committed locally as `82c884b5a`.

The rebuilt working VSIX exceeded the edit guard's check-to-record window. Its binary diff was logged and no baseline was accepted. A uniquely named sealed artifact was created, recorded immediately and matched against every installed payload. No existing artifact was overwritten again. Source and runtime edit-guard logs contain no accepts.

## Open Scope

Automatic effort for Copilot, native Cursor and native Antigravity remains open. Use their native model picker until a writable, supported control can be verified. Managed policies, model caps and explicit existing conversation or draft state remain authoritative. The active VS Code window still needs an extension reload; its existing Claude/Codex panes were inspected but not treated as fresh-session proof. Reloading the active window would interrupt this running conversation, so it was left running. No authenticated model request, repository-wide release profile, remote publication, merge or release was performed.

## CI Impact

No pipeline changes or remote CI runs were needed. Existing engine, hook, integration, extension and installer selections cover this local delivery. Unrelated primary-checkout edits were preserved in place.
