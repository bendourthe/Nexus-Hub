---
description: Generate a structured commit message for the staged changes. Permanent convenience alias for /update commit, kept for high-frequency mid-development use. Use to "commit this", "write a commit message", "generate the commit", "stage and commit", "commit my changes". SKIP - the full release flow with version bump and tag (use /update release).
---

# /commit Command (permanent alias)

`/commit` is a **permanent** convenience alias for `/update commit`, kept because committing is a high-frequency mid-development action that deserves a single-word entry point. It is not a v3.x deprecation shim.

## Forwarding

Forward every invocation to `/update commit`, passing all arguments through unchanged:

      /commit            -> /update commit            (generate a structured commit message for the staged changes)
      /commit <args>     -> /update commit <args>

The work runs in the `generate-commit-message` skill (analyze the staged diff, produce a sectioned-bullet message with no hard-wrapping), exactly as `/update commit` drives it. See [`update.md`](update.md) for the full scope contract.

## Notes

- This is a permanent alias, not a deprecation shim - do not print a deprecation notice and do not schedule it for removal at v4.0.0.
- An external `commit-commands` plugin may also provide a `/commit`; this alias forwards to Nexus-Hub's `/update commit`. If both are installed, the user's command resolution order decides which runs.
- Keep this file thin: it only forwards to `/update commit`. All commit-message logic lives in the `generate-commit-message` skill.
