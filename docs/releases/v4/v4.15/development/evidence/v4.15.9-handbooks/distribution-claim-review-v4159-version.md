# Distribution Handbook Claim Review, v4.15.9 Release Version Delta

This review re-binds the unchanged distribution handbook to the v4.15.9 release commit after two inputs changed: `scripts/installer.ps1` and `scripts/installer.sh`.

## Delta

Each installer changed in one line only, the version constant:

- `scripts/installer.ps1` (f968664975c71f68cb82770726faf158494e3a51f5ea252b44beb1715ca0522a to 61c850a1a55d222669cc22e537e24ab4bfedf52452b2ffcd2710e8fda95a3add): `$script:NexusHubVersion` moved from "4.15.7" to "4.15.9".
- `scripts/installer.sh` (644af99ea11392f7c65e90998b643e676f6c6d70cbca9930b3e2ae62dc51a7c4 to 9c8522917d0fb4ab2bff4ecd29133dcc540a036f6e3aec8b31b66e3052008ba8): `NEXUS_HUB_VERSION` moved from "4.15.7" to "4.15.9".

The starting digests are the ones recorded after the PATH opt-out change, which is reviewed in [distribution-claim-review-installer-path-optout.md](../stall-enforcement-handbooks/distribution-claim-review-installer-path-optout.md) and [distribution-claim-review-v4159-release.md](distribution-claim-review-v4159-release.md). Digests are computed over the committed (LF) bytes. No installer step, adapter dispatch, ownership rule, or hidden-subprocess behavior changed, and no line moved.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not quote the installer version, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
