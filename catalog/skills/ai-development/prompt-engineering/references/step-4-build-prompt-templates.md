### Step 4: Build Prompt Templates

**Template System with Variables and Conditionals**:

```python
import re
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """A reusable prompt template with variable substitution."""
    name: str
    version: str
    template: str
    required_vars: list[str] = field(default_factory=list)
    defaults: dict = field(default_factory=dict)

    def render(self, **variables) -> str:
        """Render the template with provided variables."""
        # Check required variables
        merged = {**self.defaults, **variables}
        missing = [v for v in self.required_vars if v not in merged]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        result = self.template

        # Handle conditional blocks: {{#if VAR}}...{{/if}}
        def replace_conditional(match):
            var_name = match.group(1)
            content = match.group(2)
            if merged.get(var_name):
                # Render inner content with variable substitution
                return content
            return ""

        result = re.sub(
            r"\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}",
            replace_conditional,
            result,
            flags=re.DOTALL,
        )

        # Handle simple variable substitution: {{VAR}}
        for key, value in merged.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result.strip()


# Example: Code review template
CODE_REVIEW_TEMPLATE = PromptTemplate(
    name="code-review",
    version="1.2.0",
    template="""You are a senior software engineer reviewing a code change.

## Review Focus
{{#if security_focus}}
Pay special attention to security vulnerabilities including:
- SQL injection, XSS, CSRF
- Authentication and authorization issues
- Secrets or credentials in code
{{/if}}

{{#if performance_focus}}
Pay special attention to performance including:
- N+1 queries, unnecessary allocations
- Missing indexes, inefficient algorithms
- Memory leaks, resource exhaustion
{{/if}}

## Language
The code is written in {{language}}.

## Standards
{{coding_standards}}

## Instructions
Review the following diff and provide:
1. A list of issues (critical, warning, info)
2. Specific suggestions with corrected code
3. An overall assessment

Diff:
```
{{diff}}
```""",
    required_vars=["diff", "language"],
    defaults={
        "coding_standards": "Follow language-idiomatic conventions.",
        "security_focus": False,
        "performance_focus": False,
    },
)

# Usage
prompt = CODE_REVIEW_TEMPLATE.render(
    diff=pr_diff,
    language="Python",
    security_focus=True,
)
```

**Prompt Composition (Combining Templates)**:

```python
class PromptComposer:
    """Compose complex prompts from reusable sections."""

    def __init__(self):
        self.sections: dict[str, str] = {}

    def register(self, name: str, content: str):
        self.sections[name] = content

    def compose(self, section_names: list[str], separator: str = "\n\n") -> str:
        """Combine named sections into a single prompt."""
        parts = []
        for name in section_names:
            if name not in self.sections:
                raise ValueError(f"Unknown section: {name}")
            parts.append(self.sections[name])
        return separator.join(parts)


# Register reusable prompt sections
composer = PromptComposer()

composer.register("persona_analyst", (
    "You are a data analyst specializing in business intelligence. "
    "You communicate findings clearly and support claims with data."
))

composer.register("output_json", (
    "Respond with ONLY a valid JSON object. "
    "No explanation, no markdown formatting, no code fences."
))

composer.register("output_markdown", (
    "Format your response as clean Markdown with headers, "
    "bullet points, and code blocks where appropriate."
))

composer.register("rules_concise", (
    "Rules:\n"
    "- Be concise; every sentence must add value\n"
    "- Use specific numbers and examples, not vague statements\n"
    "- If you are uncertain about a claim, say so explicitly"
))
```
