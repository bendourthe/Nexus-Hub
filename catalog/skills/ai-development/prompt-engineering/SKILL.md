---
name: prompt-engineering
description: Prompt engineering principles and techniques for LLM applications including system prompts, chain-of-thought, few-shot learning, and prompt evaluation. Use when designing prompts, optimizing LLM outputs, or building prompt pipelines.
summary_l0: "Design, test, and optimize prompts for LLM applications with structured evaluation"
overview_l1: "This skill provides systematic techniques for designing, testing, and optimizing prompts that drive LLM-powered applications. Use it when designing system prompts, implementing chain-of-thought or structured reasoning, building few-shot learning examples, formatting LLM outputs as JSON or structured data, creating prompt templates with variable injection, evaluating prompt quality, managing prompt versions in production, or reducing token usage and API cost. Key capabilities include prompt anatomy design (system, user, assistant roles), reasoning techniques (zero-shot, few-shot, chain-of-thought, tree-of-thought), output formatting strategies, prompt evaluation scoring, version management, and token optimization. The expected output is well-structured, tested prompt templates with evaluation metrics and production deployment patterns. Trigger phrases: prompt design, system prompt, chain-of-thought, few-shot, prompt template, structured output, prompt evaluation, LLM-as-judge, prompt optimization, token reduction, output formatting, JSON mode."
---

# Prompt Engineering

Systematic techniques for designing, testing, and optimizing prompts that drive LLM-powered applications. Covers prompt anatomy, reasoning strategies, output formatting, evaluation methods, and production prompt management with real examples across classification, extraction, generation, and code tasks.

## When to Use This Skill

Use this skill for:

- Designing system prompts for LLM applications
- Implementing chain-of-thought or structured reasoning
- Building few-shot learning examples
- Formatting LLM outputs as JSON, XML, or structured data
- Creating prompt templates with variable injection
- Evaluating and scoring prompt quality
- Managing prompt versions in production
- Reducing token usage and API cost

**Trigger phrases**: "prompt design", "system prompt", "chain-of-thought", "few-shot", "prompt template", "structured output", "prompt evaluation", "LLM-as-judge", "prompt optimization", "token reduction", "output formatting", "JSON mode"

## What This Skill Does

Provides prompt engineering expertise including:

- **Prompt Anatomy**: System, user, and assistant role design
- **Reasoning Techniques**: Zero-shot, few-shot, chain-of-thought, tree-of-thought, self-consistency
- **Output Control**: JSON mode, structured output schemas, XML tagging
- **Template Systems**: Variable injection, conditional sections, prompt composition
- **Anti-Patterns**: Common mistakes and how to avoid them
- **Evaluation**: Automated scoring, human evaluation rubrics, LLM-as-judge
- **Versioning**: Prompt management, A/B testing, regression detection
- **Cost Optimization**: Token reduction, caching, model routing

## Instructions

### Step 1: Understand Prompt Anatomy

Full walkthrough: [step-1-understand-prompt-anatomy.md](references/step-1-understand-prompt-anatomy.md) (load this step when you reach it).

### Step 2: Apply Reasoning Techniques

Full walkthrough: [step-2-apply-reasoning-techniques.md](references/step-2-apply-reasoning-techniques.md) (load this step when you reach it).

### Step 3: Control Output Format

Full walkthrough: [step-3-control-output-format.md](references/step-3-control-output-format.md) (load this step when you reach it).

### Step 4: Build Prompt Templates

Full walkthrough: [step-4-build-prompt-templates.md](references/step-4-build-prompt-templates.md) (load this step when you reach it).

### Step 5: Avoid Common Anti-Patterns

Full walkthrough: [step-5-avoid-common-anti-patterns.md](references/step-5-avoid-common-anti-patterns.md) (load this step when you reach it).

### Step 6: Evaluate Prompt Quality

Full walkthrough: [step-6-evaluate-prompt-quality.md](references/step-6-evaluate-prompt-quality.md) (load this step when you reach it).

### Step 7: Manage Prompts in Production

Full walkthrough: [step-7-manage-prompts-in-production.md](references/step-7-manage-prompts-in-production.md) (load this step when you reach it).

### Step 8: Optimize Cost and Latency

Full walkthrough: [step-8-optimize-cost-and-latency.md](references/step-8-optimize-cost-and-latency.md) (load this step when you reach it).

## Research-brief authoring

Detailed guidance lives in [research-brief-authoring.md](references/research-brief-authoring.md) (load on demand).

## Effort-Level Strategy

Detailed guidance lives in [effort-level-strategy.md](references/effort-level-strategy.md) (load on demand).

## Opus 4.7 Practices

Detailed guidance lives in [opus-4-7-practices.md](references/opus-4-7-practices.md) (load on demand).

## Best Practices

- **Be specific, not verbose**: "Return a JSON object with keys: name, age, city" beats "Please provide a structured response in JSON format containing the relevant information"
- **State positive instructions**: "Respond in formal English" rather than "Don't use slang or casual language"
- **Place critical rules at the beginning and end**: The "lost-in-the-middle" effect means rules in the center of long prompts get less attention
- **Use delimiters for user input**: Triple backticks, XML tags, or clear labels prevent prompt injection
- **Test with adversarial inputs**: Try edge cases, ambiguous queries, and injection attempts
- **Version every change**: Even small prompt tweaks can shift behavior significantly; track all changes
- **Measure before optimizing**: Establish baseline eval scores before iterating on prompts
- **Match examples to distribution**: Few-shot examples should represent the real input distribution, including edge cases
- **Separate concerns**: Use prompt composition rather than monolithic prompts; each section should have one purpose
- **Cache aggressively**: System prompts that remain constant across calls are prime caching candidates

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Our prompts are simple enough that we don't need an eval suite" | Without evals, prompt changes that improve one scenario routinely degrade another; this silent regression only surfaces in production when users report failures, at which point the causal prompt change is buried in history. |
| "We'll just iterate on prompts manually until they feel right" | Manual iteration without scoring produces prompts optimized for the last test case seen; regression rates above 20% on previously working cases are common when iterating without systematic evals. |
| "Few-shot examples aren't necessary if the instruction is clear" | For tasks with subtle output format requirements (JSON with specific fields, code in a specific style), few-shot examples reduce format errors by 40-60% compared to instruction-only prompts, as documented in multiple prompting studies. |
| "Prompt injection is only a concern for chat applications" | Any prompt that incorporates user-supplied text -- including RAG retrieved content, tool outputs, or API responses -- is a prompt injection surface; a malicious document in a retrieved corpus can override system instructions. |
| "A persona belongs in product UI, so there is nothing to do until Chat settings grow a field" | A persona card in the system role or as the first kept user message is enough for a stable identity today. Waiting on a settings field delays the prompting half that already works. |
| "We don't need to version prompts because they're just strings" | Unversioned prompts make A/B testing impossible, incident root-cause analysis unreliable, and rollback manual; prompt version control is as critical as code version control for reproducibility. |
| "Token optimization is premature until cost is a problem" | At scale, a 30% token reduction compounds across millions of calls; prompts that include unnecessary context also degrade model performance by diluting signal with noise, not just by increasing cost. |

## Verification

- [ ] Eval suite exists with at least 10 test cases covering typical inputs and known edge cases
- [ ] Automated scoring function defined and baseline score recorded before any prompt change
- [ ] Few-shot examples cover at least one typical case and one edge case relevant to the task
- [ ] Prompt injection mitigations in place for any prompt that incorporates external or user-supplied text
- [ ] Prompt version stored with content hash and associated eval score in source control
- [ ] Token count measured for representative inputs and documented in the prompt header

## Related Skills

- [[ai-agent-development]] -- building agents that rely on well-designed prompts
- [[rag-implementation]] -- constructing prompts with retrieved context
- [[tool-design]] -- writing tool descriptions (a specialized form of prompting)
- [[ai-output-evaluation]] -- evaluating and scoring LLM outputs
- [[model-routing]] -- platform-aware, live-enumerated extension of the model-routing and effort-level guidance in this skill
- [[creative-generation]] -- companion/persona voice when the card is a character, not a task role

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
