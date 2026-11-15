# Settings Platform Enforcement Proof

This record admits the bounded Settings effort mappings and owned override reconciliation exercised for the local extension update. It records configuration-loader evidence, not a claim about a billable reasoning request, existing conversations or unsupported native IDE controls.

## Admission Matrix

| ID | Write | Status | Observation |
|---|---|---|---|
| W33 | Claude authoritative effort environment | proven | CLI persistence, effective readback and exact reset |
| W34 | Codex compatible model effort | proven | Six mapped values accepted by native config/read |
| W35 | Existing project effort reconciliation | proven | Project-bound ownership and exact reset |
| W36 | Existing profile effort reconciliation | proven | Model-aware TOML updates and exact reset |

## W33

Status: PROVEN

Claude effort is persisted in the documented user `env.CLAUDE_CODE_EFFORT_LEVEL` override. Low, Medium, High and Extra high map to `low`, `medium`, `high` and `xhigh`; Max and Ultra map to `max`. Persistent `effortLevel` and per-model fallbacks remain valid at `xhigh` for the two highest shared selections. Ultra does not silently enable Claude's separate orchestration mode. Real settings CLI tests exercise set, effective readback, repeated writes and byte-exact reset. The existing editor launch environment is synchronized separately through the host configuration API without altering unrelated environment variables.

Sources: [Claude model configuration](https://code.claude.com/docs/en/model-config), [Claude settings](https://code.claude.com/docs/en/settings), [Claude VS Code configuration](https://code.claude.com/docs/en/vs-code).

## W34

Status: PROVEN

The shared default uses Codex's common client vocabulary through `model_reasoning_effort`. Max and Ultra map to `xhigh`, with a further downward clamp when the selected model advertises a lower ceiling. The installed native Codex app server 0.136.0 rejected raw `ultra` as an unknown enum value despite model-cache metadata advertising it. Its actual `config/read` boundary then accepted all six mapped selections: `low`, `medium`, `high`, `xhigh`, `xhigh`, `xhigh`. No inference or authentication request was sent. Native response and six-case report are retained in the sibling `settings-native-codex-44gw1eee` evidence directory.

The installed Codex IDE also reads the same configuration but applies its own model capability and enabled-effort filter. Its new-session default must be a valid member of that filtered model list. Existing threads and drafts retain their session settings. Hidden IDE preferences are not modified.

Source: [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference). Installed client source and the actual native loader, rather than model-cache presence alone, decide compatibility.

## W35

Status: PROVEN

Existing user-owned project effort keys are reconciled with the shared preference. The ownership record binds each project write to its exact project identity, so resetting in another workspace cannot restore a different project's data. Missing project files or effort keys are not introduced. Managed policy files are never written. Actual CLI regressions cover competing project values, repeated sets, project-specific identity and exact restoration.

## W36

Status: PROVEN

Existing Codex profile effort keys use the selected profile model's compatible native mapping. Profile defaults are synchronized without changing model selection or unrelated profile properties. CLI set/readback/reset tests preserve the original TOML text, including root/profile separators. Invalid configuration is reported instead of overwritten.

## Limits

The public VS Code language-model API omits Copilot's supported effort enums and configuration setter. Copilot's native per-model configuration file exists, but this update does not guess valid values or write its global debugging override. Cursor and Antigravity IDE native effort controls have no verified writable public control in the installed versions. Their CLI controls are separate products and do not establish IDE enforcement. These surfaces remain open and are listed in the delivery evidence.
