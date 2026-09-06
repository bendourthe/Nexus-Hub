# Out-of-Scope Register

Deliberately-declined features and request classes. This register is the documented answer to a repeat request so the same decision is not re-litigated.

It is not a backlog. Items here are **never-do**, not **do-later**.

## How this differs from known-gaps

| Surface | Question it answers | Typical IDs | What happens next |
|---|---|---|---|
| `docs/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` | What slipped, deferred, or stayed unfinished in a version we still intend to do? | NI, DF, BG, WN, MT, QG | `/generate-plan` ingests open items into the next plan |
| `docs/policy/out-of-scope/` (this register) | What have we decided we will never do, and why? | one file per topic | Point the requester at the file; do not append the item to known-gaps |

`[[known-gaps-tracker]]` owns the do-later log. When an agent or a human says "we will never do this", "this is a declined feature", or "do not add X to the catalog", write or update a file here instead of a known-gaps row.

A known-gaps `DF` (deferred) still implies the work might land. An out-of-scope file implies it will not, unless a later decision record explicitly re-opens it.

## Contract

One file per deliberately-declined feature or request class:

- **Path**: `docs/policy/out-of-scope/<topic-slug>.md` (kebab-case, matching this directory's other policy files).
- **Required sections**, in order:

    1. A one-line declaration of what is out of scope (the first paragraph after the H1, or a `**Out of scope**:` lead-in).
    2. `## Why this is out of scope` - the actual reasoning (maintenance surface, policy conflict, capability owned elsewhere). Cite the policy, comparison, or decision that recorded the decline.
    3. `## Prior requests` - links to issues, discussions, comparisons, or plans that asked for it. If none exist, say so and cite the decline record instead of inventing an issue.

- Follow [`catalog/style-guides/markdown.md`](../../../catalog/style-guides/markdown.md).
- Do not name a declined third-party product as a thing we might wrap later unless the "why" section already explains the reverse-engineer-or-drop path.

## Index

| File | One-line declaration |
|---|---|
| [search-as-service-mcps.md](search-as-service-mcps.md) | Search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service MCP registry entries are never shipped. |
| [changesets-release-automation.md](changesets-release-automation.md) | npm changesets (and a changesets-driven version-PR Action) are not the Nexus-Hub release path. |
| [oxlint-in-nexus-hub.md](oxlint-in-nexus-hub.md) | Oxlint is not a Nexus-Hub dependency, CI gate, or consumer-plugin vendor workflow. |

## Adding an entry

1. Confirm the item is never-do, not deferred. If it might ship later, it belongs in known-gaps as `DF` (or in a plan), not here.
2. Create `<topic-slug>.md` with the three required sections.
3. Add a row to the Index table above.
4. If `[[known-gaps-tracker]]` already has an open row for the same item, move that row to Resolved with `Resolved in: transferred to docs/policy/out-of-scope/<topic-slug>.md` so the two surfaces do not disagree.
