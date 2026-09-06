# v4.5.0 Phase 7 Evidence: Independent Goal-versus-Codebase Review

**Date**: 2026-09-04
**Plan**: `docs/releases/v4/v4.5/plans/v4.5.0-anti-cliche-and-agent-security.md`, sub-task 7.2 (T027)
**Method**: `implementation-convergence` against the plan's Goal, reading the repository at `440f6985` (phase 6 commit) rather than the task list. Each clause below names the command or reading that decided it. The companion ten-section record required by the implement-phase runbook is `last-phase-evidence.md` in this directory.

## Goal restated

Two tracks. Track A: a platform-wide, always-loaded writing rule that prohibits the highest-frequency AI-cliche moves and binds the agent's own chat replies as well as its files, mechanically guarded across every substantive instruction template, with the `anti-slop-editing` catalog extended to the patterns the prose-cliche comparison listed as uncovered and an offline deterministic detector for the encodable ones. Track B: `agent-execution-isolation` closes the four boundary gaps the agent-security comparison found, `agentic-endpoint-hardening` gains a narrow deterministic response class, and cross-domain attack chaining has one owning skill.

## Clause 1: is the rule genuinely always-loaded on every supported platform?

Checked by reading, not by the validator: `grep -c "^## Writing Discipline" templates/ai-instructions/*.md` returns 1 for each of the twelve substantive templates (`base-aider`, `base-claude`, `base-codex`, `base-cursor`, `base-gemini`, `base-google-shared`, `base-kimi`, `base-openclaw`, `base-opencode`, `base-qwen`, `base-windsurf`, `generic-instructions`) and 0 for the four include-only shims (`base-antigravity-10`, `base-antigravity-20`, `base-antigravity-cli`, `base-gemini-cli`), each of which carries exactly one `@` include line and therefore receives the block through `base-google-shared.md`. Sixteen files total, twelve with the block, four reaching it by include. **Converged.** One qualification: "always loaded" is a property of the installed instruction file, and the installer was not run live on this host (standing instruction; see `last-phase-evidence.md`, Tier 3). Distribution of templates into instruction files is covered by the installer smoke suites, which pass.

## Clause 2: does it genuinely bind chat replies?

Read from `base-claude.md` in the tree, not from the source-of-truth file: the self-check clause is "Self-check: before returning any response or writing any file, scan your own output against this list and fix what you find. This binds live chat replies, not only generated documents." The clause was not softened during authoring; the words "any response" and "live chat replies" are both present, and `test_the_self_check_binds_live_replies` asserts the marker sentence on all twelve. **Converged.** The decision and its alternatives are recorded in `docs/decisions/implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`.

## Clause 3: do the parity guard and companion validator fail when the block is removed from any one of the twelve?

Verified by breaking each one. For each of the twelve templates in turn, the block was stripped from the working copy, `python scripts/check_base_template_parity.py` and `python -m pytest tests/validators/test_writing_discipline_rule.py -q` were run, and the file was restored with `git checkout --`. Results:

| Template | Parity guard exit | Validator exit |
|---|---|---|
| base-claude, base-codex, base-cursor, base-gemini, base-opencode | 1 | 1 |
| base-aider, base-google-shared, base-kimi, base-openclaw, base-qwen, base-windsurf, generic-instructions | 0 | 1 |

Twelve of twelve fail the validator; the lockstep five also fail the release-gate parity guard. That is the designed split: the parity guard covers the machine-guarded five, the validator covers all twelve. The tree was clean afterwards (`git status --short | wc -l` printed 0). **Converged.**

## Clause 4: does `anti-slop-editing` cover the patterns the comparison listed as uncovered?

Checked against the comparison's own coverage table (`comparisons/v4.5.0-comparison-prose-cliche-detection.md`, rows marked Not covered and Partial):

| Comparison row | Where it now lives |
|---|---|
| "The other roughly 20 patterns" (therapist-voice and faux-reveal register) | `references/cliche-patterns.md` clusters 1 to 5: dwelling instruction, naming ceremony, understated significance, presumed knowledge, the isolated part, the lone trusted source, mock humility, the announced punchline, the discovery frame, retroactive significance, the obituary, head-sized praise, the negation chain, the verb reversal, the totality claim, performative honesty, the stranded auxiliary (17 named), plus mannered prose (cluster 7) and chatbot leftovers (cluster 6): 19 patterns |
| `ai-leftovers` | Cluster 6 in the reference file, a `Chatbot leftovers` body entry, and the detector's `chatbot-leftover` defect id |
| `echo-triad`, `sentence-anaphora`, `stacked-questions` (Partial: nothing countable) | `Robotic rhythm` is three countable rules with thresholds; detector ids `echoing-run`, `repeated-opener`, `stacked-questions` |
| `did-not-chain` (absent) | `negation-chain` and `verb-reversal` in cluster 3 and the detector |
| `colon-triple` payoff, `despite-challenges` (Partial) | Not separately named. `colon-triple`'s payoff remains under the pre-existing `Colon reveals` entry; `despite-challenges` remains adjacent to `Summary-recap endings`. |

**Converged with one recorded remainder.** The two Partial rows the comparison itself rated as adjacent to existing entries were not promoted to named patterns; the plan's phase 3 scope was the uncovered register and the countable rhythm rules, and both of those landed. Recorded as a note in `known-gaps.md`, not a gap, because the existing entries already flag both moves.

## Clause 5: does the detector run offline with no third-party import?

Import inspection of `scripts/detect_prose_cliches.py`: `argparse`, `json`, `re`, `sys`, `dataclasses`, `pathlib`, plus `from __future__ import annotations`. All stdlib. `python scripts/check_no_outbound.py --root <scripts dir>` reports OK. `test_stdlib_only_imports` pins it. **Converged.**

## Clause 6: do the four `agent-execution-isolation` gaps genuinely close?

Checked against the four gap statements in `comparisons/v4.5.0-comparison-agent-security-incidents.md` (G1 to G4), reading the skill body at `440f6985`:

| Gap statement | Where the body answers it |
|---|---|
| G1: for every allowlisted destination, enumerate what it can reach in turn and treat the union as the agent's real reachability | Step 5 sub-steps 5 to 7 (transitive reachability, named intermediary classes, scope to allowlisted destinations); triage question 3 rewritten; rationalization "the package registry is internal, so allowlisting it is safe" |
| G2: a write-capable service reachable from more than one session is a communication channel until proven otherwise | Step 3 sub-steps 6 to 8: bolded correction that ephemeral containers isolate processes not sessions, required enumeration artifact, four-rung ladder with write-scoping plus read-back denial as the minimum; rationalization "each session gets a fresh container, so the sessions cannot talk" |
| G3: an environment layer around the sandbox under the assumption code execution on the host is reachable | New step 2 (layer 0: secrets off hosts, management-network and control-plane restriction, host MAC, dedicated infrastructure, recorded host tier); rationalization "a VM is a real boundary" |
| G4: minimize the surface across the boundary (virtual devices, host mounts, management sockets, debugging interfaces) | Step 4 sub-step 5; rationalization "the sandbox's virtual devices are the hypervisor's problem" |

The comparison's remaining recommendations also landed: G5 (deterministic hard stop) in `agentic-endpoint-hardening` step 7 sub-steps 4 to 6 (phase 6); G6 (multi-layer egress) in step 5 sub-step 7 of the isolation skill; G7 (cross-domain chaining) owned by `purple-team-exercise-design` with handoff lines in the two analyzers (phase 6); G8 (agents do not stop) as a named principle at the top of the isolation skill's Instructions. **Converged.**

## Divergences and appended work

No clause diverged. Two items are appended to `known-gaps.md` as open work rather than narrated here: the human check of whether the always-on clause improves replies (DF-1), and the absence of any reachability or shared-service enumeration on this repository's own agent surface (DF-2), which the security comparison raised as an open question about Nexus-Hub itself and which the plan's fourth human test names. Neither is a miss against the Goal as written; both are what the Goal leaves to a person.
