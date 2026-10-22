# Decision: American English Spelling in Living Files and Installed Agents

Status: implemented - instruction rule shipped to every platform, living files converted, guard in the fast CI profile.

Maintainers and contributors use this record when a spelling finding fails CI, when deciding whether a file counts as frozen history, or when a platform's generated text drifts from American spelling. It covers the instruction rule, the repository guard, and what each deliberately leaves alone.

**Date**: 2026-10-21. **Source**: maintainer request to make the repository and every platform Nexus-Hub installs into use American spelling by default. The maintainer chose to convert living files only and to add a regression guard.

## Problem

The catalog mixed spellings: about 1,000 British forms (`colour`, `centre`, `behaviour`, `judgement`, `-ise` verbs) sat in skills, guides, scripts, and tests, and nothing told an installed agent which variety to write. Agents therefore followed whatever spelling the surrounding text or the user's prompt suggested, and every newly contributed skill could add more.

## Decision

The `## Writing Discipline` block, which every substantive instruction template already carries byte-identically, states that spelling is American English in prose, comments, and names an agent creates, while external identifiers, quoted text, and URLs keep their published spelling. The sentence joins the existing punctuation line, so the always-loaded block stays inside its six-line budget; condensed to 15 words, it raises the five lockstep word ceilings in `docs/policy/doc-budgets.json` by exactly that amount.

Living files were converted once with `scripts/check_american_spelling.py --fix`, and the same script runs in the fast CI profile's hygiene group and in `make validate`. It reads only tracked files and treats `docs/archives/`, `docs/releases/` (plans, comparisons, known-gaps ledgers, and development evidence), any `receipts` directory, patch and diff files, and every released CHANGELOG entry as frozen. It leaves backtick code spans, URLs, `aria-labelledby`, and hyphen or underscore compounds untouched, because those are literals whose spelling is owned elsewhere. `cancelled` is accepted: American dictionaries list it, and GitHub Actions, VS Code, and this repository's usage-monitor extensions publish it as an API value, so rewriting it would split one identifier into two spellings.

## Alternatives considered

- **Convert archives and receipts too.** Rejected: they are records of what was written at the time, several are hash-pinned evidence, and the conversion would roughly double the diff for no reader benefit.
- **Convert active release documents.** Tried first and reverted: approved plans under `docs/releases/` are hash-pinned by the completion checker, so converting the frozen v4.14.2 plan broke `tests/validators/test_recorded_followon_gaps.py` in CI, and the distribution handbook pins its development evidence the same way. Release records are history once approved, so the whole tree is frozen.
- **Rule only, no guard.** Rejected: the next contributed skill would reintroduce `colour` with nothing to catch it, and the conversion would decay silently.
- **A generic `-ise` to `-ize` pattern.** Rejected: it flags `raise`, `exercise`, `enterprise`, and `promise`, which outnumber real hits by thousands. The guard enumerates British stems instead.
- **A git grep prefilter over every word form.** Rejected after measurement: whole-word fixed-string matching over about 3,000 forms took 110 seconds to 3.5 minutes on Windows. A family-stem regex runs the whole check in about 4 seconds.
- **A separate Writing Discipline paragraph.** Rejected: the block is capped at six non-empty lines because it loads on every turn on every platform.

## Consequences

A British form in a living file fails the fast profile with its path, line, and the American replacement; `python scripts/check_american_spelling.py --fix` resolves it. A literal that must keep British spelling is either wrapped in backticks or marked on its line with `spelling: allow`. Hyphenated prose compounds such as `off-centre` are not detected, because the guard cannot tell them from kebab-case identifiers; reviewers catch those. Installed agents pick up the rule on the next installer run, which regenerates each platform's instruction file from the templates.
