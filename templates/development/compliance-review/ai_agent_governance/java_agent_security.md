---
template_id: compliance_governance_agent_security_java
template_name: AI Agent Security - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/java_agent_lifecycle.md
  - governance_policies/java_access_control.md
related_templates:
  - ai_agent_governance/java_agent_risk_controls.md
tools:
  - Spring Security
tags:
  - security
  - least-privilege
  - four-pillars
  - java
---

# AI Agent Security - Java

**🔒 Pillar 3: Security (Least Privilege)**

Secure AI agents with least privilege and input validation

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Least Privilege**: AI agents get minimum permissions needed

**Security Controls**:
- Input validation
- Output sanitization
- Access control
- Prompt injection prevention

---

## Implementation

```java
package com.organization.ai;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.*;
import java.util.regex.*;

@Service
public class AgentSecurityService {

    private static final Logger logger = LoggerFactory.getLogger(AgentSecurityService.class);
    private static final int MAX_INPUT_LENGTH = 10000;
    private static final Pattern INJECTION_PATTERN = Pattern.compile(
        "(ignore previous|disregard|system:|<script>)", Pattern.CASE_INSENSITIVE
    );

    public String validateInput(String agentId, String userInput) {
        if (userInput == null || userInput.trim().isEmpty()) {
            throw new IllegalArgumentException("Input cannot be empty");
        }

        if (userInput.length() > MAX_INPUT_LENGTH) {
            logger.warn("Input too long: agent_id={}, length={}", agentId, userInput.length());
            throw new IllegalArgumentException("Input exceeds maximum length");
        }

        Matcher matcher = INJECTION_PATTERN.matcher(userInput);
        if (matcher.find()) {
            logger.warn("Prompt injection detected: agent_id={}, pattern={}",
                       agentId, matcher.group());
            throw new SecurityException("Potential prompt injection detected");
        }

        logger.info("Input validated: agent_id={}, input_length={}", agentId, userInput.length());
        return userInput;
    }

    public String sanitizeOutput(String agentId, String agentOutput) {
        String sanitized = agentOutput
            .replaceAll("<script.*?>.*?</script>", "")
            .replaceAll("javascript:", "")
            .replaceAll("on\\w+\\s*=", "");

        if (!sanitized.equals(agentOutput)) {
            logger.warn("Output sanitized: agent_id={}", agentId);
        }

        return sanitized;
    }

    public boolean checkAgentPermission(String agentId, String resource, String action) {
        String requiredPermission = resource + ":" + action;

        List<String> agentPermissions = getAgentPermissions(agentId);
        boolean hasPermission = agentPermissions.contains(requiredPermission);

        if (!hasPermission) {
            logger.warn("Permission denied: agent_id={}, resource={}, action={}",
                       agentId, resource, action);
        }

        return hasPermission;
    }

    private List<String> getAgentPermissions(String agentId) {
        return Arrays.asList("data:read", "api:call", "database:query");
    }
}
```

---

## Success Criteria

- [ ] Input validation implemented
- [ ] Output sanitization operational
- [ ] Prompt injection prevention active
- [ ] Least privilege enforced

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
