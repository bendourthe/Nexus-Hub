# Deferred Language Extractors -- v2.2.0

Phase 4 of the [codegraph-and-antigravity plan](plans/codegraph-and-antigravity.md) shipped the `nexus-code-search` v2.0 AST-extraction pipeline with two language extractors: `PythonExtractor` and `TypeScriptExtractor` (sub-task 4.3 / T025). This document records every language extractor that was intentionally deferred to v2.3.0+ and the rationale for each, satisfying the T025 prompt's requirement to "document the deferred languages ... one paragraph each on why each one is deferred to v2.3.0+" and the plan's item N2 ("C3-extended: Remaining ... framework extractors").

These are deferrals, not rejections. The structured carry-forward entry is `DF-002` in [known-gaps.md](known-gaps.md), which the next version's `/generate-plan` reads to decide what to ingest.

## Why ship only two languages first

The deferral is an architecture-validation decision, not a technical blocker. Shipping Python and TypeScript first proves the end-to-end pipeline (tree-sitter parse -> NodeKind/EdgeKind extraction -> SQLite/FTS5 persistence -> call-graph traversal -> MCP tools -> eval harness) against two structurally different language families (dynamically-typed indentation-scoped Python vs. statically-typed brace-scoped TypeScript) before paying the long-tail cost of porting the remaining grammars. Each additional language is a bounded, repeatable unit of work, so deferring them carries no design risk.

## How a new extractor is added (the shape every deferred language follows)

Adding a language is additive and local. Each extractor is a new subclass of `Extractor` (`extensions/nexus-code-search/src/nexus_code_search/extraction/languages/base.py`) that implements `extract(file_path, source) -> tuple[list[Node], list[Edge]]` using tree-sitter s-expression queries, plus one registry entry mapping the language's file extensions to the class in `LANGUAGE_EXTRACTORS` (`extensions/nexus-code-search/src/nexus_code_search/extraction/languages/__init__.py`). No schema migration is required: the `NodeKind` (22 kinds) and `EdgeKind` (12 kinds) taxonomies in `types.py` already cover the symbol and relationship vocabulary every mainstream language needs. The canonical reference implementation to copy is `extraction/languages/python.py`.

## Deferred languages

Each language below is deferred to v2.3.0+. The common gating factor is the long-tail porting cost described above; the per-language notes call out anything specific (grammar maturity, ABI fit with the pinned `tree-sitter>=0.24,<0.26` runtime, or a distinctive structural feature the extractor must handle).

- **JavaScript (plain `.js` / `.jsx` / `.mjs`)**: The shipped `TypeScriptExtractor` already parses the TypeScript superset, so plain JavaScript is the lowest-effort port (it reuses the same tree-sitter grammar family minus type annotations). It is deferred only because v2.2.0 froze the extractor surface after validating two families; expect it as the first batch in v2.3.0 since the marginal cost is a registry entry plus a thin query subset.

- **Go**: `tree-sitter-go` is mature and ABI-compatible, and Go's explicit package/struct/interface model maps cleanly onto the existing NodeKind set (`struct`, `interface`, `function`, `method`). Deferred for sequencing only; it is a strong candidate for an early v2.3.0 batch given the repository's own Go style rules.

- **Rust**: `tree-sitter-rust` covers `struct`, `trait`, `enum`, and `impl` blocks, all of which already exist as NodeKinds (`struct`, `trait`, `enum`, `enum_member`). The extra work is resolving `impl` method association and trait `implements` edges, which is a bounded extension of the same in-file resolution pattern Python and TypeScript use. Deferred to keep the v2.2.0 extractor count at two.

- **Java**: `tree-sitter-java` is well maintained and the class/interface/method model is a direct NodeKind fit. The notable extra is annotation handling (`decorates` edges for `@Override`, framework annotations), which dovetails with the framework-resolver layer rather than the base extractor. Deferred to v2.3.0.

- **C# (`.cs`)**: `tree-sitter-c-sharp` is mature; namespaces, classes, structs, interfaces, and properties all map to existing NodeKinds (`namespace`, `class`, `struct`, `interface`, `property`). Partial classes and `using` aliasing add modest resolution work. Deferred for sequencing.

- **PHP**: `tree-sitter-php` handles the mixed-mode (HTML + PHP) source model that distinguishes PHP from the shipped languages. That mixed-mode parsing is the one piece needing care, so it is deferred until the extractor harness has a documented pattern for multi-language files (also relevant to Svelte/Vue/Liquid below).

- **Ruby**: `tree-sitter-ruby` is mature, but Ruby's open classes, metaprogramming (`define_method`, `method_missing`), and module mixins make precise `calls`/`references` resolution harder than in statically-scoped languages. Deferred so the in-file resolution upgrades tracked in `WN-6` (constructor/override resolution) can land first and inform the dynamic-dispatch approach.

- **C**: `tree-sitter-c` is stable and the function/struct/variable model is simple, but accurate call-graph resolution depends on preprocessor macro expansion, which tree-sitter does not perform. Deferred until a documented macro-handling stance exists (most likely: index the pre-expansion source and accept reduced macro-call recall).

- **C++**: `tree-sitter-cpp` is mature but C++ is the highest-complexity grammar in this list (templates, overloading, multiple inheritance, namespaces, the same preprocessor caveat as C). It is deferred to a later v2.3.0+ batch precisely because it stresses every resolution edge case at once and is best ported after the simpler languages have hardened the shared resolver.

- **Swift**: `tree-sitter-swift` exists but has historically lagged the tree-sitter core ABI; its compatibility with the pinned `tree-sitter>=0.24,<0.26` runtime must be re-verified before the port (see `WN-5` for the equivalent pin caveat that already bit `tree-sitter-languages`). Deferred pending that grammar-version check.

- **Kotlin**: `tree-sitter-kotlin` is community-maintained with less coverage than the JVM-sibling Java grammar. Kotlin's null-safety syntax, extension functions, and coroutine builders need extractor-side handling. Deferred to v2.3.0+, likely batched alongside Java given the shared JVM ecosystem.

- **Scala**: `tree-sitter-scala` is community-maintained; Scala's implicits, given/using, and trait-linearization semantics make precise edge resolution non-trivial. Deferred as a lower-demand JVM language to be scheduled after Java and Kotlin.

- **Dart**: `tree-sitter-dart` supports the class/mixin/function model used by Flutter codebases. Deferred on demand-priority grounds; it becomes a clear candidate if Nexus / Nexus-Hub users surface Flutter projects.

- **Lua**: `tree-sitter-lua` is mature and small, but Lua's table-as-everything model means "methods" and "fields" are runtime table assignments rather than syntactic declarations, so symbol extraction relies on heuristics. Deferred until those heuristics are specified.

- **Luau**: Roblox's typed Lua dialect has its own `tree-sitter-luau` grammar. It shares Lua's table-based resolution challenge plus dialect-specific type syntax. Deferred as a niche dialect, naturally batched after Lua.

- **Svelte**: `.svelte` files are multi-language single-file components (HTML template + `<script>` TypeScript/JavaScript + `<style>` CSS). Extracting the script block requires the same multi-language file handling noted for PHP, plus Svelte-specific reactive-statement and component-import semantics. Deferred until the multi-language-file pattern is documented.

- **Vue**: `.vue` Single-File Components have the same multi-block structure as Svelte (`<template>` / `<script>` / `<style>`), often with `<script setup>` Composition-API sugar. Deferred for the same multi-language-file reason and naturally batched with Svelte.

- **Liquid**: Liquid is a templating language (Shopify themes, Jekyll) embedded in HTML. Its "symbols" are tags, filters, and variable assignments rather than functions/classes, so it maps onto NodeKinds awkwardly and is the least conventional fit in this list. Deferred until a template-language extraction model is defined.

- **Pascal / Object Pascal**: `tree-sitter-pascal` exists but Pascal/Delphi is a low-demand legacy target for this catalog. The unit/procedure/function model maps onto existing NodeKinds, so the port is straightforward whenever a concrete user request arrives. Deferred as the lowest-priority item.

## Prioritization for v2.3.0+

There is no fixed order. New extractors are added as v2.3.0+ tickets arrive, prioritized by Nexus / Nexus-Hub user demand and measured against the eval baseline in [eval-baseline.md](eval-baseline.md). The expected early batch (lowest marginal cost, highest likely demand) is plain JavaScript, Go, and Rust; the multi-language-file family (Svelte, Vue, PHP, Liquid) is gated on first documenting a shared multi-block extraction pattern; C++ is deferred to last among the systems languages because it exercises every resolver edge case simultaneously.

## Related

- [known-gaps.md](known-gaps.md) -- `DF-002` (the structured carry-forward entry), `WN-5` (tree-sitter pin), `WN-6` (in-file call resolution upgrades).
- [plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) -- Phase 4 sub-task 4.3 (T025) and item N2.
