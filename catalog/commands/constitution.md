---
description: Author or amend the project constitution - the versioned governance document declaring the MUST / SHOULD principles every plan, spec, ADR, and implementation aligns with. Permanent convenience alias for /spec constitution. Use to "write the project constitution", "ratify our principles", "amend the constitution", "run the constitution check against this plan". SKIP - agent-instruction files like CLAUDE.md / AGENTS.md (those are not the constitution).
---

# /constitution Command (permanent alias)

`/constitution` is a **permanent** convenience alias for `/spec constitution`. It is not a v3.x deprecation shim: it is retained for the entire v3.x line and beyond, because the constitution is heavily cross-referenced by `/plan` (the Constitution Check gate), `analyze-spec` (the constitution-alignment pass), and the `project-constitution` skill itself, and a single-word entry point for it is worth keeping.

## Forwarding

Forward every invocation to `/spec constitution`, passing all arguments through unchanged:

      /constitution                  -> /spec constitution            (author or amend, depending on whether a constitution file exists)
      /constitution amend            -> /spec constitution amend      (explicit amend mode)
      /constitution check <path>     -> /spec constitution check <path>  (read-only Constitution Check gate against a plan / spec)

The work runs in the `project-constitution` skill (placeholder collection, draft, propagation check, Sync Impact Report, validation, and write), exactly as `/spec constitution` drives it. See [`spec.md`](spec.md) for the full scope contract.

## Notes

- This is a permanent alias, not a deprecation shim - do not print a deprecation notice and do not schedule it for removal at v4.0.0.
- Keep this file thin: it only forwards to `/spec constitution`. All governance logic lives in the `project-constitution` skill.
