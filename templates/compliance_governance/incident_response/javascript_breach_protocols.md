---
template_id: compliance_governance_breach_protocols_javascript
template_name: Breach Protocols - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/javascript_incident_response_plan.md
  - privacy_protection/javascript_gdpr_compliance.md
related_templates:
  - compliance_frameworks/javascript_soc2_compliance.md
tools:
  - forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - javascript
  - nodejs
---

# Breach Protocols - JavaScript

**Data breach notification and response protocols (GDPR 72-hour rule)**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Data Breach Notification Requirements

**GDPR Article 33**: Notify supervisory authority within 72 hours
**GDPR Article 34**: Notify individuals if high risk
**CCPA**: No specific timeline, but must notify "without unreasonable delay"
**State Laws**: Varies (CA requires notification without unreasonable delay)

---

## Implementation

```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'breach-notifications.log' })
  ]
});

class BreachNotification {
  /**
   * Data breach notification protocols.
   *
   * Compliance:
   * - GDPR Articles 33-34 (72-hour notification)
   * - CCPA (reasonable notification)
   * - State breach notification laws
   */

  constructor() {
    this.GDPR_NOTIFICATION_DEADLINE_HOURS = 72;
  }

  /**
   * Assess if incident is data breach requiring notification.
   *
   * Factors:
   * - Was personal data accessed/disclosed?
   * - Risk to data subjects' rights and freedoms
   * - Volume of affected individuals
   * - Sensitivity of data
   */
  async assessBreach(incidentId) {
    const incident = await db.collection('incidents').findOne({ incidentId });

    const isBreach = incident.dataAffected || false;

    if (!isBreach) {
      return { isBreach: false };
    }

    // Assess risk level
    const riskLevel = this._assessRiskLevel(incident);

    const breachAssessment = {
      isBreach: true,
      breachId: uuidv4(),
      incidentId,
      detectedDate: incident.detectedDate,
      riskLevel,

      // Notification requirements
      notifyGdprAuthority: ['medium', 'high', 'critical'].includes(riskLevel),
      notifyIndividuals: ['high', 'critical'].includes(riskLevel),
      notifyCcpa: incident.caResidentsAffected || false,

      // Deadlines
      gdprDeadline: new Date(
        Date.now() + this.GDPR_NOTIFICATION_DEADLINE_HOURS * 60 * 60 * 1000
      )
    };

    await db.collection('breach_assessments').insertOne(breachAssessment);

    logger.critical('Data breach assessed', {
      event: 'breach_assessed',
      breachId: breachAssessment.breachId,
      riskLevel,
      timestamp: new Date().toISOString()
    });

    return breachAssessment;
  }

  /**
   * Assess risk level of breach.
   */
  _assessRiskLevel(incident) {
    let score = 0;

    // Volume of affected individuals
    if (incident.usersAffectedCount > 10000) score += 3;
    else if (incident.usersAffectedCount > 1000) score += 2;
    else if (incident.usersAffectedCount > 100) score += 1;

    // Sensitivity of data
    const sensitiveDataTypes = ['health', 'financial', 'biometric', 'genetic'];
    if (incident.dataCategories?.some(cat => sensitiveDataTypes.includes(cat))) {
      score += 3;
    }

    // Nature of breach
    if (incident.breachType === 'exfiltration') score += 2;
    else if (incident.breachType === 'unauthorized_access') score += 1;

    // Determine risk level
    if (score >= 7) return 'critical';
    if (score >= 5) return 'high';
    if (score >= 3) return 'medium';
    return 'low';
  }

  /**
   * Notify GDPR supervisory authority within 72 hours.
   *
   * GDPR Article 33
   */
  async notifyGdprAuthority(breachId) {
    const breach = await db.collection('breach_assessments').findOne({ breachId });

    const notification = {
      notificationId: uuidv4(),
      breachId,
      notificationType: 'gdpr_authority',
      notificationDate: new Date(),

      // Article 33(3) required content
      natureOfBreach: 'Unauthorized access to customer database',
      dpoContact: 'dpo@company.com',
      likelyConsequences: 'Risk of identity theft for affected individuals',
      measuresTaken: 'Database access revoked, passwords reset, monitoring enhanced'
    };

    await db.collection('breach_notifications').insertOne(notification);

    // Send notification to authority
    await this._sendToAuthority(notification);

    logger.critical('GDPR authority notified', {
      event: 'gdpr_authority_notified',
      notificationId: notification.notificationId,
      timestamp: new Date().toISOString()
    });

    return notification.notificationId;
  }

  /**
   * Notify affected individuals.
   *
   * GDPR Article 34: High risk breaches
   */
  async notifyIndividuals(breachId) {
    const breach = await db.collection('breach_assessments').findOne({ breachId });
    const incident = await db.collection('incidents').findOne({
      incidentId: breach.incidentId
    });

    const affectedUsers = await this._getAffectedUsers(incident);

    for (const user of affectedUsers) {
      const notificationContent = `
Subject: Important Security Notice

We are writing to inform you of a data security incident.

What Happened: ${breach.description || 'Unauthorized access to systems'}

What Information Was Involved: ${breach.dataCategories?.join(', ') || 'Personal information'}

What We Are Doing: ${breach.remediation || 'Enhanced security measures'}

What You Can Do: ${breach.recommendations || 'Monitor accounts for suspicious activity'}

Contact: security@company.com
      `;

      await this._sendNotificationEmail(user, notificationContent);
    }

    logger.critical('Individuals notified', {
      event: 'individuals_notified',
      breachId,
      count: affectedUsers.length,
      timestamp: new Date().toISOString()
    });

    return affectedUsers.length;
  }

  async _getAffectedUsers(incident) {
    // Query affected users based on incident
    return await db.collection('users')
      .find({ userId: { $in: incident.affectedUserIds || [] } })
      .toArray();
  }

  async _sendToAuthority(notification) {
    // Implementation: Send to supervisory authority
    console.log('Sending notification to GDPR authority:', notification.notificationId);
  }

  async _sendNotificationEmail(user, content) {
    // Implementation: Send email notification
    console.log(`Sending breach notification to ${user.email}`);
  }
}

module.exports = BreachNotification;
```

---

## Success Criteria

- [ ] Breach detection mechanisms operational
- [ ] 72-hour notification workflow implemented
- [ ] Notification templates ready
- [ ] Authority contacts established
- [ ] Breach simulation conducted

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
