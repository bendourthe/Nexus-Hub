---
description: List all available commands in a categorized cheatsheet table with descriptions and usage examples.
---
# Commands Cheatsheet

Generate a live cheatsheet of every available slash command, organized by category, with a short description and usage guidance.

## Instructions

### Step 1: Discover Commands

Look for command files in these locations (check both; use whichever exist):
- Global commands: `~/.claude/commands/` (on macOS/Linux) or `%USERPROFILE%\.claude\commands\` (on Windows)
- Project commands: `.claude/commands/` relative to the current working directory

List all `.md` files found. These are the available commands. If both locations exist, merge the lists and deduplicate by filename (project commands take precedence over global ones with the same name).

### Step 2: Read Each Command

For each `.md` file discovered:
- Extract the `description` field from the YAML frontmatter (the value on the line starting with `description:`)
- If the frontmatter has no `description` field, use the first sentence of the body as the description
- Note the command name (the filename without the `.md` extension)

### Step 3: Assign Categories

Group commands into logical categories by reading each command's name and description. Use your judgment — do not hardcode a fixed mapping. Suggested category labels:

- **Documentation & Reports** — commands that generate or update written artifacts: changelogs, devlogs, READMEs, Word/PPT reports, dev history, SBOM, style guides
- **Code Analysis & Review** — commands that analyze, compare, or review the codebase structure or quality
- **Testing** — commands that generate tests or guide a test-driven development workflow
- **Security** — commands that audit, scan, penetration-test, or harden the project
- **Git & Versioning** — commands that assist with commit messages, version bumps, or release preparation
- **Project Setup & Maintenance** — commands that configure, refactor, or maintain project structure, layout, and memory
- **Hub Management** — commands that manage the Nexus-Hub skill/command catalog (searching, importing, creating)
- **Utility** — session helpers, usage monitoring, and meta commands like this one

Adapt or add categories as needed if the installed command set includes commands that do not fit the suggestions above.

### Step 4: Render the Cheatsheet

Output a Markdown cheatsheet. For each category (in the order listed above, omitting empty categories), produce a section in this format:

```
## <Category Name>

| Command | What it does | When to use |
|---------|--------------|-------------|
| `/command-name` | Description from the frontmatter | Practical trigger phrase or short example invocation |
```

Rules:
- Every discovered command must appear in exactly one category table
- The **Command** column uses backtick-formatted `/command-name` syntax
- The **What it does** column is the frontmatter `description` value, verbatim or lightly trimmed to one sentence
- The **When to use** column gives a concrete, practical trigger (e.g., "Before opening a PR", "After finishing a feature branch", "`/search-skills security`")
- Sort rows alphabetically by command name within each table
- This command (`commands-cheatsheet`) belongs in the **Utility** category

### Step 5: Print a Summary Line

After all tables, print exactly one summary line:

```
Total: N commands across K categories  (discovered from: <paths checked>)
```

Where N is the total number of command files found and K is the number of non-empty categories rendered.
