# Signed execution-contract study

**Status**: design only. No runtime, no hook, no CLI.
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md`](../plans/v3.19.2-rtk-and-meterless.md) Phase 5 / B6
**# DEVIATION**: the plan text still cites `docs/v3/v3.18/design/`. This file lives under the active minor `docs/v3/v3.19/design/` so it ships with v3.19.2 and is not archived with v3.18.

## Question

Meterless Scout Intent describes a signed execution contract: a capability-scoped, TTL-bounded, immutable authorization object that an executor accepts, with out-of-scope calls refused and logged. Could that become a future framing for Nexus-Hub's PreToolUse rewrite / permission path?

## What we already have

`nexus_context_compressor.rewrite.decide` is a single 0/1/2/3 decision (allow / passthrough / deny / ask). Host `permissions.deny` beats `ask` beats `allow`. Compound commands allow only when every segment matches allow. The default for a proposed rewrite is ask, never auto-allow. Thin `catalog/hooks/rewrite-command.{sh,ps1}` delegates map those exits onto a PreToolUse `permissionDecision`.

That is already a local authorization conversation between the host agent and a deterministic policy. It is not signed, not TTL-bounded, and not capability-scoped beyond prefix rules in the host settings file.

## Fit against a local agent

Nexus-Hub runs on one machine, for one user, with no executor fleet and no third-party attestation service. A cryptographic signature on a contract would need a key, a verifier, rotation, and a story for lost keys. None of that exists today, and introducing it would not block a call the host settings file cannot already deny.

The useful part of the Scout Intent model is the *discipline*, not the crypto:

- Name the capability (for example `git-read`, `pytest`, `network-deny`) instead of an open-ended shell string.
- Bound it in time so a one-session grant cannot linger.
- Treat the grant as immutable: change means a new grant, not an edit in place.
- Log refusals.

Those can be conventions on top of the existing 0/1/2/3 protocol. They do not require a signature.

## Risks if adopted as crypto

- Key material in `~/.nexus-hub/` becomes a new secret-scan and backup surface.
- TTL clocks disagree across OS sleep, WSL, and CI images.
- A signed allow that is broader than the live host deny list would violate the Phase 4 invariant (rewrite must never be more permissive than the host).
- Cross-agent portability (Claude / Cursor / Codex) has no shared verifier.

## Recommendation

**Defer.** Keep the Phase 4 protocol as the authorization object. If a later version wants Scout Intent discipline, adopt it as an unsigned convention (capability id + expiry + append-only grant log) layered on `decide`, still subordinated to host deny. Do not add signatures until Nexus-Hub has a real multi-executor or remote-runner problem.

Drop is the wrong call: the capability/TTL framing is worth keeping on the known-gaps shelf. Adopt-as-runtime is the wrong call for v3.19.2.
