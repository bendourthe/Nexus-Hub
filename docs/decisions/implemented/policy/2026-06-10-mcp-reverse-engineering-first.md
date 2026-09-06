# Decision: Govern the MCP registry by a reverse-engineering-first decision tree

Status: implemented - every registry entry must stop at the first matching bucket, and search / embeddings / scraping / generation as a service are categorically refused

## Problem

`catalog/mcp-configs/mcp-servers.json` is a curated registry that users copy into their own settings. Each entry causes a user's agent to spawn a local subprocess that may reach an external API. Every entry is therefore a security decision made on behalf of users who will not audit it.

Without a stated rule, the registry drifts toward "useful things people asked for", and each individual addition looks reasonable in isolation while the aggregate quietly becomes a set of third-party data processors sitting between the user's source code and a vendor.

## Decision

Every proposed entry walks a decision tree and stops at the first bucket that fits:

1. **Local-only** (internal servers, or zero-outbound official servers) - always allowed.
2. **LLM-native skill** - if the agent's own model can do it by instruction, ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP** - if the logic can run locally, build the internal equivalent under `extensions/`.
4. **Trusted vendor wrapper** - only when the vendor is the intrinsic data destination, reverse-engineering is not viable, AND the feature is extremely worth it. All three justified in the entry's `_comment`.
5. **Otherwise** - drop.

Search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service are a categorical no regardless of tree position. Every entry answers five audit questions in its `_comment`, and every entry has a row in `docs/policy/mcp-reverse-engineering-matrix.md`.

## Alternatives considered

- **Curate case by case on merit.** Rejected: this is what produces drift. Without a tree, each decision is argued from scratch and the precedent is whatever was decided last.
- **Allow any popular MCP with a security review.** Rejected: a review checks whether a server is malicious, which is the wrong question. The question is whether source code, prompts, or query text should leave the machine at all, and a well-behaved server still exfiltrates by design.
- **Ban all third-party MCPs outright.** Rejected as too strict: where a user is already a customer of a vendor and that vendor is the intrinsic destination (their own GitHub, their own database), a wrapper adds no new data-flow surface.
- **Attribute reverse-engineered work to its upstream source in the shipped artifact.** Rejected separately: attribution belongs in the matrix row's rationale, not in the distributed artifact, which uses generic descriptive names.

## Consequences

- Some genuinely useful capabilities are refused, and the refusal is the feature. The categorical no-list exists so those cases are not re-argued individually.
- Reverse-engineering costs real implementation effort that adopting an upstream package would not, paid to keep the zero-outbound property.
- Every registry addition now carries mandatory documentation overhead: a `_comment` answering five questions and a matrix row with upstream evidence.
- The tree's ordering is load-bearing. Because it stops at the first match, a capability achievable by a skill can never be justified as a vendor wrapper, no matter how convenient the wrapper is.
