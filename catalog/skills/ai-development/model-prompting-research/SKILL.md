---
name: model-prompting-research
description: "Refresh stale prompting conventions as new models ship: web-verify per-model guidance into a bundled profile layer, then tune model-agnostic authoring. For 'a new model shipped', 'tune prompting for X'. SKIP choosing a model (model-routing)."
summary_l0: "Research and verify current per-model prompting guidance, then tune the catalog to it"
overview_l1: "This skill keeps a skill catalog current as models ship. It enumerates the live model roster from the running platform (never a hardcoded list), fans a research branch out per model to read that vendor's own prompting docs, cookbook, model card, and changelog, and extracts discrete claims. Every claim must survive an adversarial refutation pass backed by a primary source before it is recorded, so plausible-but-unsourced guidance never lands. Verified claims are written by a deterministic script into a bundled per-model profile layer, schema-valid by construction. Model-specific guidance is confined to that layer by a hard rail; only genuinely model-agnostic authoring improvements are ever eligible to touch a shared body. Web access is the agent's own search and fetch tools, so no MCP server, dependency, or credential is introduced. Trigger phrases: a new model shipped, tune prompting for this model, refresh our prompting conventions, are our prompts stale."
version: 1.0.0
author: Benjamin Dourthe
license: MIT
category: ai-development
language: Multi-language
tags: [prompting, model-research, web-verification, catalog-maintenance, profiles, adversarial-verification]
tools_required: [Read, Write, Edit, Bash, WebSearch, WebFetch]
---

# Model-Prompting Research

Every model release quietly shifts what "good prompting" means, and a skill catalog authored against last year's conventions drifts out of date without anyone noticing. This skill closes that loop: it learns, from each current model's own vendor documentation, how that model wants to be prompted, proves each finding against a primary source, and records it somewhere the catalog can actually use.

The discipline that makes it safe is a split between two kinds of finding. Guidance that is true of ONE model goes into a per-model profile layer bundled with this skill and nowhere else. Guidance that is genuinely model-agnostic is the only kind ever eligible to change a shared body (a `SKILL.md`, a command, a `base-*.md` template), and even then only behind the repo's own guard suite. Anything ambiguous is treated as model-specific. That asymmetry is the whole safety story, because a shared body is distributed verbatim to every platform, so one model-named line there is wrong for every reader running something else.

## When to Use This Skill

Use this skill when:

- A new model has shipped and you want the catalog's prompting conventions checked against it.
- You want to know how to prompt one specific current model, sourced from that vendor rather than from memory.
- Someone asks whether the prompting guidance in the catalog is stale, or asks to refresh it.
- A release step reports that the recorded model roster has drifted from the live one.

**When NOT to use this skill**:

- Choosing WHICH model or reasoning effort a task should run on: use [[model-routing]]. That skill picks a model; this one researches how to prompt the models you already have.
- Designing, testing, or optimizing a single prompt for an application: use [[prompt-engineering]]. This skill produces catalog-wide guidance, not one tuned prompt.
- Checking consumption against a usage limit: use `/usage`. Capping autonomous spend: use [[ai-billing-safeguards]].
- Re-verifying each platform's file discovery paths before a release: use [[platform-contract-verification]]. That is a different staleness problem with a different (blocking) gate.

## How it works

```
enumerate live roster  ->  plan work-list  ->  per model: search + fetch primary sources
                                                    |
                                          extract discrete claims
                                                    |
                                    adversarially refute each claim (3 skeptics)
                                                    |
                              survivors only  ->  deterministic writer  ->  profile layer
```

The two ends of that pipeline are deliberately NOT agent work. Choosing which models need research, and writing the result, both run through `scripts/write_model_prompting_profile.py`, so the work-list is reproducible and the written layer is schema-valid by construction. The middle (search, read, judge, refute) is the part that genuinely needs an agent.

## Instructions

The full procedure, including the exact prompts, the payload shape, and the enumeration edge cases, is in `references/research-runbook.md`. Read it before running a pass. The short form:

1. **Check you can actually research.** No web tool means STOP: log the reason, write nothing, and leave the layer untouched. A stale-but-honest layer beats an invented one.
2. **Enumerate the live roster** via [[model-routing]]'s `enumerate-models` helper. Never a hardcoded list, which is the staleness this skill exists to fix. Record the provenance (`api`, `picker`, `config`, or `manual`) honestly.
3. **Build the work-list deterministically**: `write_model_prompting_profile.py plan --roster <ids>` returns the models that are unprofiled or carry only unverified claims.
4. **Calibrate on ONE model first** (`plan --only <model>`), inspect what it produced, and confirm the scale with the user before widening. A roster fan-out is a 5-15x token multiplier.
5. **Research each model** against that vendor's own primary sources only: official prompting docs, cookbook, model card or system card, changelog. Never cite a page you did not fetch, and never cite a secondary summary. No primary source found means zero claims, not a guess.
6. **Adversarially verify before recording.** A claim survives only when a primary source supports it AND a majority of independent skeptics fail to refute it. Confidence follows the margin. See [[adversarial-verifier]].
7. **Write through the deterministic writer**, per model as verification completes, then re-run the structural gate. Report every model left unverified as a known gap rather than omitting it silently.

### The hard rail

Each claim carries a `scope`, and that field alone decides where it may be written:

| `scope` | May write to | May NOT write to |
|---|---|---|
| `model-specific` | the profile layer | any shared body, ever |
| `model-agnostic-candidate` | the profile layer, and eligible to PROPOSE a shared-body edit behind the guard suite | a shared body directly, without the guards |

Ambiguity resolves to `model-specific`. A verifier may tighten a claim's scope but never loosen it: moving a claim toward shared-body eligibility needs a stronger evidence bar, not a majority vote. `scripts/check_base_template_parity.py` is what makes the rail physical, since a model-named line that diverges across the five `base-*.md` templates fails the build.

### Running the fan-out, and degrading when you cannot

`assets/research-workflow.js` is a Dynamic-Workflow TEMPLATE to adapt, not a script to run verbatim. It carries the three mandatory rules inline (graceful degradation, scope-first token caution, skill-native). Degrade in order: Dynamic Workflow, then isolated subagents, then a single sequential agent, then a logged no-op when there is no web tool. The stages never change across rungs, only the concurrency, so a degraded run is slower rather than worse. Say which rung you used. See [[agent-orchestration-primitives]] for whether a fan-out is warranted at all.

### Budget and the kill switch

The default cap is **60k output tokens per model branch** (`PER_MODEL_BUDGET` in the workflow template). Before each new branch starts, the remaining turn budget is checked against a one-branch reserve; if it will not fund another, the run stops starting branches, logs how many models were skipped, and returns. It never dies mid-verification, and because writes happen per model, a capped run leaves a valid partial layer plus a logged shortfall. Raise the cap by passing a larger turn budget or by editing the constant after stating what the new ceiling costs, never silently. See [[ai-billing-safeguards]].

## Bundled resources

| File | What it is |
|---|---|
| `references/research-runbook.md` | The full procedure: enumeration, calibration, prompts, verification bar, payload shape, degradation ladder, budget |
| `references/schema.md` | The profile-layer contract: index schema, claim fields, and why ambiguity resolves to model-specific |
| `references/models/claude-opus-5.md` | A per-model profile mirror, human-readable, generated from the index |
| `assets/profiles-index.json` | The authoritative machine index: roster, roster hash, freshness marker, and every claim |
| `assets/research-workflow.js` | The Dynamic-Workflow fan-out template to adapt |
| `scripts/write_model_prompting_profile.py` | The deterministic planner (`plan`) and writer (`write`) |

Two repo-level scripts sit alongside the bundle: `verify_model_prompting_profiles.py` is the structural hard gate that runs in `make validate`, and `check_model_prompting_freshness.py` is the advisory roster-drift check that is deliberately never a blocking gate.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This tip is great for everyone, so I'll put it straight in the shared skill body." | That ships a model-named line to every platform, where it is wrong for every reader running a different model, and it trips `check_base_template_parity.py` the moment the five `base-*.md` files diverge. Model-specific guidance goes in the profile layer; the shared-body path exists but runs behind the guard suite. |
| "I know the current model list, so I'll skip enumeration." | A hardcoded roster is exactly the failure this skill was built to fix. Model catalogs move within weeks, and a stale list silently researches models that no longer exist while missing the one that just shipped. |
| "The claim is obviously true, so it doesn't need a source." | An unsourced claim is indistinguishable from a hallucinated one once it is in the layer, and every later phase treats recorded claims as verified input. The whole pipeline is built so a claim earns its place by surviving refutation, not by sounding right. |
| "I couldn't find primary docs for this model, so I'll write what I know about it." | That converts a visible gap (an UNVERIFIED model, which is tracked and non-blocking) into an invisible defect that later phases may propagate into the shared catalog. Zero claims is the correct output. |
| "A blog post explains it more clearly than the vendor docs." | Clarity is not authority. A secondary source can be stale, wrong, or describing a different model generation, and the citation recorded in the layer is what a future reader will trust. Vendor primary sources only. |
| "I'll fan out across the whole roster immediately to save a round-trip." | A roster sweep is a 5-15x multiplier, and a bad prompt fanned across every model wastes all of it and fills the layer with claims you then have to delete. Calibrating on one model first is cheaper than one wasted sweep. |
| "The run hit the budget cap, so I'll drop the partial results." | Writes happen per model as verification completes, so the partial layer is already valid and already useful. Discarding it throws away paid-for work; the correct action is to log the shortfall and record the skipped models as gaps. |

## Verification

- [ ] The roster came from a live enumeration, and `meta.roster_source` records how it was obtained.
- [ ] Every recorded claim carries a primary-source URL that was actually fetched, and no claim cites a blog post, forum, or secondary summary.
- [ ] Every recorded claim survived the refutation pass, and its `confidence` reflects the margin (no survivor is tagged `unverified`).
- [ ] Every claim whose generality is arguable is tagged `model-specific`, and no verifier loosened a scope.
- [ ] The layer was written by `scripts/write_model_prompting_profile.py`, not hand-edited, and `python scripts/verify_model_prompting_profiles.py` exits 0 afterwards.
- [ ] Every rostered model with no surviving claim is reported as UNVERIFIED rather than omitted.
- [ ] The degradation rung actually used is stated, and an offline run wrote nothing and re-stamped nothing.
- [ ] No new outbound call, dependency, or credential was introduced; web access was the agent's own search and fetch tools.

## Related Skills

- [[model-routing]] -- enumerates the live model roster this skill researches, and is the skill to use when the question is which model to run, not how to prompt it.
- [[adversarial-verifier]] -- the refute-before-record discipline that gates every claim.
- [[ai-billing-safeguards]] -- the hard budget controls behind the per-model cap and kill switch.
- [[agent-orchestration-primitives]] -- decides whether the fan-out is warranted before the template is adapted.
- [[prompt-engineering]] -- designing and optimizing one prompt for an application; this skill produces catalog-wide guidance instead.
- [[platform-contract-verification]] -- the same "re-verify against a moving external reality" shape, applied to platform read-paths, but with a blocking gate rather than an advisory one.

---

**Version**: 1.0.0
**Last Updated**: July 2026
