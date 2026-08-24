## Core Principle

**You are the generator.** There is no `scripts/compile_deep_research.py`. There is no hardcoded Python function that emits docx. Per invocation, you:

1. Read the user's template and build a style profile from its actual XML.
2. Read each input document and normalize into a uniform representation.
3. Synthesize the merged content (deduplicating refs, renumbering citations, eliminating redundancy).
4. Write a one-shot python-docx program adapted to the template's own styles.
5. Run the program via Bash to produce the `.docx`.
6. Convert to `.pdf` (if requested) via `docx2pdf` / `libreoffice`, or emit `.md` directly via the Write tool.
7. Validate the output and iterate if anything fails.

The program you write in step 4 is saved to `<cache_dir>/generate.py` for user reproducibility but is not reused across invocations. Every invocation starts fresh from the current template + content.

### File layout (resolve these paths at the start of the run)

- `<final_dir>` = `<project_root>/docs/compiled/` -- user-facing final outputs only (`.docx`, `.pdf`, `.md`).
- `<cache_dir>` = `<project_root>/.cache/compile-deep-research/<ReportTitle>/` -- every intermediate artifact (`merged.md`, `refs.json`, `style_profile.json`, `generate.py`, `ingest.json`). Recommend the user gitignore `.cache/`.

Never mix the two. The final outputs must not share the directory with intermediates, and the `<Title>_` filename prefix is dropped on artifacts since the subdirectory scopes them.

The anti-patterns that will wreck the output:
- Using a hardcoded brand color (e.g., `#215868`), font (Consolas), or size from one specific source template -- every value must come from the template's own styles.xml.
- Using `paragraph.style = doc.styles["Heading 1"]` in python-docx -- this silently fails on templates where the style isn't already applied in the body. Always write `<w:pStyle w:val="StyleId">` directly into the paragraph's `<w:pPr>`.
- Flattening `[N]` citations to plain text -- they must be the 3-run superscript + internal-hyperlink pattern or Word won't navigate.
- Skipping the post-generation validation -- "Word found unreadable content" warnings and empty TOCs are caught here.

---
