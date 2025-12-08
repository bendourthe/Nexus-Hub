---
template_id: compliance_governance_incident_response_java
template_name: Incident Response Plan - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/java_soc2_compliance.md
  - compliance_frameworks/java_iso27001_implementation.md
related_templates:
  - incident_response/java_breach_protocols.md
  - privacy_protection/java_gdpr_compliance.md
tools:
  - PagerDuty (alerting)
  - JIRA (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - java
---

# Incident Response Plan - Java

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

```java
package com.organization.security;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class IncidentResponseService {

    private static final Logger logger = LoggerFactory.getLogger(IncidentResponseService.class);

    public enum IncidentSeverity {
        P1_CRITICAL,  // System down, data breach
        P2_HIGH,      // Significant impact
        P3_MEDIUM,    // Moderate impact
        P4_LOW        // Minor issue
    }

    public enum IncidentStatus {
        DETECTED,
        INVESTIGATING,
        CONTAINED,
        ERADICATED,
        RECOVERED,
        CLOSED
    }

    // Response time SLAs (in minutes)
    private static final Map<IncidentSeverity, Integer> RESPONSE_SLA = Map.of(
        IncidentSeverity.P1_CRITICAL, 15,    // 15 minutes
        IncidentSeverity.P2_HIGH, 60,        // 1 hour
        IncidentSeverity.P3_MEDIUM, 240,     // 4 hours
        IncidentSeverity.P4_LOW, 1440        // 24 hours
    );

    public String createIncident(
            String title,
            String description,
            IncidentSeverity severity,
            String incidentType,
            String detectedBy) {

        String incidentId = UUID.randomUUID().toString();
        Instant responseDeadline = Instant.now().plus(
            RESPONSE_SLA.get(severity), ChronoUnit.MINUTES);

        Map<String, Object> incident = new HashMap<>();
        incident.put("incident_id", incidentId);
        incident.put("title", title);
        incident.put("description", description);
        incident.put("severity", severity.toString());
        incident.put("incident_type", incidentType);
        incident.put("detected_by", detectedBy);
        incident.put("detected_date", Instant.now());
        incident.put("status", IncidentStatus.DETECTED.toString());
        incident.put("response_deadline", responseDeadline);

        // Response team
        incident.put("incident_commander", null);
        incident.put("response_team", new ArrayList<String>());

        // Timeline
        incident.put("contained_date", null);
        incident.put("eradicated_date", null);
        incident.put("recovered_date", null);
        incident.put("closed_date", null);

        // Impact
        incident.put("systems_affected", new ArrayList<String>());
        incident.put("data_affected", false);
        incident.put("users_affected_count", 0);

        // incidentRepository.save(incident);

        // Alert response team for critical/high severity
        if (severity == IncidentSeverity.P1_CRITICAL || severity == IncidentSeverity.P2_HIGH) {
            alertResponseTeam(incidentId);
        }

        logger.error("Security incident created: incident_id={}, severity={}",
                    incidentId, severity);

        return incidentId;
    }

    public void containIncident(String incidentId, List<String> containmentActions) {
        Map<String, Object> updates = new HashMap<>();
        updates.put("status", IncidentStatus.CONTAINED.toString());
        updates.put("contained_date", Instant.now());
        updates.put("containment_actions", containmentActions);

        // incidentRepository.update(incidentId, updates);

        logger.warn("Incident contained: incident_id={}, actions={}",
                   incidentId, containmentActions);
    }

    public void eradicateThreat(String incidentId, List<String> eradicationActions) {
        Map<String, Object> updates = new HashMap<>();
        updates.put("status", IncidentStatus.ERADICATED.toString());
        updates.put("eradicated_date", Instant.now());
        updates.put("eradication_actions", eradicationActions);

        // incidentRepository.update(incidentId, updates);

        logger.info("Threat eradicated: incident_id={}", incidentId);
    }

    public void recoverSystems(String incidentId, List<String> recoveryActions) {
        Map<String, Object> updates = new HashMap<>();
        updates.put("status", IncidentStatus.RECOVERED.toString());
        updates.put("recovered_date", Instant.now());
        updates.put("recovery_actions", recoveryActions);

        // incidentRepository.update(incidentId, updates);

        logger.info("Systems recovered: incident_id={}", incidentId);
    }

    public void closeIncident(String incidentId, String rootCause, String lessonsLearned) {
        // Map<String, Object> incident = incidentRepository.findById(incidentId);

        // Simulated incident for demonstration
        Map<String, Object> incident = new HashMap<>();
        incident.put("incident_id", incidentId);
        incident.put("detected_date", Instant.now().minus(48, ChronoUnit.HOURS));

        // Calculate metrics
        Instant detectedDate = (Instant) incident.get("detected_date");
        long totalDurationHours = ChronoUnit.HOURS.between(detectedDate, Instant.now());

        Map<String, Object> postMortem = new HashMap<>();
        postMortem.put("incident_id", incidentId);
        postMortem.put("root_cause", rootCause);
        postMortem.put("lessons_learned", lessonsLearned);
        postMortem.put("total_duration_hours", totalDurationHours);
        postMortem.put("created_date", Instant.now());

        // postMortemRepository.save(postMortem);

        Map<String, Object> updates = new HashMap<>();
        updates.put("status", IncidentStatus.CLOSED.toString());
        updates.put("closed_date", Instant.now());
        updates.put("root_cause", rootCause);

        // incidentRepository.update(incidentId, updates);

        logger.info("Incident closed: incident_id={}, duration_hours={}",
                   incidentId, totalDurationHours);
    }

    public Map<String, Object> generateIncidentReport(String incidentId) {
        // Map<String, Object> incident = incidentRepository.findById(incidentId);
        // Map<String, Object> postMortem = postMortemRepository.findByIncidentId(incidentId);

        // Simulated data for demonstration
        Map<String, Object> incident = new HashMap<>();
        incident.put("incident_id", incidentId);
        incident.put("title", "Database breach detected");
        incident.put("severity", IncidentSeverity.P1_CRITICAL.toString());
        incident.put("detected_date", Instant.now().minus(48, ChronoUnit.HOURS));
        incident.put("closed_date", Instant.now());
        incident.put("systems_affected", Arrays.asList("database_server", "web_application"));
        incident.put("data_affected", true);
        incident.put("users_affected_count", 5000);
        incident.put("containment_actions", Arrays.asList("Revoked access", "Changed passwords"));
        incident.put("eradication_actions", Arrays.asList("Removed malware", "Patched vulnerability"));
        incident.put("recovery_actions", Arrays.asList("Restored from backup", "Verified integrity"));

        Map<String, Object> postMortem = new HashMap<>();
        postMortem.put("root_cause", "Unpatched SQL injection vulnerability");
        postMortem.put("lessons_learned", "Implement automated patching, enhance monitoring");

        Map<String, Object> report = new HashMap<>();
        report.put("incident_id", incidentId);
        report.put("title", incident.get("title"));
        report.put("severity", incident.get("severity"));
        report.put("detection_date", incident.get("detected_date"));
        report.put("closure_date", incident.get("closed_date"));

        // Impact
        report.put("systems_affected", incident.get("systems_affected"));
        report.put("data_affected", incident.get("data_affected"));
        report.put("users_affected", incident.get("users_affected_count"));

        // Response
        report.put("containment_actions", incident.get("containment_actions"));
        report.put("eradication_actions", incident.get("eradication_actions"));
        report.put("recovery_actions", incident.get("recovery_actions"));

        // Post-mortem
        report.put("root_cause", postMortem.get("root_cause"));
        report.put("lessons_learned", postMortem.get("lessons_learned"));

        return report;
    }

    public Map<String, Object> conductPostIncidentReview(
            String incidentId,
            String rootCause,
            List<String> lessonsLearned,
            List<String> correctiveActions) {

        Map<String, Object> review = new HashMap<>();
        review.put("review_id", UUID.randomUUID().toString());
        review.put("incident_id", incidentId);
        review.put("review_date", Instant.now());
        review.put("root_cause", rootCause);
        review.put("lessons_learned", lessonsLearned);
        review.put("corrective_actions", correctiveActions);

        // reviewRepository.save(review);

        logger.info("Post-incident review completed: incident_id={}", incidentId);

        return review;
    }

    private void alertResponseTeam(String incidentId) {
        // In production: PagerDuty, email, SMS alerts
        logger.error("ALERT: Critical incident created - incident_id={}", incidentId);
    }

    private void schedulePostIncidentReview(String incidentId) {
        // In production: create calendar event for post-incident review
        logger.info("Post-incident review scheduled: incident_id={}", incidentId);
    }
}
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
