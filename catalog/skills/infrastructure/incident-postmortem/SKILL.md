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

### The surprising-behavior trigger

An incident is not only an outage. When agent or harness behavior is **surprising, contradictory, smaller than expected, or called out by the user as likely wrong**, that is an incident, not just a correction to make and move past.

This trigger exists because the most instructive failures in a tool-and-catalog project never page anyone. A hook that is registered and permanently silent, a guard whose path filter excludes the file it guards, a cross-platform sibling that never parsed - each of these is a shipped failure with a reusable shape, and each is easy to fix quietly and forget. The test is not "did this hurt a customer" but "would this recur with a different person at the keyboard".

Fixing the immediate symptom and moving on is what turns a one-time surprise into a recurring one. If the surprise had a cause worth naming, write the note.

### When NOT to use this skill

- **During an active incident** -- use the incident-response runbook and the on-call runbook. A postmortem documents an incident that has already been mitigated.
- **Status-page authoring** -- a status-page update is customer-facing and goes out during the incident. The postmortem is a separate internal artifact.
- **Sprint retrospectives or project retrospectives** -- those are team-cadence reviews, not incident artifacts. Use a retro template instead.
- **One-line incident notes** -- if the incident is genuinely trivial (<10 minutes, single-service, no customer impact, no novel failure mode), a paragraph in the operations log is more proportional than a full postmortem.

### Admission criteria: three tests, all three required

The size threshold above ("under 10 minutes, no customer impact") is necessary but not sufficient. A standalone postmortem is warranted only when the incident is simultaneously:

1. **Subtle** -- the cause is not obvious from reading the diff. If a reviewer looking at the change would immediately see the bug, the fix and a changelog line carry the whole lesson.
2. **Systemic** -- the process let it through, not just one person. Ask what SHOULD have caught it: a test, a gate, a review step, a schema. If the honest answer is "nothing was supposed to; someone slipped", that is a mistake, not a system failure.
3. **Costly to rediscover** -- someone hitting this again would burn real time re-deriving the cause. A failure that announces itself with a clear error message is cheap to rediscover and does not need a document.

Fail any one of the three and the proportionate artifact is smaller: a CHANGELOG entry, a known-gaps line, or a comment at the site of the fix. Write that instead and move on.

This gate exists because an archive nobody reads is worse than no archive. Every low-value entry raises the cost of finding the high-value ones, so admitting a marginal incident is not a neutral act of thoroughness. It taxes every future reader.

## What This Skill Does

Produces a postmortem document with eight required sections:

1. **Summary** -- the 30-second executive summary, and the only section most readers will finish. In 3-5 sentences it must answer four questions explicitly: what broke, what the root cause was, **why the process let it escape**, and **the durable lesson**. The last two are the ones that get dropped, and they are the reason the document exists; a summary that stops at what-and-why is an outage report, not a postmortem.
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

### Step 8b: Classify the Responsible Layer

Before writing the action items, classify WHERE the failure belongs. This is the step that makes the practice produce durable fixes rather than apologies, because a fix applied at the wrong layer looks like a resolution and prevents nothing.

Four layers, from most specific to most systemic:

| Layer | What it means | What a fix at this layer looks like |
|---|---|---|
| **Agent behavior** | The agent (or operator) did the wrong thing while the surface it used was correct and clearly documented. | Rarely a code change. Usually a rule, a checklist item, or a guard that makes the wrong action harder than the right one. |
| **Projection or payload** | The data, config, or output the agent acted on was wrong, malformed, or missing a field. | Fix the producer, and add a schema or shape assertion so a malformed payload fails loudly instead of being interpreted. |
| **Authoring gap** | The artifact was written incompletely or inconsistently: a missing sibling, an unregistered script, an absent test. | A mechanical gate that fails on the incomplete state, not a note asking authors to remember. |
| **Docs or process** | The correct behavior was never written down, or was written down somewhere nobody reads at the moment of the decision. | Move the rule to where the decision happens, rather than adding it to a document that is already long. |

**Repair at the lowest durable layer.** "Lowest" means most specific, and "durable" is the constraint that stops you going too low: a fix that only holds while someone remembers it is not durable, however specific it is. An agent-behavior finding whose only remedy is "be more careful" has not been classified yet - push down until you find the projection, authoring, or process condition that permitted it.

The common error runs the other way too. Rewriting a whole process because one payload was malformed is a fix at too high a layer: it is expensive, it disturbs work that was fine, and it usually does not close the specific hole.

Record the classification in the postmortem, next to the root cause. Two incidents that share a layer usually share a fix.

### Step 8c: Link the Guardrails the Incident Motivated

Action items are promises; guardrails are the things that actually make recurrence impossible. Before publishing, name and link every guardrail this incident produced, by class:

- **Tests** -- a regression test that fails without the fix, or a new case in an existing suite.
- **Validator or gate rules** -- a new check in a validator, a CI step, a hook, or a schema constraint.
- **Instruction rules** -- a line added to `AGENTS.md`, a project constitution, a runbook, or a skill body, when the failure was an authoring or process gap that no code check can catch.

Each entry names the guardrail AND links it. A guardrail described but not linked is indistinguishable from one that was never built.

If the incident produced no guardrail, say so explicitly and give the reason: the cost is disproportionate, the failure is not mechanically detectable, or the fix is inherently one-off. An unexplained absence reads as an oversight; a stated one is a decision a future reader can revisit. What is not acceptable is silence, because silence lets a document that changed nothing look like a document that changed something.

This step extends the Durable fix requirement rather than replacing it: Durable fix answers "what closed this incident", and this step answers "what makes it unable to recur".

### Step 9: Apply the Blameless Framing Pass

Before publishing, re-read the entire document and apply the blameless framing pass. Replace every instance of an individual's name in a root cause or contributing factor with the system or process that allowed the action to happen.

**Replace**: "Maria deployed during peak traffic" -> "The deploy pipeline does not block deploys during peak-traffic windows."

**Replace**: "The on-call didn't see the alert" -> "The alert was routed to a rotation that had no acknowledgement-failover policy."

Individuals appear in the document only as:

- The author of the postmortem.
- The owner column of action items.
- The on-call rotation in the timeline (as a role, not as a critique).

### Step 10: Publish and Schedule the Review Meeting

Publish the postmortem to `docs/incidents/<slug>-YYYYMMDD.md`, where the slug names the failure rather than the fix and the date is when the failure was identified. In a project with a dedicated incident-management tool, that tool is the system of record and this file is the durable, reviewable copy. See [`docs/incidents/README.md`](../../../../docs/incidents/README.md) for the convention and `TEMPLATE.md` for the shape.

Two sections are **mandatory** on top of the eight above, and a note missing either is not publishable:

- **Public-Safe Shape** - the reusable pattern, abstracted with no local absolute paths, raw log output, private links, or credentials. Write it as a claim someone outside the incident could apply. If a shape recurs across incidents, state it once in `docs/incidents/shapes.md` and reference it from each note.
- **Durable fix** - the concrete change that makes the lesson survive, named AND linked: a commit, a test, a CI gate, a hook, a validator, a skill edit.

**An incident is closed by a change, not by an explanation.** A note with no linked durable fix is an open item, not an archive entry. When the fix does not exist yet, that is an honest state, but it belongs in the version's gap log as tracked work via [[known-gaps-tracker]], with the note linking to it. This is the single control that stops an incident directory becoming a collection of writeups nobody reads.

When the same failure class shows up a third time, it has outgrown the incident archive: promote it to a solutions entry via [[solution-knowledge-base]], so the answer is discoverable by the problem rather than by the date it happened.

Schedule the postmortem review meeting within 5 business days of incident resolution. The review meeting walks the document, ratifies the root cause and contributing factors, and assigns owners to any action items that did not yet have one.

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
- [ ] The root cause carries a responsible-layer classification (agent behavior / projection or payload / authoring gap / docs or process), and the action items repair at the lowest durable layer.
- [ ] The incident passes all three admission criteria (subtle AND systemic AND costly to rediscover); if any one fails, a CHANGELOG entry or known-gaps line was written instead of this document.
- [ ] The Summary answers all four questions explicitly, including why the process let the failure escape and the durable lesson.
- [ ] Every guardrail the incident motivated is named AND linked by class (test, validator or gate rule, instruction rule), or the document states explicitly that none were added and why.
- [ ] A **Public-Safe Shape** section is present and contains no local absolute path, raw log output, private link, or credential.
- [ ] A **Durable fix** section is present and every fix it names is also linked, and the link resolves to something that exists.
- [ ] If no durable fix exists yet, the note links the tracked gap-log item instead of standing alone as though the writeup were the resolution.

If any checklist item is false, do not publish. Fix the document.

## Related Skills

- [[sre-engineer]] -- broader SRE patterns (SLOs, error budgets, on-call design). The postmortem is one artifact in the SRE practice; this skill is the artifact-producer, the advisor is the SRE skill.
- [[runbook-writer]] -- operational runbooks for services and incident types. Action items from a postmortem frequently include "write or update the runbook for X"; that work goes through the runbook writer.
- [[oncall-runbook]] -- per-alert response runbooks. Postmortem action items that close detection-and-response gaps frequently update per-alert runbooks.
- [[rollback-strategy-advisor]] -- rollback procedures. If the postmortem identified a rollback gap, the action item plan is informed by the rollback advisor.
- [[observability-setup]] -- detection-pipeline design. If the postmortem identified a detection gap, the action item plan is informed by the observability setup.
- [[known-gaps-tracker]] -- the version gap log. An incident whose durable fix does not exist yet becomes a tracked gap there, and the note links it; this is what keeps an unfixed incident an open item rather than an archive entry.
- [[solution-knowledge-base]] -- the problem-indexed store. A failure class that recurs a third time has outgrown the incident archive and graduates into a solutions entry, discoverable by the problem rather than by the date.
- [[egress-redaction]] -- the redaction discipline the Public-Safe Shape section applies. An incident note is the artifact most likely to carry internal paths and raw output into a public repository.
