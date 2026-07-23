# Search API spec

## Goals

Deliver fast full-text search across posts and comments.

## Requirements

- Acceptance criteria: p95 latency under 100ms.
- Results ranked by relevance.

## Open Questions

- Which ranking model do we adopt?
- Do we need typo tolerance in v1?
