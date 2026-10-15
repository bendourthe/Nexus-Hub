# Form-to-tier map

Which rungs of the `html-output-conventions` ladder can express each chart form at all. Read this after the chart form is chosen (SKILL.md, step 3) and before the rung is picked (step 4). The ladder's own rule decides which eligible rung to stop at: the lowest one that answers the question. This file only removes rungs that cannot carry the form.

The rungs are those of the ladder: 1 prose, 2 small table, 3 short code block, 4 Mermaid diagram, 5 HTML artifact (built from `chart-template.html`).

| Form | Eligible rungs | Notes |
|---|---|---|
| Bar (one category, one measure) | 1, 2, 5 | A handful of categories is a sentence or a table. Mermaid has no bar chart that renders everywhere, so it is not eligible. |
| Line (ordered or time axis, one or two series) | 2, 5 | A trend over many points needs the HTML rung. A few points with an obvious direction can be a table, plus one sentence naming the trend. |
| Scatter (two measures) | 5 | Prose and tables cannot show correlation. If the HTML rung is unavailable, say the form cannot be shown and give summary statistics in a table instead. |
| Distribution (one measure's spread) | 2, 5 | A table of quantiles (min, quartiles, max) is eligible and often sufficient. A histogram needs the HTML rung. |
| Flow (ordered steps) | 2, 3, 4, 5 | Up to about a dozen steps is a Mermaid flowchart. Branching logic may be clearer as a short code block. |
| Dependency graph (nodes and edges) | 4, 5 | Up to about a dozen nodes is Mermaid. Past that, or where position carries meaning, the HTML rung applies, as the ladder states. |
| Architecture diagram (components and connections) | 4, 5 | Same thresholds as a dependency graph. Label every edge with what crosses it. |

## When the eligible rung is unavailable

A rung is unavailable when its host capability check fails: no headless browser to verify the HTML rung, or a Mermaid block that does not parse. Drop to the next lower eligible rung and name the observable reason in the tier line. If no eligible rung remains (a scatter with no HTML rung), say the form cannot be shown and give the closest honest substitute, such as summary statistics in a table. Never draw a different form and present it as the one asked for.
