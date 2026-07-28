# Research Runbook

The full per-model research procedure. `SKILL.md` carries the short form; this file carries the detail you need while actually running a pass.

## Preconditions

Check these before spending a single token:

1. **A web tool is available.** If the harness has no `WebSearch` / `WebFetch`, STOP. Log `offline: no web tool; profile layer unchanged` and return. Do not fabricate a claim, do not re-stamp `meta.last_verified`, and do not write anything. A stale-but-honest layer beats a fresh-looking invented one.
2. **The profile layer exists and validates.** Run `python scripts/verify_model_prompting_profiles.py` from the repo root. A malformed layer must be fixed before research writes into it.
3. **The user has confirmed the scale.** A full roster sweep is a 5-15x token multiplier. See "Scope-first calibration" below.

## Step 1: Enumerate the live roster

Never use a hardcoded model list. That is the exact staleness this skill exists to fix. Enumerate from the running platform's own surface via [[model-routing]]:

```bash
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.sh
bash ~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.sh <platform-id>
```

```powershell
~/.nexus-hub/skills/ai-development/model-routing/scripts/detect-platform.ps1
~/.nexus-hub/skills/ai-development/model-routing/scripts/enumerate-models.ps1 <platform-id>
```

Three outcomes, and the third is common:

| Enumeration result | `roster_source` to record | What to do |
|---|---|---|
| A JSON model list | `api` | Use it directly. |
| A config or alias set | `config` | Use it directly. |
| The picker sentinel (`{"source":"picker","models":[]}`) | `picker` | No scriptable list is available. Read the model ids from the platform's model picker and record them, tagging the provenance honestly so a later reader knows the roster was not machine-enumerated. |

Record the roster verbatim. Do not normalize, shorten, or prettify a model id: the id is the join key between this layer, the freshness checker, and the platform.

## Step 2: Build the work-list (deterministic)

Do not decide by hand which models need research. Run the planner:

```bash
python <bundle>/scripts/write_model_prompting_profile.py plan --roster <id> <id> ...
```

It returns the models that are unprofiled, carry no claims, or carry only `unverified` claims. Two useful flags:

- `--only <model>` narrows to one model. This is the scope-first calibration path and should be the first run every time.
- `--refresh-all` re-researches the whole roster, for when vendor guidance has moved rather than the roster.

## Step 3: Scope-first calibration (do not skip)

Run ONE model end to end first, then look at what it produced:

- Are the claims discrete and testable, or did the agent return paragraphs?
- Does every `source_url` resolve, and is each one a vendor primary source rather than a blog post?
- Is the `scope` tagging conservative (anything arguable sitting at `model-specific`)?

Only widen to the full roster once the answer to all three is yes, and only after confirming the scale with the user. A bad prompt fanned across a whole roster wastes the multiplier and fills the layer with claims you will have to delete.

## Step 4: Research each model

One branch per model. Each branch does two things in order.

**Find and read the vendor's own current guidance.** Search for, then actually FETCH, the model vendor's official prompting or prompt-engineering documentation, cookbook, model card or system card, and release notes or changelog. Rules:

- Never cite a page you did not open.
- Never cite a blog post, forum thread, aggregator, or secondary summary. The vendor's own documentation is the only acceptable source.
- If no primary source can be found for a model, return zero claims. A model with no profile is an honest UNVERIFIED entry; a model with an invented profile is a defect that later phases will propagate into the shared catalog.

**Extract discrete claims.** One instruction per claim, not a paragraph containing four. Each claim carries the exact primary-source URL and a `scope`. Tag `model-agnostic-candidate` ONLY when the source presents the guidance as general and not tied to this model; otherwise `model-specific`. When in doubt, choose `model-specific`. This asymmetry is deliberate and is explained in `references/schema.md`.

## Step 5: Adversarially verify before anything is written

A claim earns its place by surviving refutation, not by being plausible. Spawn independent skeptics per claim (three is the default), each prompted to REFUTE rather than confirm, and each weighing a different angle: source authority, currency, actionability. See [[adversarial-verifier]].

A claim survives only when BOTH hold:

1. It is backed by a primary source that resolves and actually supports it.
2. A majority of the skeptics fail to refute it.

Map the margin to `confidence`: unanimous survival is `high`, a two-of-three margin is `medium`, anything weaker is `low`. Never record a survivor as `unverified`; that tag is reserved for a seed or a hand-entered claim that no verify pass has examined.

**Scope may be tightened by a verifier, never loosened.** If any skeptic argues a claim is model-specific, it becomes model-specific. Moving a claim the other way (toward eligibility for a shared body) needs the stronger evidence bar, not a vote, because that direction is what ships text to every platform.

## Step 6: Write through the deterministic writer

Never hand-edit `assets/profiles-index.json` or a `references/models/*.md` mirror. Both are generated:

```bash
python <bundle>/scripts/write_model_prompting_profile.py write --input verified.json
```

The payload shape:

```json
{
  "platform": "claude-code",
  "roster_source": "api",
  "verified_at": "2026-07-27",
  "roster": ["model-a", "model-b"],
  "models": {
    "model-a": [
      {
        "claim": "One discrete, testable instruction.",
        "source_url": "https://vendor.example/docs/prompting",
        "confidence": "high",
        "scope": "model-specific"
      }
    ]
  }
}
```

The writer validates every claim and refuses the entire write on anything malformed, so a bad research result fails loudly instead of quietly degrading the layer. It re-stamps the roster and its hash, and regenerates the Markdown mirror for each model it writes. Use `--dry-run` to validate a payload without touching the layer.

Write incrementally, per model, as verification completes. That is what makes a capped or interrupted run leave a valid partial layer instead of nothing.

## Step 7: Confirm and report

After writing, re-run the structural gate and the advisory freshness check:

```bash
python scripts/verify_model_prompting_profiles.py
python scripts/check_model_prompting_freshness.py <live roster ids>
```

Report per model: claims found, claims that survived, claims refuted (and why), and the models left UNVERIFIED. Every UNVERIFIED model is a known-gaps entry, not a silent omission.

## Degradation ladder

Pick the highest rung the harness supports, and say which one you used:

| Rung | When | Shape |
|---|---|---|
| Dynamic Workflow | The workflow runtime is available and the user approved the scale | `assets/research-workflow.js`, one pipelined branch per model |
| Isolated subagents | No workflow runtime | A handful of Agent calls, one per model, verified sequentially. Same stages. |
| Single sequential agent | No subagent surface, or a very small roster | One model at a time, one stage at a time. Always available. |
| Logged no-op | No web tool | Write nothing, log the reason, leave the layer untouched. |

The stages never change across rungs. Only the concurrency does, so a degraded run produces the same shape of result more slowly, never a lower-quality one.

## Budget and the kill switch

The fan-out is the expensive part. See [[ai-billing-safeguards]] for the general treatment; the specifics here:

- **Default per-model cap**: 60k output tokens per branch, declared as `PER_MODEL_BUDGET` in `assets/research-workflow.js`.
- **Kill switch**: before each new model branch starts, the remaining turn budget is checked against a one-branch reserve. If it will not fund another branch, the run stops starting new ones, logs how many models were skipped, and returns. It never terminates mid-verification.
- **Partial results are still written**, because Step 6 writes per model as verification completes. A capped run leaves a valid, smaller layer plus a logged shortfall.
- **Raising the cap**: pass a larger turn budget (for example `+500k`), or edit `PER_MODEL_BUDGET` after stating what the new ceiling costs. Do not raise it silently.

With no turn budget set, `budget.total` is null and `budget.remaining()` is `Infinity`, so the per-model cap is the only bound. That is why the cap exists: an unbounded roster sweep is the runaway case.
