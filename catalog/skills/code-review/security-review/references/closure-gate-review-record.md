# Closure-Gate Review Record

The deterministic closure gate reads one local JSON object. The record is a Nexus-Hub-native artifact: it captures the component coverage denominator, finding dispositions, supporting facts, and final report claims without depending on any external run-directory layout.

## Top-Level Shape

All six top-level fields are required.

| Field | Type | Purpose |
|-------|------|---------|
| `schema_version` | integer | Must be `1` so future schema changes fail closed |
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
- A `corrected` finding is terminal. Its corrected scope and rating remain report content, while this gate verifies only that the disposition is not dropped.

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

Run the bundled gate from the `security-review` skill directory:

```bash
python scripts/closure-gate.py review-record.json
```

Exit `0` means every diff is empty. Exit `1` means at least one claim-to-evidence diff is non-empty and the JSON output names every unresolved ID. Exit `2` means the record is malformed or unreadable and was not evaluated.
