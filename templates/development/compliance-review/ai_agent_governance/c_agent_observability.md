---
template_id: compliance_governance_agent_observability_c
template_name: AI Agent Observability - C
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
  - compliance_frameworks/c_nist_ai_rmf.md
related_templates:
  - ai_agent_governance/c_agent_security.md
tools:
  - syslog
  - Prometheus C client
tags:
  - observability
  - monitoring
  - audit-everything
  - four-pillars
  - c
---

# AI Agent Observability - C

**🔍 Pillar 4: Observability (Audit Everything)**

Monitor AI agent behavior, decisions, and performance

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Audit Everything**: Complete visibility into AI agent operations

**Key Metrics**:
- Decision logging
- Performance monitoring
- Drift detection
- Audit trails

---

## Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <syslog.h>
#include <uuid/uuid.h>

#define MAX_INPUT_SIZE 4096
#define MAX_OUTPUT_SIZE 4096

typedef struct {
    char decision_id[37];
    char agent_id[37];
    char request_id[37];
    time_t timestamp;
    char input[MAX_INPUT_SIZE];
    char output[MAX_OUTPUT_SIZE];
    double confidence;
    char model_version[32];
} AgentDecision;

typedef struct {
    char alert_id[37];
    char agent_id[37];
    char alert_type[64];
    double drift_percentage;
    time_t timestamp;
} DriftAlert;

typedef struct {
    char agent_id[37];
    int total_requests;
    int average_latency_ms;
    double error_rate;
    double confidence_avg;
} AgentMetrics;

typedef struct {
    char log_id[37];
    char agent_id[37];
    char request_id[37];
    long latency_ms;
    int success;
    time_t timestamp;
} PerformanceLog;

/* Generate UUID */
void generate_uuid(char *uuid_str) {
    uuid_t uuid;
    uuid_generate(uuid);
    uuid_unparse(uuid, uuid_str);
}

/* Log agent decision */
int log_decision(
    const char *agent_id,
    const char *request_id,
    const char *input,
    const char *output,
    double confidence)
{
    AgentDecision decision;

    generate_uuid(decision.decision_id);
    strncpy(decision.agent_id, agent_id, sizeof(decision.agent_id) - 1);
    strncpy(decision.request_id, request_id, sizeof(decision.request_id) - 1);
    decision.timestamp = time(NULL);
    strncpy(decision.input, input, sizeof(decision.input) - 1);
    strncpy(decision.output, output, sizeof(decision.output) - 1);
    decision.confidence = confidence;
    strncpy(decision.model_version, "1.0.0", sizeof(decision.model_version) - 1);

    /* In production, save to decision repository */

    syslog(LOG_INFO,
           "Agent decision logged: agent_id=%s, request_id=%s, confidence=%.2f",
           agent_id, request_id, confidence);

    return 0;
}

/* Detect model drift */
int detect_drift(
    const char *agent_id,
    double current_metric,
    double baseline_metric)
{
    double drift_percentage = fabs((current_metric - baseline_metric) / baseline_metric) * 100;

    if (drift_percentage > 10.0) {
        DriftAlert alert;

        generate_uuid(alert.alert_id);
        strncpy(alert.agent_id, agent_id, sizeof(alert.agent_id) - 1);
        strncpy(alert.alert_type, "model_drift", sizeof(alert.alert_type) - 1);
        alert.drift_percentage = drift_percentage;
        alert.timestamp = time(NULL);

        /* In production, save to alert repository */

        syslog(LOG_WARNING,
               "Model drift detected: agent_id=%s, drift=%.2f%%",
               agent_id, drift_percentage);
    }

    return 0;
}

/* Get agent metrics */
int get_agent_metrics(const char *agent_id, AgentMetrics *metrics) {
    strncpy(metrics->agent_id, agent_id, sizeof(metrics->agent_id) - 1);
    metrics->total_requests = 1000;
    metrics->average_latency_ms = 150;
    metrics->error_rate = 0.01;
    metrics->confidence_avg = 0.85;

    syslog(LOG_INFO, "Agent metrics retrieved: agent_id=%s", agent_id);

    return 0;
}

/* Track performance */
int track_performance(
    const char *agent_id,
    const char *request_id,
    long latency_ms,
    int success)
{
    PerformanceLog perf_log;

    generate_uuid(perf_log.log_id);
    strncpy(perf_log.agent_id, agent_id, sizeof(perf_log.agent_id) - 1);
    strncpy(perf_log.request_id, request_id, sizeof(perf_log.request_id) - 1);
    perf_log.latency_ms = latency_ms;
    perf_log.success = success;
    perf_log.timestamp = time(NULL);

    /* In production, save to performance repository */

    if (latency_ms > 1000) {
        syslog(LOG_WARNING,
               "High latency detected: agent_id=%s, latency_ms=%ld",
               agent_id, latency_ms);
    }

    syslog(LOG_INFO,
           "Performance tracked: agent_id=%s, request_id=%s, latency_ms=%ld, success=%d",
           agent_id, request_id, latency_ms, success);

    return 0;
}

/* Log audit event */
typedef struct {
    char event_id[37];
    char agent_id[37];
    char event_type[64];
    char user_id[37];
    char event_data[1024];
    time_t timestamp;
} AuditEvent;

int log_audit_event(
    const char *agent_id,
    const char *event_type,
    const char *user_id,
    const char *event_data)
{
    AuditEvent event;

    generate_uuid(event.event_id);
    strncpy(event.agent_id, agent_id, sizeof(event.agent_id) - 1);
    strncpy(event.event_type, event_type, sizeof(event.event_type) - 1);
    strncpy(event.user_id, user_id, sizeof(event.user_id) - 1);
    strncpy(event.event_data, event_data, sizeof(event.event_data) - 1);
    event.timestamp = time(NULL);

    /* In production, save to audit repository */

    syslog(LOG_INFO,
           "Audit event logged: agent_id=%s, event_type=%s, user_id=%s",
           agent_id, event_type, user_id);

    return 0;
}

/* Calculate accuracy */
double calculate_accuracy(
    const char *agent_id,
    const double *predictions,
    const double *actuals,
    int count)
{
    if (count == 0) {
        return 0.0;
    }

    int correct = 0;
    for (int i = 0; i < count; i++) {
        if (fabs(predictions[i] - actuals[i]) < 0.001) {
            correct++;
        }
    }

    double accuracy = (double)correct / count;

    syslog(LOG_INFO,
           "Accuracy calculated: agent_id=%s, accuracy=%.2f, samples=%d",
           agent_id, accuracy, count);

    return accuracy;
}

/* Example usage */
int main() {
    openlog("agent_observability", LOG_PID | LOG_CONS, LOG_USER);

    const char *agent_id = "agent-123";
    const char *request_id = "req-456";

    /* Log decision */
    log_decision(
        agent_id,
        request_id,
        "{\"transaction_amount\": 1500}",
        "{\"fraud_probability\": 0.12}",
        0.88
    );

    /* Track performance */
    track_performance(agent_id, request_id, 145, 1);

    /* Detect drift */
    detect_drift(agent_id, 0.75, 0.85);

    /* Get metrics */
    AgentMetrics metrics;
    get_agent_metrics(agent_id, &metrics);
    printf("Total requests: %d\n", metrics.total_requests);
    printf("Avg latency: %d ms\n", metrics.average_latency_ms);
    printf("Error rate: %.4f\n", metrics.error_rate);

    /* Log audit event */
    log_audit_event(
        agent_id,
        "model_update",
        "user789",
        "{\"version\": \"1.1.0\"}"
    );

    /* Calculate accuracy */
    double predictions[] = {1.0, 0.0, 1.0, 1.0};
    double actuals[] = {1.0, 0.0, 1.0, 0.0};
    double accuracy = calculate_accuracy(agent_id, predictions, actuals, 4);
    printf("Accuracy: %.2f\n", accuracy);

    closelog();
    return 0;
}
```

---

## Success Criteria

- [ ] Decision logging operational
- [ ] Performance metrics tracked
- [ ] Drift detection functional
- [ ] Audit trails comprehensive

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
