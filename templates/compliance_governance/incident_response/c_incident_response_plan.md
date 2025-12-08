---
template_id: compliance_governance_incident_response_c
template_name: Incident Response Plan - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/c_soc2_compliance.md
  - compliance_frameworks/c_iso27001_implementation.md
related_templates:
  - incident_response/c_breach_protocols.md
  - privacy_protection/c_gdpr_compliance.md
tools:
  - PagerDuty (alerting)
  - JIRA (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - c
---

# Incident Response Plan - C

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

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <syslog.h>
#include <uuid/uuid.h>

typedef enum {
    SEVERITY_P1_CRITICAL,
    SEVERITY_P2_HIGH,
    SEVERITY_P3_MEDIUM,
    SEVERITY_P4_LOW
} IncidentSeverity;

typedef enum {
    STATUS_DETECTED,
    STATUS_INVESTIGATING,
    STATUS_CONTAINED,
    STATUS_ERADICATED,
    STATUS_RECOVERED,
    STATUS_CLOSED
} IncidentStatus;

typedef struct {
    char incident_id[37];
    char title[256];
    char description[1024];
    IncidentSeverity severity;
    char incident_type[128];
    char detected_by[128];
    time_t detected_date;
    IncidentStatus status;
    time_t response_deadline;
    char incident_commander[128];
    int data_affected;
    int users_affected_count;
} Incident;

static const int RESPONSE_SLA[] = {15, 60, 240, 1440}; // minutes

void generate_uuid(char *uuid_str) {
    uuid_t uuid;
    uuid_generate(uuid);
    uuid_unparse(uuid, uuid_str);
}

const char* get_severity_name(IncidentSeverity severity) {
    switch(severity) {
        case SEVERITY_P1_CRITICAL: return "p1_critical";
        case SEVERITY_P2_HIGH: return "p2_high";
        case SEVERITY_P3_MEDIUM: return "p3_medium";
        case SEVERITY_P4_LOW: return "p4_low";
        default: return "unknown";
    }
}

int create_incident(
    const char *title,
    const char *description,
    IncidentSeverity severity,
    const char *incident_type,
    const char *detected_by,
    char *incident_id_out)
{
    Incident incident = {0};

    generate_uuid(incident.incident_id);
    strncpy(incident.title, title, sizeof(incident.title) - 1);
    strncpy(incident.description, description, sizeof(incident.description) - 1);
    incident.severity = severity;
    strncpy(incident.incident_type, incident_type, sizeof(incident.incident_type) - 1);
    strncpy(incident.detected_by, detected_by, sizeof(incident.detected_by) - 1);
    incident.detected_date = time(NULL);
    incident.status = STATUS_DETECTED;
    incident.response_deadline = incident.detected_date + (RESPONSE_SLA[severity] * 60);

    // incidentRepo.save(&incident);

    // Alert for critical/high
    if (severity == SEVERITY_P1_CRITICAL || severity == SEVERITY_P2_HIGH) {
        syslog(LOG_ALERT, "ALERT: Critical incident created - incident_id=%s", incident.incident_id);
    }

    syslog(LOG_ERR, "Security incident created: incident_id=%s, severity=%s",
           incident.incident_id, get_severity_name(severity));

    strcpy(incident_id_out, incident.incident_id);
    return 0;
}

int contain_incident(const char *incident_id) {
    time_t contained_date = time(NULL);

    // incidentRepo.update(incident_id, STATUS_CONTAINED, contained_date);

    syslog(LOG_WARNING, "Incident contained: incident_id=%s", incident_id);
    return 0;
}

int eradicate_threat(const char *incident_id) {
    time_t eradicated_date = time(NULL);

    // incidentRepo.update(incident_id, STATUS_ERADICATED, eradicated_date);

    syslog(LOG_INFO, "Threat eradicated: incident_id=%s", incident_id);
    return 0;
}

int recover_systems(const char *incident_id) {
    time_t recovered_date = time(NULL);

    // incidentRepo.update(incident_id, STATUS_RECOVERED, recovered_date);

    syslog(LOG_INFO, "Systems recovered: incident_id=%s", incident_id);
    return 0;
}

int close_incident(const char *incident_id, const char *root_cause, const char *lessons_learned) {
    // Simulated incident for demonstration
    time_t detected_date = time(NULL) - (48 * 3600); // 48 hours ago

    // Calculate metrics
    double total_duration_hours = difftime(time(NULL), detected_date) / 3600.0;

    // Post-mortem
    char post_mortem_id[37];
    generate_uuid(post_mortem_id);

    // postMortemRepo.save(post_mortem_id, incident_id, root_cause, lessons_learned, total_duration_hours);

    time_t closed_date = time(NULL);
    // incidentRepo.update(incident_id, STATUS_CLOSED, closed_date, root_cause);

    syslog(LOG_INFO, "Incident closed: incident_id=%s, duration_hours=%.1f",
           incident_id, total_duration_hours);

    return 0;
}

typedef struct {
    char incident_id[37];
    char title[256];
    char severity[32];
    time_t detection_date;
    time_t closure_date;
    char systems_affected[5][128];
    int systems_affected_count;
    int data_affected;
    int users_affected;
    char containment_actions[5][256];
    int containment_actions_count;
    char eradication_actions[5][256];
    int eradication_actions_count;
    char recovery_actions[5][256];
    int recovery_actions_count;
    char root_cause[512];
    char lessons_learned[512];
} IncidentReport;

int generate_incident_report(const char *incident_id, IncidentReport *report) {
    // Simulated data for demonstration
    strncpy(report->incident_id, incident_id, sizeof(report->incident_id) - 1);
    strncpy(report->title, "Database breach detected", sizeof(report->title) - 1);
    strncpy(report->severity, "p1_critical", sizeof(report->severity) - 1);
    report->detection_date = time(NULL) - (48 * 3600);
    report->closure_date = time(NULL);

    // Systems affected
    strncpy(report->systems_affected[0], "database_server", 128);
    strncpy(report->systems_affected[1], "web_application", 128);
    report->systems_affected_count = 2;

    report->data_affected = 1;
    report->users_affected = 5000;

    // Containment actions
    strncpy(report->containment_actions[0], "Revoked access", 256);
    strncpy(report->containment_actions[1], "Changed passwords", 256);
    report->containment_actions_count = 2;

    // Eradication actions
    strncpy(report->eradication_actions[0], "Removed malware", 256);
    strncpy(report->eradication_actions[1], "Patched vulnerability", 256);
    report->eradication_actions_count = 2;

    // Recovery actions
    strncpy(report->recovery_actions[0], "Restored from backup", 256);
    strncpy(report->recovery_actions[1], "Verified integrity", 256);
    report->recovery_actions_count = 2;

    // Post-mortem
    strncpy(report->root_cause, "Unpatched SQL injection vulnerability", sizeof(report->root_cause) - 1);
    strncpy(report->lessons_learned, "Implement automated patching, enhance monitoring",
            sizeof(report->lessons_learned) - 1);

    return 0;
}

int main() {
    openlog("incident_response", LOG_PID | LOG_CONS, LOG_USER);

    char incident_id[37];
    create_incident(
        "Database breach detected",
        "Unauthorized access to customer database",
        SEVERITY_P1_CRITICAL,
        "data_breach",
        "security_team",
        incident_id
    );

    printf("Incident created: %s\n", incident_id);

    contain_incident(incident_id);
    eradicate_threat(incident_id);
    recover_systems(incident_id);
    close_incident(incident_id, "Unpatched SQL injection vulnerability",
                   "Implement automated patching, enhance monitoring");

    IncidentReport report;
    generate_incident_report(incident_id, &report);
    printf("Generated report for incident: %s\n", report.incident_id);
    printf("Severity: %s\n", report.severity);
    printf("Users affected: %d\n", report.users_affected);

    closelog();
    return 0;
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
