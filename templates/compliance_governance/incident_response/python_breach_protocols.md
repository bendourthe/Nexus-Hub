---
template_id: compliance_governance_breach_protocols_python
template_name: Breach Protocols - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/python_incident_response_plan.md
  - privacy_protection/python_gdpr_compliance.md
related_templates:
  - compliance_frameworks/python_soc2_compliance.md
tools:
  - forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - python
---

# Breach Protocols - Python

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

```python
# Data breach notification
from datetime import datetime, timedelta
from typing import Dict, List

class BreachNotification:
    """
    Data breach notification protocols.

    Compliance:
    - GDPR Articles 33-34 (72-hour notification)
    - CCPA (reasonable notification)
    - State breach notification laws
    """

    GDPR_NOTIFICATION_DEADLINE_HOURS = 72

    def assess_breach(self, incident_id: str) -> Dict:
        """
        Assess if incident is data breach requiring notification.

        Factors:
        - Was personal data accessed/disclosed?
        - Risk to data subjects' rights and freedoms
        - Volume of affected individuals
        - Sensitivity of data
        """
        incident = db.incidents.find_one({"incident_id": incident_id})

        is_breach = incident.get("data_affected", False)

        if not is_breach:
            return {"is_breach": False}

        # Assess risk level
        risk_level = self._assess_risk_level(incident)

        breach_assessment = {
            "is_breach": True,
            "breach_id": generate_uuid(),
            "incident_id": incident_id,
            "detected_date": incident["detected_date"],
            "risk_level": risk_level,

            # Notification requirements
            "notify_gdpr_authority": risk_level in ["medium", "high", "critical"],
            "notify_individuals": risk_level in ["high", "critical"],
            "notify_ccpa": incident.get("ca_residents_affected", False),

            # Deadlines
            "gdpr_deadline": datetime.utcnow() + timedelta(hours=self.GDPR_NOTIFICATION_DEADLINE_HOURS)
        }

        db.breach_assessments.insert_one(breach_assessment)

        logger.critical("Data breach assessed", extra={
            "breach_id": breach_assessment["breach_id"],
            "risk_level": risk_level
        })

        return breach_assessment

    def notify_gdpr_authority(self, breach_id: str) -> str:
        """
        Notify GDPR supervisory authority within 72 hours.

        GDPR Article 33
        """
        breach = db.breach_assessments.find_one({"breach_id": breach_id})

        notification = {
            "notification_id": generate_uuid(),
            "breach_id": breach_id,
            "notification_type": "gdpr_authority",
            "notification_date": datetime.utcnow(),

            # Article 33(3) required content
            "nature_of_breach": "Unauthorized access to customer database",
            "dpo_contact": "dpo@company.com",
            "likely_consequences": "Risk of identity theft for affected individuals",
            "measures_taken": "Database access revoked, passwords reset, monitoring enhanced"
        }

        db.breach_notifications.insert_one(notification)

        # Send notification to authority
        self._send_to_authority(notification)

        logger.critical("GDPR authority notified", extra={
            "notification_id": notification["notification_id"]
        })

        return notification["notification_id"]

    def notify_individuals(self, breach_id: str) -> int:
        """
        Notify affected individuals.

        GDPR Article 34: High risk breaches
        """
        breach = db.breach_assessments.find_one({"breach_id": breach_id})
        incident = db.incidents.find_one({"incident_id": breach["incident_id"]})

        affected_users = self._get_affected_users(incident)

        for user in affected_users:
            notification_content = f"""
            Subject: Important Security Notice

            We are writing to inform you of a data security incident.

            What Happened: {breach.get('description')}

            What Information Was Involved: {breach.get('data_categories')}

            What We Are Doing: {breach.get('remediation')}

            What You Can Do: {breach.get('recommendations')}

            Contact: security@company.com
            """

            self._send_notification_email(user, notification_content)

        logger.critical("Individuals notified", extra={
            "breach_id": breach_id,
            "count": len(affected_users)
        })

        return len(affected_users)
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
