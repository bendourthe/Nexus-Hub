# Egress Boundary Runbook

Out-of-process network control for [[agent-execution-isolation]]. This is layer 3. Agent-applied redaction ([[egress-redaction]]) is a different control: it runs as the agent and can be skipped by a captured or injected agent.

## Goal

Assume the agent container is compromised. The perimeter is a mediator the agent cannot disable, restart, or reconfigure.

## Placement

- Run the proxy on the host or in a separate container/network namespace from the agent.
- The agent's only default route is toward the proxy. There is no second path (host network, extra NIC, SOCKS helper the agent starts, DNS tunnel).
- The proxy process does not run as the agent user and does not load agent-writable config from the workspace.

If the proxy config lives in a path the agent can write, this layer collapses into the host trust seam. Pair with [[agentic-endpoint-hardening]].

## Static rules (low-risk traffic)

Encode known-good destinations as static URL rules evaluated before any model:

- Scheme, host, and path prefix (not a regex the agent supplies).
- Method allowlist (GET vs POST) where it matters.
- Deny by default. A missing match is not an allow.

Examples of low-risk: a pinned package registry, a pinned docs host, the operator's own API with a fixed origin.

Static rules must be files the agent cannot write. Reload is a human or CI action.

## LLM judge (unmatched high-risk traffic)

Requests that miss static rules go to a judge:

- The judge sees a structured summary (method, host, path, purpose claimed by the agent), not a raw tool that can fetch arbitrary URLs.
- JSON-encode the payload the judge reads so injected instructions in the URL or body are data, not commands.
- The judge cannot execute tools, cannot reach the network, and cannot update policy.
- Outputs are allow / deny / escalate, plus a one-line reason. Anything else is deny.

The judge is residual risk. It exists so novel destinations are not silently allowed. It is not a reason to skip static rules or SSRF blocks.

## SSRF and private-range blocking

Independent of the judge, the proxy code must refuse:

- RFC-1918, RFC-6598 (CGNAT), loopback, link-local, IPv6 unique-local and link-local.
- Cloud metadata endpoints and well-known instance-metadata hosts.
- DNS that resolves to those ranges after a public name (rebinding): resolve, then enforce on the connected address, not on the requested hostname alone.
- Redirects that hop from an allowed host to a denied address.

These checks are deterministic. Do not delegate them to the LLM judge.

## Audit log

Log every decision: timestamp, session id, rule id or `judge`/`escalate`/`ssrf-block`, method, host, path, outcome. Do not log secrets, bodies, or query values that may contain tokens. Retention is an operator choice; existence of the log is not.

## Human-in-the-loop escalation

When the proxy denies or the judge returns escalate:

1. Notify the operator with the agent's claimed intent and the reconstructed request (redacted).
2. The operator's approval is the only path that adds a static rule or issues a one-time allow.
3. Approval updates policy in the proxy's config store, not in a file the agent owns.
4. Time-bound one-time allows. A standing allow without an expiry is a finding.

This is network-policy escalation. It is not the same as an IDE permission prompt on a local tool.

## Credential injection at the proxy

The agent authenticates to the proxy with a placeholder or session-scoped token that is useless on the public internet. The proxy attaches the real upstream credential after the request passes policy. See the skill body, step 5. Failure modes this does not cover: a compromised proxy, and an allowed destination that the agent is tricked into calling.

## Failure mode: treating content policy as this layer

If the only egress control is "the agent redacts secrets before sending", question 3 of the triage fails. Put this proxy in place, then keep [[egress-redaction]] as defense-in-depth on the content.

## Probes (binary)

- [ ] From the agent namespace, a TCP connect that does not target the proxy fails.
- [ ] A request to an RFC-1918 or metadata address is blocked in proxy code (not by the judge).
- [ ] An unmatched public URL is denied or escalated, never silently allowed.
- [ ] A human approval is required before a new static rule exists, and the rule file is not agent-writable.
- [ ] The audit log contains the denied/escalated request's host and outcome without secret material.
- [ ] Real upstream API keys are absent from the agent environment (`env` inside the container shows placeholders only).
