---
name: incident-postmortem
description: "Produce a complete, blameless incident postmortem document for production outages and degradations. Make sure to use this skill whenever the user mentions postmortem, post-incident review, RCA, root cause analysis, outage report, P1 review, SEV1 review, post-event writeup, or asks to document what happened after an incident has been resolved. SKIP: live incident command (use the runbook directly), status-page authoring, non-incident retrospectives (sprint retros, project retros)."
summary_l0: "Author blameless incident postmortems with timeline, root cause, contributing factors, and tracked action items"
overview_l1: "This skill produces a complete blameless incident postmortem after a production incident has been mitigated. It collects the facts (timeline, impact, detection, mitigation), drives a root-cause analysis via Five-Whys, separates root cause from contributing factors, captures lessons learned, and turns every lesson into a tracked action item with an owner and due date. Use it for SEV1 / SEV2 outages, customer-impacting degradations, near-misses with broad blast radius, and any incident where leadership requires a written writeup. The skill enforces blameless framing (systems and processes, never individuals), an 8-section output structure, and a verification checklist that catches missing owners, unscheduled action items, and individual-blame phrasing before the document leaves draft. Trigger phrases: postmortem, post-incident review, RCA, root cause analysis, outage report, P1 review, SEV1 review."
---

# Incident Postmortem

Produce a complete, blameless incident postmortem document after a production incident has been mitigated. This skill turns raw incident facts (timeline, impact, contributing systems) into a structured writeup with an explicit root cause, a list of contributing factors, lessons learned, and tracked action items that each have an owner and a due date.

The skill is opinionated on three points: postmortems are **blameless** (root causes are systems and processes, never individuals); every action item is **tracked** (owner + due date + tracking system reference); and the **timeline is built from artifacts** (log timestamps, paging events, deploy events), not memory.

## When to Use This Skill

Use this skill for:

- SEV1 / SEV2 / P0 / P1 production incidents that have been mitigated.
- Customer-impacting degradations: latency spikes, partial outages, data freshness regressions, billing errors.
- Near-misses where the blast radius could have been broad but was contained early.
- Security incidents where containment is complete (parallel writeup, may also need a separate security review).
- Any incident where leadership, customer success, or compliance requires a written writeup.

**Trigger phrases**: "postmortem", "post-incident review", "RCA", "root cause analysis", "outage report", "P1 review", "SEV1 review", "what happened writeup", "post-event analysis".

### When NOT to use this skill

- **During an active incident** -- use the incident-response runbook and the on-call runbook. A postmortem documents an incident that has already been mitigated.
- **Status-page authoring** -- a status-page update is customer-facing and goes out during the incident. The postmortem is a separate internal artifact.
- **Sprint retrospectives or project retrospectives** -- those are team-cadence reviews, not incident artifacts. Use a retro template instead.
- **One-line incident notes** -- if the incident is genuinely trivial (<10 minutes, single-service, no customer impact, no novel failure mode), a paragraph in the operations log is more proportional than a full postmortem.

## What This Skill Does

Produces a postmortem document with eight required sections:

1. **Summary** -- 3-5 sentences: what happened, impact, mitigation, root cause in one line.
2. **Impact** -- quantified customer impact, affected services, duration, severity, on-call response time.
3. **Timeline** -- chronological events with timestamps (UTC), built from logs, paging events, deploy events, chat transcripts.
4. **Root Cause Analysis** -- the single most-causal system or process failure, derived via Five-Whys.
5. **Contributing Factors** -- the other systems, processes, and conditions that allowed the root cause to manifest.
6. **What Went Well** -- detection signals that worked, mitigation steps that worked, communication that worked.
7. **What Went Poorly** -- gaps in detection, runbooks, escalation, automation, communication.
8. **Action Items** -- a tracked table with owner, due date, severity, and ticketing-system reference for each item.

## Instructions

### Step 1: Gather the Required Inputs

Before writing anything, collect:

- **Incident severity** (SEV1 / SEV2 / SEV3) and the criteria that triggered it.
- **Detection time, declaration time, mitigation time, resolution time** -- all in UTC.
- **Affected services and customers** -- service names, customer cohorts or percentages, regions.
- **Timeline artifacts** -- paging events from the alerting system, deploy events from the CI/CD log, chat transcripts from the incident channel, log excerpts from the affected services.
- **The proposed root cause and 3-5 contributing factors** as drafted by the incident commander and the on-call.

If any of these are missing, request them explicitly before drafting. A postmortem written from memory is unreliable.

### Step 2: Pick the Severity Definition

Pin the severity to a defined criterion. Use the team's existing severity table if present. A common default:

| Severity | Criterion |
|---|---|
| SEV1 / P0 | Full outage of a customer-facing service, or data loss / corruption |
| SEV2 / P1 | Significant degradation: high error rate, latency 5x baseline, partial outage |
| SEV3 / P2 | Localized issue, minor customer impact, single feature degraded |

State the severity and the criterion that triggered it in the Summary section.

### Step 3: Build the Timeline from Artifacts

Construct the timeline only from artifacts with timestamps. Never write timeline entries from memory.

For each event, include:

- **UTC timestamp** in `HH:MM:SS` format (date in the section header).
- **Source** -- which system emitted the event (PagerDuty, Datadog alert, deploy log, Slack message).
- **Description** -- one sentence, factual, no interpretation.

Mark the four key timeline anchors explicitly:

- **T0 -- Inciting event** (deploy, traffic spike, dependency failure).
- **TD -- Detection** (first alert fired, first user report).
- **TA -- Acknowledgement** (on-call paged and acknowledged).
- **TM -- Mitigation** (impact stopped or contained, even if root cause not yet fixed).
- **TR -- Resolution** (full restoration, root cause addressed).

Compute the four operational metrics from these anchors:

- **TTD (time to detect)** = TD - T0
- **TTA (time to acknowledge)** = TA - TD
- **TTM (time to mitigate)** = TM - TD
- **TTR (time to resolve)** = TR - T0

### Step 4: Quantify the Impact

The Impact section must be quantified. Vague impact language ("some users were affected") fails verification.

Required fields:

- **Duration** in minutes / hours.
- **Affected services** -- explicit service names.
- **Customer scope** -- percentage of users, named cohorts, regions, or absolute number of requests / customers impacted.
- **Business impact** if known -- failed transactions, revenue impact, SLA budget consumed, customer escalations.

Example acceptable phrasing: "From 14:02 to 14:38 UTC (36 minutes), 100% of checkout requests in the EU region failed with HTTP 503. 14,200 failed transactions; SLA budget consumed: 0.41% of the monthly availability budget."

### Step 5: Drive the Root Cause via Five-Whys

The Five-Whys technique forces a chain of "why did that happen?" questions until the chain bottoms out at a system or process failure. Stop when the next "why" would target an individual.

Example chain:

1. Checkout API returned 503 -- WHY? -- The database connection pool was exhausted.
2. Pool exhausted -- WHY? -- Connections were not released after a panic in the order-handler.
3. Connections not released -- WHY? -- The defer-release pattern was bypassed in a recent refactor.
4. Refactor bypassed defer-release -- WHY? -- The pattern was not codified as a lint rule or a code-review checklist item.
5. Not codified -- WHY? -- The team has no static-analysis rule for connection-lifecycle invariants.

The terminal "why" -- "no static-analysis rule for connection-lifecycle invariants" -- is the root cause. It is a process and tooling failure, not an individual's mistake.

The Root Cause section states the single most-causal system or process failure in one paragraph, then cites the Five-Whys chain that derived it.

### Step 6: List Contributing Factors

Contributing factors are conditions that allowed the root cause to manifest at scale or for as long as it did. Examples:

- Insufficient alerting -- the issue was detected by a customer escalation, not by a synthetic check.
- No circuit breaker on the dependency -- partial dependency degradation cascaded into a full outage.
- Stale runbook -- the on-call followed a procedure that referenced a deprecated endpoint.
- Deployment timing -- the deploy occurred during peak traffic, amplifying the blast radius.

List 3-7 contributing factors. Each should be a system or process condition, not a value judgment.

### Step 7: What Went Well / What Went Poorly

Two parallel sections. Each is a bulleted list of factual observations, no praise or criticism.

**What Went Well** examples:

- Synthetic check fired within 90 seconds of T0.
- Mitigation (revert) was applied within 12 minutes of acknowledgement.
- Customer-success was paged in parallel with the on-call and posted to the status page within 8 minutes.

**What Went Poorly** examples:

- The first paging alert was routed to a deprecated rotation and went unacknowledged for 7 minutes.
- The runbook's "revert deploy" step referenced a UI that has been replaced; the on-call had to discover the new path.
- No automatic rollback fired despite SLO burn-rate alerts crossing the page threshold.

### Step 8: Convert Lessons into Tracked Action Items

Every lesson learned must become an action item. Free-floating recommendations ("we should have better alerting") fail verification.

Action items are tracked in a table:

| ID | Action | Owner | Due | Severity | Ticket |
|---|---|---|---|---|---|
| AI-1 | Add static-analysis rule for db-connection-lifecycle invariants in the order-handler package | @maria | 2026-06-15 | High | ENG-4012 |
| AI-2 | Replace deprecated revert UI reference in incident-response runbook | @sam | 2026-05-30 | Medium | OPS-921 |
| AI-3 | Wire SLO burn-rate alert into the rollback automation | @priya | 2026-07-01 | High | SRE-188 |

Rules:

- Every row has an owner (one person, not a team).
- Every row has a due date (an actual date, not "ASAP" or "next quarter").
- Every row has a ticket reference in the team's tracking system; if a ticket does not exist yet, the postmortem author creates one before the document is published.
- Severity follows a 3-level scale: High (closes a gap that caused the incident or could cause a repeat), Medium (closes a gap that prolonged the incident), Low (improves response quality but is not gap-closing).

### Step 9: Apply the Blameless Framing Pass

Before publishing, re-read the entire document and apply the blameless framing pass. Replace every instance of an individual's name in a root cause or contributing factor with the system or process that allowed the action to happen.

**Replace**: "Maria deployed during peak traffic" -> "The deploy pipeline does not block deploys during peak-traffic windows."

**Replace**: "The on-call didn't see the alert" -> "The alert was routed to a rotation that had no acknowledgement-failover policy."

Individuals appear in the document only as:

- The author of the postmortem.
- The owner column of action items.
- The on-call rotation in the timeline (as a role, not as a critique).

### Step 10: Publish and Schedule the Review Meeting

Publish the postmortem to the team's standard location (incident-management tool, wiki, or git repo under `docs/incidents/`). Schedule the postmortem review meeting within 5 business days of incident resolution. The review meeting walks the document, ratifies the root cause and contributing factors, and assigns owners to any action items that did not yet have one.

## Common Rationalizations

The agent and the user will occasionally try to skip or shortcut the postmortem. The following table names each rationalization and its rebuttal.

| Rationalization | Reality |
|---|---|
| "It was a one-off so no postmortem is needed" | One-offs are the cheapest learning opportunity in the system. Skipping the writeup means the next one-off has no precedent to look up. The cost of writing it is 2-4 hours; the cost of a repeat is the incident itself. |
| "The on-call engineer just messed up, blame is the root cause" | Blame is not a root cause. Individuals operate inside a system; if the system allowed the mistake to cause an incident, the system is the root cause. Blameless framing is not a politeness convention -- it is the only framing that yields action items the team can actually act on. |
| "We already fixed it, so writing it up wastes time" | The fix addressed the immediate failure. The postmortem identifies the contributing factors that allowed the failure to reach production and the gaps in detection / response that prolonged it. Without the writeup, those factors persist. |
| "Action items can stay informal -- we know what to do" | Action items without owners and due dates are not tracked. Untracked work does not happen. The postmortem's verification step explicitly fails if any action item is missing an owner or a due date. |
| "I'll write it from memory next week" | Memory degrades within hours, not days. The timeline must be built from artifacts (logs, paging events, deploy events, chat transcripts) within 48-72 hours of resolution; after that, the artifacts get harder to gather and the writeup gets unreliable. |
| "We can skip the Five-Whys -- it's obviously a bad deploy" | "Bad deploy" is the first why, not the last. The Five-Whys exists to surface the process and tooling layer underneath the immediate failure. Skipping it produces shallow action items that close the immediate gap and leave the next one open. |

## Verification

Before publishing the postmortem, walk this binary checklist. Every item must be true.

- [ ] The document contains all 8 required sections in order: Summary, Impact, Timeline, Root Cause, Contributing Factors, What Went Well, What Went Poorly, Action Items.
- [ ] The Summary states the severity and the criterion that triggered it.
- [ ] The Impact section quantifies duration, affected services, and customer scope (percentage, cohort, or absolute count).
- [ ] The Timeline has UTC timestamps for T0, TD, TA, TM, TR and computes TTD, TTA, TTM, TTR.
- [ ] Every timeline entry cites a source artifact (alert, deploy log, chat transcript, log excerpt).
- [ ] The Root Cause section presents the Five-Whys chain and identifies the terminal "why" as a system or process failure.
- [ ] No individual name appears as a root cause or as a contributing factor; individuals appear only as action-item owners or as roles in the timeline.
- [ ] Every action item has an owner (one person), a due date (an actual date), a severity, and a ticket reference.
- [ ] The What Went Well / What Went Poorly sections are factual observations, not praise or criticism.
- [ ] The document has been read end-to-end with the blameless framing pass applied; no replacement was needed on the final pass.

If any checklist item is false, do not publish. Fix the document.

## Related Skills

- [[sre-engineer]] -- broader SRE patterns (SLOs, error budgets, on-call design). The postmortem is one artifact in the SRE practice; this skill is the artifact-producer, the advisor is the SRE skill.
- [[runbook-writer]] -- operational runbooks for services and incident types. Action items from a postmortem frequently include "write or update the runbook for X"; that work goes through the runbook writer.
- [[oncall-runbook]] -- per-alert response runbooks. Postmortem action items that close detection-and-response gaps frequently update per-alert runbooks.
- [[rollback-strategy-advisor]] -- rollback procedures. If the postmortem identified a rollback gap, the action item plan is informed by the rollback advisor.
- [[observability-setup]] -- detection-pipeline design. If the postmortem identified a detection gap, the action item plan is informed by the observability setup.
