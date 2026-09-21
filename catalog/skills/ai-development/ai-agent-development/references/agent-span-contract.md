# Agent Span Contract

The mapping between agent operations and the external GenAI span convention, and the privacy rules that govern what a local trace may contain. Read this cold: it assumes no other part of the agent skill is in context.

This file names fields. It is not an OpenTelemetry implementation, and nothing here emits OTLP. The example script this contract governs writes plain JSONL for local inspection. Calling that output "OTel" would claim conformance nobody has tested.

## Pinned source

| Field | Value |
|---|---|
| Source | OpenTelemetry semantic conventions, GenAI agent spans |
| Pinned revision | `5ca9052bc796ef1e497200b1d558fd87a201f335` |
| Upstream status | **Development** |
| Verified on | 2026-09-15 |

**Development status is the operative fact.** These names can change without a stability guarantee. Pin the revision in anything that depends on them, and treat a version bump as a breaking change until diffed.

**Recheck trigger.** Re-verify this file when any of these occur: the upstream convention leaves Development status; a consumer needs an attribute not listed below; the agent skill starts emitting a span type absent from the table; or twelve months pass since the verified date.

## Operation mapping

Verified against the pinned revision.

| Operation | `gen_ai.operation.name` | Span name | Kind |
|---|---|---|---|
| Create an agent | `create_agent` | `create_agent {gen_ai.agent.name}` | CLIENT |
| Invoke a **remote** agent | `invoke_agent` | `invoke_agent {gen_ai.agent.name}` or `invoke_agent` | **CLIENT** |
| Invoke a **local** agent | `invoke_agent` | `invoke_agent {gen_ai.agent.name}` or `invoke_agent` | **INTERNAL** |
| Invoke a workflow | `invoke_workflow` | `invoke_workflow {gen_ai.workflow.name}` | INTERNAL |
| Plan | `plan` | `plan {gen_ai.agent.name}` or `plan` | INTERNAL |

The CLIENT/INTERNAL split on `invoke_agent` is the distinction most often lost. Same operation name, different kind, decided by whether the call crosses a process boundary to a remote service. Recording a local invocation as CLIENT invents a network hop; recording a remote one as INTERNAL hides a real dependency and its failure domain.

**Emit a `plan` span only when planning boundaries are genuinely observable.** If the integration cannot see where planning started and stopped, there is no plan span. Manufacturing one from a guess produces a trace that describes an architecture nobody implemented.

## Attribute requirement levels

Verified against the pinned revision.

### Required

- All spans: `gen_ai.operation.name`
- `create_agent`: additionally `gen_ai.provider.name`
- `invoke_agent`: additionally `gen_ai.provider.name` (client only)
- `invoke_workflow`, `plan`: `gen_ai.operation.name` only

### Conditionally required (present when applicable)

`error.type`, `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.version`, `gen_ai.agent.description`, `gen_ai.conversation.id`, `gen_ai.request.model`, `gen_ai.request.choice.count`, `gen_ai.request.seed`, `gen_ai.output.type`, `gen_ai.workflow.name`, `server.address`, `server.port`

### Recommended

`gen_ai.request.temperature`, `gen_ai.request.top_p`, `gen_ai.request.max_tokens`, `gen_ai.request.frequency_penalty`, `gen_ai.request.presence_penalty`, `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`

### Opt-In

`gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`

**The Opt-In tier is exactly the payload-bearing tier.** Every attribute in it carries prompt text, model output, system instructions, or tool schemas. That is not a coincidence in the upstream design, and it is the whole basis of the default below: the convention already separates the attributes that describe an operation from the attributes that reproduce its content.

### Tool spans: partially verified

The `execute_tool` operation name is confirmed at the pinned revision. **The `gen_ai.tool.*` attribute table was not retrievable at that revision during verification** - the source document truncates before the section and no standalone tool-span file exists at the pinned path.

Do not name a `gen_ai.tool.*` attribute on the strength of this file. Verify against the sibling inference/tool specification first, then add it here with its requirement level. An unverified attribute is unknown, not Recommended.

## Default privacy contract

**Payload attributes are absent by default.** Not truncated, not hashed, not summarized - absent.

Truncation is not redaction. A 200-character prefix of a system instruction is still a system instruction, and a shortened identifier is still correlatable. A trace that records a payload it shortened has recorded the payload.

| Category | Default | Notes |
|---|---|---|
| Operation, kind, timing, status | recorded | This is what a trace is for |
| Identifiers and parent links | recorded | Opaque values only |
| Token counts, model name | recorded when available | Metadata, not content |
| Prompt and response content | **absent** | `gen_ai.input.messages`, `gen_ai.output.messages` |
| System instructions | **absent** | `gen_ai.system_instructions` |
| Tool arguments, results, definitions | **absent** | Includes `gen_ai.tool.definitions` |
| Raw exception strings | **absent** | Use a bounded error category |

### Errors carry a category, not a string

A raw exception message is uncontrolled text. It routinely contains a file path, a connection string, a row of data, or a token, and none of that was reviewed before it was written to disk.

Record a bounded, allowlisted category instead: `timeout`, `rate_limited`, `invalid_input`, `permission_denied`, `unavailable`, `internal_error`. A category that is not on the list becomes `internal_error`; it does not become the exception text.

`error.type` in the convention holds this category.

### Enabling payloads is a separate, authorized decision

Payload capture has legitimate uses - debugging a specific failure, building an evaluation set. The responsibilities that come with it:

- A human authorizes it explicitly, for a bounded window and a named purpose.
- The output path is treated as containing the most sensitive data the agent touched, because it does.
- Any movement off the host applies the per-category policy in `[[egress-redaction]]`, which owns that decision. This contract does not.
- The capture is turned off again, and the artifact deleted, when the purpose is met.

**The example script this contract governs deliberately ships no payload-enable flag**, and no export path at all. Documenting the responsibility is useful; shipping an untested egress mechanism alongside it is how the responsibility gets skipped.

## Local namespace: `nexus.*`

Concepts the upstream convention does not define get a separate namespace. Presenting a local field as a `gen_ai.*` attribute misrepresents a project convention as an interoperable standard, and the next consumer wires it into a dashboard expecting the standard's meaning.

| Field | Meaning |
|---|---|
| `nexus.iteration` | Loop iteration index, where a bounded loop is running |
| `nexus.budget.*` | Local budget accounting (calls, time, spend) against a declared cap |
| `nexus.evidence.ref` | Stable identifier linking a span to an evidence record |
| `nexus.coverage.*` | What the integration could and could not observe |
| `nexus.synthetic` | True when the record is a demonstration, not a real execution |

`nexus.coverage.*` is the one that prevents a specific misreading, and it is the subject of the next section.

## What a trace does not prove

A trace records what the integration could observe. It is not a transcript of what happened, and it is emphatically not a record of what the model thought.

- **Absence of a span is not absence of an event.** It may mean the operation was not instrumented. Record what was not observable in `nexus.coverage.*` rather than letting a silent gap read as a clean run.
- **Internal reasoning is unavailable.** No span field holds it. Where a model emits a human-readable summary of its reasoning, that summary is model output, not an authenticated record of an internal process. Store it, if at all, as output subject to the payload rules above - never as a `reasoning` field implying privileged access.
- **Self-attestation is not host observation.** "The agent reported it ran the command" and "the host observed the process execute" are different claims with different trust properties. Keep them distinguishable in the record; collapsing them is how an unverified claim acquires the authority of a measurement.
- **A passing answer, a missing alert, and a clean trace are not proof no unsafe action occurred.** Authorization and isolation are enforced outside the trace system. A trace is evidence, not a control.

## Verification

- [ ] Every emitted span uses an operation name from the mapping table, with the CLIENT/INTERNAL kind matching whether the call crossed a process boundary
- [ ] `plan` spans are emitted only where planning boundaries are actually observable
- [ ] No `gen_ai.tool.*` attribute is named without verification against the sibling tool specification
- [ ] No Opt-In payload attribute appears in default output
- [ ] Error records carry an allowlisted category; no raw exception string is written
- [ ] Local concepts use `nexus.*` and are never presented as `gen_ai.*`
- [ ] Unobservable data is omitted or marked unknown in `nexus.coverage.*`, never inferred
- [ ] The output is not described as OTLP or as OpenTelemetry-conformant
- [ ] The pinned revision and its Development status are stated wherever these names are relied on

## Related

- `step-8-instrument-for-observability.md` -- the teaching that applies this contract
- `scripts/trace-example.py` -- the runnable, metadata-only demonstration
- `[[egress-redaction]]` -- owns every decision about data leaving the host
- `[[loop-engineering]]` -- owns loop state, budgets, and evidence freshness
