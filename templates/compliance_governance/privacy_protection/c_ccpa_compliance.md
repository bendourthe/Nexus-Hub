---
template_id: compliance_governance_ccpa_c
template_name: CCPA Compliance - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/c_gdpr_compliance.md
tools:
  - syslog (logging)
tags:
  - ccpa
  - privacy
  - california
  - c
---

# CCPA Compliance - C

**California Consumer Privacy Act for C applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**5 Key Consumer Rights**: Right to Know, Right to Delete, Right to Opt-Out, Right to Non-Discrimination, Right to Correct

**Response Deadline**: 45 days

---

## Right to Know (CCPA §1798.100)

```c
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <time.h>

#define MAX_DATA_SIZE 4096
#define MAX_CATEGORIES 10
#define MAX_PURPOSES 10
#define CCPA_RESPONSE_DEADLINE_DAYS 45

typedef struct {
    char request_id[64];
    char consumer_id[64];
    time_t request_date;
    time_t response_deadline;
    char categories_collected[MAX_CATEGORIES][256];
    int category_count;
    char business_purposes[MAX_PURPOSES][256];
    int purpose_count;
    char third_parties[MAX_DATA_SIZE];
    char specific_pieces[MAX_DATA_SIZE];
} ccpa_disclosure_response_t;

int process_right_to_know(const char *consumer_id, ccpa_disclosure_response_t *response) {
    time_t now = time(NULL);

    // Generate request ID
    snprintf(response->request_id, sizeof(response->request_id),
             "CCPA-%ld", now);
    strncpy(response->consumer_id, consumer_id, sizeof(response->consumer_id) - 1);
    response->request_date = now;
    response->response_deadline = now + (CCPA_RESPONSE_DEADLINE_DAYS * 24 * 60 * 60);

    // Categories of personal information collected
    response->category_count = 5;
    strncpy(response->categories_collected[0],
            "Identifiers (name, email, IP address)",
            sizeof(response->categories_collected[0]) - 1);
    strncpy(response->categories_collected[1],
            "Commercial information (purchase history, browsing history)",
            sizeof(response->categories_collected[1]) - 1);
    strncpy(response->categories_collected[2],
            "Internet or network activity (cookies, logs)",
            sizeof(response->categories_collected[2]) - 1);
    strncpy(response->categories_collected[3],
            "Geolocation data (approximate location from IP)",
            sizeof(response->categories_collected[3]) - 1);
    strncpy(response->categories_collected[4],
            "Inferences (preferences, characteristics)",
            sizeof(response->categories_collected[4]) - 1);

    // Business purposes
    response->purpose_count = 5;
    strncpy(response->business_purposes[0],
            "Providing and improving services",
            sizeof(response->business_purposes[0]) - 1);
    strncpy(response->business_purposes[1],
            "Customer support and communication",
            sizeof(response->business_purposes[1]) - 1);
    strncpy(response->business_purposes[2],
            "Security and fraud prevention",
            sizeof(response->business_purposes[2]) - 1);
    strncpy(response->business_purposes[3],
            "Legal compliance",
            sizeof(response->business_purposes[3]) - 1);
    strncpy(response->business_purposes[4],
            "Marketing (with explicit consent)",
            sizeof(response->business_purposes[4]) - 1);

    // Third parties
    snprintf(response->third_parties, sizeof(response->third_parties),
             "Service providers: AWS (hosting), Stripe (payments); "
             "Analytics providers: Google Analytics (with anonymization); "
             "Security providers: Cloudflare (DDoS protection)");

    // Specific pieces of personal information
    snprintf(response->specific_pieces, sizeof(response->specific_pieces),
             "{\"profile\": {\"name\": \"User\", \"email\": \"user@example.com\"}, "
             "\"account_created\": \"2023-01-15\", "
             "\"last_login\": \"2025-12-05\", "
             "\"orders\": []}");

    syslog(LOG_INFO, "CCPA right to know processed: request_id=%s, consumer_id=%s",
           response->request_id, consumer_id);

    return 0;
}
```

---

## Right to Delete (CCPA §1798.105)

```c
typedef struct {
    char status[32];
    char request_id[64];
    char reason[256];
    int exception_count;
    char exceptions[10][128];
    time_t deletion_date;
} ccpa_deletion_result_t;

int verify_consumer_identity(const char *consumer_id, const char *verification_method) {
    // Implement 2-factor verification for sensitive data
    return 1; // Success
}

int check_deletion_exceptions(const char *consumer_id, ccpa_deletion_result_t *result) {
    result->exception_count = 0;

    // §1798.105(d)(1): Complete transaction
    int has_active_orders = 0; // Check database
    if (has_active_orders) {
        strncpy(result->exceptions[result->exception_count++],
                "Active orders pending completion",
                sizeof(result->exceptions[0]) - 1);
    }

    // §1798.105(d)(2): Security incidents, fraud, illegal activity
    int has_security_investigation = 0; // Check database
    if (has_security_investigation) {
        strncpy(result->exceptions[result->exception_count++],
                "Ongoing security incident investigation",
                sizeof(result->exceptions[0]) - 1);
    }

    // §1798.105(d)(5): Internal uses (legal obligations)
    int has_financial_records = 0; // Check database
    if (has_financial_records) {
        strncpy(result->exceptions[result->exception_count++],
                "Tax and accounting retention requirement (7 years)",
                sizeof(result->exceptions[0]) - 1);
    }

    // §1798.105(d)(7): Comply with legal obligation
    int has_legal_hold = 0; // Check database
    if (has_legal_hold) {
        strncpy(result->exceptions[result->exception_count++],
                "Legal hold or pending litigation",
                sizeof(result->exceptions[0]) - 1);
    }

    return result->exception_count;
}

void delete_consumer_data(const char *consumer_id, const char *request_id) {
    // Delete from all systems:
    // - User profile
    // - Preferences
    // - Analytics data
    // - Cookies and tracking data
    //
    // Pseudonymize transaction data (retain for legal compliance)

    syslog(LOG_ALERT, "Data deletion executed: consumer_id=%s, request_id=%s",
           consumer_id, request_id);
}

int process_right_to_delete(const char *consumer_id,
                            const char *verification_method,
                            ccpa_deletion_result_t *result) {
    time_t now = time(NULL);
    snprintf(result->request_id, sizeof(result->request_id), "ERASE-%ld", now);

    // Verify consumer identity (2-factor for sensitive data)
    if (!verify_consumer_identity(consumer_id, verification_method)) {
        strncpy(result->status, "Verification Failed", sizeof(result->status) - 1);
        strncpy(result->reason, "Unable to verify consumer identity",
                sizeof(result->reason) - 1);

        syslog(LOG_WARNING, "Deletion verification failed: request_id=%s",
               result->request_id);
        return -1;
    }

    // Check for deletion exceptions (§1798.105(d))
    int exception_count = check_deletion_exceptions(consumer_id, result);

    if (exception_count > 0) {
        strncpy(result->status, "Denied", sizeof(result->status) - 1);
        strncpy(result->reason, "Legal obligations require data retention",
                sizeof(result->reason) - 1);

        syslog(LOG_WARNING, "Deletion denied: request_id=%s, exceptions=%d",
               result->request_id, exception_count);
        return -1;
    }

    // Perform deletion
    delete_consumer_data(consumer_id, result->request_id);

    strncpy(result->status, "Completed", sizeof(result->status) - 1);
    result->deletion_date = now;

    syslog(LOG_ALERT, "Consumer data deleted: request_id=%s, consumer_id=%s",
           result->request_id, consumer_id);

    return 0;
}
```

---

## Right to Opt-Out of Sale (CCPA §1798.120)

```c
typedef struct {
    char status[32];
    char opt_out_id[64];
    time_t opt_out_date;
    char message[256];
} ccpa_opt_out_result_t;

void update_opt_out_preference(const char *consumer_id, int opted_out) {
    // Update database with opt-out preference
}

void notify_third_parties(const char *consumer_id) {
    // Notify any third parties about opt-out status
}

void record_affirmative_consent(const char *consumer_id, const char *consent_text) {
    // Store consent with timestamp for audit
    time_t now = time(NULL);
    syslog(LOG_INFO, "Affirmative consent recorded: consumer_id=%s, timestamp=%ld",
           consumer_id, now);
}

int process_opt_out(const char *consumer_id, ccpa_opt_out_result_t *result) {
    time_t now = time(NULL);

    snprintf(result->opt_out_id, sizeof(result->opt_out_id), "OPT-OUT-%ld", now);

    // Update consumer preferences
    update_opt_out_preference(consumer_id, 1);

    // Notify third parties (if any data sharing for monetary consideration)
    notify_third_parties(consumer_id);

    strncpy(result->status, "Completed", sizeof(result->status) - 1);
    result->opt_out_date = now;
    strncpy(result->message,
            "Your opt-out preference has been recorded. "
            "We will not sell your personal information.",
            sizeof(result->message) - 1);

    syslog(LOG_INFO, "Consumer opted out: opt_out_id=%s, consumer_id=%s",
           result->opt_out_id, consumer_id);

    return 0;
}

int process_opt_in(const char *consumer_id,
                   const char *affirmative_consent_text,
                   ccpa_opt_out_result_t *result) {
    time_t now = time(NULL);

    snprintf(result->opt_out_id, sizeof(result->opt_out_id), "OPT-IN-%ld", now);

    // Record affirmative consent
    record_affirmative_consent(consumer_id, affirmative_consent_text);

    // Update consumer preferences
    update_opt_out_preference(consumer_id, 0);

    strncpy(result->status, "Completed", sizeof(result->status) - 1);
    result->opt_out_date = now;
    strncpy(result->message, "Your consent has been recorded.",
            sizeof(result->message) - 1);

    syslog(LOG_INFO, "Consumer opted in: opt_in_id=%s, consumer_id=%s",
           result->opt_out_id, consumer_id);

    return 0;
}
```

---

## Right to Non-Discrimination (CCPA §1798.125)

```c
typedef struct {
    int access_granted;
    char service_level[32];
    char pricing[32];
    char message[128];
} service_access_result_t;

int get_ccpa_request_count(const char *consumer_id) {
    // Query database for CCPA request history
    return 0; // Count of requests
}

int validate_service_access(const char *consumer_id,
                            const char *service_type,
                            service_access_result_t *result) {
    // Check if consumer has exercised CCPA rights
    int ccpa_request_count = get_ccpa_request_count(consumer_id);

    if (ccpa_request_count > 0) {
        syslog(LOG_INFO,
               "Consumer with CCPA requests accessing service: "
               "consumer_id=%s, service_type=%s, request_count=%d",
               consumer_id, service_type, ccpa_request_count);
    }

    // CRITICAL: Must provide same service regardless of CCPA activity
    result->access_granted = 1;
    strncpy(result->service_level, "Standard", sizeof(result->service_level) - 1);
    strncpy(result->pricing, "Standard", sizeof(result->pricing) - 1);
    strncpy(result->message, "Full access granted", sizeof(result->message) - 1);

    return 0;
}
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete honored with exception handling (§1798.105(d))
- [ ] "Do Not Sell" link prominently displayed on homepage
- [ ] Opt-out mechanism operational and immediate
- [ ] Non-discrimination enforced (same pricing, service level)
- [ ] 2-factor verification for sensitive data deletion
- [ ] Third-party notification system for opt-outs
- [ ] Audit logs for all CCPA requests via syslog

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
