# Search-as-service MCP registry entries

**Out of scope**: shipping search-as-service, embeddings-as-service, scraping-as-service, or generation-as-service MCP snippets in `catalog/mcp-configs/mcp-servers.json`.

## Why this is out of scope

The [MCP Registry Policy](../../../AGENTS.md) (Hard-No List) forbids this class categorically. Named examples that have already been considered and rejected: Upstash/context7, Exa, Firecrawl, 21st.dev/magic-ui, Zilliz/claude-context.

The conflict is not taste. Those servers send query text, source, or prompts to a third-party processor the user did not already have as an intrinsic data destination, and they require new API keys and commercial relationships. That fails the policy decision tree before the trusted-vendor bucket: the capability is either skill-native, reverse-engineerable into a local internal MCP, or drop.

Nexus-Hub already took the reverse-engineer path where the job is real. Library-docs lookup is `local-docs-lookup`; HTTP fetch is the internal `nexus-web-fetch` MCP; keyword catalog search is `nexus-skill-server` / `nexus-code-search`. Wrapping the hosted originals would add outbound surface for no new capability.

Maintenance cost is permanent: every registry snippet is a subprocess users' agents will spawn. Keeping a hard-no list in AGENTS.md only works if repeat requests get this file instead of a new comparison row that re-argues the same five-question audit.

## Prior requests

- Policy source: [AGENTS.md Hard-No List](../../../AGENTS.md) and [docs/policy/mcp-reverse-engineering-matrix.md](../mcp-reverse-engineering-matrix.md).
- Original drop (v1.0.0): `docs/archive/v1/v1.0/plans/security-hardening-v100.md` (delete `context7`, `exa-web-search`, `firecrawl`, `magic-ui` from the registry) and the matching CHANGELOG removals.
- Recurring comparison pressure: `docs/archive/v2/v2.2/comparison-ECC.md` (N1, ECC bundled Exa/context7/Firecrawl/Magic UI) classified `drop-outright` for the same hard-no list.
- No dedicated GitHub issue is required to keep the decline in force; new requests should be answered with this file rather than re-opened as known-gaps `DF` rows.
