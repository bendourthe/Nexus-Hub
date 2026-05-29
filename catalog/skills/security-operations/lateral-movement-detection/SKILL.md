---
name: lateral-movement-detection
description: Detect adversary lateral movement (RDP, SMB and admin-share access, WMI, remote-service creation, and pass-the-hash or pass-the-ticket) by correlating authentication events and network telemetry across multiple hosts. Make sure to use this skill whenever the user says "detect lateral movement", "pass-the-hash detection", "RDP/SMB lateral movement", "detect remote service creation", "find lateral movement in auth logs", "detect PsExec-style activity", "spot an attacker moving between hosts", or otherwise asks to find an adversary spreading across an internal network. SKIP, do NOT use for, initial-access or phishing analysis (use phishing-analysis-and-defense) and identity-provider or cloud sign-in anomalies (use identity-threat-detection).
summary_l0: "Detect RDP/SMB/WMI/PsExec lateral movement by correlating auth events and network telemetry across hosts"
overview_l1: "This skill teaches the agent how to detect adversary lateral movement defensively by correlating authentication logs and network telemetry across hosts. It covers the common movement vectors (remote desktop, SMB and administrative shares, WMI, remote-service creation in the style of remote-exec tools, and authentication-material reuse such as pass-the-hash and pass-the-ticket), the specific Windows event IDs and network signals that betray each, and how to correlate a source host, destination host, account, and logon type into a single movement story. It builds source-to-destination authentication graphs, flags anomalous service-account interactive logons and many-to-one or one-to-many fan-out patterns, and validates every detection against a seeded benign remote-admin event. Defender's seat only - detection and triage of movement, never how to perform or evade it. Trigger phrases: lateral movement, pass-the-hash, RDP/SMB movement, remote service creation, PsExec-style activity."
mitre_attack: [T1021, T1021.001, T1021.002, T1550]
d3fend_techniques: [D3-NTA, D3-PA]
nist_csf: [DE.CM, DE.AE]
---

# Lateral Movement Detection

Detect an adversary spreading from one internal host to others by correlating authentication events and network telemetry into a single source-to-destination movement story. This skill stays in the defender's seat: it identifies and triages movement, it never teaches how to perform or evade it.

## When to Use This Skill

Use when:

- A user asks to detect lateral movement, pass-the-hash/pass-the-ticket, or remote-service-creation activity.
- An alert or hunt shows one compromised host and you need to find where the adversary went next.
- Remote-access vectors (RDP, SMB/admin shares, WMI) need monitoring for abuse across hosts.
- Authentication telemetry needs to be correlated across machines to spot fan-out or credential reuse.
- An incident's blast radius needs mapping by tracing account usage between systems.

**When NOT to use:**

- Analyzing the initial-access or phishing stage that preceded movement - use [[phishing-analysis-and-defense]].
- Investigating identity-provider, SSO, or cloud sign-in anomalies (impossible travel, OAuth abuse) - use [[identity-threat-detection]].
- Detecting credential-dumping on a single host (the technique that often supplies the material for movement) - use [[hunting-credential-dumping]], then return here to trace where the stolen material was reused.

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md).

### 1. Identify the movement vector to detect

Pick the specific vector and its ATT&CK technique so the detection has a clear target:

- Remote Desktop (T1021.001): interactive remote logons.
- SMB / admin shares (T1021.002): network logons to `ADMIN$`, `C$`, `IPC$` followed by file writes or service creation.
- WMI and remote-service creation: a service or process created on a destination host by a remote account.
- Pass-the-hash / pass-the-ticket (T1550): authentication using stolen material rather than an interactive credential prompt.

### 2. Collect the required authentication and network telemetry

Confirm the log sources are present and retained: Windows Security logs (logon events 4624/4625 with logon type, and the source network address), service-creation events (7045 and 4697), and network telemetry for SMB (port 445) and RDP (port 3389) sessions. Note the logon-type codes that matter (type 3 network, type 10 remote interactive). If logon type or source address is not logged, fix that data dependency before writing the detection.

### 3. Build the source-to-destination correlation

Correlate each remote authentication into a movement edge: source host, destination host, account, logon type, and timestamp. The unit of detection is the edge, not the single event. Join authentication events with the matching network session and any service/process that the session spawned on the destination, so a single alert tells the analyst who moved from where to where and what they did on arrival.

### 4. Flag the anomalous patterns

Apply behavioral logic on top of the edges:

- A service account performing an interactive (type 10) or remote-interactive logon when it should only run non-interactively.
- One source account authenticating to many destinations in a short window (one-to-many fan-out) or many sources hitting one destination (many-to-one).
- Network logon (type 3) immediately followed by remote service creation on the destination - the classic remote-exec pattern.
- Authentication that skips the expected interactive logon sequence, consistent with reused authentication material (T1550). Detect the absence of the normal credential-prompt events, not the secret itself.

### 5. Suppress the known-good baseline

Vulnerability scanners, patch-management tools, monitoring agents, and admin jump hosts produce legitimate many-to-one and one-to-many patterns. Build an allow-list keyed on the specific service account plus source host (not the pattern alone), so sanctioned automation is excluded while an adversary reusing a different account is still caught.

### 6. Seed a benign remote-admin event and validate

Generate or replay an authorized remote-admin action (for example, a sanctioned admin opening an RDP session or creating a service on a lab host) in a test scope, then run the detection. It MUST surface that seeded edge. A movement detection that has never fired against a known remote-admin event is unverified.

### 7. Promote to a standing detection and document the graph

Hand the validated logic to [[siem-detection-engineering]] to ship as a durable correlation rule, and document the movement graph (nodes = hosts/accounts, edges = authentications) so responders can see the spread at a glance and scope the incident.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A single failed-logon spike is enough to call lateral movement" | Lateral movement is defined by the source-to-destination edge, not by event volume on one host. Alerting on raw failed-logon counts misses quiet pass-the-hash success (which often produces a clean 4624) and floods analysts with brute-force noise that is a different problem. |
| "Pass-the-hash means I should look for the hash in the logs" | The stolen authentication material never appears in event logs. The detectable signal is the abnormal authentication pattern (a network logon without the preceding interactive prompt, or NTLM where Kerberos is expected), so a hunt for the secret itself finds nothing and gives false assurance. |
| "Service accounts are noisy, so exclude all of them" | Service accounts are precisely the credentials adversaries steal for movement because they are over-privileged and under-watched. Excluding the whole class creates the exact blind spot the adversary wants; allow-list the specific account-plus-source pair instead. |
| "Network logs alone show the movement" | A port-445 or port-3389 session by itself cannot tell you which account authenticated or whether it succeeded. Without correlating the authentication event, you cannot distinguish a blocked attempt from a successful compromise, and you cannot attribute the move to an account. |
| "The detection is written, so it works" | A correlation rule that has never matched a seeded remote-admin edge may be silently broken by a missing logon-type field or a mis-mapped source-address field. The seeded-event test is the only proof the edge actually assembles. |

## Verification

- [ ] The target movement vector is named with its ATT&CK technique (T1021.001 RDP, T1021.002 SMB, or T1550 alternate authentication material).
- [ ] Authentication logs include logon type and source network address, and service-creation events are present and retained.
- [ ] The detection correlates source host, destination host, account, logon type, and timestamp into a single edge per movement.
- [ ] At least one behavioral pattern (service-account interactive logon, fan-out, or network-logon-then-service-creation) is implemented.
- [ ] A baseline allow-list keyed on account-plus-source excludes sanctioned scanners and admin tooling.
- [ ] A seeded benign remote-admin event is replayed and the detection surfaces that exact edge.
- [ ] A movement graph (host/account nodes, authentication edges) is produced and the logic is handed to detection engineering for a standing rule.

## Related Skills

- [[security-framework-mapping]] - assign and verify the ATT&CK / D3FEND / NIST CSF identifiers this detection carries.
- [[hunting-credential-dumping]] - finds the credential theft on a single host that often supplies the material this skill traces being reused.
- [[log-threat-hunting]] - the broad hypothesis-driven hunt that can surface movement worth building this focused detection for.
- [[identity-threat-detection]] - the cloud and identity-provider sign-in counterpart for movement that happens through the IdP rather than host-to-host.
