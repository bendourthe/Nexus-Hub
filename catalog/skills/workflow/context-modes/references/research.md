# Research Mode

Gather evidence. Compare options. Produce a written report.

## Posture

- The next deliverable is a report, not code.
- Every claim is grounded: cite source files, commits, docs, or external references the user can verify.
- Options are compared explicitly. A research report that recommends one option must show what was rejected and why.
- Trade-offs are surfaced. "Option A is faster, Option B is simpler" -- make the axes explicit.

## Primary tools

- `Read`, `Grep`, `Glob` for in-repo evidence.
- `Bash` for `git log`, `git blame`, dependency listings, and read-only analysis.
- `WebFetch` and `WebSearch` when authorized by the user and the question genuinely needs external context (library docs, RFCs, vendor pages).

## Stopping conditions

- A written report exists in the session output (or in a file the user requested) that:
    1. States the question.
    2. Lists the options considered.
    3. Gives each option a short trade-off summary.
    4. Recommends one option with the reasoning, OR hands the choice to the user.

## Forbidden in research mode

- Writing or editing source code. Research informs the next decision; it does not make the change.
- Committing or running deploys.
- Picking the option silently. The user must see the alternatives even when the agent has a clear preference.
- Citing external sources the agent cannot verify in this session ("the docs say...") without a fetched URL or quoted passage.

## Report format

```
Question: <one-sentence framing>

Options:
1. <name> -- <one-sentence summary>
   Pros: ...
   Cons: ...
   Evidence: <file:line, URL, or commit hash>

2. <name> -- ...

Recommendation: <option N> because <reason>. If the user prefers <other axis>, option M is a fit instead.
```

## Common research-mode failures

- Producing one option and calling it research. If you only considered one path, the work was scoping, not research.
- Burying the trade-offs in prose. Use a list or a table so the user can scan.
- Letting the recommendation creep into an implementation. As soon as the agent starts writing code, it has left research mode -- announce the switch.

## Exit hint

Research mode hands off to `dev` once the user has accepted (or selected) an option. Announce the switch and treat the report as input to dev mode, not as something to keep amending.
