# Confidence-Anchored Scoring

A reusable discipline for scoring, deduplicating, and gating review findings so a multi-reviewer pipeline surfaces only the findings worth a human's attention. It replaces a free-floating "confidence: 0-100" slider (which reviewers anchor inconsistently) with five discrete behavioral anchors, a deterministic dedup key, cross-reviewer promotion, mode-aware demotion, and a deliberately-late suppression gate.

This reference is consumed by the multi-agent review pipeline (the persona-fanout code review) and can be cited by single-agent reviewers (`code-quality`, `security-review`) and by `run-penetration-test` synthesis when ranking findings. It is scoring policy only - it does not tell a reviewer *what* to look for.

## 1. The five confidence anchors

Confidence is one of exactly five discrete values. Reviewers pick the anchor whose behavioral definition matches their evidence; no values in between.

| Anchor | Name | Behavioral definition (what must be true to assign it) |
|---|---|---|
| **0** | Noise | The reviewer cannot substantiate the finding at all on re-read. Drop it; do not emit. |
| **25** | Speculative | A pattern that *might* be a problem, but the reviewer has not traced it to a concrete failure. No reproduction, no data-flow path - a hunch. |
| **50** | Plausible | The reviewer can describe a concrete scenario where this fails, but has not confirmed the preconditions hold in this codebase (e.g., "if this input is attacker-controlled, then..."). |
| **75** | Substantiated | The reviewer has traced the failure: the path exists, the preconditions are reachable, and the consequence is real. A skeptical reader would agree it is a true finding. |
| **100** | Proven | Backed by a reproduction, a failing test, an exploit snippet, or an unambiguous contract violation visible in the diff. Not "I am sure" - "here is the proof". |

Anchors are about *evidence*, not severity. A P0 can sit at anchor 50 (plausible-but-unconfirmed critical) and a P3 can sit at anchor 100 (proven trivial nit).

## 2. Fingerprint dedup

Two reviewers (or two passes of one reviewer) routinely report the same issue with different wording. Collapse them with a deterministic fingerprint computed BEFORE gating:

```
fingerprint = normalize(file) + "|" + line_bucket(line) + "|" + normalize(title)
```

- `normalize(file)`: repo-relative POSIX path, lowercased; strip a leading `./`.
- `line_bucket(line)`: the line number bucketed to a window of +/-3 lines, so `line // 3` (findings within three lines of each other share a bucket). This absorbs off-by-a-few-lines disagreement between reviewers reading slightly different context.
- `normalize(title)`: lowercase, strip punctuation, collapse whitespace, drop a small stopword set (`the`, `a`, `an`, `is`, `in`, `of`, `to`). Optionally reduce to a sorted token set so "missing null check on user" and "user missing null check" collide.

Findings sharing a fingerprint are one finding. Merge them per section 3.

## 3. Cross-reviewer agreement promotion

When two or more independent reviewers land on the same fingerprint, that agreement is evidence. Promote the merged finding's confidence by one anchor step, capped at 100:

- Two reviewers at **50** -> promote to **75**.
- Two reviewers at **75** -> promote to **100**.
- A reviewer at **50** and one at **75** -> take the max (75), then promote one step -> **100**.

Promote at most once per merge (agreement among three reviewers is not two steps). Record which reviewers agreed in the merged finding's provenance so a human can audit the promotion. Disagreement is never a demotion signal on its own - a single reviewer can be right - but it blocks promotion.

## 4. Mode-aware demotion

Advisory personas (testing, maintainability, style) produce many low-severity findings that are correct but rarely worth blocking on. Demote weak advisory findings by one anchor step when ALL of the following hold:

- Severity is **P2 or P3** (never demote P0/P1).
- The finding originates from an **advisory persona** (testing, maintainability, documentation, style) rather than a correctness/security/reliability persona.
- The run is in a **non-interactive mode** (report-only / headless / autofix) where the human is not present to triage.

In interactive mode, do not demote - the human is there to judge. Demotion is a prioritization tool for unattended runs, not a correctness judgement.

## 5. The deliberately-late confidence gate

Apply the suppression gate LAST - after dedup (section 2), promotion (section 3), and demotion (section 4). Gating early throws away findings that cross-reviewer agreement would have promoted above the threshold.

Gate rule:

- **Suppress** any finding below anchor **75**...
- **except** a **P0** finding at anchor **50 or above**, which is always surfaced (a plausible critical is worth a human's glance even unconfirmed).

Everything surviving the gate is emitted; everything suppressed is dropped from the headline report but kept in a verbose/appendix tier so nothing is silently lost.

### Ordering (do not reorder)

1. Collect raw findings from all reviewers.
2. Fingerprint and dedup -> merge duplicates.
3. Cross-reviewer promotion on merged findings.
4. Mode-aware demotion of weak advisory P2/P3.
5. Confidence gate (suppress < 75, except P0 >= 50).
6. Emit survivors; archive suppressed findings in the verbose tier.

## 6. Finding fields

For the pipeline to apply this policy, each finding carries:

| Field | Purpose |
|---|---|
| `title` | Short title (feeds the fingerprint). |
| `severity` | `P0` / `P1` / `P2` / `P3`. |
| `file`, `line` | Location (feed the fingerprint). |
| `confidence` | One of `0 / 25 / 50 / 75 / 100`. |
| `persona` / `owner` | Which reviewer produced it (drives demotion + promotion provenance). |
| `requires_verification` | True when confidence < 100 and the finding should get an independent verification pass before it blocks a merge. |
| `pre_existing` | True when the issue predates the diff under review (so it is reported but not attributed to the change). |
| `autofix_class` | `safe` / `assisted` / `manual` - routes the finding to autofix vs human. |
| `suggested_fix` | The concrete remediation. |

## Verification

- [ ] Every emitted finding has a `confidence` equal to exactly one of `0 / 25 / 50 / 75 / 100` (no interpolated values).
- [ ] Dedup ran before gating, using `normalize(file) + line_bucket(+/-3) + normalize(title)`.
- [ ] Cross-reviewer promotion was applied at most one anchor step per merged finding and capped at 100.
- [ ] Demotion was applied only to P2/P3 advisory-persona findings in non-interactive modes.
- [ ] The gate ran last and suppressed findings below anchor 75 except P0 findings at anchor 50+.
- [ ] Suppressed findings are retained in a verbose/appendix tier, not deleted.
