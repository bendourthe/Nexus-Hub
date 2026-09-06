### Step 3: Build Incident Management Processes

Effective incident management requires clear severity definitions, well-structured on-call rotations, defined roles, and communication protocols that minimize confusion during high-stress situations.

**Incident Severity Levels**:

| Severity | Criteria | Response Time | Notification | Example |
|----------|----------|--------------|--------------|---------|
| **SEV1** | Service down, all users affected, revenue impact | 5 minutes | Page on-call + IC + leadership | Complete checkout outage |
| **SEV2** | Major degradation, many users affected | 15 minutes | Page on-call + IC | Checkout latency 10x normal |
| **SEV3** | Partial degradation, subset of users affected | 30 minutes | Notify on-call | One payment provider failing |
| **SEV4** | Minor issue, workaround available | Next business day | Ticket | Slow dashboard loading |

**On-Call Rotation Configuration (PagerDuty)**:

```yaml
# pagerduty-terraform.tf equivalent as YAML spec
on_call_schedule:
  name: "platform-primary"
  timezone: "UTC"
  rotation:
    type: weekly
    handoff_time: "09:00"
    handoff_day: monday
    participants:
      - engineer_a
      - engineer_b
      - engineer_c
      - engineer_d
    # Minimum 4 engineers for sustainable rotation

escalation_policy:
  name: "platform-escalation"
  rules:
    - level: 1
      target: "platform-primary"        # On-call engineer
      timeout_minutes: 5
    - level: 2
      target: "platform-secondary"      # Backup on-call
      timeout_minutes: 10
    - level: 3
      target: "platform-engineering-manager"
      timeout_minutes: 15

on_call_expectations:
  acknowledgement_sla: "5 minutes for SEV1, 15 minutes for SEV2"
  laptop_required: true
  alcohol_restriction: true
  handoff_checklist:
    - "Review open incidents and active alerts"
    - "Check error budget dashboards"
    - "Read handoff notes from previous on-call"
    - "Verify pager and notification settings"
```

**Incident Commander Checklist**:

```markdown
## Incident Commander Actions

### First 5 Minutes
- [ ] Acknowledge the page and claim IC role
- [ ] Open incident channel: #inc-YYYYMMDD-short-description
- [ ] Post initial assessment: what is broken, who is affected, estimated severity
- [ ] Page additional responders if needed (subject matter experts)
- [ ] Start the incident timeline document

### Ongoing (every 15 minutes)
- [ ] Post status update to incident channel
- [ ] Update status page if customer-facing
- [ ] Coordinate between investigation streams
- [ ] Decide: escalate, mitigate, or continue investigating
- [ ] Track action items and owners

### Resolution
- [ ] Confirm service recovery with monitoring data
- [ ] Post final status update
- [ ] Update status page to resolved
- [ ] Schedule postmortem within 48 hours
- [ ] Send incident summary to stakeholders
```

**Communication Templates**:

```markdown
## Initial Notification (Internal)
INCIDENT DECLARED - SEV[1/2]
Service: [service name]
Impact: [user-facing description of the problem]
Start time: [HH:MM UTC]
IC: [name]
Channel: #inc-[date]-[slug]
Status page: [link]

## Status Page Update (External)
Title: [Service] Degraded Performance
Status: Investigating
Body: We are investigating reports of [brief description]. Some users
may experience [specific symptoms]. Our engineering team is actively
working on resolution. We will provide updates every 30 minutes.

## Resolution Notification (Internal)
INCIDENT RESOLVED - SEV[1/2]
Service: [service name]
Duration: [X hours Y minutes]
Root cause: [one sentence]
Mitigation: [what was done to fix it]
Postmortem scheduled: [date/time]
Action items: [count] items tracked in [link]
```
