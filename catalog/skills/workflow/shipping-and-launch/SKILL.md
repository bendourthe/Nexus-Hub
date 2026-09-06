---
name: shipping-and-launch
description: "Confirms launch readiness and executes a safe, monitored deployment to production. Use at the end of any feature cycle, before any production deployment, or when coordinating a release across multiple services. Covers go/no-go decisions, pre-flight checks, deployment execution, and post-deployment verification. Trigger phrases: ready to ship, deploy to production, launch checklist, go/no-go, release this feature, time to deploy."
summary_l0: "Execute safe production deployments with pre-flight checks, go/no-go decisions, and post-launch verification"
overview_l1: "This skill provides a structured launch process covering pre-flight readiness checks, explicit go/no-go decision criteria, deployment execution steps, and post-deployment verification. Use it for any production deployment -- from a single service update to a coordinated multi-service release. Key capabilities include launch readiness assessment, staged rollout guidance, feature flag strategy, rollback planning, and post-launch monitoring setup. The expected output is a deployment that either reaches full production safely or rolls back cleanly with zero data loss. This skill is distinct from CI/CD pipeline design (infrastructure) -- it is the human+AI protocol for safely executing a deployment. Trigger phrases: ship this, deploy to production, launch checklist, go/no-go decision, release this feature, time to deploy."
---

# Shipping and Launch

Deploying to production is not the end of the feature -- it is the beginning of feedback. Ship deliberately, verify fast, and have a rollback plan before you deploy.

## When to Use This Skill

Use when:
- A feature is code-complete and needs to be released to production users
- Coordinating a release across multiple services
- Deploying a change that could affect data, authentication, or payments
- Setting up a staged rollout (canary, feature flags, percentage rollout)
- After an incident, verifying the fix is safe to deploy

**When NOT to use:** For setting up the CI/CD pipeline itself, use `cicd-architect` or `cd-pipeline-generator`. For rollback procedure design, use `rollback-strategy-advisor`.

## Canonical Pre-Merge Gate

Before a change is shared, it passes a fixed, ordered sequence of checks. The order is opinionated on purpose: when the gate is stable, "this change cleared the gate" means the same thing every time, instead of each change inventing its own ad hoc checklist. Each step names the skill that owns it, so the gate composes the per-step skills rather than redefining them.

Run the steps in this order, and finish each one before starting the next:

1. **Review the diff first.** The reviewer reads fresh code before any fix churns it. See [[intent-based-review]] and [[multi-agent-code-review]].
2. **Run tests and gather verification evidence.** Prove the change works, and capture the proof. See [[verification-before-completion]] and [[demo-capture]].
3. **Update documentation.** Do this after tests, so docs are written against code that is known to work.
4. **Run lint and static analysis.** Do this last among local checks, so it does not churn over code that may still change. See [[pre-commit-checklist]].
5. **Commit and push, only after every local check is clean.** Rebase onto fresh upstream first (see [[git-branching-workflow]]), then commit with a clean message and push (see [[code-commit-workflow]]).
6. **Open or update the PR.** See [[pr-description-writer]].
7. **Watch CI.** Let the remote checks run, and read their result.

The fixed order is the point, not a suggestion. A per-run skip (a docs-only change with no tests to add, say) is a deliberate, stated exception for that run, never a reason to reorder the gate itself.

### Stop at the Human-Decision Boundary

Distinguish "validated and ready for a human decision" from "the decision was made". The end of the gate is usually the former: the change is validated, CI is green, and the PR is open, but the merge is the human's call.

At that point, stop driving. Tell the user what is ready and what decision is now theirs, include the link they need to act, and hand control back. Do not block, poll, or re-run waiting for the human to act. An agent that busy-waits for a human merge wastes a turn loop and can re-trigger work it has already done; the right behavior is a crisp summary and the specific decision requested.

This generalizes beyond merges to any human-owned gate (an approval, a sign-off, a go-live window). See [[loop-engineering]] for the loop-side half of this rule, and [[verification-before-completion]] for the evidence that makes "ready" a true claim.

## The Launch Protocol

### Phase 1: Pre-Flight Checks (before deploying)

Complete every item. If any item fails, do not deploy until it is resolved.

**Code readiness:**
- [ ] All tests pass in CI (unit, integration, the relevant E2E paths)
- [ ] No known failing tests are skipped with a `TODO: fix` comment
- [ ] Code review approved by at least one other engineer
- [ ] Linting and type-checking pass cleanly

**Feature readiness:**
- [ ] Acceptance criteria from the spec are all verifiable as met
- [ ] The feature has been tested in a staging environment that mirrors production
- [ ] All known bugs for this release are either fixed or explicitly deferred with owner and date
- [ ] Documentation updated: API docs, user docs, changelog, runbook if applicable

**Operations readiness:**
- [ ] Monitoring and alerting configured for the new code path
- [ ] Rollback plan defined and rehearsed (not just documented)
- [ ] Database migrations are backwards-compatible (old code can run against new schema)
- [ ] Dependent services notified of breaking changes with a sunset date
- [ ] On-call engineer identified and available during the deployment window

### Phase 2: Go / No-Go Decision

Make the go/no-go decision explicitly. Do not drift into deployment because things "seem fine."

**GO criteria -- all must be true:**
- All pre-flight checks passed
- Staging environment verification complete
- Rollback plan documented and fast (< 15 minutes to revert)
- No active incidents on dependent services
- Deployment window is low-traffic (weekday, off-peak hours if possible)

**NO-GO triggers -- any one stops the deployment:**
- A failing test is skipped to make CI pass
- Rollback would require manual data migration
- Dependent service is degraded
- On-call is unavailable or unaware
- Staging behavior does not match expected production behavior

If any NO-GO trigger is present, document it, schedule the deployment for a later window, and address the trigger first.

### Phase 3: Deployment Execution

**If using feature flags (recommended for risky changes):**
1. Deploy the code with the feature behind a flag (flag defaulting to `false`)
2. Verify the deployment succeeded and old behavior is unchanged
3. Enable the flag for internal users only
4. Monitor for 30 minutes: errors, latency, anomalous metrics
5. Enable for 1% of users; monitor for 1 hour
6. Gradually increase to 10%, 50%, 100% with monitoring at each step
7. Remove the flag from code in the next release cycle

**If deploying directly:**
1. Announce in the team channel: "Deploying [feature] to [environment] now"
2. Execute the deployment command
3. Watch the deploy logs in real time -- do not step away
4. Confirm the deployment reached all nodes/containers (no partial deploys)
5. Immediately run post-deployment verification (Phase 4)

### Phase 4: Post-Deployment Verification

Do not close the deployment window until all of these pass:

**Smoke tests** (run immediately after deploy, < 5 minutes):
- [ ] The service starts and health checks return 200
- [ ] The primary user flow works end-to-end (login, core action, logout if applicable)
- [ ] No spike in error rates in the first 5 minutes (check dashboards)

**Monitoring window** (first 30 minutes after deploy):
- [ ] Error rate remains within the pre-deploy baseline ± 5%
- [ ] Latency (p50, p95) within pre-deploy baseline ± 20%
- [ ] Database CPU/connections not spiking
- [ ] No new alerts fired since deploy

**Feature-specific verification:**
- [ ] The specific user flow enabled by this feature works in production
- [ ] Any third-party integrations (payment, email, auth) are functioning
- [ ] Audit logs and events are being recorded as expected

### Phase 5: Rollback

If any post-deployment check fails:
1. Declare an incident immediately -- do not wait to see if it recovers
2. Execute the pre-defined rollback plan (revert deployment, disable feature flag, or database rollback)
3. Confirm the rollback is complete: health checks pass, error rates return to baseline
4. Write a brief incident summary while it is fresh
5. Post-mortem: determine root cause before attempting re-deploy

## Communication During Launch

Minimum communication checklist:
- [ ] Pre-deploy announcement in team/ops channel (who, what, when)
- [ ] Post-deploy status update (success or in-progress issue)
- [ ] Rollback announcement if triggered (no blame -- just facts)
- [ ] Brief follow-up for external users if the change is customer-visible

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It passed in staging, it'll be fine" | Staging is not production. Traffic patterns, data shapes, and integration behavior differ. The verification steps exist because staging lies. |
| "I'll add monitoring after it's out" | Monitoring added after deploy gives you no pre-deploy baseline. You cannot tell what changed if you don't know where you started. |
| "Rollback is easy -- I'll just redeploy the old version" | Rollback requires a tested, fast procedure. "I'll figure it out if it breaks" is not a rollback plan. |
| "It's a small change, the checklist is overkill" | Small changes cause incidents. The checklist is calibrated for frequency of failure, not size of change. |
| "We don't have time for a staged rollout" | You have time for the incident if it breaks. A 30-minute canary is faster than a 4-hour incident response. |

## Verification

- [ ] All pre-flight checks completed and documented before deployment began
- [ ] Go/no-go decision was made explicitly (not "let's just try it")
- [ ] Rollback plan was defined before deploying -- not during an incident
- [ ] Post-deployment smoke tests passed within 5 minutes of deploy
- [ ] Monitoring window completed without incidents or anomalies
- [ ] Team notified of deployment outcome (success or rollback)

## Related Skills

- [[cicd-architect]] -- design the CI/CD pipeline that automates pre-flight checks
- [[cd-pipeline-generator]] -- generate deployment pipeline configuration
- [[rollback-strategy-advisor]] -- design rollback procedures for complex deployments
- [[observability-setup]] -- instrument monitoring before this skill is needed
- [[sre-engineer]] -- SLO definitions and incident response procedures
