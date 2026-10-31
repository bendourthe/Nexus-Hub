# Decision: Model-adaptive runtime scope

Status: proposed - apply a predeclared acceptance bar to the v4.15.1 evidence before choosing a runtime direction.

## Problem

Should Nexus-Hub automatically inject model-specific profile text into running sessions? This record fixes the decision rule on 2026-10-31 before the local token-cost experiment. It grants no runtime, hook, schema, telemetry, or provider-call authority.

## Proposal

Consider a runtime only if the acceptance criteria below are satisfied. The alternatives are Claude-only opt-in injection, retaining on-demand authoring guidance, a neutral core with a verified adapter, and deferral until a second independently verified detection-and-context adapter exists. Having a hook runtime alone does not prove model detection or safe context injection.

## Alternatives considered

| Alternative | Cost to assess |
|---|---|
| Claude-only opt-in runtime | Transcript metadata access, per-turn tokens, content filtering, configuration, and maintenance |
| Decline automatic injection | No new runtime cost; users continue selecting authoring references on demand |
| Neutral core with one verified adapter | The same first-adapter costs plus a shared interface whose second consumer is not established |
| Defer for a second verified adapter | No new runtime cost now; future evidence collection and re-evaluation |

## Acceptance criteria

The per-turn injection ceiling is **512 estimated tokens**, using a declared UTF-8-byte estimate of four bytes per token for the local experiment. This is a decision threshold, not a provider-billed token count or a claim about model quality. The budget is recorded before measuring the profile payload.

A build verdict requires all three: a named existing consumer consisting of a specific rule, model profile, and observed misbehavior; a measured payload at or below the ceiling; and measured paired benefit, or an explicit justified decision to ship unevaluated. Absent all three, the verdict is decline. Unknown benefit does not count as benefit. Zero additional provider API spend is authorized, and the experiment must not start nested model sessions.

The evidence must also show that the selected profile text can be treated as untrusted reference data without overriding user instructions, verification requirements, or safety boundaries. No such filter is built in this plan.

## Risks

Vendor-derived profile claims can contain imperative instructions. A schema-valid and cited claim is not automatically authorized runtime instruction. A tail-only metadata resolver can fail to find a model, and observed resolver latency cannot establish hook-to-model latency, model quality, prompt-cache behavior, or benefit. A platform's hook support is separate from model detection and context-delivery support.
