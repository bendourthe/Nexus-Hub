---
name: direct-corpus-interaction
description: "Apply a direct-corpus-interaction (DCI) search discipline: anchor with semantic retrieval, then grep, trace, and read to verify exact strings, versions, and error codes before answering. Use when searching code or hitting a retrieval dead end."
summary_l0: "Search code with a hypothesis-refine-anchor-verify discipline over hybrid retrieval plus direct corpus tools"
overview_l1: "This skill codifies Direct Corpus Interaction (DCI): the discipline of treating retrieval as an iterative loop rather than a one-shot vector lookup. Pure-vector RAG decides too early what the agent is allowed to see and breaks on exact-string, version-constraint, and multi-hop tasks. DCI fixes this by using semantic retrieval only for a broad anchor, then expanding laterally with grep, call-graph tracing, and direct file reads to verify exact constraints before answering. The agent forms a hypothesis, refines the query when results are thin, recognizes dead ends, expands from an anchor document, and confirms exact strings, versions, and error codes against source. Crucially it never pre-filters evidence out of the reasoning loop. Trigger phrases: search the codebase, find where X is defined, why does this fail, DCI, grep for, trace callers, verify the exact version, hybrid retrieval discipline."
---

# Direct Corpus Interaction (DCI)

Treat code search as an iterative hypothesis-refine loop, not a single vector lookup. Semantic retrieval is good at broad recall ("roughly where does auth live?") but decides too early what the agent sees and is unreliable for exact strings, version constraints, and multi-hop questions. DCI uses semantic recall for an anchor, then interacts with the raw corpus directly (grep, call-graph trace, read) to expand laterally and verify exact constraints before answering.

This skill makes that discipline explicit so the agent stops answering from a single embedding hit and starts proving its answer against source.

## When to Use This Skill

Use when:

- Searching a codebase for where something is defined, used, or configured.
- A question hinges on an exact string, a version constraint, an error code, a flag name, or a config key (embeddings paraphrase; they do not preserve exact tokens).
- The first retrieval pass returned thin, off-target, or contradictory results (a dead end that needs query refinement, not a confident guess).
- The answer requires multiple hops (caller -> callee -> definition -> test) that no single chunk contains.
- You are about to state a fact about the code ("X calls Y", "the default is 60", "this throws E_FOO") and have not yet read the line that proves it.

**When NOT to use:**

- A purely conceptual question with no corpus to interact with ("what is RRF?") -- answer directly.
- A one-line lookup you already have open in context -- just read it.
- Generating new code from a clear spec -- that is authoring, not retrieval (use [[plan-before-code]]).

## The DCI Loop

```
1. HYPOTHESIZE   State what you expect to find and where (one sentence).
2. ANCHOR        Use semantic / hybrid retrieval for a broad candidate region.
3. EXPAND        From the anchor, go lateral with exact tools: grep the symbol,
                 trace callers/callees, read the neighboring files.
4. VERIFY        Confirm the exact string / version / error code against the
                 source line. Cite file:line.
5. REFINE / STOP If results are thin or wrong, refine the query and loop to 2.
                 If a dead end, say so and change the hypothesis -- do not guess.
```

The loop ends only when a source line has been read that proves the answer, or when the agent has explicitly recognized a dead end and reformulated.

## Instructions

### 1. Anchor with broad recall, do not stop there

Start with semantic or hybrid retrieval to find the candidate region. In Nexus the substrate is `HybridRetriever` (BM25 lexical + dense semantic + graph, fused via Reciprocal Rank Fusion at `k=60`). Treat the top hit as a *starting point*, never as the final answer.

### 2. Expand laterally with exact tools

From the anchor, interact with the corpus directly:

- `grep_codebase` (or `grep` / ripgrep) for the exact symbol, string, flag, or error code.
- The code-graph MCP (`codegraph_trace`, `callers`, `callees`) to walk the dependency edges the embedding cannot see.
- `read_file` on the anchor and its neighbors to read surrounding context, not just the matched line.

Lateral expansion is where multi-hop answers are actually assembled.

### 3. Verify exact constraints against source

Embeddings paraphrase; they will happily return a chunk that is *about* the topic but has the wrong default value, the wrong version, or a renamed flag. Before stating any exact fact, read the line that contains it and cite `file:line`. If the question is "what version", grep the manifest, do not trust a summary.

### 4. Recognize dead ends and refine

If retrieval returns thin or contradictory results, that is signal, not failure. Refine the query (different symbol, broader or narrower term, a known-adjacent file) and loop. State the dead end explicitly ("no match for `X`; the symbol may be named `Y` after the v2 rename") rather than fabricating a confident answer from a weak hit.

### 5. Never pre-filter evidence out of the loop

Do not discard candidate matches before reasoning over them because they "look irrelevant". Retrieval quality depends on the resolution of the interface (grep, trace, read), not on better embeddings or a larger context window. Let the agent see the raw corpus and decide.

## Hybrid retrieval: where DCI fits

DCI is not "grep instead of vectors" -- it is the precision verification layer on top of broad semantic recall. The recommended end-state is hybrid:

| Stage | Method | Strength |
|---|---|---|
| Broad recall | Semantic / dense + BM25, fused via RRF | Finds the rough region from a fuzzy description |
| Lateral expansion | Call-graph trace (callers / callees) | Walks structural edges embeddings miss |
| Exact verification | grep / read exact lines | Confirms strings, versions, error codes |

A pre-built index (e.g. an FTS5-backed code-graph) answers exact-match queries without re-running grep over the whole tree, so prefer the index when one exists and fall back to raw grep otherwise.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The top semantic hit looks right, I will answer from it" | The top hit is an anchor, not a proof. Embeddings paraphrase and routinely return chunks with the wrong default, version, or renamed flag. Read the source line before stating an exact fact. |
| "Grep is slow / noisy, the vector result is good enough" | For exact strings, version constraints, and error codes, the vector result is the unreliable one. A scoped grep or a code-graph trace is both faster to trust and more precise than re-reading a fuzzy chunk. |
| "No match means it does not exist" | A dead end usually means the query was wrong (a rename, a different symbol, a generated file). Refine the query and loop; do not conclude absence from one miss. |
| "I will pre-filter the candidates to save context" | Pre-filtering before reasoning is exactly the failure DCI prevents -- it discards the evidence that would have changed the answer. Let the agent see the raw matches. |
| "Multi-hop is too much work, one chunk is enough" | If the answer spans caller -> callee -> definition, no single chunk contains it. Tracing the edges is the only way to assemble a correct multi-hop answer. |

## Verification

- [ ] Every exact claim (string, version, default, error code, flag) is backed by a read source line cited as `file:line`.
- [ ] The answer used at least one lateral-expansion step (grep, call-graph trace, or neighbor read) beyond the initial semantic hit when the question was non-trivial.
- [ ] When retrieval returned thin or contradictory results, the query was refined and the loop repeated (a dead end was named, not guessed past).
- [ ] No candidate evidence was discarded before being reasoned over.
- [ ] Multi-hop questions traced the actual edges rather than answering from a single chunk.

## Related Skills

- [[code-semantic-search]] -- the retrieval *implementation* (AST chunking, hybrid search); this skill is the *discipline* for using it well.
- [[rag-implementation]] -- builds the vector pipeline DCI deliberately looks past for exact-constraint tasks.
- [[bug-localization]] -- a concrete application of the DCI loop: anchor on the stack trace, then trace and read to the faulting line.
- [[context-engineering]] -- shapes WHAT enters the context; DCI shapes HOW evidence is gathered and verified before it does.
- [[context-manager]] -- budgets attention across a large corpus that DCI then interrogates precisely.
