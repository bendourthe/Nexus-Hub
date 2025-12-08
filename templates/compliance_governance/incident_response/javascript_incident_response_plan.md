---
template_id: compliance_governance_incident_response_javascript
template_name: Incident Response Plan - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/javascript_soc2_compliance.md
  - compliance_frameworks/javascript_iso27001_implementation.md
related_templates:
  - incident_response/javascript_breach_protocols.md
  - privacy_protection/javascript_gdpr_compliance.md
tools:
  - pagerduty (alerting)
  - jira (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - javascript
  - nodejs
---

# Incident Response Plan - JavaScript

**6-phase incident response lifecycle implementation**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Incident Response Lifecycle

**NIST SP 800-61**: 6-phase incident response process

1. **Preparation** - Tools, training, procedures
2. **Detection and Analysis** - Identify incidents
3. **Containment** - Stop spread
4. **Eradication** - Remove threat
5. **Recovery** - Restore operations
6. **Post-Incident** - Lessons learned

### Framework Requirements

**ISO 27001 Control 5.26**: Response to information security incidents
**SOC 2 CC7.4**: Respond to security incidents

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'incident-response.log' })
  ]
});

const IncidentSeverity = {
  P1_CRITICAL: 'p1_critical',  // System down, data breach
  P2_HIGH: 'p2_high',          // Significant impact
  P3_MEDIUM: 'p3_medium',      // Moderate impact
  P4_LOW: 'p4_low'             // Minor issue
};

const IncidentStatus = {
  DETECTED: 'detected',
  INVESTIGATING: 'investigating',
  CONTAINED: 'contained',
  ERADICATED: 'eradicated',
  RECOVERED: 'recovered',
  CLOSED: 'closed'
};

class IncidentResponse {
  /**
   * Incident response lifecycle management.
   *
   * Compliance: ISO 27001 Control 5.26, SOC 2 CC7.4
   * Framework: NIST SP 800-61
   */

  constructor() {
    // Response time SLAs
    this.RESPONSE_SLA = {
      [IncidentSeverity.P1_CRITICAL]: 15,   // 15 minutes
      [IncidentSeverity.P2_HIGH]: 60,       // 1 hour
      [IncidentSeverity.P3_MEDIUM]: 240,    // 4 hours
      [IncidentSeverity.P4_LOW]: 1440       // 24 hours
    };
  }

  /**
   * Create security incident.
   *
   * Phase 2: Detection and Analysis
   */
  async createIncident(title, description, severity, incidentType, detectedBy) {
    const incidentId = uuidv4();
    const responseDeadline = new Date(
      Date.now() + this.RESPONSE_SLA[severity] * 60 * 1000
    );

    const incident = {
      incidentId,
      title,
      description,
      severity,
      incidentType,
      detectedBy,
      detectedDate: new Date(),
      status: IncidentStatus.DETECTED,
      responseDeadline,

      // Response team
      incidentCommander: null,
      responseTeam: [],

      // Timeline
      containedDate: null,
      eradicatedDate: null,
      recoveredDate: null,
      closedDate: null,

      // Impact
      systemsAffected: [],
      dataAffected: false,
      usersAffectedCount: 0
    };

    await db.collection('incidents').insertOne(incident);

    // Alert response team
    if ([IncidentSeverity.P1_CRITICAL, IncidentSeverity.P2_HIGH].includes(severity)) {
      await this._alertResponseTeam(incidentId);
    }

    logger.critical('Security incident created', {
      event: 'incident_created',
      incidentId,
      severity,
      timestamp: new Date().toISOString()
    });

    return incidentId;
  }

  /**
   * Contain incident to prevent spread.
   *
   * Phase 3: Containment
   */
  async containIncident(incidentId, containmentActions) {
    await db.collection('incidents').updateOne(
      { incidentId },
      {
        $set: {
          status: IncidentStatus.CONTAINED,
          containedDate: new Date(),
          containmentActions
        }
      }
    );

    logger.warn('Incident contained', {
      event: 'incident_contained',
      incidentId,
      actions: containmentActions,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Remove threat from environment.
   *
   * Phase 4: Eradication
   */
  async eradicateThreat(incidentId, eradicationActions) {
    await db.collection('incidents').updateOne(
      { incidentId },
      {
        $set: {
          status: IncidentStatus.ERADICATED,
          eradicatedDate: new Date(),
          eradicationActions
        }
      }
    );

    logger.info('Threat eradicated', {
      event: 'threat_eradicated',
      incidentId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Restore systems to normal operations.
   *
   * Phase 5: Recovery
   */
  async recoverSystems(incidentId, recoveryActions) {
    await db.collection('incidents').updateOne(
      { incidentId },
      {
        $set: {
          status: IncidentStatus.RECOVERED,
          recoveredDate: new Date(),
          recoveryActions
        }
      }
    );

    logger.info('Systems recovered', {
      event: 'systems_recovered',
      incidentId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Close incident with post-mortem.
   *
   * Phase 6: Post-Incident Activity
   */
  async closeIncident(incidentId, rootCause, lessonsLearned) {
    const incident = await db.collection('incidents').findOne({ incidentId });

    // Calculate metrics
    const totalDuration = (Date.now() - incident.detectedDate.getTime()) / 1000 / 3600;

    const postMortem = {
      incidentId,
      rootCause,
      lessonsLearned,
      totalDurationHours: totalDuration,
      createdDate: new Date()
    };

    await db.collection('post_mortems').insertOne(postMortem);

    await db.collection('incidents').updateOne(
      { incidentId },
      {
        $set: {
          status: IncidentStatus.CLOSED,
          closedDate: new Date(),
          rootCause
        }
      }
    );

    logger.info('Incident closed', {
      event: 'incident_closed',
      incidentId,
      durationHours: totalDuration,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Generate incident report for stakeholders.
   *
   * Required for compliance audits
   */
  async generateIncidentReport(incidentId) {
    const incident = await db.collection('incidents').findOne({ incidentId });
    const postMortem = await db.collection('post_mortems').findOne({ incidentId });

    const report = {
      incidentId,
      title: incident.title,
      severity: incident.severity,
      detectionDate: incident.detectedDate.toISOString(),
      closureDate: incident.closedDate ? incident.closedDate.toISOString() : null,

      // Impact
      systemsAffected: incident.systemsAffected,
      dataAffected: incident.dataAffected,
      usersAffected: incident.usersAffectedCount,

      // Response
      containmentActions: incident.containmentActions || [],
      eradicationActions: incident.eradicationActions || [],
      recoveryActions: incident.recoveryActions || [],

      // Post-mortem
      rootCause: postMortem ? postMortem.rootCause : null,
      lessonsLearned: postMortem ? postMortem.lessonsLearned : null
    };

    return report;
  }

  async _alertResponseTeam(incidentId) {
    // Implementation: Send alerts via PagerDuty, Slack, etc.
    console.log(`Alerting response team for incident ${incidentId}`);
  }
}

module.exports = IncidentResponse;
```

---

## Success Criteria

- [ ] Incident response plan documented
- [ ] Response team identified and trained
- [ ] Incident detection mechanisms operational
- [ ] Escalation procedures defined
- [ ] Post-incident review process established

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
