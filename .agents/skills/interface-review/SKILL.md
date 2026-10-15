---
name: interface-review
description: "Coordinate a multi-domain interface review and return one consolidated verdict. Use for holistic UI review or multi-domain UX pass. SKIP: one-domain requests and general code review (multi-agent-code-review, code-quality)."
summary_l0: "Orchestrate a multi-domain UI review into one capped, honest verdict"
overview_l1: "This skill owns orchestration only: it loads the interface-craft delegates in a fixed order, applies each delegate's principles, ignores each delegate's standalone report shape, and emits one consolidated review. It never restates or overrides a delegate rule. The cluster rule-ownership table lives here. Quick mode covers the primary path, P0/P1 only, cap 5. Full mode covers the requested scope, cap 20. Missing delegates are named and marked not reviewed. Default is read-only. SKIP single-domain work and general code review."
---

# Interface Review

Run a **holistic, multi-domain** UI review and return **one** verdict. This skill does not own accessibility rules, spacing scales, microcopy, type metrics, palettes, or anti-slop gates. Those stay on the delegates. This skill owns order, coverage honesty, consolidation, caps, and the output shape.

If the user asked about only one of those domains, stop and load that owner instead.

## When to Use This Skill

Use when the user asks for an interface review, a holistic UI/UX pass, or a review that spans accessibility **and** layout (and typically copy, type, color, or polish) of a screen, component, or flow.

**When NOT to use:**

- One domain only: `accessibility-engineering`, `layout-and-spacing`, `interface-copy`, `web-typography`, `color-systems`, or `hallmark-design`.
- General code review of a diff or PR: `multi-agent-code-review` or `code-quality`.
- Implementing the UI (unless the user also asked to apply fixes). Default is **read-only**.

## Cluster rule ownership (canonical)

Exactly one owner per concern. This table is the cluster's source of truth. Delegates reference it; they do not restate another owner's rule.

| Concern | Owner | Everyone else |
|---|---|---|
| Names, keyboard, focus visibility, heading *ranks*, forms, hit areas, reduced-motion **requirement**, when contrast applies and how severe a miss is | `accessibility-engineering` | Measure/remediate color via `color-systems`; visual heading size via `web-typography`; optional motion recipe via `hallmark-design`; visual reading order via `layout-and-spacing` |
| Spatial grouping, spacing scale, breakpoints, logical RTL | `layout-and-spacing` | Truncation mechanics via `web-typography` after this skill decides the container has no more room |
| In-product source strings | `interface-copy` | AT association via `accessibility-engineering`; wrap/measure via `web-typography` |
| Font loading, type scale, wrap, truncation, visual heading size | `web-typography` | Ranks via accessibility; words via copy |
| Palette construction, measuring the rendered pair, gamut fallbacks | `color-systems` | Severity via accessibility; applying a supplied brand JSON via `theme-tokens` / `brand-styling` |
| Anti-slop judgment and optional polish recipes (elevation, radius, icon stroke, motion values) | `hallmark-design` | Requirements stay on accessibility |
| Order, coverage map, consolidation, caps, verdict | `interface-review` | Never duplicates a row above |

Tie-break already used above: accessibility decides *when* contrast is required and *how bad* a miss is; color-systems *measures* and *changes* the colors.

## Instructions

### 1. Resolve scope and mode; state them first

Name the files (or screens) in scope. Choose **quick** or **full**:

- User said skim / quick / compact, or pointed at one component: **quick**. Cover the primary path only. Report blocker and major only. Cap **5** headline findings.
- Otherwise **full**. Cover the whole requested scope. Cap **20** headline findings.

Never pad to the cap. Zero findings plus a real Considered-but-Rejected table is valid.

State in the report: scope, mode, cap.

### 2. Walk delegates in this order

1. `accessibility-engineering` -- an unlabeled or unkeyboardable control makes later notes about radius or palette a distraction.
2. `layout-and-spacing` -- structure and room before wrapping or color on the wrong surface.
3. `interface-copy` -- the words, before how they wrap.
4. `web-typography` -- wrap, scale, truncate.
5. `color-systems` -- measure pairs on the surfaces layout already named.
6. `hallmark-design` -- polish last, so inaccessible UI is not gold-plated.

**Apply each loaded delegate's principles. Ignore each delegate's standalone output format** (their checklists, gate numbers, and per-skill tables). Translate survivors into *this* skill's findings table. That consolidation is the point of a coordinator.

### 3. Missing-delegate honesty

If a delegate cannot be loaded, in the coverage section write `not reviewed (missing: <skill-name>)` for that domain and continue. Do not reconstruct its rules from memory, do not substitute a neighbour, and do not claim a holistic review. The gap must be visible in the report, not only in these instructions.

### 4. Evidence, severity, de-duplication

Each finding needs `path/to/file:line` (or a stable selector plus file) and the current implementation (quote or paraphrase the markup/CSS).

Shared severity (do not invent a fourth scale):

- **blocker** -- cannot complete the task, or a WCAG miss the accessibility skill graded blocker
- **major** -- task is possible but clearly wrong (layout collapse, misleading copy, unmeasured contrast the accessibility skill graded major)
- **advisory** -- polish, rhythm, or optional recipe

One root cause, one finding, every confirmed location listed. Do not emit one row per occurrence.

### 5. Considered but Rejected

List real candidates you inspected and chose not to report, with the reason (owner permits it, evidence insufficient, project convention, or complexity without user benefit). Never invent filler. A thin fixture says `thin scope, N candidates`.

### 6. Output shape (mandatory)

```markdown
## Scope and coverage

- Scope: ...
- Mode: quick | full (cap N)
- Mutating: no (default) | yes (user asked to apply fixes)

| Domain | Delegate | Coverage |
|---|---|---|
| Accessibility | accessibility-engineering | inspected ... / not reviewed (missing: ...) |
| Layout | layout-and-spacing | ... |
| Copy | interface-copy | ... |
| Typography | web-typography | ... |
| Color | color-systems | ... |
| Polish | hallmark-design | ... |

## Findings

| ID | Severity | Domain | Location | Current | Required (owner) |
|---|---|---|---|---|---|

## Considered but Rejected

| Candidate | Reason |

## Verification

- Checks that ran: ...
- Checks not verified: ... (missing delegate, no computed styles, no browser)

## Verdict

One paragraph. Pass / fail against the requested bar. Do not add a second summary table.
```

Overflow beyond the cap goes to a ranked appendix, never deleted, never mixed into the headline table.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will paste each delegate's report so nothing is lost." | Six formats bury the verdict. Translate into one table. |
| "Color-systems is missing, so I will recall 4.5:1 and grade it." | That reconstructs an owned rule. Mark color **not reviewed**. |
| "I should fill the cap so the review looks thorough." | Padding hides the blocker. Short is valid. |
| "This is also a PR; I will mix in code-quality findings." | Wrong skill. Route code review separately. |
| "They said review the button, so I will still walk all six domains." | Single-domain request: load the owner, not this coordinator. |

## Verification

- [ ] Scope and mode appear at the top of the report.
- [ ] Delegates were walked in the order above, or a skip is recorded as not reviewed by name.
- [ ] No delegate output format leaked into the report (no hallmark gate-number dump, no per-skill checklist dump).
- [ ] Headline finding count respects the mode cap; the list was not padded.
- [ ] Considered-but-Rejected lists real inspected candidates (or an explicit thin-scope note).
- [ ] Each finding has a location and the current implementation.
- [ ] Exactly one verdict paragraph.
- [ ] No files were edited unless the user asked for implementation.
- [ ] A one-domain prompt was not handled here.

## Related Skills

- [[functional-verification]] -- owns real-boundary exercise and rendered evidence; this skill consolidates findings from the interface-review domains.
- `accessibility-engineering`, `layout-and-spacing`, `interface-copy`, `web-typography`, `color-systems`, `hallmark-design` -- delegates; this skill does not override them
- `multi-agent-code-review` -- code/diff review, not UI-domain orchestration
- `code-quality` -- maintainability, not interface craft
- `frontend-ui-engineering` -- component architecture; not a delegate of this review
