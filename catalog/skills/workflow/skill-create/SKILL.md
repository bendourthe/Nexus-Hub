---
name: skill-create
description: Draft a new Nexus-Hub-conformant SKILL.md by mining the local git history for a recurring pattern - a sequence of commits, a repeated fix, a workflow the team keeps redoing by hand - and turning it into a reusable skill with full frontmatter, Common Rationalizations, and binary Verification. Make sure to use this skill whenever the user says "turn this into a skill", "we keep doing this, make a skill", "draft a skill from our git history", "create a skill for X", "generate a SKILL.md from these commits", "automate this recurring workflow as a skill", "should this pattern be a skill", or otherwise asks to manufacture a new skill out of work that has already happened in the repo. Also trigger when continuous-learning surfaces an instinct cluster strong enough to become a skill and the next step is drafting the actual SKILL.md. SKIP, do NOT use for, auditing or scoring skills that already exist (use skill-stocktake), the generic interactive new-skill wizard when there is no git-history signal to mine (use create-skill-or-command), or editing one existing skill.
summary_l0: "Draft a conformant SKILL.md by mining local git history for a recurring, automatable pattern"
overview_l1: "Generate a new Nexus-Hub skill from evidence in the repository's git history. Analyze git log and diffs for a recurring pattern, confirm it with the user, then draft a SKILL.md that follows every Nexus-Hub convention: pushy description with a SKIP clause, quoted summary_l0 and overview_l1, When to Use, Instructions distilled from the commits, Common Rationalizations that cite failure modes, binary Verification, and Related Skills. At the draft step apply the six agent-writing concepts in catalog/skills/developer-experience/skill-description-authoring/references/agent-writing-theory.md. The draft is local-analysis-only and is surfaced for maintainer review, never auto-registered or committed. Trigger phrases: turn this into a skill, draft a skill from git history, we keep doing this make a skill."
version: 1.0.0
author: Benjamin Dourthe
category: workflow
tags:
  - skill-authoring
  - git-history
  - pattern-mining
  - skill-generation
  - local-only
---

# Skill Create (from git history)

Manufacture a new skill out of work that already happened. Most skills are written speculatively; this one is written from evidence: the agent mines the repository's own git history for a pattern the team keeps repeating by hand, then drafts a Nexus-Hub-conformant `SKILL.md` that captures it. All analysis is local (`git log`, `git diff`) with zero outbound calls.

This is the local-analysis path of ECC's `skill-create` pattern, re-authored to Nexus-Hub conventions (`AGENTS.md` "Adding a New Skill"). No upstream text is copied.

## When to Use This Skill

Use when:

- The user points at a recurring workflow ("we keep doing this dance every release - make it a skill").
- A run of commits shows the same fix or refactor applied repeatedly and it should be codified.
- [[continuous-learning]] has surfaced an instinct cluster strong enough to graduate into a real skill, and the next step is writing the actual `SKILL.md`.

**When NOT to use:**

- You want to assess the quality of skills that already exist - use [[skill-stocktake]].
- You are authoring a skill from scratch with no git-history signal to mine - use the interactive `/skills create` wizard.
- You are editing one existing skill's content - edit it directly.

## Instructions

### 1. Gather the history signal

Run local git analysis only (no network):

```bash
git log --oneline -50
git log --stat --since="3 months ago"
git log -p -- <path-or-glob-the-user-named>
```

Look for:

- **Repeated fixes**: the same file/function touched by several commits with similar messages ("fix flaky X again").
- **Manual multi-step workflows**: a recurring commit sequence (bump version -> regenerate index -> update changelog) that a skill could codify.
- **A class of change**: many commits doing structurally the same edit across different files (e.g., "register new validator in both installers").

### 1.1 Label the evidence outcomes

Git history is success-biased: merged commits show what landed, not a balanced record of what failed along the way. Build an evidence table before drafting:

| Commit, diff, or counterexample | Outcome | Observable basis |
|---|---|---|
| SHA, revert, follow-up fix, or user-supplied example | `success` or `failure` | Passing/failing gate, revert relationship, correction, or user confirmation |

Every git-derived example used in the draft MUST carry an explicit `success` or `failure` label. Cite at least one real failure mode from a revert, a follow-up fix, or a user-supplied counterexample for Common Rationalizations; do not pretend ordinary git log is a balanced dataset. If the candidate set mixes successes and failures and any item is unlabeled, warn hard, list the unlabeled SHAs or examples, and refuse to draft until the user labels them or drops them from the evidence set. Never invent labels from commit-message sentiment and never send history to an outbound LLM-as-judge.

### 2. Confirm the pattern with the user

State the candidate pattern in one paragraph, cite the supporting commit SHAs, and ask the user to confirm it is worth a skill before drafting. A pattern with only one or two occurrences is usually premature - say so.

### 3. Pick category and name

Choose an existing category from `AGENTS.md` (do not invent a new one without sign-off). Name in `kebab-case`, descriptive but concise. Check `data/SKILL_INDEX.md` for a near-duplicate first; if one exists, propose extending it instead of creating a new skill.

### 4. Draft the SKILL.md

Write a draft that follows every Nexus-Hub convention:

- **Frontmatter**: `name` (matching the directory), a pushy `description` (verbatim trigger phrases the user is likely to say, plus a `SKIP:` clause), quoted `summary_l0` (<= 15 words), quoted `overview_l1` (<= 150 words). Optional fields exist and are omitted by default: the invocation-policy booleans `disable-model-invocation` / `user-invocable`, and the security framework-mapping lists. Add an invocation-policy field only when the skill genuinely should not be model-invoked (a destructive or side-effecting workflow) or should not appear in the slash menu (pure background knowledge).
- **Body, in order**: title, When to Use This Skill (with "When NOT to use"), Instructions as an operational runbook distilled from the actual commits (numbered actions, decision rules, artifacts, gates, and verification the agent can execute, not a language or domain textbook), Common Rationalizations (each row citing a concrete failure mode seen in the history, not a platitude), binary Verification (observable artifacts/commands), Related Skills (`[[ ]]` cross-links). Put supporting pedagogy in Tier-3 `references/` and link it from the runbook only where needed.
- Keep the body within the size norm (target <= 500 lines).
- **Agent-writing discipline**: apply all six concepts at this draft step. The full treatment is `catalog/skills/developer-experience/skill-description-authoring/references/agent-writing-theory.md` (owned by [[skill-description-authoring]]; do not fork a second copy). Condensed:

    - Context pointers: the `description` wording, not the body on disk, decides whether the skill loads. One trigger family per distinct branch. Name any bundled reference by path and why.
    - Two loads: Tier 1 spends catalog-wide context load; put branch-only procedure in `references/`.
    - Leading words: use catalog tokens (`SKIP`, `Verification`, `frontmatter`); collapse spelled-out triads; delete no-op instructions rather than trimming them.
    - Negation avoidance: state the positive target; reserve "do not" for hard guardrails paired with the allowed alternative.
    - Sediment prune: every line must still change behavior. Cut restatements of `AGENTS.md` that a link already covers.
    - Hard/soft setup-dependency: if the new skill cannot function without prior setup, put an explicit run-this-first pointer at the top of Instructions. If setup only sharpens it, mention that in soft prose and do not block.

Descriptions themselves are authored with [[skill-description-authoring]] (trigger-noun preservation, confidence bands, clarification ceiling). This step does not replace that skill.

### 5. Surface for review (do NOT auto-register)

Present the draft inline. Do NOT write it into `catalog/skills/` or touch the three data registry files (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) until the maintainer approves. Once approved, registration follows the standard `AGENTS.md` "Register the skill" steps and `make validate` must pass.

### 6. Validate the draft

A good draft must itself pass the structural validator once placed:

```bash
python scripts/validate_skills.py --path catalog/skills/<category>/<name>/
```

And ideally clear the quality pass (`--quality --verbose`) with zero warnings.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "One commit is enough evidence to justify a skill" | A skill captures a *recurring* pattern. A single occurrence is an instinct at best (see [[continuous-learning]]), not a skill. Drafting a skill from one data point produces speculative content that fails the curation bar and clutters the catalog. Require at least a few occurrences or explicit user intent. |
| "I'll fetch related examples from the web to enrich the skill" | This skill is local-analysis-only by design. Reaching out to the web reintroduces egress and violates the MCP Registry Policy framing for reverse-engineered local capabilities. The evidence is the repo's own history; that is the whole point. |
| "I can register the draft in the data files immediately since it's obviously good" | Skills are user-facing artifacts that must clear maintainer review. Step 5 is explicit: surface, do not auto-register. Auto-committing a draft bypasses the curation bar and risks shipping an unreviewed skill. |
| "Trigger phrases can be generic; the agent will figure out when to use it" | Generic descriptions cause under-triggering (AGENTS.md "combat undertriggering"). The git history tells you exactly how the work was described in commit messages - mine those phrasings into the description so the skill actually fires when the pattern recurs. |
| "Verification can say 'the skill works'" | Not a valid criterion (AGENTS.md). Every Verification item must be an observable artifact, file path, or command. Distill them from what "done" looked like in the source commits (a passing test, a regenerated file, a green validator). |
| "I will inline the writing theory so the draft cannot miss it" | The six concepts live in `skill-description-authoring/references/agent-writing-theory.md`. Inlining them here forks the rule. Link, apply, and keep this body as the git-history procedure. |
| "A few extra 'be careful' lines in Instructions make the skill safer" | That fails the no-op test. Delete instructions the model already obeys. Safety that changes behavior is a named guardrail paired with the allowed alternative (never auto-register; surface for review). |
| "This domain needs a tutorial first" | A tutorial-shaped body leaves the agent without an execution path. Keep the body as the numbered procedure and move the textbook material to `references/`, where it loads only when a runbook step needs it. |
| "Merged commits are enough; failures are not part of the skill" | Git history is success-biased. Without a revert, follow-up fix, or user-supplied counterexample, Common Rationalizations become invented warnings rather than observed failure modes. Label the evidence and cite at least one failure. |
| "The mixed examples are obvious, so labels would be ceremony" | Unlabeled mixed traces have been measured to collapse later success. List the unlabeled items and refuse to draft until the user labels or drops them; never infer outcomes to keep moving. |

## Verification

- [ ] The candidate pattern was confirmed against concrete git evidence (commit SHAs cited), not invented.
- [ ] Every example used as draft evidence is labeled `success` or `failure`, and at least one cited failure comes from a revert, follow-up fix, or user-supplied counterexample.
- [ ] Any mixed set with unlabeled items was listed and refused before drafting; no outcome label was inferred or supplied by an outbound judge.
- [ ] The drafted SKILL.md has all four required frontmatter fields, with `summary_l0` and `overview_l1` as quoted strings within their word limits.
- [ ] The draft body has all required sections in order: When to Use (+ When NOT), Instructions, Common Rationalizations, Verification, Related Skills.
- [ ] The Instructions section is an executable runbook with numbered actions, decision rules, artifacts, gates, and verification; supporting pedagogy is linked from Tier-3 `references/` rather than taught inline.
- [ ] Every Common Rationalizations row cites a concrete failure mode; every Verification item is observable.
- [ ] No file under `catalog/skills/` and none of the three data registry files were written without explicit maintainer approval.
- [ ] When placed, the draft passes `python scripts/validate_skills.py --path <skill-dir>`.
- [ ] No outbound network call was made; all analysis used local git only.
- [ ] The draft applies all six agent-writing concepts (context pointers, two loads, leading words, negation avoidance, sediment pruning, hard/soft setup-dependency) or names the gap; the theory file is linked, not copied.

## Related Skills

- [[skill-stocktake]] - audits existing skills for quality; skill-create produces the skills it later audits.
- `/skills create` - the interactive from-scratch authoring wizard; skill-create is the git-history-driven alternative.
- [[continuous-learning]] - mints local instincts; a strong instinct cluster is the natural input to skill-create.
- [[devlog-generation]] - the same git-history-mining technique applied to producing a development log instead of a skill.
- [[create-custom-command]] - when the recurring pattern is better expressed as a slash command than a skill.
- [[skill-description-authoring]] - owns description rules and `references/agent-writing-theory.md`; this skill applies both at the draft step and does not restate them.
