# Incidents

This directory holds incident notes: short, public-safe records of failures that taught this project something durable. It is the output location for the [`incident-postmortem`](../../catalog/skills/infrastructure/incident-postmortem/SKILL.md) skill.

Nexus-Hub is a catalog and an installer, not a service with a pager rotation, so "incident" here is broader than an outage. It covers any failure that shipped: a hook that was registered and permanently silent, a cross-platform sibling that never parsed, a guard whose path filter excluded the file it guarded. Those are the failures worth a note, because each one has a reusable shape.

## Naming

One file per incident: `<slug>-YYYYMMDD.md`. The slug names the failure, not the fix (`powershell-sibling-parse-error`, not `add-ast-parse-gate`), and the date is the date the failure was identified or diagnosed, not the date it shipped.

`TEMPLATE.md` is the template and is not an incident. It carries no date suffix, which is how the convention keeps it distinguishable.

## An incident is closed by a change, not by an explanation

This is the load-bearing rule of the directory, and the only control that stops it becoming a graveyard of notes nobody reads.

**Every incident note must name AND link a durable fix**: a concrete change that makes the lesson survive the memory of the people who lived it. A commit, a test, a CI gate, a hook, a validator, a skill edit. Not "we should be more careful", not "the team is now aware", not a paragraph explaining what went wrong.

**A note with no linked fix is an open item, not an archive entry.** If you write one up and the fix does not exist yet, that is fine and honest, but it belongs in [`known-gaps.md`](../releases/v3/v3.16/known-gaps.md) for the active version as tracked work, with the incident note linking to it. Do not let the note stand alone as though writing it were the resolution.

The practical test: if this exact failure recurred next quarter with a different person at the keyboard, would anything stop it? If the answer is "someone would remember reading the note", there is no durable fix yet.

## Public-safe by construction

This repository is public. Incident notes are the single most likely artifact in it to leak internal context, because the raw material of an incident is logs, paths, and local state.

Every note carries a mandatory **Public-Safe Shape** section that abstracts the reusable pattern with no local absolute paths, no raw log output, no private links, and no credentials. Write the shape first and the specifics second; if a detail cannot be abstracted without losing the lesson, the lesson is probably narrower than it seems.

Two mechanical controls back the requirement rather than leaving it to good intentions:

- The `secret-scan` hook fires on every Write and Edit regardless of path, so it covers this directory with no additional configuration. It is a credential scanner, not a privacy scanner - it will catch a leaked token and will not catch an internal hostname.
- `scripts/check_incident_notes.py` (run by `make validate` and CI) asserts that every note has both required sections and that the Durable fix section carries at least one link.

Neither substitutes for reading the note before committing it. Apply the [`egress-redaction`](../../catalog/skills/security/egress-redaction/SKILL.md) discipline: treat the note as content leaving the machine, because it is.

## Required sections

In order, per `TEMPLATE.md`:

1. **Title** and **Date**
2. **Audience** - which maintainers and which owning skill the note is for
3. **Summary** - what failed, in a few sentences
4. **Public-Safe Shape** - the reusable pattern, abstracted (mandatory)
5. **Durable fix** - the concrete change, named and linked (mandatory)

Sections beyond these are welcome (timeline, five-whys, contributing factors) when the incident warrants them. The `incident-postmortem` skill's eight-section structure is the right shape for a large incident; these five are the floor for a small one.

## Index

| Incident | Date | Shape |
|---|---|---|
| [powershell-sibling-parse-error-20260709](powershell-sibling-parse-error-20260709.md) | 2026-07-09 | Unverified cross-platform sibling |
| [provenance-ledger-sibling-divergence-20260722](provenance-ledger-sibling-divergence-20260722.md) | 2026-07-22 | Unverified cross-platform sibling |

Both current notes share one shape, which is itself the finding: the same class of failure produced two separate defects across five minor versions. See [`shapes.md`](shapes.md).
