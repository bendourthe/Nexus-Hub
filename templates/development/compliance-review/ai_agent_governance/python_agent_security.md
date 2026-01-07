---
template_id: compliance_governance_agent_security_python
template_name: AI Agent Security - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/python_agent_lifecycle.md
  - governance_policies/python_access_control.md
related_templates:
  - compliance_frameworks/python_nist_ai_rmf.md
  - ai_agent_governance/python_agent_observability.md
tools:
  - promptinject (prompt injection detection)
  - llm-guard (LLM security)
tags:
  - ai-security
  - prompt-injection
  - four-pillars
  - least-privilege
  - python
---

# AI Agent Security - Python

**🔒 Pillar 3: Security (Least Privilege)**

Implement security controls for AI agents including prompt injection prevention

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### AI-Specific Security Threats

**GenAI Risks** (NIST AI RMF Generative AI Profile):
- Prompt injection
- Jailbreaking
- Training data poisoning
- Model extraction
- Adversarial examples

### Security Principle

**Least Privilege**: AI agents get minimum permissions needed

---

## Implementation

```python
# AI Agent security controls
from typing import Dict, List
import re

class AgentSecurity:
    """
    AI Agent security controls.

    4 Pillars: Security (Least Privilege)
    Compliance: NIST AI RMF, GenAI Profile
    """

    # Dangerous patterns in prompts
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"disregard.*?instructions",
        r"system prompt",
        r"you are now",
        r"pretend you are",
        r"\[SYSTEM\]",
        r"sudo",
        r"<admin>",
    ]

    def validate_prompt(self, user_input: str, agent_id: str) -> Dict:
        """
        Validate user input for prompt injection attempts.

        NIST GenAI Profile: Information Security risk
        """
        # Check for injection patterns
        injection_detected = False
        matched_patterns = []

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                injection_detected = True
                matched_patterns.append(pattern)

        if injection_detected:
            logger.warning("Prompt injection detected", extra={
                "agent_id": agent_id,
                "matched_patterns": matched_patterns,
                "input_preview": user_input[:100]
            })

            return {
                "valid": False,
                "reason": "potential_injection",
                "matched_patterns": matched_patterns
            }

        # Check input length (prevent resource exhaustion)
        if len(user_input) > 10000:
            return {"valid": False, "reason": "input_too_long"}

        return {"valid": True}

    def enforce_agent_permissions(
        self,
        agent_id: str,
        requested_action: str,
        target_resource: str
    ) -> bool:
        """
        Enforce least privilege for AI agents.

        Pillar 3: Security (Least Privilege)
        """
        agent = db.ai_agents.find_one({"agent_id": agent_id})

        # Get agent's allowed actions
        allowed_actions = agent.get("allowed_actions", [])

        has_permission = requested_action in allowed_actions

        logger.info("Agent permission check", extra={
            "agent_id": agent_id,
            "action": requested_action,
            "resource": target_resource,
            "granted": has_permission
        })

        if not has_permission:
            raise PermissionError(f"Agent not authorized for action: {requested_action}")

        return True

    def sanitize_agent_output(self, output: str) -> str:
        """
        Sanitize AI agent output.

        Prevents:
        - PII leakage
        - Prompt leakage
        - Harmful content
        """
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        # Redact PII
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        results = analyzer.analyze(text=output, language='en')
        sanitized = anonymizer.anonymize(text=output, analyzer_results=results)

        return sanitized.text

    def implement_agent_guardrails(self, agent_id: str, guardrails: List[Dict]):
        """
        Implement guardrails for AI agent.

        Guardrails: Rules preventing unsafe agent behavior
        """
        db.ai_agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"guardrails": guardrails}}
        )

        logger.info("Guardrails implemented", extra={
            "agent_id": agent_id,
            "guardrail_count": len(guardrails)
        })
```

---

## Success Criteria

- [ ] Prompt injection detection operational
- [ ] Agent permissions enforced (least privilege)
- [ ] Output sanitization implemented
- [ ] Guardrails defined for all production agents
- [ ] Security monitoring integrated

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
