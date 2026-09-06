# Edit-Safety Verdict Contract

## Purpose

The edit-safety preflight tools convert existing local graph evidence into one ranked verdict and one recommended action before an agent edits, deletes, or renames a symbol. They are advisory, strictly read-only, local-only, and bounded to three operations: edit, delete, and rename.

The tools do not prove that a change is safe. Dynamic dispatch, reflection, generated code, configuration references, unindexed languages, and other repositories may be invisible. The honesty rule is mandatory: when the local index cannot resolve the symbol or lacks graph data, return `insufficient_data`; never replace missing evidence with a reassuring verdict.

## Ordered Taxonomy

Lower rank is more constraining.

| Rank | Tier | Meaning | Required agent behavior |
|---:|---|---|---|
| 0 | `runtime_dependency` | At least one cross-file, non-test caller, importer, or reference depends on the symbol. This is the strongest local evidence that production behavior reaches it. | Preserve behavior and contract unless all production dependents move in the same change; run affected paths and tests. |
| 1 | `insufficient_data` | The graph database is absent or empty, or the requested symbol cannot be resolved. Risk cannot be ranked honestly. | Refresh the graph index and retry before mutating the symbol. |
| 2 | `external_contract` | Known dependents are cross-file but test-only. The signature is exercised outside the defining file even though no production-path caller is indexed. | Preserve the current contract for an edit; migrate every dependent for delete or rename. |
| 3 | `internal_dependency` | Known callers or references are confined to the symbol's defining file. | Update the symbol and its same-file dependents together, then run focused tests. |
| 4 | `no_known_callers` | The symbol resolves, but the local graph contains no incoming caller, importer, or reference edge. This is a possible dead-code signal, not proof of safety. | Check dynamic, configuration, generated, and cross-repository uses before changing or removing it. |

`insufficient_data` ranks ahead of evidence-backed lower-risk tiers because an unknown graph must constrain action. `runtime_dependency` remains the highest-stakes tier because it contains affirmative evidence of a production-path dependency.

## Inputs and Evidence

Every response includes the same evidence object:

| Signal | Local derivation | Limitation |
|---|---|---|
| Resolved symbols | Existing qualified-name then plain-name graph resolution | Ambiguous plain names may produce multiple matches; all are included |
| Callers | Incoming `calls` edges | Dynamic calls may be absent |
| Importers | Incoming `imports` edges | Extractor support varies by language and import shape |
| References | Incoming `references`, `instantiates`, and `decorates` edges | String/configuration references are not inferred |
| Cross-file reach | Dependent file differs from the definition file | This is local cross-file evidence, not proof of another repository |
| Cross-repository reach | Not represented by a single repository index | Always reported as unavailable, never invented |
| Test coverage presence | At least one dependent path matches a conservative test-file convention | This is indexed structural coverage, not executed line coverage |
| Complexity | Symbol span in source lines plus incoming dependency count | Span is a structural proxy; no cyclomatic-complexity claim is made |
| Index health | Database presence plus file and node counts | A non-empty index may still omit unsupported or ignored files |

Test paths are recognized by a `tests` or `test` directory component, a filename beginning with `test_`, or a filename ending in `_test` before its extension.

## Operation Contracts

### Edit preflight

Answers: "What is the regression risk if I modify this symbol, and what must I preserve?"

The recommendation must state whether behavior/signature preservation, coordinated dependent edits, re-indexing, or dynamic-use review is required.

### Delete preflight

Answers: "Who breaks if this symbol disappears?"

The recommendation must prohibit deletion while known dependents remain, require index refresh for insufficient data, and treat no-known-callers as a review candidate rather than deletion approval.

### Rename preflight

Answers: "What references must move together?"

The recommendation must require all indexed callers/importers/references in the applicable scope to move atomically, require index refresh for insufficient data, and warn that unindexed string or cross-repository references may remain.

## Response Contract

Each tool returns:

```json
{
  "operation": "edit",
  "symbol": "package.module.target",
  "verdict": {
    "tier": "runtime_dependency",
    "rank": 0,
    "meaning": "..."
  },
  "recommended_action": "...",
  "evidence": {
    "matches": [],
    "callers": [],
    "importers": [],
    "references": [],
    "production_dependents": [],
    "external_dependents": [],
    "internal_dependents": [],
    "test_coverage": {"present": false, "files": []},
    "complexity": [],
    "cross_repo_visibility": "unavailable",
    "index": {"present": true, "files": 0, "nodes": 0}
  }
}
```

`recommended_action` is always one non-empty line. Evidence arrays contain concrete indexed nodes and edge kinds. No preflight tool writes the repository, index, sidecar file, cache, or network.

## Scope Cap

The supported fused analysis surface is exactly:

- Existing `code_impact` graph traversal.

- New `code_edit_safety` preflight.

- New `code_delete_safety` preflight.

- New `code_rename_safety` preflight.

No generic risk scorer, analytics dashboard, mutation executor, remote lookup, or additional safety tool is part of this contract.
