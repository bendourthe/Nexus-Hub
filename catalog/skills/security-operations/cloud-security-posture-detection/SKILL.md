---
name: cloud-security-posture-detection
description: "Detect risky cloud misconfigurations and posture drift across AWS, Azure, and GCP by inventorying resources and flagging public storage, over-permissive IAM, exposed compute or management ports, and disabled logging, then ranking findings for remediation. Make sure to use this skill whenever the user says \"cloud misconfiguration detection\", \"CSPM\", \"public storage bucket detection\", \"over-permissive IAM\", \"cloud posture review\", \"detect exposed cloud resources\", or \"find risky cloud settings\", including synonyms like \"open S3 bucket\", \"wildcard IAM policy\", \"security group 0.0.0.0/0\", or \"is my cloud account hardened\". SKIP, do NOT use for: cloud sign-in or identity anomaly detection (use identity-threat-detection), cloud audit-log hunting for active attacker behavior (use cloud-audit-log-detection), or infrastructure provisioning and IaC authoring (use terraform-specialist)."
summary_l0: "Detect risky cloud misconfigurations and posture drift across AWS, Azure, and GCP"
overview_l1: "This skill teaches the agent to detect and prioritize cloud security posture weaknesses across AWS, Azure, and GCP without changing infrastructure. It covers building a resource inventory from read-only APIs, evaluating each resource against a defensive baseline (publicly readable or writable storage, IAM principals with wildcard or administrative permissions, security groups and firewall rules that expose compute or management ports such as SSH, RDP, and database ports to the internet, and accounts where control-plane or flow logging is disabled), detecting drift from a previously approved baseline, and ranking findings by exposure and blast radius. The output is a triaged list of misconfigurations with the resource identifier, the rule violated, the evidence, and a remediation owner. This is a read-only assessment lens; it does not provision, modify, or delete resources, and it does not analyze runtime or sign-in telemetry."
mitre_attack: [T1078, T1578, T1530]
d3fend_techniques: [D3-PA]
nist_csf: [ID.RA, PR.AC, DE.CM]
---

# Cloud Security Posture Detection

Detect risky cloud misconfigurations and posture drift across AWS, Azure, and GCP so exposed storage, over-permissive identities, internet-facing management ports, and disabled logging are found and prioritized before an attacker exploits them. This is a read-only defensive assessment, not a provisioning or remediation tool.

## When to Use This Skill

- The user wants a point-in-time posture review of one or more cloud accounts, subscriptions, or projects.
- A storage bucket, blob container, or GCS bucket may be publicly readable or writable and needs detection.
- IAM roles, policies, or service principals may carry wildcard or administrative permissions that should be flagged.
- Security groups, network security groups, or VPC firewall rules may expose SSH, RDP, or database ports to the internet.
- Control-plane logging (CloudTrail, Azure Activity, GCP Audit) or flow logging may be disabled on some accounts.
- The user wants to compare the current configuration against a previously approved baseline and report drift.

**When NOT to use:**

- Detecting anomalous sign-ins, impossible travel, or identity-provider attacks. Use [[identity-threat-detection]].
- Hunting active attacker behavior inside cloud control-plane audit logs. Use [[cloud-audit-log-detection]].
- Writing or applying Terraform, Bicep, or other IaC to provision or fix resources. Use [[terraform-specialist]]. Suggested IaC fixes from this skill may be written only through the separate authorized patch workflow. Never run `apply`, deploy, or mutate cloud resources.
- Designing the target cloud architecture from scratch. Use [[cloud-architect]].

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md).

### 1. Scope and authorize the assessment

Confirm which accounts, subscriptions, or projects are in scope and that you hold read-only credentials for each. Posture detection must use viewer or security-auditor roles only; never request write permissions for an assessment. Record the scope so findings are attributable to a specific account boundary.

### 2. Build a read-only resource inventory

Enumerate the resource classes that carry the most posture risk:

- Object storage: buckets, blob containers, and their access policies and ACLs.
- Identity: users, roles, policies, service accounts, and attached or inline permission documents.
- Network: security groups, network security groups, and firewall rules with their ingress sources and ports.
- Compute and management surfaces: public IP assignments and exposed administrative endpoints.
- Logging configuration: whether control-plane and flow logging are enabled per account or region.

Pull this inventory from describe or list APIs only. Do not mutate any resource.

### 2A. Optional local IaC scanners (never apply)

This skill owns Trivy config and Checkov for local IaC scanning in a security-audit workflow. They are applicable only when the target contains supported Terraform, Kubernetes, CloudFormation, ARM, or related configuration. If none of those files exist, record `NOT_APPLICABLE` with that evidence and skip the tools.

Discover locally before invoking:

```bash
trivy --version
checkov --version
```

Never auto-install. Never fall back to a hosted scanner. Prefer a repository-provided config. Record tool version, target path, ruleset or config fingerprint, command, exit code, and artifact path. Cloud CLI use stays read-only. Suggested IaC patches may be drafted only through the authorized patch workflow; never run `apply`, `deploy`, `terraform apply`, or any command that mutates cloud resources.

### 3. Evaluate each resource against the defensive baseline

Apply a fixed rule set and emit one finding per violation:

- Public storage: a bucket or container readable or writable by anonymous or all-authenticated principals is a finding.
- Over-permissive IAM: a principal granted a wildcard action or resource (for example an action of `*` on a resource of `*`), or administrator-equivalent access outside the approved admin set, is a finding.
- Exposed ports: an ingress rule allowing `0.0.0.0/0` or `::/0` to SSH (22), RDP (3389), or common database ports is a finding.
- Disabled logging: an account or region with control-plane or flow logging turned off is a finding.

Use obviously fake identifiers in examples, such as bucket `arn:aws:s3:::example-bucket-0000` or role `arn:aws:iam::000000000000:role/example-role`.

### 4. Detect drift from an approved baseline

If a prior approved snapshot exists, diff the current inventory against it. Report new public exposure, newly broadened IAM grants, newly opened ports, and newly disabled logging as drift, separately from steady-state findings, so reviewers can see what changed.

### 5. Prioritize and assign remediation

Rank each finding by exposure (internet-reachable beats internal) and blast radius (admin or data-store access beats narrow scope). For each finding record the resource identifier, the rule violated, the evidence pulled from the API, the severity, and a remediation owner. Hand the list to the platform or cloud team; this skill stops at detection and triage.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The bucket is only public for a quick share, leave it." | Anonymous-readable storage is continuously indexed and scraped; a single forgotten public bucket is a routine source of mass data exposure, so it must be flagged every run regardless of intent. |
| "Wildcard IAM is fine, the account is internal." | A `*` action on `*` resource grants any compromised credential full control of the account; internal accounts are exactly where lateral movement turns one phished user into total takeover. |
| "Opening SSH to 0.0.0.0/0 is temporary for debugging." | Internet-exposed management ports are scanned within minutes and brute-forced continuously; "temporary" rules routinely survive for months and become the initial access vector. |
| "Logging is noisy, we disabled it to save cost." | An account with control-plane logging off cannot be investigated after a breach; the absence of logs converts a contained incident into an unprovable one and blinds [[cloud-audit-log-detection]]. |
| "We scanned last quarter, posture does not change." | Cloud configuration drifts daily as teams ship changes; a quarterly snapshot misses the new public bucket or widened role created last week, which is why drift detection runs continuously. |
| "Checkov or Trivy can apply the fix." | This skill is read-only. Suggested IaC changes go through the authorized patch workflow; never run apply, deploy, or mutate cloud resources. |

## Verification

- [ ] A scope record exists listing every account, subscription, or project assessed and confirming read-only credentials were used.
- [ ] An inventory artifact lists every storage, IAM, network, and logging resource enumerated, with no write API calls in the access log.
- [ ] Each finding names the resource identifier, the specific rule violated, and the API-sourced evidence.
- [ ] Public-storage, over-permissive-IAM, exposed-port, and disabled-logging rule categories were each evaluated and reported (even if zero findings).
- [ ] When a prior baseline exists, a drift section lists configuration changes since the last approved snapshot.
- [ ] Trivy config and Checkov were marked `NOT_APPLICABLE` with evidence when no supported IaC was present, or were discovered locally without auto-install; no `apply`, deploy, or cloud-mutation command was run

## Related Skills

- [[security-framework-mapping]] - map each posture finding to its ATT&CK, D3FEND, and NIST CSF identifier.
- [[cloud-architect]] - design the target cloud architecture and hardened baseline this skill detects drift against.
- [[cloud-audit-log-detection]] - hunt active attacker behavior in control-plane logs once posture gaps are known.
- [[identity-threat-detection]] - detect anomalous sign-ins and identity-provider attacks that complement posture findings.
