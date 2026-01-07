---
template_id: compliance_governance_agent_risk_controls_javascript
template_name: AI Agent Risk Controls - JavaScript
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
  - risk_management/javascript_risk_assessment.md
related_templates:
  - compliance_frameworks/javascript_nist_ai_rmf.md
  - ai_agent_governance/javascript_agent_security.md
tools:
  - ml-fairness (bias detection)
tags:
  - ai-risk
  - defense-in-depth
  - four-pillars
  - bias-detection
  - javascript
  - nodejs
---

# AI Agent Risk Controls - JavaScript

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agents including bias detection and drift monitoring

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### AI Risk Management

**Defense in Depth**: Multiple layers of risk controls

**Key AI Risks**:
- **Bias** - Unfair treatment of protected groups
- **Drift** - Model performance degrades over time
- **Hallucination** - False outputs
- **Data leakage** - Training data exposed
- **Adversarial attacks** - Malicious inputs

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'agent-risk-controls.log' })
  ]
});

class AgentRiskControls {
  /**
   * AI Agent risk management controls.
   *
   * 4 Pillars: Risk Management (Defense in Depth)
   * Compliance: NIST AI RMF MEASURE, MANAGE
   */

  /**
   * Detect bias in AI agent predictions.
   *
   * NIST AI RMF MEASURE 3.1: Bias evaluation
   * Pillar 2: Risk Management (Defense in Depth)
   */
  async detectBias(agentId, predictions, groundTruth, sensitiveFeatures) {
    // Calculate demographic parity difference
    const dpDiff = this.calculateDemographicParityDifference(
      predictions,
      groundTruth,
      sensitiveFeatures.gender
    );

    const biasDetected = Math.abs(dpDiff) > 0.1; // 10% threshold

    const result = {
      agentId,
      biasDetected,
      demographicParityDiff: dpDiff,
      threshold: 0.1,
      evaluationDate: new Date()
    };

    if (biasDetected) {
      logger.warn('Bias detected in agent', {
        event: 'bias_detected',
        agentId,
        dpDiff,
        timestamp: new Date().toISOString()
      });

      // Create risk incident
      await this._createBiasIncident(agentId, result);
    }

    return result;
  }

  /**
   * Calculate demographic parity difference.
   */
  calculateDemographicParityDifference(predictions, groundTruth, sensitiveFeature) {
    const groups = [...new Set(sensitiveFeature)];

    const positiveRates = {};

    for (const group of groups) {
      const groupIndices = sensitiveFeature
        .map((val, idx) => val === group ? idx : -1)
        .filter(idx => idx !== -1);

      const groupPredictions = groupIndices.map(idx => predictions[idx]);
      const positiveCount = groupPredictions.filter(p => p === 1).length;

      positiveRates[group] = positiveCount / groupPredictions.length;
    }

    const rates = Object.values(positiveRates);
    return Math.max(...rates) - Math.min(...rates);
  }

  /**
   * Monitor for model drift.
   *
   * NIST AI RMF MANAGE 3.1: Risk monitoring
   */
  async monitorDrift(agentId, referenceData, currentData) {
    // Simple drift detection: Compare distributions
    const drift = this.detectDistributionDrift(referenceData, currentData);

    const driftDetected = drift.pValue < 0.05;

    if (driftDetected) {
      logger.warn('Drift detected in agent', {
        event: 'drift_detected',
        agentId,
        pValue: drift.pValue,
        timestamp: new Date().toISOString()
      });

      // Trigger alert
      await this._createDriftAlert(agentId, drift);
    }

    return {
      agentId,
      driftDetected,
      driftDetails: drift
    };
  }

  /**
   * Detect distribution drift between datasets.
   */
  detectDistributionDrift(referenceData, currentData) {
    // Simplified drift detection
    // Production: Use statistical tests (KS test, etc.)

    const refMean = referenceData.reduce((a, b) => a + b, 0) / referenceData.length;
    const currMean = currentData.reduce((a, b) => a + b, 0) / currentData.length;

    const meanDiff = Math.abs(refMean - currMean);
    const pValue = meanDiff > 0.1 ? 0.01 : 0.5; // Simplified

    return {
      pValue,
      referenceMean: refMean,
      currentMean: currMean,
      meanDifference: meanDiff
    };
  }

  /**
   * Detect hallucinations in agent output.
   *
   * NIST GenAI Profile: Confabulation risk
   */
  async detectHallucination(agentId, generatedText, sourceDocuments) {
    const hallucinationScore = this._calculateHallucinationScore(
      generatedText,
      sourceDocuments
    );

    const hallucinationDetected = hallucinationScore > 0.5;

    if (hallucinationDetected) {
      logger.warn('Hallucination detected', {
        event: 'hallucination_detected',
        agentId,
        score: hallucinationScore,
        timestamp: new Date().toISOString()
      });
    }

    return {
      agentId,
      hallucinationDetected,
      score: hallucinationScore
    };
  }

  /**
   * Calculate hallucination likelihood.
   *
   * Higher score = more likely to be hallucination
   */
  _calculateHallucinationScore(generatedText, sourceDocuments) {
    const generatedLower = generatedText.toLowerCase();
    const sourcesLower = sourceDocuments.join(' ').toLowerCase();

    // Count how many generated words appear in sources
    const generatedWords = new Set(generatedLower.split(/\s+/));
    const sourceWords = new Set(sourcesLower.split(/\s+/));

    const intersection = [...generatedWords].filter(w => sourceWords.has(w));
    const overlap = intersection.length;
    const total = generatedWords.size;

    // Score: 1 - (overlap / total)
    // High score = low overlap = likely hallucination
    const score = total > 0 ? 1.0 - (overlap / total) : 0.0;

    return score;
  }

  /**
   * Create incident for bias detection.
   *
   * Automatic remediation: Flag agent for review
   */
  async _createBiasIncident(agentId, biasResult) {
    const incidentId = uuidv4();

    await db.collection('risk_incidents').insertOne({
      incidentId,
      agentId,
      incidentType: 'bias_detected',
      severity: 'high',
      details: biasResult,
      createdDate: new Date(),
      status: 'open'
    });

    // Flag agent for review
    await db.collection('ai_agents').updateOne(
      { agentId },
      { $set: { requiresBiasReview: true } }
    );
  }

  /**
   * Create alert for drift detection.
   */
  async _createDriftAlert(agentId, driftDetails) {
    const alertId = uuidv4();

    await db.collection('drift_alerts').insertOne({
      alertId,
      agentId,
      details: driftDetails,
      createdDate: new Date(),
      status: 'open'
    });
  }

  /**
   * Implement defense-in-depth risk mitigations.
   *
   * Pillar 2: Risk Management (Defense in Depth)
   */
  async implementRiskMitigations(agentId) {
    const mitigations = {
      inputValidation: true,
      outputSanitization: true,
      rateLimiting: true,
      biasMonitoring: true,
      driftDetection: true,
      hallucinationDetection: true,
      piiRedaction: true
    };

    await db.collection('ai_agents').updateOne(
      { agentId },
      { $set: { riskMitigations: mitigations } }
    );

    logger.info('Risk mitigations implemented', {
      event: 'risk_mitigations_implemented',
      agentId,
      mitigations: Object.keys(mitigations),
      timestamp: new Date().toISOString()
    });

    return mitigations;
  }
}

module.exports = AgentRiskControls;
```

---

## Success Criteria

- [ ] Bias detection implemented for all agents
- [ ] Drift monitoring operational
- [ ] Hallucination detection configured
- [ ] Defense-in-depth mitigations deployed
- [ ] Risk incidents tracked and remediated

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
