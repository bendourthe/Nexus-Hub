---
description: Show the Nexus-Hub command cheatsheet - the active commands, what each does, the deprecated name each one replaces, and common multi-command workflows. Permanent convenience alias for /skills list. Use to "list the commands", "show all commands", "what commands are there", "show the command cheatsheet", "which command replaced X", "how do I do X now". SKIP - searching the skill catalog by topic (use /skills search) or running a command you already know by name (just invoke it).
---

# /commands Command (permanent alias)

`/commands` is a **permanent** convenience alias for `/skills list`. It is not a v3.x deprecation shim: it is retained for the entire v3.x line and beyond, because "show me the commands" is an intent users reach for by the obvious name, and `/skills list` -- where the cheatsheet lives, alongside the other catalog operations (search / create / import / scan) -- is not discoverable for that intent.

## Forwarding

Forward every invocation to `/skills list`, passing all arguments through unchanged:

      /commands              -> /skills list           (full cheatsheet: active commands + what each replaces + common workflows)
      /commands <term>       -> /skills list <term>    (filter the cheatsheet to commands matching <term>)

The cheatsheet is generated at runtime from the command files themselves, per [`commands-cheatsheet.md`](../style-guides/commands-cheatsheet.md), so it always matches the commands actually installed -- including every rename and deprecation -- with no hand-maintained list.

## Notes

- This is a permanent alias, not a deprecation shim - do not print a deprecation notice and do not schedule it for removal at v4.0.0.
- Keep this file thin: it only forwards to `/skills list`. The cheatsheet procedure lives in the style-guide.
