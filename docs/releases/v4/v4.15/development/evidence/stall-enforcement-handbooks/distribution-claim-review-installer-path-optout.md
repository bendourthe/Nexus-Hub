# Distribution Handbook Claim Review, Installer PATH Opt-Out

This review re-binds the unchanged distribution handbook after two inputs changed: `scripts/installer.ps1` and `scripts/installer.sh`.

## Delta

- `scripts/installer.ps1` (363ae8cb71c88799c7a123fc83086db2a613fa80ba87154f9b10398b522f9029 to f968664975c71f68cb82770726faf158494e3a51f5ea252b44beb1715ca0522a): `Install-CliLauncher` no longer writes the bin directory to the user PATH when `NEXUS_HUB_NO_MODIFY_PATH=1` is set or when `USERPROFILE` is not the account's real profile folder. The `-NoModifyPath` switch behaves as before, and the help text names the new opt-out.
- `scripts/installer.sh` (2fdb4958a3c49000aaf7bcf6fc43aec679c878bb631186e57f2d22e5d25c2abd to 644af99ea11392f7c65e90998b643e676f6c6d70cbca9930b3e2ae62dc51a7c4): `install_cli_launcher` skips the shell profile edit when `NEXUS_HUB_NO_MODIFY_PATH=1`, matching `--no-modify-path`, and the help text names it.

Digests are computed over the committed (LF) bytes. No adapter dispatch, ownership rule, step order, or hidden-subprocess behavior changed.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It makes no statement about the user PATH or the CLI launcher directory, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
