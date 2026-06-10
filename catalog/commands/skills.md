---
description: Browse, search, create, import, and security-scan the Nexus-Hub skill and command catalog. Use to "find a skill for X", "search the catalog", "list all commands", "show the cheatsheet", "create a new skill / command", "import skills into my project", "scan a skill before installing it", "is this skill safe to install". SKIP - running a skill you already know the name of (just invoke it) or reviewing your own project's code (use /review).
---

# /skills Command

Work with the Nexus-Hub catalog: discover skills, list the full skills-and-commands cheatsheet, scaffold a new skill or command, import skills into a project, and security-scan a skill before you install it. `/skills` is the single entry point for everything you do *to and with the catalog itself*, including the v3.0.0 pre-install security scan.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `search`, `list`, `create`, `import`, `scan`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a search term, route it to `search` and pass it through.
- If `$ARGUMENTS` is a skill path or directory, route it to `scan`.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. search  (recommended) - find relevant skills by keyword, category, or role
        2. list    - unified cheatsheet of all skills and commands
        3. create  - scaffold a new skill or command interactively
        4. import  - import skills from the catalog into a project
        5. scan    - security-scan a skill (or the whole catalog) before install

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the retained skill:

      search  -> search-skills (keyword / category / role search over the catalog)
      list    -> read and follow style-guides/commands-cheatsheet.md (render the command cheatsheet live from the command files)
      create  -> create-skill-or-command (interactive scaffolding wizard)
      import  -> import-skills (copy catalog skills into the active project)
      scan    -> skill-security-scan (semantic adjudication; backed by nexus-skill-scanner once Phase 6 lands)

Pass any remaining arguments (search term, skill name, target path) through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## list scope (command cheatsheet)

`list` renders the unified command cheatsheet -- the active commands with what they do, the deprecated name each one replaces, and common multi-command workflows. It is generated **at runtime from the command files** (the installed per-platform `commands/` / `prompts/` / `workflows/` directory, or `catalog/commands/` in the repo), not from a hand-maintained table, so it always matches the commands actually present. Read and follow [`commands-cheatsheet.md`](../style-guides/commands-cheatsheet.md) (installed at `~/.nexus-hub/style-guides/commands-cheatsheet.md`) for the generation procedure and output format. An optional argument (`/skills list <term>`) filters to matching commands.

## scan scope (pre-install security check)

`scan` is the v3.0.0 addition. It runs the `skill-security-scan` skill over a skill you are about to import - reading the deterministic findings emitted by `nexus-skill-scanner` (Phase 6), filtering false positives (especially fenced-code examples in documentation), explaining any malicious intent, and assigning a final verdict before you install. This is the same lens `/review skill-scan` uses for the catalog dogfood. Until the Phase 6 engine lands, the scope adjudicates manually-collected findings. Always offer `scan` before `import` for skills sourced from outside the trusted catalog.

## Notes

- This command replaces `/search-skills`, `/commands-cheatsheet`, `/create-skill-or-command`, and `/import-skills` (removed in v3.2.0).
- Keep this dispatcher thin. The catalog procedures live in the retained skills; this file owns only scope resolution and delegation.
