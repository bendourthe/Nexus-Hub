---
name: sre-engineer
description: Site reliability engineering expertise for building and maintaining reliable production systems. Use when defining SLOs/SLIs/error budgets, designing incident response runbooks, implementing observability pipelines, capacity planning, or conducting post-incident reviews.
summary_l0: "Build reliable production systems with SLOs, incident response, and capacity planning"
overview_l1: "This skill provides specialized expertise in site reliability engineering, covering service-level objectives, observability, incident management, capacity planning, reliability patterns, and toil reduction. Use it when defining SLOs/SLIs/error budgets, designing incident response runbooks, implementing observability pipelines, capacity planning, conducting post-incident reviews, reducing operational toil, or implementing chaos engineering. Key capabilities include SLO/SLI/error budget definition and tracking, incident response runbook creation, observability pipeline design, capacity planning and forecasting, post-incident review facilitation, toil identification and automation, reliability pattern implementation, and chaos engineering experiment design. The expected output is SLO definitions, incident runbooks, capacity plans, observability configurations, and toil reduction proposals. Trigger phrases: SRE, site reliability, SLO, SLI, error budget, incident response, runbook, capacity planning, post-incident review, toil reduction, chaos engineering."
---

# SRE Engineer

Specialized expertise in site reliability engineering, providing guidance on service-level objectives, observability, incident management, capacity planning, reliability patterns, and toil reduction. Grounded in the principles from Google's SRE books and adapted for real-world production environments.

## When to Use This Skill

Use this skill for:

- Defining SLOs, SLIs, and error budgets for services
- Designing and implementing observability pipelines (metrics, logs, traces)
- Building incident response processes and on-call rotations
- Conducting blameless post-incident reviews
- Capacity planning, load testing, and autoscaling design
- Implementing reliability patterns (circuit breakers, retries, bulkheads)
- Measuring and reducing operational toil
- Chaos engineering and resilience validation

**Trigger phrases**: "SLO", "SLI", "error budget", "incident response", "postmortem", "observability", "on-call", "capacity planning", "chaos engineering", "toil reduction", "reliability", "burn rate", "load shedding"

## What This Skill Does

Provides production-ready SRE patterns including:

- **SLOs/SLIs**: Service-level objective definitions, indicator measurement, error budget policies
- **Observability**: Metrics, logs, and traces pipeline design with correlation
- **Incident Management**: Severity levels, on-call design, commander protocols, communication templates
- **Post-Incident Review**: Blameless postmortem templates, contributing factor analysis, action tracking
- **Capacity Planning**: Load testing, autoscaling policies, resource quotas, cost optimization
- **Reliability Patterns**: Circuit breakers, retry strategies, graceful degradation, chaos engineering
- **Toil Reduction**: Measurement frameworks, automation ROI, self-healing systems, GitOps

## Instructions

### Step 1: Define SLOs, SLIs, and Error Budgets

Full walkthrough: [step-1-define-slos-slis-and-error-budgets.md](references/step-1-define-slos-slis-and-error-budgets.md) (load this step when you reach it).

### Step 2: Design the Observability Stack

Full walkthrough: [step-2-design-the-observability-stack.md](references/step-2-design-the-observability-stack.md) (load this step when you reach it).

### Step 3: Build Incident Management Processes

Full walkthrough: [step-3-build-incident-management-processes.md](references/step-3-build-incident-management-processes.md) (load this step when you reach it).

### Step 4: Conduct Post-Incident Reviews

Full walkthrough: [step-4-conduct-post-incident-reviews.md](references/step-4-conduct-post-incident-reviews.md) (load this step when you reach it).

### Step 5: Plan Capacity and Scaling

Full walkthrough: [step-5-plan-capacity-and-scaling.md](references/step-5-plan-capacity-and-scaling.md) (load this step when you reach it).

### Step 6: Implement Reliability Patterns

Full walkthrough: [step-6-implement-reliability-patterns.md](references/step-6-implement-reliability-patterns.md) (load this step when you reach it).

### Step 7: Reduce Toil Through Automation

Full walkthrough: [step-7-reduce-toil-through-automation.md](references/step-7-reduce-toil-through-automation.md) (load this step when you reach it).

## Best Practices

- **Set SLOs before building features**: reliability targets should drive architectural decisions, not be retrofitted after launch
- **Alert on symptoms, not causes**: users care about error rates and latency, not CPU utilization or disk space in isolation
- **Keep error budgets visible**: display remaining budget on team dashboards so everyone understands the reliability posture
- **Practice incidents before they happen**: run regular game days and tabletop exercises with realistic failure scenarios
- **Automate the second occurrence**: the first time a manual task appears, document it as a runbook; the second time, automate it
- **Measure toil quarterly**: track the percentage of engineering time spent on toil and set reduction targets
- **Make postmortems blameless in practice, not just in policy**: focus on system improvements, and never name individuals as root causes
- **Use progressive rollouts**: canary deployments, feature flags, and traffic shifting reduce the blast radius of changes
- **Test your monitoring**: if you have never seen an alert fire, you do not know if it works
- **Keep runbooks current**: stale runbooks are worse than no runbooks because they create false confidence

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll aim for 100% uptime, more nines is always better" | Chasing 100% spends the error budget that should fund release velocity and feature work; an SLO below 100% with an explicit error budget is what lets you ship and still be reliable, rather than freezing in fear of any failure. |
| "Alert on every error so nothing slips through" | Alerting on raw error count pages on-call for noise and trains them to ignore alerts (alert fatigue); symptom-based, burn-rate alerts tied to the SLO page only when users are actually affected. |
| "The postmortem should name who caused the outage" | A blame-focused postmortem makes engineers hide information, so the real contributing factors never surface; blameless review is what produces action items that actually prevent recurrence. |
| "This manual ops task is quick, automating it is not worth it" | A quick task repeated daily across an on-call rotation is exactly the toil that compounds into burnout and error; if it is repetitive, automatable, and tactical, it meets the definition of toil to be eliminated. |

## Verification

- [ ] Each critical service has an SLO with a defined SLI and an explicit error-budget policy.
- [ ] Alerts are symptom-based and tied to SLO burn rate, not raw error counts (no alert fires without user impact).
- [ ] Incident response defines severity levels, an on-call rotation, and a commander/communication protocol.
- [ ] Post-incident reviews are blameless and produce tracked action items with owners.
- [ ] Identified toil is quantified and has an automation proposal, not just acknowledged.

## Related Skills

- [[cloud-architect]] -- cloud infrastructure design
- [[kubernetes-expert]] -- container orchestration and scaling
- [[observability-setup]] -- monitoring and alerting implementation
- [[terraform-specialist]] -- infrastructure as code
- [[cicd-architect]] -- deployment pipeline design

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Google SRE books, OpenTelemetry standards, Kubernetes best practices


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
