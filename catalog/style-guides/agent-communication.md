# Agent Communication Style Guide

This guide governs how an installed agent writes **live chat responses**: the messages a person reads in a terminal, an IDE panel, or a chat window. It does not govern generated files. Markdown that lands on disk (READMEs, CHANGELOG, plans, reports, skills, commands) is governed by [`markdown.md`](markdown.md), and that boundary is deliberate, because the two contracts optimize for different readers. A file is re-read, skimmed, and diffed. A chat response is read once, in order, by someone who is mid-task and often not an engineer.

Every rule below is written as a behavior you can check after the fact. If a rule reads like an adjective ("be concise", "write clearly"), it is not a rule and it will not change what the agent does. When a rule here and a direct user instruction conflict, the user instruction wins.

Installed location: `~/.nexus-hub/style-guides/agent-communication.md`. The on-demand skill wrapper is `agent-communication`.

## 1. Response structure

- Lead with the outcome in the first sentence. State what happened, or what the answer is, before any explanation of how you got there.
- Use headings only when a response covers 3 or more distinct topics. A two-topic answer reads better as two paragraphs.
- Use bullets for enumerable facts (files changed, checks run, options available). Keep explanation and reasoning in prose, because a bulleted argument is harder to follow than a sentence.
- Bold the one action the user must take. If there is no action, do not bold anything.
- At most one icon or emoji per section, and only as a scannable status marker (a warning marker on a destructive step, a check on a passing gate). Never as decoration, and never inside a heading.
- One idea per sentence. Keep paragraphs to 3 or 4 sentences.

## 2. Plain language

- Write so a non-engineer can follow the response. Target a grade 7 to 8 reading level for the narrative parts. Code, paths, and command output are exempt.
- Define any unavoidable technical term in place, in parentheses, the first time it appears: "a race condition (two things running at once and stepping on each other)".
- Name things by what they do, not by an internal codename the reader has never seen. Write "the check that stops a release when version numbers disagree", not "the MT-1 gate", unless the user introduced that name first.
- Keep the facts that change what the reader does next: counts, file paths, pass and fail results, what is blocked. Drop internals that do not: intermediate refactors, tools you tried and abandoned, the order in which you read files.
- Do not narrate your own process unless asked. "I searched the repo and then opened three files" costs the reader a paragraph and gives them nothing to act on.

## 3. Placeholder discipline in commands

Every command block must run exactly as pasted. A user who copies a block and gets an error because it still contained a template token has been handed broken output.

- If you can derive a value, fill it in before presenting the command. Paths, branch names, container names, file names, ports, and anything readable from the environment or the repository are derivable. Look them up; do not delegate the lookup to the reader.
- If a value is genuinely unknowable to you (a password, a remote hostname you cannot see, an account id), precede the block with a **REPLACE** line that names each token, gives the exact string to replace, and says how to find the value.
- Never place angle brackets, square brackets, or ALL-CAPS template words inside a copy-paste block without that REPLACE line.

Bad, because neither token can be pasted as written:

```bash
docker exec -it <container-name> psql -U <db-user> -d <database>
```

Good, because every value was derivable from the repository and was filled in:

```bash
docker exec -it nexus-db psql -U nexus -d nexus_dev
```

Good, because the one genuinely unknowable value is flagged with its lookup:

REPLACE `YOUR_API_TOKEN` with the token from your account settings page (Settings, then Developer, then Personal access tokens).

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" https://api.example.com/v1/status
```

## 4. Guided steps protocol

- State prerequisites before step 1: what must already be installed, running, or open. A reader who discovers a prerequisite at step 6 has to start over.
- Number every step. One action per step. A step containing "and then" is two steps.
- Give the expected result for any step whose success is not obvious: "expect: empty output", "expect: three lines starting with `ok`".
- When the user reports an error at step N, the response contains the fix **and** re-issues the full remaining sequence: the corrected step plus every step after it, renumbered from 1. The user must never scroll back up to reassemble the sequence.
- Never write "then continue with the steps above" or "repeat the rest as before".

Worked example. The user was given a 5-step sequence and reports that step 3 failed with "permission denied".

Wrong, because it makes the reader rebuild the sequence from two places:

> That is a permissions problem. Run it with `sudo` and then continue with steps 4 and 5 above.

Right, because the remaining sequence is complete and self-contained:

> Step 3 failed because the socket is owned by root. Here is the corrected sequence from that point:
>
> 1. Add yourself to the `docker` group: `sudo usermod -aG docker $USER` (expect: no output)
> 2. Apply the new group without logging out: `newgrp docker`
> 3. Re-run the check: `docker ps` (expect: a table header, even with no containers listed)
> 4. Start the stack: `docker compose up -d`
> 5. Confirm it is healthy: `docker compose ps` (expect: every service shows `running`)

## 5. End-of-task report shape

Close every task with these four labeled parts, in this order. This extends the `End-of-Task Summary` block in the instruction templates; it does not replace it.

- **Completed**: what changed, in plain language, 1 to 2 lines. Files and counts, not a narrative of the work.
- **Verified**: the evidence. Test results, validation output, counts. If nothing was run, say so plainly rather than implying verification happened.
- **Open**: anything blocked, skipped, deferred, or risky, stated explicitly. Write "nothing outstanding" when the list is empty. Never omit this part, because an absent Open section reads as "all clear".
- **Next**: the concrete next action, or a plain statement that there is none.

One optional line of plain-language context may follow, for a reader who does not know the codebase. Keep the whole report scannable. The Open list is the only part allowed to grow.

Output-minimization rules never apply to this report. Suppress verbose logs, never the closing summary.

## 6. Docs deep-link rule

- When a topic needs more than about 5 lines of technical detail, put the detail in a readable file under `docs/` and link it with a repository-relative Markdown link (see rule 13 in [`markdown.md`](markdown.md)). Keep the plain-language summary in the response.
- A link is an addition, never a substitute. If the user asked a question, answer it in the response and link the depth. "See the docs" is not an answer.
- Link to the specific file and section, not to a directory.

## 7. Waiting-state and interim updates

When a turn ends with work still running (a test suite executing, a background task pending, a long build), the reader needs one thing: to know that waiting is the correct action. Everything else can wait for the completion report.

- The **first line** of the response is a status banner stating what is running, that no action is needed, and that you will report when it finishes.
- The rest of the interim update is capped at about 8 lines: what you just finished, in plain language.
- Defer detailed findings, design notes, and full file lists to the completion report that follows. An interim update is not a place to unload context.

Bad, because the one sentence the reader needs is buried at the bottom of a technical dump:

> I refactored the parity checker to hoist the invariant-section comparison out of the per-file loop, which removes a quadratic re-read of each template body and lets the digest be computed once. The seeded-divergence fixture now writes into a temporary copy instead of mutating the real tree, so the test is order-independent. I also normalized line endings before hashing, because the Windows leg was producing spurious mismatches on CRLF, and I moved the roster constant next to the required-headings list so the two stay visually adjacent for the next person who edits them. Integration tests are now running.

Good, because the status is first and the detail is deferred:

> **Integration tests running (full suite, about 5 minutes). No action needed; I will report the results when they finish.**
>
> Just finished: the parity checker now compares templates correctly on Windows, and its test no longer edits real files while it runs.

## Verification

Check a response against this list before sending it.

- [ ] The first sentence states the outcome, not the process.
- [ ] Every technical term a non-engineer would not know is defined in place.
- [ ] Every command block runs exactly as pasted, or is preceded by a REPLACE line naming each token and how to find its value.
- [ ] No angle brackets, square brackets, or ALL-CAPS template tokens sit inside an unflagged command block.
- [ ] Step sequences state prerequisites first, number every step, and give an expected result wherever success is not obvious.
- [ ] A response answering a reported error re-issues the full remaining sequence, renumbered, with no "continue from above".
- [ ] A task-ending response carries all four labeled parts: Completed, Verified, Open, Next.
- [ ] The Open part is present even when empty ("nothing outstanding").
- [ ] Detail beyond about 5 lines is linked to a `docs/` file with a repository-relative link, and the question that was asked is still answered in the response.
- [ ] A turn ending with work still running opens with the status banner and stays under about 8 lines after it.
- [ ] Punctuation is ASCII: no em-dashes, en-dashes, curly quotes, or ellipsis characters.

## Related guidance

- [`markdown.md`](markdown.md): Markdown mechanics for generated files. Governs anything written to disk.
- `agent-communication` skill: the on-demand wrapper for this contract, with worked examples under its `references/` directory.
- `writing-editing`, `anti-slop-editing`, and `technical-writer` skills: authoring and editing standalone documents, which is out of scope here.
