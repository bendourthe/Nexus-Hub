## Step 3: Synthesize Unified Content

This is intellectual work, not mechanical. Write the merged markdown yourself after reading every extracted section from every source.

### Rules

1. **No redundancy.** If three inputs each describe "market size" or "competitive landscape", produce *one* paragraph that integrates what each says, with citations to each contributing source. Do not emit three separate paragraphs that say the same thing.
2. **Preserve specificity.** Given two versions of a fact, keep the one with concrete numbers, names, and dates.
3. **Stitch cross-references.** If input A defines a term and input B uses it, keep the definition near its first use in the merged document.
4. **Name body sections after actual themes.** Not "Background / Analysis / Conclusion" but "Clinical Evidence / Competitive Landscape / Regulatory Roadmap / Strategic Positioning" -- whatever the material actually covers.
5. **Propose the section list to the user.** Before writing the merged markdown, show the planned outline (H1s + H2s + optional H3s). Offer up to 3 edit iterations.
6. **Prefer tables over multi-column bullets** for comparative data. Limit tables to 15 rows x 5 columns.
7. **Illustrate sparingly.** Insert `[Figure N: title]` placeholders with a caption sentence where a diagram would add clarity. Do not try to generate actual figures in the `.docx` -- placeholders are intentional.

### Mandated structure

```
(Title page)
# Document's Purpose            -- one paragraph, then metadata table
(TOC inserted here)
# Executive Summary             -- 300-500 words, self-contained
  ## <H2 per body theme>
# <Body H1 #1>                  -- 3-10 H2 subsections
  ## <subtopic>
# <Body H1 #2>
  ...
# <Body H1 #N>                  -- 3-7 body H1s total
# Conclusion                    -- 1-3 paragraphs synthesizing takeaways
# References                    -- emitted from canonical ref list
```

### Write the merged markdown

Save to `<cache_dir>/merged.md`. Every sentence that carried a citation in the source retains one, with the canonical `[N]` number. No `# Table of Contents` heading. Wrap Document's Purpose in `<!-- PRE-TOC -->...<!-- /PRE-TOC -->` so the generator knows where the TOC inserts.

This `merged.md` is an intermediate. The final user-facing `.md` output (when the user requests Markdown) lives at `<final_dir>/<ReportTitle>.md` and is produced in Step 6 by wrapping this file with a title heading, a manual linked TOC, `<sup>[[N]](#refN)</sup>` citation anchors, and a References section with `<a id="refN">` anchors.

Target: 700-1300 lines.

---
