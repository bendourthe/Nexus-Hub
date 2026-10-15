### Step 4: Conduct Post-Incident Reviews

Blameless postmortems are the primary mechanism for organizational learning after incidents. The goal is to understand what happened, identify systemic improvements, and prevent recurrence without assigning individual blame.

**Blameless Postmortem Template**:

```markdown
# Postmortem: [Incident Title]

**Date**: YYYY-MM-DD
**Severity**: SEV-X
**Duration**: X hours Y minutes
**Author**: [name]
**Reviewers**: [names]
**Status**: Draft | In Review | Approved | Action Items Complete

## Executive Summary

[2-3 sentences describing what happened, the impact, and the resolution.
Write for an audience that was not involved in the incident.]

## Impact

- **Users affected**: [number or percentage]
- **Revenue impact**: [estimated dollar amount or "none"]
- **SLO impact**: [X% of monthly error budget consumed]
- **Duration of user-visible impact**: [time]
- **Support tickets generated**: [count]

## Timeline (all times UTC)

| Time | Event |
|------|-------|
| 14:00 | Deployment of checkout-api v2.3.1 begins |
| 14:05 | Error rate increases from 0.1% to 5% |
| 14:07 | Burn rate alert fires, on-call paged |
| 14:09 | On-call acknowledges, begins investigation |
| 14:15 | IC declared, incident channel opened |
| 14:22 | Root cause identified: database connection pool exhaustion |
| 14:25 | Rollback initiated |
| 14:31 | Rollback complete, error rate returning to baseline |
| 14:45 | Confirmed recovery, incident resolved |

## Contributing Factors

[List systemic factors, not individual mistakes. Use "the system"
or "the process" as the subject, never a person's name.]

1. **Missing connection pool limits**: The new database client library defaults to unlimited connections, and the deployment did not include explicit pool size configuration.
2. **No canary deployment**: The change was rolled out to 100% of instances simultaneously, preventing early detection of the issue in a smaller blast radius.
3. **Alert gap**: Existing alerts monitored HTTP error rates but not database connection pool utilization, delaying root cause identification by several minutes.

## What Went Well

- On-call response time was under 2 minutes
- Rollback procedure worked as documented
- Incident communication was clear and timely
- Status page was updated within 10 minutes

## What Could Be Improved

- Canary deployments should have caught this before full rollout
- Database connection metrics should be part of standard dashboards
- The deployment checklist does not include verifying connection pool settings

## Action Items

| ID | Action | Owner | Priority | Due Date | Status |
|----|--------|-------|----------|----------|--------|
| AI-1 | Add connection pool size to deployment checklist | @alice | P1 | 2026-04-01 | Open |
| AI-2 | Implement canary deployment for checkout-api | @bob | P1 | 2026-04-15 | Open |
| AI-3 | Add database connection pool utilization alert | @carol | P2 | 2026-04-05 | Open |
| AI-4 | Add connection pool dashboard panel | @carol | P3 | 2026-04-10 | Open |

## Lessons Learned

[Broader takeaways that apply beyond this specific incident.]

1. Library upgrades that change default connection behavior need explicit review of resource limits.
2. Any service handling financial transactions should use canary deployments.
3. Dashboard coverage should include all resource pool metrics (connections, threads, file descriptors).
```

**Action Item Tracking and Verification**:

```bash
#!/usr/bin/env bash
set -euo pipefail

# postmortem-tracker.sh - Track and verify postmortem action items
# Queries your issue tracker for open postmortem actions

log_info()  { printf "[INFO]  %s\n" "$*" >&2; }
log_error() { printf "[ERROR] %s\n" "$*" >&2; }

readonly LABEL="postmortem-action"
readonly OVERDUE_DAYS=14

check_overdue_actions() {
    local cutoff_date
    cutoff_date=$(date -d "-${OVERDUE_DAYS} days" +%Y-%m-%d 2>/dev/null \
                  || date -v-${OVERDUE_DAYS}d +%Y-%m-%d)

    log_info "Checking for postmortem actions overdue since ${cutoff_date}"

    local overdue_count
    overdue_count=$(gh issue list \
        --label "${LABEL}" \
        --state open \
        --json createdAt,title,assignees,number \
        --jq "[.[] | select(.createdAt < \"${cutoff_date}\")] | length")

    if [[ "${overdue_count}" -gt 0 ]]; then
        log_error "${overdue_count} postmortem action(s) are overdue"
        gh issue list \
            --label "${LABEL}" \
            --state open \
            --json number,title,assignees,createdAt \
            --jq ".[] | select(.createdAt < \"${cutoff_date}\") | \"#\(.number): \(.title) (assigned: \(.assignees | map(.login) | join(\", \")))\""
        return 1
    fi

    log_info "No overdue postmortem actions found"
    return 0
}

check_overdue_actions
```
