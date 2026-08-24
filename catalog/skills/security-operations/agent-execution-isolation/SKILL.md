---
name: agent-execution-isolation
description: "Confine an AI agent with OS-level execution isolation: Landlock filesystem confinement, seccomp syscall filtering, network namespaces, per-session ephemeral containers that mount only listed directories, an out-of-process egress proxy, and placeholder credentials so real API keys never sit inside the agent container. Use this skill whenever the user says \"sandbox my agent\", \"Landlock\", \"seccomp\", \"egress proxy for agents\", \"isolate the agent container\", \"agent credential isolation\", or wants the agent sandboxed so it cannot read SSH keys or exfiltrate data. SKIP: host config-write trust-seam escapes (use [[agentic-endpoint-hardening]]); agent-applied content redaction before send (use [[egress-redaction]]); generic application Dockerfiles with no agent runtime (use [[containerization]])."
summary_l0: "Run agents in OS-level isolation with ephemeral containers and an egress boundary"
overview_l1: "This skill teaches a three-layer model for running AI agents inside OS-level execution isolation. Layer one is infrastructure: a container sandbox hardened with Landlock filesystem confinement, seccomp syscall filtering, and network namespaces, plus per-session ephemeral containers that mount only explicitly listed directories. Layer two is runtime: keep the in-loop software small and auditable, stripping extra parsers and unpatched helpers. Layer three is network: assume the container is compromised and put an out-of-process egress boundary in front of it, with static URL rules for low-risk traffic, an LLM judge for unmatched high-risk requests, SSRF and RFC-1918 blocking, audit logging, and human-in-the-loop escalation. The first-class checklist is three questions: where does execution happen, what software runs inside the loop, and what leaves the boundary. This skill extends /review security when the reviewed project spawns agents, holds agent credentials, or makes agent-driven egress calls."
mitre_attack: [T1611, T1552, T1071]
d3fend_techniques: [D3-NTA, D3-PA, D3-FA]
nist_csf: [PR.AC, PR.DS, DE.CM]
---

# Agent Execution Isolation

Run AI agents inside OS-level execution isolation. Semantic instructions are not a boundary: a captured agent will skip them. This skill is the infrastructure counterpart to host trust-seam hardening and agent-applied content policy. It does not name or adopt a particular sandbox product. It teaches the durable pattern: confine the filesystem and syscalls, keep the in-loop runtime small, and move the network perimeter outside the agent process.

This skill **extends `/review security`** when the reviewed project runs or embeds AI agents. The applicability check is three yes/no questions: does the repo spawn agents, hold agent credentials, or make agent-driven egress calls? If every answer is no, skip this skill and record why. If any answer is yes, run the three-question triage below and treat a missing layer as a finding, not as out of scope.

## When to Use This Skill

- The user wants to sandbox a coding agent, isolate the agent container, or stop the agent reading SSH keys or host secrets.
- The design needs Landlock, seccomp, network namespaces, or per-session ephemeral containers with explicit mounts only.
- Real API keys must stay out of the agent environment (placeholder credentials in the container, a broker at the boundary).
- Egress from the agent must go through an out-of-process proxy the agent cannot disable.
- `/review security` is running and the applicability check above is true.

**When NOT to use:**

- The question is a host config-write that a trusted component later executes: use [[agentic-endpoint-hardening]].
- The question is redacting or hashing content the agent itself is about to send: use [[egress-redaction]].
- The question is a generic application Dockerfile with no agent runtime: use [[containerization]].
- The question is recognizing a hostile instruction as it arrives: use [[prompt-injection-defense]].
- The question is lifecycle, RBAC, and observability for a deployed service agent: use [[ai-agent-governance]].

## Three-Question Triage

Answer these before choosing controls. An unanswered question is an open finding.

| # | Question | What "unknown" means | Pass |
|---|---|---|---|
| 1 | Where does execution happen? | The agent process, its tools, and any helper daemons have no named isolation boundary (host, VM, container, nested sandbox). | Every executor is named and sits inside a documented isolation tier. |
| 2 | What software runs inside the loop? | The agent image, tool runners, parsers, and interpreters are an unbounded set. | The in-loop inventory is listed, minimal, and auditable. |
| 3 | What leaves the boundary? | Egress destinations, credentials on the wire, and who can change policy are unknown. | Egress is mediated outside the agent, credentials are injected at that mediator, and policy change is human-gated. |

Do not treat a yes on question 1 as coverage for questions 2 and 3. A container with a fat image and host networking fails 2 and 3 even when 1 looks done.

## Instructions

### 1. Confirm applicability

1. Check whether the project spawns agents, stores agent credentials, or issues agent-driven outbound calls.
2. If none of those hold, stop and write `not applicable: no agent execution, credentials, or egress`.
3. If any hold, fill the triage table and continue.

### 2. Place execution (layer 1: infrastructure)

1. Run each agent session in its own ephemeral container. Destroy the container at session end. Do not reuse a long-lived agent VM as the isolation story.
2. Mount only directories the task needs, read-only unless a write is required. Home directories, SSH keys, cloud credential files, and the Docker socket stay unmounted unless a written exception names why.
3. Apply kernel confinement inside that container: Landlock for filesystem paths, seccomp for the syscall set, and a network namespace so the agent has no raw host routing. Details and a Linux baseline live in [references/os-sandboxing.md](references/os-sandboxing.md).
4. Drop ambient capabilities, set no-new-privileges, and prefer a read-only root filesystem with a tmpfs scratch dir.
5. Record the isolation tier in the review: host process (fail), shared long-lived container (weak), per-session ephemeral container plus kernel filters (pass).

### 3. Shrink the in-loop runtime (layer 2: runtime)

1. Inventory every binary, interpreter, parser, and helper that runs in the agent container.
2. Remove anything the current task does not call. Extra parsers and unpatched utilities are the usual RCE surface after a tool-output injection.
3. Pin and scan the remaining image. A "latest" tag is a finding.
4. Do not put a privileged sidecar, a Docker socket, or a host-network helper in the same loop "for convenience".

### 4. Move the network perimeter outside the agent (layer 3: network)

1. Assume the container is compromised. Controls that run as the agent (prompt rules, agent-applied redaction) are not this layer.
2. Force all agent HTTP/HTTPS through an out-of-process egress proxy. Block raw sockets, alternate ports, and DNS that bypasses the proxy.
3. Encode low-risk destinations as static URL rules. Send unmatched high-risk requests to an LLM judge that cannot execute tools. Block SSRF and RFC-1918/link-local targets. Log every decision. Escalate denials to a human whose approval can update policy. The architecture is in [references/egress-boundary.md](references/egress-boundary.md).
4. Pair this layer with [[egress-redaction]] for content policy. Redaction is not a substitute for the proxy.

### 5. Keep real credentials out of the agent environment

1. The agent environment holds placeholder or scoped-down tokens that fail against production APIs.
2. A broker outside the container (the egress proxy or a host-side injector) substitutes real keys only onto requests that already passed policy.
3. A hijacked agent cannot exfiltrate keys it never held. This does not protect the broker itself, and it does not stop misuse of an already-approved destination. [[agentic-endpoint-hardening]] owns the host trust seam around that broker; [[authentication-patterns]] owns application auth protocols.

### 6. Record residual risk

Write down what remains: kernel features the host lacks, destinations that had to be allowlisted, brokers that still hold keys, and any human-approval path that is not wired. An isolation design with no residual-risk section is incomplete.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The agent is already sandboxed by the IDE" | IDE sandboxes usually still see the workspace, user credentials, and the network. Name the actual boundary (process, container, kernel filters, egress proxy) rather than the product label. |
| "Docker is enough" | A container with host networking, a mounted home directory, and the Docker socket is a packaging format, not isolation. Without Landlock/seccomp/netns plus an external egress proxy, a captured agent still reads secrets and leaves the box. |
| "We redacted the prompt, so egress is handled" | Agent-applied redaction is a content policy the agent can skip. Question 3 requires a mediator the agent cannot turn off. |
| "Putting API keys in the container is simpler" | Anything the agent can read, a captured agent can exfiltrate. Placeholder credentials plus a broker is the control; convenience is not. |
| "Landlock/seccomp are Linux-only, so we will skip isolation on this host" | Record the missing kernel features as accepted risk and still apply ephemeral containers, mount discipline, and the egress proxy. Skipping every layer because one kernel feature is absent is how hosts stay wide open. |
| "The LLM judge on the proxy might be injected" | That is why static rules handle the default path, the judge cannot execute tools, SSRF ranges are blocked in code, and a human gate sits on policy changes. The judge is a residual risk, not a reason to omit the proxy. |
| "This is a local coding agent, not a production service" | Local agents hold the operator's keys and the repo. The blast radius is the operator's machine and every destination those keys can reach. |

## Verification

- [ ] Applicability is recorded: spawn / credentials / agent-driven egress, or an explicit not-applicable note.
- [ ] The three-question triage table is filled; no cell is left "unknown" without being logged as a finding.
- [ ] Each agent session uses an ephemeral container; mounts are an explicit allowlist; home, SSH, cloud creds, and the Docker socket are unmounted or justified in writing.
- [ ] Landlock (or equivalent FS confinement), seccomp, and a network namespace are configured, or each missing feature is listed as accepted risk.
- [ ] The in-loop software inventory exists and has no unexplained extra parsers or privileged helpers.
- [ ] Agent egress is forced through an out-of-process proxy with static rules, SSRF/RFC-1918 blocks, an audit log, and a human escalation path.
- [ ] The agent environment holds placeholder credentials only; real keys are injected at the broker for policy-approved requests.
- [ ] `/review security` on an agent-running repo engaged this skill; on a repo with no agent surface it recorded the skip.
- [ ] Residual risk is written down (missing kernel features, allowlisted destinations, broker trust).

## Related Skills

- [[agentic-endpoint-hardening]] -- host config-write trust seam; pair with this skill so a confined agent still cannot plant host-executed config.
- [[egress-redaction]] -- agent-applied content policy; this skill's egress proxy is the network boundary that policy cannot replace.
- [[prompt-injection-defense]] -- how a hostile instruction reaches the agent; isolation bounds the cost when it does.
- [[containerization]] -- general image and Compose practice; this skill adds per-session agent isolation and kernel filters on top.
- [[ai-agent-governance]] -- deployed service lifecycle and RBAC; use it for fleet governance, this skill for execution isolation.
- [[authentication-patterns]] -- application auth protocols; this skill only places keys outside the agent process.
- [[security-framework-mapping]] -- verifies the ATT&CK / D3FEND / CSF identifiers declared in frontmatter; see [references/standards.md](references/standards.md).

---

**Version**: 1.0.0
**Last Updated**: August 2026
**Based on**: OS-level agent confinement, ephemeral per-session containers, credential brokering, and out-of-process egress-boundary patterns (generic; no product names in this body)
