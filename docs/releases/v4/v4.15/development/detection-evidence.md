# Model Detection Evidence

**Date**: 2026-10-31
**Base**: `ff69aff882f5cc825939507d326edce904ce65eb`
**Plan**: [v4.15.1](../plans/v4.15.1-adoption-model-adaptive-harness.md)
**Scope**: Metadata-only experiment and current first-party documentation. This is not an installed runtime or model-switch qualification.

## Detection channels

The [Claude Code hooks reference](https://code.claude.com/docs/en/hooks), fetched on 2026-10-31, says only SessionStart may receive an optional model field. Model-switch events use from_model and to_model. UserPromptSubmit has no documented model field. The reference states, "There is no `$CLAUDE_MODEL` environment variable". A user-set ANTHROPIC_MODEL does not follow interactive switches. The local CLAUDE_MODEL variable was absent; that observation is not a universal host proof.

The same reference documents effort.level for tool-context events on supporting models. It does not promise the field on every event, so the frozen plan's unconditional standard-payload assumption is too broad. UserPromptSubmit context is delivered alongside its prompt, rather than by rewriting the initial instruction prefix. These are documentation findings, not a measured cache hit.

The third channel was exercised against an existing local Claude transcript, independently of the Codex host running this evidence task. Only message.model was returned. No conversation text, prompt, tool result, or transcript copy was emitted or persisted.

## Real boundary exercise

A scratch-only Python CLI accepted a JSON hook-shaped payload containing a local transcript path. Its session directory was explicitly pinned. The regular-file check preceded reading; open-file identity was checked against the inspected file; the tail read was capped at 262,144 bytes; candidate lines above 65,536 bytes were skipped; malformed lines were ignored while scanning backward. I/O and parsing failures used constant enum reasons, never exception text. No cache, debug file, telemetry, or outbound call was created.

The source transcript was an existing 5,791,065-byte local Claude session. The executable boundary returned exit 0, no stderr, and exactly:

```text
claude-opus-5-5
```

The real-file resolver ran 101 times in the same local process: p50 0.6470 ms and p95 1.0941 ms. This measures the bounded resolver, not process startup, installed hook delivery, model execution, or an end-to-end prompt delay.

| Control | Observation |
|---|---|
| Valid fixture followed by an incomplete final record | `claude-fixture-only` |
| Valid fixture followed by a line above the candidate-line cap | `claude-fixture-only` |
| Missing file | `unresolved: missing` |
| Directory | `unresolved: nonregular` |
| Invalid payload shape | `unresolved: invalid-payload` |
| Regular file outside the pinned session directory | `unresolved: outside-session` |
| File symlink | NOT RUN: local Windows symlink privilege unavailable |

The two fixture observations exercise parsing recovery; they are not real-model measurements. The actual model value above comes from the real Claude transcript. No interactive mid-session switch was performed, so switch tracking remains unqualified.

## Seed and privacy cost

A SessionStart value does not automatically remain available to a later independent UserPromptSubmit process. A seed-based design would require explicit state persistence or another documented host mechanism, adding state ownership, write permissions, freshness, cleanup, and privacy obligations. This plan creates none of that state.

A future resolver would be authorized to extract message.model only. It would not gain authority to read for meaning, summarize, transmit, or act on conversation content. The temporary parser necessarily traversed bounded JSON records to locate the allowed field; no other field was recorded. The synthetic fixtures contained no private session content.

## Reproduction limits and teardown

The experiment used Python standard-library file metadata, bounded binary reads, JSON parsing, subprocess execution, and monotonic timing. The measured parameters, input sizes, outputs, sample count, and percentiles are recorded above. The private transcript path and its contents are deliberately not published. The scratch executable is deleted within this phase, so these results remain a historical experiment rather than a reusable shipped resolver.

The 7,761-byte scratch prototype had SHA-256 `1b5293400f7360192449d3a7f18429dde93b4a960eab27b4a2b9124b3a16d3d5`. Its exact resolved path was checked before removing only that file. The terminal check printed `prototype_absent=True`; `git status --short -- catalog scripts .github` printed no paths. No executable artifact remains in the committed tree or the experiment directory.


## Candidate Refresh (2026-11-08)

**Integration input:** `1dc21b92db664347d18ff591e02e1e73c0d8c867`. **Current source:** 70 models and 610 claims; LF SHA-256 `8e4e39de9c2cba3d2ee1baa076705af9eedafcfcf7e14edee47aaa5a9afd70c9`. The earlier sections above are the dated 2026-10-31 snapshot and remain historical evidence.

The first-party [hooks reference](https://code.claude.com/docs/en/hooks) was re-fetched and its common input, SessionStart, UserPromptSubmit, PreModelSwitch, PostModelSwitch and context-placement sections inspected on 2026-11-07 at 23:06:12 UTC. The optional model field remains limited to SessionStart and may be omitted; switch events use from_model and to_model. UserPromptSubmit documents prompt and optional session_title without a model field. The reference still states no CLAUDE_MODEL variable exists, and a user-set ANTHROPIC_MODEL does not follow interactive switches. Effort is conditional on supporting models and tool-context events, not unconditional standard payload data. Additional context accompanies the submitted prompt.

This is a documentation refresh, not a new runtime observation. The earlier real model value and 101-call p50/p95 remain dated measurements. No transcript, live environment value, model call, installed hook, interactive switch or cache trace was read or exercised for this refresh. SessionStart seeding still needs separately designed state ownership and privacy controls; this plan implements none.
