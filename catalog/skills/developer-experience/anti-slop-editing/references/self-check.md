# Self-Check Rubric

The `anti-slop-editing` skill grades its own output against this rubric before returning it. Run every applicable check. If any check fails, fix the output and grade again. Loop until all checks pass. This runs inside the single editing agent; there is no separate evaluator agent and no external call.

Two of the checks are conditional: the Edit-mode checks apply only to an Edit request, and the Detect-mode checks apply only to a Detect request. The shared checks apply to both.

## Shared checks (both modes)

1. **Point preserved.** The writer's actual claim and intent survive unchanged. The edit or the findings never alter what the draft is saying, only how it says it. PASS/FAIL.
2. **Voice preserved.** The 3-5 voice signals identified before editing are still present. Strong, characterful human sentences were not flattened into generic prose. PASS/FAIL.
3. **Proportional cutting.** The amount changed (or flagged) is proportional to the actual slop present. A clean draft yields few or no changes; a slop-heavy draft yields many. The pass did not invent problems to look thorough, and did not rewrite wholesale where a light touch was enough. PASS/FAIL.
4. **ASCII punctuation only.** No em-dashes, no clause-joining spaced hyphens (the " - " connector), no curly quotes, no Unicode ellipsis. Parentheses, commas, colons, straight quotes, and "..." only. PASS/FAIL.

## Edit-mode checks

5. **Named patterns removed.** Every pattern from the catalog that was present has been fixed in the edited draft (or consciously kept as protected voice, and noted as such). PASS/FAIL.
6. **Empty words and phrases removed.** Banned words, often-empty adverbs, and empty phrases from `slop-wordlist.md` are gone where they were filler. Instances that carry real emphasis, contrast, or uncertainty were kept on purpose. PASS/FAIL.
7. **What-changed list present.** The output ends with a list naming each pattern removed and the one-line reason, so the writer can see and reverse any edit. PASS/FAIL.

## Detect-mode checks

8. **Each finding is named and quoted.** Every finding cites a catalog pattern by name and quotes the exact offending line. PASS/FAIL.
9. **Each finding has a short fix.** Every finding gives a brief, concrete suggested fix (not a full rewrite). PASS/FAIL.
10. **No rewrite, no score, no authorship verdict.** Detect output contains no rewritten draft, no numeric "AI probability" or percentage, and no claim about whether a human or a machine wrote the text. PASS/FAIL.

## How to apply

- Grade only the checks that apply to the current mode plus the four shared checks.
- A single FAIL means the output is not ready. Fix the specific failing check and re-grade the whole applicable set (a fix can regress another check, for example over-cutting to satisfy check 5 can fail check 2).
- Stop when every applicable check is PASS, then return the result.

This rubric is distinct from the SKILL.md `## Verification` section, which checks observable artifacts after the skill is authored, and from `evals/trigger-cases.json`, which checks that de-slop requests route to this skill. This file checks the content quality of a specific edit or detection at runtime.
