# Solution Knowledge-Base Schema

This reference defines the on-disk contract for a `docs/solutions/<category>/<slug>.md` entry: the two-track frontmatter field set, the controlled enums, the category mapping, and the YAML-safety quoting rule. Both `solution-knowledge-base` (capture) and `solution-refresh` (lifecycle audit) validate against this contract. The parser-safety checker `scripts/validate_solution_frontmatter.py` enforces the quoting rule mechanically.

## File location and naming

- Path: `docs/solutions/<category>/<slug>.md` (relative to the repo root, or cwd when not in a repo).
- `<category>` is one of the controlled categories below (a kebab-case directory).
- `<slug>` is kebab-case, descriptive, and unique within its category (e.g., `flaky-auth-token-clock-skew`, not `bug-1`).

## Two-track frontmatter

Every entry declares `track: bug` or `track: knowledge`. Both tracks share a common field set; each track adds its own required fields.

### Common fields (both tracks)

| Field | Required | Type | Notes |
|---|---|---|---|
| `title` | yes | string | One-line human title. Quote if it contains `:` or `#`. |
| `slug` | yes | string | Matches the filename stem. |
| `track` | yes | enum | `bug` or `knowledge`. |
| `category` | yes | enum | One of the controlled categories (see mapping below). |
| `component` | yes | enum | Generic component the entry concerns (see component taxonomy). |
| `tags` | yes | list[string] | Free-form lowercase tags for overlap scoring. At least one. |
| `created` | yes | date | `YYYY-MM-DD`. |
| `updated` | yes | date | `YYYY-MM-DD`. Equals `created` on first write. |
| `related` | no | list[string] | Slugs or relative paths of related entries. |

### Bug track adds

| Field | Required | Type | Notes |
|---|---|---|---|
| `symptoms` | yes | list[string] | Observable failure signals (error text, behavior). |
| `root_cause` | yes | string | The underlying cause, not the symptom. |
| `resolution_type` | yes | enum | See `resolution_type` enum below. |

### Knowledge track adds

| Field | Required | Type | Notes |
|---|---|---|---|
| `applies_when` | yes | string | The situation in which this knowledge is relevant (the retrieval trigger). |

## Controlled enums

### `category` (top-level directory)

`bug`, `performance`, `security`, `integration`, `build`, `infra`, `data`, `api`, `ui`, `tooling`, `process`, `knowledge`.

New categories may be added when none fit, but prefer an existing one. The `bug` category is the default for the bug track; `knowledge` is the default for the knowledge track when no narrower category applies.

### `component` (generic taxonomy, language- and framework-agnostic)

`backend`, `frontend`, `database`, `api`, `auth`, `build`, `ci`, `infra`, `testing`, `tooling`, `docs`, `performance`, `security`, `dependency`.

This taxonomy is deliberately generic. Do NOT use framework-specific component names (no `model` / `controller` / `view` / `migration`); map those onto the generic set (e.g., an ORM model issue is `database`, a request handler is `backend` or `api`).

### `resolution_type` (bug track)

| Value | Meaning |
|---|---|
| `code-fix` | A change to first-party source code. |
| `config-change` | A configuration / settings / env change, no source change. |
| `dependency-upgrade` | Resolved by bumping or pinning a dependency. |
| `revert` | Resolved by reverting a prior change. |
| `workaround` | A non-root-cause mitigation (note the residual risk). |
| `environment` | A host / toolchain / runtime environment fix. |
| `documentation` | Resolved by documenting expected behavior (no code change needed). |

## Category mapping (decision order)

1. If the entry records a defect that was fixed -> `track: bug`, pick the `category` that matches the surface (`security`, `performance`, `data`, `api`, `ui`, `build`, `infra`, `integration`, or the catch-all `bug`).
2. If the entry records a durable lesson, pattern, or "how this system works" insight -> `track: knowledge`, pick the matching `category` (`knowledge` is the catch-all).
3. `component` is always from the generic taxonomy regardless of track.

## YAML-safety quoting rule

Solution docs are parsed by lightweight stdlib parsers (the validator and downstream readers), so frontmatter MUST be parser-safe. The rules below are enforced by `scripts/validate_solution_frontmatter.py`:

1. **Delimiters**: the file starts with a line that is exactly `---` and the frontmatter ends with a line that is exactly `---`. No trailing characters on a delimiter line.
2. **No unquoted ` #` in scalar values**: a space-then-hash inside an unquoted scalar is parsed as a comment and silently truncates the value. Quote the whole value: `title: "Fix the #2 retry path"`, not `title: Fix the #2 retry path`.
3. **No unquoted `: ` inside scalar values**: a colon-space inside an unquoted scalar is read as a nested mapping. Quote it: `root_cause: "race: token refresh vs request"`, not `root_cause: race: token refresh vs request`.
4. **Quote list items that start with a YAML reserved indicator**: an array item beginning with any of `! & * ? | > % @ \` { } [ ] , # :` (or a leading `- `) must be quoted. Example: `tags: ["#hotpath"]`, not `tags: [#hotpath]`.
5. **Dates are unquoted `YYYY-MM-DD`**; booleans and numbers are unquoted; everything else that could contain a reserved character is quoted.

When in doubt, quote the scalar with double quotes. Double-quoting is always safe for the field types used here.

## Minimal valid examples

Bug track:

```markdown
---
title: "Auth token expiry test flakes under clock skew"
slug: flaky-auth-token-clock-skew
track: bug
category: bug
component: testing
tags: ["auth", "flaky-test", "time"]
created: 2026-05-30
updated: 2026-05-30
symptoms:
  - "test_auth_token_expiry intermittently returns 200 instead of 401"
root_cause: "the test asserted on wall-clock expiry without freezing time"
resolution_type: code-fix
related: []
---

# Auth token expiry test flakes under clock skew

(body: context, the fix, and how to recognize a recurrence)
```

Knowledge track:

```markdown
---
title: "How the installer copies top-level scripts (explicit-name, not by folder)"
slug: installer-copies-scripts-by-explicit-name
track: knowledge
category: knowledge
component: tooling
tags: ["installer", "cross-platform", "scripts"]
created: 2026-05-30
updated: 2026-05-30
applies_when: "adding a new scripts/<name>.py and wiring it into both installers"
related: []
---

# How the installer copies top-level scripts

(body: the rule, why it exists, and the copy-step pattern to follow)
```
