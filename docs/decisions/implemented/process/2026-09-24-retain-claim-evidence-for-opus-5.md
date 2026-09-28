# Decision: Retain claim evidence for Claude Opus 5

Status: implemented - Retain fresh claim evidence while omitting redundant Opus 5 verifier prompts.

## Problem

The [Claude Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) advises removing inherited explicit verification instructions and verifier scaffolding because that model already checks its work and extra checks consume tokens. The v4.9 prompting profile records this as model-specific advice, while the shared `verification-before-completion` skill requires fresh evidence before an agent tells a user that a task is finished.

These instructions operate at different boundaries. A model may reason over its answer repeatedly without producing a test result, while a command or real-boundary exercise can prove a specific external claim. Conversely, running the same proving command repeatedly or spawning a verifier for every small edit can waste time without adding relevant evidence.

Nexus-Hub needs a rule that remains stable across models and gives users an auditable basis for completion claims. It also needs to avoid inherited prompt scaffolding that Opus 5 does not need. The trade-off is between a small amount of mandatory evidence-gathering cost and the risk of confidently reporting an untested change as complete.

## Decision

Keep the model-independent claim boundary: before a completion claim, run the narrowest fresh evidence set that covers every part of the claim and read its results. Claude Opus 5's prompt should not add unconditional "double-check" language, repeated self-review loops, or automatic verifier subagents on top of that boundary. This intentionally retains an explicit evidence obligation despite the vendor's broader recommendation to remove inherited verification instructions.

This decision does not require a full test suite for every edit, permit a green unrelated check to stand in for proof, or waive functional and rendered-surface evidence when the claim depends on those surfaces. It does not change the separate human-review or protected-branch requirements.

## Alternatives considered

### Remove the evidence gate for Opus 5

This would follow the vendor's cost guidance literally for that model.

- Benefit: no prompt-side verification instruction remains for Opus 5, and small tasks may finish faster.
- Benefit: the harness would not duplicate the model's internal checking behavior.
- Cost: a completion claim could rest only on the model's assessment, with no observed test or runtime receipt.
- Cost: the same project would have different evidence standards depending on the selected model.

### Keep the evidence gate and every legacy verifier step

This would retain fresh proof plus inherited final rechecks and verifier subagents.

- Benefit: the existing evidence rule would remain visible without any interpretive exception.
- Benefit: extra independent review could still be selected for high-risk work.
- Cost: unconditional repetition and delegation would spend time and tokens on checks unrelated to a small diff.
- Cost: the approach conflicts with the vendor's specific over-verification warning and the skill's smallest-sufficient-set rule.

### Keep one proportional claim-evidence gate

This retains fresh, relevant proof while removing automatic duplicate checking language for Opus 5.

- Benefit: completion claims retain a command or real-boundary receipt regardless of model.
- Benefit: narrow checks and risk-based review avoid making the full suite the default for every edit.
- Cost: this is an intentional exception to the vendor's broad remove-verification recommendation.
- Cost: agents must distinguish a necessary proving action from an optional self-check, and a wrong distinction can still waste time or under-cover a claim.

## Consequences

- The shared `verification-before-completion` contract remains unchanged and owns the evidence boundary.
- The Opus 5 profile explains the exception instead of proposing a shared-body deletion.
- Fresh proving checks may still cost more than relying on Opus 5's self-assessment alone; that cost buys external receipts for the user's decision.
- Extra adversarial or independent review remains available when the task's risk calls for it, but it is not a model-specific automatic step.
