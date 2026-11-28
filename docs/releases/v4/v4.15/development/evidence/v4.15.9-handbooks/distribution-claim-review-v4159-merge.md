# Distribution Handbook Claim Review, v4.15.9 Integration

This review re-binds the unchanged distribution handbook to the v4.15.9 branch after merging develop at the v4.15.6 release. It covers every input whose digest differs from the develop snapshot.

## Delta

- `scripts/lib/integrations/_catalog_adapters.py` (v4.15.9): adds the `CLAUDE_ONLY_AGENT_KEYS` constant (`model`, `effort`), the agent frontmatter keys that every non-Claude agent delivery path strips.
- `scripts/lib/integrations/cursor.py` (both sides, disjoint regions): v4.15.9 passes `CLAUDE_ONLY_AGENT_KEYS` instead of the literal `("model",)` to `agents_dropping_keys`; develop registers the `implementation-state.sh` hook. The merged file keeps both changes.

No installer step, adapter dispatch order, ownership rule, optional-extension failure behavior, or hidden-subprocess behavior changed.

## Claims

The handbook explains installer-to-adapter translation, managed ownership, optional extension failure, and hidden subprocess behavior. It does not enumerate the agent frontmatter keys a platform drops or the Cursor hook list, so every existing claim stays accurate. No model section, source.md content, figure, anchor, slide, theme, or output changes.

## Proof

The builder's read-only check reproduced the retained output byte for byte. The recorded build and browser evidence for that exact output remain valid.

## Limits

This is a private, unsigned documentation attestation. It does not establish installed provider behavior, publication, or release qualification.
