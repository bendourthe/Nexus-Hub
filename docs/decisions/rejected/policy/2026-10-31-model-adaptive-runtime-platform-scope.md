# Decision: Model-adaptive runtime scope

Status: rejected - decline automatic runtime injection; retain explicit authoring references and on-demand profile reads.

## Problem

Should Nexus-Hub automatically inject model-specific profile text into running sessions? This record fixes the decision rule on 2026-10-31 before the local token-cost experiment. It grants no runtime, hook, schema, telemetry, or provider-call authority.

## Proposal

Consider a runtime only if the acceptance criteria below are satisfied. The alternatives are Claude-only opt-in injection, retaining on-demand authoring guidance, a neutral core with a verified adapter, and deferral until a second independently verified detection-and-context adapter exists. Having a hook runtime alone does not prove model detection or safe context injection.

## Acceptance criteria

The per-turn injection ceiling is **512 estimated tokens**, using a declared UTF-8-byte estimate of four bytes per token for the local experiment. This is a decision threshold, not a provider-billed token count or a claim about model quality. The budget is recorded before measuring the profile payload.

A build verdict requires all three: a named existing consumer consisting of a specific rule, model profile, and observed misbehavior; a measured payload at or below the ceiling; and measured paired benefit, or an explicit justified decision to ship unevaluated. Absent all three, the verdict is decline. Unknown benefit does not count as benefit. Zero additional provider API spend is authorized, and the experiment must not start nested model sessions.

The evidence must also show that the selected profile text can be treated as untrusted reference data without overriding user instructions, verification requirements, or safety boundaries. No such filter is built in this plan.

## Evidence assessment

The criterion was first committed in `c786c01c2`, before this final assessment and verdict. The [local experiment](../../../releases/v4/v4.15/development/injection-prototype.md) measured the same five public synthetic prompts. The historical 18-claim case adds about 1,086 estimated tokens; the current largest 36-claim case adds about 2,512. Both exceed the 512-token ceiling. Those are byte-derived estimates of complete profile payloads, not billed token counts or proof that every hypothetical selection must exceed the ceiling.

No specific observed misbehavior was qualified as a first runtime consumer. The metadata experiment proves a bounded tail can recover one real Claude model, not that injection improves its work. The existing v4.13 skill-trigger pilot measures another intervention and cannot supply missing benefit. The paired benefit and live cache outcomes remain UNEVALUATED under zero additional provider API spend; no exception to ship unevaluated is justified by this evidence.

The [complete profile audit](../../../releases/v4/v4.15/development/profile-layer-trust-audit.md) classifies all 357 current claims across 41 models. Its conservative audit labels are 326 imperative or authoring directives and 31 descriptive references. It does not claim every directive is malicious. The current schema has neither a runtime-actionability field nor a priority field. In particular, the existing verification-removal directive is not fit to become live instruction. This audit is not a runtime filter.

The exact current Claude Code platform-label candidate fraction is 16/41, approximately 39.0%, rather than the old three-of-twelve claim. Actual adoption is that candidate fraction multiplied by the unmeasured fractions using the particular host/adapter, a configured activation surface, and explicit opt-in; no population adoption percentage can be calculated from the available data. A new hook could avoid dependence on skill-rules.json, but that is a different design, not evidence for this proposal.

The old argument that only Claude Code has hooks is false in the current repository contract. Other hooks do not establish model-detection and safe context-delivery parity. The decline therefore rests on consumer need, measured payloads, unknown benefit, and the profile trust boundary, rather than on a fabricated nineteen-empty-adapter count.

## Alternatives considered

| Alternative | Evidence and cost | Assessment |
|---|---|---|
| Build a Claude-only opt-in runtime | At least transcript metadata handling, 1,086 or 2,512 estimated tokens for the measured full-profile shape, an independently reviewed claim policy, opt-in configuration, and maintenance | Not justified without an observed first consumer and qualified benefit |
| Decline automatic runtime consumption | No new prompt-time process or token cost; retain explicit authoring proposals and Tier-3 on-demand references | Answers the current need at the first sufficient construction rung |
| Build a neutral core with one adapter | The same first-adapter work plus a shared interface; a second verified detection/context consumer is not established | Additional abstraction cannot repair the evidence deficit |
| Defer pending a second verified adapter | No runtime cost now; future detection, context delivery, privacy and benefit measurements | A valid future reconsideration condition, but hook availability alone is insufficient |

## Data handling and trust boundary

A proposed resolver would read a bounded portion of a local session transcript and extract only message.model. The temporary experiment persisted no transcript content, sent no transcript data off the machine, and created no telemetry or cache. Reading a JSON record to locate its metadata is not authority to interpret, summarize, transmit, or act on the conversation. No runtime was enabled.

Vendor-derived profile text remains untrusted reference data, even when cited, schema-valid, or confidence-scored. This plan does not weaken verification or add an automatic prompt-time consumer. The existing bundled apply_prompting_edits.py is an authoring consumer, and generated references/models files remain explicitly readable on demand. The accurate gap is absence of an automatic consumer, not a write-only profile layer.

## Risks

Vendor-derived profile claims can contain imperative instructions. A schema-valid and cited claim is not automatically authorized runtime instruction. A tail-only metadata resolver can fail to find a model, and observed resolver latency cannot establish hook-to-model latency, model quality, prompt-cache behavior, or benefit. A platform's hook support is separate from model detection and context-delivery support.

## Verdict

**DECLINE** automatic model-adaptive runtime injection under this proposal. The three-part acceptance criterion is not met, and the existing profile layer is not approved as runtime instruction. Keep the layer as authoring input and explicit on-demand reference. This settles the automatic-consumer gap by design; it does not remove any current feature.

Reconsider in a separately scoped future plan only after a specific observed misbehavior and first consumer are named, a bounded selection stays within a predeclared budget, paired benefit is qualified or unevaluated shipment is explicitly justified, and the trust/actionability/selection/retraction boundaries are independently reviewed. A second verified detection-and-context adapter can motivate that review; this record creates no platform backlog or build authorization.
