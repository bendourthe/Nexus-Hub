---
template_id: compliance_governance_risk_assessment_javascript
template_name: Risk Assessment - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 6-8
prerequisites:
  - risk_management/README.md
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - risk_management/javascript_threat_modeling.md
  - compliance_frameworks/javascript_soc2_compliance.md
tools:
  - joi (validation)
tags:
  - risk-assessment
  - iso27001
  - nist
  - javascript
  - nodejs
---

# Risk Assessment - JavaScript

**ISO 27001, NIST, SOC 2 risk assessment implementation**

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Risk Assessment Process

1. **Identify** assets and threats
2. **Analyze** likelihood and impact
3. **Evaluate** risk level
4. **Treat** risks (mitigate, accept, transfer, avoid)
5. **Monitor** residual risks

### Risk Calculation

**Risk Score** = Likelihood × Impact

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'risk-management.log' })
  ]
});

const LikelihoodLevel = {
  RARE: { value: 1, description: 'May occur in exceptional circumstances' },
  UNLIKELY: { value: 2, description: 'Could occur at some time' },
  POSSIBLE: { value: 3, description: 'Might occur at some time' },
  LIKELY: { value: 4, description: 'Will probably occur in most circumstances' },
  ALMOST_CERTAIN: { value: 5, description: 'Expected to occur in most circumstances' }
};

const ImpactLevel = {
  INSIGNIFICANT: { value: 1, description: 'Minimal impact' },
  MINOR: { value: 2, description: 'Minor disruption' },
  MODERATE: { value: 3, description: 'Significant disruption' },
  MAJOR: { value: 4, description: 'Major damage' },
  CATASTROPHIC: { value: 5, description: 'Severe consequences' }
};

const RiskLevel = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

class RiskAssessmentManager {
  /**
   * Register asset for risk assessment.
   *
   * ISO 27001 Control 5.9: Inventory of assets
   */
  async registerAsset(assetName, assetType, owner, description) {
    const assetId = uuidv4();

    const asset = {
      assetId,
      assetName,
      assetType, // 'system', 'data', 'service', 'infrastructure'
      owner,
      description,
      registeredAt: new Date(),
      lastAssessment: null,
      riskScore: null
    };

    await db.collection('assets').insertOne(asset);

    logger.info('Asset registered', {
      event: 'asset_registered',
      assetId,
      assetName,
      assetType,
      owner
    });

    return assetId;
  }

  /**
   * Conduct risk assessment for asset.
   *
   * ISO 27001 Control 5.7: Threat intelligence
   * NIST SP 800-30: Risk assessment
   */
  async conductRiskAssessment(assetId, threats) {
    const assessmentId = uuidv4();
    const riskAnalyses = [];

    for (const threat of threats) {
      const risk = await this.analyzeRisk(assetId, threat);
      riskAnalyses.push(risk);
    }

    const assessment = {
      assessmentId,
      assetId,
      assessmentDate: new Date(),
      assessedBy: 'system',
      risks: riskAnalyses,
      highestRiskLevel: this.getHighestRiskLevel(riskAnalyses)
    };

    await db.collection('risk_assessments').insertOne(assessment);

    // Update asset with latest assessment
    await db.collection('assets').updateOne(
      { assetId },
      {
        $set: {
          lastAssessment: new Date(),
          riskScore: this.calculateOverallRiskScore(riskAnalyses)
        }
      }
    );

    logger.info('Risk assessment completed', {
      event: 'risk_assessment_completed',
      assessmentId,
      assetId,
      riskCount: riskAnalyses.length,
      highestRisk: assessment.highestRiskLevel
    });

    return assessment;
  }

  /**
   * Analyze individual risk.
   *
   * Risk Score = Likelihood × Impact
   */
  async analyzeRisk(assetId, threat) {
    const riskId = uuidv4();

    // Assess likelihood
    const likelihood = this.assessLikelihood(assetId, threat);

    // Assess impact
    const impact = this.assessImpact(assetId, threat);

    // Calculate risk score
    const riskScore = likelihood.value * impact.value;

    // Determine risk level
    let riskLevel;
    if (riskScore >= 20) {
      riskLevel = RiskLevel.CRITICAL;
    } else if (riskScore >= 13) {
      riskLevel = RiskLevel.HIGH;
    } else if (riskScore >= 6) {
      riskLevel = RiskLevel.MEDIUM;
    } else {
      riskLevel = RiskLevel.LOW;
    }

    return {
      riskId,
      threatId: threat.threatId,
      threatDescription: threat.description,
      likelihood,
      impact,
      riskScore,
      riskLevel,
      existingControls: await this.getExistingControls(assetId, threat.threatId),
      recommendedControls: this.recommendControls(riskLevel, threat)
    };
  }

  /**
   * Assess likelihood of threat occurring.
   */
  assessLikelihood(assetId, threat) {
    // Factors: vulnerability exploitability, threat actor capability, historical data
    const factors = {
      vulnerabilityScore: threat.vulnerabilityScore || 3,
      threatActorCapability: threat.threatActorCapability || 3,
      historicalOccurrences: threat.historicalOccurrences || 0
    };

    let likelihoodValue;

    if (factors.historicalOccurrences > 10) {
      likelihoodValue = LikelihoodLevel.ALMOST_CERTAIN.value;
    } else if (factors.vulnerabilityScore >= 4 && factors.threatActorCapability >= 4) {
      likelihoodValue = LikelihoodLevel.LIKELY.value;
    } else if (factors.vulnerabilityScore >= 3) {
      likelihoodValue = LikelihoodLevel.POSSIBLE.value;
    } else if (factors.vulnerabilityScore >= 2) {
      likelihoodValue = LikelihoodLevel.UNLIKELY.value;
    } else {
      likelihoodValue = LikelihoodLevel.RARE.value;
    }

    return {
      value: likelihoodValue,
      description: Object.values(LikelihoodLevel).find(l => l.value === likelihoodValue).description,
      factors
    };
  }

  /**
   * Assess impact if threat materializes.
   */
  assessImpact(assetId, threat) {
    // Impact dimensions: financial, operational, reputational, legal
    const dimensions = {
      financial: threat.financialImpact || 0,
      operational: threat.operationalImpact || 0,
      reputational: threat.reputationalImpact || 0,
      legal: threat.legalImpact || 0
    };

    // Take maximum impact dimension
    const maxImpact = Math.max(...Object.values(dimensions));

    return {
      value: maxImpact,
      description: Object.values(ImpactLevel).find(i => i.value === maxImpact).description,
      dimensions
    };
  }

  /**
   * Get existing controls for threat.
   */
  async getExistingControls(assetId, threatId) {
    return await db.collection('controls')
      .find({ assetId, threatId })
      .toArray();
  }

  /**
   * Recommend controls based on risk level.
   */
  recommendControls(riskLevel, threat) {
    const controlRecommendations = {
      [RiskLevel.CRITICAL]: [
        'Immediate mitigation required',
        'Senior management approval needed',
        'Continuous monitoring',
        'Incident response plan'
      ],
      [RiskLevel.HIGH]: [
        'Priority mitigation within 30 days',
        'Management approval required',
        'Regular monitoring'
      ],
      [RiskLevel.MEDIUM]: [
        'Mitigation within 90 days',
        'Standard controls',
        'Periodic review'
      ],
      [RiskLevel.LOW]: [
        'Accept or monitor',
        'Basic controls sufficient'
      ]
    };

    return controlRecommendations[riskLevel] || [];
  }

  getHighestRiskLevel(risks) {
    const levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL];
    const riskLevels = risks.map(r => r.riskLevel);

    for (let i = levels.length - 1; i >= 0; i--) {
      if (riskLevels.includes(levels[i])) {
        return levels[i];
      }
    }

    return RiskLevel.LOW;
  }

  calculateOverallRiskScore(risks) {
    return risks.reduce((sum, r) => sum + r.riskScore, 0) / risks.length;
  }

  /**
   * Document risk treatment decision.
   *
   * ISO 27001 Control 5.8: Risk treatment
   */
  async documentRiskTreatment(riskId, treatment) {
    const treatmentId = uuidv4();

    const riskTreatment = {
      treatmentId,
      riskId,
      strategy: treatment.strategy, // 'mitigate', 'accept', 'transfer', 'avoid'
      justification: treatment.justification,
      mitigationActions: treatment.mitigationActions || [],
      residualRiskLevel: treatment.residualRiskLevel,
      ownerUserId: treatment.owner,
      approvedBy: treatment.approvedBy,
      approvalDate: new Date(),
      reviewDate: treatment.reviewDate
    };

    await db.collection('risk_treatments').insertOne(riskTreatment);

    logger.info('Risk treatment documented', {
      event: 'risk_treatment_documented',
      treatmentId,
      riskId,
      strategy: treatment.strategy,
      residualRisk: treatment.residualRiskLevel
    });

    return treatmentId;
  }

  /**
   * Generate risk register report.
   *
   * ISO 27001 Annex A: Risk register
   */
  async generateRiskRegister() {
    const assessments = await db.collection('risk_assessments')
      .find({})
      .toArray();

    const allRisks = assessments.flatMap(a => a.risks.map(r => ({
      ...r,
      assetId: a.assetId,
      assessmentDate: a.assessmentDate
    })));

    const riskRegister = {
      registerId: uuidv4(),
      generatedAt: new Date(),
      totalRisks: allRisks.length,
      risksByLevel: {
        critical: allRisks.filter(r => r.riskLevel === RiskLevel.CRITICAL).length,
        high: allRisks.filter(r => r.riskLevel === RiskLevel.HIGH).length,
        medium: allRisks.filter(r => r.riskLevel === RiskLevel.MEDIUM).length,
        low: allRisks.filter(r => r.riskLevel === RiskLevel.LOW).length
      },
      topRisks: allRisks
        .sort((a, b) => b.riskScore - a.riskScore)
        .slice(0, 10),
      untreatedCriticalRisks: await this.getUntreatedCriticalRisks()
    };

    await db.collection('risk_registers').insertOne(riskRegister);

    return riskRegister;
  }

  async getUntreatedCriticalRisks() {
    const criticalRisks = await db.collection('risk_assessments').aggregate([
      { $unwind: '$risks' },
      { $match: { 'risks.riskLevel': RiskLevel.CRITICAL } }
    ]).toArray();

    const treated = await db.collection('risk_treatments')
      .find({})
      .toArray();

    const treatedRiskIds = new Set(treated.map(t => t.riskId));

    return criticalRisks.filter(r => !treatedRiskIds.has(r.risks.riskId));
  }
}

module.exports = RiskAssessmentManager;
```

---

## Success Criteria

- [ ] All critical assets registered
- [ ] Risk assessments conducted annually
- [ ] Risk scores calculated (Likelihood × Impact)
- [ ] High and critical risks treated
- [ ] Risk register maintained and updated
- [ ] Residual risks documented and accepted
- [ ] Risk treatment plans tracked

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
