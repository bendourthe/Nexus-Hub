# Decision: Do NOT ship a standalone `grill-me` skill

Status: rejected - 2026-08-25. The capability shipped instead as an upgrade to `design-interview` plus a thin `/grill` entry point.

## Problem

`grill-me` circulates widely as a skill for stress-testing a plan, and a request arrived to add it to the Nexus-Hub catalog. The obvious reading is "create `catalog/skills/<category>/grill-me/SKILL.md`".

Two findings made that the wrong move.

**Upstream `grill-me` is a delegator, not an implementation.** Its entire body is one line instructing the agent to call a separate `grilling` skill, under a two-field frontmatter carrying `disable-model-invocation: true`. A sibling, `grill-with-docs`, is the same one-line pattern. Copying "grill-me" would copy a pointer and leave the substance behind.

**Nexus-Hub already owns the substance.** The territory was populated before this request:

| Concern | Existing owner |
|---|---|
| Interview engine (already triggers on "grill me") | `design-interview` |
| Opt-in interactive grill mode on an idea | `idea-refine` |
| Autonomous multi-persona critique of a plan | `plan-review` |
| Async interrogation of an absent stakeholder | `decision-questionnaire` |
| Structured gap detection on a written spec | `ambiguity-detector` |

A `grill-me` skill would have been the **fourth** owner of one concern.

## Decision

Do not add the skill. Instead:

1. Upgrade `design-interview` with the three mechanics that were genuinely missing: dependency-ordered **frontier rounds**, a **recommended answer** per question, and **sub-agent fact-finding** with only the downstream branch blocking.
2. Add `catalog/commands/grill.md`, a thin dispatcher, so the word people actually type resolves to the engine. The installer already synthesizes command-derived skills with `disable-model-invocation: true`, which reproduces upstream's own invocation posture without a hand-written duplicate.
3. Wire the engine into `implementation-plan` Step 4.5 so plans are grilled by default.

Two repository rules force this outcome independently. The rule-ownership convention in `AGENTS.md` requires exactly one owning skill per concern, with non-owners referencing the owner and describing only the handoff. The scope-fit gate under Boundaries requires naming the shipped behavior or active call site that a new module serves; "people type this name" is answered by a 30-line dispatcher, not by a fifth skill.

## Alternatives considered

**Ship `grill-me` as a full skill and deprecate `design-interview`.** Rejected. `design-interview` carries a second, unrelated job upstream does not have: maintaining the `CONTEXT.md` domain glossary. Four other skills invoke it as an engine. Replacing it would mean rewriting those call sites to gain a name.

**Ship `grill-me` as a one-line skill delegating to `design-interview`, mirroring upstream exactly.** Closest to the literal request and genuinely tempting. Rejected because Nexus-Hub already has a delegation mechanism for exactly this (`catalog/commands/*.md` dispatchers), and the installer already converts each command into a per-platform skill. A hand-written delegator skill would sit beside a generated one with the same name on several platforms.

**Ship nothing and rely on the existing trigger phrase.** `design-interview` already fires on "grill me", so this is defensible and was offered. Rejected because it leaves the real gap open: no plan was ever grilled unless the user asked, and there was no command-surface entry point on the platforms that expose commands but not trigger-phrase matching.

**Ship `grill-with-docs` too.** Rejected as unnecessary: it delegates to `grilling` plus a domain-modeling skill, and `design-interview` already maintains `CONTEXT.md` inline during the interview. The combined behavior is the default here rather than a second variant.

## Consequences

- The name `grill` is reachable as a command; the mechanics have exactly one owner.
- Upstream's frontier-round algorithm is adopted; upstream's project is not named in any shipped artifact, per the reverse-engineering attribution rule. Attribution lives in the comparison report's rationale.
- One deliberate adaptation: upstream formats rounds with emoji markers. Nexus-Hub's English Markdown is ASCII-only, so the round format uses an ASCII equivalent.
- If a future request asks again for a `grill-me` skill, this record is the answer.
