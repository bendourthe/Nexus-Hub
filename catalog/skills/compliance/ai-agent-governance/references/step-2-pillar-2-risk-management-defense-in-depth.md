### Step 2: Pillar 2 - Risk Management (Defense in Depth)

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import re

class AgentRiskControls:
    """
    AI Agent Risk Management.

    Pillar 2: Defense in Depth
    - Multiple overlapping defense layers
    - PII detection and redaction
    - Guardrails for inputs and outputs
    - Compliance controls
    """

    SENSITIVE_DATA_PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "api_key": r"\b(sk-|pk-|api_)[A-Za-z0-9]{20,}\b"
    }

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def apply_input_guardrails(
        self,
        user_input: str,
        agent_id: str
    ) -> Dict:
        """
        Layer 1: Input Guardrails

        Validates user input before agent processing:
        - Prompt injection detection
        - Input length limits
        - Content moderation
        """
        validation_result = {
            "valid": True,
            "blocked": False,
            "warnings": [],
            "sanitized_input": user_input
        }

        # Check for prompt injection
        injection_patterns = [
            r"ignore previous instructions",
            r"disregard.*?instructions",
            r"system prompt",
            r"you are now",
            r"pretend you are",
            r"\[SYSTEM\]",
            r"<\|im_start\|>",
            r"<admin>"
        ]

        for pattern in injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                validation_result["valid"] = False
                validation_result["blocked"] = True
                validation_result["block_reason"] = "prompt_injection_detected"

                audit_log.warning(
                    "guardrail_input_blocked",
                    agent_id=agent_id,
                    reason="prompt_injection",
                    pattern=pattern
                )

                return validation_result

        # Input length check (prevent resource exhaustion)
        if len(user_input) > 50000:
            validation_result["valid"] = False
            validation_result["blocked"] = True
            validation_result["block_reason"] = "input_too_long"
            return validation_result

        return validation_result

    def detect_and_redact_pii(
        self,
        text: str,
        context: str = "input"
    ) -> Dict:
        """
        Layer 2: PII Detection and Redaction

        Uses Microsoft Presidio for:
        - Pattern-based detection (SSN, credit cards, emails)
        - NER-based detection (names, addresses)
        - Automatic redaction
        """
        # Detect PII
        results = self.analyzer.analyze(
            text=text,
            language='en',
            entities=[
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
                "CREDIT_CARD", "US_SSN", "US_PASSPORT",
                "IP_ADDRESS", "MEDICAL_LICENSE"
            ]
        )

        pii_found = len(results) > 0

        if pii_found:
            # Redact PII
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )

            audit_log.warning(
                "pii_detected_and_redacted",
                context=context,
                pii_types=[r.entity_type for r in results],
                pii_count=len(results)
            )

            return {
                "pii_found": True,
                "pii_types": [r.entity_type for r in results],
                "original_text": text,
                "redacted_text": anonymized.text
            }

        return {
            "pii_found": False,
            "redacted_text": text
        }

    def apply_output_guardrails(
        self,
        agent_output: str,
        agent_id: str
    ) -> Dict:
        """
        Layer 3: Output Guardrails

        Validates agent output before returning to user:
        - PII redaction
        - Harmful content filtering
        - Prompt leakage prevention
        """
        result = {
            "safe": True,
            "modified": False,
            "sanitized_output": agent_output
        }

        # Check for PII in output
        pii_result = self.detect_and_redact_pii(agent_output, context="output")
        if pii_result["pii_found"]:
            result["modified"] = True
            result["sanitized_output"] = pii_result["redacted_text"]

        # Check for prompt leakage
        if self._detect_prompt_leakage(agent_output):
            result["safe"] = False
            result["blocked"] = True
            result["block_reason"] = "prompt_leakage"

            audit_log.warning(
                "guardrail_output_blocked",
                agent_id=agent_id,
                reason="prompt_leakage"
            )

        # Check for harmful content
        harmful_patterns = [
            r"how to hack",
            r"how to steal",
            r"illegal instructions",
            r"bypass security"
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, agent_output, re.IGNORECASE):
                result["safe"] = False
                result["blocked"] = True
                result["block_reason"] = "harmful_content"

        return result

    def apply_tool_guardrails(
        self,
        agent_id: str,
        tool_name: str,
        tool_input: Dict,
        user_context: Dict
    ) -> Dict:
        """
        Layer 4: Tool Use Guardrails

        Controls what tools agent can use:
        - Tool allowlist per agent
        - Sensitive operation approval
        - Rate limiting
        """
        # Get agent's allowed tools
        allowed_tools = self._get_allowed_tools(agent_id)

        if tool_name not in allowed_tools:
            audit_log.warning(
                "tool_access_denied",
                agent_id=agent_id,
                tool_name=tool_name,
                reason="not_in_allowlist"
            )

            return {
                "allowed": False,
                "reason": f"Tool '{tool_name}' not in agent's allowlist"
            }

        # Check for sensitive operations requiring approval
        sensitive_operations = ["delete", "update", "transfer", "execute"]

        if any(op in tool_name.lower() for op in sensitive_operations):
            if not self._has_human_approval(agent_id, tool_name, tool_input):
                return {
                    "allowed": False,
                    "reason": "sensitive_operation_requires_approval",
                    "approval_required": True
                }

        # Rate limiting
        if self._is_rate_limited(agent_id, tool_name):
            return {
                "allowed": False,
                "reason": "rate_limit_exceeded"
            }

        return {"allowed": True}
```
