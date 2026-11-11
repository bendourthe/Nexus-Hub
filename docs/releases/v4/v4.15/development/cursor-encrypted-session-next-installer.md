# Cursor Session Repair Inclusion

Release carry record for the next Nexus-Hub installer release. Covers the Cursor encrypted-session repair in the installer source, extension version 0.1.2, preserved pending edits, package checks, and release integration still required.

## Integration Checkpoint

The isolated repair branch is `fix/cursor-encrypted-session-release`, based on integration commit `3c4ead7b0ad1d1a4261da9869303fe905f223731`. The seven scoped repair files and version-only manifest/lock changes are transferred without changing any of the primary checkout's 43 pending paths. Existing integration configuration, dependencies, overrides and reminder behavior remain intact; unrelated primary edits remain pending in their original checkout.

Fresh local Windows qualification runs the canonical `cursor-usage-monitor` profile: compilation, coverage, normal packaging with prepublish compilation, and package verification all pass. The suite reports 393 passed and two existing skips across 26 files, including the new durable Windows-only native regression. Statement coverage is 90.52 percent and branch coverage is 85.34 percent. The monitor workflow now requires a Windows job using that same profile, alongside its existing Linux build and optional Cursor-host scenario. The 15 workflow policy tests pass.

The actual SQLite/session-adapter/PowerShell DPAPI path passes with a disposable synthetic profile, without reading real credentials or consent records and without outbound requests. Denied consent prevents adapter access; authenticated tampering, native unprotect failure and unsupported envelopes fail safely, and plaintext still works without Local State. The durable repository regression exercises the real native subprocess rather than injecting the decryption result. The ten-second native process bound is retained; timeout expiry itself is not claimed as exercised. The [decision record](../../../../decisions/implemented/tooling/2026-11-06-cursor-encrypted-session-native-validation.md) explains the scoped decryption and required Windows gate.

The rebuilt local VSIX is extension version 0.1.2 with SHA-256 `03aac0dbc8b73a344164baa8e39d3d1a4a5902d4ed29f470c4c2ed0e254ca02b`. It contains 65 total files, including 63 extension files and 25 reachable runtime modules; all 27 archived JavaScript files match the compiled output byte for byte. The new module and consent scope are present. Five pytest-cache files found in the primary reference archive are absent. The reference archive is retained as prior evidence and is not substituted for this build.

These are local integration checks. Protected PR validation, the next Nexus-Hub release, the released installer payload and fresh usage after any required reload/renewed consent remain required. Rebuild and verify from the actual release source rather than treating this local package as the final installer artifact.

## Original Carry Status

The user confirmed the installed repair is working and requested its inclusion in the next installer release. The repair is now applied in the primary checkout on `feat/tune-prompting-20261104`, rather than existing only in the isolated repair worktree or the installed extension. No commit, push, merge, or release was performed for this carry step.

Both `scripts/installer.ps1` and `scripts/installer.sh` already build `extensions/cursor-usage-monitor`, compile its TypeScript, package a VSIX, and install that package. No installer-script change is needed. The manifest and both root version fields in the lockfile now specify 0.1.2.

## Included Changes

- Windows decryption of the named session value in Cursor's new `cursor-safe-storage:v1:` envelope, using the application key from Cursor's adjacent `Local State` file and Windows data protection.

- A new consent scope that discloses local decryption and requires a new decision; refusal prevents the session adapter from being called.

- Safe decryption-failure messages, plaintext-session compatibility, and 20 regression cases.

- The README describes the expanded access boundary and the Windows-only limitation for encrypted sessions.

## Preservation

The user explicitly approved adopting the current `extensions/cursor-usage-monitor/package.json`, `extensions/cursor-usage-monitor/package-lock.json`, and `docs/todos.md` as the preserved baseline. The official edit guard's `diff`, `accept`, and `check` flow was used. The manifest's existing settings defaults, shared credit-reminder path, and dependency ranges were preserved. The lockfile's existing dependency updates and the tracker's current history were preserved. Only the extension version fields and the new release-tracking entry were changed in those three files.

Other pending hook, template, credit-reminder, extension, and changelog work remains intact.

## Original Carry Verification

- `npm run compile --silent` succeeded from the primary checkout's Cursor extension directory.

- `npm test -- --reporter=dot` reported 392 passed and two existing skips across 25 files.

- A fresh VSIX was built from the primary checkout's compiled source using the same package implementation and no-dependency setting used by the installer. The duplicate prepublish compilation was omitted because compilation had just passed. `npm run verify:package --silent` reported 68 archived files, 24 runtime modules, and a passing result.

- A real fetch through the primary checkout's compiled session adapter, transport, and provider returned `source: credential-api` and `stale: false`.

- Archive inspection confirmed version 0.1.2, the four session-related runtime modules byte for byte against the compiled source, and the new decryption consent scope. This archive is a full source build, distinct from the installed-build repair previously delivered.

- The installer-source archive SHA-256 is `a42c301e19917584fbe6d5bdcac3aa9a7f780c13a34710a941f6b9c95a12fd1c`. Its local path is `extensions/cursor-usage-monitor/cursor-usage-monitor-0.1.2.vsix`.

## Release Requirement

Include the Cursor repair source, regression tests, README, manifest version, lockfile version, this record, and the tracker entry in the next authorized release integration. Do not ship only the earlier temporary installed-build repair. Publication and the complete installer run remain part of that release's normal qualification; they were not triggered by this request.
