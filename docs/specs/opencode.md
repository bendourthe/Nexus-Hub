# OpenCode Capability Spec

**Integration key**: `opencode`
**Distribution tier**: Behavioral guardrails (`AGENTS.md`) plus a skills mirror
**Instruction merge mode**: `shared` (marker-merged)
**Hooks**: not supported

OpenCode receives a marker-merged `AGENTS.md` instruction file plus a mirror of the skills, commands, and rules subtrees. It has no agent or hook surface.

## Install surface

| Aspect | Global scope | Workspace scope |
|--------|--------------|-----------------|
| Catalog root | `~/.opencode/` | `<project>/.opencode/` |
| Instruction file | `~/.opencode/AGENTS.md` | `<project>/.opencode/AGENTS.md` |

## Distributed content

| Catalog subtree | Destination subdir | Notes |
|-----------------|--------------------|-------|
| `catalog/skills/` | `skills/` | Full mirror. |
| `catalog/commands/` | `commands/` | Command bodies (no native slash surface; see notes). |
| `catalog/rules/` | `rules/` | Code-style and security rules. |

There is no `agents_subdir` and `hooks_supported = False`.

## Instruction file

- Template: `templates/ai-instructions/base-opencode.md`
- Mode: `shared` (marker-merged).
- Global file is `~/.opencode/AGENTS.md`; workspace file is `<project>/.opencode/AGENTS.md`.

## Quirks and notes

- Slash surface: no. OpenCode does not expose a slash-command menu for the mirrored commands; users invoke a command by pasting its body (the command files are still copied for reference).
- Hooks: not supported.
- OpenCode and Cursor are the two behavioral-guardrails platforms in the `AGENTS.md` coverage table; OpenCode additionally mirrors `skills/` (Cursor does not).

## Source of truth

Mirrors `scripts/lib/integrations/opencode.py` (`OpenCodeIntegration`) and the `AGENTS.md` platform-coverage section.
