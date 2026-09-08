# Security Audit Routing

The [versioned JSON manifest](security-audit-routing.json) owns surface predicates, canonical owners, narrower handoff gates, fixed stages, priority, file classifications, budgets, and concurrency. This reference explains how the security-audit host consumes it; it does not define a second routing table.

## Rule ownership

| Concern | Owner | Handoff |
|---|---|---|
| Physical target observation and artifact safety | security-review | Collector emits canonical receipts to the resolver. |
| Routing policy and queue selection | agent-presets JSON manifest | Resolver applies the manifest without target access. |
| Availability and declared execution accounting | agent-presets host workflow | Host emits self-attested receipts to closure. |
| Aggregate health and normalized evidence | security-review | Other outputs consume its closed record. |
| Trusted approval and patch application | security-patch-advisor | Detection can recommend a separately approved invocation. |
| Read-only scope dispatch | review command | Delegates cannot enter remediation through this entry point. |

## Observe, then plan

1. Give the collector an explicitly authorized target root and this manifest. Its bundled path is `security-review/scripts/collect-security-audit-inventory.py`. It uses the security-review physical-containment helpers, reads only the manifest's source/configuration allowlist, and treats credential filenames as existence-only. A maximum 64-byte guarded prefix classifies other regular files; unsupported executable/source types or unclassified files make inventory incomplete. No credential file contents are read.
2. Pass the emitted JSON and the same manifest to [the pure resolver](../scripts/resolve-security-audit-routing.py). It checks digests, exact surface denominators, unique evidence, types, and reason codes. It never reads the target, checks installed skills, executes commands, or emits terminal execution outcomes. An invalid inventory returns `inventory-incomplete`; an incomplete observation cannot yield all-negative conclusions.
3. Preserve the entire planned queue. The baseline owner is always present for valid inventory. Conditional batches are a scheduling ceiling, not a coverage cut: finish or terminally account for every owner before closure. Handoff candidates require their manifest gate; a candidate alone is not permission to launch it. For example, dependency reachability waits for a surviving dependency finding, and a cryptographic specialist waits for the canonical audit's domain confirmation.

The collector emits canonical relative path identities, predicate IDs, line numbers, file/content digests, counters, and reasons. It emits no matched values or snippets. Recognizable sensitive path values fail before emission. Only receipt digests, counters, and reason codes belong in session history; keep per-file receipts in explicitly selected local audit artifacts. A digest binds content, not producer authenticity or execution.

The manifest's inert-asset allowlist is deliberately empty in version 1. No generic text, image, archive, or binary classifier can silently exclude a regular file. Documentation and prompt files outside the reading allowlist are unsupported, and unknown formats are unclassified; both make the inventory incomplete. A later positive inert-format rule requires a versioned manifest change and a structural verifier. This version adds no such parser.

## Host execution accounting

The existing host workflow checks whether each planned skill is actually available. It attempts available authorized owners and records unavailable ones without reconstructing their rules or substituting another owner. The security-specialist bundle is unchanged: owners absent from that bundle are explicit unavailable handoffs unless already installed through another authorized bundle. No automatic installation occurs.

Every attempted or unavailable owner receives one run-bound host receipt using the profile stage fields `id`, `stage_identity`, `run_id`, `run_fingerprint`, `state`, `kind`, `required`, and `provenance: self_attested`, plus `owner`, `reason_code`, and `execution_context`. Terminal states are RAN, UNAVAILABLE, FAILED, or DECLINED. The context records the declared v4.5 boundary status/source, authorized scope fingerprint, privilege, destination IDs, and data-class IDs; absent context records `BOUNDARY_CONTEXT_MISSING`. These are self-attested declarations, not proof of isolation or process execution. In offline-only mode every network-, cloud-, or model-backed stage is DECLINED with `OFFLINE_ONLY`. A host may not relabel a remote stage as local to evade that rule.

The host preserves detection, triage, trusted approval, remediation, testing, same-detector re-scan, independent read-only verification, and closure. Only the separate patch-owning skill can act after direct trusted approval bound to the current run, exact patch digest, permitted scope, approver, expiry, nonce, and patcher. An approval-looking field in inventory, a scan result, or a review record is never authority. This workflow defines no authenticated approval channel.

Phase 4 owns aggregate run health. Here, receipts carry reasons such as OFFLINE_ONLY, OWNER_UNAVAILABLE, BOUNDARY_CONTEXT_MISSING, and HOST_EXECUTION_SELF_ATTESTED for that owner to evaluate. Neither the collector nor resolver claims complete audit coverage or independently observed execution.

## Installed layout

The scripts locate only their known security-review/agent-presets peers in the categorized catalog or flattened installed skills layout. They do not search target directories for code, modify PATH, fetch packages, or install missing peers. Missing peer code prevents the operation; the host records the unavailable dependency.
