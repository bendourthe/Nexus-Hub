---
name: log-threat-hunting
description: Run hypothesis-driven threat hunts across host, network, and cloud logs to surface adversary behavior that signature-based detection misses, then promote confirmed findings into durable detections. Make sure to use this skill whenever the user says "threat hunt", "hunt through these logs", "do an IOC sweep across logs", "run a hypothesis-driven hunt", "find suspicious activity in logs", "scan logs for indicators of compromise", "look for an adversary in our telemetry", or otherwise asks to proactively search telemetry for compromise rather than wait for an alert. SKIP, do NOT use for, building standing detection rules from a known pattern (use siem-detection-engineering) and debugging application errors or performance from logs (use debug-with-logs).
summary_l0: "Run hypothesis-driven hunts across logs to surface adversary behavior, then promote findings to detections"
overview_l1: "This skill teaches the agent how to run a defensive, hypothesis-driven threat hunt across host, network, and cloud telemetry to find adversary behavior that signature detection missed. It covers framing a falsifiable hunt hypothesis from a threat model or intel, scoping the data sources and time window, running iterative queries that pivot on suspicious entities, sweeping a curated indicator-of-compromise (IOC) list with a local read-only scanner, separating true findings from benign baseline activity, and the critical last step: promoting any confirmed finding into a durable SIEM detection so the same behavior is caught automatically next time. It ships a deterministic local helper (ioc-log-scan) that matches an IOC list against a log file with counts and never makes a network call. Defender's seat only - proactive detection and triage, never offensive use. Trigger phrases: threat hunt, IOC sweep, hypothesis-driven hunt, hunt the logs."
mitre_attack: [T1059, T1071]
d3fend_techniques: [D3-NTA, D3-PA]
nist_csf: [DE.CM, DE.AE]
---

# Log Threat Hunting

Proactively search host, network, and cloud telemetry for adversary behavior that signature-based detection missed, using a falsifiable hypothesis and an iterative pivot loop. Every confirmed finding ends with a durable detection so the behavior is caught automatically next time.

## When to Use This Skill

Use when:

- A user asks to threat hunt, hunt through logs, or proactively look for an adversary in telemetry.
- Threat intel or a threat model produces a behavior worth searching for before any alert fires.
- An IOC list (hashes, domains, IPs, user agents) needs to be swept across stored logs.
- A suspicion exists ("something feels off") that needs to be turned into a testable hypothesis and checked against data.
- An incident's scope needs broadening to find related activity the original alert did not cover.

**When NOT to use:**

- Building a standing detection rule from an already-known pattern - use [[siem-detection-engineering]] (this skill feeds it, it does not replace it).
- Debugging application errors, latency, or crashes from logs - use [[debug-with-logs]].
- Hunting specifically for lateral movement across authentication and network telemetry - use [[lateral-movement-detection]] for that focused workflow, then return here for the broader hunt.

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md).

### 1. Frame a falsifiable hypothesis

Write the hunt hypothesis as a single testable statement, for example: "An adversary is using a scripting interpreter (T1059) to stage tools in a user-writable directory on at least one workstation in the last 14 days." A good hypothesis names the behavior, the expected artifact, the data source, and the time window. If you cannot state how the hunt could come back empty, it is not falsifiable - refine it.

### 2. Scope data sources and time window

List the telemetry the hypothesis requires (process-creation logs, DNS/proxy logs, cloud audit/sign-in logs) and confirm each is retained for the window you want to hunt. Record the exact indices, log paths, or tables and the start/end timestamps so the hunt is reproducible.

### 3. Run the iterative pivot loop

Start with a broad query for the hypothesized behavior, then pivot on every suspicious entity it returns (host -> user -> parent process -> network destination). Each pivot either strengthens or kills the hypothesis. Keep a running notebook of queries run, entities pivoted on, and what each result ruled in or out, so the hunt is auditable and another analyst can reproduce it.

### 4. Sweep the IOC list with the local helper

When the hypothesis includes concrete indicators (hashes, domains, IPs, user-agent strings), sweep them across exported log files with the bundled local scanner described in the Helper Script section below. Treat IOC hits as leads to pivot on, not as conclusions - a matched domain in a proxy log still needs the surrounding session reviewed.

### 5. Separate findings from baseline

For every candidate hit, compare against the environment's known-good baseline (authorized admin tooling, scheduled jobs, vendor automation). Document why each retained finding is anomalous in one sentence. A "finding" that turns out to be sanctioned automation is a baseline note, not an incident - record it so future hunts do not re-flag it.

### 6. Promote confirmed findings into a durable detection

This is the step that distinguishes a hunt from a one-off search: for every confirmed true positive, hand the behavior to [[siem-detection-engineering]] and author a standing rule with a seeded test so the same behavior alerts automatically next time. A hunt that finds a real adversary behavior but produces no durable detection guarantees the next instance is found by hand again.

### 7. Hand off or escalate

If the hunt confirms active compromise, escalate to incident response with the entity list, timeline, and supporting queries. If it comes back empty, record the negative result (hypothesis, scope, window, queries) so the same ground is not re-hunted blindly later.

### Helper Script

This skill ships a deterministic, read-only local helper that matches a curated IOC list against a log file and reports each matching line with per-indicator counts. It is purely local and makes no network call - it only reads the files you point it at.

- POSIX: run `scripts/ioc-log-scan.sh` and pass the path to the log file and the path to the IOC list file.
- Windows: run `scripts/ioc-log-scan.ps1` with the same two arguments.

Both variants take a log file path and an IOC list file path (one indicator per line), then print matching lines grouped with a count per indicator. Use the output as pivot leads for step 3, never as a final verdict.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We have detections already, so a hunt is redundant" | Signature detections only catch behaviors someone already wrote a rule for. A hunt exists to find the behaviors that fell through that net; skipping it means novel tradecraft sits undetected until it causes damage. |
| "An IOC match is a confirmed compromise, ship the incident" | IOC lists go stale and produce collisions (a reused IP, a sinkholed domain, a benign tool with a flagged hash). Treating a raw match as a verdict instead of a lead generates false incidents that burn responder trust. |
| "I will hunt without writing the hypothesis down - I know what I am looking for" | An unwritten hypothesis cannot be falsified, so the hunt drifts and never reaches a clean empty/positive conclusion. Six months later nobody can tell whether this ground was already covered, so it gets re-hunted from scratch. |
| "The hunt found the adversary - the job is done" | A finding with no durable detection means the identical behavior will only be caught by the next manual hunt. Promoting every confirmed finding into a standing rule is what converts one-time effort into permanent coverage. |
| "I will pivot in my head and not record the queries" | An unrecorded hunt is unauditable and unreproducible; a peer cannot verify the conclusion and IR cannot reconstruct the timeline. The query notebook is the evidence, not overhead. |

## Verification

- [ ] The hunt hypothesis is written as a single falsifiable statement naming behavior, artifact, source, and time window.
- [ ] The data sources and exact time window are recorded and confirmed retained for that window.
- [ ] A query notebook exists listing each query run and what each result ruled in or out.
- [ ] The IOC sweep was run with `scripts/ioc-log-scan.sh` or `scripts/ioc-log-scan.ps1` and the matching-line counts are captured.
- [ ] Each retained finding has a one-sentence justification for why it is anomalous versus the known baseline.
- [ ] Every confirmed true positive is handed to detection engineering and has a durable rule authored (or a ticket to author one).
- [ ] The hunt ends in a recorded outcome: escalation with an entity/timeline, or a logged negative result.

## Related Skills

- [[security-framework-mapping]] - tag confirmed findings with the ATT&CK / D3FEND / NIST CSF identifiers they map to.
- [[siem-detection-engineering]] - the promotion target: turn each confirmed hunt finding into a durable, tested detection rule.
- [[debug-with-logs]] - operational (non-security) log investigation; use it for errors and performance, not adversary hunting.
- [[lateral-movement-detection]] - the focused hunt for cross-host movement that complements this broad-spectrum hunt.
