# Context Provider Contract

Context providers let local non-code artifacts contribute native nodes and edges to the existing SQLite graph. The shipped provider set is intentionally small: only Markdown heading structure is included. Additional ecosystems are extension points, not commitments.

## Interface

A provider subclasses `ContextProvider` under `nexus_code_search.frameworks`, declares a non-empty `file_patterns` tuple, and implements `resolve(file_path, source, existing_nodes)`. The orchestrator reads matched bytes under the same size, ignore, symlink, and repository-root constraints as code files, then gives the provider only the relative path, bytes, and existing in-memory nodes.

The provider returns standard `Node` and `Edge` values. New-node local identifiers begin at `len(existing_nodes)`, matching the established framework-resolver contract. The orchestrator owns SQLite writes and isolates provider failures, so providers receive no database handle.

## Local-Only Rule

Providers are deterministic parsers. They must not open a connection, read a credential, invoke a model, run a subprocess, write outside the graph index, or import an HTTP client. Tests execute every shipped provider with socket connections blocked and statically reject network or credential surfaces in the provider implementation.

## Shipped Markdown Provider

`MarkdownContextProvider` handles `*.md`, emits one `module` node per ATX heading, and emits `contains` edges that preserve the heading hierarchy. It intentionally does not parse links, fetch linked pages, render Markdown, or infer semantic relationships.

## Adding a Provider

1. Add a focused provider module under `nexus_code_search.frameworks`.

2. Register one instance in `CONTEXT_PROVIDERS`.

3. Add a fixture proving pattern matching, exact nodes and edges, orchestrator discovery, searchability, deterministic failure isolation, and successful execution with socket connections blocked.

4. Keep the provider set narrow. Prefer one broadly useful local format over ecosystem-specific adapters without a demonstrated repository use case.
