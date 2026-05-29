---
name: siem-detection-engineering
description: Author, tune, and test SIEM detection rules and correlation logic as portable Sigma-style rules and platform-native queries, with a disciplined false-positive-management and seeded-test-event workflow that proves each rule fires before it ships. Make sure to use this skill whenever the user says "write a detection rule", "author a Sigma rule", "build a correlation rule", "SIEM correlation search", "tune this alert", "reduce false positives", "do detection engineering", "lower the noise on this alert", or otherwise asks to create or refine analytics that watch security telemetry. SKIP, do NOT use for, standing log-pipeline or observability infrastructure (use observability-setup) and one-off hypothesis hunting that does not produce a durable rule (use log-threat-hunting).
summary_l0: "Author, tune, and test portable SIEM detection rules with seeded-event proof and FP management"
overview_l1: "This skill teaches the agent how to engineer durable SIEM detections defensively: translate an adversary behavior into a hypothesis, express it as a portable Sigma-style rule plus a platform-native query (Splunk SPL, Elastic, Sentinel KQL), and prove the rule fires by replaying a seeded benign test event before it ships. It covers selecting the right log source and required fields, writing precise selection-plus-condition logic, scoping with allow-lists instead of broad exclusions, measuring and driving down false positives with a tracked tuning loop, versioning rules with metadata (author, references, MITRE technique, severity), and gating promotion on a binary test-fires check. The defender's seat only: building detection content and noise control, never evasion or offensive use. Trigger phrases: detection engineering, Sigma rule, correlation search, alert tuning, reduce false positives, SIEM analytics."
mitre_attack: [T1059, T1071]
d3fend_techniques: [D3-NTA, D3-PA]
nist_csf: [DE.CM, DE.AE, DE.DP]
---

# SIEM Detection Engineering

Engineer SIEM detection rules and correlation logic as durable, portable, tested content rather than ad-hoc one-off searches. This skill keeps the agent in the defender's seat: every rule must map to a behavior, ship with a seeded test that proves it fires, and carry a tracked false-positive budget.

## When to Use This Skill

Use when:

- A user asks to write a new detection rule, author a Sigma rule, or build a SIEM correlation search.
- An existing alert is too noisy and the user wants to tune it or reduce false positives without losing true positives.
- A hunt or incident surfaced a behavior worth converting into a standing, repeatable detection.
- A detection needs to be made portable across SIEM platforms (Sigma source of truth, then platform-native query).
- A rule needs metadata, severity, and a MITRE technique mapping before it can be promoted to production.

**When NOT to use:**

- Building or operating the log-collection, parsing, or routing pipeline itself - use [[observability-setup]].
- Running a single hypothesis-driven sweep that does not produce a durable rule - use [[log-threat-hunting]].
- Debugging application errors or performance from logs - use [[debug-with-logs]].
- Writing endpoint-agent (EDR) telemetry rules specifically - use [[endpoint-edr-detection]] for the EDR-native surface, then return here to port the logic to the SIEM.

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md).

### 1. Define the detection hypothesis

State the behavior in one sentence before writing any query. Example: "A scripting interpreter spawned by a document-handling process executes an encoded command line." Name the ATT&CK technique it covers (here, command and scripting interpreter activity, T1059). A rule without a one-sentence behavior is untunable later because nobody knows what a true positive looks like.

### 2. Pick the log source and confirm required fields

Identify the exact log source (process-creation events, proxy/firewall flow logs, authentication logs) and list the fields the rule depends on (for example: process name, parent process, command line, user, host). Confirm those fields are actually populated in the environment by running a scoping query that returns recent raw events. If a required field is empty or absent, the rule cannot fire - fix the data dependency first.

### 3. Write the portable Sigma-style rule as the source of truth

Express the logic as a Sigma-style rule so it is platform-agnostic and reviewable. Use a precise `selection` block plus an explicit `condition`, and prefer narrow `filter` allow-lists over broad wildcard exclusions.

```yaml
title: Encoded Interpreter Command From Document Handler
status: experimental
description: Scripting interpreter launched by an office document process running an encoded command line.
references:
    - https://attack.mitre.org/techniques/T1059/
author: detection-engineering
date: 2026/05/29
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        ParentImage|endswith:
            - '\winword.exe'
            - '\excel.exe'
        Image|endswith: '\powershell.exe'
        CommandLine|contains:
            - ' -enc '
            - ' -EncodedCommand '
    filter_known_admin:
        User|startswith: 'SVC_'
    condition: selection and not filter_known_admin
level: high
tags:
    - attack.execution
    - attack.t1059
falsepositives:
    - Signed administrative automation; track in the allow-list, do not widen the rule.
```

### 4. Translate to the platform-native query

Generate the equivalent query for the target SIEM (Splunk SPL, Elastic Query DSL/EQL, or Sentinel KQL). Keep field names mapped explicitly to the platform's schema so the Sigma rule remains the canonical version. Do not hand-tune the platform query in ways that drift from the Sigma source - change Sigma first, regenerate.

### 5. Seed a benign test event and prove the rule fires

Generate or replay a non-malicious event that matches the selection logic (for example, an authorized lab host running an encoded but harmless command in a test index), then run the rule against it. The rule MUST return that seeded event. This is the binary gate: a detection that has never fired against a known-matching input is unverified. Use a dedicated test index or label so seeded events are isolated from production data.

### 6. Run the false-positive tuning loop

Run the rule over a recent window of real telemetry (for example, 7 to 14 days) and review every hit. For each false positive, prefer a narrow allow-list entry (specific service account, specific signed binary, specific host group) over loosening the core selection. Record the FP rate before and after each tuning pass. Set a noise budget (for example, alerts per analyst per shift) and do not promote until the rate is under budget while the seeded true positive still fires.

### 7. Add metadata and promote

Finalize rule metadata: stable title, unique id, author, creation/modified date, references (public ATT&CK URLs), severity/level, ATT&CK tags, and a `falsepositives` note describing each known-benign pattern. Move `status` from `experimental` to `test` to `stable` as confidence grows. Version the rule in source control so changes are reviewable and revertible.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The query looks right, so it works - no need to seed a test event" | A query that parses cleanly can still match zero real events because a field is empty, mis-mapped, or named differently in this SIEM. Without a seeded matching event, the first time you learn the rule never fired is during a breach post-mortem. |
| "I will exclude the noisy values with a broad wildcard to ship faster" | A broad exclusion (for example, excluding an entire host subnet or any command containing a common word) silently creates a blind spot an adversary can live inside. Narrow allow-lists fail safe; broad excludes fail open. |
| "Tuning is the SOC's job after handoff, not mine" | Shipping a rule above its noise budget trains analysts to ignore it, so the eventual true positive is closed as noise. Measuring and driving down the FP rate before promotion is part of authoring the rule, not a downstream chore. |
| "One platform query is enough; portability is over-engineering" | Single-platform rules rot when the org migrates SIEMs or runs two in parallel, and they cannot be peer-reviewed by anyone who does not know that query language. A Sigma source of truth keeps the logic reviewable and the platform query regenerable. |
| "Mapping to an ATT&CK technique is paperwork" | Without a technique mapping and a one-sentence behavior, the rule cannot be placed on a coverage matrix, deduplicated against existing rules, or triaged by an analyst who needs to know what the alert means at 3 a.m. |

## Verification

- [ ] The Sigma-style rule file exists with `title`, `logsource`, `detection.selection`, `detection.condition`, `level`, and `tags`.
- [ ] The required fields named in the selection are confirmed populated by a scoping query against real telemetry.
- [ ] The platform-native query (SPL/KQL/EQL) is generated and its field names map to the target SIEM schema.
- [ ] A seeded benign test event is replayed and the rule query returns that exact seeded event.
- [ ] The false-positive rate is measured over a defined window and recorded before and after at least one tuning pass.
- [ ] Each known false positive is handled by a narrow allow-list entry, not by loosening the core selection.
- [ ] The rule carries an ATT&CK technique tag and a public reference URL, and is committed to version control.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers this rule carries.
- [[log-threat-hunting]] - the hunting loop that surfaces behaviors worth promoting into the detections this skill builds.
- [[observability-setup]] - the log-pipeline and telemetry plumbing this skill's rules consume; build it there, detect here.
- [[endpoint-edr-detection]] - EDR-native detection content that pairs with the SIEM rules authored here.
