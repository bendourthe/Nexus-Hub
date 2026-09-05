---
name: deep-research-compilation
description: Compile multiple research reports (.docx/.md/.pdf/.pptx/.html/.txt/URLs) into one unified document (.docx, .pdf, or .md) with deduplicated inline [N] citations linking to a References section. The agent analyzes the user's template at runtime and writes a throwaway python-docx program tailored to that template's styles -- no persistent generator.
summary_l0: "Compile multi-source research into a template-matched document with managed citations"
overview_l1: "Use when a user has several related research sources and wants them merged into one coherent, citation-rich document whose visual style matches a chosen Word template. The agent ingests heterogeneous inputs (.docx/.md/.pdf/.pptx/.html/URLs/.txt), synthesizes the content with no redundancy, deduplicates references by DOI / normalized URL / fuzzy title, renumbers inline [N] citations against a canonical list, inspects the selected template to build a style profile (fonts, colors, sizes, TOC settings, table borders, hyperlink color), then authors a one-shot python-docx program per invocation that produces a .docx whose appearance is driven entirely by that style profile -- never by hardcoded values. Also emits .md (with clickable anchor citations) and .pdf (via docx2pdf or libreoffice). Trigger phrases: compile research, merge reports, consolidate literature review, combine research documents, deep research compilation, unified report with citations, compile to docx matching template, reference deduplication, citation renumbering."
---

# Deep Research Compilation

This skill is the agent-driven, template-matching playbook for compiling multi-source research into a single unified document. It replaces the older script-based approach: every invocation, **you (the agent) do the generation work yourself** -- inspect the template, synthesize content, write a throwaway python-docx program tailored to that template, run it, validate the output. No persistent generator exists and none should be written.

## When to Use This Skill

- The user has several research sources (Claude Desktop outputs, Gemini deep-research, ChatGPT reports, Word/PDF whitepapers, URLs, Markdown drafts) and wants them compiled into one coherent document.
- The user wants the output to visually match a specific Word template they supply or pick from the defaults.
- The output must carry clickable inline `[N]` citations that link to a References section whose entries are themselves clickable hyperlinks to external sources.
- One or more output formats is required: `.docx` (primary), `.pdf` (via conversion from `.docx`), or `.md` (lightweight variant).

**Trigger phrases**: "compile these reports", "merge this research", "combine these documents with references", "consolidate my deep research output", "build a unified report from these sources", "compile deep research", "merge my literature review", "merge into a Word doc matching this template".

## Core Principle

Detailed guidance lives in [core-principle.md](references/core-principle.md) (load on demand).

## Upstream: gathering sources as a Dynamic Workflow (optional)

The steps below assume the user already has the research sources. When the user instead arrives with a *question* and no sources, the gathering is the upstream `/research deep` shape: fan-out searches -> fetch sources -> adversarially verify claims -> synthesize. When the harness has the Dynamic Workflows runtime, [scripts/research-fanout-workflow.js](scripts/research-fanout-workflow.js) is a ready-to-adapt scaffold for exactly that phase (a multi-modal search sweep, a per-source fetch pipeline, per-claim refutation, then a cited synthesis whose canonical `[N]` list feeds the renumbering in Step 4).

This does not violate the "you are the generator; there is no persistent script" core principle: that rule governs document *emission* (the throwaway python-docx generator). This file emits no document -- it is an orchestration harness for *source gathering* that hands its synthesized, citation-ready output to Step 3 onward.

It is a **template to adapt, not a script to run verbatim**, and it must **degrade gracefully**: Dynamic Workflows is a plan-gated research-preview capability that may be absent, so fall back to a few isolated subagents (one per search angle) or a single sequential search-read-synthesize pass. Because the fan-out carries a 5-15x token multiplier, keep the **scope-first** discipline: calibrate on one search angle first, review the candidate source list on the first trigger, and confirm before fanning out across every angle. The subagents use only the harness's built-in `WebSearch` / `WebFetch` tools -- no new dependency or credential. For whether a fan-out is warranted at all and the hard budget controls, see [[agent-orchestration-primitives]] and [[ai-billing-safeguards]].

---

## Step 1: Inspect the .docx Template

Detailed guidance lives in [step-1-inspect-the-docx-template.md](references/step-1-inspect-the-docx-template.md) (load on demand).

## Step 2: Ingest Input Documents

Detailed guidance lives in [step-2-ingest-input-documents.md](references/step-2-ingest-input-documents.md) (load on demand).

## Step 3: Synthesize Unified Content

Detailed guidance lives in [step-3-synthesize-unified-content.md](references/step-3-synthesize-unified-content.md) (load on demand).

### Worked example: marking quotation

The failure this guards against is reproducing a source's sentences without marking them. The fix is an example, not a rule.

**Request**: "Compile what the three field reports say about soil moisture and the pump schedule."

**Ingested sources** (the Step 2 manifest, templated): `[1]` Northfield Irrigation Review, `[2]` Delta Basin Field Notes, `[3]` Hillcrest Pump Log.

**Response** (the compiled paragraph, in this skill's inline `[N]` style):

> The three reports agree that the pump schedule, not the sensor network, drove the moisture swings [1][2][3]. The Northfield review and the Delta Basin notes both attribute the mid-season dry spell to a schedule that ran on calendar days rather than on readings [1][2]; the Hillcrest log differs on the remedy, recording that the crew switched to reading-triggered runs in week six and saw the swings flatten within two cycles [3]. On cost the sources part ways: Northfield calls the reading-triggered schedule "the only change that paid for itself in one season" [1], while Delta Basin reports higher pump wear and no net saving [2].

**Rationale**: the paragraph is organized around where the sources agree and differ rather than walking through each source in turn; each source is conveyed in one or two sentences of the agent's own indirect speech; exactly one short phrase is marked as a quotation and attributed to one source; every other claim is reworded while staying specific (week six, two cycles, one season) and complete. Zero marked phrases is also a valid outcome when no sentence is worth quoting.

## Step 4: Reference Management

Detailed guidance lives in [step-4-reference-management.md](references/step-4-reference-management.md) (load on demand).

## Step 5: Write the Python-Docx Generation Program

Detailed guidance lives in [step-5-write-the-python-docx-generation-program.md](references/step-5-write-the-python-docx-generation-program.md) (load on demand).

## Step 6: Markdown Output

Detailed guidance lives in [step-6-markdown-output.md](references/step-6-markdown-output.md) (load on demand).

## Step 7: PDF Output

Detailed guidance lives in [step-7-pdf-output.md](references/step-7-pdf-output.md) (load on demand).

## Step 8: Validate + Iterate

Detailed guidance lives in [step-8-validate-iterate.md](references/step-8-validate-iterate.md) (load on demand).

## Common OOXML Pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Word dialog: "Word found unreadable content" | Empty `<w:t>` tags, bad `<w:rPr>` child ordering, missing xml:space="preserve" | Ensure every run's `<w:t>` has text (even if ""); emit `<w:rPr>` children in canonical order (rStyle -> b -> i -> smallCaps -> rFonts -> sz -> szCs -> color -> u -> vertAlign); add `xml:space="preserve"` to every `<w:t>` |
| Headings render as Normal; TOC empty | `paragraph.style = doc.styles["Heading 1"]` silent fail | Always use the `apply_style()` helper that writes `<w:pStyle>` directly via `OxmlElement` |
| Word dialog: "Start by applying a heading style" when refreshing TOC | No paragraphs carry heading styles | Same fix as above |
| Citation hyperlinks don't navigate | Anchor name doesn't match bookmark name | Ensure bookmark is exactly `_RefN` and anchor is exactly `_RefN`; validate post-generation |
| Citation anchors valid but not clickable | Citation emitted as plain text run, not hyperlink | Use the 3-run pattern in Section K |
| References section URLs are blue text but not clickable | External hyperlink created without `RT.HYPERLINK` rel | Always use `paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)` |
| Metadata table keeps the source-template look when applied to a different target template | Hardcoded `#BFBFBF` instead of profile value | Pull border colors from `profile["metadata_table"]` |
| Title page text is the wrong font/size/color | Style profile not used; hardcoded Consolas/Calibri/32pt | Every run-level property must come from `profile[<style_name>]` |
| Page 1 shows the header/footer that should only appear page 2+ | sectPr's `<w:titlePg/>` was dropped during body clearing | `clear_body` must preserve the final `<w:sectPr>` byte-for-byte |
| Duplicate bookmark IDs (Word opens but TOC is broken) | Bookmark ID counter collides with Word's auto-generated IDs | Use IDs >= 1000 for your own bookmarks; never reuse IDs |

---

## Critical Rules

- **Never fabricate citations.** A sentence that had no citation in the source material gets no citation in the merged document.
- **Never silently drop references.** Every canonical reference appears in the final References section even if its inline citation count is zero (it might have been cut during editing -- preserve it for the user to decide).
- **Never hardcode output format.** The command always asks.
- **Always ask for the template.** Silently defaulting is the v1 bug; the command's Phase 2 must be honored.
- **Always validate after generation.** Broken citations and empty TOCs are the common failure modes; catch them before handing off.
- **Every style value comes from the profile.** No hardcoded fonts, colors, or sizes in the generator. When a new template is supplied, the output must visually match it -- never the previous template.
- **Save the generator script.** `<cache_dir>/generate.py` is kept so the user can re-run or tweak it without invoking the command.
- **Separate final outputs from intermediates.** Final outputs live in `<final_dir>` (`docs/compiled/`). Intermediate artifacts live in `<cache_dir>` (`.cache/compile-deep-research/<ReportTitle>/`). Never put intermediates in `docs/`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add a citation here to make the claim look sourced" | A fabricated citation is worse than none: it points a reader to a source that does not support the claim, destroying the document's credibility. A sentence with no citation in the source material gets none in the merge. |
| "These two references look like the same paper, I'll keep both" | Near-duplicate references with slightly different titles inflate the reference count and break renumbering. Dedup by DOI, normalized URL, and fuzzy title before assigning the canonical [N]. |
| "I'll hardcode the fonts to match the last template, it's faster" | Hardcoded fonts and colors are the documented v1 bug: the output then matches the previous template, not the one the user just supplied. Every style value must read from the template's style profile. |
| "The document opens in Word, so the citations and TOC are fine" | Word opens documents with broken citation anchors and empty TOCs without complaint. Only a post-generation validation pass catches the unresolved [N] links and the missing references. |

## Verification

- [ ] The final document is written to `docs/compiled/` and intermediates stay in `.cache/compile-deep-research/<ReportTitle>/`
- [ ] Every inline [N] citation resolves to an entry in the References section
- [ ] Every canonical reference appears in References (even if its inline count is zero)
- [ ] No citation exists in the merged document that was absent from the source material
- [ ] The output's fonts, colors, and sizes are read from the template style profile, not hardcoded
- [ ] The generator script is saved at `<cache_dir>/generate.py` for re-run
- [ ] The output format (.docx / .pdf / .md) matches what the user explicitly chose

## Related Skills

- [[docx-generation]] -- the python-docx fundamentals the per-run generator script is built on
- [[pdf-document-generation]] -- the PDF export path when the user chooses .pdf output
- [[technical-writer]] -- content synthesis and information architecture for the merged narrative
- `/research deep` -- upstream multi-source research that produces the reports this skill compiles
- [[trend-research]] -- source gathering across web, Reddit, and X that feeds the compilation
