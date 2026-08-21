---
name: creative-generation
description: Creative direction for image prompts, presentation slides, and ideation. Use when asked to generate image prompts, design slide decks, brainstorm ideas, create visual concepts, or produce creative content.
summary_l0: "Generate image prompts, slide decks, and creative ideation with structured direction"
overview_l1: "This skill applies creative director standards to generative and design tasks, covering detailed image generation prompts, presentation slide design with speaker notes, and structured ideation with varied, distinct options. Use it when generating image prompts, designing slide decks, brainstorming ideas, creating visual concepts, or producing creative content. Key capabilities include detailed image generation prompt construction (subject, style, lighting, composition, mood, negative prompts), presentation narrative design with logical flow and speaker notes, structured ideation with varied and distinct creative options, visual concept development, and creative brief interpretation. The expected output is polished creative deliverables including detailed image prompts with specifications, slide deck outlines with speaker notes, and structured brainstorm outputs with diverse options. Trigger phrases: generate image prompt, design slides, brainstorm ideas, creative concept, visual design, presentation deck, ideation, creative brief."
long_description: >
  Applies creative director standards to generative and design tasks.
  Covers detailed image generation prompts, presentation slide design with
  speaker notes, and structured ideation with varied, distinct options.
category: Developer Experience
priority: MEDIUM
languages:
  - All
version: 1.0.0
---

# Creative Generation

## Image Generation Prompts
- Provide detailed, descriptive prompts including subject, style, lighting, composition, and mood
- Specify negative prompts to avoid common artifacts
- Include aspect ratio and resolution preferences when relevant

## Presentation Slides
- Outline clear narratives with logical flow
- Slide content: concise bullet points, key visual descriptions
- Speaker notes: detailed talking points and context for the presenter
- One key idea per slide

## Ideation
- Generate distinct, varied options rather than slight variations of the same idea
- Focus on novelty and relevance to the stated goal
- Present at least 3 meaningfully different approaches
- Explain the rationale behind each option

## Static Poster / Print Workflow

For static-art outputs intended for print or fixed-format distribution (posters, one-page handouts, conference signage, exported PDFs), do not jump straight to rendering. Use a deliberate two-step approach: write the philosophy first, then express it.

### Step 1: Design philosophy

Before any pixel is rendered, write a short Markdown manifesto (typically 30-80 lines) that fixes the design direction:

- **Color palette** -- 3 to 5 named colors with hex values; one accent, one or two neutrals, one or two secondaries. State which color is dominant, which is the punctuation.
- **Typography** -- display face for the headline, body face for supporting copy, optional monospace for tabular or technical content. State the type pairing and at least one reason it matches the brief.
- **Composition principles** -- what occupies which third of the canvas; whether the layout is symmetric or asymmetric; which element is the focal point and how the eye is directed there.
- **Reference movements** -- 1 to 2 design lineages the piece draws from (e.g., Swiss / International style, mid-century modern editorial, Bauhaus geometric, contemporary brutalism). Cite them as a directional anchor, not as imitation targets.

Save the manifesto next to the output (e.g., `poster-philosophy.md` alongside `poster.pdf`). It is the artifact that lets a second iteration converge on the same direction instead of drifting.

### Step 2: Visual expression

Render the actual `.png` / `.pdf` output via whichever path matches the format:

- **Slide / deck output** → invoke the `pptx-generation` skill.
- **Document or letter-format poster** → invoke the `docx-generation` skill.
- **Print-quality PDF** → invoke the `pdf-document-generation` skill.
- **One-off bespoke layouts** that none of the above cover cleanly → write a single-purpose Python script using Pillow (`PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`) for raster output or `matplotlib` for plot-driven layouts. Keep the script small and readable; the philosophy doc is the durable artifact, not the script.

The manifesto fixes the direction; the renderer fixes the format. Iterate on the manifesto when the design needs to change; iterate on the script only when the format needs to change.

### Out of scope for this skill

Generative / algorithmic / interactive visual outputs (p5.js sketches, HTML canvas, real-time parameterized art) belong to the `generative-art` skill, not here. If the deliverable is an interactive HTML canvas, switch skills.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We don't need a philosophy step for one poster." | Without it, the agent defaults to AI-slop visuals (generic gradient backgrounds, centered title, three-icon grid). The manifesto is 50 lines and saves a 10x rework when the first render misses the brief. |
| "I'll iterate on the rendered image directly." | Rendered iteration is expensive and hard to compare. Iterating on the manifesto first lets you fix direction in 5 minutes of writing, not 30 minutes of re-rendering. |
| "The user only said 'make a poster', so any poster is fine." | The user said "poster" because they don't have the vocabulary to specify direction. The manifesto is how you offer a direction back to them and confirm before rendering. |

## Verification

- [ ] For static print output, a philosophy manifesto exists next to the render (e.g., `poster-philosophy.md` beside `poster.pdf`)
- [ ] The manifesto names a 3-5 color palette with hex values and identifies the dominant color and accent
- [ ] Image prompts specify subject, style, lighting, composition, mood, and at least one negative prompt
- [ ] Ideation output presents at least 3 meaningfully different approaches, each with a stated rationale
- [ ] The rendered format was produced through the matching skill (pptx/docx/pdf), not improvised

## Related Skills

- [[pptx-generation]] -- renders slide and deck output once the creative direction is fixed
- [[docx-generation]] -- renders document or letter-format poster output from the manifesto
- [[pdf-document-generation]] -- produces print-quality PDF output for fixed-format distribution
- [[generative-art]] -- handles interactive and algorithmic visual outputs that are out of scope here
