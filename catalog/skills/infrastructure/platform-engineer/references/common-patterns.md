## Common Patterns

### Pattern 1: New Service Golden Path

```
Developer opens Backstage -> Selects template -> Fills form
    -> Repo created with CI/CD, monitoring, docs
    -> First deploy to dev in < 30 minutes
    -> Registered in service catalog automatically
```

### Pattern 2: Self-Service Database Provisioning

```
Developer opens PR with database.yaml -> CI runs plan + policy check
    -> Cost estimate posted as PR comment -> Auto-approved under threshold
    -> Merge triggers provisioning -> Connection string in Vault
    -> ExternalSecret syncs to Kubernetes -> App reads from mounted secret
```

### Pattern 3: Progressive Delivery Pipeline

```
Push to main -> Build + test -> Deploy to staging (rolling)
    -> Automated smoke tests -> Deploy to production (canary 5%)
    -> Monitor error rate + latency -> Auto-promote or rollback
    -> Full rollout -> Notify Slack
```
