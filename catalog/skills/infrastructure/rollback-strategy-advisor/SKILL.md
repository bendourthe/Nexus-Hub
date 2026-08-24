---
name: rollback-strategy-advisor
description: Plans and implements rollback strategies for production deployments including database migration rollbacks, feature flag rollbacks, and incident response integration. Use when designing rollback procedures, recovering from failed deployments, or building deployment runbooks.
summary_l0: "Plan rollback strategies for deployments with database, feature flag, and incident procedures"
overview_l1: "This skill plans, implements, and tests rollback strategies across the full deployment stack, addressing real production complexity including database schema changes that cannot be naively reversed, stateful services with in-flight requests, feature flags gating partially-released functionality, and multi-service deployments. Use it when designing rollback procedures, recovering from failed deployments, building deployment runbooks, planning database migration rollbacks, implementing feature flag rollbacks, or integrating rollback into incident response. Key capabilities include application rollback strategy design, database migration rollback planning, feature flag rollback coordination, stateful service rollback handling, multi-service dependency rollback sequencing, rollback automation scripting, runbook template generation, and rollback testing procedures. The expected output is concrete rollback procedures, automation scripts, and runbook templates ready for incident response use. Trigger phrases: rollback, deployment rollback, failed deployment, database rollback, feature flag rollback, incident response, deployment runbook, recovery procedure."
---

# Rollback Strategy Advisor

Specialized skill for planning, implementing, and testing rollback strategies across the full deployment stack. This skill goes beyond simple "undo the last deploy" approaches to address the real complexity of production rollbacks: database schema changes that cannot be naively reversed, stateful services with in-flight requests, feature flags that gate partially-released functionality, and multi-service deployments where rolling back one service affects others. The output includes concrete rollback procedures, automation scripts, and runbook templates ready for incident response use.

## When to Use This Skill

Use this skill for:

- Designing rollback strategies before a risky production deployment
- Planning database migration rollbacks that preserve data integrity
- Implementing feature flag-based rollbacks for gradual feature releases
- Building blue-green switchback procedures with traffic verification
- Creating incident response runbooks that include rollback decision trees
- Evaluating whether a deployment is safe to roll back or requires a roll-forward fix
- Automating rollback triggers based on error rates, latency, or health check failures
- Coordinating rollbacks across multiple dependent microservices
- Testing rollback procedures in staging environments before production releases

**Trigger phrases**: "rollback strategy", "rollback plan", "deployment rollback", "undo deployment", "revert release", "production incident rollback", "database rollback", "migration rollback", "feature flag rollback", "blue-green switchback", "rollback runbook", "rollback automation"

## What This Skill Does

This skill follows a structured methodology for rollback planning:

1. **Deployment Analysis**: Examines the deployment to identify all components being changed (application code, database schema, configuration, infrastructure) and their interdependencies.

2. **Rollback Classification**: Categorizes the rollback type needed based on the change characteristics: immediate (stateless code change), gradual (traffic shifting), data-aware (schema migration), or composite (multi-component).

3. **Risk Assessment**: Evaluates rollback risks including data loss potential, service disruption duration, downstream dependency impact, and whether the rollback itself could cause failures.

4. **Procedure Generation**: Produces step-by-step rollback procedures with exact commands, verification checks at each step, and decision points where human judgment is required.

5. **Automation Scripting**: Creates executable rollback scripts that can be triggered manually or automatically, with safety checks and confirmation prompts built in.

6. **Runbook Integration**: Formats the rollback procedure as a runbook suitable for on-call engineers, with clear escalation paths and communication templates.

## Instructions

### Step 1: Classify the Rollback Type

Full walkthrough: [step-1-classify-the-rollback-type.md](references/step-1-classify-the-rollback-type.md) (load this step when you reach it).

### Step 2: Implement Immediate Rollback

Full walkthrough: [step-2-implement-immediate-rollback.md](references/step-2-implement-immediate-rollback.md) (load this step when you reach it).

### Step 3: Implement Database Migration Rollbacks

Full walkthrough: [step-3-implement-database-migration-rollbacks.md](references/step-3-implement-database-migration-rollbacks.md) (load this step when you reach it).

### Step 4: Implement Feature Flag Rollbacks

Full walkthrough: [step-4-implement-feature-flag-rollbacks.md](references/step-4-implement-feature-flag-rollbacks.md) (load this step when you reach it).

### Step 5: Implement Blue-Green Switchback

Full walkthrough: [step-5-implement-blue-green-switchback.md](references/step-5-implement-blue-green-switchback.md) (load this step when you reach it).

### Step 6: Multi-Service Rollback Coordination

Full walkthrough: [step-6-multi-service-rollback-coordination.md](references/step-6-multi-service-rollback-coordination.md) (load this step when you reach it).

### Step 7: Generate Incident Response Runbook

Full walkthrough: [step-7-generate-incident-response-runbook.md](references/step-7-generate-incident-response-runbook.md) (load this step when you reach it).

## Best Practices

- **Test rollbacks regularly**: A rollback procedure that has never been executed is an untested assumption. Run rollback drills in staging at least monthly, and in production (during maintenance windows) quarterly.

- **Maintain rollback-safe migrations**: Use the expand-contract pattern for all database schema changes. Never drop a column or table in the same release that adds its replacement. Separate the "expand" and "contract" phases into different releases with at least one release cycle between them.

- **Keep the previous version running**: In blue-green deployments, do not scale down the inactive environment immediately after switching traffic. Keep it running for at least the duration of your monitoring window (typically 30-60 minutes) so switchback is instant.

- **Document rollback decisions**: When you decide not to roll back (choosing to roll forward instead), document the reasoning. This creates institutional knowledge about when each approach is appropriate.

- **Automate with manual gates**: The rollback script should be fully automated, but triggering it should require a conscious human decision (except for automated canary rollbacks). This prevents false positive rollbacks from transient issues.

- **Version your rollback scripts**: Rollback scripts are critical infrastructure. Store them in version control, review changes, and tag them alongside application releases.

- **Include rollback time estimates**: Every runbook should state how long the rollback takes. This helps incident commanders set expectations and decide whether to roll back or roll forward.

- **Separate rollback permissions**: The ability to trigger a production rollback should be granted to on-call engineers without requiring elevated access that takes time to obtain during an incident.

## Common Pitfalls

- **Assuming all changes are rollback-safe**: Not every deployment can be safely rolled back. Destructive schema migrations, data format changes, and external API contract changes may make rollback impossible or harmful. Assess rollback safety before deploying, not during an incident.

- **Rolling back without verifying the target version**: Before rolling back, confirm that the target version is actually the one you want. If the previous version also had issues, rolling back to it will not help.

- **Forgetting about in-flight requests**: A rollback that happens while requests are in flight can cause errors if the old and new versions handle requests differently. Use graceful shutdown (preStop hooks, drain periods) to let in-flight requests complete.

- **Ignoring cache invalidation**: If your application caches data in a format specific to the new version, rolling back the code without clearing caches can cause deserialization errors or incorrect behavior.

- **Rolling back one service in a multi-service deployment**: If services A and B were deployed together because B depends on a new API in A, rolling back only B while leaving A on the new version can break the dependency contract. Always consider the full dependency graph.

- **No backup before database rollback**: Never execute a database migration rollback without first taking a backup. Even "safe" rollback migrations can have unexpected consequences.

- **Confusing "rollback" with "roll forward"**: Sometimes the fastest recovery is to push a fix rather than revert. If the fix is a one-line change and the rollback involves complex data migration, rolling forward is often the better choice. The runbook should help the responder make this decision.

- **Skipping post-rollback verification**: A rollback is not complete until the system is verified healthy. Always run health checks, check error rates, and confirm the user-facing behavior matches expectations after rolling back.

- **Not communicating during rollback**: An unannounced rollback confuses other team members who may be investigating the same incident. Always announce the rollback decision and its outcome in the incident channel.

- **Deleting the failed version's artifacts**: Keep the failed version's container image, build artifacts, and logs. You will need them for the post-incident review to understand what went wrong.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Rollback is just deploying the previous version, no plan needed" | A destructive schema migration or a data-format change cannot be naively reversed; assuming every deploy is rollback-safe is how an incident response makes the outage worse. Classify rollback safety before deploying, not during the incident. |
| "We'll figure out the rollback when something breaks" | An untested rollback procedure invented under incident pressure fails exactly when it is needed; the procedure must be written and rehearsed in staging before the risky deploy. |
| "Roll back the database migration, that undoes the change" | Reversing a migration without a fresh backup risks irreversible data loss if the reverse path is wrong; and a forward-only destructive migration has no safe reverse at all, making roll-forward the correct call. |
| "Roll back the one service that's erroring" | In a multi-service deploy where B depends on A's new API, reverting only B breaks the dependency contract; the full dependency graph determines the rollback sequence. |

## Verification

- [ ] Rollback safety is classified before deploy (immediate, gradual, data-aware, or composite), and roll-forward is chosen where reverse is unsafe.
- [ ] A fresh backup is taken before any database migration rollback.
- [ ] The rollback procedure has been tested in staging, not invented during the incident.
- [ ] Multi-service rollbacks follow the dependency graph; no service is reverted in isolation that breaks a contract.
- [ ] Post-rollback verification (health checks, error rate, user-facing behavior) is part of the runbook, and the failed version's artifacts are retained.

## Related Skills

- [[cd-pipeline-generator]] -- generates the deployment pipeline whose automated rollback job this strategy drives
- [[runbook-writer]] -- turns the rollback procedure into the operational runbook responders follow
- [[incident-postmortem]] -- consumes the retained failed-version artifacts to analyze what went wrong
- [[sre-engineer]] -- the incident-response and reliability practice this rollback strategy plugs into
