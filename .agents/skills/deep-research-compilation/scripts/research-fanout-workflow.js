// =============================================================================
// research-fanout-workflow.js
//
// TEMPLATE TO ADAPT -- NOT a production script and NOT meant to run verbatim.
//
// An executable scaffold for the UPSTREAM research-gathering phase that feeds
// this compilation skill: fan-out searches -> fetch sources -> adversarially
// verify claims -> synthesize a cited report. It is the runnable form of the
// [[deep-research]] harness this skill names as its upstream. Use it when the
// user has a QUESTION rather than a pile of finished reports: this template
// gathers and verifies the material, and the SKILL.md steps then format the
// synthesized result into a template-matched .docx / .md / .pdf.
//
// This is a SEPARATE artifact from the skill's throwaway python-docx generator.
// The skill's core rule ("you are the generator; there is no persistent
// script") is about document EMISSION. This file is an orchestration harness
// for SOURCE GATHERING -- it emits no document and writes no docx.
//
// -----------------------------------------------------------------------------
// GRACEFUL DEGRADATION (REQUIRED)
//
// Dynamic Workflows is a plan-gated research-preview capability that may be
// absent in the user's harness. NEVER hard-depend on it. When the Workflow
// runtime is unavailable, fall back, in order of decreasing surface:
//   1. a handful of isolated subagents (one per search angle, then a fetch
//      pass), or
//   2. a single agent doing one sequential search -> read -> synthesize pass.
// The decision guide for whether a fan-out is warranted at all is the
// agent-orchestration-primitives skill; this template does not duplicate it.
//
// -----------------------------------------------------------------------------
// SCOPE-FIRST TOKEN CAUTION (REQUIRED)
//
// A search fan-out + per-source fetch + per-claim verification carries a 5-15x
// token multiplier plus per-agent overhead. Before running at full scale:
//   1. Calibrate on ONE search angle (or a handful of sources) first.
//   2. Review the candidate source list on the FIRST trigger -- confirm the
//      URLs are on-topic and trustworthy before deep-reading them all.
//   3. Confirm with the user before fanning out across every angle.
// Pair this with hard budget controls -- see the ai-billing-safeguards skill.
//
// -----------------------------------------------------------------------------
// SKILL-NATIVE: this template introduces no NEW dependency, credential, or
// third-party MCP. The subagents it spawns use only the harness's own built-in
// tools -- WebSearch / WebFetch for gathering, and the local read tools for any
// user-supplied source files. There is no new outbound integration to register.
// =============================================================================

// The phase titles here must match the phase() strings used in the body below.
export const meta = {
  name: 'research-fanout-verify',
  description: 'Fan out searches, fetch sources, verify claims, synthesize a cited report',
  phases: [
    { title: 'Search', detail: 'one agent per search angle (multi-modal sweep)' },
    { title: 'Fetch', detail: 'fetch + deep-read each candidate source' },
    { title: 'Verify', detail: 'an independent agent tries to refute each claim' },
    { title: 'Synthesize', detail: 'merge verified claims into one cited report' },
  ],
}

// ADAPT: a fetched source. Forcing a schema makes each agent call a
// StructuredOutput tool, so agent() returns a validated object -- no brittle
// text parsing. Keep url/title so the synthesis step can build the canonical
// [N] citation list the compilation skill renumbers against.
const SOURCE_SCHEMA = {
  type: 'object',
  required: ['url', 'title', 'claims'],
  properties: {
    url: { type: 'string' },
    title: { type: 'string' },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['statement', 'support'],
        properties: {
          statement: { type: 'string' },
          support: { type: 'string' }, // the quoted/paraphrased evidence in the source
        },
      },
    },
  },
}

// ADAPT: the refutation verdict. The verifier is adversarial by design -- it
// tries to prove the claim is NOT supported by the source, and defaults to
// unsupported when it cannot substantiate it. This is the research analogue of
// the code-review validator-template refutation pass.
const VERDICT_SCHEMA = {
  type: 'object',
  required: ['supported', 'rationale'],
  properties: {
    supported: { type: 'boolean' },
    rationale: { type: 'string' },
  },
}

// ADAPT: the research question and the search angles. Workflow scripts have NO
// filesystem and NO network of their own -- the agents do the web work. Pass the
// refined question in as `args.question` after the scope-first calibration; an
// underspecified question wastes the whole fan-out, so narrow it FIRST.
const question = (args && args.question) || 'unstated -- refine the question first'
const ANGLES = (args && args.angles) || [
  'authoritative primary sources and standards bodies',
  'recent peer-reviewed or industry-analyst coverage',
  'dissenting / contrarian views and known criticisms',
]

// ---- search: a multi-modal sweep, one agent per angle ----------------------
//
// Each angle is blind to what the others surface, which is the point -- one
// query angle never finds everything. parallel() is a BARRIER here on purpose:
// the dedup below needs the FULL candidate set at once to collapse the same URL
// found by two angles before the expensive fetch phase.
phase('Search')
const sweeps = await parallel(
  ANGLES.map((angle, i) => () =>
    agent(
      `Search the web for sources on: ${question}. Angle: ${angle}. Use the ` +
        `WebSearch tool. Return a JSON array of candidate source URLs (most ` +
        `relevant first). Read-only; do not fetch full pages yet.`,
      {
        label: `search:${i}`,
        phase: 'Search',
        schema: { type: 'array', items: { type: 'string' } },
      },
    ),
  ),
)

// Dedup candidate URLs across angles (plain deterministic code, not an agent).
const candidates = [...new Set(sweeps.filter(Boolean).flat())]
log(`${candidates.length} unique candidate source(s) across ${ANGLES.length} angle(s)`)

// ---- fetch: deep-read each source independently ----------------------------
//
// pipeline() runs each URL through the fetch stage with NO barrier -- source B
// can be fetching while source A is already extracted. A stage that throws
// (dead link, paywall) drops that source to null, so filter before use.
phase('Fetch')
const fetched = await pipeline(candidates, (url) =>
  agent(
    `Fetch and read this source with the WebFetch tool: ${url}. Extract its ` +
      `key claims relevant to "${question}", each with the supporting evidence ` +
      `from the page. Read-only.`,
    { label: `fetch:${url}`, phase: 'Fetch', schema: SOURCE_SCHEMA },
  ),
)
const sources = fetched.filter(Boolean)
const claims = sources.flatMap((s) => s.claims.map((c) => ({ ...c, url: s.url, title: s.title })))
log(`${sources.length} source(s) read, ${claims.length} claim(s) extracted`)

// ---- verify: adversarially refute each claim against its own source --------
//
// A fresh agent that did not extract the claim tries to refute it. This is what
// keeps a plausible-but-unsupported claim out of the final report. Claims whose
// support the verifier cannot confirm are dropped from the cited synthesis.
phase('Verify')
const verdicts = await parallel(
  claims.map((c) => () =>
    agent(
      `Independently verify this research claim -- try to REFUTE it. Default to ` +
        `skepticism. Claim: "${c.statement}". Source: ${c.url}. Re-read the ` +
        `source with WebFetch and decide whether it genuinely supports the claim.`,
      { label: `verify:${c.url}`, phase: 'Verify', schema: VERDICT_SCHEMA },
    ).then((v) => ({ ...c, supported: v.supported, rationale: v.rationale })),
  ),
)
const verified = verdicts.filter(Boolean).filter((c) => c.supported)
log(`${verified.length}/${claims.length} claim(s) survived adversarial verification`)

// ---- synthesize: one agent writes the cited report -------------------------
//
// The synthesis hands off to the compilation SKILL.md: the report carries
// inline [N] citations against a canonical source list. NEVER fabricate a
// citation -- a statement with no verified source gets none (skill Critical
// Rule). The compilation steps then renumber and format this into the .docx.
phase('Synthesize')
const canonical = [...new Set(verified.map((c) => c.url))].map((url, i) => ({
  num: i + 1,
  url,
  title: (verified.find((c) => c.url === url) || {}).title || url,
}))
const report = await agent(
  `Synthesize these verified claims into a coherent report with inline [N] ` +
    `citations that reference the canonical source list. Use ONLY verified ` +
    `claims; do not fabricate citations. Deduplicate overlapping points.\n` +
    `Verified claims: ${JSON.stringify(verified, null, 2)}\n` +
    `Canonical sources [N]: ${JSON.stringify(canonical, null, 2)}`,
)

// The return value is handed back to the caller, not shown to the user -- relay
// what matters, then feed `report` + `canonical` into the compilation steps.
return { sourceCount: sources.length, verifiedClaims: verified.length, canonical, report }
