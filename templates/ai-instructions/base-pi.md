# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## Tech Stack

- **Language**: {{PRIMARY_LANGUAGE}} {{LANGUAGE_VERSION}}
- **Package Manager**: {{PACKAGE_MANAGER}}
- **Build**: {{BUILD_TOOL}}
- **Test**: {{TEST_FRAMEWORK}}
- **Lint/Format**: {{LINT_TOOL}}

## Project Layout

{{PROJECT_STRUCTURE_BRIEF}}

## Key Commands

```bash
{{BUILD_CMD}}
{{TEST_CMD}}
{{LINT_CMD}}
```

## Non-Obvious Tooling

{{NON_OBVIOUS_TOOLING}}

## {{PRIMARY_LANGUAGE}} Conventions

{{LANGUAGE_CONVENTIONS}}

## Working Conventions

- Verify solutions work before claiming completion
- Find root causes; no temporary fixes
- **MANDATORY**: When invoking a shell-style tool (Bash, PowerShell, `run_shell_command`, `shell`, etc.), provide the `description` parameter as a single plain-text sentence (<=120 chars, no newlines, no formatting, no `#` characters or borders). Prefer single-line commands; use multi-line bodies only when a here-string or heredoc is genuinely required (e.g. commit messages, file content). The `description` field is the universally-rendered surface across all approval-dialog implementations - keep it precise and scannable.
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- Commit messages must be ASCII-only: no em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
- Use `docs/todos.md` as the project progress tracker: read it at session start if it exists, check off completed tasks, add newly identified work, and update dashboard metrics after relevant milestones. Use the dev-progress-tracker skill to create or maintain it.
- If requirements are ambiguous, batch all clarifying questions into the first turn rather than asking one question per turn. Surface multiple interpretations and acceptance criteria together so the user can answer them in a single round-trip. State any assumptions explicitly before acting. Avoid unbounded per-question ping-pong.
- Every changed line must trace directly to the user's request; do not clean up adjacent code, pre-existing dead code, or style issues outside the stated scope
- Place punctuation outside quotation marks; no em-dashes
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Communication Contract

- Outcome first, in language a non-engineer follows; define jargon in place; put detail beyond ~5 lines in a linked docs/ file.
- Commands must run as pasted: fill derivable values, flag the rest with a REPLACE line and where to find it.
- Number steps, prerequisites first, expected results. After an error, re-issue ALL remaining steps renumbered.
- Close tasks with Completed / Verified / Open / Next.
- Work still running at turn end: lead with a one-line status banner, cap the update at ~8 lines.
- Say in one line what you are about to do; on a long tool-calling turn, add brief progress notes. This narration is not tool output, so Output Minimization still applies.
- Use lists when asked or when content is multifaceted; drop bullets, headers, and bold when the reader wants minimal formatting; keep conversational or emotional exchanges in plain prose.

Full contract: `~/.nexus-hub/style-guides/agent-communication.md`.

## Writing Discipline


Do not produce the high-frequency AI-cliche moves: throat-clearing openers; "not just X, but Y" and "it is not X, it is Y" contrasts; importance puffery ("crucial", "it is important to note"); weasel attribution ("experts say", "studies show"); faux-insight setups ("here is the thing"); trailing "-ing" clauses that restate a sentence as analysis; fake-profound closing lines; summary-recap endings; and mannered prose, where metaphor or flourish stands in for a direct statement.

Punctuation is ASCII only: no em-dashes, no clause-joining spaced hyphens, punctuation placed outside quotation marks by logic, and no hard-wrapping of paragraph text. Keep a professional teaching tone.

Chatbot leftovers are defects, not style: never emit "as an AI language model", "here is the revised version", or "I hope this helps".

Self-check: before returning any response or writing any file, scan your own output against this list and fix what you find. This binds live chat replies, not only generated documents.

Full catalog and the Edit / Detect modes: `anti-slop-editing`.

## Documentation Layout


Use lifespan as the single placement axis for project documentation.

- Active release work: `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`.
- Closed release work: `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/`.
- Living product documentation: stable purpose-based roots such as `docs/handbooks/`, `docs/guides/`, `docs/reference/`, `docs/standards/`, `docs/runbooks/`, and `docs/decisions/`.

Admission test: "Will this document still change after this release closes?" If yes, use a living root. If no, use the matching active release tree.

Use the `docs-layout-refactor` skill for classification, migration, and link-integrity procedures.

## Branching


- Follow the project's declared branching strategy. Do not commit feature or version work directly to the protected (release) branch -- branch off the integration branch and integrate through it. If the strategy is unstated, infer it (a `develop` branch implies a develop+main model; otherwise assume GitHub Flow) and confirm before branching. See the `git-branching-workflow` skill for the per-model discipline.

## Plan Lifecycle and CI/CD


- Every plan phase verifies locally and ends with ONE local commit.
- No non-final phase pushes or starts remote CI: a run per phase bills to validate work the plan itself calls incomplete.
- A phase records its CI impact; it edits pipeline files only when CI/CD is that phase's stated deliverable.
- The final phase reconciles the pipeline against the canonical contract, then publishes once. That pull request is the plan's first remote validation and tests the merge result.
- Post-merge work stays minimal; release starts only after the integration result is green and merged.

Skill: `cicd-architect`.

## Consequential Decisions

Before asking the user to approve or choose anything consequential, give a short plain-language walkthrough. This rule applies when the choice changes security posture, deletes or overwrites data, changes distributed or user-facing behavior, or expands the agreed scope. It does not apply to routine clarification, formatting preferences, or a choice with an obvious default.

The walkthrough must explain what the current work is doing without assuming codebase knowledge, name the relevant moving parts and why they matter, describe what each option (including doing nothing) changes for the user or project, and give a clear recommendation with reasons. Define any necessary jargon in place and keep the explanation to a few short paragraphs.

This is context guidance, not a mechanically enforced tool gate. A parity check can verify that the rule ships consistently, but it cannot guarantee that an agent follows it on every turn.

The boundary itself is stated once, in `## Autonomous Operation`: reversible work the request already covers proceeds without asking; destructive actions and genuine scope changes stop here.

## Autonomous Operation


You are operating autonomously: the user may not be watching in real time and cannot answer mid-task, so asking permission for work the original request already covers blocks progress. Proceed on the reversible steps that follow from the request. Stop for destructive actions and genuine scope changes; that is the one boundary, and `## Consequential Decisions` governs how such a stop is presented. When the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is the assessment: report and stop. Before ending a turn, read your last paragraph; if it is a plan, an analysis, or a promise about work not yet done, do that work now instead of announcing it. Prefer a targeted edit over rewriting a whole file when the result is the same, because a rewrite spends output and time for no gain.

The user's instructions take precedence over guidelines in a skill. Routine skill lookup stays unmentioned, but when a skill instruction would block, narrow, or alter what the user asked for, follow the user, name the skill, link its `SKILL.md`, and quote the line you set aside; if the file cannot be found, say so by name rather than inventing a path. When two skills conflict with each other and neither with the user, apply the rule-ownership convention and name both.
## Output Minimization

- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log

## End-of-Task Summary

- End every completed task with a short closing summary, even when the change was small
- Use the labeled parts **Completed** (what changed), **Verified** (the evidence), **Open** (blocked, skipped, or deferred work; "nothing outstanding" when empty), **Next** (the concrete next step)
- Keep it scannable and factual: do not restate the conversation or add preamble
- Output-minimization rules never apply to this summary: suppress verbose logs, never the closing summary

## Construction Discipline

- After reading the real flow, stop at the first sufficient rung: skip, reuse this codebase, stdlib, native feature, installed dependency, one line, then minimum.
- Governs what you build, not how you talk. Do not drop trust-boundary, data-loss, security, accessibility, or a proving command owned by `verification-before-completion`.
- End-of-Task Summary and user-requested explanation are not debt. `minimal-construction` and `over-engineering-review` own intensity and delete-lists. Mark a cut ceiling with `construction-debt:`.

## MCP Registry Policy


Nexus-Hub's MCP registry (`catalog/mcp-configs/mcp-servers.json`) is governed by a strict decision tree. When proposing a new entry, walk it in order and stop at the first bucket that fits:

1. **Local-only** (internal Nexus-Hub servers or zero-outbound Anthropic-official servers) - always allowed.
2. **LLM-native skill** (capability achievable by instructing the agent directly) - ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP** - if the external project's logic can run locally, build the internal equivalent under `extensions/`. Strip external-source attribution; use generic descriptive names.
4. **Trusted vendor wrapper (your-own-account)** - acceptable only when the vendor is the intrinsic data destination, reverse-engineering isn't viable, AND the feature is extremely worth it. Justify all three in the `_comment`.
5. **Otherwise** - drop.

Hard no: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service. Full policy + 5-question audit in `AGENTS.md`. Matrix at `docs/policy/mcp-reverse-engineering-matrix.md`.

## Skill Discovery
When the user's request matches a skill in the SKILL INDEX below, read the full skill file from the path listed and follow its instructions. Do not mention the skill lookup to the user. Disclosure of a skill instruction that blocks, narrows, or alters the request is governed by `## Autonomous Operation`.

{{SKILL_INDEX}}

## Context References

- Skills: see the Skill Index above (the Nexus-Hub catalog ships under `~/.nexus-hub/`)
