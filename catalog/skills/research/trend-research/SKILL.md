---
name: trend-research
description: Research any topic across Reddit, X (Twitter), and the web to identify recent trends (last 30 days) and generate production-ready prompts or recommendations
summary_l0: "Research recent trends across Reddit, X, and the web with prompt generation"
overview_l1: "This skill researches any topic across Reddit, X (Twitter), and the web to identify recent trends from the last 30 days and generate production-ready prompts or recommendations. Use it when exploring emerging trends in a technology area, generating up-to-date prompts based on community consensus, identifying best practices from recent discussions, or producing research summaries for decision-making. Key capabilities include multi-source trend research (Reddit, X/Twitter, web), last-30-day time window filtering, community consensus identification, best practice extraction, production-ready prompt generation from research findings, and structured recommendation reports. The expected output is a research report with identified trends, community consensus, and copy-paste-ready prompts or recommendations. Trigger phrases: research trends, latest trends, what is trending, community consensus, recent best practices, trend analysis, research topic."
version: 1.0.0
author: Benjamin Dourthe (ported from mvanhorn/last30days-skill)
category: Research
language: Multi-language
tags: [research, trends, prompt-engineering, analysis]
tools_required: [Search]
---

# Trend Research & Prompt Generation

This skill enables you to research any topic to find the latest trends, best practices, and community consensus from the last 30 days, and then turn that research into high-quality, copy-paste-ready prompts or recommendations.

## 1. Parse User Intent
Before researching, identify these three variables from the user's request:
1.  **TOPIC**: What they want to learn about (e.g., "Claude Code workflows", "shadcn/ui templates").
2.  **TARGET_TOOL** (Optional): Where they will use the output (e.g., "Cursor", "Midjourney", "ChatGPT").
3.  **QUERY_TYPE**:
    *   **PROMPTING**: "prompts for X", "how to prompt X" (Goal: Create a prompt)
    *   **RECOMMENDATIONS**: "best X", "top tools for Y" (Goal: List of items)
    *   **NEWS**: "latest on X", "what's new with Y" (Goal: Summary of events)
    *   **GENERAL**: Everything else (Goal: Broad understanding)

## 2. Execute Research (Native)
Perform a targeted search using your `Search` tool. Do NOT use Python scripts or external APIs. Use your internal browsing capabilities.

### Search Strategy
Run these specific search queries in order:

**Query 1: Community Discussions (Reddit/Forums)**
*   Search for: `site:reddit.com "{TOPIC}" after:2025-12-01` (Adjust date to ~30 days ago)
*   *Goal*: Find what real users are discussing, debating, and upvoting.

**Query 2: Current Trends (General Web)**
*   Search for: `"{TOPIC}" latest trends 2026` OR `"{TOPIC}" best practices 2026`
*   *Goal*: Find articles, blog posts, and news from the last month.

**Query 3: Prompt Specifics (If QUERY_TYPE is PROMPTING)**
*   Search for: `"{TOPIC}" prompt examples` OR `"{TOPIC}" system prompt template`
*   *Goal*: Find the specific JSON/XML/Markdown formats that work best for this topic.

## 3. Synthesize Findings (The Judge Agent)
Analyze the search results. apply these "Judge" rules:
1.  **Weight Community Higher**: Trust repeated mentions in Reddit threads/X posts over generic SEO blog posts.
2.  **Look for Formats**: If multiple sources say "Use JSON for this tool" or "Include rigid constraints", NOTE THAT. This is critical for the final output.
3.  **Identify Consensus**: What are the top 3-5 things everyone agrees on?
4.  **Ignore Noise**: Discard generic advice that applies to everything (e.g., "be specific"). Focus on topic-unique advice.

### Worked example: quoting from the search results

**Request**: "What are people saying about growing basil under LED panels indoors?"

**Search results** (native search, excerpted in templated form):

```text
[community thread, 9 days ago] ... moved the panel to 30 cm and the leaf curl stopped within a week ...
[community thread, 21 days ago] ... 16 hours of light was too much for my setup; 14 fixed the bitter taste ...
[grower blog, 12 days ago] ... a 30 cm hang height at 14 to 16 hours a day is the sweet spot most growers land on ...
```

**Response** (the synthesized finding):

> The threads and the blog converge on two settings: a hang height near 30 cm and a light period of 14 to 16 hours. They differ on the upper end of that range. One grower reports that 16 hours produced a bitter crop and that dropping to 14 fixed it, while the blog treats the full range as safe. One thread pins the leaf-curl symptom on the panel sitting too close, describing the fix as moving the panel to 30 cm, after which "the leaf curl stopped within a week".

**Rationale**: the finding is organized around agreement and difference, not source by source; each source is conveyed in the agent's own words in one or two sentences; exactly one short phrase is marked as a quotation and tied to its source; the numbers stay specific (30 cm, 14 to 16 hours, one week) and nothing else is reproduced verbatim.

## 4. Generate Output
Based on the `QUERY_TYPE`, generate the final response.

### If QUERY_TYPE is PROMPTING
Write **ONE** perfect, massive, copy-paste-ready prompt.

**CRITICAL**: The prompt format **MUST** match your research findings.
*   If research says "Use XML tags", ANY prompt you write MUST use XML tags.
*   If research says "Use JSON", use JSON.
*   *Do not use your default style if the research suggests a different specific format is better for this tool.*

**Output Structure**:
```markdown
# Trend Research: {TOPIC}

Based on analysis of community discussions from the last 30 days:
*   **Key Insight 1**: [Insight]
*   **Key Insight 2**: [Insight]
*   **Format Consensus**: The community recommends using [Format, e.g., JSON/XML] for best results.

---

## Generated Prompt for {TARGET_TOOL}

```text
[THE ACTUAL PROMPT CONTENT GOES HERE]
[Ensure it follows the constraints finding in your research]
```
```

### If QUERY_TYPE is RECOMMENDATIONS
Provide a ranked list based on **community sentiment**, not just popularity.

**Output Structure**:
```markdown
# Top Recommendations for {TOPIC}

1.  **[Item Name]**
    *   *Why it's trending*: [Specific reason from research, e.g., "Released v2.0 last week"]
    *   *Community Consensus*: [Positive/Negative sentiment]
    
2.  **[Item Name]** ...
```

### If QUERY_TYPE is NEWS/GENERAL
Provide a "State of the Union" summary.

**Output Structure**:
```markdown
# State of {TOPIC}: Last 30 Days

## 🚨 Headlines
*   [Major Event 1]
*   [Major Event 2]

## 📈 Trending Discussions
*   [What are people arguing about?]
*   [What are people excited about?]

## 💡 Takeaway
[One sentence summary of the current vibe]
```


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "My training data already knows this topic, so I can skip the search" | Training data has a fixed cutoff; a 30-day trend window is by definition newer than any cutoff, so skipping the search returns stale consensus that contradicts what the community now recommends. |
| "One web query is enough to call something a trend" | A single SEO blog post is marketing, not consensus. Without cross-checking Reddit and X you cannot distinguish a vendor's launch announcement from an actual community-validated practice. |
| "I can write the prompt in my default style instead of the format the research found" | If the research shows the target tool needs XML tags or JSON and you ship Markdown prose, the prompt underperforms on that tool -- the format finding is the deliverable, not a suggestion. |
| "I will keep results from older than 30 days because they look authoritative" | Old high-ranking pages describe deprecated APIs and retired tools; including them dilutes the trend signal the user explicitly asked for. |

## Verification

- [ ] At least three distinct search queries were run (community, general web, and format-specific when QUERY_TYPE is PROMPTING).
- [ ] Every cited trend draws on a source dated within the last 30 days of the request.
- [ ] The output identifies an explicit community consensus (top 3-5 agreed points), not just a single source.
- [ ] If QUERY_TYPE is PROMPTING, the generated prompt's format matches the format consensus found in research.
- [ ] The final report follows the output structure for the detected QUERY_TYPE (PROMPTING, RECOMMENDATIONS, or NEWS/GENERAL).

## Related Skills

- [[prompt-engineering]] -- refine and structurally evaluate the prompt this skill generates from trend findings.
- [[deep-research-compilation]] -- compile multiple trend reports into one cited deliverable when the topic spans several sessions.
- [[cross-project-comparison]] -- compare the surfaced trends against the current project to produce an adoption plan.
