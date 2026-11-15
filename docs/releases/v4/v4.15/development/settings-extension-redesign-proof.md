# Settings Redesign Proof Matrix

This local evidence matrix records behavior exercised for the Settings 0.2.0 controls. A row becomes proven only after its real configuration or hook boundary has been exercised. The companion evidence file records commands, outcomes and limits; none of these observations establishes a repository release or universal vendor enforcement.

## Control Proofs

| ID | Behavior | Status | Evidence |
|---|---|---|---|
| W27 | Shared effort persistence, native write planning, readback and reset | proven | `test_installed_cli_applies_shared_effort_and_restores_existing_override` passed through the actual installed-layout CLI |
| W28 | Git safety boolean changes the dangerous-command hook result | proven | Actual hook switch suite: 122 passing cases; affected sibling parity and PowerShell syntax: 37 passing cases |
| W29 | Secret scanning boolean changes the write guard result | proven | Actual hook switch suite: 122 passing cases; affected sibling parity and PowerShell syntax: 37 passing cases |
| W30 | Edit protection boolean changes the user-edit hook behavior | proven | Actual hook switch suite: 122 passing cases; affected sibling parity and PowerShell syntax: 37 passing cases |
| W31 | Large-file warning boolean changes advisory output | proven | Actual hook switch suite: 122 passing cases; affected sibling parity and PowerShell syntax: 37 passing cases |
| W32 | Applying effort synchronizes an existing user environment override and reset restores it | proven | `test_installed_cli_applies_shared_effort_and_restores_existing_override` passed with exact prior-file restoration |

## Limits

Vendor session defaults, host permission modes and installed hook discovery remain separate from a persisted preference. No native session behavior is inferred from a saved JSON or TOML value alone. No production preference is changed by these scratch exercises.
