---
name: decision-questionnaire
description: Turn a decision the agent cannot resolve in-session into a self-contained Markdown questionnaire for the one person who can answer it - filled in async or walked through live. Use whenever the user says "I need to ask my stakeholder", "make a questionnaire", "prepare questions for the client", "prepare questions for the PM", "prepare questions for the security team", "async decision", or needs a send-ready question list with enumerated options. Interviews the requester about the send (who, what context they lack, what must come back, deadline), not about the design itself. SKIP - interviewing the current user about their own design (use design-interview); reviewing a written spec (use ambiguity-detector); writing internal comms with the six templates (use internal-comms).
summary_l0: "Write an async Markdown questionnaire for the one stakeholder who can unblock"
overview_l1: "When a decision cannot be resolved in-session, interview the requester about the send and emit a questionnaire for the recipient. Lead with a short context block in the recipient's language, ask the minimum questions with enumerated options plus a free-text escape, and close with answers-needed-by and what happens next. Default output docs/questionnaires/<date>-<topic>.md. SKIP design interviews of the current user and spec review. Trigger phrases: I need to ask my stakeholder, make a questionnaire, prepare questions for the client, async decision."
category: business-product
---

# Decision Questionnaire

Turn a decision that cannot be resolved in this session into a Markdown questionnaire addressed to the one person who can answer it. They may fill it async or walk through it live. The skill interviews the requester about the *send*, not the subject: who the recipient is, what context they lack, what must come back for work to unblock, and the deadline or format.

## When to Use This Skill

Use when:

- Work is blocked on a decision the current user cannot make.
- The user asks for a questionnaire, an async decision, or questions for a client, PM, or security team.
- The recipient is not in the session, so a grilling interview would question the wrong person.

**When NOT to use:**

- Interviewing the *current* user about their own design. That is [[design-interview]].
- Reviewing an already-written spec for ambiguity. That is [[ambiguity-detector]].
- Drafting a status update, FAQ, or incident note. That is [[internal-comms]].

## Instructions

### 1. Interview the requester about the send

Ask one question at a time (reuse the one-at-a-time discipline; do not fork a second protocol) until these four are known:

1. **Recipient** - name or role, and what they already know.
2. **Missing context** - what the recipient would need in order to answer without opening the repo.
3. **Unblock condition** - the specific answers without which implementation cannot continue.
4. **Deadline and format** - when answers are needed, and whether a Markdown file, email, or live walkthrough is the send path.

If the requester is actually the decision-maker, stop and hand off to [[design-interview]].

### 2. Write the questionnaire for the recipient

Output path: caller-specified, or `docs/questionnaires/<YYYY-MM-DD>-<topic-slug>.md`. Create `docs/questionnaires/` if needed.

Required shape:

1. **Context** (short, no repo jargon unless defined in that block). Written for the recipient.
2. **Questions** - the minimum set. Each question has enumerated options where possible, plus a free-text escape ("something else:").
3. **Answers needed by / what happens next** - date or event, and what the team will do with each likely outcome.

Do not include internal ticket ids, file paths, or slang the recipient would have to decode. If a term is unavoidable, define it in the context block.

### 3. Keep the question set minimum

Every question must map to an unblock condition from step 1. Drop nice-to-haves. Prefer options the recipient can circle over essay prompts. Pair each option list with the free-text escape so a real-world "none of these" does not stall the send.

### 4. Hand the file back; do not silently decide

Present the path. Do not fill in the recipient's answers. Do not treat silence as a default option unless the requester explicitly chose a default in step 1 and the questionnaire states that default in the "what happens next" block.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just grill the developer in this session; they know what security would say." | Guessing a stakeholder's decision is how the wrong control ships. Send the questionnaire. |
| "A long essay prompt gives richer answers." | Recipients skip long forms. Enumerated options plus a free-text escape get a usable reply. |
| "I can put repo paths in the context; they have GitHub access." | Many recipients will not open the repo. The context block has to stand alone. |
| "This is design-interview with a file at the end." | Design-interview questions the current user. This skill packages questions for someone who is not here. Wrong audience, wrong artifact. |
| "internal-comms already has templates." | Those templates are status, FAQ, incident, and leadership notes. They are not a decision-capture form with unblock conditions. |

## Verification

- [ ] The output file exists at the caller path or `docs/questionnaires/<date>-<topic>.md`.
- [ ] The file has a context block, numbered questions with options plus a free-text escape, and an answers-needed-by / what-happens-next block.
- [ ] Every question maps to a stated unblock condition; there is no orphan "while we have them" question.
- [ ] Repo jargon is defined in the context block or absent.
- [ ] The recipient is named (person or role); the requester was not treated as the decision-maker.
- [ ] No recipient answers were fabricated.

## Related Skills

- [[design-interview]] - interviews the current user about a design; this skill writes for an absent stakeholder
- [[business-analyst]] - broader requirements gathering; this skill is the send-ready decision form when one person must unblock
- [[internal-comms]] - six comms templates; not a questionnaire
- [[ambiguity-detector]] - audits a written spec; does not produce a send packet
- [[idea-refine]] - problem statement with the current user, before anyone else needs to be asked
