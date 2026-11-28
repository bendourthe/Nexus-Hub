# Distribution Handbook Claim Review, v4.15.11 Release Version Delta

This review re-binds the unchanged distribution handbook to the v4.15.11 release commit after two inputs changed: `scripts/installer.ps1` and `scripts/installer.sh`.

## Delta

Each installer changed in one line only, the version constant:

- `scripts/installer.ps1` (61c850a1a55d222669cc22e537e24ab4bfedf52452b2ffcd2710e8fda95a3add to a0e4b7ed9d34172c519fe18a3d6bfb9911e8f7283fa80d25f165600053239358): `$script:NexusHubVersion` moved from "4.15.9" to "4.15.11".
- `scripts/installer.sh` (9c8522917d0fb4ab2bff4ecd29133dcc540a036f6e3aec8b31b66e3052008ba8 to f5a65a42fe47cab0273a431d7c5a95b42f4e8d30af804ba0da6653dffc3591c5): `NEXUS_HUB_VERSION` moved from "4.15.9" to "4.15.11".

The starting digests are the ones recorded by the v4.15.9 version delta, reviewed in [distribution-claim-review-v4159-version.md](../v4.15.9-handbooks/distribution-claim-review-v4159-version.md). Digests are computed over the committed (LF) bytes, and `scripts/installer.ps1` keeps its UTF-8 byte order mark. No installer step, adapter dispatch, ownership rule, or hidden-subprocess behavior changed, and no line moved.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not quote the installer version, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
