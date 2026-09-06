---
name: agentic-endpoint-hardening
description: "Harden a local coding agent's endpoint against the config-write-then-executed escape pattern: enumerate every file the agent can write, name the trusted component that later executes each one, and apply nine layered controls across that trust seam. Make sure to use this skill whenever the user mentions \"agent sandbox escape\", \"config-write-then-executed\", \"trust seam\", \"harden the coding agent endpoint\", \"which files the agent writes get trusted\", \"can the agent escape its sandbox\", \"the agent wrote a hook config\", hooksPath or fsmonitor abuse, a privileged daemon socket reachable from the agent, or a safe-command allowlist that a dangerous argument slipped past, even when they only describe the symptom (something executed that the agent never directly ran). SKIP, do NOT use for: governing a deployed autonomous service agent's lifecycle, RBAC, or observability (use [[ai-agent-governance]]); writing the access-control policy itself once the seam is known (use [[agent-access-policy]]); recognizing a hostile instruction as it reaches the agent (use [[prompt-injection-defense]]); or adjudicating scanner findings on an imported skill bundle (use [[skill-security-scan]])."
summary_l0: "Harden the coding-agent endpoint against config-write-then-executed sandbox escapes at the trust seam"
overview_l1: "This skill models and hardens the trust seam where a local coding agent's file writes become some other component's execution. The threat is rarely a direct sandbox break. It is a three-step pattern: the agent writes a workspace file that is legal and in scope, a trusted component outside the sandbox later reads that file as its own configuration, and that component executes it at host privilege once the agent is no longer being watched. The skill enumerates the canonical execution-trigger surfaces (agent-harness settings and hooks, editor task and launch files, version-control hook paths and filesystem-monitor commands, interpreter and virtual-environment paths), names the executor and trigger behind each, and applies nine layered controls running from deny-by-default through provenance and seam monitoring. It supplies a seven-question audit checklist for evaluating any agent platform, and it states plainly that a pattern denylist is defense-in-depth rather than a boundary."
mitre_attack: [T1546, T1059, T1611]
d3fend_techniques: [D3-FA, D3-FH, D3-PA, D3-CR, D3-PT]
nist_csf: [PR.PS, DE.CM]
---

# Agentic Endpoint Hardening

Harden the endpoint a local coding agent runs on by treating the agent's write surface, not the agent process, as the blast radius. The escapes that matter in practice are not direct sandbox breaks. They are writes the sandbox correctly permits, which a trusted component outside the sandbox later loads and executes at its own privilege. This skill maps that seam, enumerates the paths that cross it, and applies layered controls with an honest account of which layers are enforceable and which are only guidance.

The taxonomy and controls below are generalized from publicly disclosed advisories affecting several mainstream coding-agent and editor platforms during 2025 and 2026. Advisory identifiers, framework mappings, and source attribution are recorded in [references/standards.md](references/standards.md) rather than here, so this body stays about the durable pattern instead of a particular product version.

## When to Use This Skill

- You are threat-modeling a local coding agent and need to know what its file-write capability actually grants.
- You need to enumerate which agent-writable files a trusted component outside the sandbox will later execute.
- Something executed on the host that the agent never directly ran, and you need to find the seam it crossed.
- You are reviewing whether a command-approval layer keys on command names (bypassable) or on invocation effects (sound).
- You are deciding whether a privileged local daemon reachable from the agent should be denied or justified.
- You are writing or reviewing a guardrail over agent-writable configuration and need to state its limits accurately.
- You are evaluating an agent platform and need a concrete audit checklist to put to its vendor.
- You are designing provenance or seam monitoring so an agent write that is later executed leaves a record.

**When NOT to use:**

- Governing a deployed autonomous service agent (lifecycle, credential RBAC, tool-call allowlists, production observability): use [[ai-agent-governance]], which addresses a running service rather than a local endpoint's filesystem seam.
- Writing the access-control policy once you already know the seam: use [[agent-access-policy]], which owns the deny-by-default scoping, tool allowlists, and approval gates this threat model feeds.
- Recognizing or resisting a hostile instruction as it arrives: use [[prompt-injection-defense]], which owns instruction-origin discipline. This skill assumes the agent may already be misdirected and bounds what that costs.
- Adjudicating scanner findings on an imported skill bundle: use [[skill-security-scan]].
- Deciding what may leave the machine at the content layer: use [[egress-redaction]]. This skill covers a local handoff, not an outbound one.
- Confining the agent process with OS-level sandboxing, ephemeral containers, or an out-of-process egress proxy: use [[agent-execution-isolation]]. This skill hardens the host trust seam around that sandbox; it does not replace it.

## The Config-Write-Then-Executed Pattern

Every form in the taxonomy below is the same three-step sequence. Understanding why each step looks legitimate in isolation is the whole point, because that is why the pattern survives review.

1. **Write.** The agent creates or modifies a file inside the workspace. This is in scope, permitted, and often indistinguishable from the task it was asked to do.
2. **Trust.** A component outside the agent's sandbox reads that file and treats it as configuration or code that the component itself owns. The component has no notion that an agent authored it.
3. **Execute.** The component runs the named command at its own privilege, on its own trigger, at a time the agent no longer controls and nothing is watching.

The structural reason this is hard to catch: the write is inside the policy boundary and the execution is outside it, so neither side observes a violation. The sandbox sees a legal file write. The executor sees its own configuration file. Nobody instruments the handoff between them. That handoff is what this skill calls the trust seam.

Two consequences follow, and both should be stated to stakeholders directly:

- **The blast radius is not the agent process.** It is the union of everything the agent can write and every privilege held by the components that later read those writes.
- **Time-of-write and time-of-execution are decoupled.** A write reviewed and approved today can execute on the next editor launch, the next commit, or the next environment probe. Approval at write time is not approval of the execution.

## Escape Taxonomy

One pattern, six recurring forms. The final column is the reason each form passes inspection, which is the part worth internalizing.

| Form | What the agent writes | What executes it | Why it slips through |
|---|---|---|---|
| Harness hook configuration | A hook or command entry in the agent harness's own settings file | The harness itself, running outside the agent sandbox | Loading its own configuration file is the harness behaving normally; the file format is designed to name commands |
| Editor task or launch configuration | A build, test, or debug task definition in the editor's workspace config | The editor, on user action or on folder open | The editor treats workspace task files as recorded user intent, not as untrusted input |
| Interpreter or shim substitution | The interpreter binary, shim, or environment marker that a language extension auto-discovers | The editor's language extension during environment discovery | Discovery runs unprompted and unsandboxed, and it commonly executes what it finds to query a version or capability |
| Version-control metadata indirection | A repository-local hook directory or filesystem-monitor command in version-control config | The version-control tool, or an editor extension invoking it, on ordinary operations | The executed path is not the conventional hook directory, so guards that watch only that directory never see it |
| Safe-name argument smuggling | Dangerous arguments passed to a command whose name is on the approved list | The approval layer itself, which approved on the name alone | Policy keyed on the first token never inspects the arguments that decide the effect |
| Privileged local daemon | A request to a privileged daemon socket the sandbox can still reach | The daemon, at host privilege, on request | The daemon is a separate trust domain that the sandbox boundary was never drawn around |

Note the pattern in the last two rows: they are not file writes at all. The safe-name form abuses the approval layer, and the daemon form abuses a reachable trust domain. They belong in the taxonomy because they share the defining property (the agent causes execution it never performed) and because a control set that covers only file writes leaves both open.

## Canonical Execution-Trigger Surfaces

This section is normative. It is the single source of truth for which surfaces are treated as execution-triggering, and the repository's own guardrails consume it directly: the sensitive-path advisory (`escalation-trigger`) matches groups A and C, the command guardrail (`git-guardrails`) matches group B, and the opt-in strict permission stub derives its deny and ask entries from all three. A change here must propagate to those consumers, or they drift into a denylist that reads as coverage while missing the current surface.

The split by group is not cosmetic. Each group is matched against a different input, so a control that covers one cannot cover another.

### Group A: file paths (matched against a write or edit target)

| Path pattern | Executor | Trigger |
|---|---|---|
| `.claude/settings.json`, `.claude/settings.local.json`, `.claude/settings*.json` | The agent harness | Session start, and configuration reload |
| `.claude/hooks/*` | The agent harness | The registered tool or session event |
| `.vscode/tasks.json` | The editor | Task run, and any configured automatic or folder-open task |
| `.vscode/launch.json` | The editor, and its debug adapter | Debug or run action |
| `.git/hooks/*` | The version-control tool | Commit, merge, checkout, push, and other hooked operations |
| `.git/config` | The version-control tool | Any operation that reads the hook path or filesystem-monitor setting written into it |
| `.cursor/*` | The editor, and its agent surface | Editor or agent startup, and rule or command evaluation |

### Group B: command-string patterns (matched against a shell command)

| Command pattern | Executor | Trigger |
|---|---|---|
| `git -c core.hooksPath=` | The version-control tool | Immediately, for that invocation, redirecting hooks to an agent-chosen directory |
| `git -c core.fsmonitor=` | The version-control tool | Immediately, executing the named command as a filesystem monitor |
| `git config core.hooksPath`, `git config core.fsmonitor` | The version-control tool | Persistently, on every later operation, because the value is written to config |

Group B exists because these two settings are reachable two different ways: written into `.git/config` as a file (caught by group A) or passed inline per invocation (caught only here). A control that watches the file and not the command string misses the inline form entirely, and vice versa.

### Group C: interpreter and environment paths (matched against a write or edit target)

| Path pattern | Executor | Trigger |
|---|---|---|
| `.venv/bin/*`, `.venv/Scripts/*`, `venv/bin/*`, `venv/Scripts/*` | The editor's language extension, and any tooling resolving the environment | Environment discovery, version probe, and interpreter selection |
| `pyvenv.cfg` | The editor's language extension | Environment discovery, because it decides which interpreter is used |

### Project extension candidates (verify, do not assume)

The three groups above are the normative minimum. The following commonly exist and are execution-triggering, but they vary by project and are deliberately outside the normative list so that adding one is a conscious decision rather than silent scope drift. Check each against your project and promote the ones that apply.

- `.vscode/settings.json`, which can set an interpreter path or terminal profile and therefore decide what runs.
- `.devcontainer/*`, which decides what builds and runs on container attach.
- `.idea/*` and equivalent editor directories carrying run configurations.
- Any project-local script directory that a build tool, task runner, or package manifest resolves by convention.
- Any package-manifest lifecycle script field, which executes on install in most ecosystems.

## Instructions

### 1. Enumerate what the agent can write

1. Read the effective permission configuration and list every path glob the agent may write or edit. Include the paths the project's own tooling and installers write, because a legitimate writer and a hostile one produce the same file.
2. Do not stop at the source tree. Configuration directories, version-control metadata, environment directories, and editor directories are the surfaces that matter, and they are frequently omitted from a write-scope review that thinks in terms of application code.
3. Record the list. If the write scope cannot be enumerated, that is the first finding: an unbounded write scope makes every later step unanswerable.

### 2. Name the executor behind each writable path

1. For each writable path, name the specific component that reads it, the privilege it holds, and the event that triggers it. Use the three-column shape from the normative tables above.
2. Any path left with an unknown executor is an open finding, not a low risk. The whole pattern depends on an executor nobody was tracking.
3. Flag every executor that runs outside the agent's sandbox. Those are the seam crossings; the rest are contained.

### 3. Build the project's execution-trigger surface list

1. Start from the three normative groups. Keep the group split, because each group is matched against a different input by a different control.
2. Add the project extension candidates that apply, and record why each was promoted.
3. Publish the list in one place and make every control reference it, rather than copying patterns into each guardrail. A duplicated denylist drifts, and a drifted denylist is worse than none because it reports coverage it no longer has.

### 4. Enumerate reachable privileged daemons

1. List every local daemon or socket reachable from inside the agent's execution context: container and build daemons, package-manager and service-manager sockets, virtualization and orchestration endpoints, and any local service that performs work at elevated privilege on request.
2. For each, decide deny or justify in writing. A daemon that runs work at host privilege on request is a full escape path, so an undocumented one is an unowned risk.
3. Prefer denying the socket over trusting the requests sent to it, because request-level filtering has to anticipate every API the daemon exposes.

### 5. Test the command policy for name-only approval

1. Take one command that the approval layer permits by name and construct an invocation of it whose arguments produce a dangerous effect. The version-control hook-path redirection in group B is a ready example.
2. Submit it and observe. If it is approved, the policy is keyed on names, and every allowlisted name is an execution primitive.
3. Record the result. A policy that passes this test on one command should be re-tested whenever a name is added to the allowlist.

### 6. Apply the nine control layers

Work the layer table in the next section. For each layer, mark it enforced, advisory, or guidance-only for this project, and record the reason. A layer left unclassified will be assumed covered by whoever reads the assessment next.

### 7. Instrument the seam

1. Ensure a write to any surface on the list produces at least an advisory signal, and confirm the signal by observing it fire on a test write. An untested advisory is indistinguishable from a missing one.
2. Where feasible, correlate write to execution: record the path and a content hash on write, and flag a later command that executes a recently written path. Record paths and hashes only, never file bodies or secret material, per [[egress-redaction]].
3. Default the signal to advisory rather than blocking on surfaces the project's own tooling legitimately writes, so the guardrail does not block the tooling that installs it. Suppress by writer identity where identity can actually be established, rather than dropping the surface from the list. This advisory default remains the default; sub-steps 4 to 6 add a second, narrow class beside it and replace nothing.
4. **Deterministic response class.** A violation of an ARCHITECTURAL ASSUMPTION, a behavior with no legitimate case whatever, connects to a deterministic response rather than to a human queue. The qualifying test is one question: would any legitimate operation produce this signal? If yes, it stays advisory. If no, it qualifies. Examples that pass the test: a sandbox contacting the cluster control-plane API; a processing worker reading secrets unrelated to its function; a research identity creating public infrastructure. Each is definitionally illegitimate, so waiting for a human adds delay and no judgment.
5. The response options for a qualifying violation are: revoke the credential, isolate the host, terminate the workload. A model-based monitor may identify suspicious intent, but it must connect to one of these deterministic actions rather than to another model's judgment; a chain of two models is still a guardrail, not a boundary.
6. Carry the untested-signal discipline forward and extend it: a signal is untrusted until it has been observed firing on a test event, and an automated stop is untrusted until it has been observed stopping something in a test before it is trusted in production. An unobserved stop is indistinguishable from a missing one, and a stop that fires on a legitimate operation is a self-inflicted outage, which is exactly why the qualifying test is strict. This class is guidance for the project's own control plane; this skill ships no reference implementation and no script capable of terminating a workload.

### 8. Record the residual boundary

Write down what remains uncovered: executors you cannot instrument, daemons you must allow, layers that are guidance-only because they are the platform vendor's architecture rather than yours. This is the deliverable that keeps the assessment honest. An assessment that lists only what it covers will be read as complete.

## The Nine Control Layers

| # | Layer | What it means | Typical enforceability |
|---|---|---|---|
| 1 | Deny by default | Start from no execution and no write, then add only the narrowest globs the task needs. A denylist sandbox cannot keep pace with the surface it must cover. | Enforced, through the permission configuration (opt-in; see the posture split below) |
| 2 | Treat execution-triggering config as sensitive | Every surface in the normative list is classified sensitive, so a write to it is an event rather than a routine edit. | Enforced or advisory, through a write-path guardrail |
| 3 | Approve host-side automation explicitly | When the agent creates or modifies anything that will later run on the host, require a human decision at write time. | Enforced through an approval gate, per [[agent-access-policy]] |
| 4 | Run helpers under the same policy as the agent | A helper process, extension, or subprocess that executes on the agent's behalf should carry the agent's policy, not the host's. | Guidance-only where the helper belongs to the platform vendor |
| 5 | Constrain automatic discovery | Discovery that executes workspace-controlled binaries should not run unsandboxed or unprompted. | Guidance-only where discovery is the platform's own behavior |
| 6 | Model command policy on effects, not names | Policy decisions key on the invocation and its side effects, never on the command name alone. | Enforced where you own the approval layer |
| 7 | Restrict privileged local daemons | Deny reachability to privileged daemons unless a specific need is documented. | Enforced, through command and socket scoping |
| 8 | Preserve provenance | Distinguish user-created, repository-created, and agent-created files, so an agent-authored config is not read as user intent. | Partly enforceable locally; a same-session ledger ships, full provenance does not (see the limits section) |
| 9 | Monitor the trust handoff | Instrument the seam itself, not just the agent process, so a write that is later executed leaves a correlated record. | Partly enforceable locally; same-session correlation ships, cross-executor instrumentation does not (see the limits section) |

### What this catalog actually ships for these layers

Naming the concrete controls keeps the table honest, and shows which layers are enforced here versus left to the reader's own project.

- **Layer 2, advisory** (`escalation-trigger`): warns on a write to any group A or C surface. Default action is `warn`, never `block`, so first-party tooling is never self-blocked.
- **Layer 6, blocking** (`git-guardrails`): blocks the group B command patterns, including the interleaved-option form a glob cannot express.
- **Layer 1, opt-in** (the strict permission overlay): `deny` and `ask` entries for the same surfaces, installed only with `--strict-permissions` / `-StrictPermissions`.
- **Layers 8 and 9, best-effort** (`provenance-ledger`): records path and content hash on each agent write, then flags a later same-session command that references one of those paths. Paths and hashes only, never file contents.

**The deliberate posture split.** The default install is convenience-first: an allow-only auto-approve list, no prompts. The hardened posture is opt-in behind a flag. That is a decision, not an oversight. A default deny stub would contradict the no-prompt install philosophy and would surprise every existing user on upgrade, so the project ships the guardrails advisory-by-default and the hard enforcement on request. State the split plainly when assessing a project against layer 1: doctrine present and enforceable, enforcement opt-in.

Layers 4 and 5 are marked guidance-only deliberately. Whether a platform's language extension or version-control integration runs sandboxed is that platform's architecture, not something a catalog, a hook, or a permission file can change. The correct action for those two layers is to put them to the vendor as questions (see the checklist below) and to record the answer as an accepted risk, rather than claiming a control that does not exist.

## Privileged Local Daemons

A privileged local daemon is a second trust domain sitting beside the sandbox, and the sandbox boundary was almost certainly not drawn around it. If the agent can reach the socket, it can ask a host-privileged process to do work, which makes the daemon a complete escape path that never touches a file.

Treat the following as the enumeration checklist:

- **Container and virtualization daemons**, which can run a workload with host mounts or host namespaces. This is the cleanest total escape available, because the requested workload is host-privileged by design.
- **Build and compilation daemons**, which execute build logic that the workspace supplies.
- **Package-manager and service-manager sockets**, which install or start units at elevated privilege.
- **Orchestration and remote-management endpoints** reachable on the local network, which extend the blast radius past the machine.

Apply three controls in order. First, deny the command and socket globs unless the task documents a need. Second, when access is genuinely required, scope it to the narrowest operation and prefer an isolated tier over the host, per [[containerization]]. Third, log the request before it is issued, so a misdirected request is visible in the record rather than discovered by its effect. The deny globs and least-privilege scoping belong in the access policy itself, which is [[agent-access-policy]]'s territory; this skill supplies the enumeration and the reason.

## Platform Audit Checklist (Seven Questions)

Put these to any agent platform, whether a vendor's product or your own harness. Each maps to a layer above, and the answers are the assessment. An answer of "we do not know" is a finding.

1. **What can the agent write?** Ask for the effective write scope, including configuration, version-control metadata, and environment directories, not just the source tree.
2. **Which host components trust those writes?** For each writable surface, which process reads it, at what privilege, on what trigger?
3. **Which privileged local daemons can the agent reach?** Enumerated, not assumed absent.
4. **Which commands skip approval?** The exact list, and what qualifies a command for it.
5. **Is command policy keyed on names or on effects?** If on names, every allowlisted name is an execution primitive, and the answer to question 4 becomes the escape list.
6. **Can the system distinguish user-created from agent-created state?** Without provenance, an agent-authored configuration file is read as recorded user intent.
7. **What telemetry fires at the trust handoff?** Not what monitors the agent process, which is the common answer, but what fires when a component executes something the agent wrote.

## Limits and Honest Boundaries

State these plainly wherever the controls are documented, because a control mistaken for a boundary is worse than a documented gap.

- **A pattern denylist is defense-in-depth, not a boundary.** A fixed list of patterns matched against a raw command string only catches the strings someone already thought of. Each disclosed escape in the taxonomy used a path, flag, or setting that no existing list named. Add the known-bad patterns, and document that novel ones will pass.
- **Matching a raw command string is not argument parsing.** A guardrail that regex-matches a command line does not decompose arguments, so quoting, ordering, environment indirection, and equivalent alternate flags can all evade it. This is a real limitation of the group B control, not a hypothetical one.
- **Provenance is partial locally.** A local hook can record that the agent wrote a path, but it cannot retroactively label files created before it was installed, and it cannot force an external executor to consult the provenance record before acting.
- **Seam monitoring cannot cover every executor.** A local hook observes the tool calls of the harness it is installed in. It cannot instrument an editor extension, a language server, or a version-control integration running in another process. Correlating an agent write with a later execution in the same session is achievable; full cross-executor instrumentation is not, and claiming otherwise is the failure mode to avoid.
- **Advisory controls do not stop anything.** A warning that defaults to advisory (the correct default where first-party tooling writes the same paths) informs a reviewer and blocks nothing. Do not count an advisory as a preventive control in a risk register. Only the deterministic response class in step 7 counts as preventive, and only for the narrow set of architectural-assumption violations that pass its qualifying test and have been observed stopping something in a test.
- **This skill hardens, it does not sandbox.** The strongest available answer to an unclosable seam is to move execution into an isolated tier rather than to add another pattern to a list.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The agent is sandboxed, so a file write cannot hurt me" | The write is not the exploit; the later read by an unsandboxed component is. A sandbox that permits writing a harness hook config has already granted everything the hook executor can do, at a time the sandbox is no longer watching. |
| "We added the dangerous patterns to the denylist, so the seam is closed" | A fixed pattern list is satisfied only by the strings someone anticipated. Every disclosed escape in the taxonomy used a path or flag that no list named, which is exactly why the pattern list is defense-in-depth and the surface list is the real control. |
| "It is only config, not code, so it is a low-risk write" | In five of the six forms the payload IS config. A hook entry, a task definition, and a version-control hook path are each configuration that names a command an executor runs at host privilege. The config-versus-code distinction does not survive an executor that treats config as instructions. |
| "The command name is on the approved list" | Approving a name approves every argument that name accepts. A permitted version-control command carrying an agent-chosen hook path executes arbitrary code under an approval that only ever inspected the first token. |
| "Environment discovery is a read, not an execution" | Discovery routinely executes what it discovers, to ask its version or capabilities. An interpreter or shim written moments earlier gets run by that probe, unsandboxed, with no user action at all. |
| "We do not use containers, so a daemon socket is irrelevant" | Container daemons are one instance, not the class. Build daemons, package-manager sockets, and service managers each perform privileged work on request. Enumerate what is actually reachable instead of concluding there is nothing. |
| "Nothing has warned us, so the seam is not being crossed" | Nothing monitors the seam by default; there is typically no hook on the handoff at all. Absence of alerts from uninstrumented ground is absence of instrumentation, not absence of crossings. |
| "Our own installer writes these paths, so warning on them is noise" | The advisory exists precisely because a legitimate writer and a hostile one produce an identical file. Suppress by writer identity where identity can be established, and keep the surface classified, rather than deleting the class to quiet the signal. |
| "Automating a stop is dangerous, so every alert should go to a human" | For surfaces the project's own tooling writes, yes, and that stays the default. For a sandbox calling the cluster control plane or a worker reading secrets it has no function for, there is no legitimate case to protect, so the human in the queue adds latency and nothing else. Apply the qualifying test rather than the blanket rule: if no legitimate operation produces the signal, connect it to a deterministic response and prove the response in a test first. |
| "The platform vendor patched those CVEs, so this is handled" | The specific bypasses were patched; the pattern was not, because the pattern is a consequence of an agent that writes files and a host that trusts them. Assess your own write scope and executors rather than treating a vendor patch as coverage. |

## Verification

- [ ] The agent's effective write scope is enumerated, including configuration, version-control metadata, environment, and editor directories, not only the source tree.
- [ ] Every writable surface has a named executor, privilege, and trigger recorded. No surface is left with an unknown executor.
- [ ] The project's execution-trigger surface list exists in exactly one place, keeps the A/B/C group split, and every guardrail references it rather than carrying its own copy.
- [ ] Every reachable privileged local daemon is enumerated, and each is either denied or justified in writing.
- [ ] The command policy has been tested against at least one name-allowlisted command carrying a dangerous argument, and the observed result is recorded (an approval is a failed test).
- [ ] A test write to a listed surface has been observed producing its advisory signal. The signal was seen firing, not assumed.
- [ ] The default action for each guardrail is recorded, and a legitimate first-party write has been tested to confirm the guardrail does not block the project's own tooling.
- [ ] Every signal wired to a deterministic response passes the qualifying test (no legitimate operation produces it), names its response (revoke, isolate, or terminate), and has been observed stopping a test event; every signal that fails the test stays advisory.
- [ ] All nine control layers are marked enforced, advisory, or guidance-only for this project, with no layer left unclassified.
- [ ] The denylist limitation is documented where the denylist lives, so no reader can mistake it for a boundary.
- [ ] The residual boundary (uninstrumentable executors, allowed daemons, guidance-only layers) is written down as accepted risk rather than omitted.
- [ ] Live production credentials are absent from the agent environment; substitution happens at a broker outside the trust seam ([references/credential-brokering.md](references/credential-brokering.md)).

## Credential Brokering

The agent process is assumed compromisable. Live API keys in its environment are therefore keys a hijacked session can steal. Hold placeholders only inside the agent; a broker outside the trust seam (an L7 proxy or a host wrapper) attaches real keys solely to egress requests that already passed policy. Wiring, placement options, the approval flow for new endpoints, and the limits of the pattern (it does not protect the broker, and it does not stop misuse of already-approved destinations) are in [references/credential-brokering.md](references/credential-brokering.md). Pair with [[agent-execution-isolation]] for the sandbox and egress architecture, and with [[authentication-patterns]] for application auth protocols.

## Related Skills

- [[agent-access-policy]]: owns the deny-by-default write scoping, tool allowlists, approval gates, and privileged-daemon deny globs that this threat model feeds. Read this skill to find the seam, then that one to write the policy.
- [[prompt-injection-defense]]: covers how a hostile instruction reaches the agent in the first place. Provenance discipline lowers the chance of being misdirected; the containment here bounds the cost when it happens.
- [[skill-security-scan]]: adjudicates imported skill bundles, another agent-writable surface that a trusted component later executes.
- [[egress-redaction]]: the redaction discipline any provenance or seam ledger must apply, namely paths and hashes only, never file bodies or secret material.
- [[containerization]]: builds the isolated execution tier that is the correct answer when a seam cannot be closed.
- [[agent-execution-isolation]]: OS-level sandbox, ephemeral per-session containers, and the out-of-process egress boundary this skill's credential-brokering pattern rides on.
- [[authentication-patterns]]: application OAuth/JWT/MFA; this skill isolates agent-held credentials, it does not design those protocols.
- [[ai-agent-governance]]: governs a deployed autonomous service agent's lifecycle, risk, security, and observability. Use it instead of this skill when the subject is a production service rather than a local endpoint.
- [[security-framework-mapping]]: assigns and verifies the framework identifiers declared in this skill's frontmatter.
