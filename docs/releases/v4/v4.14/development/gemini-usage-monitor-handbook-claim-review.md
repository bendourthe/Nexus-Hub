# Handbook claim review -- Gemini Usage Monitor installer routing

**Covers**: the re-attestation of the `distribution` living handbook after both installers gained the Antigravity-only Gemini Usage Monitor. **Read by**: the reviewer of the `feat/gemini-usage-monitor` integration pull request and `/update release`. **Key topics**: stale snapshot cause, installer diff, claim verdicts, why the build and render receipts still hold.

**Candidate**: branch `feat/gemini-usage-monitor`, created from `origin/develop` at `432abfa90`, with the Gemini Usage Monitor changes applied.

## Why the evidence was stale

`check_handbooks.py` reported `distribution: stale evidence -- inputs: scripts/installer.ps1, scripts/installer.sh`. A recomputed snapshot differs from the recorded one in exactly those two digests (`installer.ps1` `0afc5a1e...` to `11c4f5f8...`, `installer.sh` `b461538c...` to `1b44b824...`). The handbook entry digest and the output digest are unchanged, and no other input moved.

## Claims reviewed against the installer diff

Each installer gains about 40 lines and does three things. It resolves an Antigravity IDE launcher (`antigravity-ide`, then `antigravity`, then fixed install paths; never the `agy` agent CLI). It adds a GOOGLE vendor section that calls the existing shared build-and-install function for `extensions/gemini-usage-monitor` with that launcher alone. It adds one banner line and widens two others. No platform integration, copy target, ownership path or attribution step changes.

A search of every distribution source (`source.md` and the five composition fragments) for `Antigravity`, `Gemini`, `usage monitor`, `Copilot`, `Cursor`, `VS Code`, `editor`, `agy` and `launcher` returns no match. The handbook makes no claim about which editor or launcher receives which usage monitor.

| Handbook | Claim | Verdict |
|---|---|---|
| distribution | "Both installer entry points prepare the bundle and invoke platform integration logic ... The Bash installer reports optional extension build failures and continues the core install; a failed extension is not installed." | Holds. The Gemini monitor is built by the same `build_and_install_one_extension` / `Build-And-Install-One-Extension` function as the other four monitors, and `tests/installer/test_optional_extension_build.py` passes. |
| distribution | Delivery shapes, name precedence, owned-file writing | Unaffected. No adapter, flattening call or manifest path changed. |
| distribution | "Both installers activate user-attribution Git hooks from a digest-checked copy ..." | Holds. Hook activation is untouched. |
| distribution | "Inspect reported actions and actual installed files, then exercise the capability in its host." | Holds. The new section reports through the shared function's existing `[OK]` and "CLI not found" lines. |

No claim is false, and no source edit is needed.

## Build and render

The handbook output digest is unchanged, because the rendered page does not depend on installer content. The v4.13.11 [build receipt](../../../../archives/v4/v4.13/development/v4.13.11-phase-8-receipts/distribution-build.json) and [render receipt](../../../../archives/v4/v4.13/development/v4.13.11-phase-8-receipts/distribution-render.json) therefore still describe the current output and their recorded digests still verify. This follows the WN-30 precedent in the [v4.13.11 Phase 8 claim review](../../../../archives/v4/v4.13/development/v4.13.11-phase-8-handbook-claim-review.md), where an installer-only usage-monitor routing change refreshed only the installer digests.
