# /org Command

Connect, synchronize, inspect, or author an organization knowledge bundle. This command is a thin dispatcher: lifecycle operations delegate to the `nexus-hub org` CLI, while guided bundle creation delegates to the `org-standards-authoring` skill.

## Scope Resolution

Resolve `SCOPE` from the first positional argument in `$ARGUMENTS`. Recognized scopes are `connect`, `sync`, `status`, and `author`.

- If `$ARGUMENTS` begins with a recognized scope, set `SCOPE`, remove that token, and pass the remaining arguments through unchanged.
- If no recognized scope is present, show this menu and wait for a selection:

  ```text
  What scope?
    1. status   (recommended) - inspect the current connection and platform postures
    2. connect  - validate and connect a directory or git URL
    3. sync     - refresh the currently connected organization source
    4. author   - build a valid organization standards bundle through a guided workflow

  Reply with a number or a scope name.
  ```

- Accept menu numbers and scope names case-insensitively. Pressing Enter selects `status`.
- Never run an operation before the user selects a scope when the menu is shown.

## Delegation

Dispatch the resolved scope as follows:

```text
status  -> nexus-hub org status
connect -> nexus-hub org connect <remaining arguments>
sync    -> nexus-hub org sync
author  -> org-standards-authoring
```

For `connect`, require a bundle directory or git URL. Explain that the source must contain a valid `org.json` plus its referenced core document; if the source argument is absent, request it before invoking the CLI. `nexus-hub org connect` owns validation and persistence.

For `sync` and `status`, delegate directly to the CLI and report its exit status without reproducing lifecycle logic in this command.

For `author`, invoke `[[org-standards-authoring]]` and run its guided inventory, tiering, manifest, validation, and distribution workflow. Pass any remaining arguments as authoring context.

## Platform Surfaces

The installer automatically distributes this command to Claude `commands/`, Gemini `workflows/`, Codex `prompts/`, Cursor global and project command surfaces, Copilot `prompts/`, and Antigravity project `workflows/`. No installer edit or manual command-list update is required.
