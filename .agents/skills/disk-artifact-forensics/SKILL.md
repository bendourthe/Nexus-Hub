---
name: disk-artifact-forensics
description: "Reconstruct attacker activity from a forensic disk image using filesystem and OS artifacts (MFT, $UsnJrnl, registry hives, prefetch, shimcache/amcache, event logs, browser history) and build a defensible host timeline. Make sure to use this skill whenever the user says \"disk forensics\", \"analyze the MFT\", \"registry hive forensics\", \"prefetch analysis\", \"build a host timeline\", \"examine a forensic disk image\", or \"amcache/shimcache analysis\", even when they only hand you an .E01 / .dd / .vmdk image and ask what happened on the host. SKIP, do NOT use for: volatile-memory analysis of a RAM capture (use [[memory-forensics]]) or live triage of a still-running endpoint (use [[endpoint-edr-detection]])."
summary_l0: "Reconstruct host activity and a timeline from disk-image filesystem and OS artifacts"
overview_l1: "This skill drives defensive reconstruction of attacker activity from a forensic disk image. It teaches which artifacts answer which question - the MFT and $UsnJrnl for file create/modify/delete, registry hives for persistence and configuration, prefetch and amcache/shimcache for program-execution evidence, Windows event logs for logon and service activity, and browser history for initial-access and download evidence - and how to fuse them into a single super-timeline. The workflow runs read-only against a verified, hashed image, distinguishes indicators of anti-forensic activity (log clearing, timestomping) from normal churn, and produces a defensible chronological narrative an investigator can defend. Findings map to ATT&CK indicator-removal, persistence, and execution techniques and to D3FEND file/system-artifact analysis countermeasures, and they feed directly into an incident timeline and postmortem."
mitre_attack: [T1070, T1547, T1059]
d3fend_techniques: [D3-FA, D3-SFA]
nist_csf: [DE.AE, RS.AN]
---

# Disk Artifact Forensics

Reconstruct what an attacker did on a host from a forensic disk image by fusing filesystem and OS artifacts into a single defensible timeline. This is a read-only, defender-seat workflow performed against a verified evidence image.

## When to Use This Skill

- You have a forensic disk image (`.E01`, `.dd`, `.raw`, `.vmdk`) and must determine what happened on the host.
- You need program-execution evidence (which binaries ran, when, how many times) from prefetch, amcache, or shimcache.
- You need to reconstruct file create/modify/delete activity from the MFT and `$UsnJrnl`.
- You need persistence evidence from registry hives (Run keys, services, scheduled tasks) and event logs.
- You are building a host timeline / super-timeline to anchor an incident narrative.
- You suspect anti-forensic activity (log clearing, timestomping, secure deletion) and must prove or disprove it.
- A ransomware or data-theft case requires reconstructing the delivery-to-execution chain from a seized disk image.

**When NOT to use:**

- Volatile-memory analysis (process injection, in-memory connections) - use [[memory-forensics]].
- Live triage of a still-running endpoint - use [[endpoint-edr-detection]].
- Rotating credentials or executing containment - those are IR-runbook actions, not disk analysis.
- Any request to wipe, timestomp, or clear logs - out of scope; this skill detects anti-forensics, it does not perform it.

## Artifact Reference Map

Each investigative question is answered by a specific artifact. Fuse them; no single artifact tells the whole story, and the strongest findings come from cross-artifact agreement (or disagreement).

| Question | Artifact | What it proves |
|---|---|---|
| What files were created/modified/deleted? | MFT (MACB timestamps), $UsnJrnl | File lifecycle, including names of deleted files. |
| Was a timestamp forged? | $STANDARD_INFORMATION vs $FILE_NAME | Timestomping when the two attribute sets disagree. |
| What programs ran, and how often? | Prefetch (.pf) | Executable name, first/last run, run count. |
| Did a now-deleted binary ever run? | Amcache, Shimcache | Presence and last-execution of binaries absent from disk. |
| What persistence was installed? | Registry hives (SYSTEM/SOFTWARE/NTUSER.DAT) | Run keys, services, scheduled tasks, with hive write times. |
| Who logged on, and from where? | Security/System event logs | Logon types, source hosts, service installs. |
| How did it get in? | Browser history, downloads, cache | Initial-access URL and downloaded payloads. |

## Instructions

### 1. Verify and mount the image read-only

1. Confirm the acquisition hash matches the image you received; record the SHA-256 and the acquisition metadata.
2. Mount the image read-only (or work from a forensic copy) so analysis cannot alter evidence.
3. Establish the host's timezone and clock offset before interpreting any timestamp - a wrong timezone silently corrupts the whole timeline.
4. Record the OS build and patch level; artifact formats (amcache schema, event-log channels) differ across versions and dictate which parsers apply.
5. Work in a case-scoped directory so every derived artifact can be hashed as a reproducible set.

### 2. Reconstruct filesystem activity (MFT and $UsnJrnl)

1. Parse the MFT for the full file inventory with the four MACB timestamps (Modified, Accessed, Changed/MFT-modified, Born/created) from both `$STANDARD_INFORMATION` and `$FILE_NAME` attributes.
2. Compare `$STANDARD_INFORMATION` against `$FILE_NAME` timestamps - a mismatch is a timestomping indicator (ATT&CK T1070.006).
3. Look for sub-second-precision anomalies: forged timestamps often have zeroed sub-second fields where genuine OS-written ones do not.
4. Parse `$UsnJrnl` for the create/rename/delete change record, which often survives even when a file itself was deleted.
5. Recover resident data and slack for small deleted files directly from the MFT record where possible.

### 3. Recover program-execution evidence

1. Parse prefetch (`.pf`) for executable name, first/last run times, and run count.
2. Parse amcache and shimcache for program presence and last-execution/last-modified evidence, including binaries no longer on disk.
3. Cross-check the three sources - a binary in amcache/shimcache but absent from disk and from prefetch is a strong indicator of a deleted tool that ran (ATT&CK T1059 command/scripting execution).

### 4. Extract persistence and configuration from registry hives

1. Parse SYSTEM, SOFTWARE, and per-user NTUSER.DAT hives for autostart locations: Run/RunOnce keys, Services, scheduled tasks, and known persistence keys (ATT&CK T1547 boot/logon autostart).
2. Record the hive last-write times for each suspicious key to place creation in the timeline.
3. Note user-context configuration (mounted shares, typed paths, recent docs) that explains attacker movement.

### 5. Correlate event logs and account activity

1. Parse Security, System, and relevant Application/PowerShell-Operational event logs for logon types, service installs, and process creation.
2. Detect event-log clearing and gaps (ATT&CK T1070.001, indicator removal) - a cleared log is itself an indicator, not an absence of evidence.
3. Tie logon events to the accounts and source hosts that drove the activity.

### 6. Recover initial-access and download evidence

1. Parse browser history, downloads, and cache for the first-access URL and any downloaded payloads.
2. Correlate a download timestamp to a subsequent execution event from step 3 to establish the delivery-to-execution chain.

### 7. Fuse into a defensible timeline

1. Normalize every artifact's timestamps to a single timezone and merge them into one chronological super-timeline.
2. For each entry record the artifact source and offset so every line is independently verifiable.
3. Annotate anti-forensic events (timestomp, log clear, deletion) explicitly so the narrative survives challenge.
4. Distinguish confirmed events from inferred ones in the timeline so the certainty of each line is visible to a reviewer.
5. Map each significant event to its ATT&CK technique and hand the timeline to [[incident-postmortem]].

### 8. Seal the evidence

1. Re-hash the source image and confirm it matches the acquisition digest from step 1.
2. Hash the case directory of derived artifacts and record it with analyst, date, and parser versions.
3. Preserve the original artifact files alongside your parsed output so a reviewer can re-derive every timeline line.

Framework mappings are documented in [references/standards.md](references/standards.md).

## Evidence Handling and Chain of Custody

A disk-forensics conclusion that cannot be reproduced or defended is worthless, so handle the image as evidence throughout.

- Record the acquirer, tool and version, source host, and acquisition time before mounting anything.
- Mount read-only or operate on a verified copy; never let an analysis tool write back to the evidence image.
- Keep an append-only activity log of every parser run, every artifact extracted, and every hash computed, with timestamps.
- Preserve the raw artifact files (MFT, hives, event logs, prefetch) next to your parsed output so a reviewer can re-derive any timeline entry independently.
- Annotate which parser and version produced each line of the timeline; a finding tied to an unstated tool version is hard to defend.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The file was deleted, so there is nothing to find" | The MFT entry, the `$UsnJrnl` change record, and amcache/shimcache often retain a deleted file's name and execution evidence long after the data is gone. Declaring "nothing to find" after a deletion is exactly the conclusion the attacker wanted. |
| "Prefetch shows it ran once, so I'll trust that timestamp as the only run" | Prefetch holds the last several run times and a run count, and amcache/shimcache corroborate independently. Reading only the single last-run field undercounts execution and breaks the timeline's frequency picture. |
| "The Security log is empty, so the attacker did nothing during that window" | An empty or gapped log in an active window is an indicator-removal signal (T1070.001), not proof of inactivity. Treating a cleared log as a clean window hands the attacker their cover story. |
| "All four MFT timestamps agree, so the file creation time is genuine" | Timestomping that only touches `$STANDARD_INFORMATION` leaves `$FILE_NAME` untouched; agreement on one attribute set is not validation. The `$SI`-vs-`$FN` comparison in step 2.2 is what actually tests authenticity. |
| "I'll skip setting the timezone, the timestamps are close enough" | A wrong host timezone or clock offset shifts every artifact uniformly and silently reorders the cross-source timeline, producing a confident but wrong narrative. Anchoring the clock first is what makes the fused timeline defensible. |
| "One artifact shows execution, so I do not need to cross-check the others" | A single source can be tampered with or incomplete; prefetch can be disabled, amcache can lag. Cross-artifact agreement is what makes an execution finding survive a defense challenge, and disagreement is itself a tampering signal. |

## Verification

- [ ] The image acquisition SHA-256 matches the received image and is recorded, and the image is mounted read-only.
- [ ] The host timezone and clock offset are established before any timestamp is interpreted.
- [ ] The MFT `$STANDARD_INFORMATION`-vs-`$FILE_NAME` comparison is documented, with any timestomping delta listed (or "none").
- [ ] Program-execution evidence is cross-checked across prefetch, amcache, and shimcache, and deleted-but-executed binaries are flagged.
- [ ] Persistence keys carry their hive last-write times and are placed on the timeline.
- [ ] Event-log clearing or gaps are explicitly annotated as indicators rather than treated as clean windows.
- [ ] A single normalized super-timeline exists where every entry cites its artifact source and each significant event carries an ATT&CK mapping.
- [ ] Confirmed events are distinguished from inferred ones in the timeline.
- [ ] The source image re-hash matches the acquisition digest and the derived-artifact case directory is hashed with analyst, date, and parser versions.

## Limitations

State these boundaries in the report so the timeline is not over-read.

- Artifacts age out. Prefetch holds a bounded number of entries, $UsnJrnl wraps, and event logs roll over, so an absent record is not proof an action never happened.
- A confident anti-forensic actor can clear or forge multiple artifacts; cross-artifact agreement raises confidence but no single timeline line is unforgeable on its own.
- Execution artifacts (amcache/shimcache/prefetch) prove a binary was present or registered, which is not always the same as proving it executed with malicious effect; corroborate with event logs and file activity.
- Disk artifacts cannot recover what lived only in memory (injected code, in-memory connections); pair with [[memory-forensics]] when a memory image is available.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers used here.
- [[memory-forensics]] - the volatile-memory counterpart; correlate disk artifacts against in-memory process and connection evidence.
- [[persistence-mechanism-hunting]] - turns the registry/service/scheduled-task persistence findings into proactive fleet-wide detections.
- [[incident-postmortem]] - consumes the fused timeline and ATT&CK-mapped events this skill produces.
