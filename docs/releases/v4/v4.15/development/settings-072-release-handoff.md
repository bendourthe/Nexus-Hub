# Nexus Hub Extension Release Handoff

Nexus Hub 0.7.2 is the required settings extension for the next Nexus-Hub release. This handoff covers the local package, fresh-install defaults, restart controls, and the integration work still required before publication.

## Release Inclusion

- Integrate the complete `feat/settings-redesign-20261104` branch, including the settings engine, hook consumers, live effort runtime and vendor adapters. Taking only the VSIX would omit required behavior.
- The Windows and POSIX installers already build `extensions/nexus-hub-settings` and install the same package into every detected VS Code, Cursor and Antigravity host.
- Require extension version 0.7.2 or newer in the next release. The local work is not yet merged into `develop` or published; integration and the normal release checks remain required.
- Package: `C:/Users/BEDOURTHE/Documents/nx-settings072-qualification/nexus-hub-settings-0.7.2.vsix`.
- SHA-256: `4d62d70f8fcc5cacc3572bedac01bda4dd84e925d58b37fd41d62b379bef4737`.

## Defaults and Controls

- On first trusted activation of an installed Nexus-Hub, absent preference files are created with Medium effort, Fast mode off and Open Codex in tabs on. Existing preference files are preserved byte for byte; upgrades do not reset saved choices.
- Editor is renamed Extensions. Claude Code and Codex each have an aligned Restart button.
- Neither installed provider exposes an individual restart command. Both buttons explain the shared extension-host restart and ask for confirmation before running VS Code's supported `workbench.action.restartExtensionHost` action. Running requests may be interrupted; saved conversations are retained.
- Live effort, Fast mode, manual session override and guardrail implementations are unchanged from 0.7.1.

## Verification

- Full extension suite: 400 passed, one skipped, zero failed. Compilation and package-content verification passed with 31 required payload files.
- All 31 payload files match the installed 0.7.2 copies in VS Code, Cursor and Antigravity; installer-added manifest metadata was excluded from the semantic manifest comparison.
- New tests exercise fresh defaults, repeated initialization, preservation of existing and malformed preference files, restart confirmation and cancellation, untrusted-workspace refusal, and provider-only panel messages.
- Native disposable VS Code window: inspected Extensions and aligned provider buttons; opened and canceled Codex's confirmation; confirmed Claude Code's shared-host restart. The native log records host 74896 exiting with code zero and replacement host 76156 starting and activating Nexus Hub at 08:28 on November 6, 2026. Working editor windows were not restarted.
- Artifacts and logs: `C:/Users/BEDOURTHE/Documents/nx-settings072-qualification/`. Current native live effort and Fast behavior was not retested because those adapters are unchanged.

## Remaining Gates

- Merge the full feature branch through the integration branch, run required release checks, and publish the next Nexus-Hub release under its normal release authorization.
- The previously tracked Codex inactive-tab renderer startup timeout is independent and remains open.
