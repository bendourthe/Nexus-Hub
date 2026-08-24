## Research-brief authoring

Turn a vague research need into ONE self-contained paragraph that a researcher with zero prior knowledge of the project can act on with zero back-and-forth. This is a distinct prompt-engineering deliverable: a PORTABLE brief you hand to a human researcher OR paste into any external deep-research tool. When Nexus-Hub itself runs the research, the `/research` command and its harness execute the brief; this technique writes the brief, it does not replace the harness.

Author the brief with these rules:

- **Open with a plain-English explainer.** Lead with one or two sentences saying what the project or product is and why it exists, written for a reader who has never heard of it.
- **State the mission and the decision.** Name the single question the research must answer and the decision that answer informs. One mission per brief.
- **Embed all context inline.** Put every name, date, prior known fact, and constraint directly in the paragraph; the researcher has nothing else to go on.
- **Number 3 to 6 sub-questions inline** so coverage is explicit and checkable.
- **State include and avoid constraints.** Say what is in scope and what to skip.
- **Declare a source hierarchy.** Prefer primary sources (official docs, source repositories, papers, filings, changelogs); treat forums and social posts as weak signal only.
- **Require contradiction handling.** Keep confirmed fact, inference, and unresolved uncertainty separate rather than forcing a false consensus, and flag every low-confidence claim explicitly.
- **Set a completion bar.** Do not stop at the first plausible answer; corroborate each key claim with multiple independent primary sources where they exist, and say so explicitly where they do not.
- **Require a final gap round.** End with a self-critique pass that lists gaps, contradictions, and single-source claims, then runs another search round to close them, repeating until clean.
- **Constrain the deliverable hard, the method loosely.** Fix the output shape; leave the researcher free to choose how to search.
- **Fix the per-finding output**: the source link, the specific claim, and a one-line "why it matters".
- **End with the output instruction.** Tell the researcher to write everything into a single detailed Markdown file.

Worked template (the shape to fill in, not the content):

```
We are researching [MISSION] for [PROJECT]. [PROJECT] is [one-line plain-English explainer of what it is and why it exists]. The one question this brief must answer is [QUESTION], which decides [DECISION]. Known context: [names, dates, facts, constraints]. Answer these sub-questions: (1) ...; (2) ...; (3) .... Include [in scope]; avoid [out of scope]. Prefer primary sources (official docs, repositories, papers, filings, changelogs); treat forums and social posts as weak signal. Separate confirmed fact from inference from open uncertainty, and flag anything low-confidence. Do not stop at the first plausible answer: corroborate each key claim with multiple independent primary sources, and say where none exist. For every finding give the source link, the specific claim, and a one-line why-it-matters. Finish with a self-critique pass listing gaps, contradictions, and single-source claims, then search again to close them and repeat until clean. Write everything into a single detailed Markdown file.
```

Related techniques: [[trend-research]] (surfacing what is worth asking about before the brief is written) and [[deep-research-compilation]] (merging the returned findings into one cited document).
