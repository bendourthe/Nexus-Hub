---
name: analysis-logic
description: Structured analytical reasoning and data presentation principles. Use when asked to analyze data, compare options, evaluate trade-offs, create decision matrices, or present findings with tables and structured reasoning.
summary_l0: "Apply structured analytical reasoning with decision matrices and data presentation"
overview_l1: "This skill applies data analyst and strategist standards to analytical tasks, covering step-by-step reasoning, assumption identification, BLUF (Bottom Line Up Front) summaries, table-based comparisons, and critical thinking with edge case consideration. Use it when analyzing data, comparing options, evaluating trade-offs, creating decision matrices, or presenting findings with structured reasoning. Key capabilities include step-by-step problem decomposition, assumption and bias identification, BLUF summary generation, table-based comparison creation, decision matrix construction with weighted criteria, edge case and alternative interpretation analysis, and structured findings presentation. The expected output is clear analytical reports with BLUF summaries, comparison tables, decision matrices, identified assumptions, and well-reasoned conclusions. Trigger phrases: analyze data, compare options, evaluate trade-offs, decision matrix, structured analysis, pros and cons, data presentation, BLUF summary, critical analysis."
long_description: >
  Applies data analyst and strategist standards to analytical tasks.
  Covers step-by-step reasoning, assumption identification, BLUF summaries,
  table-based comparisons, and critical thinking with edge case consideration.
category: Developer Experience
priority: MEDIUM
languages:
  - All
version: 1.0.0
---

# Analysis & Logic

## Structured Reasoning
- Show your work; break down complex problems step-by-step
- Identify assumptions and potential biases explicitly
- Consider edge cases and alternative interpretations
- Challenge premises if they seem incorrect

## Data Presentation
- Use tables for comparisons and structural data
- Summarize key insights at the top (BLUF: Bottom Line Up Front)
- Quantify where possible; avoid vague qualifiers
- Label data sources and confidence levels

## Decision Support
- Present trade-offs clearly with pros/cons
- Recommend an approach with supporting rationale
- Highlight risks and mitigation strategies
- Distinguish facts from opinions

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The recommendation is obvious, I'll skip the decision matrix" | Without weighted criteria the obvious choice is often the one that fit your prior, not the one that scores best; the matrix surfaces the option you discounted. |
| "I'll just say it's faster, no need to quantify" | Vague qualifiers like "faster" hide the magnitude; a reader cannot act on "faster" but can act on "30% lower P95 latency". |
| "I don't need to state my assumptions, they're standard" | An unstated assumption (e.g., "traffic stays flat") is exactly where the analysis silently breaks when the assumption fails in production. |
| "Putting the conclusion last builds the argument better" | Burying the answer forces every reader to reconstruct it; BLUF puts the bottom line first so a skimming decision-maker still gets the recommendation. |

## Verification

- [ ] The output opens with a BLUF summary stating the recommendation up front
- [ ] Comparisons are presented as tables, not prose paragraphs
- [ ] Every quantitative claim cites a number and its source or confidence level
- [ ] Assumptions and known biases are listed explicitly in a dedicated section
- [ ] At least one alternative interpretation or edge case is considered before concluding

## Related Skills

- [[creative-generation]] -- structures ideation output the way this skill structures analytical output
- [[writing-editing]] -- tightens the prose around the tables and BLUF this skill produces
- [[technical-debt-analyzer]] -- a domain-specific application of weighted decision matrices to remediation priority
- [[product-manager]] -- consumes these decision matrices when prioritizing features and trade-offs
