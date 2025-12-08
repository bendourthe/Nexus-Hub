---
template_id: compliance_governance_incident_response_python
template_name: Incident Response Plan - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - compliance_frameworks/python_iso27001_implementation.md
related_templates:
  - incident_response/python_breach_protocols.md
  - privacy_protection/python_gdpr_compliance.md
tools:
  - pagerduty (alerting)
  - jira (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - python
---

# Incident Response Plan - Python

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

```python
# Incident response management
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels."""
    P1_CRITICAL = "p1_critical"  # System down, data breach
    P2_HIGH = "p2_high"          # Significant impact
    P3_MEDIUM = "p3_medium"      # Moderate impact
    P4_LOW = "p4_low"            # Minor issue

class IncidentStatus(Enum):
    """Incident lifecycle status."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"

class IncidentResponse:
    """
    Incident response lifecycle management.

    Compliance: ISO 27001 Control 5.26, SOC 2 CC7.4
    Framework: NIST SP 800-61
    """

    # Response time SLAs
    RESPONSE_SLA = {
        IncidentSeverity.P1_CRITICAL: 15,   # 15 minutes
        IncidentSeverity.P2_HIGH: 60,       # 1 hour
        IncidentSeverity.P3_MEDIUM: 240,    # 4 hours
        IncidentSeverity.P4_LOW: 1440       # 24 hours
    }

    def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        incident_type: str,
        detected_by: str
    ) -> str:
        """
        Create security incident.

        Phase 2: Detection and Analysis
        """
        incident_id = generate_uuid()
        response_deadline = datetime.utcnow() + timedelta(
            minutes=self.RESPONSE_SLA[severity]
        )

        incident = {
            "incident_id": incident_id,
            "title": title,
            "description": description,
            "severity": severity.value,
            "incident_type": incident_type,
            "detected_by": detected_by,
            "detected_date": datetime.utcnow(),
            "status": IncidentStatus.DETECTED.value,
            "response_deadline": response_deadline,

            # Response team
            "incident_commander": None,
            "response_team": [],

            # Timeline
            "contained_date": None,
            "eradicated_date": None,
            "recovered_date": None,
            "closed_date": None,

            # Impact
            "systems_affected": [],
            "data_affected": False,
            "users_affected_count": 0
        }

        db.incidents.insert_one(incident)

        # Alert response team
        if severity in [IncidentSeverity.P1_CRITICAL, IncidentSeverity.P2_HIGH]:
            self._alert_response_team(incident_id)

        logger.critical("Security incident created", extra={
            "event": "incident_created",
            "incident_id": incident_id,
            "severity": severity.value
        })

        return incident_id

    def contain_incident(self, incident_id: str, containment_actions: List[str]):
        """
        Contain incident to prevent spread.

        Phase 3: Containment
        """
        db.incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "status": IncidentStatus.CONTAINED.value,
                "contained_date": datetime.utcnow(),
                "containment_actions": containment_actions
            }}
        )

        logger.warning("Incident contained", extra={
            "incident_id": incident_id,
            "actions": containment_actions
        })

    def eradicate_threat(self, incident_id: str, eradication_actions: List[str]):
        """
        Remove threat from environment.

        Phase 4: Eradication
        """
        db.incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "status": IncidentStatus.ERADICATED.value,
                "eradicated_date": datetime.utcnow(),
                "eradication_actions": eradication_actions
            }}
        )

        logger.info("Threat eradicated", extra={
            "incident_id": incident_id
        })

    def recover_systems(self, incident_id: str, recovery_actions: List[str]):
        """
        Restore systems to normal operations.

        Phase 5: Recovery
        """
        db.incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "status": IncidentStatus.RECOVERED.value,
                "recovered_date": datetime.utcnow(),
                "recovery_actions": recovery_actions
            }}
        )

        logger.info("Systems recovered", extra={
            "incident_id": incident_id
        })

    def close_incident(self, incident_id: str, root_cause: str, lessons_learned: str):
        """
        Close incident with post-mortem.

        Phase 6: Post-Incident Activity
        """
        incident = db.incidents.find_one({"incident_id": incident_id})

        # Calculate metrics
        total_duration = (datetime.utcnow() - incident["detected_date"]).total_seconds() / 3600

        post_mortem = {
            "incident_id": incident_id,
            "root_cause": root_cause,
            "lessons_learned": lessons_learned,
            "total_duration_hours": total_duration,
            "created_date": datetime.utcnow()
        }

        db.post_mortems.insert_one(post_mortem)

        db.incidents.update_one(
            {"incident_id": incident_id},
            {"$set": {
                "status": IncidentStatus.CLOSED.value,
                "closed_date": datetime.utcnow(),
                "root_cause": root_cause
            }}
        })

        logger.info("Incident closed", extra={
            "incident_id": incident_id,
            "duration_hours": total_duration
        })

    def generate_incident_report(self, incident_id: str) -> Dict:
        """
        Generate incident report for stakeholders.

        Required for compliance audits.
        """
        incident = db.incidents.find_one({"incident_id": incident_id})
        post_mortem = db.post_mortems.find_one({"incident_id": incident_id})

        report = {
            "incident_id": incident_id,
            "title": incident["title"],
            "severity": incident["severity"],
            "detection_date": incident["detected_date"].isoformat(),
            "closure_date": incident["closed_date"].isoformat() if incident["closed_date"] else None,

            # Impact
            "systems_affected": incident["systems_affected"],
            "data_affected": incident["data_affected"],
            "users_affected": incident["users_affected_count"],

            # Response
            "containment_actions": incident.get("containment_actions", []),
            "eradication_actions": incident.get("eradication_actions", []),
            "recovery_actions": incident.get("recovery_actions", []),

            # Post-mortem
            "root_cause": post_mortem.get("root_cause") if post_mortem else None,
            "lessons_learned": post_mortem.get("lessons_learned") if post_mortem else None
        }

        return report
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
