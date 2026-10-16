# Decision: Codex permissions profile not installed on Windows

Status: implemented - Windows Codex configs get no Nexus-Hub permissions profile and rely on `sandbox_mode`; macOS and Linux keep the read-limited profile, which every install now reconciles against the template.

## Problem

The Nexus-Hub Codex template ships a permissions profile (`default_permissions = "default"` plus `[permissions.default.*]`) that limits command reads to system essentials and the open workspace. On native Windows, Codex refused to start threads with "windows unelevated restricted-token sandbox cannot enforce split filesystem read restrictions directly; refusing to run unsandboxed". The vendor documents that the `unelevated` sandbox "can't enforce every split read/write carveout and refuses unsupported policies", and that Codex uses it "as a fallback when `elevated` setup isn't available", which is why the failure was intermittent: it fired whenever Codex fell back (https://learn.chatgpt.com/docs/permissions and https://learn.chatgpt.com/docs/windows/windows-sandbox, fetched 2026-10-15).

The same investigation found two installer defects. The three Codex writers (`installer.sh`, `installer.ps1`, `Install-Nexus-Hub-Permissions.ps1`) skipped any config where the block already existed, so the 2026-09-27 template fix (`":project_roots"` to `":minimal"` + `":workspace_roots"`) never reached existing machines. And when they appended to a config ending in a table, TOML bound the appended `default_permissions` / `approval_policy` to that table instead of the root.

## Decision

1. Codex permissions are reconciled by one implementation, `scripts/merge_permissions.py --codex` (TOML edited through `tomlkit`), which all three writers call. Every run compares against the template instead of testing for presence.
2. On Windows the helper writes no profile and removes a Nexus-managed one, recognized by its `network.allowed_domains` key, which only the Nexus-Hub template has written. `sandbox_mode = "workspace-write"`, seeded by `platform_defaults.py`, becomes the single sandbox setting, which every Windows sandbox mode can enforce. A profile the user authored is left untouched.
3. On macOS and Linux the profile stays, because its read limit is enforced there (measured in the v4.13.2 end-to-end runs). The helper refreshes Nexus-owned keys, retires `":project_roots"`, keeps user-added grants and domains, and moves a misplaced selector to the root.

## Alternatives considered

**Keep the profile on Windows only when `[windows] sandbox = "elevated"`.** Rejected. Codex falls back to `unelevated` when elevated setup is unavailable, so a config that names `elevated` still hits the refusal, and the failure would stay intermittent.

**Keep the profile on Windows but drop its read limits.** Rejected. Permission profiles are beta, an open upstream report (openai/codex#28776) describes the Windows app rewriting a custom profile to read-only, and on Windows the profile would then add nothing `sandbox_mode` does not already give.

**Drop the profile on every platform.** Rejected. It would remove a read limit that works on macOS and Linux and that the end-to-end harness depends on.

## Consequences

- On Windows, Codex commands can read outside the workspace (the only model the unelevated sandbox supports) and have no network inside the sandbox unless approved, which is the `workspace-write` default. Network was previously open whenever the profile was active, because the profile's `mode` and `allowed_domains` keys are not in the vendor schema and were never enforced.
- Open follow-ups: the profile's network keys should move to the documented `[permissions.<name>.network.domains]` table with `features.network_proxy = true`, which would start enforcing the allowlist on macOS and Linux and needs its own decision; and macOS/Linux configs still combine `sandbox_mode` with `default_permissions`, which the vendor says not to do.
