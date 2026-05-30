---
name: solution-refresh
description: Audit and maintain the docs/solutions/ knowledge base over time - for each entry decide Keep, Update, Consolidate, Replace, or Delete. Make sure to use this skill whenever the user says "review the solutions docs", "is the knowledge base still accurate", "clean up docs/solutions", "audit our saved solutions", "consolidate duplicate solution entries", "prune stale fixes", or whenever the solution store has drifted from the current codebase and needs a freshness pass. Also trigger when a solution entry is suspected to be outdated, superseded, or duplicated. SKIP, do NOT use for, capturing a brand-new solution (use solution-knowledge-base), per-version unfinished-work logging (use known-gaps-tracker), or general docs/ folder reorganization (use refactor-docs).
summary_l0: "Audit docs/solutions/ entries and decide Keep / Update / Consolidate / Replace / Delete"
overview_l1: "Maintains the docs/solutions/ knowledge base so it stays accurate as the codebase evolves. For each audited entry it decides one of five outcomes: Keep (still accurate), Update (drifted but salvageable), Consolidate (merge duplicates into one canonical entry), Replace (superseded by a newer solution), or Delete (the underlying code or problem no longer exists). It runs in interactive mode (propose each verdict, confirm before acting) or autofix mode (apply safe verdicts - Keep, frontmatter Update - automatically and surface the rest). Scope is selectable: a single file, a component, a category, or the whole store. It reuses solution-knowledge-base references/schema.md for frontmatter validation rather than duplicating the contract, and runs the parser-safety checker before and after edits. Everything is local and zero-outbound. Trigger phrases: review the solutions docs, audit our saved solutions, consolidate duplicate solution entries, prune stale fixes."
---

# Solution Refresh

Keep the `docs/solutions/` knowledge base honest. As the codebase changes, captured solutions drift: a fix gets superseded, a file referenced in an entry is deleted, two entries describe the same root cause. This skill is the lifecycle half of the compound knowledge loop - the capture half is [[solution-knowledge-base]]. It audits entries and assigns each one of five verdicts.

Everything is local and zero-outbound: it reads `docs/solutions/` and the current repo, then edits or removes Markdown files. It never uploads anything and never calls an external model.

## When to Use This Skill

Use when:

- The user asks to "review the solutions docs", "audit our saved solutions", "clean up docs/solutions", or "is the knowledge base still accurate".
- The knowledge base has grown and likely contains duplicates or stale entries.
- A specific entry is suspected to be outdated, superseded, or no longer applicable.
- A release or major refactor just landed and the captured solutions should be reconciled against the new code.

**When NOT to use:**

- Capturing a brand-new solution - use [[solution-knowledge-base]].
- Logging per-version unfinished work, deferrals, and open bugs - use [[known-gaps-tracker]].
- Reorganizing the broader `docs/` folder layout (archiving versions, moving reports) - use [[refactor-docs]].

## The Five Verdicts

| Verdict | When | Action |
|---|---|---|
| **Keep** | The entry is still accurate and useful. | No change (optionally bump nothing). |
| **Update** | The entry drifted (a path moved, a detail changed) but the core is salvageable. | Edit the body / frontmatter, bump `updated`. |
| **Consolidate** | Two or more entries cover the same root cause or insight. | Merge into one canonical entry, redirect the others via `related`, then Delete the duplicates. |
| **Replace** | A newer solution supersedes this one. | Write the successor (or point to it) and Delete or archive the superseded entry. |
| **Delete** | The underlying code, problem, or dependency no longer exists. | Remove the file and its `README.md` index row. |

`Keep` and a pure-frontmatter `Update` are the only verdicts safe to apply automatically in autofix mode. `Consolidate`, `Replace`, and `Delete` always require explicit confirmation, because they remove content.

## Instructions

### 1. Choose scope

Resolve the audit scope from the user request: a single file, a `component` (filter on the frontmatter field), a `category` (one directory), or the whole `docs/solutions/` tree. Default to the whole tree when unspecified, but report the count first and confirm before a large autofix run.

### 2. Validate parser-safety first

Run `python scripts/validate_solution_frontmatter.py <scoped paths>` before auditing. Fix any parser-safety failure (per the YAML-safety quoting rule in [solution-knowledge-base/references/schema.md](../solution-knowledge-base/references/schema.md)) before reasoning about content - an unparseable entry cannot be reliably audited.

### 3. Audit each entry

For each in-scope entry, gather evidence read-only:

- **Existence check**: do the files / symbols / dependencies the entry references still exist? (`git grep`, file lookups.)
- **Accuracy check**: does the described resolution still match how the code behaves now?
- **Duplication check**: does another entry share its category + component + root-cause family + tags? (Reuse the 5-dimension overlap heuristic from [[solution-knowledge-base]].)
- **Supersession check**: is there a newer entry (`created` date, `related` links) that covers the same ground better?

Validate the frontmatter against [solution-knowledge-base/references/schema.md](../solution-knowledge-base/references/schema.md) (required fields per track, controlled enums, generic component taxonomy).

### 4. Assign a verdict and act

Assign one of the five verdicts. In **interactive mode**, present the verdict with its evidence and confirm before acting. In **autofix mode**, apply `Keep` and pure-frontmatter `Update` automatically, and surface `Consolidate` / `Replace` / `Delete` for confirmation (never auto-delete).

On any content change, bump `updated`, keep the frontmatter parser-safe, and keep `docs/solutions/README.md` index rows in sync (remove rows for deleted entries, update titles for edited ones).

### 5. Re-validate

Run `python scripts/validate_solution_frontmatter.py <scoped paths>` again after edits to confirm every surviving entry is still parser-safe, and confirm the `README.md` index matches the files on disk (no orphan rows, no missing rows).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The entry is old, just delete it" | Age is not staleness. An entry from a year ago about a root cause that still exists is still valuable. Run the existence and accuracy checks; Delete only when the underlying problem is genuinely gone. |
| "Two similar entries are fine, more coverage is better" | Duplicates fragment retrieval - the next reader finds one and misses the other's detail. Consolidate into one canonical entry and redirect via `related`. |
| "Autofix should just clean everything up for me" | Autofix may apply only `Keep` and pure-frontmatter `Update`. `Consolidate` / `Replace` / `Delete` destroy content and always need confirmation. Silent deletion of a solved-problem record is exactly the failure this guard prevents. |
| "I'll rewrite the schema inline so this skill is self-contained" | Duplicating the field contract guarantees drift between capture and refresh. Always validate against the single source: [solution-knowledge-base/references/schema.md](../solution-knowledge-base/references/schema.md). |
| "I can skip the parser-safety run, the entries looked fine" | An entry with an unquoted ` #` or `: ` silently truncates or misparses, so your accuracy check reasons about the wrong content. Validate first (step 2) and last (step 5). |

## Verification

- [ ] `python scripts/validate_solution_frontmatter.py <scoped paths>` exits 0 both before (after any fixes) and after the audit.
- [ ] Every audited entry received exactly one verdict (Keep / Update / Consolidate / Replace / Delete).
- [ ] No `Consolidate`, `Replace`, or `Delete` was applied without explicit user confirmation.
- [ ] `docs/solutions/README.md` index rows match the files on disk (no orphan rows, no missing rows).
- [ ] Edited entries have `updated` bumped to today and still satisfy the schema (required fields, controlled enums, generic component).
- [ ] No network call, upload, or external store access occurred.

## Related Skills

- [[solution-knowledge-base]] - the capture half; this skill maintains what that skill writes. Shares its `references/schema.md` contract.
- [[known-gaps-tracker]] - per-version unfinished work; a resolved gap can graduate into a solution entry that this skill later audits.
- [[continuous-learning]] - prunes and re-confirms in-session instincts; this skill is the same lifecycle discipline applied to durable solution docs.
- [[refactor-docs]] - broader `docs/` reorganization; use it for archiving versions and moving reports, not for per-entry solution verdicts.
