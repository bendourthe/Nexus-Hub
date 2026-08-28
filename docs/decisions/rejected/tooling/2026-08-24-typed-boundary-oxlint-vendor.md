# Decision: Vendor a typed-boundary Oxlint plugin into consumer repositories

Status: rejected - the skill-native runbook already owns the behavior, while Nexus-Hub has no in-repo TypeScript application that can prove or maintain an ESTree plugin against `@oxlint/plugins` API drift

## Problem

Phase 2 added `typed-boundary-hygiene`, which teaches agents to replace chained assertions, weak `unknown` or `object` contracts, unsafe dictionaries, widen-then-assert flows, reflection, and broad module mocks with named types and checked seams. The remaining question is whether Nexus-Hub should also ship a user-invoked installer skill that copies a re-authored Oxlint plugin into a consumer's TypeScript repository, queries live package versions, merges lint configuration, and makes those rules machine-enforced there.

That plugin would not run against Nexus-Hub itself. This repository has no TypeScript application or Oxlint stack that can serve as a proving ground, so maintainers would own visitor correctness, configuration merging, package-manager behavior, and upstream plugin-API drift without exercising the result in the product that distributes it.

## Proposal

Do not add Oxlint or `@oxlint/plugins` to Nexus-Hub runtime, development dependencies, CI, workflows, or installers. Do not add a `typed-boundary-lint-install` catalog skill or bundled plugin assets. Keep typed-boundary behavior skill-native through `typed-boundary-hygiene`, its trigger cases, ownership handoffs, and the catalog's existing validation gates.

This is a rejected capability, not deferred v4.1.0 work. Reconsideration requires a later decision that explicitly supersedes this one, identifies a maintained consumer repository as the proving ground, and assigns ownership for upstream API drift and installation behavior.

## Alternatives considered

- **Ship the consumer-repository vendor skill.** Rejected because it creates a package-manager and plugin-API maintenance surface that Nexus-Hub cannot test against its own application. Live npm version queries would avoid stale pins but would not prove visitor semantics or config compatibility.
- **Add Oxlint to Nexus-Hub CI as the proving ground.** Rejected because Nexus-Hub has no in-repo TypeScript product for those typed-boundary rules. Adding a tool solely to justify its own distribution would create circular infrastructure rather than product coverage.
- **Drop both the plugin and the skill-native guidance.** Rejected because Phase 2 already provides a tested, platform-portable runbook with no new dependency or outbound requirement.
- **Keep the plugin idea in known gaps.** Rejected because that would imply intended future delivery. The current answer is no unless a superseding decision changes the ownership facts.

## Risks

- Skill-native guidance is advisory rather than compiler-enforced. The accepted mitigation is the dedicated runbook, trigger fixtures, TypeScript ownership handoff, and semantic catalog tests.
- A consumer team may independently need lint enforcement. That team can own a repository-local implementation under its own dependencies and CI; Nexus-Hub does not distribute or maintain it.
