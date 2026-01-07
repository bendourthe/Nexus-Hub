---
template_id: compliance_governance_breach_protocols_c
template_name: Breach Protocols - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/c_incident_response_plan.md
  - privacy_protection/c_gdpr_compliance.md
related_templates:
  - compliance_frameworks/c_soc2_compliance.md
tools:
  - Forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - c
---

# Breach Protocols - C

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

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <syslog.h>
#include <uuid/uuid.h>

#define GDPR_NOTIFICATION_DEADLINE_HOURS 72

typedef enum {
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL
} RiskLevel;

typedef struct {
    char breach_id[37];
    char incident_id[37];
    time_t detected_date;
    RiskLevel risk_level;
    int notify_gdpr_authority;
    int notify_individuals;
    int notify_ccpa;
    time_t gdpr_deadline;
} BreachAssessment;

void generate_uuid(char *uuid_str) {
    uuid_t uuid;
    uuid_generate(uuid);
    uuid_unparse(uuid, uuid_str);
}

const char* get_risk_level_name(RiskLevel level) {
    switch(level) {
        case RISK_LOW: return "low";
        case RISK_MEDIUM: return "medium";
        case RISK_HIGH: return "high";
        case RISK_CRITICAL: return "critical";
        default: return "unknown";
    }
}

RiskLevel assess_risk_level(int users_affected) {
    if (users_affected > 10000) return RISK_CRITICAL;
    if (users_affected > 1000) return RISK_HIGH;
    if (users_affected > 100) return RISK_MEDIUM;
    return RISK_LOW;
}

int assess_breach(const char *incident_id, BreachAssessment *assessment) {
    // Simulated incident data
    int data_affected = 1;
    int users_affected_count = 5000;
    int ca_residents_affected = 1;

    if (!data_affected) {
        return -1; // Not a breach
    }

    RiskLevel risk_level = assess_risk_level(users_affected_count);

    generate_uuid(assessment->breach_id);
    strncpy(assessment->incident_id, incident_id, sizeof(assessment->incident_id) - 1);
    assessment->detected_date = time(NULL);
    assessment->risk_level = risk_level;
    assessment->notify_gdpr_authority = (risk_level >= RISK_MEDIUM);
    assessment->notify_individuals = (risk_level >= RISK_HIGH);
    assessment->notify_ccpa = ca_residents_affected;
    assessment->gdpr_deadline = assessment->detected_date + (GDPR_NOTIFICATION_DEADLINE_HOURS * 3600);

    syslog(LOG_ERR, "Data breach assessed: breach_id=%s, risk_level=%s",
           assessment->breach_id, get_risk_level_name(risk_level));

    return 0;
}

int notify_gdpr_authority(const char *breach_id, char *notification_id_out) {
    generate_uuid(notification_id_out);

    syslog(LOG_ERR, "GDPR authority notified: notification_id=%s, breach_id=%s",
           notification_id_out, breach_id);

    return 0;
}

int notify_individuals(const char *breach_id) {
    int affected_count = 5000; // Simulated

    const char *notification_content =
        "Subject: Important Security Notice\n\n"
        "We are writing to inform you of a data security incident.\n\n"
        "What Happened: Unauthorized access to customer database\n"
        "What Information Was Involved: Names, email addresses, account numbers\n"
        "What We Are Doing: Enhanced security measures, password resets, monitoring\n"
        "What You Can Do: Update your password, enable 2FA, monitor accounts\n\n"
        "Contact: security@company.com\n";

    syslog(LOG_ERR, "Individuals notified: breach_id=%s, count=%d",
           breach_id, affected_count);

    return affected_count;
}

int main() {
    openlog("breach_protocols", LOG_PID | LOG_CONS, LOG_USER);

    const char *incident_id = "incident-123";
    BreachAssessment assessment;

    if (assess_breach(incident_id, &assessment) == 0) {
        printf("Breach ID: %s\n", assessment.breach_id);
        printf("Risk Level: %s\n", get_risk_level_name(assessment.risk_level));
        printf("Notify GDPR Authority: %s\n", assessment.notify_gdpr_authority ? "Yes" : "No");
        printf("Notify Individuals: %s\n", assessment.notify_individuals ? "Yes" : "No");

        if (assessment.notify_gdpr_authority) {
            char notification_id[37];
            notify_gdpr_authority(assessment.breach_id, notification_id);
            printf("GDPR Notification ID: %s\n", notification_id);
        }

        if (assessment.notify_individuals) {
            int count = notify_individuals(assessment.breach_id);
            printf("Individuals notified: %d\n", count);
        }
    }

    closelog();
    return 0;
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
