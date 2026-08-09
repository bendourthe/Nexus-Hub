# Incident: <short title naming the failure, not the fix>

**Date**: YYYY-MM-DD (when the failure was identified or diagnosed)
**Audience**: <which maintainers this is for> / owning skill: <[[skill-name]]>

## Summary

What failed, in three to five sentences. State what was expected, what actually happened, and how long the gap persisted before anyone noticed. Name the surface (a hook, a validator, an installer path, a CI job), not a person.

## Public-Safe Shape

**Mandatory.** The reusable pattern, abstracted so it is useful to someone who was not there and safe to read by someone outside the project.

No local absolute paths, no raw log output, no private links, no credentials, no internal hostnames. Reference a repository-relative path (`catalog/hooks/foo.ps1`) rather than a machine path, and describe an error class rather than pasting its output.

Write this section as a claim someone could apply elsewhere. "A cross-platform sibling can be silently non-functional when the test suite only exercises one platform" is a shape. "The PowerShell file had a typo" is not.

If a shape recurs across incidents, write it once in [`shapes.md`](shapes.md) and reference it from each note rather than restating it.

## Durable fix

**Mandatory.** The concrete change that makes this lesson survive, named AND linked. A commit, a test file, a CI job, a hook, a validator, a skill edit.

| Fix | Link |
|---|---|
| <what the change is, in one line> | [`path/to/the/change`](../../path/to/the/change) |

State plainly what the fix would catch if the failure recurred, and what it would still miss. A fix with no stated blind spot has usually not been thought through.

If no durable fix exists yet, this note is **not** an archive entry. Record the work in the active version's `known-gaps.md`, link it here, and say so explicitly.
