### Step 6: Evaluate Prompt Quality

**Automated Evaluation with LLM-as-Judge**:

```python
@dataclass
class PromptEvalCase:
    """A test case for prompt evaluation."""
    input_text: str
    expected_behavior: str  # Description of what a good response looks like
    tags: list[str] = field(default_factory=list)


@dataclass
class PromptEvalResult:
    case: PromptEvalCase
    output: str
    score: float  # 0.0 to 1.0
    feedback: str


def evaluate_prompt_quality(
    system_prompt: str,
    eval_cases: list[PromptEvalCase],
    model: str = "claude-sonnet-4-20250514",
) -> list[PromptEvalResult]:
    """Evaluate a system prompt against test cases using LLM-as-judge."""
    results = []

    for case in eval_cases:
        # Generate output with the prompt being tested
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": case.input_text}],
        )
        output = extract_text(response.content)

        # Judge the output
        judge_response = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    "You are evaluating an AI system's response.\n\n"
                    f"Input: {case.input_text}\n\n"
                    f"Expected behavior: {case.expected_behavior}\n\n"
                    f"Actual output:\n{output}\n\n"
                    "Score the output from 0.0 (completely wrong) to 1.0 "
                    "(perfectly matches expected behavior).\n\n"
                    'Respond with JSON: {"score": 0.X, "feedback": "..."}'
                ),
            }],
        )
        judgment = json.loads(extract_text(judge_response.content))

        results.append(PromptEvalResult(
            case=case,
            output=output,
            score=judgment["score"],
            feedback=judgment["feedback"],
        ))

    # Print summary
    avg_score = sum(r.score for r in results) / len(results)
    print(f"\nPrompt Evaluation: {avg_score:.2f} avg score ({len(results)} cases)")
    for r in results:
        status = "PASS" if r.score >= 0.7 else "FAIL"
        print(f"  [{status}] {r.case.input_text[:60]}... (score: {r.score:.2f})")
        if r.score < 0.7:
            print(f"         Feedback: {r.feedback}")

    return results
```

**Human Evaluation Rubric Template**:

```markdown
## Prompt Evaluation Rubric

### Accuracy (0-5)
- 5: All claims are correct and verifiable
- 3: Most claims are correct, minor inaccuracies
- 1: Significant factual errors
- 0: Mostly incorrect or fabricated

### Relevance (0-5)
- 5: Directly addresses the question with no tangents
- 3: Addresses the question but includes unnecessary content
- 1: Partially relevant, significant off-topic content
- 0: Does not address the question

### Format Compliance (0-5)
- 5: Perfectly matches requested output format
- 3: Mostly correct format with minor deviations
- 1: Partially correct format
- 0: Completely ignores format instructions

### Completeness (0-5)
- 5: Covers all requested aspects thoroughly
- 3: Covers most aspects, some gaps
- 1: Missing major aspects
- 0: Barely addresses the request
```
