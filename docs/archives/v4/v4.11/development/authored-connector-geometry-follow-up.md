# Authored connector geometry follow-up

This release-scoped record qualifies the v4.11 MT-10 exact-path candidate for maintainers reviewing protected integration. It preserves the [original qualification](authored-connector-geometry-qualification.md), where all four diagrams were `unchecked`, and records only the new local result.

## Supported boundary

The routing check admits declared `<path data-edge="...">` connectors with explicit inherited `fill="none"` and one argument group per absolute `M`, `L`, `H`, `V`, `C`, or `Z` command. It rejects potentially filled paths, implicit argument repetition, other commands, unmarked paths, malformed or non-finite coordinates, unsupported transforms, and exhausted budgets as `unchecked`. A straight segment intersects an unrelated rectangle only when it enters its interior; boundary-only contact is `unchecked`. A cubic is never flattened into a polyline: repeated control-hull subdivision proves disjointness or interior crossing, and unresolved contact is `unchecked`. Nonpainted marker definitions are excluded while retaining their resource cost.

The label-occlusion check admits the same authored diagram only because every painted connector path precedes the labels. A path painted after a label leaves the SVG `unchecked`. This check still decides later opaque rectangle occlusion, not every possible path-label overlap or source-fidelity claim.

## Local evidence, 2026-09-23

- The unchanged retained Phase 6 `report-final/pilot.html` has horizontal SVGs 7 and 17 and vertical SVGs 8 and 18. Both checks returned `pass` with one checked SVG for each isolated diagram. The whole page returned `pass` for routing with four checked SVGs and explicit unchecked coverage for its other path-based SVGs; label occlusion returned `pass` with 23 checked SVGs under its paint-order envelope.
- An unrelated rectangle inserted beneath the actual horizontal return curve changed routing from `pass` to `fail`. Separate straight, diagonal, and cubic crossing controls fail; clear and attached connectors pass; unsupported arcs, ambiguous tangencies, unmarked filled paths, paths with no drawn segment, paths painted after labels, and non-finite geometry remain `unchecked` where applicable.
- The pre-edit visual-QA module passed 94 tests. After the candidate and new controls, it passed 112 tests, including a red-first filled-path regression. The scorer passed Ruff; `git diff --check` and the repository fast profile are final publication gates.

## Closure gate

This is a local candidate, not a merged result. Keep MT-10 open until the protected pull request passes required checks, merges to `develop`, and post-merge smoke/provenance pass. MT-5 temporal source-value mapping and MT-9 generic inert controls remain separate open items.

## Publication result

PR #269 passed 21 hosted checks with one expected skip, merged to `develop` as `91617927` on 2026-09-24 UTC, and post-merge run 35940086752 passed smoke and provenance. MT-10 is closed for the declared `data-edge` path envelope. The original all-`unchecked` qualification above remains historical evidence, and MT-5 and MT-9 remain open.
