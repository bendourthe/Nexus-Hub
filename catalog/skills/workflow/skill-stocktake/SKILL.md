---
name: skill-stocktake
description: Audit Nexus-Hub skills for quality - frontmatter completeness, binary Verification, Common Rationalizations depth, Tier-1 field length, and Related-Skills wiring - combining a deterministic checklist with the agent's holistic judgment, and caching results so re-runs only re-score changed skills. Make sure to use this skill whenever the user says "audit our skills", "stocktake the catalog", "which skills are low quality", "are our skills up to standard", "review skill quality", "score the skills", "find weak skills", "quality pass on the catalog", or otherwise asks for a quality assessment across one or many SKILL.md files rather than a structural pass/fail. Also trigger before a release when the user wants a quality snapshot of the catalog, or after a batch of new skills lands and someone asks "are these any good". SKIP, do NOT use for, structural validation that only needs pass/fail (use scripts/validate_skills.py directly), writing or editing a single new skill (use create-skill-or-command), or generating a brand-new skill from git history (use skill-create).
summary_l0: "Holistic skill-quality audit with a cached results file and quick-diff re-scoring over changed skills"
overview_l1: "Defines a two-mode quality audit for Nexus-Hub SKILL.md files. Quick Scan reads a cached .nexus/skill-stocktake/results.json, recomputes a per-skill content hash, and re-scores only skills whose hash changed since the last run, so an audit after a small edit is near-instant. Full Stocktake scores every skill and rewrites the cache. Each skill gets a deterministic checklist score (required frontmatter, tight Tier-1 fields, binary Verification, Common Rationalizations with concrete failure modes, Related Skills links, body within the size norm) plus a short holistic judgment on whether the body teaches a real procedure. The deterministic half reuses scripts/validate_skills.py --quality rather than re-implementing heuristics. Output is a worst-first ranked report and the refreshed cache. Trigger phrases: audit our skills, stocktake the catalog, score the skills, which skills are low quality."
version: 1.0.0
author: Benjamin Dourthe
category: workflow
tags:
  - skill-quality
  - audit
  - catalog-health
  - quality-gate
  - caching
---

# Skill Stocktake

Audit Nexus-Hub skills for quality, not just structure. `scripts/validate_skills.py` answers "does this skill parse and have the required fields"; this skill answers "is this skill any good": does its body teach the agent what to do, are its Common Rationalizations real failure modes, is its Verification observable, and are its Tier-1 fields tight. It pairs a deterministic checklist (the `--quality` pass of the validator) with the agent's holistic reading, and caches per-skill results so repeat runs only re-score what changed.

This is the local-only reverse-engineered analogue of ECC's `skill-stocktake` holistic-audit pattern. The content is re-authored to Nexus-Hub's own frontmatter and quality conventions (see `AGENTS.md` "Write SKILL.md"); no upstream text is copied.

## When to Use This Skill

Use when:

- The user asks for a quality assessment across the catalog or a subset of skills ("audit our skills", "which skills are weak", "score the skills").
- A batch of new or re-authored skills just landed and you want a worst-first ranking before merge.
- You are preparing a release and want a quality snapshot of the catalog alongside the structural `make validate` gate.
- A prior stocktake exists and you only want to re-score the handful of skills that changed since (Quick Scan).

**When NOT to use:**

- You only need a structural pass/fail - run `python scripts/validate_skills.py` directly; it is faster and is the CI gate.
- You are authoring or editing one specific skill - use `/skills create`.
- You want to draft a new skill from recurring git-history patterns - use [[skill-create]].

## Cache Layout

The cache is project-scoped and local. Nothing leaves the machine.

| Path | Written by | Read by | Lifecycle |
|---|---|---|---|
| `.nexus/skill-stocktake/results.json` | this skill (both modes) | this skill (Quick Scan) | Persistent; rewritten each Full Stocktake. Safe to delete to force a clean run. |
| `.nexus/skill-stocktake/report.md` | this skill | humans | Regenerated on every run. |

`results.json` shape (one record per skill):

```json
{
  "schema": 1,
  "generated": "2026-05-28",
  "skills": {
    "catalog/skills/workflow/skill-create/SKILL.md": {
      "hash": "sha256:abcd...",
      "checklist_score": 7,
      "checklist_max": 8,
      "warnings": ["quality: missing '## Common Rationalizations' section"],
      "holistic": "Verification is binary and observable; rationalizations are concrete. Body slightly thin on the evolve step."
    }
  }
}
```

## Instructions

### 1. Decide the mode

- **Quick Scan** (default when `results.json` exists): re-score only skills whose content hash changed.
- **Full Stocktake**: score every skill and rewrite the cache. Use when there is no cache, the schema changed, or the user asks for a complete run.

### 2. Run the deterministic checklist

Do NOT re-implement quality heuristics in the skill body. Run the validator's quality pass and capture its per-skill warnings:

```bash
python scripts/validate_skills.py --quality --verbose
```

This emits warnings (never errors) for: missing Common Rationalizations table, prose-only (non-binary) Verification, over-long `summary_l0` (> 15 words) or `overview_l1` (> 150 words), and missing Related Skills links. Each warning is one checklist miss. The deterministic checklist score is `checklist_max - (number of quality warnings for that skill)`.

For a single skill or a subdirectory, scope it: `python scripts/validate_skills.py --quality --verbose --path catalog/skills/workflow/`.

### 3. Compute the change set (Quick Scan only)

For each skill, compute a content hash of `SKILL.md` (and its `references/*.md` if present). Compare against `results.json`. A skill is "changed" if its hash differs or it is absent from the cache. In Quick Scan, only changed skills proceed to step 4; unchanged skills keep their cached record.

### 4. Add holistic judgment

For each changed (or all, in Full Stocktake) skill, read the body and write a 1-3 sentence holistic assessment answering:

- Does the Instructions section actually teach the agent a procedure, or is it vague prose?
- Are the Common Rationalizations entries real failure modes with concrete rebuttals (per `AGENTS.md`: "Each entry must cite a concrete failure mode, not a generic principle")?
- Is every Verification item an observable artifact or state (a file path, a command, a count), not "the code looks good"?
- Is the body within the size norm (target <= 500 lines, soft cap 800)?

The holistic note is the agent's own words, not a score. Keep it terse.

### 4b. Directive-density review (advisory)

A skill can pass every structural check, read well, and still not change what the agent does. That skill explains a domain instead of instructing an agent, and the deterministic checklist cannot see it because nothing is missing - the sections are all present and full of competent prose.

Sample each substantial section of the body (a section with more than roughly 10 lines; cap at 8 sections per skill to keep this bounded) and ask one binary question:

> Does this section yield at least one **observable action**, **decision rule**, **artifact**, **gate**, or **verification condition** that changes what the agent does?

| Signal | Example of what counts |
|---|---|
| Observable action | "Run `python scripts/validate_skills.py --quality`" |
| Decision rule | "Pairwise is the default; move to 3-tuple only for a suspected interaction" |
| Artifact | "Write `.nexus/skill-stocktake/results.json` with one record per skill" |
| Gate | "Reject the batch wholesale if the spot-check error rate is high" |
| Verification condition | "The held-out split was evaluated against exactly once" |

Record a section as **directive** if any one is present, **expository** if none is. Report the count and name the expository sections, for example: `6 of 7 substantial sections directive; "Background on retrieval" is expository`. A skill where most substantial sections are expository is a candidate for rewriting toward instruction, or for demotion to a Tier-3 reference where explanation is the point.

When a `language-specialists/*-expert` skill, or a similarly shaped `framework-specialists/*-expert` skill, has mostly expository substantial sections, label it `runbook-backlog` in the report. Propose a later edit that keeps executable procedure in SKILL.md and moves pedagogy to `references/`; do not rewrite the expert skill during the stocktake and do not turn this advisory label into a `make validate` failure.

This is an **advisory quality signal, not a gate**. It never fails a run, never blocks a merge, and never produces a numeric threshold anyone can tune against.

**Non-goals - do not do these:**

- **Do not compute an imperative-verb ratio or any word-count metric.** A binary per-section question is deliberate. A density score invites optimizing prose toward the score, which degrades skills.
- **Concise rationale that explains a failure mode is not slop, and must not be removed to raise directive density.** The "Reality" column of a Common Rationalizations table is explanatory by design and is the most valuable prose in the schema; AGENTS.md requires each entry to cite a concrete failure mode. A section that pairs one sentence of why with an observable instruction is the target state, not a violation of it.
- **Do not flag Tier-3 reference files.** Under the three-tier model, `references/*.md` exist to carry the explanation that does not belong in the body. Expository prose there is correct.
- **Do not remove or shorten the required Common Rationalizations or Verification sections** on the strength of this signal. Their presence is a checklist item; this review never argues for their deletion.

### 4c. Audit semantic confusability

Build a lowercase trigger-noun index from each scored skill's `description` plus its `SKIP` fence. Compare candidates through shared noun buckets rather than constructing a catalog-wide all-pairs matrix.

- **Quick Scan**: compare each changed skill with every other skill in the same category.
- **Full Stocktake**: start with the lowest-checklist skills in each category, then add any same-category skill that shares two or more trigger nouns with another skill in the noun index. Compare only those candidates. Do not compare every pair in the catalog.
- **Always-run cross-category watchlist**: inspect `anti-slop-editing` versus `typed-boundary-hygiene` for anti-slop vernacular, `typed-boundary-hygiene` versus `typescript-expert` for unknown and boundary language, and `javascript-cleanup` versus `typed-boundary-hygiene` for cleanup language.

Calibrate a Full Stocktake on `language-specialists` first. It must name the `typed-boundary-hygiene` / `typescript-expert` split and state whether their `SKIP` fences separate contract hygiene from general type design and I/O parsing. Fan out only after that report shape is useful; [[agent-orchestration-primitives]] is optional when the active harness supports it.

Write a `## Confusable clusters` section in `.nexus/skill-stocktake/report.md`. For every real candidate, record skill A, skill B, overlapping phrases, whether their `SKIP` fences separate ownership, and one proposed description or `SKIP` repair. Propose repairs only. Never delete a skill, never auto-edit either description, and never turn this advisory pass into a `validate_skills.py` error.

### 5. Write the cache and the report

Write the refreshed `results.json` and a worst-first `report.md`: rank skills by checklist score ascending (ties broken by holistic severity), one row per skill with score, warnings, and the holistic note. Surface the bottom 10 prominently.

### 6. Propose remediation (do not auto-edit)

For the lowest-scoring skills, propose specific fixes (add a Common Rationalizations table, convert prose Verification to checkboxes, tighten `summary_l0`). Never silently rewrite a skill - surface the proposal and let the maintainer decide.

## Agent-setup grade (companion signal)

The per-skill stocktake above scores individual SKILL.md files. For a quick whole-setup health signal alongside it, `scripts/harness_audit.py` emits a single explainable 1-100 agent-setup grade plus a cross-snapshot regression guard. Use it during a release stocktake as a fast catalog-health check, not a replacement for the per-skill pass.

- `python scripts/harness_audit.py grade` prints the grade with a per-dimension breakdown (registry consistency, skill-frontmatter conformance, security-hook presence and registration, instruction-file presence, hook-reference integrity, and data-registry JSON health), each with its weight, sub-score, and a one-line reason.
- `python scripts/harness_audit.py snapshot` writes that graded setup to a local baseline at `.nexus/harness-audit/latest.json` (gitignored, same local-tooling convention as this skill's cache).
- `python scripts/harness_audit.py diff` compares the current setup against the latest snapshot and reports each dimension as improved / unchanged / regressed plus the overall grade delta, so a change that quietly degrades the setup becomes visible.

Both the grade and the diff are advisory by default: they print and exit 0 regardless of score. Only `diff --fail-on-regression` opts a CI job into a gate. Pair this whole-setup grade with [[skill-security-scan]] for per-skill security findings and the benchmark loop in [[skill-eval-loop]] for a fuller catalog-health picture.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "validate_skills.py already passes, so the skills are fine" | Structural validation only checks that required fields exist and parse. A skill can pass structurally and still have a prose-only Verification ("the implementation looks correct"), a Common Rationalizations table full of generic platitudes, or a 200-word summary_l0. Those are exactly the gaps the quality pass surfaces and the structural gate does not. |
| "I'll re-implement the quality heuristics here so the skill is self-contained" | That duplicates logic that lives in scripts/validate_skills.py --quality and the two will drift. The skill MUST shell out to the validator for the deterministic half; the skill's unique value is the holistic judgment and the caching, not re-coded regexes. |
| "Full Stocktake every time is simpler than maintaining a cache" | On a 200+ skill catalog a full holistic pass is expensive. The cache + content-hash diff is the whole point of the ECC pattern: a re-run after one edit re-scores one skill, not 216. Skipping the cache makes the skill too slow to run routinely, so it stops being run. |
| "A low checklist score means the skill should be deleted" | No. A low score means the skill needs the missing sections added. Deletion requires maintainer approval (AGENTS.md "Never do: Delete existing skills without maintainer approval"). The stocktake proposes remediation; it does not prune. |
| "I can edit the worst skills automatically since the fixes are mechanical" | Step 6 is propose-only. Adding a Common Rationalizations table or rewriting Verification changes user-facing content that must clear the curation bar. Surface the diff; let the maintainer approve. |
| "Directive density would be more objective as an imperative-verb ratio" | A ratio is tunable, and prose optimized toward it gets worse: the first casualty is the "Reality" column of the Common Rationalizations table, which is explanatory by design and is the most valuable prose in the schema. Step 4b asks a binary per-section question precisely so there is no number to game. |
| "This section is mostly explanation, so it should be cut to raise directive density" | Explanation that names a concrete failure mode is what makes an instruction followable; AGENTS.md requires it. The target state is one sentence of why paired with an observable instruction, not instructions with the why stripped out. Cutting rationale to raise a signal that was never a gate is the failure mode 4b's non-goals exist to prevent. |
| "The safest confusability audit compares every skill with every other skill" | A global all-pairs pass makes routine stocktakes unusable as the catalog grows. The noun index narrows comparisons to changed or low-scoring same-category candidates, while the named cross-category watchlist preserves known vernacular collisions. |
| "Confusable skills should be merged or deleted" | Overlap is evidence for a clearer ownership fence, not deletion authority. The report proposes a description or `SKIP` repair; only a maintainer can approve a skill removal. |

## Verification

- [ ] `python scripts/validate_skills.py --quality --verbose` runs and exits 0 (quality warnings never fail the run).
- [ ] `.nexus/skill-stocktake/results.json` exists, is valid JSON, and has one record per scored skill with `hash`, `checklist_score`, `warnings`, and `holistic` fields.
- [ ] In Quick Scan, a skill whose `SKILL.md` is unchanged since the last run keeps its prior cached record (its `hash` matches and it was not re-scored).
- [ ] `.nexus/skill-stocktake/report.md` exists and lists skills worst-first by checklist score.
- [ ] No `.nexus/` file is written outside the project root, and no network call is made.
- [ ] No SKILL.md is edited by the stocktake itself; remediation is proposed, not applied.
- [ ] The directive-density review reports a directive/expository count per scored skill and names the expository sections, without emitting any ratio, threshold, or pass/fail verdict.
- [ ] Mostly expository language- or framework-specialist expert skills are labeled `runbook-backlog` with a later Tier-3 migration proposal, without being rewritten or failed by validation.
- [ ] No Common Rationalizations or Verification section was removed or shortened as a result of the directive-density signal, and no `references/*.md` file was flagged by it.
- [ ] `.nexus/skill-stocktake/report.md` contains `## Confusable clusters` with each candidate pair, overlapping phrases, fence verdict, and proposed repair.
- [ ] Quick Scan compares changed skills only against their category; Full Stocktake uses the lowest-score plus two-shared-noun candidate set rather than a catalog-wide all-pairs matrix.
- [ ] The always-run watchlist includes anti-slop, unknown/boundary, and cleanup vernacular, and the language-specialists calibration names `typed-boundary-hygiene` versus `typescript-expert`.
- [ ] Confusability remains advisory: no skill was deleted or auto-edited, and no `validate_skills.py` hard error was added.

## Related Skills

- [[skill-create]] - drafts a new skill from git history; stocktake audits skills that already exist.
- `/skills create` - the interactive authoring wizard; stocktake feeds it the list of skills that need work.
- [[continuous-learning]] - mints local instincts and draft skills; stocktake is the quality gate those drafts must clear.
- [[code-quality]] - the same quality-over-structure philosophy applied to source code instead of skills.
- [[known-gaps-tracker]] - low-scoring skills that are not fixed this pass become tracked gaps.
- [[skill-security-scan]] - per-skill security adjudication; the harness-audit setup grade folds security-hook presence into a whole-setup signal.
- [[skill-eval-loop]] - benchmark a single skill against a baseline; the setup grade is the catalog-wide companion to that per-skill loop.
