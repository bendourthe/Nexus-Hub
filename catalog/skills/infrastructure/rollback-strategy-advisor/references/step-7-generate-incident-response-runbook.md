### Step 7: Generate Incident Response Runbook

**Rollback Runbook Template** (`runbooks/rollback-runbook.md`):

```markdown
# Rollback Runbook: [Service Name]

## Quick Reference

| Item                | Value                              |
|---------------------|------------------------------------|
| Service             | myapp                              |
| Namespace           | app-production                     |
| Current Version     | v2.5.0 (abc1234)                   |
| Previous Version    | v2.4.3 (def5678)                   |
| Rollback Type       | Immediate / Data-Aware / Flag      |
| Estimated Duration  | 5 minutes                          |
| Last Tested         | 2026-02-28                         |

## Decision Tree

1. Is the issue caused by a feature behind a feature flag?
   - YES: Go to "Feature Flag Rollback" below
   - NO: Continue to step 2

2. Does the deployment include database schema changes?
   - YES: Go to "Database Migration Rollback" below
   - NO: Continue to step 3

3. Is this a blue-green deployment?
   - YES: Go to "Blue-Green Switchback" below
   - NO: Go to "Immediate Rollback" below

## Immediate Rollback

Run the following command:

    bash scripts/rollback-immediate.sh app-production myapp

Verification:
- [ ] Rollout status shows complete
- [ ] All pods are ready
- [ ] Health endpoint returns 200
- [ ] Error rate has decreased
- [ ] No new errors in application logs

## Feature Flag Rollback

Run the following command:

    bash scripts/rollback-feature-flag.sh new-checkout-flow launchdarkly

Verification:
- [ ] Flag shows as disabled in LaunchDarkly dashboard
- [ ] Application serves old behavior
- [ ] No errors related to the disabled feature

## Communication Template

Subject: [INCIDENT] Production rollback for [service name]

Body:
We have initiated a rollback of [service name] from [new version]
to [previous version] due to [brief description of issue].

Timeline:
- [HH:MM UTC] Issue detected: [description]
- [HH:MM UTC] Rollback initiated by [name]
- [HH:MM UTC] Rollback completed
- [HH:MM UTC] Verification passed

Impact: [description of user impact]
Status: [Monitoring / Resolved]
Next steps: [RCA scheduled / fix in progress]

## Escalation

| Level   | Contact          | When                                     |
|---------|------------------|------------------------------------------|
| L1      | On-call engineer | First responder, executes runbook         |
| L2      | Team lead        | Rollback fails or impact unclear          |
| L3      | VP Engineering   | Extended outage (>30 min) or data loss    |
```
