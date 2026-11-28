# Codebase Ownership Mode (Opt-In)

Do not use this snippet in a repository you do not own, or where the owner wants the code changed as little as possible. It makes the agent consolidate duplicated code and fix nearby bugs that nobody asked for. It is off by default, and no Nexus-Hub template contains it.

Summary: an opt-in instruction-file snippet for a maintainer who owns a repository and wants the agent to improve its structure as it works, with the scope exception it needs, the vendor-measured costs, the off switch, and what it does not grant. `minimal-construction` owns the trace-to-request rule this snippet relaxes.

## Who Should Use It

- A maintainer who owns the repository and wants its structure improved, such as duplicated code merged into one shared function.
- A user who accepts a larger diff and a longer closing summary in return.

## The Snippet

The first sentence is the vendor's own ownership sentence, from the Claude Fable 5.2 prompting guide at https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2 (section "Say who owns the code"). The second is the scope exception that this repository adds, because a scope rule earlier in the same prompt does not cancel the first sentence.

```text
You are the owner and long-term maintainer of this codebase, and its design is up to you.

In this repository, consolidating duplicated code and fixing bugs related to the task are in scope; list every change, including small ones, in the closing summary.
```

Paste both into the project's instruction file (for example CLAUDE.md or AGENTS.md).

## Measured Costs

The vendor measured these on small coding tasks with Claude Fable 5.2. They are not Nexus-Hub measurements and may not carry over to another model.

- Consolidation of duplicated code rose from under 10 percent of runs to about 75 percent with the sentence.
- Output tokens rose by about 70 to 80 percent.
- The model made changes nobody asked for, many of them new tests and documentation, and in some runs it changed how an existing feature behaves.
- The closing summary often left out small changes. The scope exception above exists to counter that, and the diff still needs a review.
- A scope rule that limits changes did not cancel the sentence: with "No drive-by refactors, renames or cleanups" earlier in the same prompt, the model still consolidated duplicated code in more than half of runs.

See the `claude-fable-5-2` profile in `model-prompting-research` for the recorded claims.

## One-Session Check

Run this once in a throwaway project to confirm the snippet works for the model you use.

1. Create a project with two duplicated functions and a request to add a third caller.
2. Start one fresh session with the snippet in the project's instruction file.
3. Read the closing summary. It must list every changed file, including any consolidation.

A session that consolidates but omits a file from the summary fails the check.

## Turn It Off

Remove the two paragraphs from the instruction file. Nothing else was installed, so nothing else needs removal.

## What It Does Not Grant

- No destructive action. Confirmation rules for risky or irreversible actions still apply.
- No push, and no change to branches or releases.
- No edit outside the repository.
- It does not relax the verification, security, or accessibility rules owned by other skills.

## Related

- `minimal-construction` `SKILL.md` owns the rule that every changed line traces to the request. This snippet is a declared, scoped exception to it.
