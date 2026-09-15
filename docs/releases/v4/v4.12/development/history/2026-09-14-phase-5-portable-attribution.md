# Phase 5 - Portable user attribution

The user expanded v4.12.0 to protect fresh Nexus-Hub installations across supported agent platforms. The earlier history repair protected this repository only, so this phase adds a separate configured-user Git guard, installer activation, shared instructions and verification. See the [qualification record](../portable-attribution-evidence.md) for exact results and limits.

## Implementation

One standard-library Python helper owns installation, checks, message/identity enforcement, hook forwarding, checked tags and rollback. The existing CLI delegates to it. Both installers copy and activate it, while all 17 platform instruction templates load the same attribution policy. Claude's native attribution defaults are sourced and generated through the existing defaults pipeline. Existing human history and user settings remain subject to the documented preservation behavior.

## Troubleshooting and review

Real Git and installer runs found initialization-time hook discovery, Windows output decoding and interpreter alias issues. Independent review then found message validation ordering, special-hook presence semantics, streaming stdin, worktree scope and two interpreter-lifecycle defects. Each correction was exercised through its affected boundary; failing original receipts remain unchanged. The new tests also cover a second user's commit, a push with an existing remote baseline, outgoing agent history and human cherry-pick authorship.

## Documentation and phase gate

The final platform-source review found two instruction-delivery gaps: Cursor has no global Markdown instruction file, and Aider's native attribution defaults can annotate generated commits. The adapter changes add Cursor session-start policy context and Aider's documented flags/read list. A reviewer also caught a Python command-alias assumption; the new Cursor command uses the resolved interpreter. Actual installer tests execute that context command and inspect the generated Aider configuration.

The user guide, distributed style guide, decision record, platform defaults evidence and distribution handbook were updated. The handbook's retained design passed rendered and visual checks. CI adds the new tests to the Windows group and native macOS installer job, with Linux already covering the repository test tree. Local final qualification, one phase commit and normal integration are recorded in the qualification document. Release version mutation and publication follow the separate approved release flow.
