---
name: over-engineering-review
description: "Review a diff or a repo for over-engineering and emit a tagged delete-list. Use this skill whenever the user says review for over-engineering, what can we delete, is this over-engineered, audit this repo for bloat, or wants a delete-list of extra machinery, even if they do not name this skill. SKIP: correctness, security, performance, Fowler smell catalogs, and post-write structural simplification (code-simplification). Do NOT apply fixes, and never tag a proving command or trust-boundary check as bloat."
summary_l0: "Emit a tagged over-engineering delete-list without applying fixes"
overview_l1: "Hunt extra machinery in a diff (default) or a whole repo and emit one tagged line per finding (delete, stdlib, native, yagni, shrink) plus a net line-count, or Lean already. Ship. This skill does not apply fixes, does not replace SOLID or Fowler reviews, and does not flag required proving commands or trust-boundary checks. Trigger phrases: review for over-engineering, what can we delete, is this over-engineered, audit this repo for bloat."
---

# Over-Engineering Review

Hunt extra machinery. Report it. Do not apply the deletes. Two scopes share one skill: `diff` (default) and `repo`.

Trigger routing cases live in `evals/trigger-cases.json`.

## When to Use This Skill

Use when:

- The user asks to review for over-engineering, what can we delete, or whether this is over-engineered.
- The user wants to audit this repo for bloat.
- A complementary delete-list is useful beside a quality or multi-agent review.

**When NOT to use:**

- Correctness, security, or performance review (`security-review`, `performance-review`, and the multi-agent pipeline).
- Fowler smell catalogs (`code-smell-detector`).
- SOLID / maintainability scoring (`code-quality`).
- Post-write structural simplification in place (`code-simplification`).
- Pre-write construction choices before the extra code exists (`minimal-construction`).
- Applying the deletes. This skill reports; it does not patch.

## Instructions

### 1. Resolve scope

- `diff` (default): the current uncommitted or specified diff.
- `repo`: a bounded walk of the paths the user named, or the whole repository if they asked to audit this repo for bloat.

Record the scope in the first line of the report. Do not silently expand a diff review into a repo walk.

### 2. Hunt extra machinery, not required floors

Look for wrappers around stdlib, native platform features, unused generalization, speculative helpers, and new dependencies that a few lines would replace.

Never tag as bloat:

- A proving command required by `verification-before-completion`.
- Trust-boundary validation, data-loss handling, security, or accessibility checks.
- End-of-Task Summary or a user-requested explanation.

### 3. Emit a tagged delete-list

One line per finding, exactly this shape:

`<file>:L<line>: <tag> <what>. <replacement>.`

Tags (one per line):

- `delete` -- the symbol can go with no replacement.
- `stdlib` -- replace with the language or runtime standard library.
- `native` -- replace with a platform or framework feature that already ships.
- `yagni` -- speculative machinery for a caller that does not exist.
- `shrink` -- keep the behavior, cut the wrapper.

Do not invent extra tags. Do not copy these tag definitions into `code-quality`.

Cap: report the highest-value findings you actually found. Do not pad. A short list is valid. A clean result is valid.

### 4. Close the report

If any finding remains, end with:

`net: -<N> lines possible`

If nothing qualifies, emit only:

`Lean already. Ship.`

Then add **Considered but Rejected**: real candidates you inspected and did not report, each with a reason. Never invent filler. If the scope was thin, say so.

Do not apply fixes. Do not open an editor to delete the lines. Hand application to the user or to an implementer they name.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I should just delete it while I am here" | This skill is a review. Applying the delete collides with implementers and with `security-patch-advisor`. |
| "The proving command looks like bloat" | `verification-before-completion` owns proving commands. Required checks are not `delete:`. |
| "I will also score SOLID and Fowler smells" | Those stay on `code-quality` and `code-smell-detector`. Do not absorb them. |
| "Every review should include this lens" | It is optional. `multi-agent-code-review` must not make this a mandatory second report. |
| "I need twenty findings to look thorough" | Do not pad. `Lean already. Ship.` is a complete result. |

## Verification

- [ ] Scope is `diff` or `repo` and is stated in the report
- [ ] Each finding uses `<file>:L<line>: <tag> ...` with one of `delete`, `stdlib`, `native`, `yagni`, `shrink`
- [ ] The report ends with `net: -<N> lines possible` or `Lean already. Ship.`
- [ ] No proving command or trust-boundary check is tagged for deletion
- [ ] No fix was applied
- [ ] Considered but Rejected lists real inspected candidates, or states that the scope was thin
- [ ] `evals/trigger-cases.json` still lists positives for delete-list review and negatives for security, in-place simplify, and Fowler smells

## Related Skills

- `minimal-construction` -- pre-write ladder; this skill reviews code that already exists
- `code-simplification` -- applies post-write collapse; this skill only reports
- `dead-code-eliminator` -- unreachable code at scale
- `code-quality` -- SOLID and maintainability; optional handoff to this delete-list
- `code-smell-detector` -- Fowler smells
- `multi-agent-code-review` -- optional extra lens, not a required persona
- `security-review` -- trust-boundary and security findings
- `verification-before-completion` -- proving commands
