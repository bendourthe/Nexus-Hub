---
name: container-runtime-detection
description: "Detect runtime threats in containers and Kubernetes by analyzing runtime and orchestrator telemetry for container escape to the host, malicious or crypto-mining workloads, suspicious exec-into-pod activity, and privileged-pod abuse, then alerting with evidence. Make sure to use this skill whenever the user says \"container runtime threats\", \"Kubernetes runtime security detection\", \"detect container escape\", \"pod runtime anomaly\", \"detect malicious container\", or \"kubectl exec detection\", including synonyms like \"crypto miner in a pod\", \"privileged container abuse\", \"host namespace breakout\", or \"suspicious process inside a container\". SKIP, do NOT use for: container image scanning or software composition analysis of dependencies and CVEs (use dependency-security-audit), or cluster provisioning, configuration, and Helm or manifest authoring (use kubernetes-expert)."
summary_l0: "Detect runtime threats in containers and Kubernetes from runtime and orchestrator telemetry"
overview_l1: "This skill teaches the agent to detect runtime threats in containers and Kubernetes from runtime and orchestrator telemetry rather than from static image scans. It covers identifying the telemetry sources (container runtime syscall and process events, kernel security events, and Kubernetes audit and orchestrator events), then building detections for the highest-value runtime threats: container escape to the host through privileged mounts, host namespaces, or capability abuse, malicious or crypto-mining workloads, suspicious interactive exec-into-pod sessions, and abuse of privileged or host-networked pods. The skill emphasizes establishing a baseline of expected process and network behavior per workload, correlating runtime events with the Kubernetes audit trail to attribute actions to a user or service account, and emitting alerts with the pod, node, process, and evidence. It is a runtime detection lens; it does not scan images for vulnerabilities and does not provision or configure clusters."
mitre_attack: [T1610, T1611, T1613]
d3fend_techniques: [D3-PA]
nist_csf: [DE.CM, DE.AE]
---

# Container Runtime Detection

Detect runtime threats in containers and Kubernetes so container escape, malicious or crypto-mining workloads, suspicious exec-into-pod sessions, and privileged-pod abuse are caught from live runtime and orchestrator telemetry. This is a runtime detection lens, not an image scanner or a cluster provisioning tool.

## When to Use This Skill

- The user wants detections built over container runtime and Kubernetes audit telemetry.
- A workload may be attempting to escape its container to the underlying host through privileged mounts, host namespaces, or capability abuse.
- A pod may be running a malicious or crypto-mining process and the user wants to detect it at runtime.
- Interactive `kubectl exec` or `docker exec` sessions into running pods need to be detected and attributed.
- Privileged or host-networked pods may be abused and the user wants runtime alerts on their behavior.
- The user wants to baseline per-workload process and network behavior and alert on deviation.

**When NOT to use:**

- Scanning container images for vulnerable packages, CVEs, or license issues. Use [[dependency-security-audit]].
- Provisioning clusters, writing Helm charts, or configuring manifests and RBAC. Use [[kubernetes-expert]].
- Building the base image or hardening the Dockerfile itself. Use [[containerization]].

## Instructions

Framework mappings are documented in [references/standards.md](references/standards.md).

### 1. Identify and confirm telemetry sources

Detection requires live signals. Confirm which sources are available and collected:

- Container runtime events: process exec, file, and network syscalls per container.
- Kernel security events: capability use, namespace changes, and mount activity.
- Kubernetes audit events: API server requests including exec, attach, and pod creation, with the requesting user or service account.

Record which sources exist; a detection that depends on a missing source must be flagged as a coverage gap, not silently skipped.

### 2. Baseline expected behavior per workload

Establish what normal looks like for each workload: the expected set of processes, outbound network destinations, and whether the workload should ever receive an interactive session. A web service that suddenly spawns a shell or connects to a mining pool is anomalous only against a baseline, so capture the baseline first.

### 3. Build detections for the priority runtime threats

Author one detection per threat class:

- Container escape: detect privileged container starts, host namespace use (host PID, network, or IPC), sensitive host-path mounts, and dangerous capability use such as the ability to load kernel modules or access raw devices.
- Malicious or crypto-mining workloads: detect unexpected process names, sustained high CPU paired with connections to mining pools, and execution from writable or temporary paths.
- Suspicious exec-into-pod: detect interactive exec or attach sessions, especially into production or system pods, and attribute each to the requesting identity from the audit log.
- Privileged-pod abuse: detect privileged or host-networked pods performing host-level actions beyond their baseline.

Use obviously fake identifiers in examples, such as pod `example-pod-0000` on node `node-example-0000`.

### 4. Correlate runtime events with the Kubernetes audit trail

Runtime telemetry tells you what happened inside a container; the audit trail tells you who asked for it. Join the two so an exec event is attributed to a specific user or service account and source. Correlation also strengthens confidence: a privileged pod created by an unusual identity that then mounts a host path is a far stronger signal than any single event.

### 5. Emit triaged alerts

For each alert, output the pod, namespace, node, offending process or syscall, the attributed identity where available, the evidence event IDs, a severity, and a triage verdict. Route container-escape and confirmed-malicious-workload alerts to incident response immediately. Keep detection logic in version control so it is reviewable and testable against sample events.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We scan images, so the running containers are safe." | Image scanning catches known vulnerable packages but misses runtime behavior; a clean image can still be exploited live or run a malicious payload injected after start, which only runtime telemetry reveals. |
| "Privileged pods are needed for our agents, so do not alert on them." | A privileged or host-namespaced pod is the primary container-escape vector; suppressing all alerts on it removes the one detection that would catch a breakout, so baseline its expected behavior instead of muting it. |
| "kubectl exec into prod is normal for our oncall." | Untracked interactive sessions are how attackers and insiders operate hands-on; without attributing every exec to an identity and baselining who should do it, a malicious exec is indistinguishable from routine oncall. |
| "High CPU is just a busy workload, not a miner." | Crypto-mining hides behind plausible load; correlating sustained CPU with outbound connections to mining infrastructure and unexpected process names separates a real miner from a busy service that single-metric thresholds would miss. |
| "Container escape is theoretical, we have never seen one." | Host-path mounts, host namespaces, and capability misuse are actively exploited breakout primitives; "never seen one" usually means no runtime detection exists to see it, not that it is not happening. |

## Verification

- [ ] A coverage record lists which runtime, kernel, and Kubernetes audit telemetry sources are collected, with gaps flagged.
- [ ] A per-workload baseline of expected processes, network destinations, and interactive-session expectation exists.
- [ ] A detection exists for each of container escape, malicious or mining workloads, suspicious exec-into-pod, and privileged-pod abuse.
- [ ] Exec and pod-creation events are correlated with the Kubernetes audit trail and attributed to a user or service account where available.
- [ ] Each emitted alert names the pod, namespace, node, offending process or syscall, evidence event IDs, severity, and triage verdict.
- [ ] Detection logic is stored as version-controlled detection-as-code and is testable against sample events.

## Related Skills

- [[security-framework-mapping]] - map each runtime detection to its ATT&CK, D3FEND, and NIST CSF identifier.
- [[kubernetes-expert]] - provision and configure the cluster and RBAC whose audit trail this skill correlates against.
- [[containerization]] - harden the image and Dockerfile so fewer runtime threats are possible in the first place.
- [[endpoint-edr-detection]] - apply the same host-level process and syscall detection lens to the underlying nodes.
