---
name: ransomware-incident-response
description: "Execute a ransomware incident-response runbook end to end - detect and contain active encryption, preserve forensic evidence, identify the strain and entry vector, eradicate, recover from clean backups, and run the post-incident review. Make sure to use this skill whenever the user says \"ransomware response\", \"respond to ransomware\", \"files are being encrypted\", \"ransomware incident\", \"contain a ransomware outbreak\", \"ransomware recovery\", or describes mass file encryption, ransom notes, or shadow-copy deletion in progress. SKIP, do NOT use for: generic incident-response theory with no active ransomware, pre-incident proactive threat hunting (use log-threat-hunting), or backup architecture design and capacity planning."
summary_l0: "Run a ransomware incident-response runbook from containment through recovery and post-incident review"
overview_l1: "This skill walks the agent through a full defensive ransomware incident-response lifecycle: rapid detection and triage of active encryption, network and host containment to stop lateral spread, forensic preservation of volatile and disk evidence before any cleanup, identification of the ransomware family and the initial entry vector, eradication of attacker footholds, recovery from validated clean backups, and a blameless post-incident review that captures timeline, root cause, and tracked action items. It is purely defensive: it never advises paying a ransom, never decrypts via attacker tooling, and never performs offensive actions. The runbook emphasizes evidence-first ordering (preserve before you wipe), backup integrity verification before restore, and explicit go/no-go gates between phases. Trigger phrases: ransomware response, files are being encrypted, contain a ransomware outbreak, ransomware recovery."
mitre_attack: [T1486, T1490, T1489]
d3fend_techniques: [D3-FA, D3-FH]
nist_csf: [RS.RP, RS.MI, RC.RP, DE.CM]
---

# Ransomware Incident Response

Drive a live ransomware incident from first alert to closed post-incident review, ordering every action so that containment stops the spread and evidence is preserved before any system is wiped or rebuilt. This is a defensive runbook only: it never pays, negotiates, or runs attacker-supplied decryptors.

## When to Use This Skill

- An alert or user report indicates files are actively being encrypted, ransom notes are appearing, or extensions are being mass-renamed.
- Backups, volume shadow copies, or recovery points are being deleted faster than normal.
- A confirmed ransomware detonation has occurred and you need a phased containment-to-recovery plan.
- A tabletop exercise or readiness drill needs a concrete ransomware runbook to follow.
- Leadership needs a structured timeline and recovery sequence during an active outbreak.

**When NOT to use:**

- The request is generic incident-response theory with no ransomware indicators - use a general IR framework instead.
- The task is proactive threat hunting before any incident - use [[log-threat-hunting]].
- The task is designing backup architecture, retention tiers, or capacity - that is engineering, not response.

## Instructions

Work the phases in order. Do not skip the evidence-preservation phase to save time - rebuilding before capture destroys the only record of the attack. Treat each phase boundary as a go/no-go gate.

### 1. Detect and triage

1. Confirm the alert is true-positive: look for ransom notes, mass file-modification events, encrypted-extension patterns, and spikes in file-write or rename operations in endpoint and file-server telemetry.
2. Scope the blast radius: list affected hosts, file shares, and identities. Record the first-observed timestamp and the alerting source.
3. Declare severity and stand up the incident bridge, an incident commander, and a scribe so every subsequent action is logged with a timestamp.
4. Open the running incident timeline now; every later phase appends to it. The timeline is the input to the post-incident review.

Gate: do not move to containment until you have at least a partial host and identity scope, otherwise containment will be incomplete and the attacker simply continues from an un-isolated host.

### 2. Contain

1. Isolate affected hosts at the network layer (host quarantine, VLAN isolation, or switch-port disable). Prefer EDR network-containment so the host stays reachable for forensics.
2. Disable compromised accounts and rotate exposed credentials. Never paste secret values into chat or tickets - reference them as `<credential>` and rotate at the source.
3. Block known malicious indicators (hashes, domains, IPs) at the firewall, proxy, and EDR.
4. Protect backups: take backup repositories offline or read-only so the attacker cannot reach them. Verify the backup network path is no longer reachable from compromised hosts.
5. Contain identity, not just hosts: revoke active sessions and tokens for affected accounts so an isolated endpoint does not simply hand off to a stolen session elsewhere.

Gate: confirm spread has stopped (no new encryption events after isolation) before spending time on identification.

### 3. Preserve evidence

1. Capture volatile data first (running processes, network connections, logged-on users, memory if tooling allows) before powering anything off. Pulling power destroys memory-resident evidence.
2. Image affected disks or capture forensic file artifacts (event logs, registry hives, ransom note, sample of encrypted files) with hashes recorded for chain of custody.
3. Record a hash for every collected artifact and store it write-once with documented custody. Hashing both proves integrity and lets you deduplicate samples across hosts.
4. Preserve before you eradicate. This evidence-first ordering is non-negotiable: it is the only record of the entry vector and the attacker's actions. This is where MITRE D3FEND file-analysis and file-hashing actions apply. Framework mappings are documented in [references/standards.md](references/standards.md).

Gate: evidence for at least patient-zero and one lateral-movement host is captured and hashed before any eradication or rebuild.

### 4. Identify strain and entry vector

1. Identify the ransomware family from the note, file markers, and extension using only trusted public threat-intel references - do not execute samples outside a contained analysis environment.
2. Trace the initial access vector (phishing, exposed remote-access, vulnerable service, compromised credential) by working backward through authentication, EDR, and email logs to patient zero.
3. Reconstruct the lateral-movement path so you know every host the actor touched, not only the ones that encrypted.
4. Map observed attacker behaviors to encryption, inhibit-recovery, and service-stop techniques so eradication is complete, not cosmetic.

Gate: the entry vector is identified, or explicitly flagged as unknown, before recovery. Recovering without closing the vector invites immediate reinfection.

### 5. Eradicate

1. Remove persistence and attacker footholds on every affected host (scheduled tasks, services, autoruns, rogue accounts). Use [[persistence-mechanism-hunting]] to sweep systematically rather than by memory.
2. Patch or close the confirmed entry vector before anything is returned to production.
3. Reset credentials broadly across the affected trust boundary, prioritizing privileged and service accounts.
4. Hunt for second-stage tooling and beacons that survive a single-host cleanup so the actor cannot re-enter through a forgotten backdoor.

Gate: eradication confidence is documented per host; low-confidence hosts go to rebuild, not restore-in-place.

### 6. Recover

1. Verify backup integrity and confirm the chosen restore point predates first compromise. Validate the backup is itself uninfected before restoring.
2. Rebuild from known-clean images where eradication confidence is low; restore data from validated backups.
3. Restore in a staged, monitored sequence with heightened detection enabled to catch reinfection. This is the NIST CSF Recover (RC.RP) phase.
4. Validate restored services against a business-priority order so the most critical systems return first under the closest watch.

Gate: no reinfection observed during a defined soak window before the incident is downgraded.

### 7. Post-incident review

1. Run a blameless review capturing the timeline, root cause, contributing factors, and detection gaps.
2. Record tracked, owned action items (control gaps, backup hardening, detection tuning) with due dates.
3. Feed the confirmed indicators and techniques back into detection content so the next attempt is caught earlier.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Just rebuild the boxes now - speed matters more than forensics" | Wiping before capture destroys the entry-vector evidence, so the same vulnerability is re-exploited days later and the second outbreak is worse than the first. |
| "We restored from the latest backup, we are done" | If the restore point post-dates compromise, the dormant payload or attacker access is restored too, and encryption resumes on the recovered systems. |
| "Paying the ransom is the fastest recovery path" | Decryptors supplied by attackers are frequently broken or incomplete, payment funds repeat attacks, and it does not remove the persistence that caused reinfection in observed cases. |
| "Containment can wait until we understand the malware fully" | Every minute without isolation lets encryption and lateral movement reach more shares and hosts, turning a single-host event into an enterprise outage. |
| "Backups are safe because they are on a separate server" | Modern ransomware specifically enumerates and deletes reachable backups and shadow copies first, so a network-reachable backup is a primary target, not a safe haven. |

## Verification

- [ ] An incident record exists with declared severity, incident commander, and first-observed timestamp.
- [ ] Affected hosts show network-containment or isolation status in the EDR or network console.
- [ ] Forensic evidence (memory or disk image, key host logs, ransom note, encrypted sample) is stored write-once with recorded hashes and custody.
- [ ] The initial entry vector is documented and the corresponding fix (patch, closed port, rotated credential) is applied.
- [ ] The selected backup restore point is documented as pre-compromise and validated clean before restore.
- [ ] Recovered systems are running under heightened monitoring with no reinfection observed during the staged restore window.
- [ ] A blameless post-incident review document exists with timeline, root cause, and owned action items with due dates.

## Related Skills

- [[security-framework-mapping]] - assign ATT&CK / D3FEND / NIST CSF identifiers to the techniques and controls in this runbook.
- [[incident-postmortem]] - structure the blameless post-incident review and action-item tracking.
- [[oncall-runbook]] - format the per-alert response steps that page the responders who run this skill.
- [[rollback-strategy-advisor]] - plan the staged recovery and rollback sequence during the Recover phase.
