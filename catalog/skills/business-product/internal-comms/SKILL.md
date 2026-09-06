---
name: internal-comms
description: "Draft structured internal communications using six named templates - 3P Update (Progress / Plans / Problems), Weekly Status Report, Leadership Update, Company FAQ entry, Incident Report, Project Update. Use whenever the user asks to write a status update, weekly summary, leadership briefing, exec brief, FAQ, post-mortem, incident write-up, project update, one-pager, or any internal-audience message that needs structure to land. The skill always picks the right template before drafting and resists the urge to free-form. SKIP: external-audience marketing copy (use writing-editing), long-form decision docs / RFCs / ADRs (use doc-coauthoring), single-paragraph Slack messages, or commit messages."
summary_l0: "Draft internal comms using six structured templates (3P, status, leadership, FAQ, incident, project)"
overview_l1: "This skill provides six named templates for structured internal communications - 3P Update (Progress / Plans / Problems), Weekly Status Report, Leadership Update (executive briefing format), Company FAQ entry, Incident Report (timeline + root cause + remediation), and Project Update (one-pager). Each template specifies when to use it, the exact section headers, expected length, and 3-5 common pitfalls. Worked examples use placeholder organizations (Project Aurora, Team Phoenix) so the patterns are reusable across companies. The skill picks the template before the prose so structure carries the message and the writer focuses on content. Trigger phrases: 3P update, weekly status, status report, leadership update, exec brief, executive summary, internal FAQ, company FAQ, incident report, post-mortem, project update, one-pager, internal memo, weekly digest, project status."
---

# Internal Communications

Six structured templates for internal-audience writing. Each template fixes the section structure so the writer stops re-deciding shape and starts producing content. Templates are scaffolding, not boilerplate - they make the doc easier to write AND easier to read at the same time, because readers learn the format once and skim every future instance in seconds.

## When to Use This Skill

Use this skill when:

- The user wants to write a status update, weekly digest, or progress report
- A leadership / exec audience needs a briefing in a fixed format
- An internal FAQ entry must match the rest of the FAQ in shape
- An incident requires a structured post-mortem with timeline + cause + remediation
- A project needs a one-page update for a stakeholder review
- The user has written a free-form draft and wants it restructured into the right template

**Trigger phrases**: "3P update", "weekly status", "status report", "leadership update", "exec brief", "executive summary", "company FAQ", "internal FAQ", "incident report", "post-mortem", "incident write-up", "project update", "one-pager", "internal memo", "weekly digest", "project status".

**When NOT to use**:

- External marketing copy, blog posts, press releases (use `developer-experience/writing-editing` for the prose, `business-product/technical-writer` for technical-public docs)
- Long-form decision docs, RFCs, ADRs, design docs (use `workflow/doc-coauthoring` for the 3-stage co-authoring workflow)
- Single-paragraph Slack messages, one-line announcements, or quick replies in a thread (templates are overkill at that length)
- Commit messages, PR descriptions, code review notes (use `workflow/code-commit-workflow`)
- Open-ended brainstorming or strategy memos where the shape is the point of the writing (use `workflow/doc-coauthoring`)

If the format is supposed to vary, this skill is the wrong shape. Templates earn their keep when the same audience reads the same shape of message regularly.

## The Six Templates

### 1. 3P Update (Progress / Plans / Problems)

**When to use**: A weekly or fortnightly individual or team update where the audience needs to know what shipped, what is next, and what is blocked.

**Structure**:

```
## Progress
- [What shipped or moved forward this period; 3-6 bullets, concrete artifacts]

## Plans
- [What is targeted next period; 3-6 bullets, concrete deliverables]

## Problems
- [What is blocked, slipped, or needs help; 0-4 bullets, with the ask if any]
```

**Expected length**: 150-300 words. Bullets, not paragraphs.

**Common pitfalls**:

- Padding Progress with activity that did not produce an artifact ("met with X" is activity, not progress; "agreed plan with X" is progress).
- Listing every Plan instead of the next-period commitments. If everything is in Plans, nothing is.
- Hiding Problems under euphemism ("some interesting questions emerged"). If it is blocked, write "blocked", say what you need, who can unblock you.
- Omitting Problems entirely when there are none, instead of writing "Problems: none this period." The empty section is information.
- Mixing past, present, and future tense across bullets. Progress is past, Plans is future, Problems is present.

**Example**: see `examples/3p.md`.

---

### 2. Weekly Status Report

**When to use**: A team-level weekly broadcast to a wider audience (cross-team or department) where the reader is skimming for what their dependency just did.

**Structure**:

```
# <Team Name> - Weekly Status, week of <YYYY-MM-DD>

## TL;DR
<One sentence: what the team did this week and what changes for readers.>

## Shipped
- [Artifact + link, 3-6 bullets]

## In Flight
- [Active work + ETA, 3-6 bullets]

## Risks and Asks
- [Any risk or ask the wider audience can act on, 0-4 bullets]

## Metrics (optional)
| Metric | Last week | This week | Trend |
|---|---|---|---|
| <name> | <value> | <value> | up/down/flat |
```

**Expected length**: 250-450 words. Skimmable on a phone.

**Common pitfalls**:

- Burying the lede - skipping or weakening the TL;DR so the reader has to reconstruct what changed for them.
- Linking to internal-only docs without summarizing the relevant point inline; readers two teams away cannot click every link.
- "In Flight" stretching to 15 items because cutting feels political. The cap is 6; below-6 is honest, above-6 is performative.
- Metric tables that change shape every week so the trend column is meaningless. Pick three metrics and stick with them for a quarter.
- Posting on a different day each week. The day matters; pick one and stick with it.

**Example**: see `examples/status.md`.

---

### 3. Leadership Update (Executive Briefing)

**When to use**: A short briefing to a leadership audience (director / VP / exec) where the reader has 90 seconds and decides whether to dig deeper.

**Structure**:

```
# <Topic> - Leadership Update, <YYYY-MM-DD>

## Decision or Recommendation
<One sentence stating what you want the reader to do (approve, decline, choose between options, take no action).>

## Context (60 seconds)
<3-5 bullets: what the situation is, why it matters now, what the reader needs to know.>

## Options
1. <Option name> - <one sentence consequence>
2. <Option name> - <one sentence consequence>
3. (optional) <Option name> - <one sentence consequence>

## Recommendation
<One paragraph: which option, why, what tradeoff is accepted.>

## Risks
- [Top 2-3 risks, each with mitigation]

## Appendix (optional)
<Links, source data, deeper analysis.>
```

**Expected length**: 300-500 words. Recommendation visible above the fold.

**Common pitfalls**:

- Leading with context instead of the decision. Executive readers decide whether to keep reading after the first sentence.
- Three options where two of them are obviously bad. The decoy options waste the reader's time and make the recommendation feel pre-cooked.
- Risk section that lists everything that could go wrong, with no relative weighting. Top 2-3, with mitigations, beats top 12.
- Appendix that is the actual document; main body should stand alone without it.
- Mixing "recommendation" and "request" - say which one. If you want a decision, say "I am asking for approval"; if you want input, say "I want feedback before deciding".

**Example**: see `examples/leadership.md`.

---

### 4. Company FAQ entry

**When to use**: A single Q&A in a wider FAQ collection (HR, IT, security, product). The audience reads many of these and needs them to feel uniform.

**Structure**:

```
### <Question phrased exactly as users would ask it>

**Short answer**: <one sentence, direct.>

**Details**:

<2-4 sentences expanding the short answer. Concrete: who, what, when, how.>

**Related**:
- [Other FAQ entries or canonical docs]

**Last reviewed**: YYYY-MM-DD by <owner role>
```

**Expected length**: 80-180 words per entry. Skimmable on a phone.

**Common pitfalls**:

- Writing the question as the writer would phrase it ("How does the company's onboarding workflow function?") instead of as users actually ask it ("Who do I talk to on day one?"). Use the user's words verbatim, even if they're not technically precise.
- Putting the answer behind context. Short answer FIRST, then details.
- Linking to a 30-page policy doc instead of giving the answer. The point of an FAQ is to short-circuit the policy doc for the 5 most common cases.
- "Last reviewed" missing or stale. An FAQ entry without an owner and a date rots silently.
- Marketing voice ("we're committed to your success") in an internal FAQ. Read what you wrote; if it sounds like a recruiting page, rewrite.

**Example**: see `examples/faq.md`.

---

### 5. Incident Report (Post-mortem)

**When to use**: After a production incident, an outage, a data quality issue, or any event with measurable user-facing impact. Audience: the team plus anyone who needs to know it will not happen again.

**Structure**:

```
# Incident <YYYY-MM-DD-####> - <one-line headline>

## Summary
<One paragraph: what happened, when, who was affected, how long, current state.>

## Impact
- Users affected: <count or scope>
- Duration: <start - end UTC>
- Severity: <SEV1 / SEV2 / SEV3>
- Detection: <how we found out, time-to-detect>

## Timeline (UTC)
| Time | Event |
|---|---|
| HH:MM | <observation or action> |
| HH:MM | <observation or action> |

## Root Cause
<2-4 paragraphs: what actually caused it. Single root cause if possible; otherwise contributing factors with weights.>

## What Went Well
- [2-4 bullets: detection, response, communication that worked]

## What Went Wrong
- [2-4 bullets: gaps, slow signals, missing playbook]

## Action Items
| Item | Owner | Due | Type (prevent / detect / respond) |
|---|---|---|---|
| <action> | <name> | <date> | prevent |
```

**Expected length**: 600-1200 words. The timeline and action items are the contracts.

**Common pitfalls**:

- Blaming individuals. Root cause is systemic; if a person made a mistake, the system that allowed the mistake is the cause.
- Vague timeline ("around 2pm"). Use UTC, with HH:MM precision; if the data is fuzzy, write "approx HH:MM" - the precision claim itself matters.
- Action items without owners. An action item without a name is a wish. Owner + date + type, every row.
- Skipping "What Went Well" because it feels self-congratulatory. Without it, the next incident response loses the patterns that worked.
- Overloading the action items list. 5-8 is the right scale; 30 means none of them get done.

**Example**: see `examples/incident.md`.

---

### 6. Project Update (One-Pager)

**When to use**: A periodic update on a multi-month project for a stakeholder audience (sponsor, steering committee, partner team). One page, fixed format, every period.

**Structure**:

```
# <Project Name> - Update, <YYYY-MM-DD>

## Status: <On track / At risk / Off track>

## Current Phase
<One sentence: what phase we're in, what the phase produces.>

## Progress This Period
- [3-5 bullets: shipped artifacts]

## Next Period
- [3-5 bullets: planned artifacts, with ETAs]

## Risks and Mitigations
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| <risk> | low/med/high | low/med/high | <action> |

## Asks
- [0-3 bullets: what the stakeholder can do]

## Metrics (optional)
| Metric | Target | Current | Trend |
|---|---|---|---|
| <name> | <value> | <value> | up/down/flat |
```

**Expected length**: One page. Aim for 350-550 words.

**Common pitfalls**:

- Status field that is always "On track" until suddenly it is "Off track". Use "At risk" honestly; the status field is the single most important word in the doc.
- Missing the "Asks" section, then complaining the stakeholder is not helping. If you do not ask, the answer is no by default.
- Risk table with everything as low / low. If everything is low / low, the risk register is performative; rewrite.
- Metrics that show only the current value with no target. The reader cannot evaluate "good" without "what would good look like".
- Update written by someone who was not in the work this period. The voice goes hollow; the reader hears it.

**Example**: see `examples/project.md`.

---

## Instructions

1. **Pick the template before drafting prose**. If the user does not name one, ask: "Which of the six? (3P, status, leadership, FAQ, incident, project)" - or infer from context. Do not start drafting until the template is fixed.
2. **Honor the structure exactly**. Every section header in the template is required, even if a section is "none this period". Empty sections are information.
3. **Match the expected length**. If the user-supplied content overflows, push back: ask what to cut, do not silently expand the template.
4. **Use placeholder organizations**. Worked examples in this skill use Project Aurora, Team Phoenix, Apex Logistics, etc. Do not model examples on real companies, real products, or specific employers.
5. **Keep tense consistent**. Past for what shipped; future for what is next; present for what is blocked. Do not mix.
6. **Format for skim**. Bullets over paragraphs; tables over prose for parallel data; bold for the one word the reader must not miss; one TL;DR at the top of any doc longer than 200 words.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just write it freeform - templates are bureaucratic" | Freeform updates lose readers. Templates are scaffolding that lets the writer focus on content because the shape is already decided. The reader's skim cost drops by 5-10x once the format stabilizes; that compounds across every reader, every week. |
| "My team's update doesn't fit any of the six templates" | The six cover 95% of internal-audience writing. If a draft genuinely doesn't fit, it is probably long-form (use `workflow/doc-coauthoring`) or a one-line message (no template needed). The two unmatched cases push to the right neighbors, not to a custom seventh template. |
| "I'll skip the TL;DR / Status / Recommendation line - the reader can find it" | The reader at the top of the inbox at 7am cannot find it. The single visible line is what determines whether the doc gets read. Skip it and the doc is invisible. |
| "I'll list every risk so I can't be accused of hiding any" | A risk register with 30 entries is functionally identical to no register at all - the reader cannot prioritize. Top 2-3 with mitigations is the contract; the rest go in the appendix or the followup tracker. |
| "Action items in incident reports don't need owners - the team will sort it out" | Action items without owners do not happen. Owner + date + type, every row, no exceptions. If you do not know the owner, write the role; replace with a name within 48 hours. |
| "Examples in the templates feel artificial - I'll skip them and just describe the structure" | Without a worked example, the writer guesses at the shape and the next instance drifts. The bundled `examples/` files are the contract; reference one when in doubt. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] One of the six template names is explicitly named in the draft (in the title, the URL slug, or a top-of-doc comment) so the reader knows which contract applies.
- [ ] Every section header from the template appears in the draft (empty sections explicitly say "none this period" or equivalent).
- [ ] The single most important line (TL;DR / Status / Recommendation) is visible in the first 60 words.
- [ ] Tense is consistent within sections (Progress / Shipped is past; Plans / Next Period is future; Problems / In Flight is present).
- [ ] No real-company names, product names, or stakeholder names appear in template content; placeholder organizations only.
- [ ] Word count falls within the template's stated range (within 20% tolerance); overflow has been explicitly trimmed, not silently expanded.
- [ ] Action items (in incident / project / status) have owner + due date + type, every row.

"The update reads well" is not a valid verification criterion. The verification is: does the draft match the template structure, are the empty sections explicit, and does the visible line carry the message?

## Bundled Resources

Six worked examples ship under `examples/`. Each is a complete instance of one template, using placeholder organizations (Project Aurora, Team Phoenix, Apex Logistics) so the patterns are reusable. Reference the matching example when drafting.

- `examples/3p.md` - 3P Update for an individual contributor on Project Aurora.
- `examples/status.md` - Weekly Status Report from Team Phoenix.
- `examples/leadership.md` - Leadership Update recommending a vendor decision for Apex Logistics.
- `examples/faq.md` - Three Company FAQ entries (HR, IT, security).
- `examples/incident.md` - Incident Report for a SEV2 production outage at Apex Logistics.
- `examples/project.md` - One-pager Project Update for Project Aurora at end of phase 2.

The examples are deliberately generic; do not adapt them to a specific real organization in a way that overwrites the placeholder names.

## Related Skills

- [[writing-editing]] -- sentence-level polish on the draft this skill produces; use as a follow-up step.
- [[technical-writer]] -- audience-appropriate technical documentation; complements when the comm has substantial technical content (an incident on a complex system, a project update with architecture detail).
- [[doc-coauthoring]] -- 3-stage co-authoring workflow for long-form decision docs / specs / RFCs that don't fit any of the six templates.
- [[technical-documentation]] -- architecture docs, ADRs, design specs; use instead of the project-update one-pager when the artifact needs to be referenced after the period ends.
- [[idea-refine]] -- upstream pre-template step when the writer is not yet sure what they want to say.
