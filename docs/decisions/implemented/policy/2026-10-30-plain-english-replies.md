# Decision: Plain-English Replies for a Non-Native Reader

Status: implemented - the non-native-reader bar and the slang ban ship in every instruction template; the list and detector stay on demand.

Maintainers use this record when a reply is flagged for agent or engineering slang, when a template edit touches the Communication Contract or Writing Discipline blocks, or when v4.15.0's standing-rule review reassesses the wording. It covers the two always-loaded edits, the on-demand material, and the ownership split between `agent-communication` and `anti-slop-editing`.

**Date**: 2026-10-30. **Source**: the maintainer's assessment of a public list of agent and engineering slang with plain replacements, and the plan `docs/releases/v4/v4.14/plans/v4.14.8-plain-english-replies-and-source-labels.md` (Part A).

## Problem

The Communication Contract asked for "plain language a non-engineer follows; define jargon in place". That bar lets through the slang an agent uses among peers: "load-bearing", "blast radius", "land", "punt", "sanity check", "spin up", "cutover". A reader whose first language is not English, or who does not work in software, cannot follow those at first read, and nothing in the always-loaded text named them as a defect. The `anti-slop-editing` word list covered marketing words ("leverage", "robust") but no engineering slang, and the offline detector had no pattern for it, so an agent self-checking a reply had nothing to check against. The repository's own prose shows how normal the habit is: 55 catalog and policy files use "load-bearing" and 50 use "blast radius".

A second gap sat beside it. The contract did not say what to do with a warning, an error, or a hook message. An agent that rewrites `[secret-scan] BLOCKED: Potential secrets detected in deploy.env` as "the scanner tripped on your file" has made the reply shorter and taken away the exact words the reader needs to search for or report.

## Decision

Two always-loaded edits, byte-identical across the 13 substantive templates and guarded by `tests/validators/test_communication_contract_rule.py` and `tests/validators/test_writing_discipline_rule.py`:

- The first Communication Contract bullet reads: outcome first, in simple English a non-native reader follows at first read; explain a needed technical term in place; quote warnings, errors, and names exactly, then explain them; link detail beyond about 5 lines in a `docs/` file. The `agent-communication` skill and `catalog/style-guides/agent-communication.md` section 2 own the rule and the procedure.
- The first Writing Discipline paragraph names "agent or engineering slang" as a banned habit, with five example pairs beside it: load-bearing -> needed, blast radius -> what it affects, land -> merge, punt -> postpone, sanity check -> quick check. The clause is folded into the existing one-line paragraph, so the body stays at six non-empty lines. The `anti-slop-editing` skill owns the list, its exemptions, and the detector.

The on-demand material carries the rest. `anti-slop-editing/references/slop-wordlist.md` section "Agent and engineering slang" lists 24 terms with plain replacements and owns four exemptions: the list applies to text a person reads, not to messages between agents; a real name in backticks is never slang; when the slang word is the precise term, explain it in place instead of replacing it; warnings, errors, commands, and identifiers are quoted exactly and then explained. `detect_prose_cliches.py` reports an advisory `engineering-slang` finding for the 13 terms whose slang reading is unambiguous; "happy path", "fan out", "surface", "land", "ship", "gate", "park", "plumbing", "nit", "punt", and "first-class" stay with the editor's judgment because each has a literal meaning or names a real technique. A match inside backticks or straight quotes is exempt, which is an accepted bypass because the class is advisory and nothing gates on it.

The five lockstep word ceilings in `docs/policy/doc-budgets.json` rose by exactly the measured 40 words, logged under `_v4_14_8_plain_english_justification` and in `docs/policy/doc-budgets.md`.

## Alternatives considered

- **Paste the full list into every template.** Rejected: 24 terms with replacements cost about 150 words on every turn on every platform, and the list grows. One sentence and five examples carry the habit; the list loads only when the agent or an editor opens it.
- **No examples in the always-loaded text, only a pointer.** Rejected: a model that never sees an example rarely opens the on-demand list, and "no slang" with no example reads as the marketing-word rule the block already states. Five pairs are enough to teach the shape of the habit.
- **Flag every listed term lexically in the detector.** Rejected: "the ship sailed", "park the car", "the gate is locked", "happy path" as a testing term (67 files), and "fan-out" as an orchestration pattern (50 files) would all fire, and an advisory class that fires on legitimate prose is one nobody reads. The 13 encoded terms have no common literal reading.
- **A new Writing Discipline line for slang.** Rejected: `test_the_rule_stays_short_enough_to_always_load` caps the body at six non-empty lines, and the block already uses them. The clause joins the first paragraph's list of banned habits instead, which is also where a reader expects it.
- **Leave the bar at "non-engineer".** Rejected: a non-engineer who is a native speaker follows "sanity check" and "spin up"; a non-native reader does not, and the maintainer's reports came from that reader.

## Consequences

Installed agents pick up both rules on the next installer run, which regenerates each platform's instruction file from the templates; `scripts/lib/installer/legacy_fingerprints.json` was regenerated so the installer recognizes the previous template text as its own. An agent can self-check a reply with `detect_prose_cliches.py` and see slang as an advisory finding, and a reviewer can point at one owned list instead of restating it. The repository's own 55 "load-bearing" and 50 "blast radius" uses remain until a follow-on plan rewords them; this decision changes what agents write, not what the catalog already says. v4.15.0's instruction-necessity review will reassess both edits under its standing-rule review and must count the 40 words. Part B of the same plan (hook and agent source labels) is a separate decision and ships or is cut independently.
