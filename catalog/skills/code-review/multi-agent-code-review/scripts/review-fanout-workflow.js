// =============================================================================
// review-fanout-workflow.js
//
// TEMPLATE TO ADAPT -- NOT a production script and NOT meant to run verbatim.
//
// An executable scaffold for the multi-agent-code-review pipeline: the
// dimensions -> find -> adversarially-verify shape. Each reviewer persona is a
// "dimension"; it returns structured findings; each surviving finding is then
// refuted by an independent agent before it reaches a human. This is the
// runnable form of Stages 3-6 of the parent SKILL.md -- copy it into a review
// flow and adapt the PERSONAS list, the two schemas, and the synthesis prompt.
//
// The two schemas below are the skill's own contracts:
//   - FINDINGS_SCHEMA mirrors references/findings-schema.md
//   - VERDICT_SCHEMA  mirrors references/validator-template.md
// Keep them in sync with those files; do not invent a parallel shape.
//
// -----------------------------------------------------------------------------
// GRACEFUL DEGRADATION (REQUIRED)
//
// Dynamic Workflows is a plan-gated research-preview capability that may be
// absent in the user's harness. NEVER hard-depend on it. When the Workflow
// runtime is unavailable, fall back, in order of decreasing surface:
//   1. dispatch the personas as a handful of isolated subagents (Stage 4 of the
//      SKILL.md run by hand), or
//   2. a single reviewer doing one sequential read-only pass (smallest surface).
// The decision guide for whether a fan-out is warranted at all is the
// agent-orchestration-primitives skill; this template does not duplicate it.
//
// -----------------------------------------------------------------------------
// SCOPE-FIRST TOKEN CAUTION (REQUIRED)
//
// A persona fan-out + per-finding verification carries a 5-15x token multiplier.
// Before running at full scale:
//   1. Calibrate on ONE module (or a <=800-line slice of the diff) first.
//   2. Review the execution plan on the FIRST trigger -- confirm the persona set
//      and the resolved diff base ref before fanning out.
//   3. Confirm with the user before reviewing the whole change set.
// Pair this with hard budget controls -- see the ai-billing-safeguards skill.
//
// -----------------------------------------------------------------------------
// SKILL-NATIVE: this template introduces no outbound call, no new dependency,
// and no credential. The subagents it spawns use only the harness's own local
// read tools over the local diff and the local agent definitions.
// =============================================================================

// The phase titles here must match the phase() strings used in the body below.
export const meta = {
  name: 'review-fanout-verify',
  description: 'Review a diff across reviewer-persona dimensions and refute each finding',
  phases: [
    { title: 'Review', detail: 'one reviewer persona per dimension, in parallel' },
    { title: 'Verify', detail: 'an independent agent tries to refute each finding' },
    { title: 'Synthesize', detail: 'merge confirmed findings into one ranked report' },
  ],
}

// ADAPT: the per-diff persona set. Stage 3 of the SKILL.md selects these from
// the diff's content -- always-on lenses plus conditional lenses. Trim this to
// what the diff actually touches; an irrelevant persona invents noise to look
// useful. Record which were skipped so coverage stays auditable.
const PERSONAS = [
  { key: 'correctness', prompt: 'logic errors, off-by-one, nil/None, wrong branches' },
  { key: 'maintainability', prompt: 'naming, duplication, dead code, structure' },
  { key: 'testing', prompt: 'untested branches, missing edge-case coverage' },
  { key: 'project-standards', prompt: 'does this do what its intent claims; house style' },
  // Conditional (include only when the diff matches the trigger):
  // { key: 'security', prompt: 'input handling, auth, crypto, secrets' },
  // { key: 'performance', prompt: 'loops over user-sized data, queries, hot paths' },
  // { key: 'api-contract', prompt: 'breaking changes to a consumed interface/schema' },
]

// ADAPT: forcing a schema makes each agent call a StructuredOutput tool, so
// agent() returns a validated object -- no brittle text parsing. This mirrors
// references/findings-schema.md; confidence is one of five anchors, never
// interpolated.
const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['title', 'severity', 'file', 'line', 'confidence', 'persona'],
        properties: {
          title: { type: 'string' },
          severity: { enum: ['P0', 'P1', 'P2', 'P3'] },
          file: { type: 'string' },
          line: { type: 'integer' },
          confidence: { enum: [0, 25, 50, 75, 100] },
          persona: { type: 'string' },
          requires_verification: { type: 'boolean' },
          suggested_fix: { type: 'string' },
        },
      },
    },
  },
}

// ADAPT: the refutation verdict, mirroring references/validator-template.md. The
// validator is adversarial by design -- it tries to prove the finding is NOT
// real, and defaults to refuted when it cannot substantiate it from the code.
const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'rationale', 'adjusted_confidence'],
  properties: {
    verdict: { enum: ['confirmed', 'refuted'] },
    rationale: { type: 'string' },
    adjusted_confidence: { enum: [0, 25, 50, 75, 100] },
  },
}

// ADAPT: how the diff base ref arrives. Workflow scripts have NO filesystem
// access, so scout the scope inline BEFORE calling Workflow (Stage 1 of the
// SKILL.md) and pass `{ base, intent }` in as `args`. This is the scope-first
// calibration path -- every persona must review the SAME lines.
const base = (args && args.base) || 'HEAD'
const intent = (args && args.intent) || 'unstated -- write a 1-3 sentence intent first'

// ---- find: one reviewer per dimension, dispatched in parallel ---------------
//
// parallel() is a BARRIER (it awaits all personas). A barrier is the CORRECT
// choice here -- the merge step below needs the FULL finding set at once to do
// cross-reviewer promotion (a fingerprint two personas independently land on is
// promoted one confidence step). That is the textbook justification for a
// barrier; do not "optimize" it into a pipeline.
phase('Review')
const reviews = await parallel(
  PERSONAS.map((p) => () =>
    agent(
      `You are the ${p.key} reviewer. Intent of the change: ${intent}. ` +
        `Review the diff at base ${base} through your lens only (${p.prompt}). ` +
        `Read-only. Return findings in the schema; persona = "${p.key}".`,
      { label: `review:${p.key}`, phase: 'Review', schema: FINDINGS_SCHEMA },
    ),
  ),
)

// Collect, then dedup + cross-reviewer promotion across the WHOLE set (Stage 5).
// This is plain deterministic code, not an agent -- the loop holds the merge.
const raw = reviews.filter(Boolean).flatMap((r) => r.findings || [])
const merged = new Map()
for (const f of raw) {
  // Fingerprint: file + line bucket (+/-3) + normalized title (SKILL.md Stage 5).
  const fp = `${f.file}|${Math.round(f.line / 3)}|${(f.title || '').toLowerCase().trim()}`
  const seen = merged.get(fp)
  if (!seen) {
    merged.set(fp, { ...f, agreed_by: [f.persona] })
  } else {
    seen.agreed_by.push(f.persona)
    // Cross-reviewer agreement promotes confidence one anchor step (cap 100).
    const anchors = [0, 25, 50, 75, 100]
    seen.confidence = anchors[Math.min(anchors.indexOf(seen.confidence) + 1, 4)]
  }
}
const deduped = [...merged.values()]
log(`${raw.length} raw finding(s) -> ${deduped.length} after dedup/promotion`)

// ---- adversarially verify: refute each finding that is not already proven ---
//
// Only findings below anchor 100 (or flagged requires_verification) need a
// refutation pass; a proof-backed 100 is kept as-is. The verifier is a FRESH
// agent that did not produce the finding (validator-template.md).
phase('Verify')
const toVerify = deduped.filter((f) => f.confidence < 100 || f.requires_verification)
const verdicts = await parallel(
  toVerify.map((f) => () =>
    agent(
      `Independently verify this code-review finding -- REFUTE it if you can. ` +
        `Default to skepticism. Title: "${f.title}". Persona: ${f.persona}. ` +
        `Location: ${f.file}:${f.line}. Diff base: ${base}. Read the actual ` +
        `code and decide if the defect is real and reachable.`,
      { label: `verify:${f.file}:${f.line}`, phase: 'Verify', schema: VERDICT_SCHEMA },
    ).then((v) => ({ ...f, verdict: v })),
  ),
)

// Apply verdicts, then the deliberately-LATE confidence gate (Stage 5 step 4):
// suppress below anchor 75, except a P0 at 50+ which always surfaces. Suppressed
// findings are kept (appendix tier), never deleted.
const adjudicated = [
  ...deduped.filter((f) => f.confidence === 100 && !f.requires_verification),
  ...verdicts
    .filter(Boolean)
    .filter((f) => f.verdict.verdict === 'confirmed')
    .map((f) => ({ ...f, confidence: f.verdict.adjusted_confidence })),
]
const headline = adjudicated.filter(
  (f) => f.confidence >= 75 || (f.severity === 'P0' && f.confidence >= 50),
)
const appendix = adjudicated.filter((f) => !headline.includes(f))
log(`${headline.length} headline finding(s), ${appendix.length} in appendix tier`)

// ---- synthesize: one agent ranks the confirmed survivors into a report ------
phase('Synthesize')
const report = await agent(
  `Synthesize these confirmed code-review findings into one report ranked by ` +
    `severity then confidence. Note which personas agreed on each (agreed_by). ` +
    `List the appendix (suppressed) tier separately.\n` +
    `Headline: ${JSON.stringify(headline, null, 2)}\n` +
    `Appendix: ${JSON.stringify(appendix, null, 2)}`,
)

// The return value is handed back to the caller, not shown to the user -- relay
// what matters from it yourself.
return { personaCount: PERSONAS.length, headline: headline.length, report }
