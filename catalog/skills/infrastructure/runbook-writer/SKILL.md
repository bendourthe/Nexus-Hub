---
name: runbook-writer
description: "Produce an operational runbook for a service, incident type, or deployment procedure. Make sure to use this skill whenever the user mentions runbook, operational runbook, ops guide, deployment runbook, maintenance procedure, disaster recovery runbook, DR runbook, ops playbook, or asks for a step-by-step procedure that another engineer can follow at 3am. SKIP: incident postmortems (use `incident-postmortem`), per-alert paging response runbooks (use `oncall-runbook`), customer-facing how-to guides (use `user-documentation`)."
summary_l0: "Write copy-pasteable operational runbooks with rollback, troubleshooting, and escalation"
overview_l1: "This skill produces an operational runbook -- a step-by-step procedural document an on-call engineer can follow at 3am with no prior context. It supports four runbook types (Deployment, Incident Response, Maintenance, Disaster Recovery), each with a tailored output structure that always includes Overview, Prerequisites, Step-by-Step Procedures, Rollback Steps, Troubleshooting Table, and Escalation Paths. Every procedure step is an exact command or click-path (not a description); every step has a verification check; every runbook has reversible rollback steps; every troubleshooting row has a specific symptom and a specific resolution. Use it for new service onboarding, deploy procedures, planned maintenance windows, DR drills, and any operational procedure that more than one engineer needs to execute. Trigger phrases: runbook, operational runbook, ops guide, deployment runbook, maintenance procedure, DR runbook."
---

# Runbook Writer

Produce a complete operational runbook for a service, incident type, or procedure. The runbook is designed for a single use case: a tired on-call engineer reads it at 3am and can execute every step without prior context.

This skill is opinionated on five points: every step is a **copy-pasteable command** (not a prose description); every step has a **verification check** so the operator knows whether it worked; every runbook has **reversible rollback steps**; every troubleshooting row pairs **a specific symptom with a specific resolution**; and the runbook is **dated and owned** so stale runbooks can be triaged.

## When to Use This Skill

Use this skill for:

- New service onboarding -- the operational runbook that documents how to deploy, restart, scale, and recover the service.
- Deployment procedures that go beyond `git push` (database migrations, dual-deploy, blue-green, canary stages with manual gates).
- Maintenance windows -- planned downtime procedures, certificate rotations, dependency upgrades, scheduled failovers.
- Disaster recovery -- region failover, restore-from-backup, data corruption recovery.
- Any procedure that more than one engineer will execute, especially under time pressure or with imperfect information.

**Trigger phrases**: "runbook", "operational runbook", "ops guide", "deployment runbook", "maintenance procedure", "DR runbook", "disaster recovery runbook", "ops playbook", "operations guide".

### When NOT to use this skill

- **Incident postmortems** -- the writeup of a specific incident after the fact uses `incident-postmortem`. A runbook is the procedure; the postmortem is the historical artifact.
- **Per-alert paging response runbooks** -- the short response procedure for a specific alert (e.g. "what to do when `checkout-error-rate-high` pages") uses `oncall-runbook`. A general runbook is broader and longer; an on-call runbook is one page per alert.
- **Customer-facing how-to guides** -- end-user documentation uses `user-documentation`. A runbook is for internal operators.

## What This Skill Does

Selects one of four runbook types based on the user's input, then produces the matching output structure.

| Runbook type | Primary use case | Output sections |
|---|---|---|
| **Deployment** | Releasing the service to staging or production | Overview, Prerequisites, Pre-flight checks, Deploy procedure, Verification, Rollback, Troubleshooting, Escalation |
| **Incident Response** | Recovering from a class of incidents (not a single past incident) | Overview, Detection signals, Diagnostic procedure, Containment, Mitigation, Recovery, Rollback, Troubleshooting, Escalation |
| **Maintenance** | Planned ops work (cert rotation, dep upgrades, failovers) | Overview, Prerequisites, Pre-work communication, Maintenance procedure, Verification, Rollback, Troubleshooting, Escalation |
| **Disaster Recovery** | Catastrophic failures (region loss, data corruption) | Overview, Prerequisites, Detection criteria, Failover/restore procedure, Verification, Cutback procedure, Troubleshooting, Escalation |

## Instructions

### Step 1: Gather the Required Inputs

Before writing, collect:

- **Runbook type** -- Deployment / Incident Response / Maintenance / Disaster Recovery.
- **System / service** -- the exact service name, version (if applicable), and repository link.
- **Audience** -- on-call engineer, deploy engineer, release captain, all of the above. The reading level is always "tired engineer at 3am" regardless of nominal audience.
- **Tech stack** -- relevant tools, versions, and access requirements (cloud provider, container orchestrator, CI/CD system).
- **Existing access prerequisites** -- IAM roles, VPN, kubectl context, bastion host, MFA tokens.
- **Estimated time** -- best-case and worst-case duration for the procedure.

If any of these are missing, request them before drafting.

### Step 2: Write the Overview

The Overview is 5-10 lines max. It answers four questions:

1. What does this runbook do?
2. When should you run it?
3. When should you NOT run it (escalate instead)?
4. What is the expected duration and the worst-case duration?

If the answer to "when should you NOT run it" is long enough to be its own runbook, write that runbook too and cross-link.

### Step 3: Document the Prerequisites Concretely

The Prerequisites section lists every required access, tool, and pre-condition. Each entry is a binary check the operator can run before starting.

Example:

- **Access**: IAM role `deploy-prod-checkout` (request via `https://access.internal/request`).
- **Tools**: `kubectl` v1.29+, `helm` v3.13+, AWS CLI v2.
- **Context**: `kubectl config use-context prod-us-east-1` returns "Switched to context".
- **Auth**: `aws sts get-caller-identity` returns the prod-deployer ARN.
- **Pre-state**: The previous deploy has finished (`kubectl rollout status deploy/checkout` returns "successfully rolled out").
- **Pre-work**: A change ticket has been filed in ChangeTracker (link).

A prerequisite that the operator cannot verify with a single command is not a prerequisite; it is a wish.

### Step 4: Write the Procedure as Copy-Pasteable Commands

This is the operational heart of the runbook. The rules:

- Every step is a **command**, not a description. Wrong: "Restart the checkout service." Right: ``kubectl rollout restart deployment/checkout -n payments``.
- Every step has a **verification check**. Wrong: ``kubectl rollout restart deployment/checkout``. Right: ``kubectl rollout restart deployment/checkout && kubectl rollout status deployment/checkout --timeout=5m``.
- Every step states an **expected output**. The operator should know whether the step worked without consulting the runbook author.
- If a step requires a click-path in a web console, write the exact click-path: "1. Open `https://console.aws.amazon.com/route53/`. 2. Select the `internal-zone` hosted zone. 3. Click `Edit record` on the `checkout.internal` record."
- If a step is conditional, state the condition explicitly: "**If the cluster's restart-count metric is above 100**, run the canary procedure instead (Section 5b). **Otherwise**, proceed to Step 6."

Number the steps. Do not nest sub-steps more than one level deep.

### Step 5: Write the Rollback Steps

Every runbook has a Rollback section. The rules:

- Rollback steps must be **reversible**. If a step in the main procedure cannot be cleanly reversed, it must be flagged in the main procedure as `IRREVERSIBLE` and the rollback section explains the recovery path (restore from backup, escalate, etc.).
- Rollback steps must be **executable without the original procedure's success**. If the deploy failed half-way, the rollback must work from any intermediate state.
- The expected rollback time must be stated.

Example acceptable rollback step: ``helm rollback checkout 1 && kubectl rollout status deployment/checkout --timeout=5m`` (rollback to release 1; expected duration: 3 minutes).

### Step 6: Build the Troubleshooting Table

The Troubleshooting section is a table, not prose. Each row pairs a specific symptom with a specific resolution.

| Symptom | Likely cause | Resolution |
|---|---|---|
| `kubectl rollout status` times out after 5 minutes | Pod is failing readiness probe | `kubectl describe pod -l app=checkout` -> check Events -> resolve based on probe failure |
| `helm upgrade` fails with `release in failed state` | Previous deploy left release in `failed` | `helm history checkout`; `helm rollback checkout <previous-revision>`; restart procedure |
| `aws sts get-caller-identity` returns `ExpiredToken` | MFA token expired | Re-run `aws-mfa --token <token>` and retry |
| Service deploys but health check fails | Configuration drift | `kubectl get configmap checkout-config -o yaml | diff - expected-config.yaml` |

Each row has three columns: Symptom (what the operator sees), Likely cause (the diagnostic hypothesis), Resolution (the next concrete command). No prose-only entries.

### Step 7: Document the Escalation Path

The Escalation section answers:

- **When to escalate** -- specific criteria. Wrong: "If you're stuck, escalate." Right: "If the rollback procedure has not restored service within 15 minutes, escalate."
- **Who to escalate to** -- the specific on-call rotation, named team, or named individual with their paging method.
- **What to tell them** -- the minimum context (incident ID, runbook section, current state, what has been tried).
- **When to declare an incident** -- the explicit criterion that elevates this from a procedure execution to an incident.

### Step 8: Stamp the Runbook with Metadata

Every runbook ends with metadata:

- **Last reviewed**: 2026-05-19
- **Next review due**: 2026-11-19
- **Owner**: @team-platform (or `@named-person` if no team owns it)
- **Estimated duration**: best-case 8 minutes, worst-case 45 minutes (deploy failure + rollback)
- **Related runbooks**: links to upstream / downstream procedures.

The Last reviewed / Next review due dates allow stale runbooks to be detected and triaged. The default review cadence is 6 months.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The team already knows how to do this" | The team knows it today. The team turns over; on-call schedules rotate; new hires join. The runbook exists for the engineer who does not yet know how, and that engineer is the person who needs it at 3am. |
| "It will go stale anyway" | A stamped, owned runbook with a review date can be triaged. An undocumented procedure is permanently stale. Stale-with-a-date is better than missing. |
| "We can write it after the next incident" | Writing under post-incident pressure produces a hurried runbook tied to one failure mode. The runbook should be written when the team has time to think about the full procedure, not when the team is in recovery. |
| "The script comments are enough" | Script comments are good but they do not document prerequisites, escalation, rollback, or the click-paths that are not in the script. The runbook is the document for procedures the operator follows; the script is the artifact the procedure invokes. |
| "We have a wiki article from 2 years ago" | Two-year-old wiki articles are not runbooks; they are archaeology. If the wiki article is still accurate, port it to the runbook format with a fresh `Last reviewed` date. If it is not accurate, the runbook is the rewrite. |
| "Verification checks are obvious, the operator will know" | The operator might know. The operator at 3am, after the third paging cycle, after the previous on-call's notes were unclear, will not know. Every step states its expected output. |

## Verification

Before publishing the runbook, walk this binary checklist. Every item must be true.

- [ ] The runbook type is declared (Deployment / Incident Response / Maintenance / Disaster Recovery).
- [ ] The Overview answers all four questions (what / when / when-not / duration).
- [ ] Every prerequisite is a binary check the operator can run with a single command.
- [ ] Every procedure step is an exact command or click-path, not a prose description.
- [ ] Every procedure step states an expected output or a verification check.
- [ ] Rollback steps are present and reversible, with an estimated rollback duration.
- [ ] Any irreversible step in the main procedure is flagged `IRREVERSIBLE`.
- [ ] The Troubleshooting section is a table with three columns (Symptom / Likely cause / Resolution); every row is specific.
- [ ] The Escalation section names the criterion, the contact, the message template, and the incident-declaration trigger.
- [ ] The runbook is stamped with Last reviewed, Next review due, Owner, and Estimated duration.
- [ ] No step references a deprecated tool, deprecated UI path, or deprecated endpoint (verified by spot-check against the current console / CLI).

If any item is false, do not publish. Fix the runbook.

## Related Skills

- [[sre-engineer]] -- the broader SRE practice in which runbooks live. The advisor for SLOs, error budgets, and operational design; this skill is the artifact-producer for procedures.
- [[incident-postmortem]] -- the writeup of a specific past incident. A frequent postmortem action item is "write or update the runbook for X"; that work goes through this skill.
- [[oncall-runbook]] -- the per-alert response runbook. An on-call runbook is shorter and narrower than a general runbook (one page per alert); use it when the procedure is keyed to a specific paging event.
- [[rollback-strategy-advisor]] -- the design of the rollback strategy itself. This skill writes the rollback section of the runbook; the rollback strategy advisor designs what the rollback should do.
- [[cd-pipeline-generator]] -- the CI/CD pipeline. Deployment runbooks frequently document procedures invoked by the pipeline; the pipeline generator designs the automation that the runbook describes.
