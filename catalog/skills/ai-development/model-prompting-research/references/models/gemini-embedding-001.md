# Prompting Profile: gemini-embedding-001

**Platform**: gemini
**Last verified**: 2026-11-04
**Roster provenance**: `api`

This file mirrors the `models["gemini-embedding-001"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
| Set the task_type field in the embedContent method to optimize gemini-embedding-001 embeddings for the intended use. Supported values are SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, CODE_RETRIEVAL_QUERY, QUESTION_ANSWERING and FACT_VERIFICATION. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |
| For retrieval with gemini-embedding-001, embed queries with RETRIEVAL_QUERY and the documents to be retrieved with RETRIEVAL_DOCUMENT. CODE_RETRIEVAL_QUERY, QUESTION_ANSWERING and FACT_VERIFICATION query-side types are likewise paired with RETRIEVAL_DOCUMENT for the corpus side. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |
| gemini-embedding-001 outputs 3072-dimensional vectors by default. Use the output_dimensionality parameter to shrink them. Supported range is 128 to 3072, and the recommended sizes are 768, 1536 and 3072. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-001) |
| With gemini-embedding-001, any embedding whose dimensionality is not 3072 must be normalized manually (divided by the vector norm), and the resulting norm should be very close to 1. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |
| gemini-embedding-001 accepts text input only, with an input token limit of 2,048 tokens per input, so longer text must be truncated or chunked before embedding. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/models/gemini-embedding-001) |
| When latency is not a concern, use the Gemini Embeddings models with the Batch API, which gives much higher throughput at 50% of the default Embedding price. | `high` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |
| Migration: the embedding spaces of gemini-embedding-001 and gemini-embedding-2 are incompatible, so moving to gemini-embedding-2 requires re-embedding all existing data. gemini-embedding-2 does not support task_type (it uses prompt-prefix formatting), whereas gemini-embedding-001 uses the task_type parameter and needs manual normalization for non-3072 dimensions. | `medium` | `model-specific` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |
| Compare embedding vectors with cosine similarity, which focuses on direction rather than magnitude (range -1 to 1). | `high` | `model-agnostic-candidate` | not recorded | [source](https://aistudio.google.com/docs/embeddings) |

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
