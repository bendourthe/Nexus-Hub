---
name: interface-copy
description: "Write in-product UI microcopy: buttons, errors, empty states, settings, confirmations. Use for button labels, validation messages, or empty-state copy. SKIP: docs (writing-editing, technical-writer), anti-slop-editing, and internal-comms."
summary_l0: "Write in-product UI microcopy for actions, errors, and empty states"
overview_l1: "This skill owns text that ships inside the product UI: action labels, error and validation messages, empty loading and zero-result states, settings and permission wording, confirmation and destructive-action copy, and terminology consistency. Long-form docs belong to writing-editing or technical-writer. AI-slop removal from drafted prose belongs to anti-slop-editing. Internal memos belong to internal-comms. This skill owns the words; web-typography owns wrapping and measure; accessibility-engineering owns accessible names and error association."
---

# Interface Copy

Write the words that appear *inside the product*: buttons, field errors, empty states, settings, permissions, and confirmations. This is not documentation and not a blog post. The reader is trying to do a task, not settle in to read.

`web-typography` owns how those words wrap and whether they ellipsize. `accessibility-engineering` owns whether the accessible name matches the visible label and whether an error is programmatically associated. This skill owns the source string.

## When to Use This Skill

Use when:

- The user asks for button labels, CTA text, microcopy, UX writing, empty-state copy, error messages, confirmation wording, or settings/permission strings.
- A UI string is vague ("Submit", "Error", "No data") and needs to name the object and the outcome.

**When NOT to use:**

- README, guides, reports, blog posts: `writing-editing` or `technical-writer`.
- Stripping AI-slop from a drafted paragraph: `anti-slop-editing`.
- Status emails, exec briefs, incident write-ups: `internal-comms`.
- How the string looks (size, truncation): `web-typography`.

## Quick Reference

| Topic | Read when | File |
|---|---|---|
| Empty, loading, zero-result, and destructive confirmations | Those surfaces | `references/empty-error-and-confirm.md` |

## Instructions

### 1. Name the object and the outcome

A button says what happens: "Save draft", "Send invite", "Delete project". Not "OK", "Submit", or "Click here".

If two buttons sit together, they must not both be generic. "Save" + "Cancel" is acceptable when the object is obvious from the heading immediately above. "Submit" + "Submit" on two forms in one view is a fail.

### 2. Errors tell how to fix it

Pattern: what is wrong + what to do.

- Bad: "Invalid."
- Good: "Enter an email that includes @."

Do not blame the user ("You entered a bad email"). Do not joke in a payment or deletion error. Do not dump a stack trace or an internal code unless the audience is an operator screen that already shows codes.

Validation copy is written here; binding it with `aria-describedby` is `accessibility-engineering`. If that skill is unavailable, still write the string, and mark association as not covered.

### 3. Empty, loading, and zero-result are different

| State | Job of the copy |
|---|---|
| First-use empty | Say what this place is for and the one next action ("Create your first invoice") |
| Zero result after a search | Repeat the query in the message and offer a clear next step (clear filters, different terms) |
| Loading | Name the wait if it can exceed a second ("Loading invoices..."); a spinner with no text is an accessible-name gap, not a copy gap -- still provide the string |
| Error empty (couldn't load) | What failed + retry or another path |

Do not use "Nothing to see here" or "Oops". Do not illustrate with lorem. See `references/empty-error-and-confirm.md`.

### 4. Settings and permissions in plain language

Permission prompts name the capability and the reason: "Allow camera to take a profile photo", not "Allow ACCESS_FINE_CAMERA".

Settings labels are nouns or short verb phrases that match the control ("Email notifications", not "Would you like us to perhaps send you mail?"). Descriptions under the label are one sentence; they do not repeat the label.

### 5. Confirmations for destructive and expensive actions

A destructive confirm names the object and the consequence: "Delete "Q3 forecast"? This cannot be undone." The confirm button repeats the verb: "Delete project", not "Yes".

Expensive non-destructive actions (send 400 emails, charge a card) also get a named confirm. Quiet actions (save draft, add to list) do not.

### 6. One term per thing

Pick a word for each object (`invoice` vs `bill`, `workspace` vs `team`) and use it in buttons, headings, errors, and empty states. Do not call it a workspace on the button and a team in the error.

Sentence case for buttons and titles unless the product's existing UI is Title Case. Match the product; do not introduce a second convention.

Full sentences in errors and empty-state body. No period on a one- or two-word button.

### 7. Language the user used

If the UI is English, write English. Do not mix tone: a playful empty state next to a legal permission dialog on the same path is a fail. Match the gravest screen on that path.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Submit is fine; everyone knows it." | Submit does not name the outcome. On a page with two forms, both Submits are indistinguishable. |
| "The red border already shows the error." | Color is not the message. The string is what AT reads and what the user can quote to support. |
| "I'll polish this later in writing-editing." | writing-editing will treat it as a document and add framing the UI cannot hold. UI strings stay here. |
| "A witty empty state makes the product feel human." | Wit on a failed payment or a deleted record reads as mockery. Reserve play for first-use empties only, and only if the rest of the product already does. |
| "Yes / No is a clear confirm." | Yes does not repeat the verb. Screen-reader users who land on the button hear "Yes" with no object. |

## Verification

- [ ] Every primary action label names the outcome (verb + object, or verb when the heading supplies the object).
- [ ] Every error string says what is wrong and how to fix it; none are "Invalid" alone.
- [ ] Empty, zero-result, loading, and load-error states have distinct copy (not one "No data" for all four).
- [ ] Destructive confirm names the object and the confirm button repeats the verb.
- [ ] The same object uses the same term in labels, errors, and empty states in the files touched.
- [ ] Strings are sentence case (or match the product's existing convention consistently).
- [ ] Accessible-name match and error association were handed to `accessibility-engineering` or marked not covered if that skill is unavailable.
- [ ] No README, memo, or blog-post framing was added to a UI string.

## Related Skills

- `writing-editing` -- long-form prose and docs, not in-product strings
- `anti-slop-editing` -- slop removal from drafted prose
- `internal-comms` -- internal audience memos
- `accessibility-engineering` -- accessible names and error association
- `web-typography` -- wrapping, measure, truncation of these strings
- `layout-and-spacing` -- whether the empty-state block is centered and how wide
- `interface-review` -- coordinating review
