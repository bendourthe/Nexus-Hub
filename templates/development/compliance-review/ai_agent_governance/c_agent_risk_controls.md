---
template_id: compliance_governance_agent_risk_controls_c
template_name: AI Agent Risk Controls - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/c_agent_lifecycle.md
  - risk_management/c_risk_assessment.md
related_templates:
  - ai_agent_governance/c_agent_security.md
tools:
  - syslog
tags:
  - risk-management
  - defense-in-depth
  - four-pillars
  - c
---

# AI Agent Risk Controls - C

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agent operations

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Defense in Depth**: Multiple layers of risk controls

**Risk Controls**:
- Rate limiting
- Circuit breakers
- Confidence thresholds
- Human-in-the-loop

---

## Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <syslog.h>
#include <uuid/uuid.h>

#define CONFIDENCE_THRESHOLD 0.7
#define RATE_LIMIT_PER_MINUTE 60
#define MAX_RISK_FACTORS 10

typedef enum {
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL
} RiskLevel;

typedef struct {
    char agent_id[37];
    RiskLevel risk_level;
    int requires_human_review;
    char risk_factors[MAX_RISK_FACTORS][128];
    int risk_factor_count;
    double confidence;
} RiskAssessment;

typedef struct {
    char agent_id[37];
    char status[16]; /* "open" or "closed" */
    char reason[256];
    time_t activated_at;
} CircuitBreaker;

/* Get risk level name */
const char* get_risk_level_name(RiskLevel level) {
    switch(level) {
        case RISK_LOW: return "low";
        case RISK_MEDIUM: return "medium";
        case RISK_HIGH: return "high";
        case RISK_CRITICAL: return "critical";
        default: return "unknown";
    }
}

/* Generate UUID */
void generate_uuid(char *uuid_str) {
    uuid_t uuid;
    uuid_generate(uuid);
    uuid_unparse(uuid, uuid_str);
}

/* Get request count (simulated) */
int get_request_count(const char *user_id) {
    /* In production, query last minute request count from cache/database */
    return 45; /* Simulated */
}

/* Check rate limit */
int check_rate_limit(const char *agent_id, const char *user_id) {
    int request_count = get_request_count(user_id);

    if (request_count >= RATE_LIMIT_PER_MINUTE) {
        syslog(LOG_WARNING,
               "Rate limit exceeded: agent_id=%s, user_id=%s, count=%d",
               agent_id, user_id, request_count);
        return 0; /* Rate limit exceeded */
    }

    return 1; /* Within rate limit */
}

/* Evaluate decision risk */
int evaluate_decision_risk(
    const char *agent_id,
    const void *decision, /* Generic pointer to decision data */
    double confidence,
    RiskAssessment *assessment)
{
    /* Initialize assessment */
    strncpy(assessment->agent_id, agent_id, sizeof(assessment->agent_id) - 1);
    assessment->risk_level = RISK_LOW;
    assessment->requires_human_review = 0;
    assessment->risk_factor_count = 0;
    assessment->confidence = confidence;

    /* Check confidence threshold */
    if (confidence < CONFIDENCE_THRESHOLD) {
        assessment->risk_level = RISK_HIGH;
        assessment->requires_human_review = 1;
        strncpy(assessment->risk_factors[assessment->risk_factor_count++],
                "Low confidence score", 128);
    }

    /* Check financial impact (simplified - in production, parse decision data) */
    double financial_impact = 0.0;
    /* Assume decision contains financial_impact field */
    /* financial_impact = get_financial_impact_from_decision(decision); */
    financial_impact = 15000.0; /* Simulated */

    if (financial_impact > 10000.0) {
        assessment->risk_level = RISK_CRITICAL;
        assessment->requires_human_review = 1;
        strncpy(assessment->risk_factors[assessment->risk_factor_count++],
                "High financial impact", 128);
    }

    /* Check PII access */
    int accesses_pii = 0; /* Simulated */
    if (accesses_pii) {
        if (assessment->risk_level < RISK_MEDIUM) {
            assessment->risk_level = RISK_MEDIUM;
        }
        strncpy(assessment->risk_factors[assessment->risk_factor_count++],
                "Accesses PII data", 128);
    }

    if (assessment->requires_human_review) {
        syslog(LOG_WARNING,
               "Decision requires human review: agent_id=%s, risk_level=%s",
               agent_id, get_risk_level_name(assessment->risk_level));
    }

    return 0;
}

/* Enable circuit breaker */
int enable_circuit_breaker(const char *agent_id, const char *reason) {
    CircuitBreaker cb;

    strncpy(cb.agent_id, agent_id, sizeof(cb.agent_id) - 1);
    strncpy(cb.status, "open", sizeof(cb.status) - 1);
    strncpy(cb.reason, reason, sizeof(cb.reason) - 1);
    cb.activated_at = time(NULL);

    /* In production, save to circuit breaker repository */

    syslog(LOG_ERR,
           "Circuit breaker activated: agent_id=%s, reason=%s",
           agent_id, reason);

    return 0;
}

/* Check circuit breaker */
int check_circuit_breaker(const char *agent_id) {
    /* In production, query circuit breaker state from repository */
    /* Return 0 if circuit is open (agent disabled), 1 if closed */
    return 1; /* Simulated - circuit closed */
}

/* Apply confidence threshold */
typedef struct {
    int approved;
    char reason[256];
    int requires_review;
    double confidence;
} ThresholdResult;

int apply_confidence_threshold(
    const char *agent_id,
    double confidence,
    ThresholdResult *result)
{
    if (confidence < CONFIDENCE_THRESHOLD) {
        syslog(LOG_WARNING,
               "Confidence below threshold: agent_id=%s, confidence=%.2f, threshold=%.2f",
               agent_id, confidence, CONFIDENCE_THRESHOLD);

        result->approved = 0;
        strncpy(result->reason, "Confidence below threshold", sizeof(result->reason) - 1);
        result->requires_review = 1;
        result->confidence = confidence;
        return 0;
    }

    result->approved = 1;
    result->reason[0] = '\0';
    result->requires_review = 0;
    result->confidence = confidence;
    return 1;
}

/* Check if action requires human approval */
int requires_human_approval(const char *agent_id, const char *action_type) {
    /* High-risk actions */
    const char *high_risk_actions[] = {
        "delete",
        "transfer_funds",
        "modify_permissions",
        NULL
    };

    for (int i = 0; high_risk_actions[i] != NULL; i++) {
        if (strcmp(action_type, high_risk_actions[i]) == 0) {
            syslog(LOG_WARNING,
                   "High-risk action requires approval: agent_id=%s, action_type=%s",
                   agent_id, action_type);
            return 1; /* Requires approval */
        }
    }

    return 0; /* Does not require approval */
}

/* Log risk decision */
int log_risk_decision(
    const char *agent_id,
    const RiskAssessment *assessment,
    int approved)
{
    char log_id[37];
    generate_uuid(log_id);

    /* In production, save to risk decision repository */

    syslog(LOG_INFO,
           "Risk decision logged: agent_id=%s, approved=%d",
           agent_id, approved);

    return 0;
}

/* Example usage */
int main() {
    openlog("agent_risk_controls", LOG_PID | LOG_CONS, LOG_USER);

    const char *agent_id = "agent-123";
    const char *user_id = "user-456";

    /* Check rate limit */
    int within_limit = check_rate_limit(agent_id, user_id);
    printf("Within rate limit: %d\n", within_limit);

    /* Evaluate decision risk */
    RiskAssessment assessment;
    evaluate_decision_risk(agent_id, NULL, 0.65, &assessment);
    printf("Risk level: %s\n", get_risk_level_name(assessment.risk_level));
    printf("Requires human review: %d\n", assessment.requires_human_review);
    printf("Risk factors:\n");
    for (int i = 0; i < assessment.risk_factor_count; i++) {
        printf("  - %s\n", assessment.risk_factors[i]);
    }

    /* Apply confidence threshold */
    ThresholdResult threshold_result;
    apply_confidence_threshold(agent_id, 0.65, &threshold_result);
    printf("Approved: %d\n", threshold_result.approved);
    if (!threshold_result.approved) {
        printf("Reason: %s\n", threshold_result.reason);
    }

    /* Check if action requires approval */
    int requires_approval = requires_human_approval(agent_id, "transfer_funds");
    printf("Requires approval for transfer_funds: %d\n", requires_approval);

    requires_approval = requires_human_approval(agent_id, "read_data");
    printf("Requires approval for read_data: %d\n", requires_approval);

    /* Enable circuit breaker */
    enable_circuit_breaker(agent_id, "Error rate exceeds threshold");

    /* Check circuit breaker */
    int circuit_closed = check_circuit_breaker(agent_id);
    printf("Circuit breaker closed: %d\n", circuit_closed);

    /* Log risk decision */
    log_risk_decision(agent_id, &assessment, 0);

    closelog();
    return 0;
}
```

---

## Success Criteria

- [ ] Rate limiting operational
- [ ] Confidence thresholds enforced
- [ ] Human-in-the-loop triggers functional
- [ ] Circuit breakers implemented

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
