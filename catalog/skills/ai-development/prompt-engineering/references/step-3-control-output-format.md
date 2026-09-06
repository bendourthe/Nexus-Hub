### Step 3: Control Output Format

**JSON Output with Schema Enforcement**:

```python
def structured_extraction(text: str, schema: dict) -> dict:
    """Extract structured data matching a JSON schema."""
    schema_str = json.dumps(schema, indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Extract information from the text to match this JSON schema:\n"
                f"```json\n{schema_str}\n```\n\n"
                f"Text:\n{text}\n\n"
                "Respond with ONLY the JSON object. No explanation, no markdown fences."
            ),
        }],
    )

    raw = extract_text(response.content).strip()
    # Strip markdown fences if model includes them despite instruction
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    return json.loads(raw)


# Example schema for meeting notes extraction
MEETING_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "attendees": {
            "type": "array",
            "items": {"type": "string"}
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": "string"},
                    "deadline": {"type": "string"}
                }
            }
        },
        "decisions": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}
```

**XML Tagging for Multi-Part Outputs**:

```python
MULTI_PART_PROMPT = """Analyze the pull request and provide feedback in the following format:

<summary>
A 1-2 sentence overview of what this PR does.
</summary>

<issues>
- [severity: critical|warning|info] Description of issue
- [severity: critical|warning|info] Description of issue
</issues>

<suggestions>
- Specific suggestion for improvement
- Specific suggestion for improvement
</suggestions>

<verdict>
APPROVE | REQUEST_CHANGES | COMMENT
</verdict>

Pull request diff:
{diff}
"""


def parse_xml_response(text: str) -> dict:
    """Parse a multi-section XML-tagged response."""
    return {
        "summary": extract_between_tags(text, "summary"),
        "issues": extract_between_tags(text, "issues"),
        "suggestions": extract_between_tags(text, "suggestions"),
        "verdict": extract_between_tags(text, "verdict").strip(),
    }


def extract_between_tags(text: str, tag: str) -> str:
    """Extract content between XML-style tags."""
    import re
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""
```
