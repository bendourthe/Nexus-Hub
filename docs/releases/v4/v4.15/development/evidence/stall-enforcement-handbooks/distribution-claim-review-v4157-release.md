# Distribution Handbook Claim Review, Release Version Delta

This review re-binds the unchanged distribution handbook to the v4.15.7 release candidate after two inputs changed: `scripts/installer.ps1` and `scripts/installer.sh`.

## Delta

Each installer changed in one line only, the version constant:

- `scripts/installer.ps1` (6900a4fce84934637da7c363cba74f840c0dcd8ad17bbc34fb7296c37b00deff to 363ae8cb71c88799c7a123fc83086db2a613fa80ba87154f9b10398b522f9029): `$script:NexusHubVersion` moved from "4.15.6" to "4.15.7".
- `scripts/installer.sh` (239a3b282996ce23bd5b9a289281627a31933c5ff7b08f59d8686892d62c4c5f to 2fdb4958a3c49000aaf7bcf6fc43aec679c878bb631186e57f2d22e5d25c2abd): `NEXUS_HUB_VERSION` moved from "4.15.6" to "4.15.7".

Digests are computed over the committed (LF) bytes. No installer step, adapter dispatch, ownership rule, or hidden-subprocess behavior changed, and no line moved.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not quote the installer version, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
