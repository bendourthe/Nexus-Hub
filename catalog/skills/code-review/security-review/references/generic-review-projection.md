# Generic Review Projection

This contract covers the local projection from a normalized application-audit envelope to the generic review-finding shape used by `multi-agent-code-review` and `final-report`. Maintainers and agents read it before changing `scripts/project-review-findings.py` or any consumer of its output. Key topics: authority, expected review context, field mapping, unavailable fields, refusal behavior, legacy compatibility.

## Authority

The envelope stays the only ledger. The projection validates it with the shared `_normalized_audit.validate` and `_strict_json` decoder, then copies evaluator-owned values unchanged: health, coverage, reason codes, dispositions, severities, confidence, receipts and provenance. It does not re-grade, recompute health, open source or artifact paths, run reproduction commands, contact services, or modify targets. Evidence is carried as the envelope's own receipt identifiers, so a reader resolves proof in the envelope and never in a second ledger.

## Expected review context

The review caller supplies the expected context separately, with `--expected-context <file>`, from its own pinned revision, root and scope fingerprints and admitted run or input identity. The context is never derived from the submitted envelope.

| Key | Required | Compared with |
|---|---|---|
| `revision` | yes | `target.revision` |
| `root_fingerprint` | yes | `target.root_fingerprint` |
| `scope_fingerprint` | yes | `target.scope_fingerprint` |
| `input_run_fingerprint` | yes | `input_run_fingerprint` |
| `run_id` | no | `run_id` |
| `run_fingerprint` | no | `run_fingerprint` |
| `routing_manifest_digest` | no | `routing_manifest_digest` |

Every supplied key is compared before any finding or coverage is associated with the current review. One mismatch refuses the whole projection: exit 2, empty stdout, stderr `{"error":"review_projection_context_mismatch"}`. A self-consistent foreign envelope, including an empty complete one, fails the same way because its recomputed fingerprints prove only internal integrity.

Without `--expected-context` the projection is `unbound`. Findings are still projected so they stay visible, but `claims.current_target_confirmation` and `claims.complete_review` are both `false`. An unbound result never supports a current-target confirmation or a completeness claim. `complete_review` is `true` only when the binding is `bound` and the source `computed_health` is `complete`.

## Output shape

One JSON object, `nexus.generic-review-projection/v1`, with four members:

- `binding`: `state` (`bound` or `unbound`), the keys `checked`, and the `submitted` bindings.
- `claims`: the two booleans above.
- `source`: health, evaluation scope, evaluator, provenance, reason codes, graph quality, remediation, routing, disposition counts and target, copied from the envelope.
- `findings`: one entry per envelope finding, sorted by `id`.

## Field mapping

| Projected field | Source | Rule |
|---|---|---|
| `id` | `id` | Opaque envelope identity, unchanged |
| `fingerprint_key` | `id` | `security:` plus the id, so locationless findings dedup by identity and never by a fake file or line |
| `severity` | `severity` | `critical` P0, `high` P1, `medium` P2, `low` and `info` P3; a `release_blocking` finding is never below P1 |
| `source_severity`, `release_blocking` | same names | Unchanged |
| `source_confidence` | `confidence` | Numeric source value, unchanged |
| `confidence_band` | `confidence` | Deterministic floor to 25, 50, 75 or 100, never below 25. This is a display band, not the behavioral proof anchor |
| `review_state` | `disposition` | `confirmed` stays `confirmed`, `needs-live-validation` becomes `pending`, `corrected` and `rejected` keep their names |
| `source_disposition` | `disposition` | Unchanged, so no generic state replaces the source vocabulary |
| `requires_verification` | `disposition` | `true` only for `needs-live-validation` |
| `file`, `line`, `end_line` | `location` | `null` file and line with `locationless: true` when the source is locationless |
| `security.evidence_receipt_ids` | `evidence_receipt_ids` | Unchanged references into the envelope |
| `security.rule_id`, `vulnerability_kind`, `language`, `source_to_sink` | same names | Unchanged; `source_to_sink` only when present |

## Unavailable fields

The strict source schema has no proof class, reproducer, environment details, duplicate or root-cause links, or expected and observed results. Each finding lists them under `security.unavailable`; they are never inferred. A consumer that needs one marks it unavailable and requests a safe validation.

## Legacy compatibility

Ordinary findings without a `security` member follow the existing [findings schema](../../multi-agent-code-review/references/findings-schema.md) unchanged. The projection adds a security extension and a distinct `fingerprint_key`; it does not alter any legacy field.

## Failure behavior

- Invalid or absent stdin, malformed JSON, a bad fingerprint, an unknown or malformed context key, or a missing context file: exit 2, empty stdout, stderr `{"error":"review_projection_invalid"}`.
- Context mismatch: exit 2, empty stdout, stderr `{"error":"review_projection_context_mismatch"}`.
- Conflicting identities or bindings are never resolved by choosing a winner.
