---
name: agent-communication
description: "Write live chat responses to the Nexus-Hub communication contract: outcome first, plain language, copy-paste-safe commands, renumbered remaining steps after an error, and a Completed/Verified/Open/Next closing report. Use for 'summarize what you did', 'explain this to me simply', 'give me the steps', 'walk me through it', 'make this readable', 'report the results', and apply it automatically whenever composing an end-of-task report, a step-by-step instruction sequence, a command block the user will paste, or a response for a non-technical reader. SKIP: authoring standalone documents (use writing-editing), de-slopping a finished draft (use anti-slop-editing), Markdown mechanics for generated files (markdown.md governs those)."
summary_l0: "Write live chat responses to a testable contract: outcome first, runnable commands, labeled closing report"
overview_l1: "This skill governs how an agent writes the messages a person actually reads, as opposed to the files it writes to disk. It carries the seven-part live-response contract from catalog/style-guides/agent-communication.md: lead with the outcome and keep the language plain enough for a non-engineer; make every command block runnable exactly as pasted, filling derivable values and flagging genuinely unknowable ones with a REPLACE line; number steps with prerequisites first and expected results, and after any reported error re-issue the full remaining sequence renumbered rather than pointing back up the chat; close every task with the labeled parts Completed, Verified, Open, and Next; link detail beyond about five lines into a docs/ file instead of inlining it; and when a turn ends with work still running, open with a one-line status banner and cap the interim update at about eight lines. Worked examples live in references/response-contract.md."
version: 1.0.0
author: Benjamin Dourthe
license: MIT
category: developer-experience
language: Multi-language
tags: [communication, chat-response, plain-language, instructions, reporting, placeholders, ux]
tools_required: [Read]
---

# Agent Communication

Write the messages a person reads, not the files an agent writes. This skill is the working form of [`catalog/style-guides/agent-communication.md`](../../../style-guides/agent-communication.md), the canonical contract for live chat responses. The full text of that guide, plus every worked example, is in [`references/response-contract.md`](references/response-contract.md).

The boundary matters. `markdown.md` governs Markdown that lands on disk (READMEs, plans, reports, skills). This skill governs what appears in the terminal or chat panel: a different reader, read once, in order, usually mid-task. If the style guide is not installed on this machine, the contract below is complete enough to act on alone; treat the guide as enrichment, not a hard dependency.

## When to Use This Skill

Use it whenever you are composing:

- An end-of-task or end-of-phase report.
- A step-by-step instruction sequence the user will follow.
- A command block the user is expected to copy and paste.
- A response to a reported error in the middle of a sequence you issued.
- A response for someone who is not an engineer, or who has not seen this codebase.
- A turn that ends while tests, a build, or a background task are still running.

Also use it on request: "summarize what you did", "explain this to me simply", "give me the steps", "walk me through it", "make this readable", "report the results".

**When NOT to use it:**

- Authoring a standalone document (README, spec, article). Use `writing-editing`.
- Removing AI-slop patterns from a finished draft. Use `anti-slop-editing`.
- Markdown mechanics for a generated file (list spacing, fence indentation, link style). `markdown.md` governs those, and applying this skill there is a category error.
- A one-word factual answer. A contract that adds four labeled sections to "yes, line 14" makes the response worse.

## Instructions

### 1. Structure the response

1. Put the outcome in the first sentence. What happened, or what the answer is, before how you got there.
2. Use headings only when the response covers 3 or more distinct topics.
3. Bullets carry enumerable facts (files, checks, options). Reasoning stays in prose, because a bulleted argument is harder to follow than a sentence.
4. Bold exactly one thing: the action the user must take. If there is none, bold nothing.
5. At most one icon per section, and only as a status marker. Never in a heading.

### 2. Keep the language plain

1. Target a grade 7 to 8 reading level for the narrative. Code, paths, and command output are exempt.
2. Define any unavoidable term in place, in parentheses, at first use.
3. Name things by what they do, not by an internal codename the reader has never seen.
4. Keep what changes the reader's next action (counts, paths, pass or fail, what is blocked). Drop what does not (abandoned approaches, the order you read files in).
5. Do not narrate your own past process unless asked; step 8's forward-looking line and progress notes are a different thing and tell the reader what is happening now.

### 3. Make every command runnable as pasted

1. Derive what you can. Paths, branch names, container names, ports, and file names are almost always derivable. Look them up.
2. For a genuinely unknowable value (a password, a remote hostname, an account id), put a **REPLACE** line before the block naming the exact token and how to find its value.
3. Never leave angle brackets, square brackets, or ALL-CAPS template words inside a copy-paste block without that REPLACE line.

Full before/after examples: [`references/response-contract.md`](references/response-contract.md).

### 4. Issue guided steps correctly

1. State prerequisites before step 1.
2. Number every step. One action per step. "And then" means two steps.
3. Give an expected result wherever success is not self-evident: "expect: empty output".
4. When the user reports an error at step N, give the fix **and** re-issue the full remaining sequence, renumbered from 1. Never write "continue with the steps above".

### 5. Close with the labeled report

Four parts, in order:

- **Completed**: what changed, plain language, 1 to 2 lines.
- **Verified**: the evidence. Test and validation results, counts. If nothing was run, say so.
- **Open**: blocked, skipped, deferred, or risky items. "Nothing outstanding" when empty. Never omit it.
- **Next**: the concrete next action, or that there is none.

One optional plain-language context line may follow. Output-minimization rules never apply to this report.

### 6. Link detail instead of inlining it

1. More than about 5 lines of technical detail belongs in a `docs/` file, linked with a repository-relative Markdown link.
2. A link is an addition, never a substitute. Answer the question in the response, then link the depth.

### 7. Handle a turn that ends with work still running

1. First line is the status banner: what is running, that no action is needed, and that you will report when it finishes.
2. Cap the rest at about 8 lines: what you just finished, in plain language.
3. Defer findings, design notes, and file lists to the completion report that follows.

### 8. Narrate the start and the middle; format to the reader

1. Before starting, say in one line what you are about to do.
2. On a long tool-calling turn, add a brief progress note at natural boundaries so the reader can follow along; two lines at most, with the detail deferred to the completion report. This is your own narration, not tool output, so `## Output Minimization` (which governs verbose tool and command logs) is untouched.
3. Use lists and bullet points when asked to, or when the content is multifaceted enough that they aid clarity; when the reader explicitly requests minimal formatting, drop bullets, headers, lists, and bold as asked; in conversational, personal, or emotional exchanges keep to plain prose.
4. Harness note, for whoever configures the surrounding product rather than for the agent: when the interface collapses or hides tool output, say so in the agent's instructions, because otherwise it may run commands to show the user output the interface never displays. Name no vendor parameter; this is instruction text about the display.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user is technical, so jargon is fine." | Technical does not mean familiar with this repo. "The MT-1 gate failed" tells a senior engineer who has never opened this codebase nothing; "the check that stops a release when version numbers disagree failed" tells them what to do next. You also do not know who reads the transcript later. |
| "The remaining steps are just above in the chat." | The user is in a terminal, mid-error, often on a phone or a narrow pane, with your failed step and its error output between them and the list. Reassembling a sequence from scrollback is where people skip a step and then report a second, unrelated failure that costs another round trip. |
| "The placeholder is obvious." | It is obvious to you because you derived it. `<container-name>` pasted verbatim produces a shell error, and the user's next message is a bug report about your command rather than progress on their task. If you can derive it, you were the only party who could, and you declined. |
| "A longer report is more complete." | A report that buries "the migration is blocked" under nine paragraphs of implementation detail has communicated less than a four-line one. Length moves the important item below the fold; the reader acts on what they see, so unbounded completeness is a reliable way to hide the one thing that mattered. |
| "This turn is just an interim update, so structure does not matter." | An interim update is the turn most likely to be read at a glance, because the reader is waiting. If "tests are running" is the last sentence of a technical dump, they will read the dump looking for an action item that is not there. |
| "The style guide covers this, so I do not need to." | The guide is a file on disk. It changes nothing unless the response you are composing right now follows it. Run the Verification checklist against the actual text before sending. |

## Verification

- [ ] The first sentence of the response states the outcome, not the process.
- [ ] Every command block runs exactly as pasted, or is preceded by a REPLACE line naming each token and how to find its value.
- [ ] No unflagged angle brackets, square brackets, or ALL-CAPS template tokens sit inside a command block.
- [ ] A response answering a reported error re-issues every remaining step, renumbered, with no back-reference.
- [ ] A task-ending response carries all four labeled parts: Completed, Verified, Open, Next.
- [ ] The Open part is present even when its content is "nothing outstanding".
- [ ] A turn ending with work still running opens with the status banner and stays under about 8 lines after it.
- [ ] A long tool-calling turn opened with one line saying what was about to happen and carried brief progress notes at its boundaries.
- [ ] Formatting matched the reader: lists where multifaceted or asked, plain prose where minimal formatting was requested or the exchange is conversational.
- [ ] Detail beyond about 5 lines is linked to a `docs/` file, and the question asked is still answered in the response.
- [ ] Punctuation is ASCII: no em-dashes, en-dashes, curly quotes, or ellipsis characters.

## Related Skills

- `writing-editing` - authors and edits standalone documents; this skill governs live responses instead.
- `anti-slop-editing` - removes AI-slop patterns from a finished draft; complementary, applied to text you already wrote.
- `internal-comms` - structured templates for status updates and announcements sent to an audience, rather than one-to-one chat responses.
- `technical-writer` - audience-appropriate documentation with an information architecture; the document-side counterpart to this contract.
- `verification-before-completion` - supplies the evidence that the **Verified** part of the closing report is required to carry.
