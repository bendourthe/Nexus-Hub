---
template_id: compliance_governance_agent_security_javascript
template_name: AI Agent Security - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/javascript_agent_lifecycle.md
  - governance_policies/javascript_access_control.md
related_templates:
  - compliance_frameworks/javascript_nist_ai_rmf.md
  - ai_agent_governance/javascript_agent_observability.md
tools:
  - helmet (security headers)
tags:
  - ai-security
  - prompt-injection
  - four-pillars
  - least-privilege
  - javascript
  - nodejs
---

# AI Agent Security - JavaScript

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

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'agent-security.log' })
  ]
});

class AgentSecurity {
  /**
   * AI Agent security controls.
   *
   * 4 Pillars: Security (Least Privilege)
   * Compliance: NIST AI RMF, GenAI Profile
   */

  constructor() {
    // Dangerous patterns in prompts
    this.INJECTION_PATTERNS = [
      /ignore previous instructions/i,
      /disregard.*?instructions/i,
      /system prompt/i,
      /you are now/i,
      /pretend you are/i,
      /\[SYSTEM\]/i,
      /sudo/i,
      /<admin>/i
    ];
  }

  /**
   * Validate user input for prompt injection attempts.
   *
   * NIST GenAI Profile: Information Security risk
   */
  validatePrompt(userInput, agentId) {
    // Check for injection patterns
    let injectionDetected = false;
    const matchedPatterns = [];

    for (const pattern of this.INJECTION_PATTERNS) {
      if (pattern.test(userInput)) {
        injectionDetected = true;
        matchedPatterns.push(pattern.source);
      }
    }

    if (injectionDetected) {
      logger.warn('Prompt injection detected', {
        event: 'prompt_injection_detected',
        agentId,
        matchedPatterns,
        inputPreview: userInput.substring(0, 100),
        timestamp: new Date().toISOString()
      });

      return {
        valid: false,
        reason: 'potential_injection',
        matchedPatterns
      };
    }

    // Check input length (prevent resource exhaustion)
    if (userInput.length > 10000) {
      return { valid: false, reason: 'input_too_long' };
    }

    return { valid: true };
  }

  /**
   * Enforce least privilege for AI agents.
   *
   * Pillar 3: Security (Least Privilege)
   */
  async enforceAgentPermissions(agentId, requestedAction, targetResource) {
    const agent = await db.collection('ai_agents').findOne({ agentId });

    // Get agent's allowed actions
    const allowedActions = agent.allowedActions || [];

    const hasPermission = allowedActions.includes(requestedAction);

    logger.info('Agent permission check', {
      event: 'permission_check',
      agentId,
      action: requestedAction,
      resource: targetResource,
      granted: hasPermission,
      timestamp: new Date().toISOString()
    });

    if (!hasPermission) {
      throw new Error(`Agent not authorized for action: ${requestedAction}`);
    }

    return true;
  }

  /**
   * Sanitize AI agent output.
   *
   * Prevents:
   * - PII leakage
   * - Prompt leakage
   * - Harmful content
   */
  sanitizeAgentOutput(output) {
    // Basic PII redaction (production: use dedicated library)
    const piiPatterns = [
      { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN-REDACTED]' },
      { pattern: /\b\d{16}\b/g, replacement: '[CARD-REDACTED]' },
      { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL-REDACTED]' }
    ];

    let sanitized = output;

    for (const { pattern, replacement } of piiPatterns) {
      sanitized = sanitized.replace(pattern, replacement);
    }

    return sanitized;
  }

  /**
   * Implement guardrails for AI agent.
   *
   * Guardrails: Rules preventing unsafe agent behavior
   */
  async implementAgentGuardrails(agentId, guardrails) {
    await db.collection('ai_agents').updateOne(
      { agentId },
      { $set: { guardrails } }
    );

    logger.info('Guardrails implemented', {
      event: 'guardrails_implemented',
      agentId,
      guardrailCount: guardrails.length,
      timestamp: new Date().toISOString()
    });
  }
}

module.exports = AgentSecurity;
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
