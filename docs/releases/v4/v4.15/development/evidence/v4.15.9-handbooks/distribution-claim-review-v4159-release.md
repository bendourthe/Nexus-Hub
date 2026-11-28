# Distribution Handbook Claim Review, v4.15.9 Release

This review re-binds the unchanged distribution handbook to the v4.15.9 release branch, which combines the v4.15.9 member, the action-restatement guard, and the installer PATH opt-out fix. It covers every input whose digest differs from the v4.15.7 release snapshot.

## Delta

- `scripts/lib/integrations/_catalog_adapters.py` and `scripts/lib/integrations/cursor.py` (v4.15.9): the `CLAUDE_ONLY_AGENT_KEYS` constant (`model`, `effort`) and its use in Cursor's agent delivery. Reviewed in [distribution-claim-review-v4159-merge.md](distribution-claim-review-v4159-merge.md).
- `scripts/installer.ps1` and `scripts/installer.sh` (installer PATH opt-out): the persistent PATH write is skipped on `-NoModifyPath` / `--no-modify-path`, on `NEXUS_HUB_NO_MODIFY_PATH=1`, and, on Windows, when `USERPROFILE` points away from the real profile. Reviewed in [distribution-claim-review-installer-path-optout.md](../stall-enforcement-handbooks/distribution-claim-review-installer-path-optout.md).

No installer step order, adapter dispatch, ownership rule, optional-extension failure behavior, or hidden-subprocess behavior changed.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not describe agent frontmatter key stripping, the Cursor hook list, or the PATH opt-out conditions, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte. The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
