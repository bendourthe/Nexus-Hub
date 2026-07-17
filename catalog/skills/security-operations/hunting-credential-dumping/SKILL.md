---
name: hunting-credential-dumping
description: "Hunt for OS credential-dumping behavior - LSASS memory access, SAM/SECURITY hive theft, and NTDS.dit extraction - across endpoint telemetry and SIEM logs, and turn the patterns into durable detections. Make sure to use this skill whenever the user says \"hunt for credential dumping\", \"detect LSASS access\", \"detect credential theft\", \"SAM/NTDS extraction detection\", \"credential access hunting\", or \"detect handle access to lsass\", even when they only describe the symptom (an unexpected process reading lsass). SKIP, do NOT use for: rotating already-compromised credentials (use [[authentication-patterns]] plus your IR runbook) or any offensive credential-dumping technique - this skill is detection only."
summary_l0: "Hunt LSASS, SAM/SECURITY, and NTDS.dit credential theft across endpoint and SIEM telemetry"
overview_l1: "This skill drives a defensive threat hunt for OS credential-dumping behavior across the three canonical access paths: LSASS process-memory access, SAM/SECURITY registry-hive theft, and NTDS.dit Active Directory database extraction. It teaches the analyst what telemetry to query (process handle-access events, sensitive-file access, volume-shadow-copy creation, suspicious parent/child chains), how to write detection logic that survives common benign noise, how to seed a known test event so the query is proven to fire, and how to tune for false positives from backup agents and security tooling. Every step is framed from the defender's seat - the skill writes detections and hunt queries, never dumping tooling. Findings map to ATT&CK credential-access techniques and D3FEND process-analysis countermeasures so each detection routes cleanly into a SIEM rule and an incident record."
mitre_attack: [T1003, T1003.001, T1003.002, T1003.003]
d3fend_techniques: [D3-PA, D3-PSA]
nist_csf: [DE.CM, DE.AE]
---

# Hunting Credential Dumping

Hunt for OS credential-dumping behavior across endpoint and SIEM telemetry, then convert the confirmed patterns into durable, test-proven detections. This is a detection-and-hunt workflow from the defender's seat; it never produces or runs dumping tooling.

## When to Use This Skill

- You need a proactive hunt for credential theft across a fleet (not a single forensic image).
- An alert mentions a process opening a handle to LSASS and you must confirm whether it is malicious.
- You want detections for SAM/SECURITY hive copies (registry save, raw hive file reads, shadow-copy hive extraction).
- You need to detect NTDS.dit extraction on a domain controller (volume shadow copy + ntds.dit/ese access).
- You are building or tuning SIEM rules for the Credential Access tactic and need test-proven queries.
- A red-team or purple-team exercise needs detection coverage validated against sanctioned credential-access activity.
- A post-incident review found credential theft that the existing rules missed, and you must close the detection gap.

**When NOT to use:**

- Rotating or revoking credentials that are already compromised - use [[authentication-patterns]] and your incident-response runbook.
- Analyzing a single captured memory image for credential residue - use [[memory-forensics]].
- Any request to perform, script, or evade credential dumping - out of scope; this skill is detection only.

## Telemetry Source Map

Each credential-access path leaves a different signature. Confirm the corresponding source is collected before writing the query; an uncollected source is a silent coverage hole.

| Path (ATT&CK) | Primary signal | Telemetry source |
|---|---|---|
| LSASS memory (T1003.001) | Process opens a handle to lsass.exe with read/clone rights; minidump creation. | Endpoint process-access events (for example Sysmon Event ID 10), EDR handle-access telemetry. |
| LSASS memory (T1003.001) | Unexpected child of, or access from, an office/browser process. | Process-creation events (Sysmon Event ID 1) correlated to access events. |
| SAM/SECURITY (T1003.002) | Registry hive save/export; raw read of on-disk hive files; shadow-copy hive extraction. | Registry-operation events, file-access auditing, volume-shadow-copy creation events. |
| NTDS (T1003.003) | Shadow copy created then ntds.dit / ESE files accessed; directory-export utility run. | DC file-access auditing, shadow-copy events, process-creation with command line. |

## Instructions

### 1. Scope the hunt and confirm telemetry coverage

1. List the credential-access paths in scope: LSASS memory access (T1003.001), SAM/SECURITY hive theft (T1003.002), NTDS.dit extraction (T1003.003).
2. Confirm the telemetry exists for each path before writing queries: process handle-access events against LSASS, file-access events on hive paths, registry save/export events, volume-shadow-copy creation events, and process-creation events with command lines.
3. If a required event source is not collected, record the visibility gap explicitly - a detection you cannot feed is a false sense of security.

### 2. Build the LSASS-access detection (T1003.001)

1. Query for processes that open a handle to the LSASS process with read/clone access rights that are not on a known-good list (security agents, the OS itself).
2. Add the process-memory-read and minidump-creation signals where available, and correlate to the requesting process image and its parent chain.
3. Exclude documented benign accessors by full path and signer, not by image name alone (image-name-only allowlists are trivially satisfied by a renamed binary).
4. Flag access requests that carry the specific rights needed to read process memory rather than treating every handle open as equal - benign callers usually request limited rights.
5. Where the platform exposes it, add detection for direct system-call patterns that bypass standard API instrumentation, so an evasive caller is not invisible.

### 3. Build the SAM/SECURITY hive-theft detection (T1003.002)

1. Detect registry hive export/save operations targeting SAM, SECURITY, or SYSTEM.
2. Detect raw file reads or copies of the on-disk hive files by non-system processes.
3. Detect shadow-copy-based hive extraction (a shadow copy created immediately before a hive-path read).

### 4. Build the NTDS.dit extraction detection (T1003.003)

1. On domain controllers, detect volume-shadow-copy creation followed by access to the ntds.dit / ESE database files.
2. Detect built-in directory-service export utilities invoked outside change-management windows.
3. Correlate to the initiating account and host so a single rule fires once per extraction attempt, not once per file event.

### 5. Seed a known test event and prove the query fires

1. In an authorized lab or test tenant, generate one benign, sanctioned event for each path that produces the same telemetry signature (for example a sanctioned handle open to LSASS by your own test tool, or an approved hive backup). Do not use offensive tooling.
2. Run each detection query and confirm it returns the seeded test event. A query that has never returned its own seeded event is unverified.
3. Record the seed-to-fire confirmation alongside the rule.

### 6. Tune for false positives

1. Identify benign sources per path: backup agents (hive and NTDS reads), EDR/AV (LSASS access), patch tooling, and legitimate DC maintenance.
2. Suppress by full path plus signer plus expected parent, not by a single attribute.
3. Set a severity that reflects path risk (NTDS.dit extraction on a DC outranks a single LSASS handle open).

### 7. Operationalize

1. Promote each test-proven query to a SIEM/EDR rule with an owner and a runbook link.
2. Tag each rule with its ATT&CK technique ID so coverage reporting can show which credential-access paths are monitored.
3. Schedule a periodic re-seed so the detection is re-proven after telemetry-schema or agent upgrades that silently break field mappings.
4. Record the residual visibility gaps from step 1 as tracked risks, not as covered paths, so leadership sees the true coverage picture.

### 8. Hand off confirmed hits to incident response

1. For any rule firing on real (non-seeded) activity, package the requesting process, account, host, and parent chain as an indicator set.
2. Route the highest-severity paths (NTDS extraction, multi-host LSASS access) to the IR runbook for credential rotation; this skill detects, it does not rotate.

Framework mappings are documented in [references/standards.md](references/standards.md).

## Detection Hygiene and Test Discipline

A credential-access detection that has not been proven and is not maintained is a liability, because it creates false confidence, so apply the same discipline you would to production code.

- Version-control every rule with its query, its allowlist tuples, its owner, and its ATT&CK tag in the same artifact.
- Keep the seeded test event and its expected result next to the rule, so the next maintainer can re-prove the rule in one step.
- Re-run the seed after any telemetry-schema change, agent upgrade, or index migration; these silently rename fields and break filters.
- Record allowlist suppressions with a justification and an expiry-review date, so a temporary exclusion does not become a permanent blind spot.
- Track the residual visibility gaps from step 1 in the same register as the rules, so coverage reporting reflects reality, not aspiration.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We allowlist LSASS access by image name, that is enough" | An image-name allowlist is satisfied by any binary renamed to match; an attacker copies their tool to the allowlisted name and the rule goes silent. Allowlist by full path plus code-signer plus expected parent so a renamed binary still trips the rule. |
| "The rule is written, so the path is covered" | A rule that has never returned its own seeded test event may have a field-name typo, a wrong index, or a filter that excludes everything. Until step 5 shows the query returning the seed, the coverage is imaginary. |
| "Backup agents read the hives, so hive-read detection is pure noise" | Backup reads are predictable by path, signer, and schedule; an attacker's hive copy is not. Suppressing the known-good backup tuple leaves the malicious read visible instead of disabling the whole detection. |
| "We watch LSASS, so credential dumping is covered" | LSASS memory access is one of three paths. SAM/SECURITY hive theft and NTDS.dit extraction leave entirely different telemetry and are missed by an LSASS-only rule, which is precisely the gap an attacker pivots to. |
| "NTDS detection is a DC problem, not ours" | A single NTDS.dit extraction yields every domain credential at once; treating it as someone else's problem means the highest-impact credential-access path has no owner. Assign it explicitly with the highest severity. |
| "The query has low volume, so it must be tuned correctly" | Low volume can mean a wrong index, a mistyped field, or a filter that drops everything - the same symptom as a perfectly tuned rule. Only the seeded-test-event check in step 5 distinguishes a quiet rule from a broken one. |

## Verification

- [ ] Telemetry coverage is confirmed (or the gap recorded) for each of the LSASS, SAM/SECURITY, and NTDS.dit paths.
- [ ] A seeded benign test event exists for each path and the corresponding detection query returns that seeded event.
- [ ] Each allowlist entry is expressed as full path plus signer plus expected parent, not image name alone.
- [ ] The NTDS.dit detection correlates shadow-copy creation to ntds.dit/ESE access and fires once per attempt.
- [ ] Each promoted rule carries its ATT&CK technique ID, an owner, and a runbook link.
- [ ] A periodic re-seed is scheduled so the rule is re-proven after telemetry or agent upgrades.
- [ ] Residual visibility gaps are recorded as tracked risks, not silently counted as covered.
- [ ] No offensive dumping tool was used to generate test events; all seeds are sanctioned benign actions in an authorized environment.

## Limitations

State these boundaries so the detections are not treated as guarantees.

- Detection is not prevention; a firing rule confirms an attempt was observed, not that credentials are safe. Route confirmed hits to rotation via the IR runbook.
- Coverage is bounded by telemetry. A path with no collected source is invisible regardless of rule quality, which is why step 1 records gaps as risks.
- An attacker who reads credential material from an already-acquired memory image or backup, off the monitored host, leaves no live-telemetry signal; pair this hunt with [[memory-forensics]] for offline cases.
- Allowlists tuned for today's benign tools drift as the environment changes; an un-reviewed suppression silently widens into a blind spot over time.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers used here.
- [[memory-forensics]] - confirms the same LSASS-access indicator inside a captured memory image when a host is pulled offline.
- [[endpoint-edr-detection]] - the live-endpoint telemetry source these hunt queries draw from and where the rules are deployed.
- [[lateral-movement-detection]] - the natural follow-on hunt, since stolen credentials are used to move laterally.
