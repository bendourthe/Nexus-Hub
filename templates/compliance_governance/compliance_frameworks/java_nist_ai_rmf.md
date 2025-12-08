---
template_id: compliance_governance_nist_ai_rmf_java
template_name: NIST AI RMF - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/java_iso27001_implementation.md
related_templates:
  - ai_agent_governance/java_agent_lifecycle.md
tools:
  - anthropic-sdk-java (LLM API)
tags:
  - nist-ai-rmf
  - ai-governance
  - genai
  - java
  - spring-boot
---

# NIST AI RMF 1.0 - Java

**AI Risk Management Framework + Generative AI Profile**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### NIST AI RMF Structure

**4 Core Functions**: GOVERN, MAP, MEASURE, MANAGE

---

## GOVERN Function

```java
package com.company.compliance.ai;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.UUID;

/**
 * AI Governance Manager.
 *
 * NIST AI RMF GOVERN 1.1: AI system inventory
 */
@Service
public class AIGovernanceManager {
    private static final Logger logger = LoggerFactory.getLogger(AIGovernanceManager.class);

    public enum AISystemType {
        GENERATIVE, PREDICTIVE, DECISION_SUPPORT, AUTONOMOUS
    }

    public enum RiskTier {
        MINIMAL, LIMITED, HIGH, UNACCEPTABLE
    }

    /**
     * Register AI system in inventory.
     */
    public String registerAISystem(String systemName, AISystemType systemType,
                                  String useCase, ImpactAssessment impactAssessment,
                                  boolean isGenerative) {
        String systemId = UUID.randomUUID().toString();
        RiskTier riskLevel = calculateRiskLevel(impactAssessment);

        logger.info("AI system registered: systemId={}, name={}, type={}, " +
                   "riskLevel={}, isGenerative={}, timestamp={}",
            systemId, systemName, systemType, riskLevel, isGenerative, Instant.now());

        if (isGenerative) {
            initiateGenerativeAIReview(systemId);
        }

        return systemId;
    }

    private RiskTier calculateRiskLevel(ImpactAssessment assessment) {
        int score = 0;

        if (assessment.isSafetyCritical()) score += 4;
        if (assessment.isPersonalDataProcessing()) score += 3;
        if (assessment.isLegalConsequences()) score += 3;

        if (score >= 10) return RiskTier.UNACCEPTABLE;
        if (score >= 6) return RiskTier.HIGH;
        if (score >= 3) return RiskTier.LIMITED;
        return RiskTier.MINIMAL;
    }

    private void initiateGenerativeAIReview(String systemId) {
        logger.warn("Generative AI review initiated: systemId={}", systemId);
    }

    public static class ImpactAssessment {
        private boolean safetyCritical;
        private boolean personalDataProcessing;
        private boolean legalConsequences;

        public boolean isSafetyCritical() { return safetyCritical; }
        public boolean isPersonalDataProcessing() { return personalDataProcessing; }
        public boolean isLegalConsequences() { return legalConsequences; }

        public void setSafetyCritical(boolean safetyCritical) {
            this.safetyCritical = safetyCritical;
        }
        public void setPersonalDataProcessing(boolean personalDataProcessing) {
            this.personalDataProcessing = personalDataProcessing;
        }
        public void setLegalConsequences(boolean legalConsequences) {
            this.legalConsequences = legalConsequences;
        }
    }
}
```

---

## Success Criteria

- [ ] All AI systems registered in inventory
- [ ] Risk tier assigned to each system
- [ ] Generative AI systems undergo additional review
- [ ] Context and intended use documented

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
