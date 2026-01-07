---
template_id: compliance_governance_nist_ai_rmf_c
template_name: NIST AI RMF - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/c_iso27001_implementation.md
related_templates:
  - risk_management/c_risk_assessment.md
tools:
  - syslog (logging)
tags:
  - nist-ai-rmf
  - ai-governance
  - responsible-ai
  - c
---

# NIST AI Risk Management Framework - C

**NIST AI RMF 1.0 for C applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## GOVERN-1: AI System Inventory

```c
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <time.h>

typedef enum {
    SYSTEM_TYPE_TRADITIONAL_ML,
    SYSTEM_TYPE_GENERATIVE_AI,
    SYSTEM_TYPE_RECOMMENDATION
} ai_system_type_t;

typedef enum {
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_CRITICAL
} risk_level_t;

typedef struct {
    char system_id[64];
    char system_name[128];
    ai_system_type_t system_type;
    int is_generative;
    risk_level_t risk_level;
    time_t registered_at;
} ai_system_record_t;

int register_ai_system(const char *system_name, ai_system_type_t system_type,
                       int is_generative, ai_system_record_t *record) {
    snprintf(record->system_id, sizeof(record->system_id), "AI-%ld", time(NULL));
    strncpy(record->system_name, system_name, sizeof(record->system_name) - 1);
    record->system_type = system_type;
    record->is_generative = is_generative;
    record->risk_level = RISK_LEVEL_MEDIUM;
    record->registered_at = time(NULL);

    syslog(LOG_INFO, "AI system registered: system_id=%s, type=%d, is_generative=%d",
           record->system_id, system_type, is_generative);

    return 0;
}
```

---

## MEASURE-2: Bias Detection

```c
#include <math.h>

#define MAX_GROUPS 10
#define BIAS_THRESHOLD 0.1

typedef struct {
    int bias_detected;
    double demographic_parity_diff;
} bias_metrics_t;

double calculate_positive_rate(const double *predictions, const int *group_indices,
                               int count) {
    double sum = 0.0;
    for (int i = 0; i < count; i++) {
        sum += predictions[group_indices[i]];
    }
    return count > 0 ? sum / count : 0.0;
}

bias_metrics_t detect_bias(const char *system_id, const double *predictions, int pred_count,
                          const char **feature_values, int feature_count) {
    bias_metrics_t metrics = {0, 0.0};

    // Count unique groups
    const char *groups[MAX_GROUPS];
    int group_counts[MAX_GROUPS] = {0};
    int group_indices[MAX_GROUPS][1000];
    int num_groups = 0;

    // Group predictions by feature value
    for (int i = 0; i < feature_count && num_groups < MAX_GROUPS; i++) {
        int found = 0;
        for (int j = 0; j < num_groups; j++) {
            if (strcmp(feature_values[i], groups[j]) == 0) {
                group_indices[j][group_counts[j]++] = i;
                found = 1;
                break;
            }
        }
        if (!found) {
            groups[num_groups] = feature_values[i];
            group_indices[num_groups][group_counts[num_groups]++] = i;
            num_groups++;
        }
    }

    // Calculate rates for each group
    double rates[MAX_GROUPS];
    for (int i = 0; i < num_groups; i++) {
        rates[i] = calculate_positive_rate(predictions, group_indices[i], group_counts[i]);
    }

    // Find max and min
    double max_rate = rates[0], min_rate = rates[0];
    for (int i = 1; i < num_groups; i++) {
        if (rates[i] > max_rate) max_rate = rates[i];
        if (rates[i] < min_rate) min_rate = rates[i];
    }

    metrics.demographic_parity_diff = max_rate - min_rate;
    metrics.bias_detected = fabs(metrics.demographic_parity_diff) > BIAS_THRESHOLD;

    if (metrics.bias_detected) {
        syslog(LOG_WARNING, "Bias detected: system_id=%s, dp_diff=%.3f",
               system_id, metrics.demographic_parity_diff);
    }

    return metrics;
}
```

---

## Success Criteria

- [ ] AI systems registered with unique IDs
- [ ] Bias detection operational
- [ ] Demographic parity differences < 0.1

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
