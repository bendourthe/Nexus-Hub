---
template_id: compliance_governance_threat_modeling_javascript
template_name: Threat Modeling - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - risk_management/javascript_risk_assessment.md
related_templates:
  - compliance_frameworks/javascript_iso27001_implementation.md
tools:
  - OWASP Threat Dragon
tags:
  - threat-modeling
  - stride
  - attack-trees
  - javascript
  - nodejs
---

# Threat Modeling - JavaScript

**STRIDE methodology and attack tree implementation**

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Threat Modeling Methodologies

**STRIDE**:
- **S**poofing
- **T**ampering
- **R**epudiation
- **I**nformation Disclosure
- **D**enial of Service
- **E**levation of Privilege

**DREAD**: Risk ranking (Damage, Reproducibility, Exploitability, Affected users, Discoverability)

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'threat-modeling.log' })
  ]
});

class ThreatModeling {
  constructor() {
    // STRIDE applicability by component type
    this.STRIDE_APPLICABILITY = {
      'api_endpoint': ['Spoofing', 'Tampering', 'Repudiation', 'Information Disclosure', 'Denial of Service', 'Elevation of Privilege'],
      'database': ['Tampering', 'Information Disclosure', 'Denial of Service'],
      'data_flow': ['Tampering', 'Information Disclosure', 'Denial of Service'],
      'external_service': ['Spoofing', 'Tampering', 'Information Disclosure', 'Denial of Service'],
      'user_interface': ['Spoofing', 'Tampering', 'Repudiation']
    };
  }

  /**
   * Create threat model for system.
   *
   * ISO 27001 Control 5.7: Threat intelligence
   */
  async createThreatModel(systemName, systemDescription, components) {
    const modelId = uuidv4();

    const threatModel = {
      modelId,
      systemName,
      systemDescription,
      components,
      createdDate: new Date(),
      lastUpdated: new Date(),
      threats: []
    };

    await db.collection('threat_models').insertOne(threatModel);

    logger.info('Threat model created', {
      event: 'threat_model_created',
      modelId,
      systemName,
      componentCount: components.length,
      timestamp: new Date().toISOString()
    });

    return modelId;
  }

  /**
   * Analyze component using STRIDE methodology.
   */
  async analyzeComponent(modelId, component) {
    const componentType = component.componentType;
    const applicableCategories = this.STRIDE_APPLICABILITY[componentType] || [];

    const threats = [];

    for (const category of applicableCategories) {
      const threat = this._generateThreat(component, category);
      threats.push(threat);
    }

    // Add threats to model
    await db.collection('threat_models').updateOne(
      { modelId },
      { $push: { threats: { $each: threats } } }
    );

    logger.info('Component analyzed with STRIDE', {
      event: 'stride_analysis_completed',
      modelId,
      componentId: component.componentId,
      threatCount: threats.length,
      timestamp: new Date().toISOString()
    });

    return threats;
  }

  /**
   * Generate threat based on STRIDE category.
   */
  _generateThreat(component, strideCategory) {
    const threatId = uuidv4();

    const threatTemplates = {
      'Spoofing': {
        description: `Attacker could impersonate legitimate user accessing ${component.componentName}`,
        mitigation: 'Implement strong authentication (MFA)',
        severity: 'high'
      },
      'Tampering': {
        description: `Attacker could modify data in ${component.componentName}`,
        mitigation: 'Implement integrity checks, encryption',
        severity: 'high'
      },
      'Repudiation': {
        description: `User could deny performing action on ${component.componentName}`,
        mitigation: 'Implement comprehensive audit logging',
        severity: 'medium'
      },
      'Information Disclosure': {
        description: `Sensitive data from ${component.componentName} could be exposed`,
        mitigation: 'Encrypt data at rest and in transit',
        severity: 'critical'
      },
      'Denial of Service': {
        description: `Attacker could overwhelm ${component.componentName}`,
        mitigation: 'Implement rate limiting, resource quotas',
        severity: 'high'
      },
      'Elevation of Privilege': {
        description: `Attacker could gain elevated access to ${component.componentName}`,
        mitigation: 'Implement least privilege, RBAC',
        severity: 'critical'
      }
    };

    const template = threatTemplates[strideCategory];

    return {
      threatId,
      componentId: component.componentId,
      componentName: component.componentName,
      strideCategory,
      description: template.description,
      recommendedMitigation: template.mitigation,
      severity: template.severity,
      status: 'identified',
      mitigated: false
    };
  }

  /**
   * Rank threat using DREAD methodology.
   */
  async rankThreatWithDread(threatId, dreadScores) {
    const {
      damage,           // 0-10: Potential damage
      reproducibility,  // 0-10: How easy to reproduce
      exploitability,   // 0-10: How easy to exploit
      affectedUsers,    // 0-10: How many users affected
      discoverability   // 0-10: How easy to discover
    } = dreadScores;

    const dreadScore = (damage + reproducibility + exploitability +
                        affectedUsers + discoverability) / 5;

    let riskRating;
    if (dreadScore >= 8) riskRating = 'critical';
    else if (dreadScore >= 6) riskRating = 'high';
    else if (dreadScore >= 4) riskRating = 'medium';
    else riskRating = 'low';

    await db.collection('threat_models').updateOne(
      { 'threats.threatId': threatId },
      {
        $set: {
          'threats.$.dreadScore': dreadScore,
          'threats.$.riskRating': riskRating,
          'threats.$.dreadBreakdown': dreadScores
        }
      }
    );

    logger.info('Threat ranked with DREAD', {
      event: 'threat_ranked',
      threatId,
      dreadScore,
      riskRating,
      timestamp: new Date().toISOString()
    });

    return { dreadScore, riskRating };
  }

  /**
   * Create attack tree for threat.
   */
  async createAttackTree(threatId, rootGoal) {
    const treeId = uuidv4();

    const attackTree = {
      treeId,
      threatId,
      rootGoal,
      nodes: [
        {
          nodeId: uuidv4(),
          type: 'root',
          description: rootGoal,
          children: []
        }
      ],
      createdDate: new Date()
    };

    await db.collection('attack_trees').insertOne(attackTree);

    logger.info('Attack tree created', {
      event: 'attack_tree_created',
      treeId,
      threatId,
      rootGoal,
      timestamp: new Date().toISOString()
    });

    return treeId;
  }

  /**
   * Add attack path to attack tree.
   */
  async addAttackPath(treeId, parentNodeId, attackStep) {
    const nodeId = uuidv4();

    const node = {
      nodeId,
      type: attackStep.type, // 'and' | 'or'
      description: attackStep.description,
      likelihood: attackStep.likelihood,
      impact: attackStep.impact,
      children: []
    };

    await db.collection('attack_trees').updateOne(
      { treeId, 'nodes.nodeId': parentNodeId },
      { $push: { 'nodes.$.children': node } }
    );

    return nodeId;
  }

  /**
   * Generate threat modeling report.
   */
  async generateThreatReport(modelId) {
    const model = await db.collection('threat_models').findOne({ modelId });

    const threatsBySeverity = {
      critical: model.threats.filter(t => t.severity === 'critical').length,
      high: model.threats.filter(t => t.severity === 'high').length,
      medium: model.threats.filter(t => t.severity === 'medium').length,
      low: model.threats.filter(t => t.severity === 'low').length
    };

    const report = {
      reportId: uuidv4(),
      modelId,
      systemName: model.systemName,
      generatedDate: new Date(),
      totalThreats: model.threats.length,
      threatsBySeverity,
      mitigatedThreats: model.threats.filter(t => t.mitigated).length,
      unmitigatedCritical: model.threats.filter(
        t => t.severity === 'critical' && !t.mitigated
      ),
      topThreats: model.threats
        .filter(t => t.dreadScore)
        .sort((a, b) => b.dreadScore - a.dreadScore)
        .slice(0, 10)
    };

    await db.collection('threat_reports').insertOne(report);

    return report;
  }
}

module.exports = ThreatModeling;
```

---

## Success Criteria

- [ ] Threat models created for all critical systems
- [ ] STRIDE analysis completed
- [ ] Threats ranked with DREAD methodology
- [ ] Attack trees documented
- [ ] Mitigation strategies defined
- [ ] Threat model reviewed quarterly

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
