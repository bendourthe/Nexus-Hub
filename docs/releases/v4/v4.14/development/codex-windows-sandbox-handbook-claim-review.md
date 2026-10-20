# Handbook claim review -- Codex Windows sandbox fix

**Covers**: the re-attestation of the `distribution` living handbook after the Codex permissions fix changed two of its recorded inputs. **Read by**: the reviewer of the `fix/codex-windows-sandbox` pull request. **Key topics**: why the evidence went stale, the input diff, the claims reviewed, and why the build and render receipts stay valid.

**Candidate**: branch `fix/codex-windows-sandbox`, created from `origin/develop` at `317dc4b8f`.

## Why the evidence was stale

`check_handbooks.py` reported `distribution: stale evidence -- inputs: scripts/installer.ps1, scripts/installer.sh`. A recomputed snapshot differs from the recorded one in exactly those two digests: `installer.ps1` `024251a6...` to `89744418...`, and `installer.sh` `5c08e680...` to `ee0e85ab...`. The entry digest (`90b6e519...`) and the output digest (`d5200075...`) are unchanged.

## Claims reviewed against the input diff

The diff is confined to the Codex permissions path:

- `scripts/installer.sh`: the `CODEX` branch of `install_permissions` no longer appends TOML with `grep`, `awk` and `sed`; it calls a new `sync_codex_permissions_via_helper`, which runs `scripts/merge_permissions.py --codex` through the existing `resolve_permissions_helper` and reports the helper's `set:` / `removed:` lines.
- `scripts/installer.ps1`: `Merge-PermissionsViaHelper` gains a `-Codex` switch, and the `CODEX` branch of `Install-Permissions` calls it in place of the string-append path.

No delivery call, adapter, flattening step, manifest path, ownership rule, entry point, or version line changed. A search of every distribution source (`source.md` and the five composition fragments) for `permission`, `codex`, `config.toml`, `sandbox`, `merge`, `backup`, `profile` and `toml` returns no match.

| Handbook | Claim | Verdict |
|---|---|---|
| distribution | Installer entry points prepare the bundle and invoke platform integration logic | Holds. The permission step is not the integration runner and no entry point moved. |
| distribution | Delivery shapes, name precedence, owned-file writing ("Unowned file: Preserve by default") | Holds. The Codex sync changes only keys Nexus-Hub wrote, recognized by a Nexus-only fingerprint, and leaves a user-authored profile untouched. |
| distribution | Install-time defaults are seeded only where a platform documents a lever | Unaffected. `platform_defaults.py` and `configs/platform-defaults.json` are unchanged. |
| distribution | "Inspect reported actions and actual installed files, then exercise the capability in its host." | Holds, and the fix was verified that way: `codex sandbox cmd /c echo sandbox-ok` failed on the pre-fix config and succeeded after the sync. |

No claim is false, and no source edit is needed.

## Build and render

The handbook output digest is unchanged (`d5200075...`), because the rendered page does not depend on these input bytes. The existing build and render receipts recorded in `docs/handbooks/_sources/distribution/evidence.json` therefore remain valid, following the precedent of the [v4.13.13 release claim review](v4.13.13-release-handbook-claim-review.md). Only the snapshot's two input digests and this content evidence are updated.

## Merge onto develop

`origin/develop` (`1224a4dd`) was merged into this branch after the v4.14.0 release changed the same two inputs (the installers' version line). The recorded snapshot taken from develop differs from a recomputed one only in the two installer digests: `installer.ps1` `e43ebc89...` to `40035601...`, and `installer.sh` `cc7607b3...` to `105b7af8...`. The entry digest and the output digest are unchanged.

The installer difference between develop and the merged tree is exactly this branch's change: the added and removed lines of `git diff <merge-base> HEAD` and of `git diff origin/develop` hash identically for both installers (82 changed lines in `installer.ps1`, 85 in `installer.sh`). The claims reviewed above therefore still hold, the build and render receipts remain valid, and only the two input digests and this content evidence are updated.
