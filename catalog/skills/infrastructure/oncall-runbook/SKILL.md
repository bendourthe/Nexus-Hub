---
name: oncall-runbook
description: "Produce a per-alert on-call response runbook. Make sure to use this skill whenever the user mentions on-call runbook, on-call guide, alert runbook, paging runbook, escalation procedure, on-call handoff, alert response, or asks for a one-pager that an on-call engineer can follow when a specific alert pages them. SKIP: general operational runbooks (use `runbook-writer`), incident postmortems (use `incident-postmortem`), customer-facing status guides (use `user-documentation`)."
summary_l0: "Write per-alert on-call response runbooks with diagnostics, remediation, and escalation"
overview_l1: "This skill produces a per-alert on-call response runbook -- one short page per paging alert, designed for an on-call engineer reading it during an active page. Each entry follows a fixed structure: Alert summary, Quick Reference (mitigation command at the top), Diagnostic Commands, Remediation Options, Rollback, Service Dependencies. The skill also produces the Escalation Matrix (when, who, how) and the On-Call Handoff Template (what the outgoing on-call tells the incoming on-call at shift change). Every alert that pages should have an entry; entries without a known cause carry a placeholder with the diagnostic-first procedure. Trigger phrases: on-call runbook, alert runbook, paging runbook, escalation procedure, on-call handoff."
---

# On-Call Runbook

Produce a per-alert response runbook. Each page is keyed to a specific paging alert; the on-call engineer who acknowledges that alert reads the matching page and follows it.

This skill is opinionated on three points: the **mitigation command appears at the top** (the on-call should not have to scroll during an active page); the **escalation matrix is explicit and time-bound** (when to escalate, not just "if stuck"); and **every paging alert has an entry**, even if the entry is a placeholder with a diagnostic-first procedure.

## When to Use This Skill

Use this skill for:

- Adding a new alert that pages -- write the entry as part of adding the alert.
- Onboarding a new service -- enumerate every alert the service emits and produce a runbook page per alert.
- Refreshing an existing on-call runbook after an incident -- the postmortem identified a runbook gap.
- Producing the team's escalation matrix and on-call handoff template.

**Trigger phrases**: "on-call runbook", "on-call guide", "alert runbook", "paging runbook", "escalation procedure", "on-call handoff", "alert response", "page response".

### When NOT to use this skill

- **General operational runbooks** (deploy, maintenance, DR) -- use `runbook-writer`. A general runbook is longer and covers a full procedure; an on-call runbook is one page per alert.
- **Incident postmortems** -- use `incident-postmortem`. A postmortem documents one past incident; the on-call runbook documents the response procedure that future on-calls will follow.
- **Customer-facing status guides** -- use `user-documentation`.

## What This Skill Does

Produces three artifacts:

1. **Per-alert pages** -- one page per paging alert, following a fixed structure.
2. **Escalation Matrix** -- a single table mapping alert classes to escalation paths.
3. **On-Call Handoff Template** -- the document the outgoing on-call hands to the incoming on-call at shift change.

### Per-Alert Page Structure

| Section | Length | Content |
|---|---|---|
| Alert header | 1 line | Alert name + severity + paging team |
| Quick Reference | 3-5 lines | The mitigation command(s) at the top; "if you only read one thing, read this" |
| When this fires | 2-3 lines | The exact alert condition (Prometheus expression, CloudWatch threshold, etc.) |
| Diagnostic Commands | 5-10 commands | What to run to understand the situation |
| Remediation Options | 2-4 options | Specific commands for the most likely causes |
| Rollback | 1-3 commands | If the remediation makes it worse, how to undo |
| Service Dependencies | 3-7 entries | Upstream / downstream services with health-check links |
| Escalation Trigger | 1-2 lines | The condition that elevates this from a page response to an incident |

## Instructions

### Step 1: Build the Alert Inventory

Before writing pages, list every alert that pages. For each, capture:

- Alert name (must match the alerting system's name exactly).
- Severity (PAGE / WARN / INFO -- only PAGE entries get a full runbook page; WARN entries optionally get a short reference).
- Paging team (the rotation that gets the page).
- Alert condition (the exact Prometheus expression / CloudWatch threshold / Datadog monitor).

If an alert pages but has no corresponding runbook page, that is a P0 gap. Write a placeholder page (Step 5 below) before merging.

### Step 2: Write the Quick Reference

The Quick Reference is the most important part of the page. It appears at the top so the on-call does not scroll during an active page.

The Quick Reference is 3-5 lines. It states:

- **The most likely cause** (the cause that fires this alert >50% of the time, if there is one).
- **The mitigation command** (the single command that resolves the most likely cause).
- **The "do not run this" warning** if there is a commonly-tried fix that makes things worse.

Example for a `checkout-error-rate-high` alert:

```
QUICK REFERENCE
- Most likely cause: db connection pool exhaustion (last 5 incidents)
- Mitigation: kubectl rollout restart deployment/checkout -n payments
- DO NOT: scale the deployment up before restarting (amplifies the bad pool state)
```

If there is no single dominant cause, state that explicitly and skip to the Diagnostic Commands section.

### Step 3: Document the Diagnostic Commands

The Diagnostic Commands section is 5-10 copy-pasteable commands the on-call runs to understand the state. The rules:

- Plain shell, no pseudo-code.
- Each command has a one-line description of what it checks.
- Commands are ordered fastest-to-slowest and broadest-to-narrowest.

Example:

```
DIAGNOSTIC COMMANDS

# 1. Service health (5 sec)
curl -sf https://checkout.internal/healthz && echo "OK" || echo "FAIL"

# 2. Recent error rate (10 sec)
promtool query instant http://prometheus:9090 \
  'sum(rate(http_requests_total{service="checkout",code=~"5.."}[5m]))'

# 3. Pod state (5 sec)
kubectl get pods -l app=checkout -n payments

# 4. Recent restart count (5 sec)
kubectl get pods -l app=checkout -n payments -o jsonpath='{.items[*].status.containerStatuses[*].restartCount}'

# 5. Recent deploys in last hour (10 sec)
kubectl rollout history deployment/checkout -n payments | tail -5
```

### Step 4: Document the Remediation Options

For each likely cause, document the specific remediation. The structure:

```
REMEDIATION OPTIONS

Option A: Pool exhaustion (most common)
  Signal: high `db_pool_in_use` metric in diagnostic 2 above.
  Action: kubectl rollout restart deployment/checkout -n payments
  Expected recovery: 2-3 minutes
  Verify: error rate drops below 1% within 5 minutes

Option B: Downstream dependency degraded
  Signal: high error rate on `payments-gateway` health check (diagnostic 6).
  Action: enable circuit breaker via feature flag `payments_gateway_circuit_breaker=true`
  Expected recovery: 30 seconds
  Verify: error rate drops; circuit-breaker metric shows open state

Option C: Bad deploy
  Signal: deploy in last hour (diagnostic 5) coincides with error rate climb.
  Action: helm rollback checkout <previous-revision>
  Expected recovery: 3-5 minutes
  Verify: error rate drops; deploy version matches previous-revision
```

Each option must have: Signal (how to confirm), Action (the command), Expected recovery (the duration), Verify (the success check).

### Step 5: Write the Placeholder Page for Unknown Causes

For an alert that has no known dominant cause yet, write a placeholder page that follows the diagnostic-first pattern:

```
QUICK REFERENCE
- This alert has no known dominant cause yet. Run the diagnostics below.
- If the cause becomes clear from diagnostics, follow the matching remediation in the related runbooks list.
- If no cause is clear after 10 minutes of diagnosis, escalate to the service owner.

DIAGNOSTIC COMMANDS
... (5-10 commands as above)

REMEDIATION OPTIONS
- No prior remediation patterns established. Document the cause and remediation in this runbook after the page is resolved.
```

The placeholder is fully acceptable. The unacceptable state is "alert pages but no runbook exists at all".

### Step 6: Build the Escalation Matrix

The Escalation Matrix is a single table for the whole service or team, not per-alert.

| Alert class | Page on-call | Escalate after | Escalate to | How |
|---|---|---|---|---|
| Payments-related PAGE | @payments-oncall | 15 minutes unresolved | @payments-lead | PagerDuty escalation policy `pay-l2` |
| Authentication PAGE | @platform-oncall | 10 minutes unresolved | @platform-lead | PagerDuty `plat-l2` |
| Data pipeline PAGE | @data-oncall | 30 minutes unresolved | @data-lead | PagerDuty `data-l2` |
| Any PAGE during freeze | + @release-captain | immediately | release-captain | Slack @here in #release-coord |

The rules:

- Every paging alert class has a row.
- Every row has an escalation time (a number of minutes), not a vague trigger.
- Every row has a contact path (the specific PagerDuty policy or Slack handle), not just a name.

### Step 7: Build the On-Call Handoff Template

The On-Call Handoff is the standard document the outgoing on-call sends to the incoming on-call at shift change. The template:

```
On-Call Handoff -- <date>
Outgoing: <name>
Incoming: <name>

ACTIVE ISSUES (require attention this shift)
- <one line per issue>: <link to incident or ticket>

WATCH ITEMS (no action now, but flagged)
- <one line per item>: <reason and threshold>

OPEN PAGES THIS SHIFT
- <alert name> -- <when> -- <resolution or current state>

KNOWN BAD STATES
- <e.g. "checkout-canary at 10%, do not promote">

UPCOMING WORK
- <e.g. "scheduled cert rotation Friday 14:00 UTC, runbook: <link>">

CONTACT FOR QUESTIONS
- <outgoing on-call's contact method for the first 4 hours of the new shift>
```

The template enforces a structured handoff. Free-form "anything I should know?" handoffs lose context across the rotation.

### Step 8: Stamp Each Page with Metadata

Every per-alert page ends with:

- **Last reviewed**: date.
- **Next review due**: date (default cadence: 3 months for paging runbooks; shorter than general runbooks because alert configurations change more often).
- **Owner**: the on-call rotation or team that owns the alert.
- **Last paged**: the date the alert last fired (refreshed automatically if integrated with the paging system; otherwise updated by the on-call who resolves a page).
- **Related**: links to general runbooks and recent postmortems that involved this alert.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We can figure it out at 3am from the dashboard" | At 3am you can read three commands and run two. You cannot reason from a dashboard you have not seen before. The runbook exists so that the on-call's 3am cognitive load is "follow steps", not "investigate from scratch". |
| "The previous on-call left notes in Slack, that's enough" | Slack notes are not searchable in the paging app, do not survive Slack retention policies, and are not stamped with a review date. Notes are an input to the runbook, not a replacement for it. |
| "Most alerts auto-resolve so a runbook is overkill" | "Most" is a great reason to write a one-line Quick Reference ("This alert auto-resolves in <5 min in 90% of cases. If it has not resolved in 10 min, run the diagnostics below."). Overkill is shorter than scrambling. |
| "We don't have a known cause yet so writing it is premature" | The placeholder page (Step 5) is the answer. A diagnostic-first page is fully acceptable. The unacceptable state is "alert pages, no runbook page exists at all". |
| "The escalation is obvious: ping the team lead" | Team leads rotate; vacation schedules vary; on-call rotations cover for each other. "Obvious" is fragile. The matrix names the specific path, the specific time threshold, and the specific contact method. |

## Verification

Before publishing the on-call runbook, walk this binary checklist. Every item must be true.

- [ ] Every paging alert in the alert inventory has a corresponding entry in the runbook (placeholder pages count).
- [ ] Every per-alert page has the Quick Reference at the top.
- [ ] The Quick Reference contains the mitigation command (or explicitly says "no dominant cause, run diagnostics").
- [ ] Every Diagnostic Commands section is plain shell, copy-pasteable, with a one-line description per command.
- [ ] Every Remediation Option states a Signal, an Action, an Expected recovery, and a Verify step.
- [ ] The Rollback section is present and gives a command that undoes the most likely remediation if it makes things worse.
- [ ] The Service Dependencies section names upstream and downstream services with health-check links.
- [ ] The Escalation Matrix has one row per paging alert class.
- [ ] Every Escalation Matrix row has a numeric time threshold (in minutes) and a specific contact method.
- [ ] The On-Call Handoff Template is present and structured (Active / Watch / Open Pages / Known Bad States / Upcoming / Contact).
- [ ] Every page is stamped with Last reviewed, Next review due, Owner, and Related links.

If any item is false, do not publish. Fix the runbook.

## Related Skills

- [[sre-engineer]] -- the SRE practice. The on-call runbook is one of several artifacts in the practice; this skill is the artifact-producer.
- [[runbook-writer]] -- general operational runbooks. The general runbook is longer and procedural; the on-call runbook is per-alert and short. Cross-link from this runbook's "Related" metadata to the matching general runbooks.
- [[incident-postmortem]] -- the writeup of a specific past incident. Postmortem action items frequently update the on-call runbook for the alert involved in the incident.
- [[observability-setup]] -- the alerting pipeline. The on-call runbook documents the response to alerts; the observability setup designs the alerts themselves. If a page has no actionable response, the alert (not the runbook) is the gap.
