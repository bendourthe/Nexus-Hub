---
template_id: compliance_governance_breach_protocols_java
template_name: Breach Protocols - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/java_incident_response_plan.md
  - privacy_protection/java_gdpr_compliance.md
related_templates:
  - compliance_frameworks/java_soc2_compliance.md
tools:
  - Forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - java
---

# Breach Protocols - Java

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

```java
package com.organization.security;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
public class BreachNotificationService {

    private static final Logger logger = LoggerFactory.getLogger(BreachNotificationService.class);
    private static final int GDPR_NOTIFICATION_DEADLINE_HOURS = 72;

    public enum RiskLevel {
        LOW, MEDIUM, HIGH, CRITICAL
    }

    public Map<String, Object> assessBreach(String incidentId) {
        // Retrieve incident details
        // Map<String, Object> incident = incidentRepository.findById(incidentId);

        // Simulated incident for demonstration
        Map<String, Object> incident = new HashMap<>();
        incident.put("incident_id", incidentId);
        incident.put("data_affected", true);
        incident.put("detected_date", Instant.now());
        incident.put("users_affected_count", 5000);
        incident.put("ca_residents_affected", true);

        boolean isBreach = (Boolean) incident.getOrDefault("data_affected", false);

        if (!isBreach) {
            return Map.of("is_breach", false);
        }

        // Assess risk level
        RiskLevel riskLevel = assessRiskLevel(incident);

        String breachId = UUID.randomUUID().toString();
        Instant gdprDeadline = Instant.now().plus(
            GDPR_NOTIFICATION_DEADLINE_HOURS, ChronoUnit.HOURS);

        Map<String, Object> breachAssessment = new HashMap<>();
        breachAssessment.put("is_breach", true);
        breachAssessment.put("breach_id", breachId);
        breachAssessment.put("incident_id", incidentId);
        breachAssessment.put("detected_date", incident.get("detected_date"));
        breachAssessment.put("risk_level", riskLevel.toString());

        // Notification requirements
        breachAssessment.put("notify_gdpr_authority",
            riskLevel == RiskLevel.MEDIUM ||
            riskLevel == RiskLevel.HIGH ||
            riskLevel == RiskLevel.CRITICAL);
        breachAssessment.put("notify_individuals",
            riskLevel == RiskLevel.HIGH || riskLevel == RiskLevel.CRITICAL);
        breachAssessment.put("notify_ccpa",
            (Boolean) incident.getOrDefault("ca_residents_affected", false));

        // Deadlines
        breachAssessment.put("gdpr_deadline", gdprDeadline);

        // breachAssessmentRepository.save(breachAssessment);

        logger.error("Data breach assessed: breach_id={}, risk_level={}",
                    breachId, riskLevel);

        return breachAssessment;
    }

    private RiskLevel assessRiskLevel(Map<String, Object> incident) {
        int usersAffected = (Integer) incident.getOrDefault("users_affected_count", 0);

        if (usersAffected > 10000) {
            return RiskLevel.CRITICAL;
        } else if (usersAffected > 1000) {
            return RiskLevel.HIGH;
        } else if (usersAffected > 100) {
            return RiskLevel.MEDIUM;
        } else {
            return RiskLevel.LOW;
        }
    }

    public String notifyGdprAuthority(String breachId) {
        // Retrieve breach assessment
        // Map<String, Object> breach = breachAssessmentRepository.findById(breachId);

        String notificationId = UUID.randomUUID().toString();

        Map<String, Object> notification = new HashMap<>();
        notification.put("notification_id", notificationId);
        notification.put("breach_id", breachId);
        notification.put("notification_type", "gdpr_authority");
        notification.put("notification_date", Instant.now());

        // Article 33(3) required content
        notification.put("nature_of_breach", "Unauthorized access to customer database");
        notification.put("dpo_contact", "dpo@company.com");
        notification.put("likely_consequences", "Risk of identity theft for affected individuals");
        notification.put("measures_taken",
            "Database access revoked, passwords reset, monitoring enhanced");

        // breachNotificationRepository.save(notification);

        // Send notification to authority
        sendToAuthority(notification);

        logger.error("GDPR authority notified: notification_id={}", notificationId);

        return notificationId;
    }

    public int notifyIndividuals(String breachId) {
        // Retrieve breach assessment and affected users
        // Map<String, Object> breach = breachAssessmentRepository.findById(breachId);
        // List<User> affectedUsers = getAffectedUsers(breach);

        // Simulated affected users
        int affectedCount = 5000;

        String notificationContent = """
            Subject: Important Security Notice

            We are writing to inform you of a data security incident.

            What Happened: Unauthorized access to customer database

            What Information Was Involved: Names, email addresses, account numbers

            What We Are Doing: Enhanced security measures, password resets, monitoring

            What You Can Do: Update your password, enable 2FA, monitor accounts

            Contact: security@company.com
            """;

        // for (User user : affectedUsers) {
        //     sendNotificationEmail(user, notificationContent);
        // }

        logger.error("Individuals notified: breach_id={}, count={}", breachId, affectedCount);

        return affectedCount;
    }

    public void notifyCcpa(String breachId) {
        logger.info("CCPA notification initiated: breach_id={}", breachId);

        // California-specific notification requirements
        // Send to California Attorney General if > 500 CA residents affected
    }

    private void sendToAuthority(Map<String, Object> notification) {
        // In production: Send to supervisory authority via official channels
        logger.info("Sending notification to GDPR supervisory authority");
    }

    private void sendNotificationEmail(String user, String content) {
        // In production: Send email via email service
        logger.info("Sending breach notification email to user");
    }

    public Map<String, Object> generateBreachReport(String breachId) {
        Map<String, Object> report = new HashMap<>();
        report.put("report_id", UUID.randomUUID().toString());
        report.put("breach_id", breachId);
        report.put("generated_date", Instant.now());

        // Report sections
        report.put("executive_summary", "Summary of breach incident");
        report.put("timeline", "Detailed timeline of events");
        report.put("impact_analysis", "Analysis of affected systems and data");
        report.put("response_actions", "Actions taken to contain and remediate");
        report.put("lessons_learned", "Key takeaways and improvements");

        // breachReportRepository.save(report);

        logger.info("Breach report generated: breach_id={}", breachId);

        return report;
    }
}
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
