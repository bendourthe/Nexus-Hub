---
template_id: compliance_governance_nist_ai_rmf_javascript
template_name: NIST AI RMF - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - ai_agent_governance/javascript_agent_lifecycle.md
  - ai_agent_governance/javascript_agent_risk_controls.md
tools:
  - openai (LLM API)
  - @anthropic-ai/sdk (Claude API)
tags:
  - nist-ai-rmf
  - ai-governance
  - genai
  - javascript
  - nodejs
---

# NIST AI RMF 1.0 - JavaScript

**AI Risk Management Framework + Generative AI Profile (July 2024)**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### NIST AI RMF Structure

**4 Core Functions**:
1. **GOVERN** - Organizational structures and policies
2. **MAP** - Context and impact assessment
3. **MEASURE** - Testing and evaluation
4. **MANAGE** - Risk response and monitoring

**Generative AI Profile** (July 2024): 12 GenAI-specific risks

---

## GOVERN Function

### GOVERN 1.1: AI Risk Management Strategy

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'ai-governance.log' })
  ]
});

const AISystemType = {
  GENERATIVE: 'generative',
  PREDICTIVE: 'predictive',
  DECISION_SUPPORT: 'decision_support',
  AUTONOMOUS: 'autonomous'
};

const RiskTier = {
  MINIMAL: 'minimal',
  LIMITED: 'limited',
  HIGH: 'high',
  UNACCEPTABLE: 'unacceptable'
};

class AIGovernanceManager {
  /**
   * Register AI system in inventory.
   *
   * NIST AI RMF GOVERN 1.1: AI system inventory
   */
  async registerAISystem(systemName, systemType, useCase, impactAssessment, isGenerative = false) {
    const systemId = uuidv4();
    const riskLevel = this.calculateRiskLevel(impactAssessment);

    const systemRecord = {
      systemId,
      systemName,
      systemType,
      useCase,
      isGenerative,
      riskLevel,
      impactAssessment,

      // Governance tracking
      capabilitiesDocumented: false,
      biasEvaluationCompleted: false,
      securityReviewCompleted: false,
      approvedForProduction: false,

      // Lifecycle
      registeredAt: new Date(),
      registeredBy: 'system',
      status: 'development'
    };

    await db.collection('ai_systems').insertOne(systemRecord);

    logger.info('AI system registered', {
      event: 'ai_system_registered',
      systemId,
      systemName,
      systemType,
      riskLevel,
      isGenerative,
      timestamp: new Date().toISOString()
    });

    // Generative AI requires additional governance
    if (isGenerative) {
      await this.initiateGenerativeAIReview(systemId);
    }

    return { systemId, riskLevel };
  }

  /**
   * Calculate risk tier based on impact assessment.
   *
   * NIST AI RMF GOVERN 1.2: Risk tiering
   */
  calculateRiskLevel(impactAssessment) {
    const {
      safetyCritical,
      personalDataProcessing,
      legalConsequences,
      financialImpact,
      reputationalRisk
    } = impactAssessment;

    let score = 0;

    if (safetyCritical) score += 4;
    if (personalDataProcessing) score += 3;
    if (legalConsequences) score += 3;
    if (financialImpact > 1000000) score += 2;
    if (reputationalRisk === 'high') score += 2;

    if (score >= 10) return RiskTier.UNACCEPTABLE;
    if (score >= 6) return RiskTier.HIGH;
    if (score >= 3) return RiskTier.LIMITED;
    return RiskTier.MINIMAL;
  }

  /**
   * Initiate Generative AI governance review.
   *
   * NIST GenAI Profile: Additional requirements for GenAI
   */
  async initiateGenerativeAIReview(systemId) {
    const reviewId = uuidv4();

    const genAIReviewChecklist = {
      reviewId,
      systemId,
      initiatedAt: new Date(),

      // GenAI-specific risks to assess
      risks: {
        confabulation: { assessed: false, mitigation: null },
        toxicContent: { assessed: false, mitigation: null },
        dataPoisoning: { assessed: false, mitigation: null },
        promptInjection: { assessed: false, mitigation: null },
        intellectualProperty: { assessed: false, mitigation: null },
        privacyLeakage: { assessed: false, mitigation: null }
      },

      status: 'pending'
    };

    await db.collection('genai_reviews').insertOne(genAIReviewChecklist);

    logger.warn('Generative AI review initiated', {
      event: 'genai_review_initiated',
      reviewId,
      systemId
    });

    return reviewId;
  }
}

module.exports = AIGovernanceManager;
```

---

## MAP Function

### MAP 1.1: Context Mapping

```javascript
class AIContextMapper {
  /**
   * Document AI system context and intended use.
   *
   * NIST AI RMF MAP 1.1: Context documentation
   */
  async documentSystemContext(systemId, contextData) {
    const {
      intendedUse,
      targetUsers,
      operationalEnvironment,
      dataCharacteristics,
      externalDependencies
    } = contextData;

    const contextDoc = {
      contextId: uuidv4(),
      systemId,
      intendedUse,
      targetUsers,
      operationalEnvironment,
      dataCharacteristics,
      externalDependencies,
      documentedAt: new Date(),
      documentedBy: contextData.documentedBy
    };

    await db.collection('ai_context_docs').insertOne(contextDoc);

    logger.info('AI system context documented', {
      event: 'context_documented',
      systemId,
      contextId: contextDoc.contextId
    });

    return contextDoc.contextId;
  }

  /**
   * Assess stakeholder impacts.
   *
   * NIST AI RMF MAP 1.2: Stakeholder impact analysis
   */
  async assessStakeholderImpacts(systemId, stakeholders) {
    const impacts = [];

    for (const stakeholder of stakeholders) {
      const impact = {
        stakeholderType: stakeholder.type,
        positiveImpacts: stakeholder.positiveImpacts || [],
        negativeImpacts: stakeholder.negativeImpacts || [],
        riskLevel: this.assessStakeholderRisk(stakeholder.negativeImpacts),
        mitigationRequired: stakeholder.negativeImpacts.length > 0
      };

      impacts.push(impact);
    }

    await db.collection('ai_systems').updateOne(
      { systemId },
      {
        $set: {
          stakeholderImpacts: impacts,
          impactAssessmentDate: new Date()
        }
      }
    );

    logger.info('Stakeholder impacts assessed', {
      event: 'stakeholder_impacts_assessed',
      systemId,
      impactCount: impacts.length
    });

    return impacts;
  }

  assessStakeholderRisk(negativeImpacts) {
    if (negativeImpacts.some(i => i.severity === 'critical')) return 'high';
    if (negativeImpacts.some(i => i.severity === 'high')) return 'medium';
    return 'low';
  }
}

module.exports = AIContextMapper;
```

---

## MEASURE Function

### MEASURE 2.7: AI System Performance

```javascript
class AIPerformanceMonitoring {
  /**
   * Monitor AI system performance metrics.
   *
   * NIST AI RMF MEASURE 2.7: Performance monitoring
   */
  async monitorPerformance(systemId, predictions, groundTruth) {
    const metrics = {
      systemId,
      timestamp: new Date(),

      // Classification metrics
      accuracy: this.calculateAccuracy(predictions, groundTruth),
      precision: this.calculatePrecision(predictions, groundTruth),
      recall: this.calculateRecall(predictions, groundTruth),
      f1Score: null
    };

    // Calculate F1 score
    if (metrics.precision > 0 || metrics.recall > 0) {
      metrics.f1Score = 2 * (metrics.precision * metrics.recall) /
                        (metrics.precision + metrics.recall);
    }

    await db.collection('ai_performance_metrics').insertOne(metrics);

    // Check for performance degradation
    const performanceDrift = await this.detectPerformanceDrift(systemId, metrics);

    if (performanceDrift) {
      logger.warn('AI performance degradation detected', {
        event: 'performance_drift',
        systemId,
        metrics,
        driftDetails: performanceDrift
      });

      await this.createPerformanceAlert(systemId, performanceDrift);
    }

    return metrics;
  }

  calculateAccuracy(predictions, groundTruth) {
    const correct = predictions.filter((pred, idx) => pred === groundTruth[idx]).length;
    return correct / predictions.length;
  }

  calculatePrecision(predictions, groundTruth) {
    const truePositives = predictions.filter((pred, idx) =>
      pred === 1 && groundTruth[idx] === 1
    ).length;

    const falsePositives = predictions.filter((pred, idx) =>
      pred === 1 && groundTruth[idx] === 0
    ).length;

    return truePositives / (truePositives + falsePositives) || 0;
  }

  calculateRecall(predictions, groundTruth) {
    const truePositives = predictions.filter((pred, idx) =>
      pred === 1 && groundTruth[idx] === 1
    ).length;

    const falseNegatives = predictions.filter((pred, idx) =>
      pred === 0 && groundTruth[idx] === 1
    ).length;

    return truePositives / (truePositives + falseNegatives) || 0;
  }

  /**
   * Detect performance drift over time.
   *
   * NIST AI RMF MEASURE 2.8: Drift detection
   */
  async detectPerformanceDrift(systemId, currentMetrics) {
    const historicalMetrics = await db.collection('ai_performance_metrics')
      .find({ systemId })
      .sort({ timestamp: -1 })
      .limit(30)
      .toArray();

    if (historicalMetrics.length < 10) {
      return null; // Need baseline
    }

    const baselineAccuracy = historicalMetrics
      .slice(0, 10)
      .reduce((sum, m) => sum + m.accuracy, 0) / 10;

    const accuracyDrop = baselineAccuracy - currentMetrics.accuracy;

    // Alert if accuracy drops by more than 5%
    if (accuracyDrop > 0.05) {
      return {
        driftType: 'performance_degradation',
        baselineAccuracy,
        currentAccuracy: currentMetrics.accuracy,
        degradationPercent: (accuracyDrop * 100).toFixed(2)
      };
    }

    return null;
  }

  async createPerformanceAlert(systemId, driftDetails) {
    const alertId = uuidv4();

    await db.collection('ai_alerts').insertOne({
      alertId,
      systemId,
      alertType: 'performance_drift',
      severity: 'high',
      details: driftDetails,
      createdAt: new Date(),
      status: 'open'
    });

    return alertId;
  }
}

module.exports = AIPerformanceMonitoring;
```

### MEASURE 3.1: Bias Evaluation

```javascript
class AIBiasEvaluator {
  /**
   * Evaluate AI system for bias across protected groups.
   *
   * NIST AI RMF MEASURE 3.1: Bias testing
   */
  async evaluateBias(systemId, predictions, groundTruth, sensitiveFeatures) {
    const biasMetrics = {};

    // Evaluate for each sensitive attribute
    for (const [attribute, values] of Object.entries(sensitiveFeatures)) {
      const groups = [...new Set(values)];
      const groupMetrics = {};

      for (const group of groups) {
        const groupIndices = values
          .map((val, idx) => val === group ? idx : -1)
          .filter(idx => idx !== -1);

        const groupPredictions = groupIndices.map(idx => predictions[idx]);
        const groupGroundTruth = groupIndices.map(idx => groundTruth[idx]);

        groupMetrics[group] = {
          accuracy: this.calculateAccuracy(groupPredictions, groupGroundTruth),
          positiveRate: groupPredictions.filter(p => p === 1).length / groupPredictions.length
        };
      }

      // Calculate disparate impact
      const disparateImpact = this.calculateDisparateImpact(groupMetrics);

      biasMetrics[attribute] = {
        groupMetrics,
        disparateImpact,
        biasDetected: Math.abs(disparateImpact - 1.0) > 0.2 // 80% rule
      };
    }

    await db.collection('ai_bias_evaluations').insertOne({
      evaluationId: uuidv4(),
      systemId,
      biasMetrics,
      evaluatedAt: new Date()
    });

    // Check for bias violations
    const biasViolations = Object.entries(biasMetrics)
      .filter(([_, metrics]) => metrics.biasDetected);

    if (biasViolations.length > 0) {
      logger.warn('Bias detected in AI system', {
        event: 'bias_detected',
        systemId,
        violations: biasViolations.map(([attr, _]) => attr)
      });

      await this.createBiasIncident(systemId, biasViolations);
    }

    return biasMetrics;
  }

  calculateAccuracy(predictions, groundTruth) {
    const correct = predictions.filter((pred, idx) => pred === groundTruth[idx]).length;
    return correct / predictions.length;
  }

  /**
   * Calculate disparate impact ratio.
   *
   * 80% rule: Ratio should be >= 0.8
   */
  calculateDisparateImpact(groupMetrics) {
    const groups = Object.values(groupMetrics);
    const positiveRates = groups.map(g => g.positiveRate);

    const minRate = Math.min(...positiveRates);
    const maxRate = Math.max(...positiveRates);

    return minRate / maxRate;
  }

  async createBiasIncident(systemId, biasViolations) {
    const incidentId = uuidv4();

    await db.collection('ai_incidents').insertOne({
      incidentId,
      systemId,
      incidentType: 'bias_violation',
      severity: 'high',
      details: {
        violations: biasViolations
      },
      createdAt: new Date(),
      status: 'open',
      requiresRemediation: true
    });

    return incidentId;
  }
}

module.exports = AIBiasEvaluator;
```

---

## MANAGE Function

### MANAGE 2.3: Risk Response

```javascript
class AIRiskManager {
  /**
   * Document risk response strategies.
   *
   * NIST AI RMF MANAGE 2.3: Risk treatment
   */
  async documentRiskResponse(systemId, risk, responseStrategy) {
    const responseId = uuidv4();

    const riskResponse = {
      responseId,
      systemId,
      riskId: risk.riskId,
      riskDescription: risk.description,
      riskLevel: risk.level,

      // Response strategy
      strategy: responseStrategy.type, // 'mitigate' | 'accept' | 'transfer' | 'avoid'
      mitigationActions: responseStrategy.actions || [],
      residualRisk: responseStrategy.residualRisk,

      // Accountability
      ownerUserId: responseStrategy.owner,
      reviewDate: responseStrategy.reviewDate,

      documentedAt: new Date(),
      status: 'active'
    };

    await db.collection('ai_risk_responses').insertOne(riskResponse);

    logger.info('Risk response documented', {
      event: 'risk_response_documented',
      responseId,
      systemId,
      riskLevel: risk.level,
      strategy: responseStrategy.type
    });

    return responseId;
  }

  /**
   * Track risk response implementation.
   *
   * NIST AI RMF MANAGE 2.4: Risk monitoring
   */
  async trackResponseImplementation(responseId, progress) {
    await db.collection('ai_risk_responses').updateOne(
      { responseId },
      {
        $set: {
          implementationProgress: progress.percentComplete,
          lastUpdated: new Date(),
          completedActions: progress.completedActions
        }
      }
    );

    logger.info('Risk response progress updated', {
      event: 'risk_response_progress',
      responseId,
      progress: progress.percentComplete
    });
  }
}

module.exports = AIRiskManager;
```

---

## Generative AI Profile Implementation

### CONFABULATION Risk

```javascript
const Anthropic = require('@anthropic-ai/sdk');

class GenerativeAIRiskControls {
  constructor() {
    this.anthropic = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY
    });
  }

  /**
   * Detect hallucinations/confabulation in LLM outputs.
   *
   * NIST GenAI Profile: Confabulation risk
   */
  async detectConfabulation(generatedText, sourceDocuments, systemId) {
    // Use NLI (Natural Language Inference) to check consistency
    const consistencyScore = await this.checkFactualConsistency(
      generatedText,
      sourceDocuments
    );

    const confabulationDetected = consistencyScore < 0.7;

    if (confabulationDetected) {
      logger.warn('Confabulation detected in LLM output', {
        event: 'confabulation_detected',
        systemId,
        consistencyScore,
        outputPreview: generatedText.substring(0, 100)
      });

      await this.createGenAIIncident(systemId, 'confabulation', {
        consistencyScore,
        outputLength: generatedText.length
      });
    }

    return {
      confabulationDetected,
      consistencyScore
    };
  }

  /**
   * Check factual consistency with source documents.
   */
  async checkFactualConsistency(generatedText, sourceDocuments) {
    // Use Claude to assess factual consistency
    const prompt = `
You are evaluating whether generated text is factually consistent with source documents.

SOURCE DOCUMENTS:
${sourceDocuments.join('\n\n')}

GENERATED TEXT:
${generatedText}

Respond with ONLY a JSON object:
{
  "consistent": true/false,
  "confidence": 0.0-1.0,
  "inconsistencies": ["list any factual errors or hallucinations"]
}
`;

    const message = await this.anthropic.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 500,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const result = JSON.parse(message.content[0].text);

    return result.consistent ? result.confidence : 0.0;
  }

  /**
   * Detect toxic/harmful content in LLM outputs.
   *
   * NIST GenAI Profile: Toxic content risk
   */
  async detectToxicContent(generatedText, systemId) {
    const toxicityScore = await this.assessToxicity(generatedText);

    const toxicContentDetected = toxicityScore > 0.6;

    if (toxicContentDetected) {
      logger.warn('Toxic content detected', {
        event: 'toxic_content_detected',
        systemId,
        toxicityScore
      });

      await this.createGenAIIncident(systemId, 'toxic_content', {
        toxicityScore
      });
    }

    return {
      toxicContentDetected,
      toxicityScore
    };
  }

  async assessToxicity(text) {
    // Integration with toxicity detection API
    // Placeholder implementation
    return 0.1;
  }

  async createGenAIIncident(systemId, incidentType, details) {
    const incidentId = uuidv4();

    await db.collection('genai_incidents').insertOne({
      incidentId,
      systemId,
      incidentType,
      details,
      createdAt: new Date(),
      status: 'open'
    });

    return incidentId;
  }
}

module.exports = GenerativeAIRiskControls;
```

---

## Success Criteria

- [ ] All AI systems registered in inventory
- [ ] Risk tier assigned to each system
- [ ] Generative AI systems undergo additional review
- [ ] Context and intended use documented
- [ ] Performance metrics monitored continuously
- [ ] Bias evaluation completed for production systems
- [ ] Confabulation detection operational
- [ ] Risk responses documented and tracked

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
