# Memory Record Template

Use this envelope for a file-backed lasting fact, and the same header fields (before a `---` line) for a `nexus-memory` `record` write. A record with no `source:` is invalid. When importing a pre-provenance file, set `source: legacy-import`.

```yaml
---
source: conversation:2026-08-23
tier: working
derived_from: []
supersedes:
---
```

The fact itself follows the header.

## Required fields

- `source:` origin of the fact (conversation, file path, decision id). Required. Use `legacy-import` only when migrating a record whose origin is truly unknown.
- `tier:` `session`, `working`, or `durable`. Session entries are the ones `maintain --preview` lists for archival.
- `derived_from:` ids or indexes this synthesis was built from. Empty if the fact is first-hand.
- `supersedes:` index or id of the record this one replaces. Leave empty for a new fact. Never delete the old row.

## Changelog

Append one line per mutation. Do not edit earlier lines.

```text
2026-08-23T19:00:00Z	added	0	source=conversation:2026-08-23
```

The store writes `changelog.log` on `record` and on `maintain --apply`. File-backed notes keep an equivalent list under this heading.

## Lifecycle

1. **session** -- useful this session, candidate for archival.
2. **working** -- still in play across nearby sessions.
3. **durable** -- keep.

Maintenance is preview-first. Run `python -m nexus_memory maintain` to list session-tier rows, then `python -m nexus_memory maintain --apply` to copy a backup and append `archived` changelog rows. Entries are never deleted; a superseded fact stays readable.

## Worked example

```text
source: conversation:2026-08-23
tier: durable
derived_from: 3,4
supersedes: 3
---
Prefer SHA-256 via hashlib/.NET over Get-FileHash for installer checksums.
```

Index 3 remains in the log. Readers skip it when a later row lists `supersedes: 3`.
