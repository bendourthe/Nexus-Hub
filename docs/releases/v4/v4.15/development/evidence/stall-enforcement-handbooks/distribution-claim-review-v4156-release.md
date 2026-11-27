# Distribution Handbook Claim Review, Release Version Delta

This review re-binds the unchanged distribution handbook to the v4.15.6 release candidate after two inputs changed: `scripts/installer.ps1` and `scripts/installer.sh`.

## Delta

Each installer changed in one line only, the version constant:

- `scripts/installer.ps1` (2ddeb6a4645a22753fda4781c1e37f0381d37a8ba62d64e291d1c18f6ffd8285 to 6900a4fce84934637da7c363cba74f840c0dcd8ad17bbc34fb7296c37b00deff): `$script:NexusHubVersion` moved from "4.15.5" to "4.15.6".
- `scripts/installer.sh` (655feabb16d2d53a94a86a7ea1819e18331082486b65ce01799d8a146f70e6e8 to 239a3b282996ce23bd5b9a289281627a31933c5ff7b08f59d8686892d62c4c5f): `NEXUS_HUB_VERSION` moved from "4.15.5" to "4.15.6".

No installer step, adapter dispatch, ownership rule, or hidden-subprocess behavior changed, and no line moved.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not quote the installer version, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
