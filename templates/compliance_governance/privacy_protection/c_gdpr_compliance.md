---
template_id: compliance_governance_gdpr_c
template_name: GDPR Compliance - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/c_iso27001_implementation.md
tools:
  - syslog (logging)
tags:
  - gdpr
  - privacy
  - data-protection
  - c
---

# GDPR Compliance - C

**General Data Protection Regulation for C applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Right to Access (Art. 15)

```c
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <time.h>

#define MAX_DATA_SIZE 4096
#define GDPR_RESPONSE_DEADLINE_DAYS 30

typedef struct {
    char request_id[64];
    char data_subject_id[64];
    time_t request_date;
    time_t response_deadline;
    char personal_data[MAX_DATA_SIZE];
    char processing_purposes[1024];
    char recipients[1024];
} gdpr_access_report_t;

int process_access_request(const char *data_subject_id, gdpr_access_report_t *report) {
    time_t now = time(NULL);

    snprintf(report->request_id, sizeof(report->request_id), "GDPR-%ld", now);
    strncpy(report->data_subject_id, data_subject_id, sizeof(report->data_subject_id) - 1);
    report->request_date = now;
    report->response_deadline = now + (GDPR_RESPONSE_DEADLINE_DAYS * 24 * 60 * 60);

    // Collect personal data
    snprintf(report->personal_data, sizeof(report->personal_data),
             "Profile: {name: User, email: user@example.com}");

    snprintf(report->processing_purposes, sizeof(report->processing_purposes),
             "Providing services, Improving user experience");

    snprintf(report->recipients, sizeof(report->recipients),
             "Cloud providers, Payment processors");

    syslog(LOG_INFO, "GDPR access request processed: request_id=%s, data_subject_id=%s",
           report->request_id, data_subject_id);

    return 0;
}
```

---

## Right to Erasure (Art. 17)

```c
typedef struct {
    char status[32];
    char request_id[64];
    char reason[256];
    int exception_count;
    char exceptions[10][128];
    time_t erasure_date;
} erasure_result_t;

int check_erasure_exceptions(const char *data_subject_id, erasure_result_t *result) {
    result->exception_count = 0;

    // Check for legal obligations
    int has_legal_obligation = 0; // Check financial records

    if (has_legal_obligation) {
        strncpy(result->exceptions[result->exception_count++],
                "Legal retention obligation (7 years for financial records)",
                sizeof(result->exceptions[0]) - 1);
    }

    return result->exception_count;
}

int process_erasure_request(const char *data_subject_id, erasure_result_t *result) {
    time_t now = time(NULL);
    snprintf(result->request_id, sizeof(result->request_id), "ERASE-%ld", now);

    // Check exceptions
    int exception_count = check_erasure_exceptions(data_subject_id, result);

    if (exception_count > 0) {
        strncpy(result->status, "Denied", sizeof(result->status) - 1);
        strncpy(result->reason, "Legal obligations require data retention",
                sizeof(result->reason) - 1);

        syslog(LOG_WARNING, "Erasure denied: request_id=%s, exceptions=%d",
               result->request_id, exception_count);

        return -1;
    }

    // Perform erasure
    strncpy(result->status, "Completed", sizeof(result->status) - 1);
    result->erasure_date = now;

    syslog(LOG_ALERT, "Personal data erased: request_id=%s, data_subject_id=%s",
           result->request_id, data_subject_id);

    return 0;
}
```

---

## Consent Management

```c
typedef struct {
    char consent_id[64];
    char data_subject_id[64];
    char purpose[256];
    int consent_given;
    time_t timestamp;
} consent_record_t;

int record_consent(const char *data_subject_id, const char *purpose,
                   int consent_given, consent_record_t *record) {
    time_t now = time(NULL);

    snprintf(record->consent_id, sizeof(record->consent_id), "CONSENT-%ld", now);
    strncpy(record->data_subject_id, data_subject_id, sizeof(record->data_subject_id) - 1);
    strncpy(record->purpose, purpose, sizeof(record->purpose) - 1);
    record->consent_given = consent_given;
    record->timestamp = now;

    syslog(LOG_INFO, "Consent recorded: consent_id=%s, purpose=%s, given=%d",
           record->consent_id, purpose, consent_given);

    return 0;
}

int withdraw_consent(const char *data_subject_id, const char *consent_id) {
    syslog(LOG_WARNING, "Consent withdrawn: data_subject_id=%s, consent_id=%s",
           data_subject_id, consent_id);

    return 0;
}
```

---

## Success Criteria

- [ ] Access requests processed within 30 days
- [ ] Erasure honored with exception handling
- [ ] Consent recorded and withdrawable

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
