---
template_id: compliance_governance_iso27001_c
template_name: ISO 27001 Implementation - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/c_soc2_compliance.md
related_templates:
  - risk_management/c_risk_assessment.md
tools:
  - OpenSSL (cryptography)
  - syslog (logging)
tags:
  - iso27001
  - isms
  - information-security
  - c
---

# ISO 27001:2022 Implementation - C

**Information Security Management System for C applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**: Organizational (37), People (8), Physical (14), Technological (34)
**Total**: 93 controls

---

## Control 5.17: Authentication Information

```c
#include <string.h>
#include <ctype.h>
#include <syslog.h>
#include <time.h>

#define PASSWORD_MIN_LENGTH 12
#define PASSWORD_MAX_AGE_DAYS 90
#define MAX_FAILED_ATTEMPTS 5

/**
 * Validate password complexity.
 *
 * ISO 27001 Control 5.17: Authentication information
 */
int validate_password_strength(const char *password, char *violations[], int *violation_count) {
    *violation_count = 0;
    size_t len = strlen(password);

    if (len < PASSWORD_MIN_LENGTH) {
        violations[(*violation_count)++] = "Password must be at least 12 characters";
    }

    int has_upper = 0, has_lower = 0, has_digit = 0, has_special = 0;

    for (size_t i = 0; i < len; i++) {
        if (isupper(password[i])) has_upper = 1;
        if (islower(password[i])) has_lower = 1;
        if (isdigit(password[i])) has_digit = 1;
        if (ispunct(password[i])) has_special = 1;
    }

    if (!has_upper) violations[(*violation_count)++] = "Must contain uppercase letter";
    if (!has_lower) violations[(*violation_count)++] = "Must contain lowercase letter";
    if (!has_digit) violations[(*violation_count)++] = "Must contain number";
    if (!has_special) violations[(*violation_count)++] = "Must contain special character";

    int compliant = (*violation_count == 0);

    if (!compliant) {
        syslog(LOG_WARNING, "Password validation failed: violation_count=%d", *violation_count);
    }

    return compliant;
}

/**
 * Record failed login attempt.
 *
 * ISO 27001 Control 8.3: Account lockout
 */
int record_failed_login(const char *user_id, int *failed_attempts) {
    (*failed_attempts)++;

    syslog(LOG_WARNING, "Failed login: user_id=%s, attempts=%d", user_id, *failed_attempts);

    if (*failed_attempts >= MAX_FAILED_ATTEMPTS) {
        syslog(LOG_ALERT, "Account locked: user_id=%s, attempts=%d", user_id, *failed_attempts);
        return 1; // Account locked
    }

    return 0; // Account still active
}
```

---

## Control 8.16: Monitoring Activities

```c
#include <stdio.h>
#include <time.h>

typedef struct {
    char user_id[64];
    time_t timestamp;
    int success;
    char ip_address[46];
} auth_log_t;

/**
 * Detect authentication anomalies.
 *
 * ISO 27001 Control 8.16: Monitoring activities
 */
int detect_auth_anomalies(const auth_log_t *logs, int log_count, const char *user_id) {
    int failed_count = 0;
    int night_access_count = 0;

    for (int i = 0; i < log_count; i++) {
        if (strcmp(logs[i].user_id, user_id) == 0) {
            if (!logs[i].success) {
                failed_count++;
            }

            struct tm *tm_info = localtime(&logs[i].timestamp);
            int hour = tm_info->tm_hour;

            // Check for unusual access times (2 AM - 5 AM)
            if (hour >= 2 && hour <= 5) {
                night_access_count++;
            }
        }
    }

    int anomalies_detected = 0;

    if (failed_count >= 5) {
        syslog(LOG_WARNING, "Anomaly detected: excessive failed logins, user_id=%s, count=%d",
               user_id, failed_count);
        anomalies_detected = 1;
    }

    if (night_access_count > 3) {
        syslog(LOG_WARNING, "Anomaly detected: unusual access time, user_id=%s, count=%d",
               user_id, night_access_count);
        anomalies_detected = 1;
    }

    return anomalies_detected;
}
```

---

## Success Criteria

- [ ] Password policy enforced (12+ chars, complexity)
- [ ] Account lockout after 5 failed attempts
- [ ] Failed login attempts logged to syslog
- [ ] Authentication anomalies detected
- [ ] Unusual access times monitored

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
