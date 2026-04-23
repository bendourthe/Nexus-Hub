---
description: Deprecated alias for /generate-plan. Forwards to the renamed command, which produces plans at docs/<version>/plans/<slug>.md instead of the old hardcoded docs/v0.1.0/implementation-plan.md path.
---
# Generate Implementation Plan (Deprecated Alias)

This command has been renamed to **`/generate-plan`**. It now produces plans at `docs/<version>/plans/<slug>.md` with an auto-suggested slug derived from the user's intent, rather than the hardcoded `docs/v0.1.0/implementation-plan.md` path.

## Action

When this command is invoked:

1. Print a one-line deprecation notice:
   > `/generate-implementation-plan` has been renamed to `/generate-plan`. Forwarding now. The old name will be removed in a future release.
2. Execute the `/generate-plan` command exactly as if the user had typed it, passing through any arguments.

See [generate-plan.md](generate-plan.md) for the full specification.
