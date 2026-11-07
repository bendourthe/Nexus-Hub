# Decision: Cursor Encrypted Session Native Validation

Status: implemented - Require Windows-native validation for consent-gated encrypted-session support in the normal Cursor monitor build.

## Problem

Cursor's named session value can now contain an encrypted envelope. Sending that value as a bearer token produces repeated authorization failures. Maintainers need a narrow decryption boundary and durable validation of the Windows subprocess, while keeping the existing installer build and unrelated user work intact. A Linux-only monitor workflow cannot exercise Windows data protection, and injected unit dependencies alone do not verify the actual native script or pipe handling.

## Decision

Recognize the supported encrypted envelope, read only the adjacent application's named Local State key, and unwrap it with Windows data protection for the current user. Authenticate and decrypt the session in memory. Use a hidden, absolute-path native executable with a static script, private stdin/stdout pipes, a ten-second timeout and bounded output. Do not place credentials or encryption keys in arguments, logs or evidence. Preserve plaintext support and stop safely for unsupported platforms, formats, authentication failures or native errors.

Renew the existing versioned consent under `state-db-allowlisted-key+model-key+windows-decryption+usage-json/v3` before the session adapter can run. Earlier decisions do not authorize the additional application-key read. Declining preserves the existing manual/cache behavior; no consent record is edited to bypass the prompt.

Retain unit coverage for format, authorization and error boundaries, and add a Windows-only repository regression using disposable synthetic SQLite and DPAPI data. The real default subprocess runs without injected decryption. It verifies successful recovery, read-only database behavior, authenticated tamper rejection, native failure and plaintext compatibility without reading a real profile. The path-filtered monitor workflow adds a Windows job calling the existing canonical monitor profile; `cursor-required` requires that job alongside the Linux build and existing optional-host scenario. The normal installers already build this extension tree and need no special repair package or script change.

## Alternatives considered

| Alternative | Disposition |
|---|---|
| Retry the encrypted value as a bearer token | Rejected because retries repeat the same invalid credential representation. |
| Read the additional key under earlier consent | Rejected because that decision did not disclose local Windows decryption. |
| Persist or cache the unwrapped application key | Rejected because the authorized operation needs only transient in-memory use. |
| Qualify only through injected unit decryption or an external manual script | Rejected because neither supplies durable CI coverage of the native producer. |
| Keep the monitor workflow Linux-only | Rejected because the supported encrypted-session path is Windows-specific. |
| Add decryption for other operating systems in this repair | Deferred because their access mechanisms require separate implementation, disclosure and qualification. |

## Consequences

Selected monitor pull requests incur one additional Windows profile job. The profile remains the single command contract, and no duplicate push or post-merge monitor run is added. Native tests use generated data and remove only their verified owned temporary directory. The native timeout remains delegated to the process API; forced timeout expiry is not claimed by the current proof. Protected integration and actual released-installer verification remain separate gates, including fresh usage after any required reload and genuine renewed consent.
