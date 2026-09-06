---
name: persistence-mechanism-hunting
description: "Hunt for attacker persistence across endpoints - autostart entries, scheduled tasks, services, WMI event subscriptions, registry run keys, and startup folders - then triage each finding as benign or malicious with concrete enrichment criteria. Make sure to use this skill whenever the user says \"hunt for persistence\", \"find malicious autoruns\", \"detect scheduled-task persistence\", \"WMI event subscription persistence\", \"registry run-key persistence\", \"detect malicious services\", or asks how an attacker survives a reboot or maintains a foothold. SKIP, do NOT use for: eradicating persistence during a live ransomware incident (use ransomware-incident-response), or firmware, UEFI, and bootkit forensics, which need specialized low-level tooling."
summary_l0: "Hunt and triage attacker persistence across autostart, scheduled tasks, services, WMI, and run keys"
overview_l1: "This skill teaches the agent to proactively hunt for attacker persistence mechanisms on endpoints and triage each finding. It covers the major persistence surfaces - registry run keys and startup folders, scheduled tasks, Windows services, WMI permanent event subscriptions, and other autostart extensibility points - and gives a repeatable workflow: enumerate from host or EDR telemetry, baseline against known-good, enrich each candidate (signature, path, parent, prevalence, creation time), and classify as benign, suspicious, or malicious. It is detection and triage only: it identifies and explains persistence so a responder can act, and never installs persistence or performs offensive actions. The skill stresses prevalence and signing as primary triage levers, masquerading detection (legit names in odd paths), and documenting each verdict with evidence. Trigger phrases: hunt for persistence, find malicious autoruns, scheduled-task persistence, WMI event subscription persistence, registry run-key persistence."
mitre_attack: [T1547, T1053, T1543, T1546]
d3fend_techniques: [D3-PA, D3-SFA]
nist_csf: [DE.CM, DE.AE]
---

# Persistence Mechanism Hunting

Proactively sweep endpoints for the ways an attacker survives a reboot or re-establishes access, then triage every autostart artifact as benign, suspicious, or malicious with evidence. This is a defensive hunting skill: it finds and explains persistence so a responder can act on it.

## When to Use This Skill

- You are hunting for an undiscovered foothold across one or many endpoints.
- An alert or threat-intel report names a persistence technique and you need to confirm or rule it out fleet-wide.
- After eradicating an incident, you want to verify no persistence remains.
- You are baselining a host's autostart surface to build a known-good reference for future hunts.
- You need to triage a list of autorun, scheduled-task, service, or WMI-subscription findings into actionable verdicts.

**When NOT to use:**

- You are mid-incident and need to eradicate confirmed persistence under time pressure - use [[ransomware-incident-response]] for the contain-and-eradicate flow.
- The persistence lives in firmware, UEFI, or a bootkit - that needs specialized low-level forensic tooling outside this skill's scope.
- You need to build a SIEM-wide correlation rule rather than run a host-level hunt - use a detection-engineering workflow.

## Instructions

Run the phases in order: enumerate broadly, then narrow with enrichment. Resist deleting anything during a hunt - this is triage, not eradication, and premature removal destroys the evidence a responder needs.

### 1. Scope the hunt

1. Decide the host set: a single suspect host, a business unit, or the whole fleet. Fleet-wide hunts make prevalence usable as a triage lever.
2. State the hypothesis if one exists (for example, a threat-intel report naming a scheduled-task technique) so enumeration can be targeted as well as broad.

### 2. Enumerate the persistence surfaces

1. Collect autostart extensibility points: registry run and run-once keys, startup-folder shortcuts, and logon scripts.
2. Collect scheduled tasks, including hidden tasks and tasks with unusual triggers (logon, idle, event-based).
3. Collect services, focusing on auto-start services with non-standard binary paths or unusual service accounts.
4. Collect WMI permanent event subscriptions (event filters, consumers, and their bindings), a low-noise surface attackers favor for stealth.
5. Prefer pulling this inventory from EDR or host telemetry across the fleet so you can compare hosts, not just inspect one.

Gate: confirm every listed surface was actually collected before triaging, or the stealthiest foothold stays invisible.

### 3. Baseline against known-good

1. Compare each finding against a known-good baseline for the platform and image. Items present on a clean gold image are low priority.
2. Compute prevalence: an autostart entry on one host out of thousands is far more interesting than one on every host.
3. Flag baseline-deviating items (present on a host but not on the gold image) as the priority queue for enrichment.

### 4. Enrich each candidate

For every candidate, gather the triage signals defenders rely on:

1. Signature status (signed by a trusted publisher vs unsigned or self-signed).
2. File path and name (system directory vs user-writable temp, plus masquerading checks where a legitimate name sits in an odd path).
3. Parent or creating process and the account that created the entry.
4. Creation and modification timestamps versus the host's baseline build time; an autostart entry created long after imaging is suspicious.
5. Reputation of the hash and any network indicators it references.

This per-artifact analysis is the MITRE D3FEND process-analysis and system-file-analysis lens. Framework mappings are documented in [references/standards.md](references/standards.md).

### 5. Classify and document

1. Assign each finding a verdict: benign, suspicious (needs follow-up), or malicious. Treat the verdict as defensible only if you can state the evidence in one sentence.
2. Map the malicious findings to their persistence technique (autostart, scheduled task, service, or event-triggered execution) so the responder understands the foothold.
3. Document each verdict with the evidence that supports it (signature, path, prevalence, timeline).
4. Hand confirmed-malicious findings to the responder or the live-incident skill; do not eradicate from within the hunt. Removal is the responder's action, taken after the foothold is scoped.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It is signed, so it is safe" | Attackers abuse signed living-off-the-land binaries and steal or buy code-signing, so a valid signature on a binary in a user-writable path with no prevalence is still a strong lead, not a clearance. |
| "I checked the run keys, persistence is covered" | Run keys are one of a dozen autostart surfaces; skipping scheduled tasks, services, and WMI event subscriptions leaves the stealthiest footholds in place and the host re-compromises after cleanup. |
| "The name looks legitimate, skip it" | Masquerading is a primary evasion - a service named like a trusted system component but launched from a temp directory is a classic persistence tell that name-only triage misses. |
| "It is on every host, so it is normal" | High prevalence usually means benign, but supply-chain and gold-image compromises are fleet-wide by definition, so prevalence is a prioritization signal, not an automatic acquittal for items that fail other checks. |
| "I will just delete the suspicious entries as I find them" | Deleting during a hunt destroys the timeline and the link to the entry vector, so the responder cannot scope the breach and the same actor re-establishes a foothold you can no longer trace. |

## Verification

- [ ] An enumeration record exists covering run keys, startup folders, scheduled tasks, services, and WMI event subscriptions for each in-scope host.
- [ ] Each finding is compared against a known-good baseline and carries a computed prevalence across the fleet.
- [ ] Every candidate has enrichment fields recorded: signature status, file path, parent or creating process, and creation timestamp.
- [ ] Every finding has an explicit verdict (benign, suspicious, or malicious) with the supporting evidence noted.
- [ ] Confirmed-malicious findings are mapped to their persistence technique and handed off, with no eradication performed inside the hunt.

## Related Skills

- [[security-framework-mapping]] - assign ATT&CK / D3FEND / NIST CSF identifiers to the persistence techniques and detections found here.
- [[disk-artifact-forensics]] - deepen analysis of suspicious on-disk persistence artifacts during follow-up.
- [[endpoint-edr-detection]] - turn confirmed persistence patterns into behavioral EDR detections.
- [[log-threat-hunting]] - correlate host-level findings with log-based hunting across the environment.
