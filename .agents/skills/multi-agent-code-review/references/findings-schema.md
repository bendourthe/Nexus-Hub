# Findings Schema

The structured contract every persona agent returns and the merge stage consumes. It is the operational form of the field table in [confidence-anchored-scoring](../../code-quality/references/confidence-anchored-scoring.md) section 6. Keeping every persona on one schema is what makes fingerprint dedup and cross-reviewer promotion possible.

## Shape

Each agent returns a JSON array of finding objects. An agent with nothing to report returns `[]`. No prose around the array.

```json
[
  {
    "title": "Off-by-one in pagination offset",
    "severity": "P1",
    "file": "src/api/list.ts",
    "line": 47,
    "confidence": 75,
    "persona": "correctness",
    "requires_verification": false,
    "pre_existing": false,
    "autofix_class": "assisted",
    "suggested_fix": "Use (page - 1) * size; the current page * size skips the first page of results."
  }
]
```

## Fields

| Field | Type | Rule |
|---|---|---|
| `title` | string | Short, specific. Feeds the dedup fingerprint, so name the *issue*, not the file. |
| `severity` | enum | `P0` / `P1` / `P2` / `P3`. Impact, not evidence. |
| `file` | string | Repo-relative POSIX path. Feeds the fingerprint. |
| `line` | integer | Best-known line in the changed file. Feeds the fingerprint (bucketed +/-3). |
| `confidence` | enum | Exactly one of `0 / 25 / 50 / 75 / 100`. Never interpolate. Anchor 0 means "do not emit". |
| `persona` | string | The persona name from [persona-selection.md](persona-selection.md) (e.g. `correctness`, `security`). Drives attribution, demotion, and promotion provenance. |
| `requires_verification` | boolean | `true` when confidence < 100 and the finding should get an independent validation pass before it blocks a merge. |
| `pre_existing` | boolean | `true` when the issue predates the diff (reported but not attributed to the change). |
| `autofix_class` | enum | `safe` (mechanical, auto-appliable) / `assisted` (human confirms) / `manual` (needs design judgement). |
| `suggested_fix` | string | The concrete remediation, specific enough to act on. |

## Validity rules

- `confidence` MUST be one of the five anchors. A finding with an interpolated value (e.g. 60) is malformed - reject it back to the agent.
- `severity` and evidence (`confidence`) are independent: a `P0` may sit at `confidence: 50` (plausible-but-unconfirmed critical) and a `P3` at `confidence: 100` (proven nit).
- An agent that emits a finding it would score at anchor 0 is malformed - anchor-0 findings are dropped at the source, not emitted.
- `file` must be repo-relative (no absolute or personal paths) so the fingerprint is stable across machines.

## Merged-finding extension (post-Stage-5)

After the merge stage, a surviving finding additionally carries provenance the agents do not set:

| Field | Set by | Meaning |
|---|---|---|
| `agreed_by` | promotion | List of personas that independently produced this fingerprint. |
| `promoted_from` | promotion | The pre-promotion confidence, when a step was applied. |
| `demoted` | demotion | `true` when mode-aware demotion lowered it one step. |
| `validation` | Stage 6 | `confirmed` / `refuted` and the validator's one-line rationale. |
| `suppressed_reason` | gate / validation | Why a finding was moved to the appendix tier (below gate, or refuted). |

Suppressed findings keep all their fields and move to the verbose/appendix tier; they are never deleted.
