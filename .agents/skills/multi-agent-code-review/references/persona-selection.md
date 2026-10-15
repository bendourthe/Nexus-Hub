# Persona Selection

How Stage 3 of the pipeline chooses reviewers from a diff, and which agent backs each persona. The goal is high signal: always-on lenses guarantee a floor of coverage, conditional lenses fire only when the diff contains the surface they own, so irrelevant reviewers never run.

## Agent mapping

Each persona maps to an agent definition under `catalog/agents/`. Some reuse existing general agents; the rest are the dedicated single-lens reviewers added for this pipeline.

| Persona | Backing agent | Origin |
|---|---|---|
| correctness | `code-reviewer` | reused (its primary focus is correctness + SOLID) |
| maintainability | `maintainability-reviewer` | dedicated |
| testing | `testing-reviewer` | dedicated |
| project-standards | `project-standards-reviewer` | dedicated |
| security | `security-reviewer` | reused |
| performance | `performance-reviewer` | dedicated |
| api-contract | `api-contract-reviewer` | dedicated |
| reliability | `reliability-reviewer` | dedicated |
| adversarial | `adversarial-reviewer` | dedicated |
| agent-native | `agent-native-reviewer` | dedicated (see [[tool-design]]) |

When a persona reuses a general agent (`code-reviewer`, `security-reviewer`), dispatch it with an instruction to return findings in the [findings-schema](findings-schema.md) JSON shape and to set `persona` to the persona name in this table, so the merge stage can attribute and dedup uniformly.

Two further existing agents are referenced but are not fan-out personas:

- `architect` - escalation target when an `api-contract` or `correctness` finding raises a genuine design-redesign question (not a contract break). Surface it as a recommendation, do not dispatch it per-diff.
- `refactor-cleaner` - the applier for `autofix_class: safe` (and proposed `assisted`) fixes in autofix mode. It mutates code; it is never a read-only review persona.

## Always-on personas

These run on every review regardless of diff content. They are the coverage floor:

- **correctness** - logic errors, edge cases, error paths, race conditions.
- **maintainability** - naming, duplication, complexity, cohesion (advisory).
- **testing** - coverage of new branches, edge cases, test quality (advisory).
- **project-standards** - AGENTS.md / CLAUDE.md / constitution compliance.

## Conditional personas

Select a conditional persona when the diff matches its trigger. When in doubt, prefer selecting it (a quiet reviewer returns `[]`; the cost is one dispatch). Record the trigger that fired for each.

| Persona | Select when the diff... |
|---|---|
| **security** | touches input handling, authentication / authorization, sessions, crypto, secrets / env vars, file paths, deserialization, outbound requests, SQL / queries, or HTML output. |
| **performance** | adds a loop over user-sized or unbounded data, a query / RPC / file read (especially inside a loop), allocation-heavy work, caching, or changes a known hot path. |
| **api-contract** | changes a public function signature, a REST / GraphQL / gRPC route shape, a request / response field, an enum, an event / message payload, a config key, or a DB schema other code reads. |
| **reliability** | adds external I/O (network / DB / queue / filesystem / subprocess), a multi-step state change, retry / timeout logic, resource acquisition, or anything assumed to survive a restart. |
| **adversarial** | parses or validates input, crosses a trust boundary, performs arithmetic on external values, or exposes a new endpoint / action a hostile user could abuse. |
| **agent-native** | adds a new user-facing capability (command, action, UI affordance, API) - check it is reachable by an agent with the context needed to use it. See [[tool-design]]. |

## Heuristics for reading the diff

- Use `git diff --stat` and file extensions/paths to bucket the change (API layer, data layer, UI, infra, docs-only).
- A docs-only or comment-only diff selects only `project-standards` (and `maintainability` if structure changed); skip the code lenses.
- A migration file or `*.proto` / `*.graphql` / OpenAPI change always selects `api-contract`.
- A change adding `try` / `catch` / `defer` / `finally` / retry keywords, or new client construction, selects `reliability`.
- Selecting a persona that then returns `[]` is a correct, cheap outcome - it documents that the lens was applied and found nothing. Under-selecting (skipping a lens whose surface is present) is the failure to avoid.
