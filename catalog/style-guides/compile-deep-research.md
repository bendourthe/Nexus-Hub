# Compile Deep Research Style Guide

This file is the quality reference for the `/compile-deep-research` command. Every merged markdown produced by that command MUST follow the patterns in this guide. Read this file completely before writing any content.

## Target Document Metrics

For a document compiled from 2-5 source reports covering a substantial topic:

| Metric | Target Range | Hard Limit |
|--------|-------------|------------|
| H1 headings (body, excluding Title/Purpose/TOC/References) | 5-9 | Never exceed 10 |
| H2 headings per body H1 | 3-8 | Never exceed 10 |
| H3 headings per H2 | 0-5 | Never exceed 6 |
| Total tables | 5-15 | Never exceed 20 |
| Bullet points (total) | 60-150 | Minimum 30 |
| Total lines in `merged.md` | 700-1300 | Never exceed 1600 |
| Canonical references | 10-80 | -- |
| Inline citations (per body paragraph average) | 0.5-2.0 | Never exceed 4 per sentence |

If your merged markdown exceeds any hard limit, fix it before calling the generator.

---

## Heading Hierarchy Template

```
(Title page -- emitted by the generator from title/subtitle/date, not in markdown)

<!-- PRE-TOC -->
# Document's Purpose                       <- 1-2 paragraphs, then metadata table
<!-- /PRE-TOC -->

(Table of Contents -- emitted by the generator as an auto-refreshing SDT field)

# Executive Summary                        <- 300-500 words, self-contained
  ## [Topic Area 1]                        <- one H2 per body section
  ## [Topic Area 2]
  ## [Topic Area N]

# [Body Section 1: Topic-Specific Name]    <- 3-10 H2 subsections
  ## 1. [Subtopic]
  ## 2. [Subtopic]

# [Body Section 2: Topic-Specific Name]
  ## ...

# Conclusion                               <- 1-3 paragraphs

# References                               <- stripped by the generator, re-emitted from refs.json
```

Use **real topic names** ("Clinical Evidence", "Competitive Landscape", "Regulatory Roadmap") rather than generic labels ("Background", "Analysis", "Findings"). The reader must be able to identify the contents of a section from its name.

---

## Citation Rules

- Inline citations use the format `[N]` where `N` is the canonical number from `refs.json`.
- Multi-citations: `[N,M]` (comma-separated, no spaces). The generator renders these as `[N, M]` with a superscript comma between hyperlinks.
- Every citation must correspond to a canonical reference in `refs.json`. Citations that point nowhere become "broken anchors" in the validator output.
- Citations always go **at the end of the relevant sentence**, before the period or comma. Example:

  > The SUPPORT I feasibility study reached its enrollment target in Q3 2025 [12].

- When two inputs had different local numbers for the same reference, both rewrite to the same canonical number. The renumbering map handles this automatically; you never manually choose which number to use.

---

## Good vs. Bad Body Paragraphs

### BAD (no citations, generic claims)

> The market for mechanical circulatory support is growing. Several competitors have launched new devices in the past few years. Our company has a strong position.

### GOOD (specific, cited, mined from source material)

Two example domains -- the same discipline applies regardless of subject matter.

**Medical device example (anonymized):**

> The US market for the target device class reached $1.1B in 2024 and is projected to exceed $2.3B by 2030 [8]. Company A remains the dominant platform with an estimated 65% share of the relevant procedures [12,14], but Company B's smaller-profile access strategy and in-situ unloading algorithm target the 20-25% of patients for whom Company A's larger delivery catheter is contraindicated [6,23].

**Open-source library benchmark example:**

> Library X processed 1.2M requests/sec on the reference benchmark hardware in v3.1 -- a 38% improvement over v2.4 [3]. Library Y, the closest functional equivalent, plateaued at 740K requests/sec in its 4.0 release and has not shipped a new major version in 14 months [5,9]. Library Z (added to the benchmark in March 2026) hit 1.05M requests/sec on the same hardware while consuming 22% less memory than X [11].

---

## Overlap Handling Across Inputs

When the same topic appears in multiple inputs:

1. **Merge, don't concatenate.** Write one coherent paragraph that captures what every input contributes, with citations to each.
2. **Collapse contradictions.** If two inputs disagree on a fact, note the disagreement briefly with citations to both.
3. **Preserve specificity.** Choose the version with concrete numbers, names, and dates over the version with generalities.
4. **Stitch cross-references.** If Input A defines a term and Input B uses it, keep the definition from A near where B first references it.

---

## Structural Rules

- Every H1 and H2 opens with 1-3 sentences of prose context. Never start with a table, list, or sub-heading.
- Paragraphs are 3-5 sentences max. A paragraph that runs past 5 sentences probably has two ideas and needs splitting.
- Tables: max 15 rows, max 5 columns. Each table is preceded by a context sentence and followed by a takeaway sentence.
- Bullet lists for enumerable items (features, findings, counterexamples). Numbered lists for sequenced steps.
- Never put implementation steps in a table -- use `### Step N:` sub-headings with objective, sub-steps, and verification.
- Never include `# Table of Contents` -- the generator inserts the TOC.
- Never hand-author `# References` entries with styling; the generator re-emits References from `refs.json`. Your `# References` block in the merged markdown is a hint to the parser only.

---

## Metadata Table

The generator inserts the metadata table automatically from the confirmed Author and Date. Your merged markdown should not contain a hand-authored metadata table -- but if it does, the generator will render it as a regular table (the auto-emitted one is styled with the borderless-row-rules look derived from the template's style profile).

---

## Self-Check Before Generation

Count in your merged markdown before invoking the generator:

1. **H1 headings**: should be 5-9 body H1s (Purpose + Exec Summary + 3-5 body + Conclusion). Plus `# References` if you emit one. Fix if outside this range.
2. **H2 headings per body H1**: 3-8. Fewer than 3 means the section lacks depth; more than 10 means break it.
3. **Prose opener check**: spot-check 5 H2 sections. Each must start with a sentence, not a table or list.
4. **Citation density**: every analytical claim that came with a citation must keep one. If a source paragraph had 4 citations and the synthesized paragraph has 1, you dropped information.
5. **No duplicate headings**: each heading text should appear once.
6. **Line count**: 700-1300 lines target. Under 600 is thin; over 1600 is content-dumping.
7. **PRE-TOC markers**: the Document's Purpose section is wrapped in `<!-- PRE-TOC -->...<!-- /PRE-TOC -->`.
8. **Citation format**: all citations are `[N]` or `[N,M]` -- no `[N; M]`, `[N and M]`, or other variants.

If any check fails, fix the merged markdown before calling the generator.
