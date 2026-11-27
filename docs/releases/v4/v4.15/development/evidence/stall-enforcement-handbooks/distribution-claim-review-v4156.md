# Distribution Handbook Claim Review, CLI Help Delta

This review re-binds the unchanged distribution handbook to the candidate after one input changed: `scripts/nexus_hub_cli.py`.

## Delta

Between the recorded input (3475846d349f1a744b20f0efdcc724f8321181e5a3a06fa2b95f5805f6d3f40b) and the candidate (202bc000599bfbe61b9c6bbb093aee440f6f0d7e131bb6462010b4926dba602a), the file changed in two strings only: the module docstring and the `worktree` subcommand help text now list `prune-merged`. No installer step, adapter dispatch, ownership rule, or hidden-subprocess behavior changed.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not describe the `worktree` subcommand, so every existing claim stays accurate. All six retained model sections and source.md need no content, figure, anchor, slide, theme or output change.

## Proof

The builder's read-only check reproduced the retained output byte for byte (output sha256 244be8bb60f452da3ff8d1d705bc53afa33e0c9e224aae38a5463727f855ee65). Because the output bytes are identical, the earlier browser measurement of that exact output remains the rendered evidence.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication or release qualification.
