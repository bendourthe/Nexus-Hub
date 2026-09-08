# Closure-Gate Review Record

The deterministic closure gate reads one local JSON object. The record is a Nexus-Hub-native artifact: it captures the component coverage denominator, finding dispositions, supporting facts, and final report claims without depending on any external run-directory layout.

## Top-Level Shape

Schema v1 requires the six fields below. Schema v2 keeps those fields and adds the scanner, remediation, and verifier collections described later. Unknown schema versions are usage errors.

| Field | Type | Purpose |
|-------|------|---------|
| `schema_version` | integer | `1` for the original closure record, or `2` for a full security-audit record with scanner receipts |
| `components` | array | The complete Phase 3 component denominator |
| `review_actions` | array | Logged actions and results that establish component coverage |
| `findings` | array | Every candidate and its terminal or explicitly pending disposition |
| `facts` | array | Evidence-bearing facts that support findings and report claims |
| `report_claims` | array | Assertions made by the final report and their fact references |

Every object in an array has a unique, non-empty `id`. Duplicate or missing IDs are data errors, not closure failures, because the gate cannot compute a trustworthy set difference from an ambiguous denominator.

## Components and Review Actions

A component uses one of the Phase 3 states: `COVERED`, `OMITTED`, or `UNCOVERED`.

- A `COVERED` component must name at least one `review_action_ids` entry. The referenced action must point back to the same component and carry non-empty `action`, `result`, and `evidence` fields.
- An `OMITTED` or `UNCOVERED` component must carry a non-empty `caveat`. This implements the closure rule that residue may ship only when it is stated explicitly; it cannot be silently implied as covered.
- An unknown status, a missing action, or an unresolved action reference appears in `components_without_review_action_or_caveat`.

## Finding Dispositions

Use exactly one of the established dispositions: `confirmed`, `needs-live-validation`, `corrected`, or `rejected`.

- A `confirmed` finding names one or more `evidence_fact_ids`. Every referenced fact must exist and carry non-empty evidence.
- A `needs-live-validation` finding carries `pending_validation` with non-empty `safe_test`, `expected_vulnerable`, `expected_safe`, and `potential_severity` fields. A bare disposition string is not explicitly pending.
- A `rejected` finding carries a complete `rejection_record` with a `counter_hypothesis`, an `actual_input_sources` denominator, and one route result for every source. Each route uses `observed-blocked`, `observed-safe`, or `not-applicable` and cites evidence. When `reachability_claim` is true, `reachability_evidence` is also required.
- A `corrected` finding is terminal. Its corrected scope and rating remain report content, while this gate verifies only that the disposition is not dropped. Under schema v2, a corrected finding with `source_scanner_id` also requires equivalent before and after scanner receipts.

## Facts and Report Claims

A fact has an `id` and non-empty `evidence`. A report claim has an `id` and a non-empty `fact_ids` list. A missing fact, an empty evidence field, or a claim with no fact reference appears in `report_claims_without_matching_facts`.

The same fact may support both a confirmed finding and a report claim. That is intentional: the gate checks referential closure, not one-to-one ownership.

## Clean Example

```json
{
  "schema_version": 1,
  "components": [
    {
      "id": "api",
      "status": "COVERED",
      "review_action_ids": ["RA-1"]
    },
    {
      "id": "generated-client",
      "status": "OMITTED",
      "review_action_ids": [],
      "caveat": "Generated from the reviewed schema and outside the declared scope."
    }
  ],
  "review_actions": [
    {
      "id": "RA-1",
      "component_id": "api",
      "action": "Traced request inputs to authorization checks.",
      "result": "One surviving authorization finding.",
      "evidence": "trace:api-auth-2026-07-31"
    }
  ],
  "findings": [
    {
      "id": "F-1",
      "disposition": "confirmed",
      "evidence_fact_ids": ["FACT-1"]
    },
    {
      "id": "F-2",
      "disposition": "rejected",
      "rejection_record": {
        "counter_hypothesis": "Every actual input route applies the same ownership check.",
        "actual_input_sources": ["path", "request body"],
        "routes": [
          {
            "source": "path",
            "result": "observed-safe",
            "evidence": "test:test_path_owner_guard"
          },
          {
            "source": "request body",
            "result": "observed-blocked",
            "evidence": "trace:body-id-ignored"
          }
        ],
        "reachability_claim": false
      }
    }
  ],
  "facts": [
    {
      "id": "FACT-1",
      "evidence": "artifact:reproduction/F-1.txt"
    }
  ],
  "report_claims": [
    {
      "id": "CLAIM-1",
      "fact_ids": ["FACT-1"]
    }
  ]
}
```

## Schema v2 Scanner Receipts

Schema v2 is opt-in for full security-audit runs. Schema v1 records keep their previous required fields, diffs, and exit behavior. Extra v2 keys on a v1 record are ignored.

A v2 record also requires `scanner_inventory`, `scanner_receipts`, `deterministic_coverage`, `remediation_receipts`, and `verifiers`.

`scanner_inventory` is the scanner denominator. Each entry has a unique `id`, boolean `applicable`, and non-empty `evidence`. Every inventory id must have at least one receipt whose `scanner_id` matches.

Receipt `state` is exactly one of `RAN`, `NOT_APPLICABLE`, `UNAVAILABLE`, `FAILED`, or `DECLINED`.

A `RAN` receipt requires `scanner_version`, `applicability_evidence`, `target_scope` with a non-empty `fingerprint`, `config_fingerprint`, `command`, integer `exit_code`, `started_at`, `finished_at`, and `artifact_path`. `NOT_APPLICABLE` requires `applicability_evidence` and `omission_reason`. `UNAVAILABLE` and `DECLINED` require those two fields. `FAILED` also requires `command` and integer `exit_code`.

`deterministic_coverage.status` is `complete` or `degraded`. `complete` is allowed only when every applicable scanner `RAN`. An inventory scanner with no receipt is a silent omission and always fails.

`remediation_receipts` may be empty when no patch was produced. Each remediation names `finding_ids`, `fixer_identity`, `before_receipt_id`, `after_receipt_id`, and `finding_delta` with `resolved_finding_ids`, `unresolved_finding_ids`, and `new_finding_ids`. Before and after receipts must share detector, config fingerprint, and target-scope fingerprint.

When remediations exist, `verifiers` must include at least one `read_only` identity that is not a fixer. The fixer may appear as an additional verifier. The independent verifier must not be the patch producer.

Schema v2 adds these diffs: `applicable_scanners_without_successful_run`, `malformed_or_unsupported_receipt_states`, `corrected_scanner_findings_without_equivalent_rescan`, `mismatched_detector_config_or_scope`, `unresolved_new_after_scan_findings`, and `fixer_is_sole_verifier`.

## Schema v2 Application-Audit Profile

The `application_audit` profile is an OPT-IN, additive block on a schema-v2 record. It is not schema v3, and it changes nothing about a record that omits it: a schema-v1 record, and a schema-v2 record with no `application_audit` key, keep their previous required fields, diff names, output bytes, and exit behavior. The gate adds the profile diffs below only when the key is present, so an existing record cannot start failing, and cannot start emitting new empty diff keys, because this profile shipped.

The profile exists because a pipeline that routes several owners across several stages can produce a result that reads clean while most of it never ran. Every rule here follows from one principle: absence of a finding is never evidence of safety. A missing applicable owner, an unavailable graph, a timed-out stage, an ambiguous symbol, a partial artifact, or insufficient provenance all DEGRADE coverage, and none of them may be reported as a clean surface.

### The record is untrusted input

The gate treats the whole record as data supplied by something it does not control.

- A command string inside a receipt is recorded for accounting and is never executed.
- A path inside the record is metadata, never a read instruction. The gate reads only paths passed explicitly on its own command line.
- A producer-supplied verdict has no authority (see `computed_health` below).
- A conflict between an observed value and a producer claim resolves to the observation, and the conflict itself is a failure rather than a silent correction.

### Required identity

`application_audit` requires an identity block sufficient to bind every later artifact to one run over one tree.

Two different failures live here and they exit differently, so the distinction is worth stating plainly. An identity that is MALFORMED or ABSENT (no `run_id`, an unrecognized `profile_version`, a `target_identity` with no valid `kind`) is a data error: the gate reports a usage error and evaluates nothing, because a set difference computed against an ambiguous denominator cannot be trusted and a diff list implies the denominator was understood. An identity that is well-formed but INCOMPLETE (most often a content manifest that does not cover every required class) is a closure failure: the denominator is understood, and what it says is that coverage was partial. Only the second appears in `application_audit_identity_incomplete`.

| Field | Type | Purpose |
|-------|------|---------|
| `profile_version` | integer | `1`; an unrecognized value is a usage error |
| `run_id` | string | Unique, non-empty; every receipt and artifact binds to it |
| `target_revision` | string | The revision under audit, as reported |
| `target_identity` | object | Exactly one of the two forms below |
| `target_root_fingerprint` | SHA-256 hex string | Identity of the authorized analysis root |
| `scope_fingerprint` | SHA-256 hex string | Identity of the declared in-scope set |
| `routing_manifest_digest` | SHA-256 hex string | Which routing contract selected the owners |
| `run_fingerprint` | SHA-256 hex string | Recomputed by `profile_fingerprint`, binding the required identity fields, profile version, and target identity, excluding this fingerprint itself |

`target_identity.kind` is either `immutable_checkout`, which asserts the tree cannot change during the run and carries its checkout identity, or `content_manifest`, which carries a complete target-content-manifest digest. A content manifest is complete only when it covers tracked, dirty, untracked, submodule (gitlink plus dirty and untracked state), and link or reparse state. A manifest that silently omits any of those classes is incomplete, and an incomplete manifest cannot support a `complete` health result, because the unmeasured class is exactly where an undeclared change hides.

### Six separate vocabularies, deliberately not one

Conflating these is the most common way a pipeline overstates its result, so each is a distinct field with its own closed set.

1. **Receipt terminal state** is exactly one of `RAN`, `NOT_APPLICABLE`, `UNAVAILABLE`, `FAILED`, `DECLINED`. These are the same five values schema v2 already uses, unchanged.
2. **Reason code** is a separate stable string explaining a non-`RAN` state or a degrade. A terminal state says what happened; a reason code says why. Reason codes are compared and aggregated, so they are stable identifiers rather than prose.
3. **Graph quality** is one of `complete`, `partial`, `ambiguous`, `unknown`. It describes reachability evidence, never execution.
4. **Validation outcome** is a separate field recording whether the record passed structural validation. A record can be structurally valid and describe a failed run.
5. **Provenance assurance** is one of `content_observed` or `self_attested`. There is deliberately no `process_observed` value, and the profile must not introduce one.
6. **Health** is one of `complete`, `degraded`, `failed`.

### Health is evaluator-owned

`computed_health` is written EXCLUSIVELY by the evaluator. A producer may emit `claimed_health`, and it carries no downstream authority whatsoever: it is recorded so a disagreement is visible, and a `claimed_health` that contradicts `computed_health` is itself a failure. Nothing reads `claimed_health` to decide anything.

The aggregation rules, in order:

- A terminal `FAILED` state on any stage, or invalid or mutually contradictory evidence anywhere, yields `failed`.
- A valid required host execution stage whose provenance is only `self_attested` CAPS aggregate health at `degraded`. It can never reach `complete`, no matter how clean the reported result, because nothing in the record proves that stage ran.
- Any other valid degrade condition (a non-`RAN` applicable owner, graph quality below `complete`, insufficient observation, an out-of-scope proven change) yields `degraded`. A structurally incomplete identity or malformed artifact is invalid evidence and yields `failed`.
- `complete` requires every applicable stage `RAN`, every artifact `content_observed`, graph quality `complete`, and a complete target manifest.

### Provenance: what re-hashing does and does not buy

Artifact digests recomputed by the evaluator from an explicitly caller-supplied path, over physically contained bytes, are `content_observed`. Everything a host reports about its own execution is `self_attested`.

Content observation NEVER upgrades execution provenance. Re-hashing an artifact proves what the bytes are; it proves nothing about which process produced them, with which arguments, on which model, under which settings, or whether other launches happened and were not reported. That asymmetry is the profile's central honesty constraint, and it is the reason `complete` is unreachable for a self-attested execution stage.

The record-only closure invocation has no independent host observation channel. It treats every execution statement as self-attested, including one labeled `content_observed` by its producer. The structurally complete profile fixture therefore exits zero with `computed_health: degraded`; structural closure and complete execution assurance are separate results.

### Execution-boundary receipt (self-attested)

Each stage that could leave the machine carries a boundary receipt recording declared outbound destinations, transmitted data classes, credential source and privilege level, explicit authorization, and reported boundary status. It records no secret values: a credential is described by source and privilege, never by value.

Absent explicit authorization, the run is offline-only. Every network, cloud, or model stage must be `DECLINED`, and health is at best `degraded`. A record claiming such a stage `RAN` without authorization is contradictory evidence and yields `failed`.

This receipt is accounting, not enforcement. It does NOT prove process identity, the arguments actually used, that any boundary was enforced, the identity of the model or its settings, the absence of hidden retries, or that no answer key was accessed. It is recorded so those limits are visible in the artifact rather than assumed away by a reader.

### Mutable-target decision table

When `target_identity.kind` is `content_manifest`, the target can change under the run, so content is revalidated before and after every stage. One table decides the outcome, and it has no discretionary branch.

| Observed between the before and after manifests | Result |
|---|---|
| No content change | Ordinary health rules apply |
| A change to declared scope, to a stage input, or to a bound artifact | `failed`, and NO envelope is produced |
| Any change whose relevance cannot be proven | `failed`, and NO envelope is produced |
| A change proven by the before and after manifests plus scope fingerprints to be outside all declared scope, all stage inputs, and all bound artifacts | At best `degraded`, recording BOTH digests and a stable reason code |

The default for an unproven change is failure, not tolerance. "Probably unrelated" is not a row in this table: proving irrelevance requires the manifests and fingerprints to show it, and where they cannot, the run failed.

The Python evaluator accepts separately supplied `observed_manifests=(before, after)` for this comparison. A caller must supply full manifests from the authorized root; the evaluator recomputes their digests and compares their root, scope, exclusions, budgets, Git classification, and changed entries against `scope_paths` and `bound_input_paths`. The record's `changed` boolean must match the digest comparison. A producer's `change_proven_out_of_scope` flag has no authority. Unknown metadata changes fail conservatively, and a proven outside-scope change requires `OUT_OF_SCOPE_CHANGE_PROVEN` while retaining degraded health.

### Surface, graph, and artifact receipts

- **Surface-routing receipts** record, per supported surface, either positive matched evidence or an explicit negative check. A surface simply absent from the receipts is a silent omission and always fails, because "we did not look" and "we looked and found nothing" are different results and must stay distinguishable in the record.
- **Graph-query receipts** record qualified symbol identity, the query and its provenance, any ambiguity, observed tool availability, and a graph quality value. Missing, conflicting, or `unknown` graph evidence never proves a path unreachable.
- **Observed artifacts** bind a digest to a run id and a stage identity. An artifact with no bound digest, or one bound to a different run, is rejected rather than accepted as cross-run substitution.

Duplicate or contradictory receipts for the same stage and identity FAIL. There is no last-writer-wins rule, because whichever writer won would be an arbitrary choice between two claims the record itself says are both true.

Every receipt collection binds `run_fingerprint`; stages additionally bind `run_id`, and artifacts bind both `run_id` and an existing `stage_id`. Empty stage, surface, graph, or artifact denominators fail. Stage `required` and execution-boundary `authorized` values are JSON booleans. Missing or unsupported provenance, malformed digests, duplicate identities, and unavailable graph receipts claiming complete quality fail validation.

### Remediation approval receipt

An approval receipt is the only thing that may authorize mutation, and its origin is what makes it an approval at all. It must originate from a trusted host-controlled interaction OUTSIDE every target, record, and artifact input. An approval receipt that arrived as part of the input, or that is merely self-attested, can never authorize mutation. This is where the untrusted-input stance has teeth: a record that supplies its own permission slip is describing an attack, not a workflow.

A valid receipt binds `run_id`, target revision and content digest, target-root and scope fingerprints, the finding IDs it covers, the permitted paths and actions, the proposed patch digest, approver and session identity, issue time, expiry and nonce, patcher identity, and revocation state.

Every one of these is checked IMMEDIATELY before mutation, not at record load, because the gap between the two is where a stale approval becomes a live one. Stale, replayed, cross-run, cross-root, revoked, patch-mismatched, and scope-expanded approvals are all rejected at that point.

Trusted origin is necessary but NOT sufficient. Without exact proposed-patch and scope binding, a genuine approval for one change still authorizes nothing else, so a correctly-originated receipt whose patch digest does not match the patch about to be applied is rejected exactly like a forged one.

The read-only closure evaluator has no trusted approval channel and never authorizes mutation. It rejects every input-supplied `approval_receipt`, even one whose own `origin` field says `trusted_host`. The existing patch owner must obtain and recheck actual host-controlled approval immediately before a separately authorized mutation.

### Profile diffs

These diff names are present only when `application_audit` is present.

- `application_audit_identity_incomplete`
- `stages_without_terminal_receipt`
- `surfaces_without_positive_or_negative_evidence`
- `graph_receipts_without_qualified_identity`
- `artifacts_without_bound_digest`
- `contradictory_or_duplicate_receipts`
- `mutable_target_change_unproven`
- `approval_receipts_without_trusted_origin`
- `provenance_insufficient_for_claimed_health`

### Out of scope for this profile

The profile deliberately does NOT introduce a `process_observed` provenance value, schema v3, a persistence or database model, a retry policy, a production or user-repository staging pipeline, provider-specific fields, or any agent-boundary control owned elsewhere. Acceptance constraints for this profile come from this repository's own comparison report and plan, not from any upstream project's wording.

## Running the Gate

The schema-v1 example above remains valid. A schema-v2 detection-only record adds inventory, receipts, degraded-or-complete coverage, empty remediations, and empty verifiers without changing the original collections.

Run the bundled gate from the `security-review` skill directory:

```bash
python scripts/closure-gate.py review-record.json
```

Exit `0` means every diff is empty. Exit `1` means at least one claim-to-evidence diff is non-empty. Ordinary records retain their unresolved IDs; application-audit records emit SHA-256 references for every diagnostic ID, so record-supplied identifiers cannot disclose credentials or personal data. Exit `2` means the record is malformed or unreadable and was not evaluated.

The target manifest rejects recognizable embedded credential values, token formats, and personal email addresses in path metadata before emission. It rechecks every observed leaf at the end of traversal, limits Git content checks to the declared scope, and records its sanitized Git environment policy. On Windows, the required system directory comes from the operating system rather than inherited environment text. These are content and lifecycle checks; they establish no process attestation.

### Application-audit graph receipts

The metadata-only graph shape is validated by [`_graph_receipt.py`](../scripts/_graph_receipt.py); the [seeding procedure](code-search-seeding.md) owns its public API and fallback rules. Each requested operation binds the run, target revision/root, content-bound run fingerprint, scope and routing identities, parameters, result and optional observed index digests. Keep qualified symbol IDs, canonical relative regions, duration, terminal reason, ambiguity/truncation, and fallback only. A RAN receipt proves a returned output, not graph freshness; current public responses project to unknown quality unless partial or ambiguous. FAILED or conflicting results fail closure; unavailable, partial, ambiguous, unknown, and direct-corpus fallback remain visibly degraded. No source-derived scalar or nested arbitrary property is permitted in a graph receipt.
