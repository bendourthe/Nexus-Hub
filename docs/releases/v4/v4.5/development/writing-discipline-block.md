# Writing Discipline block (Phase 1 source of truth)

This file holds the exact text inserted into all twelve substantive instruction templates by v4.5.0 phases 1 and 2. The block below, from its heading to the final line, is what the lockstep parity guard byte-compares and what the companion validator asserts on the seven unguarded templates. Edit it here first, then propagate; never edit one template alone.

## Design notes

- Two parts, as the plan specifies: a PROHIBITION naming the highest-frequency cliche moves, and a SELF-CHECK that binds live chat replies as well as generated files.
- The punctuation rule previously lived only in base-claude.md under `## Communication Style`, so only Claude Code users received it. It moves into this shared block, and that Claude-only section is retired, which is why the net word cost on base-claude.md is lower than on the other four lockstep files.
- Mannered prose is named as one class and not defined; its definition lives in the anti-slop-editing reference file that phase 3 adds.
- Response structure stays owned by `## Communication Contract` and verbosity by `## Output Minimization`; this block governs neither.
- Written in compliant prose: ASCII only, no em-dashes, no hard-wrapped paragraphs, no cliche from its own list.

## The block

```markdown
## Writing Discipline

Do not produce the high-frequency AI-cliche moves: throat-clearing openers; "not just X, but Y" and "it is not X, it is Y" contrasts; importance puffery ("crucial", "it is important to note"); weasel attribution ("experts say", "studies show"); faux-insight setups ("here is the thing"); trailing "-ing" clauses that restate a sentence as analysis; fake-profound closing lines; summary-recap endings; and mannered prose, where metaphor or flourish stands in for a direct statement.

Punctuation is ASCII only: no em-dashes, no clause-joining spaced hyphens, punctuation placed outside quotation marks by logic, and no hard-wrapping of paragraph text. Keep a professional teaching tone.

Chatbot leftovers are defects, not style: never emit "as an AI language model", "here is the revised version", or "I hope this helps".

Self-check: before returning any response or writing any file, scan your own output against this list and fix what you find. This binds live chat replies, not only generated documents.

Full catalog and the Edit / Detect modes: `anti-slop-editing`.
```

## Measured cost

- Lines: 11 (heading, four single-line paragraphs, one pointer line, and their separators), under the 14-line budget.
- Words: 163. Net template growth: +163 words on each lockstep file except base-claude.md, where retiring the absorbed `## Communication Style` section (54 words including its heading) leaves +109.
- Tokens: roughly 215 per turn at the usual 1.3 tokens per English word, because the instruction file is part of the context on every request; prompt caching makes the repeat reads cheap but not free. That cost is paid on whichever platform the user is running, so the common single-platform case is 215 tokens per turn, and a user who works across several platforms pays it once per platform in use.
- Word ceilings: the five lockstep ceilings were raised by exactly the measured delta rounded up to 10 (+110 on base-claude.md, +170 on the other four), which leaves each file the same headroom it had before the block. Justification recorded in `docs/policy/doc-budgets.md` under Recorded raises.
