# Distribution Handbook Review: Settings Multi-Host Install

This record covers the distribution handbook after the settings branch changed three of its inputs: `scripts/installer.sh`, `scripts/installer.ps1`, and `scripts/lib/integrations/cursor.py`. The change surfaced when the branch was merged with `develop`, whose own refresh of the handbook evidence described the pre-branch versions of those files.

## Input Changes

- Both installers now install the Nexus-Hub Settings extension into every detected editor (VS Code, Cursor, and Antigravity) from one built package. Previously it installed into VS Code only. The shared install helper accepts a third optional host and loops over the extra hosts; a missing optional editor is skipped silently, and one host's install failure does not stop the others.
- The extension banner in both installers now says that Nexus-Hub Settings installs into every detected editor (VS Code, Cursor, and Antigravity), replacing the earlier "installs into VS Code only" line that no longer matched the install step.
- The Cursor integration registers `git-guardrails.sh`, `secret-scan.sh`, `user-edit-guard.sh`, and `large-file-guard.sh` on the generic `preToolUse` event instead of registering `git-guardrails.sh` alone on `beforeShellExecution`, and adds `user-edit-guard.sh` to `postToolUse` for the edit-preservation ledger. The three new guard scripts join the curated hook copy list.

## Claim Review

The handbook does not name the Settings extension, the editors it installs into, or Cursor's hook event names. Its one statement about extensions is that the Bash installer reports an optional extension build failure and continues the core install, and that a failed extension is not installed. That still holds: the build step is unchanged, and the per-host loop keeps a failed host from stopping either the remaining hosts or the core install. The statements about delivery shapes, name precedence, owned-file writing, attribution hooks, seeded defaults, and outcome inspection do not depend on the changed lines.

No handbook source, model, generated output, or rendered evidence changes. Only the input digests of the three changed files are refreshed, with this record as the content review. The build and rendered receipts stay valid because the handbook output digest is unchanged.
