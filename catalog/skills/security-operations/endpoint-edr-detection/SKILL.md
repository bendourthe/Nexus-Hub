---
name: endpoint-edr-detection
description: "Detect malicious endpoint behavior from EDR and host telemetry - process injection, suspicious process trees, living-off-the-land binary (LOLBin) abuse, and script-interpreter misuse - then build or tune behavioral detections with low false-positive rates. Make sure to use this skill whenever the user says \"EDR detection\", \"detect process injection\", \"suspicious process tree\", \"LOLBin abuse detection\", \"endpoint behavioral detection\", \"hunt EDR telemetry\", or asks to write, tune, or validate a behavioral rule over host process and command-line data. SKIP, do NOT use for: memory-image forensics (use memory-forensics), or SIEM-wide multi-source correlation engineering (use siem-detection-engineering)."
summary_l0: "Detect process injection, suspicious process trees, and LOLBin abuse from EDR host telemetry"
overview_l1: "This skill teaches the agent to detect malicious endpoint behavior from EDR and host telemetry and to build or tune behavioral detections. It covers the highest-signal behaviors - process injection, anomalous parent-child process trees, abuse of trusted living-off-the-land binaries (LOLBins), and suspicious script-interpreter and command-line activity - and gives a workflow to model normal behavior, write a hypothesis-driven detection, validate it against benign and malicious samples, and tune for an acceptable false-positive rate. It is detection engineering only: it produces analytic logic and triage guidance over host telemetry, never offensive tooling or evasion advice. The skill emphasizes behavior over static signatures, parent-child and command-line context as primary features, and measuring precision before deployment so a noisy rule does not bury responders. Trigger phrases: EDR detection, detect process injection, suspicious process tree, LOLBin abuse detection, endpoint behavioral detection, hunt EDR telemetry."
mitre_attack: [T1055, T1059, T1218]
d3fend_techniques: [D3-PA, D3-PSA]
nist_csf: [DE.CM, DE.AE]
---

# Endpoint EDR Detection

Turn EDR and host process telemetry into reliable behavioral detections for process injection, suspicious process trees, LOLBin abuse, and script-interpreter misuse. This is a detection-engineering skill: it produces analytic logic and triage guidance, never offensive tooling or evasion techniques.

## When to Use This Skill

- You need to detect process injection, abnormal parent-child process relationships, or hollowing from host telemetry.
- A trusted system binary (a LOLBin) is being abused to proxy execution and you need a detection for it.
- Script interpreters (shells, scripting engines) are launching with suspicious command lines and you need behavioral coverage.
- An existing EDR rule is too noisy or too quiet and you need to tune its precision and recall.
- You are hunting EDR telemetry for a specific behavioral hypothesis derived from threat intel.

**When NOT to use:**

- The task is analyzing a captured memory image - use [[memory-forensics]].
- The task is multi-source SIEM correlation across network, identity, and cloud logs - use [[siem-detection-engineering]].
- The task is malware reverse engineering of a binary sample rather than behavioral detection over telemetry.

## Instructions

Detect on behavior, not static signatures, and measure precision before you ship. A rule that fires constantly trains responders to ignore it, so tuning is part of building, not an afterthought.

### 1. Model normal behavior

1. Establish what normal looks like for the in-scope hosts: typical parent-child process chains, common command-line shapes, and the expected callers of sensitive binaries.
2. Identify the legitimate uses of each LOLBin and script interpreter in the environment so the detection can subtract benign activity.
3. Capture which administrative tools and automation routinely produce activity that resembles the target behavior; these are the false positives you must design around up front.

### 2. Form a detection hypothesis

1. State the malicious behavior precisely: for example, a trusted binary spawned by an office application, or a script interpreter launching with an encoded or remote-download command line.
2. Choose the highest-signal features: parent-child lineage, the full command line, the signing status and path of the binary, and any injection indicators (remote thread creation, cross-process memory-permission changes).
3. Map the hypothesis to its technique class (injection, command and scripting interpreter, or system-binary proxy execution) so coverage gaps are visible.
4. Prefer a behavior that is rare-when-benign and common-when-malicious; a feature present in both produces an unusable rule no matter how it is tuned.

### 3. Write the detection

1. Express the analytic over host process and command-line telemetry, anchored on the behavioral features rather than a single hash or filename.
2. Add context conditions that separate the malicious shape from benign use (unexpected parent, user-writable path, unusual flags).
3. Keep the logic readable so a responder can understand on a hit why it fired; an opaque rule cannot be triaged.
4. This per-process behavioral analysis is the MITRE D3FEND process-analysis and process-spawn-analysis lens. Framework mappings are documented in [references/standards.md](references/standards.md). EDR-native detection queries for process injection, suspicious process trees, and LOLBin abuse (Sigma plus Microsoft Defender for Endpoint KQL and Splunk SPL) are in [references/query-examples.md](references/query-examples.md).

### 4. Validate

1. Test against benign samples from the modeled normal behavior to measure false positives.
2. Test against malicious examples (from a contained lab or a trusted detection test harness) to confirm true positives. Do not run live malware outside a contained analysis environment.
3. Record precision and recall so the rule's quality is measurable, not asserted.
4. Re-test after every condition change; a tweak that cuts false positives can silently cut true positives too.

### 5. Tune and document

1. Adjust conditions until the false-positive rate is acceptable for the responder team's capacity, trading the minimum recall needed to get there.
2. Document the rule's hypothesis, the behavior it covers, known benign triggers, and the triage steps an analyst should follow on a hit.
3. Set a review trigger (for example, a periodic re-validation) so environment drift does not silently degrade the rule.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Block the binary hash - that stops the threat" | LOLBins are trusted OS components that cannot be blocked by hash without breaking the system, and attackers recompile or repath payloads, so hash blocking misses the behavior the next variant reuses. |
| "The rule fires, so detection is working" | A rule with no measured precision often fires mostly on benign activity, so responders mute it within a week and the real detonation lands in a muted channel. |
| "Parent-child context is overkill, the command line is enough" | The same command line is benign from one parent and malicious from another (a script interpreter spawned by a document viewer), so dropping lineage either floods the queue or misses the attack. |
| "Signed and in System32, so it is safe" | System-binary proxy execution deliberately uses signed, trusted-path binaries to launch attacker logic, so location and signature alone clear the very technique this skill targets. |
| "I will tune the false positives after it is in production" | Shipping an untuned rule erodes responder trust immediately and the alert fatigue it causes outlasts the rule, so precision must be measured before deployment, not after. |

## Verification

- [ ] A normal-behavior model exists describing expected parent-child chains and the legitimate callers of the targeted binaries and interpreters.
- [ ] Each detection states an explicit behavioral hypothesis and the features it keys on (lineage, command line, path, injection indicators).
- [ ] Each detection is mapped to its technique class (injection, scripting interpreter, or system-binary proxy execution).
- [ ] The detection has measured precision and recall from validation against benign and malicious samples.
- [ ] The rule is documented with its hypothesis, known benign triggers, and analyst triage steps for a hit.

## Related Skills

- [[security-framework-mapping]] - assign ATT&CK / D3FEND / NIST CSF identifiers to the behaviors and detections built here.
- [[hunting-credential-dumping]] - apply the same behavioral-detection workflow to credential-access activity on the host.
- [[persistence-mechanism-hunting]] - feed confirmed persistence patterns into behavioral EDR detections.
- [[siem-detection-engineering]] - escalate single-host detections into multi-source SIEM correlation rules.
