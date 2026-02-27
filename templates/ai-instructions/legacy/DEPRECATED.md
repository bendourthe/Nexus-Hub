# Legacy Templates (Deprecated)

These full-file language templates are **deprecated** as of v0.7.0.

## What Changed

The installer now uses a **base template + snippets** architecture:
- `base-claude.md` / `base-gemini.md` provide the concise WHAT/WHY/HOW structure
- `coding-snippets/*.md` contain only language-specific conventions
- The installer renders templates with auto-detected project metadata

## Why

Research shows that monolithic agent config files (175+ lines of generic instructions) actively
hurt agent performance while increasing inference cost by 20%+. The new templates are 54-66%
smaller, 2.7x more relevant to coding tasks, and platform-specific.

See: "Bad AGENTS.md Are Making Your Coding Agent Worse" (2025)

## Migration

1. Run the installer (`scripts/installer.ps1` or `scripts/installer.sh`)
2. It will generate a project-specific CLAUDE.md with detected metadata
3. Run `/setup-project` in Claude Code to customize further

## Files in This Directory

- `coding-instructions/python.md` (replaced by `../coding-snippets/python.md`)
- `coding-instructions/javascript.md` (replaced by `../coding-snippets/javascript.md`)
- `coding-instructions/typescript.md` (replaced by `../coding-snippets/typescript.md`)
- `coding-instructions/java.md` (replaced by `../coding-snippets/java.md`)
- `coding-instructions/csharp.md` (replaced by `../coding-snippets/csharp.md`)
- `coding-instructions/go.md` (replaced by `../coding-snippets/go.md`)
- `coding-instructions/cpp.md` (replaced by `../coding-snippets/cpp.md`)
