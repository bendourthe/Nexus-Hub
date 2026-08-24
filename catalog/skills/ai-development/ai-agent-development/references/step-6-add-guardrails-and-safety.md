### Step 6: Add Guardrails and Safety

**Input Validation Layer**:

```python
@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    modified_input: str | None = None


class AgentGuardrails:
    """Safety layer wrapping agent execution."""

    def __init__(self, max_tool_calls: int = 50, max_cost_usd: float = 1.0):
        self.max_tool_calls = max_tool_calls
        self.max_cost_usd = max_cost_usd
        self.tool_call_count = 0
        self.estimated_cost = 0.0
        self.blocked_patterns = [
            r"rm\s+-rf\s+/",           # Destructive filesystem commands
            r"DROP\s+TABLE",            # SQL injection attempts
            r"curl.*\|\s*bash",         # Remote code execution
        ]

    def check_input(self, user_input: str) -> GuardrailResult:
        """Validate user input before agent processing."""
        import re
        for pattern in self.blocked_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return GuardrailResult(
                    allowed=False,
                    reason=f"Input contains blocked pattern: {pattern}"
                )
        return GuardrailResult(allowed=True)

    def check_tool_call(self, tool_name: str, arguments: dict) -> GuardrailResult:
        """Validate a tool call before execution."""
        self.tool_call_count += 1

        if self.tool_call_count > self.max_tool_calls:
            return GuardrailResult(
                allowed=False,
                reason=f"Tool call limit reached ({self.max_tool_calls})"
            )

        # Block destructive file operations outside workspace
        if tool_name in ("edit_file", "write_file", "delete_file"):
            path = arguments.get("file_path", "")
            if not path.startswith(("/workspace/", "./", "src/")):
                return GuardrailResult(
                    allowed=False,
                    reason=f"File operation outside workspace: {path}"
                )

        return GuardrailResult(allowed=True)

    def check_output(self, output: str) -> GuardrailResult:
        """Validate agent output before returning to user."""
        # Check for leaked secrets or sensitive data patterns
        import re
        sensitive_patterns = [
            r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+",
            r"sk-[a-zA-Z0-9]{20,}",
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return GuardrailResult(
                    allowed=False,
                    reason="Output may contain sensitive data. Redacting."
                )
        return GuardrailResult(allowed=True)
```
