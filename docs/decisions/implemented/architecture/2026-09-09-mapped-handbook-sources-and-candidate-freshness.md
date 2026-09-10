# Decision: Mapped handbook sources and candidate freshness

Status: implemented - Preserve native handbook layouts and verify mapped sources and rendered evidence against the release candidate.

This decision governs living handbook source/output ownership and release freshness for maintainers updating documentation. It supersedes the fixed-folder and empty-source no-op portions of the 2026-08-24 living-docs decision; its release snapshots and separate decisions tree remain valid.

## Problem

A universal Markdown folder misses authored topic HTML and native generators. An empty-folder no-op permits a release with no explanation of enduring code behavior, and timestamps do not prove that existing explanations match the candidate.

## Decision

Keep `docs/handbooks/` living. Use an existing source/output map or a small `handbooks.json`; preserve legacy Markdown/HTML pairs and topic layouts without automatic migration. Retain editable inputs and generated output ownership. Full refresh discovers every eligible HTML, reviews code claims and verifies final rendered output before release version mutation. Missing inputs preserve originals and block completion. Bootstrap a focused overview and relevant technical material from actual code. Explicit narrow scope remains narrow; presentation opt-outs remain recorded exceptions.

## Alternatives considered

- Require one folder layout: rejected because native and authored sources have different valid layouts.
- Count an empty source folder as success: rejected because it hides missing documentation.
- Regenerate with an agent on every check: rejected because freshness checks must be read-only and unchanged output must remain stable.

## Consequences

The documentation owner performs semantic refresh and browser review; a small checker detects stale source, builder, output and evidence hashes. Hashes cannot establish semantic correctness by themselves. Release rechecks the integrated candidate and any version-dependent outputs. Snapshots retain rebuild inputs and described-version identity; live handbooks remain in place. Historical decisions are preserved.
