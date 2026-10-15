---
name: writing-editing
description: Professional writing and editing principles for clear, concise documentation and prose. Use when asked to write, edit, rewrite, or review documents, README files, reports, blog posts, or any non-code text content.
summary_l0: "Write and edit professional documentation with clarity, structure, and concision"
overview_l1: "This skill applies professional editor and technical writer standards to all written output, covering clarity, concision, structure, active voice, logical hierarchy, and smooth transitions. Use it when writing, editing, rewriting, or reviewing documents, README files, reports, blog posts, or any non-code text content. Key capabilities include clarity and concision editing (removing fluff and jargon), active voice transformation, logical hierarchy structuring with headings and bullet points, smooth paragraph transitions, content refinement through iterative rewrites, and tone calibration for different audiences (technical, executive, end-user). The expected output is polished, well-structured prose with clear headings, concise language, active voice, and logical flow appropriate to the target audience. Trigger phrases: write documentation, edit text, rewrite, review document, improve writing, README, blog post, report writing, technical writing, proofread."
long_description: >
  Applies professional editor and technical writer standards to all written output.
  Covers clarity, concision, structure, active voice, logical hierarchy, and
  smooth transitions. Includes refinement guidance for rewrites.
category: Developer Experience
priority: MEDIUM
languages:
  - All
version: 1.0.0
---

# Writing & Editing

## Clarity & Concision
- Prioritize clear, direct language
- Avoid fluff and corporate jargon
- Use active voice where possible
- Cut unnecessary words without losing meaning

## Structure
- Use logical hierarchy with clear headings and bullet points
- Ensure smooth transitions between paragraphs
- Lead with the most important information (BLUF pattern)
- Group related ideas together

## Refinement
- When asked to rewrite, improve flow and impact while retaining original meaning
- Preserve the author's voice and intent
- Focus on readability and scan-ability
- Break long paragraphs into digestible chunks

## Style Rules
- Place punctuation outside quotation marks (logical punctuation)
- Do not use em-dashes to break up sentences; use parentheses, commas, or separate sentences
- Maintain a professional, helpful, and teaching tone

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The draft reads fine, it doesn't need editing" | First drafts carry passive voice, hedge words, and buried leads; skipping the edit pass ships a document the reader has to work to understand. |
| "More detail makes the writing more thorough" | Padding with fluff and jargon lowers signal density; cutting unnecessary words without losing meaning is what makes the same content scannable. |
| "I'll keep the conclusion at the end for impact" | Burying the key point forces every reader to read to the end; the BLUF pattern leads with the most important information so a skimming reader still gets it. |
| "An em-dash reads naturally here" | Em-dashes violate the project ASCII-punctuation rule and corrupt on Windows; parentheses, commas, or separate sentences carry the same break safely. |

## Verification

- [ ] The most important point appears first (BLUF), not buried in the conclusion
- [ ] Passive voice was converted to active voice where it does not distort meaning
- [ ] No em-dashes are used to break sentences (parentheses, commas, or separate sentences instead)
- [ ] Punctuation sits outside quotation marks (logical punctuation)
- [ ] Long paragraphs are broken into digestible chunks with logical headings

## Related Skills

- [[technical-writer]] -- produces audience-appropriate technical documentation with structured information architecture
- [[user-documentation]] -- applies these conventions to READMEs, guides, and tutorials
- [[analysis-logic]] -- supplies the BLUF and table structure this skill polishes into prose
- [[strategic-comments]] -- the same clarity discipline applied to in-code explanatory comments
