# Markdown Style Guide for Generated Documentation

This file is the canonical style reference for every Markdown file Nexus-Hub generates or modifies. Read it before producing any new documentation. The conventions below address the most common cross-renderer rendering bugs (GitHub, VS Code preview, Cursor preview, JetBrains preview, npm-rendered READMEs, marketplace listings).

The rules are not stylistic preferences. They are concrete fixes for rendering inconsistencies that appear across CommonMark, GitHub-Flavored Markdown (GFM), and the various preview implementations.

## Files Governed

This style applies to every Markdown artifact produced by Nexus-Hub commands and skills, including:

- `README.md`, `README_zh.md`, and any subdirectory READMEs
- `CHANGELOG.md`, `DEVLOG.md`
- `RELEASE_NOTES.md`
- Plans (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/*.md`)
- Comparison reports (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/comparisons/v<MAJOR>.<MINOR>.<PATCH>-comparison-*.md`)
- Pen test reports (`docs/security/penetration-test-*.md`)
- Session histories (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/*.md`)
- Skill files (`catalog/skills/<cat>/<name>/SKILL.md`)
- Command files (`catalog/commands/*.md`)
- Style guides (`catalog/style-guides/*.md`)
- Generated reports from `/generate-report` and `/compile-deep-research`

## The Core Rules

### 1. Always a blank line before a list

Lists immediately following a paragraph or heading without a blank line render inconsistently. Some renderers treat the list as part of the preceding paragraph; others treat it as a list with awkward spacing.

```markdown
<!-- WRONG -->
Some intro paragraph.
- First item
- Second item

<!-- RIGHT -->
Some intro paragraph.

- First item
- Second item
```

This rule applies to ordered lists, unordered lists, and lists that follow a heading.

### 2. Always a blank line after a list

Same problem in reverse: a paragraph or heading following a list without a blank line gets absorbed into the last list item by some renderers.

```markdown
<!-- WRONG -->
- Last item
Next paragraph runs into the list.

<!-- RIGHT -->
- Last item

Next paragraph stands on its own.
```

### 3. Single space after the bullet marker

Use `- text`, not `-   text`. Use `1. text`, not `1.  text`. Multiple spaces are valid CommonMark but render unevenly across previewers, especially when the list item contains formatting like bold text.

```markdown
<!-- AVOID -->
*   **Item**: description

<!-- USE -->
- **Item**: description
```

### 4. `-` for unordered, `1. 2. 3.` for ordered

Pick one bullet character for unordered lists and use it everywhere. `-` is the consensus choice across modern style guides (Google, Microsoft, GitHub docs). Avoid mixing `*` and `-` within a single document.

For ordered lists, use sequential numbering (`1.`, `2.`, `3.`). Renderers will auto-correct the displayed numbers, but human readers diff the source - sequential numbering reads better.

### 5. Loose vs tight lists is a deliberate choice

A **tight list** has no blank lines between items. It renders compactly:

```markdown
- First
- Second
- Third
```

A **loose list** has blank lines between items. It renders with `<p>` tags around each item, creating breathing room:

```markdown
- First item with multi-sentence content. The blank line after this item makes it loose.

- Second item also has breathing room because the list is loose.

- Third item.
```

Choose intentionally:

- **Use tight lists** for short, parallel items (e.g. a list of file names, a quick enumeration of steps).

- **Use loose lists** when items have multi-sentence content, code blocks, sub-lists, or when readability suffers from compactness.

A mixed list (some items with blank lines, some without) is rendered as loose by CommonMark - but the visual result is uneven. Be consistent within a single list.

### 6. Nested lists use 4-space indent

Indent nested items by exactly 4 spaces from the start of the parent item's text (not from the bullet marker).

```markdown
<!-- WRONG (2-space indent fragile across renderers) -->
- Parent item
  - Nested

<!-- RIGHT (4-space indent) -->
- Parent item
    - Nested
```

CommonMark allows 2-space indent in many cases, but VS Code preview, JetBrains preview, and some GitHub contexts have rendered 2-space-indented nested lists at the parent level. 4-space indent is the safest universal pattern.

### 7. Code blocks inside list items

Three rules together:

- Blank line BEFORE the fence
- Blank line AFTER the closing fence
- Indent the fence (and content) by 4 spaces relative to the parent list item's text content. For a top-level list item, that means 4 spaces. For a nested list item, that means 8 spaces.

```markdown
<!-- RIGHT (top-level list item with code block) -->
1. Run the migration:

    ```bash
    bun run db:migrate
    ```

2. Verify the schema:

    ```bash
    bun run db:status
    ```
```

Without the blank lines and the 4-space indent, code blocks inside list items render unpredictably (sometimes as code, sometimes as a preformatted text run within the list item, sometimes breaking out of the list entirely).

### 8. Tables

Always a blank line before and after a table. Use pipe-delimited syntax with the `|---|` separator row required even for two-column tables. Right-pad cells to align in source for readability (the renderer ignores the padding):

```markdown
Some intro paragraph.

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| value 1  | value 2  | value 3  |

Continuing paragraph.
```

### 9. Headings

- Use ATX-style (`# Heading`), not Setext (`Heading\n======`).
- Always a blank line before AND after a heading.
- Skip exactly one level when descending (do not jump from `##` to `####`).
- One `#` (H1) per document, used as the title.

### 10. Hard-wrap rule

**Never hard-wrap paragraph text at a fixed column width.** Each paragraph or bullet point is a single continuous line in the source. Editors and renderers handle visual wrapping. This rule already exists at the global CLAUDE.md level; it is restated here because some markdown linters default to hard-wrap-enforcing rules and would conflict.

### 11. No emoji-only headings

Emoji are fine as ornamental markers, but always paired with text:

```markdown
<!-- AVOID -->
## 🎯

<!-- USE -->
## 🎯 Recommended Workflows
```

Emoji-only headings break automatic anchor generation in many renderers.

### 12. Inline code in list items: surround with single backticks

```markdown
- Run `make test` before committing.
```

For multi-line code, use a fenced block (rule 7).

### 13. Links

- Prefer reference-style links for repeated URLs in long documents.
- For one-off links, inline `[text](url)` is fine.
- Always include alt text for images: `![alt text](path)`.
- For internal repo links, use repo-relative paths: `[CHANGELOG](../CHANGELOG.md)`, not `[CHANGELOG](https://github.com/.../CHANGELOG.md)`. Reference-style and relative links survive forks and clones; absolute links break.

### 14. Plain ASCII commit messages and code (per project rule)

This rule lives in `CLAUDE.md` but applies to anything generated as Markdown content too: avoid em-dashes, en-dashes, curly quotes, ellipsis characters, and other Unicode punctuation. Use hyphens, straight quotes, and `...` (three dots) instead. This prevents encoding corruption on Windows when the file is later read by tools that default to cp1252.

Exception: Chinese, Japanese, or other natural-language content (such as `README_zh.md`) may use the Unicode characters native to that language. The ASCII rule applies to English-language Markdown.

## Quick Reference Card

For commands and skills that need a short summary instead of the full guide:

| Rule | One-line form |
|------|---------------|
| Lists | Blank line before AND after every list |
| Bullet | Use `-`, single space after |
| Numbered | Use `1. 2. 3.`, single space after |
| Nested | 4-space indent |
| Code in list | Blank line before/after fence; 4-space indent |
| Tables | Blank line before/after; `|---|` separator |
| Headings | Blank line before/after; ATX-style; one `#` per doc |
| No hard wrap | Each paragraph or bullet is one continuous line |
| ASCII | English Markdown is ASCII-only (hyphens, straight quotes, `...`) |

## Automated enforcement (markdownlint-cli2)

The prose rules in this guide have an executable counterpart at `catalog/style-guides/markdownlint-cli2.jsonc`. The installer copies the entire `catalog/style-guides/` tree to `~/.nexus-hub/style-guides/` via the recursive `safe_folder_copy` / `Safe-Folder-Copy` primitives in `scripts/installer.sh` and `scripts/installer.ps1`, so the JSON config lands automatically alongside this guide.

To enable enforcement in a downstream project bootstrapping from Nexus-Hub:

1. Copy the file to the project root as `.markdownlint-cli2.jsonc`:

    ```bash
    cp ~/.nexus-hub/style-guides/markdownlint-cli2.jsonc .markdownlint-cli2.jsonc
    ```

2. Run the linter (no global install required - `npx` fetches `markdownlint-cli2` on demand):

    ```bash
    npx markdownlint-cli2 "**/*.md"
    ```

3. Optionally wire the linter into CI or a pre-commit hook. The config disables MD013 (line length) and MD036 (emphasis-as-heading) intentionally - those rules conflict with the no-hard-wrap and table-card conventions used across the Nexus-Hub catalog.

The JSON config is documented inline (JSONC comments). If you want to tighten a rule for a specific project (e.g. enforce MD040 for fenced code-block languages on a repo with strict editorial standards), edit the `config` block directly; the catalog version is a starting baseline, not a frozen contract.

## Verification

Before committing any generated Markdown, the agent should self-check:

- Does every list have a blank line above and below?
- Are all nested lists indented by 4 spaces?
- Are code blocks inside list items preceded and followed by blank lines?
- Are headings preceded and followed by blank lines?
- Is the file ASCII-clean (for English content)?

If any of these fail, fix them before reporting the document as complete.
