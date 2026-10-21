# Decision-Policy Harness for Agent Tool Calls

Summary: how an agent harness decides whether a proposed tool call runs, by splitting scoring from a pure policy function, using two thresholds for allow, ask, or block, declaring each component's failure direction, and treating tool arguments as untrusted data.
Read this when: building or reviewing the gate an agent harness puts in front of its own tool calls (shell, file writes, network, external actions).
Covers: the scorer and policy split, the allow / ask / block band, failure directions, untrusted arguments, the decision record, and handoffs to the skills that own the neighbouring rules.

This reference teaches only the decision mechanics of a tool-call gate. For guardrail design in general, start with [step-6-add-guardrails-and-safety.md](step-6-add-guardrails-and-safety.md).

## Scorer, then policy

Keep two components apart:

- **A scorer returns numbers.** It looks at the proposed call (tool name, arguments, context) and returns one or more scores, for example a risk score per concern. It decides nothing.
- **A pure policy function returns the verdict.** It takes the scores plus the deterministic facts about the call and returns allow, ask, or block, with the rule that matched. Being pure, it can be tested exhaustively with no model in the loop.

```python
def decide(scores: dict[str, float], deterministic: str | None, ask_at: float, block_at: float) -> tuple[str, str]:
    """Illustrative only: a deterministic verdict wins; otherwise the highest score picks the band."""
    if deterministic is not None:
        return deterministic, "deterministic"
    concern, worst = max(scores.items(), key=lambda item: item[1], default=("none", 0.0))
    if worst >= block_at:
        return "block", concern
    if worst >= ask_at:
        return "ask", concern
    return "allow", concern
```

## The allow / ask / block band

Two thresholds give three verdicts. A score below the ask threshold allows the call, a score at or above it asks a person, and a score at or above the block threshold blocks. When several concerns are scored, the highest score decides, so one alarming concern is never averaged away by several calm ones. Set the thresholds from labelled examples of your own calls, not from a default.

## Failure directions

Every component declares what happens when it fails: a timeout, a crash, an unparseable input. A tool gate fails closed: when the scorer cannot run or the policy cannot decide, the call is asked or blocked, never allowed. A component that fails open must say so in its contract and must not sit in front of a destructive or outward-facing tool.

## Tool arguments are untrusted data

The agent produced the arguments after it read content it does not control (web pages, files, tool output), so the arguments may carry instructions planted in that content. Treat them as data:

- A model-based scorer receives the arguments clearly delimited as data, never as instructions.
- No score may lower a deterministic verdict. A deterministic block (a denied path, a forbidden command) stays a block whatever a model scores; a model can only raise caution.

The defence posture behind this is owned by [[prompt-injection-defense]].

## The decision record

Each decision writes a record of the tool name, a hash and the length of each argument, the scores, the verdict, and the matched rule. It never stores raw file contents or command bodies. Redact the record before it is written, as [[egress-redaction]] defines, because a record that stores what it judged leaks exactly the material the gate was protecting.

## Handoffs

- Run deterministic checks before any scored check, as [[minimal-construction]] and the review pre-pass of the not-yet-landed `v4.17.1` plan own.
- Accepting a cheap judge's verdict only above a validated threshold is owned by [[ai-output-evaluation]] (its judge cascade arrives with `v4.16.0` T025), and it never applies to a permission decision.
- Complete-and-distinct option sets for the ask path belong to the owner that `v4.16.0` T002 chooses.
- Which model runs a model-based scorer is owned by [[model-routing]].
- The cache cost of calling a scorer model on every tool call is owned by `prompt-engineering`'s [step-8-optimize-cost-and-latency.md](../../prompt-engineering/references/step-8-optimize-cost-and-latency.md).

The scorer may be a local model or a heuristic. A hosted per-call scoring service is out of scope: it would send every tool call, arguments included, to a third party.
