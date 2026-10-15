// =============================================================================
// research-workflow.js
//
// TEMPLATE TO ADAPT -- NOT a production script and NOT meant to run verbatim.
//
// Per-model prompting research: for each live-enumerated model, find its own
// vendor's current prompting guidance, extract discrete claims, adversarially
// verify each one against a PRIMARY source, and hand the survivors to the
// deterministic writer so they land schema-valid in the profile layer.
//
// Adapted from the canonical fan-out shape in
// catalog/skills/orchestration/agent-orchestration-primitives/assets/example-fanout-workflow.js.
// See [[agent-orchestration-primitives]] for whether a fan-out is warranted at
// all before adapting this.
//
// -----------------------------------------------------------------------------
// RULE 1 -- GRACEFUL DEGRADATION (REQUIRED)
//
// Dynamic Workflows is a plan-gated research-preview capability and may be
// absent in the user's harness. NEVER hard-depend on it. Degrade in order of
// decreasing surface:
//   1. Dynamic Workflow (this file) -- one research branch per model.
//   2. Isolated subagents -- a handful of Agent calls, one per model, verified
//      sequentially. Same stages, no pipeline runtime.
//   3. A single sequential agent -- one model at a time, one stage at a time.
//      This is the smallest surface and is always available.
// And one more rung below all three: OFFLINE. When the harness has no web tool,
// this workflow is a LOGGED NO-OP. It must not fabricate a claim, must not
// re-stamp `meta.last_verified`, and must not write anything. Log
// "offline: no web tool; profile layer unchanged" and return.
//
// -----------------------------------------------------------------------------
// RULE 2 -- SCOPE-FIRST TOKEN CAUTION (REQUIRED)
//
// A full roster fan-out is token-heavy (a 5-15x multiplier plus per-agent
// overhead), and each branch does web search + fetch + N refuters.
//   1. CALIBRATE ON ONE MODEL FIRST. Run the planner with `--only <model>`,
//      inspect the profile it produces, and confirm the claims are the shape
//      you want before widening.
//   2. Review the execution plan on the FIRST trigger -- confirm the work-list
//      and the per-model prompt before fanning out.
//   3. Confirm with the user before going full-scale across the whole roster.
// Pair this with the hard budget controls below and see [[ai-billing-safeguards]].
//
// -----------------------------------------------------------------------------
// RULE 3 -- SKILL-NATIVE (REQUIRED)
//
// This template introduces NO new outbound call, NO dependency, and NO
// credential. Web access is the agent's own WebSearch / WebFetch tool, which is
// why the MCP Registry Policy is not engaged. The subagents it spawns use only
// the harness's own tools plus the bundled deterministic writer.
// =============================================================================

export const meta = {
  name: 'model-prompting-research',
  description: 'Research, verify, and record current prompting guidance per live model',
  phases: [
    { title: 'Research', detail: 'search + fetch each model vendor primary sources' },
    { title: 'Verify', detail: 'independent refuters per candidate claim' },
    { title: 'Record', detail: 'hand survivors to the deterministic writer' },
  ],
}

// ---------------------------------------------------------------------------
// Budget cap and kill switch (RULE 2's teeth -- see [[ai-billing-safeguards]])
// ---------------------------------------------------------------------------
// DEFAULT CAP: 60k output tokens per model branch. With no `+Nk` budget
// directive from the user, `budget.total` is null and `budget.remaining()` is
// Infinity, so PER_MODEL_BUDGET is the only thing bounding the run -- that is
// deliberate, because an unbounded roster sweep is the runaway case.
// TO RAISE IT: the user passes a larger turn budget (e.g. "+500k"), or you edit
// PER_MODEL_BUDGET here after saying what the new ceiling costs.
const PER_MODEL_BUDGET = 60_000
// Stop starting NEW model branches once the remaining turn budget cannot fund
// one. This is the kill switch: it terminates the fan-out GRACEFULLY, and every
// model already verified has been written, so a capped run leaves a valid
// partial layer rather than nothing.
const RESERVE = PER_MODEL_BUDGET

const CLAIMS_SCHEMA = {
  type: 'object',
  required: ['model', 'claims'],
  properties: {
    model: { type: 'string' },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'source_url', 'scope'],
        properties: {
          claim: { type: 'string' },
          source_url: { type: 'string' },
          // The hard rail. Default to model-specific whenever it is unclear
          // whether the guidance generalizes: a model-specific claim parked in
          // the profile layer is merely unhelpful to other models, whereas a
          // wrongly-generalized one ships to every platform.
          scope: { enum: ['model-specific', 'model-agnostic-candidate'] },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['refuted', 'reason'],
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
    // A verifier may DOWNGRADE scope but never upgrade it: moving a claim from
    // model-specific to model-agnostic-candidate makes it eligible for a shared
    // body, so that direction requires the stronger evidence bar, not a vote.
    scope: { enum: ['model-specific', 'model-agnostic-candidate'] },
  },
}

// ADAPT: the work-list. Workflow scripts have NO filesystem access, so the
// CALLER scouts it first (the scope-first path) by running:
//   python <bundle>/scripts/write_model_prompting_profile.py plan --roster <live ids>
// and passing the resulting `targets` array in as `args`. Enumerate the live
// roster via the model-routing skill's enumerate-models helper -- never a
// hardcoded model list, which is the whole reason this feature exists.
const targets = Array.isArray(args) ? args.filter(Boolean) : []
if (!targets.length) {
  log('no research targets supplied; run the planner first (scope-first path)')
  return { researched: [], written: [], skipped: 'no targets' }
}
log(`${targets.length} model(s) queued for research`)

const verifiedByModel = []
const skipped = []

phase('Research')
const results = await pipeline(
  targets,
  // ---- Stage 1: find and read the vendor's own current guidance -----------
  // Kill switch: check the budget BEFORE starting each branch, so the run stops
  // cleanly at the ceiling instead of dying mid-verification.
  (model) => {
    if (budget.total && budget.remaining() < RESERVE) {
      skipped.push(model)
      log(`budget reached; skipping ${model} (${skipped.length} model(s) unresearched)`)
      return null
    }
    return agent(
      `Research how to prompt the model "${model}" effectively, using ONLY that ` +
        `model vendor's own primary sources: official prompting / prompt-engineering ` +
        `docs, the cookbook, the model card or system card, and the release notes ` +
        `or changelog. Search the web, then FETCH each page you cite and read it -- ` +
        `never cite a page you did not open, and never cite a blog post, forum, or ` +
        `secondary summary. Extract DISCRETE, testable claims (one instruction per ` +
        `claim, not a paragraph). For each claim record the exact primary-source URL ` +
        `and a scope: "model-agnostic-candidate" ONLY if the source presents it as ` +
        `general prompting guidance that is not tied to this model, otherwise ` +
        `"model-specific". When in doubt, choose "model-specific". If you cannot ` +
        `find primary sources for this model, return an empty claims array rather ` +
        `than guessing.`,
      { label: `research:${model}`, phase: 'Research', schema: CLAIMS_SCHEMA },
    )
  },
  // ---- Stage 2: adversarially verify each claim, in parallel -------------
  // No barrier between stages: model B is still searching while model A's
  // claims are already being refuted. See [[adversarial-verifier]].
  (found, model) => {
    if (!found || !found.claims || !found.claims.length) {
      log(`${model}: no primary-source claims found; leaving UNVERIFIED`)
      return { model, claims: [] }
    }
    return parallel(
      found.claims.map((c) => () =>
        // Three independent skeptics per claim, each prompted to REFUTE. A claim
        // survives only on a primary source AND a majority failing to refute it.
        parallel(
          [0, 1, 2].map((i) => () =>
            agent(
              `Try to REFUTE this prompting claim about the model "${model}":\n` +
                `  claim: ${c.claim}\n  cited source: ${c.source_url}\n\n` +
                `Refute it if ANY of these hold: the cited URL does not resolve or ` +
                `does not actually support the claim; the claim contradicts the ` +
                `vendor's current documentation; the claim is stale guidance from an ` +
                `older model generation; or it is too vague to act on. Angle ${i + 1} ` +
                `of 3 -- weigh source authority, currency, and actionability in that ` +
                `order respectively. Default to refuted=true when uncertain.`,
              { label: `refute:${model}`, phase: 'Verify', schema: VERDICT_SCHEMA },
            ),
          ),
        ).then((votes) => {
          const cast = votes.filter(Boolean)
          const survived = cast.length && cast.filter((v) => !v.refuted).length > cast.length / 2
          if (!survived) return null
          // Confidence follows the margin, so a barely-surviving claim is recorded
          // as such rather than presented with the same weight as a unanimous one.
          const clean = cast.filter((v) => !v.refuted).length
          const confidence = clean === cast.length ? 'high' : clean >= 2 ? 'medium' : 'low'
          // Scope can only ever be tightened by a verifier, never loosened.
          const downgraded = cast.some((v) => v.scope === 'model-specific')
          return {
            claim: c.claim,
            source_url: c.source_url,
            confidence,
            scope: downgraded ? 'model-specific' : c.scope,
          }
        }),
      ),
    ).then((claims) => ({ model, claims: claims.filter(Boolean) }))
  },
)

for (const r of results.filter(Boolean)) {
  if (r.claims.length) verifiedByModel.push(r)
  else log(`${r.model}: no claim survived verification; leaving UNVERIFIED`)
}

// ---- Stage 3: hand the survivors to the deterministic writer --------------
// The workflow does NOT write files itself. It returns the payload, and the
// caller runs, once per model or once for the batch:
//   python <bundle>/scripts/write_model_prompting_profile.py write --input <payload>
// That script validates every claim and rewrites the index + mirrors atomically,
// so the layer is schema-valid by construction and a capped run still leaves a
// valid partial layer.
phase('Record')
const payload = {
  platform: '<the platform id the roster was enumerated from>',
  roster_source: '<api | picker | config | manual>',
  // The workflow runtime has no clock and no RNG (they would break resume), so
  // the caller stamps the date and passes it in.
  verified_at: '<YYYY-MM-DD, stamped by the caller>',
  models: Object.fromEntries(verifiedByModel.map((r) => [r.model, r.claims])),
}
log(
  `${verifiedByModel.length} model(s) verified, ${skipped.length} skipped at the budget cap`,
)

return {
  payload,
  researched: targets,
  written: verifiedByModel.map((r) => r.model),
  unverified: targets.filter((m) => !verifiedByModel.some((r) => r.model === m)),
  skippedAtCap: skipped,
}
