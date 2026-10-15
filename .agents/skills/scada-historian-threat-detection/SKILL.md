---
name: scada-historian-threat-detection
description: "Detect tampering and covert channels in SCADA servers and process historians. Use this skill whenever the user says \"historian tag tampering\", \"SCADA HMI persistence\", \"process-data integrity monitoring\", or wants detections on PI/IP.21-style historians. SKIP, do NOT use for, generic Windows EDR hunts with no process-data angle."
summary_l0: "Detect SCADA server and historian tag tampering and covert channels"
overview_l1: "This skill looks at HMI servers and historians as high-value OT assets: tag integrity, engineering-account use, and outbound channels hiding in process data. Trigger phrases: historian tag tampering, SCADA HMI persistence, process-data integrity monitoring."
mitre_attack: [T0878, T0891]
nist_csf: [DE.CM, PR.DS]
---

# SCADA and Historian Threat Detection

If the historian lies, every dashboard after it lies. Treat process-data stores as integrity assets, not as IT file servers.

## When to Use This Skill

Use this skill when:

- A historian or HMI farm is in scope
- Operators report impossible tag values
- Engineering accounts are shared

Do NOT use this skill when:

- The ask is endpoint malware triage with no process-data store

**Trigger phrases**: "historian tag tampering", "SCADA HMI persistence", "process-data integrity monitoring"

## Instructions

### Step 1: Map the data path

From field sensor to RTU to SCADA to historian to dashboard. Note where values can be written backwards.

### Step 2: Inventory privileged clients

Engineering workstations, OLE/DB consumers, and service accounts that can insert tags. Shared passwords are a finding.

### Step 3: Integrity-monitor high-consequence tags

Setpoint, interlock, and custody-transfer tags get checksums or dual-sourced compares. Informational tags do not page.

### Step 4: Watch for covert channels

Unusually precise floating-point payloads, new tags with incrementing names, and historian replication to unexpected hosts.

### Step 5: Preserve forensics without stopping the plant

Snapshot configurations and audit logs. Do not reboot an HMI as a first response during operations.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The historian is just a database | It is the plant's memory. Tampering it is an integrity attack on operations. |
| EDR on the HMI is enough | EDR will not notice a one-count change on a tank level tag. |
| We can restore from last night's backup immediately | Restoring a historian blindly can reintroduce the attacker or wipe the evidence of what operators saw. |

## Verification

- [ ] Data-path diagram exists
- [ ] High-consequence tags have an integrity check
- [ ] Engineering-account use is logged

## Related Skills

- [[ics-protocol-anomaly-detection]] -- protocol abuse often precedes historian tampering
- [[ot-incident-response]] -- confirmed tampering becomes an OT incident

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
