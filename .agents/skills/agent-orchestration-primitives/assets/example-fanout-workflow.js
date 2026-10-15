// =============================================================================
// example-fanout-workflow.js
//
// TEMPLATE TO ADAPT -- NOT a production script and NOT meant to run verbatim.
//
// This is a reference Dynamic-Workflow that fans a read-only audit across every
// file under a directory and synthesizes the findings into a single report. It
// is the canonical "embarrassing parallelism, large surface" shape from
// agent-orchestration-primitives. Copy it into a skill's scripts/ or assets/
// directory and adapt the meta, the schema, the per-file prompt, and the
// synthesis prompt to the task at hand.
//
// -----------------------------------------------------------------------------
// GRACEFUL DEGRADATION (REQUIRED)
//
// Dynamic Workflows is a plan-gated research-preview capability. It may be
// absent in the user's harness (availability varies by harness, version, and
// /config toggle). NEVER hard-depend on it. When the Workflow runtime is
// unavailable, fall back, in order of decreasing surface:
//   1. a handful of isolated subagents (small surface), or
//   2. a single agent doing one sequential read-only pass (smallest surface).
// The decision guide for which primitive a task actually needs is the parent
// skill, agent-orchestration-primitives.
//
// -----------------------------------------------------------------------------
// SCOPE-FIRST TOKEN CAUTION (REQUIRED)
//
// A full fan-out is token-heavy (a 5-15x multiplier plus per-agent overhead).
// Before running at full scale:
//   1. Calibrate on ONE folder (or a handful of files) first.
//   2. Review the execution plan on the FIRST trigger -- confirm the file list
//      and the per-file prompt are correct before fanning out.
//   3. Confirm with the user before going full-scale across the whole tree.
// Pair this with hard budget controls -- see the ai-billing-safeguards skill.
//
// -----------------------------------------------------------------------------
// SKILL-NATIVE: this template introduces no outbound call, no dependency, and
// no credential. The subagents it spawns use only the harness's own read tools.
// =============================================================================

// Every workflow script must begin with a pure-literal `meta` block. The phase
// titles here must match the phase() strings used in the body below.
export const meta = {
  name: 'example-fanout-audit',
  description: 'Audit every file under a directory and synthesize the findings',
  phases: [
    { title: 'Discover', detail: 'list the files in scope' },
    { title: 'Audit', detail: 'one read-only agent per file' },
    { title: 'Synthesize', detail: 'merge all findings into one report' },
  ],
}

// ADAPT: the schema each per-file agent must return. Forcing a schema makes the
// agent call a StructuredOutput tool, so agent() returns a validated object --
// no brittle text parsing downstream.
const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['file', 'findings'],
  properties: {
    file: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'description'],
        properties: {
          severity: { enum: ['low', 'medium', 'high'] },
          description: { type: 'string' },
        },
      },
    },
  },
}

// ADAPT: how the work-list arrives. Workflow scripts have NO filesystem access,
// so either (a) scout the file list inline BEFORE calling Workflow and pass it
// in as `args` (this is the scope-first calibration path -- preferred), or
// (b) let a discovery agent produce it (shown as the fallback below).
phase('Discover')
const files =
  Array.isArray(args) && args.length
    ? args // caller already scouted the list (scope-first path)
    : (await agent(
        'List every source file under the target directory. Return a JSON ' +
          'array of repo-relative paths. Read-only -- do not modify anything.',
        { schema: { type: 'array', items: { type: 'string' } } },
      )) || []

log(`${files.length} file(s) in scope`)

// ADAPT: the per-file audit prompt. The pipeline runs each file through the
// audit stage independently with NO barrier -- file B can be auditing while
// file A is already done. Concurrency is capped by the runtime automatically;
// passing 500 files is fine, only a handful run at any instant.
phase('Audit')
const audited = await pipeline(files, (file) =>
  agent(
    `Audit this single file for issues: ${file}. Read it and report concrete ` +
      `findings, each with a severity. Read-only -- do not modify anything.`,
    { label: `audit:${file}`, phase: 'Audit', schema: FINDINGS_SCHEMA },
  ),
)

// A pipeline stage that throws drops that item to null, so filter before use.
const findings = audited.filter(Boolean).flatMap((r) => r.findings || [])
log(`${findings.length} finding(s) across ${audited.filter(Boolean).length} file(s)`)

// ADAPT: the synthesis prompt. A single agent merges the off-context
// intermediates (which lived in the `findings` variable, never in anyone's
// context window) into one prioritized report.
phase('Synthesize')
const report = await agent(
  `Synthesize these ${findings.length} findings into a prioritized report ` +
    `grouped by severity (high -> low):\n${JSON.stringify(findings, null, 2)}`,
)

// The workflow's return value is handed back to the caller, not shown to the
// user -- relay what matters from it yourself.
return { fileCount: files.length, findingCount: findings.length, report }
