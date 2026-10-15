---
name: memory-forensics
description: "Analyze a volatile-memory image (RAM capture) to detect injected code, hidden processes, malicious network connections, and credential-theft artifacts using a fixed Volatility 3 triage plugin workflow. Make sure to use this skill whenever the user says \"analyze a memory dump\", \"RAM forensics\", \"run volatility\", \"find injected processes in a memory image\", \"memory image triage\", or \"extract processes and network connections from a capture\", even when they only hand you a .raw / .lime / .vmem path and ask what is in it. SKIP, do NOT use for: live response on a running host (use [[endpoint-edr-detection]]) or disk-image forensics over an .E01 / .dd filesystem image (use [[disk-artifact-forensics]])."
summary_l0: "Triage a RAM image for injected code, hidden processes, and credential artifacts"
overview_l1: "This skill drives defensive analysis of a captured volatile-memory image (RAM dump) to reconstruct what was running at acquisition time. It teaches a deterministic Volatility 3 triage sequence: enumerate the process tree, diff visible processes against carved/hidden ones, list network connections, hunt for process-injection and reflectively-loaded code, and extract credential-theft indicators such as LSASS access residue. The workflow is read-only against an immutable image, hashes the image before and after, and never executes carved samples. It maps the findings to ATT&CK credential-access and defense-evasion techniques and to D3FEND process-analysis countermeasures so an analyst can route each indicator into an incident record. A bundled helper script wraps a locally-installed vol binary to run the fixed plugin set against an image path with no network symbol fetches."
mitre_attack: [T1003.001, T1055, T1620]
d3fend_techniques: [D3-PA, D3-PSA]
nist_csf: [DE.CM, DE.AE]
---

# Memory Forensics

Analyze an acquired volatile-memory image to reconstruct the processes, injected code, network connections, and credential-theft artifacts present at capture time, and turn each observation into a defensible incident indicator. This is a defender-seat workflow that runs read-only against an immutable image; it never executes carved code.

## When to Use This Skill

- The user hands you a RAM capture (`.raw`, `.lime`, `.mem`, `.vmem`, `.dmp`, hibernation/crash dump) and asks what was running.
- An incident requires confirming whether a process was injected or hollowed (reflective loading, unbacked executable memory).
- You need to list the network connections that existed only in memory and never touched disk logs.
- You suspect credential theft and want to confirm LSASS access residue or carved secret material in memory.
- You are triaging an endpoint pulled offline and only a memory image (not the live host) is available.
- A captured hibernation file, crash dump, or hypervisor snapshot needs to be analyzed for what was resident at capture time.
- You must confirm or refute an EDR alert (for example "process injection detected") against the ground truth in the memory image.

**When NOT to use:**

- Live triage of a still-running host - use [[endpoint-edr-detection]] for live EDR telemetry and response.
- Filesystem / disk-image forensics (MFT, registry hives, prefetch on an `.E01` or `.dd` image) - use [[disk-artifact-forensics]].
- Rotating or revoking credentials you found - that is an IR-runbook action, not a memory-analysis action.
- Any request to weaponize, run, or evade detection on a carved sample - out of scope; analysis only.

## Triage Plugin Map

Each triage question maps to a Volatility 3 plugin family. Run the whole set; do not cherry-pick, because the hidden-process and injection findings only emerge from cross-plugin diffs.

| Question | Plugin family (Volatility 3) | What it answers |
|---|---|---|
| What was running? | `windows.pslist` / `windows.pstree` | Visible process list and parent/child tree. |
| What is hidden? | `windows.psscan` | Carved processes from pool scanning, diffed against the visible list. |
| What loaded into a process? | `windows.dlllist` / `windows.ldrmodules` | Loaded modules vs unlinked / unbacked modules. |
| Where is injected code? | `windows.malfind` | Executable private regions not backed by an image file. |
| What was talking out? | `windows.netscan` | Connection table (local/remote/port/PID/state). |
| What touched LSASS? | `windows.handles` / `windows.dumpfiles` | Handles to LSASS and dumpable secret-bearing regions. |
| What commands ran? | `windows.cmdline` | Per-process command lines for context. |

Linux and macOS images use the equivalent `linux.*` / `mac.*` plugin families; the cross-plugin diff logic is identical.

## Instructions

### 1. Preserve and verify the image

1. Treat the image as read-only evidence. Work on a copy, never the original acquisition.
2. Hash the image before analysis and record the digest: `sha256sum <image_path>` (PowerShell: `Get-FileHash <image_path> -Algorithm SHA256`).
3. Note acquisition metadata (tool, time, host, OS build) in your case notes so plugin output can be interpreted against the right OS profile.
4. Store the image and all derived artifacts in a case-scoped directory you can later hash as a unit, so the evidence set is reproducible.
5. If the image is a hibernation file or crash dump, record that conversion step explicitly - the converted artifact gets its own hash so the chain remains unbroken.

### 2. Establish the OS context

1. Confirm Volatility 3 is installed locally (`vol --help` resolves) and that symbol tables are present offline.
2. Identify the OS family from acquisition metadata; Volatility 3 auto-detects the kernel symbols from the image, so do not fetch symbol packs from the network during an investigation.
3. Record the detected kernel build in case notes - it scopes which artifacts are meaningful.

### 3. Enumerate and diff the process tree

1. List the visible process tree (parent/child relationships, command lines, start times).
2. Carve processes from pool tags / kernel structures independently of the visible list.
3. Diff the two lists. A process present in the carved set but absent from the visible tree is a hidden-process indicator (possible direct kernel object manipulation or unlinking).
4. Flag suspicious parentage (for example a browser or office process spawning a shell) for follow-up.
5. Capture per-process command lines so a benign-looking image name with a malicious argument string is not overlooked.

### 4. Hunt for injected and reflectively-loaded code

1. Scan process memory for regions that are executable but not backed by an on-disk image (private, RX/RWX, image-less mappings) - this is the core process-injection indicator (ATT&CK T1055).
2. Look for reflectively-loaded modules: in-memory PE headers with no corresponding module-list entry, mismatched in-memory vs on-disk module hashes, or carved unbacked executables (ATT&CK T1620, reflective code loading).
3. Triage each hit against its owning process: a JIT compiler or a script host legitimately allocates executable private memory, so judge by owner and module backing, not by the RWX flag alone.
4. Dump only the suspicious regions to disk for offline static review; never execute them. Hash each dump and record the source PID and virtual address.

### 5. Reconstruct network connections

1. Enumerate the connection table preserved in memory (local/remote address, port, owning PID, state).
2. Correlate each connection's owning PID back to the process-tree results from step 3 so an orphaned or hidden process owning a remote connection stands out.
3. Record external IPs and ports for enrichment against your threat-intel sources outside this workflow.

### 6. Extract credential-theft artifacts

1. Identify processes that accessed LSASS memory or carved LSASS-derived secret material (ATT&CK T1003.001, OS Credential Dumping: LSASS Memory).
2. Look for handles to LSASS held by non-system processes and for carved secret structures in memory.
3. Record the indicator (which process, what was accessed) - treat any recovered secret material as evidence to be sealed, not reused. Use placeholders like `<recovered_secret>` in your written notes; never transcribe live secret values into reports.

### 7. Helper Script

A bundled helper runs the fixed triage plugin set deterministically against an image path. Run `scripts/volatility-runner.sh <image_path>` on POSIX or `scripts/volatility-runner.ps1 <image_path>` on Windows. The script is a thin wrapper around a locally-installed Volatility 3 (`vol`): it requires Volatility 3 to already be installed and fetches no symbol packs from the network. It executes the same enumerate-processes / diff-hidden / list-connections / find-injection / scan-credential-access sequence above and writes each plugin's output to a per-case directory for review. Inspect the script output; do not let it execute any carved sample.

### 8. Build the indicator set and timeline

1. For each confirmed observation (hidden process, injected region, suspicious connection, credential access) write one indicator line: artifact, owning PID/process, evidence (plugin + offset/hash), and the ATT&CK/D3FEND mapping.
2. Order indicators by process start time where available to seed a timeline that [[incident-postmortem]] can consume.
3. Separate confirmed indicators from leads still needing corroboration so the handoff does not overstate certainty.

### 9. Seal the evidence

1. Re-hash the original image and confirm it matches the pre-analysis digest from step 1.
2. Hash the case directory of derived artifacts (dumps, plugin output) and record it alongside the analyst, date, and tool versions used.
3. Treat any recovered secret material as sealed evidence; reference it by placeholder in reports and never reuse it operationally.

Framework mappings are documented in [references/standards.md](references/standards.md).

## Evidence Handling and Chain of Custody

Memory analysis is only useful if its conclusions survive scrutiny, so treat the image as evidence from first contact.

- Record who acquired the image, with what tool and version, on which host, and at what time, before you open it.
- Never analyze the original acquisition; derive a working copy and document the copy operation.
- Keep an append-only activity log: every plugin run, every region dumped, every hash computed, with timestamps.
- Store dumped regions and carved samples in a quarantined location that is not on the analysis host's execution path, so an accidental double-click cannot detonate them.
- When a finding involves recovered secret material, log only that secret material was recovered and where; never copy the value into the case notes (use a placeholder such as `<recovered_secret>`).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The visible process list is clean, so the host is clean" | Unlinked or directly-manipulated process objects do not appear in the visible list; only the carve-and-diff step in 3.2-3.3 surfaces them. Skipping the diff is exactly how a hidden implant survives triage. |
| "I'll just run the carved executable to see what it does" | Executing a carved sample on the analysis host detonates malware on your own workstation and destroys the read-only chain of custody. Dump, hash, and review statically; detonation belongs in an isolated sandbox owned by a different workflow. |
| "Network connections aren't worth checking - the firewall logs have them" | In-memory connection tables capture short-lived or pre-logging C2 sockets that never reached the perimeter logger, and they tie the socket to an owning PID the firewall log cannot. The memory view is the only place PID-to-socket attribution survives. |
| "I can skip hashing the image - it's a copy anyway" | Without a pre/post hash you cannot prove the image was unaltered during analysis, and any indicator you derive becomes inadmissible. The hash in step 1.2 is what makes every later finding defensible. |
| "Injected-code scanning produces too many false positives to bother" | Legitimate JIT regions are distinguishable from malicious unbacked RX mappings by owning process and module backing; treating the scan as noise means missing the single hollowed process that matters. Triage the flags, do not suppress the scan. |
| "I only need the plugin that matches the alert, not the full set" | Hidden processes and injection surface only from the diff between `pslist` and `psscan` and between loaded and unbacked modules. Running a single plugin removes the comparison that produces the finding, so the implant the alert hinted at stays invisible. |

## Verification

- [ ] The pre-analysis and post-analysis SHA-256 of the image are recorded and identical.
- [ ] The helper script output directory contains one file per triage plugin in the fixed set.
- [ ] The visible-vs-carved process diff is documented, with any hidden-process delta explicitly listed (or "none" stated).
- [ ] Every flagged injected/reflective memory region was dumped to disk and hashed, and no carved sample was executed.
- [ ] The network-connection table is reconstructed and each remote connection is attributed to an owning PID from the process tree.
- [ ] Each confirmed indicator carries an ATT&CK and D3FEND mapping and feeds a timeline line consumable by incident review.
- [ ] Confirmed indicators are separated from unverified leads in the handoff.
- [ ] The case directory of derived artifacts is hashed and recorded with analyst, date, and tool versions.
- [ ] No live secret value is transcribed into the report; recovered secret material is referenced by placeholder only.

## Limitations

State these boundaries in any report so the findings are not over-read.

- A memory image is a single point in time; it shows what was resident at acquisition, not what ran earlier and exited. Absence of a process is not proof it never ran - corroborate with [[disk-artifact-forensics]].
- Anti-forensic tooling can manipulate kernel structures so that even the carve-and-diff step under-reports; a clean diff lowers but does not eliminate suspicion.
- Carved network connections lack full session content; they attribute a socket to a PID but do not prove what data crossed it.
- Symbol coverage for an uncommon or heavily-customized kernel may be incomplete, which can suppress some plugin output; record any plugin that failed to resolve symbols rather than treating its silence as a negative result.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers used here.
- [[disk-artifact-forensics]] - the on-disk counterpart; correlate memory indicators against filesystem and registry artifacts.
- [[hunting-credential-dumping]] - turns the LSASS-access indicators from step 6 into proactive detection logic across the fleet.
- [[incident-postmortem]] - consumes the indicator set and timeline this skill produces.
