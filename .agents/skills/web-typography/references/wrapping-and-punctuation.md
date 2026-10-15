# Wrapping, Truncation, and Punctuation

## Wrapping

- `overflow-wrap: anywhere` on strings the user typed (URLs, emails, names) so a long token cannot blow the layout.
- `hyphens: auto` only when the nearest ancestor has `lang` and the column is narrower than about 45ch. Hyphenating English in a 70ch column is noise.
- `text-wrap: pretty` for headings and pull quotes (avoids orphans at the cost of extra layout). Skip on infinite-scroll feeds if profiling shows jank.
- `text-wrap: balance` for two-line headings and short cards, not for paragraphs.

`white-space: nowrap` on a nav item is allowed; on a paragraph it is a fail.

## Widows and orphans

CSS `widows` / `orphans` apply mainly to paged media. For screens, `text-wrap: pretty` is the practical control. Do not insert `<br>` to babysit line endings; it breaks translations.

## Truncation

Single line:

```css
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

Multi line: `-webkit-line-clamp` / `line-clamp` with `overflow: hidden`.

Rules:

1. `layout-and-spacing` tried wrap or a wider track first.
2. The full string is available (title plus a name AT can read, or a "Show more" that `interface-copy` worded).
3. Do not clamp error messages or legal text.

## Smart punctuation

In the product UI, use the punctuation the locale uses (straight apostrophe vs a typographic apostrophe, ASCII quotes vs guillemets). Do not convert a user's input as they type unless the field is a typesetting surface.

In this repository's English Markdown, ASCII hyphen and straight quotes remain the house style (`catalog/style-guides/markdown.md`). Do not "smart-quote" SKILL.md or CHANGELOG.md as part of a typography pass.

## Mixed direction

- Page `dir` from the document language.
- A nested opposite-direction phrase: `<span dir="rtl" lang="ar">...</span>` (or `dir="auto"` for mixed user input).
- `unicode-bidi: isolate` on user-generated snippets inside a toolbar so a leading RTL character does not flip the chrome.
- Logical properties for padding belong to `layout-and-spacing`; this skill only sets `dir` / `unicode-bidi` on the text node.
