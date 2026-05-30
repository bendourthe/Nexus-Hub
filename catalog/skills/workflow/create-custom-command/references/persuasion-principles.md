# Persuasion Principles for Discipline Skills

This reference explains why the structural devices in a discipline skill (the hard gate, the rationalization table, the red-flag list, the authority framing) actually change agent behavior, grounded in the persuasion research, and which principles to use versus avoid when the goal is compliance rather than agreement. It is the "why it works" companion to `tdd-for-skills.md` (which tells you to capture rationalizations and rebut them) and `pressure-testing.md` (which tells you how to surface them). Use it when you are deciding HOW to phrase a rebuttal or a gate so it holds under pressure.

## The research, in brief

Two public sources motivate the framing choices below. Read the originals; this reference summarizes their relevance to skill authoring and does not reproduce their text.

- **Cialdini, R. (2021), Influence: The Psychology of Persuasion (revised edition).** Catalogues the principles of influence that reliably shift human (and, as the second source shows, model) behavior: authority, commitment/consistency, scarcity, social proof, unity, liking, and reciprocity.
- **Meincke et al. (2025), a large-scale study (N approximately 28,000 conversations) measuring how Cialdini-style framing affects LLM compliance.** Reported that persuasion framing moved compliance on a target behavior from roughly 33% to roughly 72%. The headline relevance for skill authoring: the same framing devices that influence people measurably influence models, so the wording of a discipline gate is not cosmetic, it is causal.

The practical takeaway is that a discipline skill's effectiveness depends on more than listing the correct steps. How the gate and its rebuttals are framed determines whether the agent follows them when a rationalization is available.

## Principles to use

These four principles map directly onto the devices a discipline skill already uses, and strengthen them when applied deliberately.

### Authority

State the gate as a non-negotiable rule in a clear, imperative voice, and where appropriate ground it in an external standard the agent recognizes (a project Iron Law, a documented convention, a cited failure history). Authority is why a discipline skill earns blunt, absolute phrasing ("run the proving command FRESH before any completion claim") that would feel heavy-handed in a capability skill. The authority must be real: cite the convention or the failure record, do not manufacture urgency. Hollow authority ("this is critically important") habituates the agent to ignore emphasis.

### Commitment and consistency

Get the agent to state the disciplined intention explicitly before the pressure peaks, then the skill can hold it to its own stated commitment. A gate that asks the agent to name the proving command up front, then verify against that named command, leverages consistency: skipping the verification now contradicts a commitment the agent already made in this session. This is more durable than an instruction delivered only at the moment of temptation.

### Scarcity

Frame the cost of the shortcut as an irreversible loss, not a deferred chore. "Shipping an unverified claim spends the user's trust, and that does not refund when the regression surfaces" frames verification as protecting something scarce (trust, a clean record) rather than as optional diligence. Scarcity framing works because the agent weighs a concrete loss more heavily than an abstract best-practice.

### Social proof

Where a behavior is the established norm, say so concretely: "every shipped discipline skill in this catalogue runs its proving command before claiming done". Social proof is strongest when it is specific and true; a vague "best engineers always verify" is weaker than a checkable statement about what the surrounding skills actually do. Use it to normalize the disciplined action, not to shame the shortcut.

### Unity

Frame the agent and the user as on the same side of the goal ("we are both trying to ship a change that actually works"), so the gate reads as shared interest rather than external imposition. Unity reduces the adversarial feel of a hard gate, which matters because an agent that experiences the gate as an obstacle looks harder for a way around it.

## Principles to AVOID for compliance

Two Cialdini principles are actively counterproductive when the goal is to make the agent do the correct-but-harder thing, because they optimize for agreement and warmth rather than for the disciplined action.

### Liking

Framing that makes the agent want to please or agree produces sycophancy: the agent tells the user what the user appears to want to hear. For a discipline skill this is the disease, not the cure. The `receiving-code-review` skill exists precisely to block performative agreement ("you're absolutely right!") and reasoned-but-false concession. Do not write rebuttals that lean on being agreeable; write rebuttals that name the failure. Liking-based framing is what makes an agent concede a correct technical position under mild social pressure.

### Reciprocity

Framing that sets up a "the user did X for you, so comply" exchange creates a transactional dynamic where the agent complies to settle a debt rather than because the discipline is correct. This produces compliance that evaporates the moment the perceived debt is paid, and it teaches the agent that the discipline is negotiable currency rather than a standard. Avoid it.

The common failure both principles share: they make the agent optimize for the relationship instead of for the correct outcome, which is the root of sycophancy. Discipline skills must keep the agent anchored to the observable correct action.

## Principle-by-skill-type guidance

Not every skill type wants the same persuasion posture. Match the framing to the skill's job.

| Skill type | Goal | Use heavily | Use sparingly | Avoid |
|---|---|---|---|---|
| Discipline (gate, anti-rationalization) | Make the agent do the harder correct thing under pressure | Authority, commitment, scarcity | Social proof | Liking, reciprocity (they produce sycophancy) |
| Guidance (how-to, technique) | Help the agent do something well | Social proof, unity | Authority (too heavy for non-gates) | Scarcity (manufactures false urgency) |
| Collaborative (brainstorming, spec, review-receiving) | Reach a good joint decision without sycophancy | Unity, commitment | Authority | Liking (the specific risk: warmth becomes agreement) |
| Reference (schemas, lookups, conventions) | Be accurate and findable | None (persuasion is irrelevant) | None | All (framing devices add noise to factual content) |

The boundary that matters most: collaborative skills want unity but must avoid liking, because the warmth that makes collaboration pleasant is one short step from the agreement that makes it useless. A spec or review-receiving skill should feel like two people solving a problem, not one person flattering another.

## Common Rationalizations (about applying these principles)

| Rationalization | Reality |
|---|---|
| "Persuasion framing is manipulation; the steps should speak for themselves." | The steps speaking for themselves is the baseline that the research shows produces roughly 33% compliance under pressure. Framing is not manipulation when the gate is correct and the authority cited is real; it is the difference between a gate the agent follows and one it rationalizes past. |
| "More emphasis is always better, so I'll make everything an Iron Law." | Authority habituates: if every line shouts, none of it carries weight. Reserve absolute phrasing for the actual gate and ground it in a real standard, so the emphasis stays meaningful. |
| "A friendly, agreeable tone makes the skill more pleasant to follow." | Agreeableness (liking) is the exact lever that produces sycophancy, where the agent concedes a correct position to keep the interaction warm. For discipline and collaborative skills, pleasantness that erodes the disciplined action is a defect. |
| "Citing research is overkill for a skill body." | The citation does two jobs: it supplies real authority (a principle the agent recognizes as grounded) and it documents WHY the framing was chosen, so a future editor does not flatten the gate back into neutral prose. Cite the source; do not reproduce its copyrighted text. |

## Verification

- [ ] The gate uses authority framing grounded in a real standard or documented failure, not manufactured urgency.
- [ ] At least one rebuttal leverages commitment, scarcity, or social proof with a concrete (checkable) claim.
- [ ] No rebuttal or framing relies on liking or reciprocity (no warmth-for-agreement, no debt-settling compliance).
- [ ] Collaborative sections use unity without tipping into liking.
- [ ] The research is cited by author and year; no copyrighted text is reproduced.

## Related references

- `tdd-for-skills.md` - the methodology that produces the rationalizations these principles help you rebut.
- `pressure-testing.md` - the scenarios under which well-framed rebuttals must hold.
- `[[receiving-code-review]]` - the discipline skill whose entire purpose is to block the liking-driven sycophancy this reference warns against.
- `[[skill-eval-loop]]` - measure whether a reframed rebuttal actually raises pass-rate under pressure.
