# Decision: Defer signed execution contracts

Status: implemented - the PreToolUse 0/1/2/3 rewrite decision stays the only authorization object; no cryptographic contract is added until a multi-executor or remote-runner surface exists.

## Problem

The v3.19.2 study (`docs/archives/v3/v3.19/design/signed-execution-contract-study.md`) asked whether a signed, capability-scoped, time-bounded execution contract should become the authorization model for Nexus-Hub's command rewrite and permission path. It recommended deferral, but the recommendation was never ratified, so the question stayed open as a known gap (v3.19.2 DF-4, carried as v4.13 AR-43) and would be re-asked in every minor.

## Decision

Nexus-Hub keeps the existing local protocol as its authorization object: `nexus_context_compressor.rewrite.decide` returns one of allow, passthrough, deny, or ask; the thin `rewrite-command.{sh,ps1}` hooks map that onto a PreToolUse `permissionDecision`; and the host's own `permissions.deny` always wins. No signature, key, verifier, or TTL clock is added.

If capability discipline is wanted later, it is adopted first as an unsigned convention (a named capability id, an expiry, and an append-only grant log) layered on `decide` and still subordinate to host deny.

Reopening trigger: Nexus-Hub gains a real multi-executor or remote-runner surface, where one party grants authority that another party executes. Only then does a signature block something the host settings file cannot already refuse.

## Alternatives considered

**Adopt signed contracts now.** Rejected. A single-user local agent has no second party to verify against, so a signature adds key material to back up and secret-scan, TTL clocks that disagree across sleep, WSL, and CI images, and no shared verifier across Claude, Cursor, and Codex, while blocking nothing host deny cannot.

**Drop the idea entirely.** Rejected. The capability-and-expiry framing is a useful discipline, and dropping it would lose the reasoning a future remote-runner design needs.

**Leave the gap open.** Rejected by the maintainer on 2026-10-10 during v4.13.11 Phase 4: the study already contained the answer, and an open gap with no new evidence only re-litigates it.

## Consequences

- v4.13 AR-43 (origin v3.19.2 DF-4) closes on this record; the study remains the technical reference.
- A future proposal to add signatures must first show the multi-executor or remote-runner surface that justifies it.
- The rewrite path keeps its invariant that it is never more permissive than the host's live deny list.
