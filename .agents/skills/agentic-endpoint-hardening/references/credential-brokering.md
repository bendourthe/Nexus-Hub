# Credential Brokering

Keep real API keys and cloud credentials out of the agent process. The agent is assumed compromisable (see the config-write-then-executed seam in the parent skill). Anything it can read, a hijacked session can exfiltrate. The durable pattern is: the agent environment holds only placeholder credentials; a broker outside the trust seam substitutes real keys into egress requests that have already passed policy.

This file is the pattern. The surrounding OS sandbox and the out-of-process egress architecture live in [[agent-execution-isolation]] (`references/os-sandboxing.md`, `references/egress-boundary.md`). Application-level OAuth, JWT, and MFA live in [[authentication-patterns]].

## Placeholder-key wiring

1. Provision the agent with credentials that fail against production APIs: a dedicated `placeholder` token, an empty value the runtime treats as "broker will fill", or a tightly scoped key that can only authenticate to the local broker.
2. Store real keys in a host-side secret store or the broker's own environment. Do not bind-mount `~/.aws`, `~/.ssh`, `.env`, or the process environment of the operator into the agent workspace.
3. Make the placeholder obvious in logs and traces (`AGENT_PLACEHOLDER_*`) so a leak is identifiable and useless.
4. Probe: `env` and common credential paths inside the agent environment must not contain live production secrets.

A "read-only copy of prod keys" is not a placeholder. If the value works on the real endpoint, it is a live key.

## Broker placement

Two workable shapes. Pick one and name it; mixing them without a single policy engine duplicates allow decisions.

| Shape | Where it runs | How substitution happens | Fit |
|---|---|---|---|
| L7 proxy | Separate process or container on the host; the agent's only default route | After static/judge/SSRF policy allows the request, the proxy attaches `Authorization` (or equivalent) and forwards | Default for HTTP/HTTPS tool use |
| Host wrapper | Host-side helper that the agent calls through a narrow local API | The wrapper performs the upstream call with real keys and returns the response body | Fit for non-HTTP tools (CLI cloud SDKs) that cannot be pointed at a proxy |

Rules that apply to both:

- The broker does not load configuration from an agent-writable path (that is this skill's trust seam applied to the broker).
- The broker does not run as the agent user.
- Substitution happens only after destination policy passes. A denied request never sees a real key, even in memory of the agent.

## Approval flow for new endpoints

1. Unknown destinations are denied or escalated, never silently allowed.
2. A human approval adds a static rule (or a time-bounded one-time allow) in the broker's config store.
3. Until that rule exists, the agent cannot reach the endpoint with a working credential, because it never held one.
4. Record who approved, which host/path, and the expiry. A standing allow with no owner is a finding.

This is network-policy approval, not an IDE "run this command" prompt. Do not treat those as equivalent.

## What this does not protect

- **The broker itself.** If the proxy or wrapper is writable by the agent, or runs in the same sandbox, the pattern collapses. Harden that seam with the parent skill's nine layers.
- **Approved-destination misuse.** A captured agent can still call every destination already on the allowlist, with real keys attached by the broker. Limit scopes on the upstream keys, and keep the allowlist short.
- **Non-egress secrets.** Signing keys used only inside the sandbox (if any) are still in the blast radius. Prefer none.
- **Host-executed config.** Placeholder keys do not stop a config-write-then-executed escape. That remains this skill's core taxonomy.

## Verification

- [ ] Agent environment contains no production API keys, cloud creds, or SSH private keys (checked by listing env and well-known credential paths).
- [ ] A request to a non-allowlisted host is denied or escalated and never receives a real `Authorization` header.
- [ ] A request to an allowlisted host succeeds with a key that is absent from the agent environment.
- [ ] Broker config is not on an agent-writable path.
- [ ] Residual risk (broker compromise, allowlisted misuse) is written down.
