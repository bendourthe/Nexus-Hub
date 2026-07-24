/**
 * visual-qa-workflow.js - Dynamic-Workflow TEMPLATE for the presentify
 * visual-QA loop (Phase 5). ADAPT this, do NOT run it verbatim: the segment
 * list, the source references, and the rebuild callback are placeholders you
 * wire to the run at hand.
 *
 * What it does: with the generated page rendered and segmented, it grades EACH
 * segment against references/visual-qa-rubric.md AND its SOURCE figure/section,
 * adversarially verifies each HIGH-severity finding, synthesizes a fix list,
 * hands it back for ONE rebuild pass, re-renders, and re-grades - looping until
 * the page-level bar passes (no confirmed high-severity finding) or the
 * iteration / budget cap is hit.
 *
 * THREE MANDATORY RULES (AGENTS.md workflow-as-skill-bundle pattern):
 *
 *   1. GRACEFUL DEGRADATION. Dynamic Workflows is a plan-gated research-preview
 *      capability that may be ABSENT. This template MUST fall back:
 *        Dynamic Workflows  ->  isolated subagents (one grader per segment)
 *                           ->  a single sequential agent (grade segments in a loop)
 *      and, orthogonally, for the render:
 *        headless browser (screenshot grading via [[browser-testing-with-devtools]])
 *                           ->  the STRUCTURAL scorer scripts/visual_qa_score.py
 *                               (markup / computed CSS; a "structural-only" pass)
 *      Never hard-fail on a missing runtime or a missing browser.
 *
 *   2. SCOPE-FIRST TOKEN CAUTION. A per-segment fan-out carries a 5-15x token
 *      multiplier. CALIBRATE on ONE segment first, review the execution plan on
 *      the first trigger, and CONFIRM before going full-scale. See
 *      [[agent-orchestration-primitives]] for whether a fan-out is warranted at
 *      all, and [[ai-billing-safeguards]] for the hard budget caps.
 *
 *   3. SKILL-NATIVE. No outbound call, no dependency, no credential. The
 *      subagents use only the harness's own tools; the render is a LOCAL
 *      headless render; the structural scorer is a bundled local script.
 */

export const meta = {
  name: 'presentify-visual-qa',
  description:
    'Render, per-segment grade vs source + rubric, adversarially verify, ' +
    'synthesize fixes, re-render until the page-level bar passes',
  phases: [
    { title: 'Grade', detail: 'grade each segment against the rubric + its source' },
    { title: 'Verify', detail: 'adversarially verify each high-severity finding' },
    { title: 'Fix', detail: 'synthesize fixes, rebuild, re-render, re-grade' },
  ],
}

// --- StructuredOutput schemas (validated at the tool-call layer) ------------

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    segment: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          criterion: {
            type: 'string',
            enum: [
              'full-width', 'image-sizing', 'annotation-fidelity',
              'imagery-integration', 'readability-layout',
            ],
          },
          status: { type: 'string', enum: ['pass', 'fail', 'n/a'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          kind: { type: 'string', enum: ['structural', 'agent-vision'] },
          evidence: { type: 'string' },
        },
        required: ['criterion', 'status', 'evidence'],
      },
    },
  },
  required: ['segment', 'findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' },
  },
  required: ['refuted'],
}

// args (wire these to the run): {
//   segments: [{ id, screenshot, sourceRef }],  // one per top-level band
//   rebuild:  async () => { /* apply fixes, rebuild + re-render */ },
//   cap:      number,                            // max iterations (default 4)
// }
const segments = (args && args.segments) || []
const CAP = (args && args.cap) || 4

// SCOPE-FIRST: calibrate on ONE segment before fanning out over all of them.
log(
  `visual-QA: ${segments.length} segment(s). Calibrate on the first, confirm ` +
  `the plan, THEN scale (a per-segment fan-out is a 5-15x token multiplier).`
)

let iteration = 0
let open = []
while (iteration < CAP) {
  iteration++

  // Grade each segment, and verify its HIGH findings as soon as that segment's
  // grade completes (pipeline: no barrier between grade and verify).
  const graded = await pipeline(
    segments,
    (seg) =>
      agent(
        `Grade segment "${seg.id}" against references/visual-qa-rubric.md and ` +
        `compare it to its SOURCE (${seg.sourceRef}). Report per-criterion ` +
        `findings (full-width, image-sizing, annotation-fidelity, ` +
        `imagery-integration, readability-layout).`,
        { label: `grade:${seg.id}`, phase: 'Grade', schema: FINDINGS_SCHEMA },
      ),
    (grade, seg) =>
      parallel(
        (grade.findings || [])
          .filter((f) => f.status === 'fail' && f.severity === 'high')
          .map((f) => () =>
            // Independent skeptic: try to REFUTE the finding; default to
            // refuted when uncertain, so only real defects survive.
            agent(
              `Adversarially verify this HIGH finding on segment "${seg.id}": ` +
              `${f.criterion} - ${f.evidence}. Try to REFUTE it; if uncertain, ` +
              `refuted=true.`,
              { label: `verify:${seg.id}`, phase: 'Verify', schema: VERDICT_SCHEMA },
            ).then((v) => ({ ...f, segment: seg.id, confirmed: !!v && !v.refuted })),
          ),
      ),
  )

  open = graded.flat().filter(Boolean).filter((f) => f.confirmed)
  if (open.length === 0) {
    log(`visual-QA: clean at iteration ${iteration} (page-level bar passed).`)
    break
  }
  if (budget.total && budget.remaining() < 50_000) {
    log('visual-QA: budget cap reached; stopping with a bounded, explained non-pass.')
    break
  }

  // Synthesize the confirmed fixes and hand them back for ONE rebuild pass,
  // then re-render and re-grade on the next loop iteration.
  phase('Fix')
  const fixList = open
    .map((f) => `[${f.segment}] ${f.criterion}: ${f.evidence}`)
    .join('\n')
  await agent(
    `Apply ONLY these confirmed fixes to the HTML, preserving everything else:\n` +
    `${fixList}`,
    { label: `fix:pass-${iteration}`, phase: 'Fix' },
  )
  if (typeof (args && args.rebuild) === 'function') {
    await args.rebuild()
  }
}

return { iterations: iteration, openFindings: open, passed: open.length === 0 }
