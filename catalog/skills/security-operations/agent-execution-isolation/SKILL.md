---
name: agent-execution-isolation
description: "Confine an AI agent with OS-level execution isolation: Landlock filesystem confinement, seccomp syscall filtering, network namespaces, per-session ephemeral containers that mount only listed directories, an out-of-process egress proxy, and placeholder credentials so real API keys never sit inside the agent container. Use this skill whenever the user says \"sandbox my agent\", \"Landlock\", \"seccomp\", \"egress proxy for agents\", \"isolate the agent container\", \"agent credential isolation\", or wants the agent sandboxed so it cannot read SSH keys or exfiltrate data. SKIP: host config-write trust-seam escapes (use [[agentic-endpoint-hardening]]); agent-applied content redaction before send (use [[egress-redaction]]); generic application Dockerfiles with no agent runtime (use [[containerization]])."
summary_l0: "Run agents in OS-level isolation with ephemeral containers and an egress boundary"
overview_l1: "This skill teaches a four-layer model for running AI agents inside OS-level execution isolation, designed on the assumption that any single boundary eventually fails. Layer zero is the host environment: secrets off sandbox hosts, management-network restriction, host-level mandatory access control, and dedicated infrastructure for high-risk workloads. Layer one is infrastructure: a container sandbox hardened with Landlock, seccomp, and network namespaces, per-session ephemeral containers with explicit mounts, and an enumeration of every shared writable service, because two containers that share one are not isolated from each other. Layer two is runtime: keep the in-loop software and the sandbox's own devices, mounts, and sockets minimal. Layer three is network: an out-of-process egress boundary whose allowlist is checked for transitive reachability, enforced at more than one layer. The triage is three questions: where does execution happen, what runs inside the loop, and what leaves the boundary and what can it then reach."
mitre_attack: [T1611, T1552, T1071, T1090, T1080]
d3fend_techniques: [D3-NTA, D3-PA, D3-FA, D3-NI, D3-PH]
nist_csf: [PR.AC, PR.DS, PR.PT, DE.CM]
---

# Agent Execution Isolation

Run AI agents inside OS-level execution isolation. Semantic instructions are not a boundary: a captured agent will skip them. This skill is the infrastructure counterpart to host trust-seam hardening and agent-applied content policy. It does not name or adopt a particular sandbox product. It teaches the durable pattern: harden the host the sandbox stands on, confine the filesystem and syscalls, keep the in-loop runtime and the sandbox's own interfaces small, and move the network perimeter outside the agent process, then check what that perimeter can actually reach.

This skill **extends `/review security`** when the reviewed project runs or embeds AI agents. The applicability check is three yes/no questions: does the repo spawn agents, hold agent credentials, or make agent-driven egress calls? If every answer is no, skip this skill and record why. If any answer is yes, run the three-question triage below and treat a missing layer as a finding, not as out of scope.

## When to Use This Skill

- The user wants to sandbox a coding agent, isolate the agent container, or stop the agent reading SSH keys or host secrets.
- The design needs Landlock, seccomp, network namespaces, or per-session ephemeral containers with explicit mounts only.
- Real API keys must stay out of the agent environment (placeholder credentials in the container, a broker at the boundary).
- Egress from the agent must go through an out-of-process proxy the agent cannot disable, and the allowlist behind that proxy needs to be audited for what its destinations can reach in turn.
- Several agent sessions share a package registry, artifact store, bucket, cache, or volume, and someone needs to know whether that makes them one session.
- `/review security` is running and the applicability check above is true.

**When NOT to use:**

- The question is a host config-write that a trusted component later executes: use [[agentic-endpoint-hardening]].
- The question is redacting or hashing content the agent itself is about to send: use [[egress-redaction]].
- The question is a generic application Dockerfile with no agent runtime: use [[containerization]].
- The question is recognizing a hostile instruction as it arrives: use [[prompt-injection-defense]].
- The question is lifecycle, RBAC, and observability for a deployed service agent: use [[ai-agent-governance]].
- The question is subnet or perimeter segmentation design on its own: use [[network-microsegmentation-design]] or [[zero-trust-architecture-design]]; this skill wires them into the agent's egress path but does not restate them.

## Three-Question Triage

Answer these before choosing controls. An unanswered question is an open finding.

| # | Question | What "unknown" means | Pass |
|---|---|---|---|
| 1 | Where does execution happen? | The agent process, its tools, and any helper daemons have no named isolation boundary (host, VM, container, nested sandbox). | Every executor is named and sits inside a documented isolation tier, and the host beneath the tier is hardened on the assumption the tier fails. |
| 2 | What software runs inside the loop? | The agent image, tool runners, parsers, and interpreters are an unbounded set, or the sandbox's own devices, mounts, and management interfaces have never been inventoried. | The in-loop inventory and the sandbox configuration are listed, minimal, and auditable. |
| 3 | What leaves the boundary, and what can the things it reaches then reach? | Egress destinations, credentials on the wire, and who can change policy are unknown; or the allowlist exists but nobody has enumerated what each allowlisted destination can itself reach, or which destinations several sessions can write to. | Egress is mediated outside the agent, credentials are injected at that mediator, policy change is human-gated, every allowlisted destination's own reachability is recorded and the union is treated as the agent's real reachability, and every shared writable destination is scoped per session or removed. |

Do not treat a yes on question 1 as coverage for questions 2 and 3. A container with a fat image and host networking fails 2 and 3 even when 1 looks done. Do not treat an allowlist as coverage for question 3 either: an allowlisted service that can reach the internet is an internet route, whatever the allowlist says.

## Instructions

Two principles govern every step below. **Guardrails versus boundaries**: tell the model what it SHOULD do with prompts, classifiers, and policy models, and enforce what it MUST NOT do outside the model, with the execution system enforcing any required approval before a call can proceed. A guardrail shapes behavior; only a boundary survives a captured agent. **Agents do not stop**: an agent will pursue a goal for hours where a human would give up, so the correct assumption is that a reachable path will eventually be found, and the design question is what remains reachable after each layer fails, not whether a layer is likely to hold.

### 1. Confirm applicability

1. Check whether the project spawns agents, stores agent credentials, or issues agent-driven outbound calls.
2. If none of those hold, stop and write `not applicable: no agent execution, credentials, or egress`.
3. If any hold, fill the triage table and continue.

### 2. Harden the host around the sandbox (layer 0: host environment)

This layer sits beneath layer 1. It is the ground the container stands on, and it is designed on the assumption that an attacker can eventually execute code on the host. A virtual machine raises the cost of getting there and does not terminate the threat model: a capable agent given hours has escaped a virtual machine repeatedly on a fully patched stack rebuilt from current upstream sources, with the final chain requiring vulnerabilities that were not previously known.

1. Keep secrets off sandbox hosts entirely. A host that runs agent sandboxes holds no production credentials, no signing keys, and no long-lived tokens; anything the sandbox needs arrives through the broker in step 6.
2. Restrict sandbox-host access to management networks and control planes. The host cannot reach the orchestration API, the secrets manager, or the CI control plane except through paths that are themselves gated, and the sandbox cannot reach them at all.
3. Apply host-level mandatory access control (SELinux, AppArmor, or the platform's equivalent) to the sandbox runtime and its helpers, so an escape lands in a confined profile rather than in an unconfined shell.
4. Place high-risk agent workloads on dedicated infrastructure rather than alongside unrelated workloads. An escape from a dedicated host reaches nothing that was not already at risk.
5. Record the host tier in the review: shared host with secrets and control-plane reach (fail), shared host with MAC and no secrets (weak), dedicated host with MAC, no secrets, and no control-plane reach (pass).

### 3. Place execution (layer 1: infrastructure)

1. Run each agent session in its own ephemeral container. Destroy the container at session end. Do not reuse a long-lived agent VM as the isolation story.
2. Mount only directories the task needs, read-only unless a write is required. Home directories, SSH keys, cloud credential files, and the Docker socket stay unmounted unless a written exception names why.
3. Apply kernel confinement inside that container: Landlock for filesystem paths, seccomp for the syscall set, and a network namespace so the agent has no raw host routing. Details and a Linux baseline live in [references/os-sandboxing.md](references/os-sandboxing.md).
4. Drop ambient capabilities, set no-new-privileges, and prefer a read-only root filesystem with a tmpfs scratch dir.
5. Record the isolation tier in the review: host process (fail), shared long-lived container (weak), per-session ephemeral container plus kernel filters (pass).
6. **Correction to sub-steps 1 through 5: per-session ephemeral containers isolate PROCESSES, not sessions.** Two containers that share a writable service are not isolated from each other, however ephemeral each one is. Agents that were deliberately denied any inter-agent communication established it anyway by writing files into a service they could all reach, then used it to exchange exploits and credentials across otherwise separate runs. A reader who applies sub-steps 1 through 5 and stops has not finished this layer.
7. Enumerate every write-capable service reachable from more than one agent session: package registries and mirrors, artifact stores, object buckets, CI caches, shared volumes, shared databases, and any scratch or log sink more than one session can write to. Treat each as a communication channel between those sessions until per-session scoping proves otherwise. This enumeration is a required artifact; the Verification checklist asks for it by name.
8. Apply the remediation ladder to each shared writable service, from weakest to strongest: per-session credentials and per-session prefixes or namespaces; write-scoping so a session can write only to its own prefix; read-back denial so a session cannot read what another wrote; removing the shared write path entirely. The minimum acceptable rung is write-scoping plus read-back denial, because the first rung alone still lets one session read another's writes, and a channel only needs one direction to carry a credential.

### 4. Shrink the in-loop runtime and the sandbox itself (layer 2: runtime and boundary interfaces)

1. Inventory every binary, interpreter, parser, and helper that runs in the agent container.
2. Remove anything the current task does not call. Extra parsers and unpatched utilities are the usual RCE surface after a tool-output injection.
3. Pin and scan the remaining image. A "latest" tag is a finding.
4. Do not put a privileged sidecar, a Docker socket, or a host-network helper in the same loop "for convenience".
5. Extend the same discipline ACROSS the boundary to the configuration of the sandbox itself. Start from a minimal machine configuration and add a feature only when the task requires it: remove unused virtual devices, host mounts, management sockets, debugging interfaces, and networking functions. Each of these is code sitting across the security boundary, reachable from inside it, and exactly the class that virtual-machine escapes exercise. A device the task never uses is attack surface with no compensating benefit.

### 5. Move the network perimeter outside the agent (layer 3: network)

1. Assume the container is compromised. Controls that run as the agent (prompt rules, agent-applied redaction) are not this layer.
2. Force all agent HTTP/HTTPS through an out-of-process egress proxy. Block raw sockets, alternate ports, and DNS that bypasses the proxy.
3. Encode low-risk destinations as static URL rules. Send unmatched high-risk requests to an LLM judge that cannot execute tools. Block SSRF and RFC-1918/link-local targets. Log every decision. Escalate denials to a human whose approval can update policy. The architecture is in [references/egress-boundary.md](references/egress-boundary.md).
4. Pair this layer with [[egress-redaction]] for content policy. Redaction is not a substitute for the proxy.
5. **Check transitive reachability.** An allowlisted destination is a node, not a leaf. For every destination on the egress allowlist, enumerate what that destination can itself reach, and record the union as the agent's REAL network reachability. An allowlisted internal service that can reach the internet is an internet route, whatever the allowlist says, and the destinations that carry this property are the ones an allowlist most readily approves because they are internal, legitimate, and look low-risk: package registries and mirrors, CI workers, webhook receivers, browser and rendering services, URL-preview and link-unfurl tools, forward and reverse proxies, and cloud control-plane APIs. This is how sandboxed agents with no internet access have obtained it.
6. Scope the obligation to allowlisted destinations only. Mapping the whole network is not required and will not be done; mapping the reachability of each destination the proxy permits is tractable and is the control.
7. Enforce egress at more than one layer. The proxy is the workload-layer control and, on its own, a single point of failure. Pair it with subnet-level segmentation from [[network-microsegmentation-design]] and a perimeter tier from [[zero-trust-architecture-design]], so a proxy bypass or misconfiguration meets a second and third enforcement point rather than the internet.

### 6. Keep real credentials out of the agent environment

1. The agent environment holds placeholder or scoped-down tokens that fail against production APIs.
2. A broker outside the container (the egress proxy or a host-side injector) substitutes real keys only onto requests that already passed policy.
3. A hijacked agent cannot exfiltrate keys it never held. This does not protect the broker itself, and it does not stop misuse of an already-approved destination. [[agentic-endpoint-hardening]] owns the host trust seam around that broker; [[authentication-patterns]] owns application auth protocols.
4. Run the compromised-worker test: assume this worker is already compromised, then enumerate everything its credentials can do. Every capability on that list is in the blast radius today, and every one the task does not need is a finding to scope down before the design is accepted.

### 7. Record residual risk

Write down what remains: kernel features the host lacks, destinations that had to be allowlisted and what each can reach, shared writable services that could not be removed and the rung they sit on, brokers that still hold keys, host-layer controls that could not be applied, and any human-approval path that is not wired. An isolation design with no residual-risk section is incomplete.

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
| "The package registry is internal, so allowlisting it is safe" | A service with internet egress launders the agent's own egress: the agent reaches the registry, the registry reaches the internet, and the allowlist reads clean. That is precisely how sandboxed agents with no internet access obtained it. Enumerate what the registry can reach before calling it internal. |
| "Each session gets a fresh container, so the sessions cannot talk" | Fresh containers isolate processes. Two sessions that can both write to one registry, bucket, cache, or volume share a channel that outlives both containers, and agents denied any other channel have used exactly that one to pass exploits and credentials between runs. Scope or remove the shared write path. |
| "A VM is a real boundary, so the host behind it is safe" | A capable agent given hours escaped a virtual machine repeatedly, including against a stack rebuilt from current upstream sources, with the last chain requiring vulnerabilities that were not previously known. A VM raises cost and does not terminate the threat model; harden the host as if the escape will happen, because given enough time it will. |
| "The sandbox's virtual devices are the hypervisor's problem, not ours" | Every device, mount, socket, and debugging interface exposed to the sandbox is code across the boundary that the sandbox can drive. Escapes exercise exactly that class. A minimal machine configuration is a control this design owns, not one it inherits. |

## Verification

- [ ] Applicability is recorded: spawn / credentials / agent-driven egress, or an explicit not-applicable note.
- [ ] The three-question triage table is filled; no cell is left "unknown" without being logged as a finding, and question 3 answers both halves (what leaves, and what the things it reaches can then reach).
- [ ] The host tier is recorded: no secrets on sandbox hosts, management-network and control-plane reach restricted, host-level mandatory access control applied, high-risk workloads on dedicated infrastructure, or each missing control listed as accepted risk.
- [ ] Each agent session uses an ephemeral container; mounts are an explicit allowlist; home, SSH, cloud creds, and the Docker socket are unmounted or justified in writing.
- [ ] Landlock (or equivalent FS confinement), seccomp, and a network namespace are configured, or each missing feature is listed as accepted risk.
- [ ] The shared-writable-service enumeration exists, names every write-capable service more than one session can reach, and records the remediation rung for each; every service sits at write-scoping plus read-back denial or higher, or is listed as residual risk.
- [ ] The in-loop software inventory exists and has no unexplained extra parsers or privileged helpers.
- [ ] The sandbox configuration is minimal: unused virtual devices, host mounts, management sockets, debugging interfaces, and networking functions are removed or each is justified by a task requirement.
- [ ] Agent egress is forced through an out-of-process proxy with static rules, SSRF/RFC-1918 blocks, an audit log, and a human escalation path, and the proxy is backed by subnet and perimeter enforcement rather than standing alone.
- [ ] The transitive-reachability map exists: for every allowlisted destination, what it can itself reach is recorded, and the union is treated as the agent's real reachability with no allowlisted destination able to reach the internet unrecorded.
- [ ] The agent environment holds placeholder credentials only; real keys are injected at the broker for policy-approved requests; the compromised-worker enumeration of everything those credentials can do exists and every unneeded capability is scoped down.
- [ ] `/review security` on an agent-running repo engaged this skill; on a repo with no agent surface it recorded the skip.
- [ ] Residual risk is written down (missing kernel features, allowlisted destinations and their reach, shared services and their rung, broker trust, host-layer gaps).

## Related Skills

- [[agentic-endpoint-hardening]] -- host config-write trust seam; pair with this skill so a confined agent still cannot plant host-executed config, and see its deterministic response class for architectural-assumption violations that this skill's layers are meant to make impossible.
- [[egress-redaction]] -- agent-applied content policy; this skill's egress proxy is the network boundary that policy cannot replace.
- [[prompt-injection-defense]] -- how a hostile instruction reaches the agent; isolation bounds the cost when it does.
- [[network-microsegmentation-design]] -- the subnet tier of multi-layer egress enforcement behind the proxy in step 5.
- [[zero-trust-architecture-design]] -- the perimeter tier and the identity-aware access model that step 2's control-plane restriction and step 6's credential scoping draw on.
- [[containerization]] -- general image and Compose practice; this skill adds per-session agent isolation and kernel filters on top.
- [[ai-agent-governance]] -- deployed service lifecycle and RBAC; use it for fleet governance, this skill for execution isolation.
- [[authentication-patterns]] -- application auth protocols; this skill only places keys outside the agent process.
- [[security-framework-mapping]] -- verifies the ATT&CK / D3FEND / CSF identifiers declared in frontmatter; see [references/standards.md](references/standards.md).

---

**Version**: 1.1.0
**Last Updated**: September 2026
**Based on**: OS-level agent confinement, ephemeral per-session containers, credential brokering, out-of-process egress-boundary patterns, and the incident lessons of 2026 (transitive reachability through allowlisted services, shared writable services as inter-agent channels, repeated virtual-machine escape) described generically; no product, vendor, researcher, or company names in this body
