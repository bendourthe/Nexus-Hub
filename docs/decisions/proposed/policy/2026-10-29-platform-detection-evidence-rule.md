# Platform Detection Evidence Rule

Status: proposed - gated platforms are detected only by evidence Nexus-Hub did not create (PATH, vendor entries, app paths, or an explicit --platforms)

Plan: `docs/releases/v4/v4.14/plans/v4.14.7-installer-platform-detection.md`. Policy: `docs/policy/platform-detection.md`.

## Problem

Kimi, Qwen, Hermes, and Pi treated "the tool's home folder exists" as proof the tool was installed, and Nexus-Hub wrote into that same folder. On the maintainer's machine `~/.kimi-code`, `~/.qwen`, and `~/.hermes` were all created in the same minute on 2026-08-08, during the v3.16.0 defaults-seeding work (commit `7ea867c04` landed 41 minutes later), and every later install then counted all three tools as present although none was ever installed. Nexus-AI and Aider were never gated at all, and OpenCode's global surfaces were ungated while its completion plugin was gated on the folder its own first install creates. A second folder-existence detector in `docs/policy/platform-read-contracts.json` drove `nexus-hub verify`, so fixing the installer alone would have left verify telling users to reinstall a platform the installer then skips.

## Proposal

One rule, declared per integration and evaluated in one place. A gated platform is detected when the user forced it with `--platforms`, when its home root or a vendor-only folder holds an entry Nexus-Hub did not write, when a declared executable resolves on `PATH` (with corroboration for collision-prone names), or when a declared application path exists. Tracked files, declared Nexus-Hub names, OS metadata, and Nexus-Hub backups and temporaries are never evidence. Install, verify, and the stale-surface report all call the same function. A not-detected install keeps the previous action record so file hashes survive.

## Alternatives considered

- **Folder existence (status quo).** Rejected: circular. Any one write by Nexus-Hub, or by an earlier development build, makes the folder exist forever, which is exactly the defect observed on 2026-10-29.
- **Executable on PATH only.** Rejected: misses desktop applications (Nexus AI Studio has no command) and tools installed without a PATH entry or behind a `.ps1`-only npm shim, which would silently drop skills for real users.
- **Folder existence minus Nexus-only folders.** Rejected: misses a freshly installed tool that has not created its folder yet, and still needs a definition of "Nexus-only", which is the classification this proposal makes anyway.
- **File-content rule for shared configs (Aider's `~/.aider.conf.yml`).** Rejected: Nexus-Hub writes that file without tracking it, so "the file exists or is untracked" reintroduces the circular test, and a content classifier over a file both parties edit is fragile. Aider is detected by its executable only, with `--platforms aider` as the override.
- **Backups (`*.nexus-hub.bak`) as vendor evidence.** Considered after the plan review and rejected during implementation: the merge helpers write a backup whenever the config already existed, including a config Nexus-Hub seeded in the same install, so the maintainer's Kimi-free `~/.kimi-code` held one. Backups are neutral.

## Acceptance criteria

- On a home with none of the seven tools, a global install writes none of their roots or files, twice in a row.
- A root holding only files a previous install wrote is not detected on the next install.
- A stub executable, a vendor entry, an application path, or `--platforms <key>` each makes exactly that platform install.
- For every gated platform with a verify row, `nexus-hub verify` and the install gate agree on absent, Nexus-only, and executable states.
- Detection never creates the root it inspects and never executes the resolved file.

## Risks

- **False negatives** for tools installed without a PATH entry and with no tool-created entry yet. Mitigation: `--platforms <key>` forces and records the platform; the install output names the remedy.
- **False positives** from a same-named command. Mitigation: corroboration for verified collisions (Hermes); `pi` remains unverified and is not corroborated.
- **Unverified install locations** (Nexus AI Studio's Windows subfolder). Mitigation: two spellings probed, `~/.nexus` app data checked as well, and the override.
