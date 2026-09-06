---
name: cloud-audit-log-detection
description: "Detect malicious activity in cloud control-plane audit logs across AWS CloudTrail, Azure Activity and Entra audit logs, and GCP Audit Logs by building detections for privilege escalation, IAM-based persistence, logging tamper, and unauthorized data-store access. Make sure to use this skill whenever the user says \"CloudTrail detection\", \"analyze cloud audit logs\", \"detect cloud privilege escalation\", \"Azure activity log hunting\", \"GCP audit log threats\", or \"detect IAM persistence in cloud logs\", including synonyms like \"who created this admin role\", \"find suspicious AssumeRole\", \"detect disabled logging events\", or \"control-plane threat hunting\". SKIP, do NOT use for: posture or misconfiguration scanning of static resource state (use cloud-security-posture-detection), or identity-provider sign-in anomaly detection such as impossible travel and MFA fatigue (use identity-threat-detection)."
summary_l0: "Detect malicious activity in AWS, Azure, and GCP control-plane audit logs"
overview_l1: "This skill teaches the agent to detect malicious activity inside cloud control-plane audit logs: AWS CloudTrail, Azure Activity and Entra audit logs, and GCP Audit Logs. It covers normalizing each provider's event schema to a common shape (actor, action, target, source, outcome, time), then building detection logic for the high-value control-plane abuse patterns: privilege escalation through policy and role manipulation, persistence created through new IAM principals, access keys, or trust relationships, tampering that disables or deletes logging, and unauthorized access to data stores. The skill emphasizes corroboration across events, suppression of known-good automation, and producing alerts with the actor, action, evidence event IDs, and a triage verdict. It is a detection-engineering and hunting lens over already-collected logs; it does not scan static resource configuration and does not analyze identity-provider sign-in telemetry."
mitre_attack: [T1078, T1098, T1530]
d3fend_techniques: [D3-PA]
nist_csf: [DE.CM, DE.AE, RS.AN]
---

# Cloud Audit Log Detection

Detect malicious activity in cloud control-plane audit logs across AWS, Azure, and GCP so privilege escalation, IAM-based persistence, logging tamper, and unauthorized data access are caught from the events the provider already records. This is a detection-engineering and hunting lens over collected logs, not a posture scan or a sign-in analytics tool.

## When to Use This Skill

- The user wants detections built over CloudTrail, Azure Activity or Entra audit, or GCP Audit Logs.
- A new admin role, policy attachment, or trust relationship was created and the user wants to know who did it and whether it is malicious.
- The user suspects persistence via newly created IAM users, access keys, or service accounts.
- Logging may have been disabled, deleted, or redirected and the tamper event needs to be detected.
- A data store (object storage, database, secrets store) may have been accessed by an unexpected principal.
- The user wants to hunt across already-collected control-plane events for adversary behavior.

**When NOT to use:**

- Scanning static resource configuration for public buckets, open ports, or wildcard IAM. Use [[cloud-security-posture-detection]].
- Detecting anomalous sign-ins, impossible travel, or MFA fatigue at the identity provider. Use [[identity-threat-detection]].
- Standing up the SIEM pipeline or correlation platform itself. Use [[siem-detection-engineering]].

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md). Vendor-native query examples per cloud (AWS CloudTrail, Azure Activity and Entra KQL, and GCP Audit Logs) are in [references/query-examples.md](references/query-examples.md).

### 1. Confirm log coverage and integrity

Verify that control-plane logging is enabled, multi-region where applicable, and delivered to a tamper-resistant destination before trusting any detection. Detections over partial logs produce false confidence. Record which accounts, regions, and log sources are in scope.

### 2. Normalize provider events to a common shape

Map each provider's schema to a shared event model so one detection can span clouds:

- Actor: the principal or identity that performed the action.
- Action: the API call or operation name.
- Target: the resource acted upon.
- Source: source IP, user agent, and session context.
- Outcome: success, failure, or error code.
- Time: event timestamp.

CloudTrail, Azure Activity and Entra audit, and GCP Audit Logs each name these fields differently; normalize once, detect everywhere.

### 3. Build detections for control-plane abuse patterns

Author detection logic for the high-value patterns, one rule per pattern:

- Privilege escalation: attaching admin-equivalent policies, modifying a role's permissions, or adding a principal to a privileged group.
- IAM persistence: creating new users or service accounts, generating long-lived access keys, or altering trust or assume-role relationships outside change windows.
- Logging tamper: stopping, deleting, or reconfiguring a trail, diagnostic setting, or audit sink; treat any logging-disable event as high severity.
- Data-store access: a principal reading or exporting object storage, database, or secrets-store contents outside its normal pattern.

Reference events with obviously fake values, such as principal `arn:aws:iam::000000000000:user/example-user` calling `CreateAccessKey`.

### 4. Suppress known-good and corroborate

Reduce noise without blinding the detection. Maintain an allowlist of approved automation principals, deployment pipelines, and change windows, and suppress matches that fully attribute to them. For surviving alerts, corroborate across events: a role creation followed by an access-key creation followed by a data export from a single actor is far stronger signal than any one event alone.

### 5. Emit triaged alerts

For each alert, output the actor, the action sequence, the evidence event IDs, the source context, a severity, and a triage verdict (benign automation, needs review, or likely malicious). Route likely-malicious alerts to incident response. Keep detection-as-code in version control so rules are reviewable and testable.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CloudTrail is on, so we are covered." | Single-region or management-event-only trails miss data-plane and cross-region activity; an adversary operating in an unlogged region leaves no trace, so coverage must be verified before detections are trusted. |
| "A logging-disable event is probably just an engineer cleaning up." | Disabling audit logging is a classic pre-attack step to blind defenders; treating it as routine is exactly how attackers buy themselves an unmonitored window, so every such event is high severity until attributed. |
| "One CreateRole event is too noisy to alert on." | Privilege-escalation and persistence chains are built from individually-benign events; correlating role creation with key creation and data export turns noise into a high-confidence detection that single-event filtering would discard. |
| "This export came from an internal IP, so it is safe." | Compromised credentials and SSRF make internal source IPs trivial to forge or pivot through; source IP alone is not authorization, so data-store access still requires actor-pattern corroboration. |
| "We will review the logs after an incident." | Audit logs age out or are tampered with; retroactive review without standing detections means the breach is discovered months late, when evidence has rotated and the actor has entrenched. |

## Verification

- [ ] A coverage record confirms which accounts, regions, and log sources are enabled and in scope.
- [ ] Events from each in-scope provider are normalized to the shared actor / action / target / source / outcome / time model.
- [ ] A detection exists for each of privilege escalation, IAM persistence, logging tamper, and data-store access.
- [ ] An allowlist of approved automation and change windows is applied, and suppressed matches are logged rather than silently dropped.
- [ ] Each emitted alert names the actor, the action sequence, the evidence event IDs, the severity, and a triage verdict.
- [ ] Detection rules are stored as version-controlled detection-as-code and are testable against sample events.

## Related Skills

- [[security-framework-mapping]] - map each detection to its ATT&CK, D3FEND, and NIST CSF identifier.
- [[cloud-security-posture-detection]] - find the static misconfigurations that these control-plane detections then watch for abuse of.
- [[identity-threat-detection]] - detect sign-in and identity-provider anomalies that often precede control-plane abuse.
- [[siem-detection-engineering]] - operationalize these detections in the SIEM with correlation, tuning, and alert routing.
