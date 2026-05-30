# Validator Template

The independent per-finding refutation pass run in Stage 6 (externalizing modes: autofix / report-only / headless). Its purpose is to kill plausible-but-wrong findings before they reach a human or block a merge. The validator is adversarial by design: it tries to prove the finding is NOT real. A finding that survives a genuine refutation attempt is trustworthy; one that does not is downgraded.

## Who runs it

A fresh reviewer that did NOT produce the finding (different persona, or the same persona on a clean pass with no memory of asserting it). It runs at the session model tier - refutation is high-stakes. It is read-only.

## Which findings get validated

- Every surviving finding with `requires_verification: true`, or `confidence < 100`.
- Skip `confidence: 100` findings (already proof-backed) unless the user requests full validation.
- In interactive mode the whole stage is skipped - the human is the validator.

## Prompt template

> You are independently verifying a code-review finding. Your job is to REFUTE it if you can. Default to skepticism: if you cannot substantiate the finding from the code, mark it refuted.
>
> Finding under review:
> - Title: `{title}`
> - Persona: `{persona}`  Severity: `{severity}`  Confidence: `{confidence}`
> - Location: `{file}:{line}`
> - Claim: `{suggested_fix implies the defect}`
>
> Diff base ref: `{base}`. Read the actual code at and around the location. Determine:
> 1. Does the described defect actually exist in this code, on a reachable path?
> 2. Are the preconditions the finding assumes actually satisfiable here?
> 3. Is it already handled elsewhere (guard, caller, framework) so the finding is moot?
>
> Return one JSON object:
>
> ```json
> { "verdict": "confirmed" | "refuted", "rationale": "<one sentence citing the code>", "adjusted_confidence": 0 | 25 | 50 | 75 | 100 }
> ```
>
> `confirmed` only if the defect is real and reachable. `refuted` if it does not exist, is unreachable, or is already handled. `adjusted_confidence` is your evidence-based anchor for the finding after reading the code.

## Applying the verdict

| Verdict | Action |
|---|---|
| `confirmed`, `adjusted_confidence >= 75` | Keep in the headline list; set `validation: confirmed`. |
| `confirmed`, `adjusted_confidence < 75` | Keep only if it is a `P0` at 50+ (late-gate exception); else move to appendix with `suppressed_reason: validation-downgraded`. |
| `refuted` | Move to the appendix tier; set `validation: refuted` and record the `rationale` as `suppressed_reason`. Never delete it. |

A single validator is enough for most findings. For a `P0` whose confirmation would block a merge, run two independent validators and require both to confirm (majority refute kills it) - the same adversarial-verification pattern the catalog uses elsewhere.

## Why refutation, not confirmation

Asking a validator to "check if this is right" invites agreement bias - it finds reasons the original reviewer was correct. Asking it to "refute this" forces it to look for the disconfirming evidence, which is exactly the evidence a false positive lacks. The asymmetry is the point.
