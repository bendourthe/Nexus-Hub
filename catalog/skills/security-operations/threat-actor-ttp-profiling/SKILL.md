---
name: threat-actor-ttp-profiling
description: "Build a threat-actor TTP profile from observed behaviors mapped to ATT&CK, not from brand folklore. Use this skill whenever the user says \"profile this threat actor\", \"TTP mapping\", \"intrusion set behaviors\", \"map this campaign to ATT&CK\", or wants a defender-usable actor dossier. SKIP, do NOT use for, IOC reputation triage (use ioc-enrichment-and-reputation-triage), leak-site watching, or writing intrusion malware."
summary_l0: "Profile intrusion-set behaviors and map them to ATT&CK for defense"
overview_l1: "This skill produces a defender-usable actor profile from observed techniques, not from marketing names. It maps behaviors to ATT&CK, records evidence, and lists detections that would catch the same behaviors. Trigger phrases: profile this threat actor, TTP mapping, intrusion set behaviors, map this campaign to ATT&CK."
mitre_attack: [T1583, T1059, T1021]
nist_csf: [ID.RA, DE.AE]
---

# Threat-Actor TTP Profiling

Replace actor folklore with a behavior profile a detection engineer can implement.

## When to Use This Skill

Use this skill when:

- A campaign needs ATT&CK mapping
- Two incidents may be the same intrusion set
- A briefing must separate evidence from attribution theater

Do NOT use this skill when:

- The ask is a single hash lookup
- The ask is to write offensive tooling

**Trigger phrases**: "profile this threat actor", "TTP mapping", "intrusion set", "map this campaign to ATT&CK"

## Instructions

### Step 1: Separate observations from labels

List behaviors with timestamps and evidence IDs. Keep the marketing actor name in a single field so it cannot leak into detections.

### Step 2: Map each behavior to ATT&CK

Assign a technique and sub-technique only when the evidence supports it. Record 'insufficient evidence' rather than forcing a match.

### Step 3: Cluster by procedure, not by malware family

Group repeating procedures (how they move laterally, how they persist). Family names change; procedures persist.

### Step 4: Write detections that would catch the procedure

For each mapped technique, name a log source and a detection idea. If no log source exists, that is a coverage gap, not a skipped row.

### Step 5: State attribution confidence separately

Confidence in 'these behaviors occurred' is not confidence in 'group X did it'. Never merge the two scores.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| The vendor already named the actor, so mapping is optional | A name without procedures cannot be detected. Detections fire on behaviors. |
| One matching malware family is attribution | Commodity malware is shared. Procedure overlap plus exclusive infrastructure is the minimum bar. |
| We can skip log-source gaps | An unmapped gap is how the same actor returns through the same blind spot. |

## Verification

- [ ] Every mapped TTP cites evidence
- [ ] Attribution confidence is a separate field
- [ ] Each technique has a detection idea or an explicit coverage gap

## Related Skills

- [[ioc-enrichment-and-reputation-triage]] -- indicators feed the profile; they are not the profile
- [[siem-detection-engineering]] -- procedures here become detections there

Framework identifiers declared in frontmatter are explained in [references/standards.md](references/standards.md).
