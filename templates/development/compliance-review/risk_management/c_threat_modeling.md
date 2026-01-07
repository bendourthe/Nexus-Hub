---
template_id: compliance_governance_threat_modeling_c
template_name: Threat Modeling - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/c_risk_assessment.md
  - compliance_frameworks/c_nist_ai_rmf.md
related_templates:
  - compliance_frameworks/c_soc2_compliance.md
tools:
  - syslog (logging)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - c
---

# Threat Modeling - C

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Systematic threat modeling using STRIDE, PASTA, and attack tree analysis

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Threat Modeling Methodologies**:
- **STRIDE**: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **PASTA**: 7-stage risk-centric methodology
- **Attack Trees**: Visual attack path representation

---

## System Decomposition

```c
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <time.h>

#define MAX_NAME 128
#define MAX_DESC 512
#define MAX_COMPONENTS 50

typedef enum {
    ELEMENT_TYPE_EXTERNAL_ENTITY,
    ELEMENT_TYPE_PROCESS,
    ELEMENT_TYPE_DATA_STORE,
    ELEMENT_TYPE_DATA_FLOW
} element_type_t;

typedef enum {
    TRUST_BOUNDARY_INTERNET,
    TRUST_BOUNDARY_DMZ,
    TRUST_BOUNDARY_INTERNAL,
    TRUST_BOUNDARY_DATABASE,
    TRUST_BOUNDARY_AI_MODEL
} trust_boundary_t;

typedef struct {
    char component_id[64];
    element_type_t component_type;
    char name[MAX_NAME];
    char description[MAX_DESC];
    trust_boundary_t trust_boundary;

    // Security properties
    int authenticates_users;
    int validates_input;
    int logs_activity;
    int encrypted_at_rest;
    int access_controlled;

    char runs_as[64];
    char data_classification[32];
} component_t;

typedef struct {
    char system_name[MAX_NAME];
    component_t components[MAX_COMPONENTS];
    int component_count;
} system_decomposition_t;

int add_external_entity(
    system_decomposition_t *system,
    const char *name,
    const char *description,
    const char *trust_level) {

    if (system->component_count >= MAX_COMPONENTS) {
        return -1;
    }

    component_t *component = &system->components[system->component_count];
    time_t now = time(NULL);

    snprintf(component->component_id, sizeof(component->component_id),
             "ENTITY-%ld", now);
    component->component_type = ELEMENT_TYPE_EXTERNAL_ENTITY;
    strncpy(component->name, name, sizeof(component->name) - 1);
    strncpy(component->description, description, sizeof(component->description) - 1);
    component->trust_boundary = TRUST_BOUNDARY_INTERNET;

    system->component_count++;

    syslog(LOG_INFO, "External entity added: id=%s, name=%s",
           component->component_id, name);

    return 0;
}

int add_process(
    system_decomposition_t *system,
    const char *name,
    const char *description,
    trust_boundary_t trust_boundary,
    const char *runs_as) {

    if (system->component_count >= MAX_COMPONENTS) {
        return -1;
    }

    component_t *component = &system->components[system->component_count];
    time_t now = time(NULL);

    snprintf(component->component_id, sizeof(component->component_id),
             "PROCESS-%ld", now);
    component->component_type = ELEMENT_TYPE_PROCESS;
    strncpy(component->name, name, sizeof(component->name) - 1);
    strncpy(component->description, description, sizeof(component->description) - 1);
    component->trust_boundary = trust_boundary;
    strncpy(component->runs_as, runs_as, sizeof(component->runs_as) - 1);

    component->authenticates_users = 0;
    component->validates_input = 0;
    component->logs_activity = 0;

    system->component_count++;

    syslog(LOG_INFO, "Process added: id=%s, name=%s",
           component->component_id, name);

    return 0;
}

int add_data_store(
    system_decomposition_t *system,
    const char *name,
    const char *description,
    const char *data_classification,
    trust_boundary_t trust_boundary) {

    if (system->component_count >= MAX_COMPONENTS) {
        return -1;
    }

    component_t *component = &system->components[system->component_count];
    time_t now = time(NULL);

    snprintf(component->component_id, sizeof(component->component_id),
             "DATASTORE-%ld", now);
    component->component_type = ELEMENT_TYPE_DATA_STORE;
    strncpy(component->name, name, sizeof(component->name) - 1);
    strncpy(component->description, description, sizeof(component->description) - 1);
    component->trust_boundary = trust_boundary;
    strncpy(component->data_classification, data_classification,
            sizeof(component->data_classification) - 1);

    component->encrypted_at_rest = 0;
    component->access_controlled = 0;

    system->component_count++;

    syslog(LOG_INFO, "Data store added: id=%s, name=%s, classification=%s",
           component->component_id, name, data_classification);

    return 0;
}
```

---

## STRIDE Analysis

```c
typedef enum {
    STRIDE_SPOOFING,
    STRIDE_TAMPERING,
    STRIDE_REPUDIATION,
    STRIDE_INFORMATION_DISCLOSURE,
    STRIDE_DENIAL_OF_SERVICE,
    STRIDE_ELEVATION_OF_PRIVILEGE
} stride_category_t;

typedef struct {
    char threat_id[64];
    char component_id[64];
    stride_category_t category;
    char threat_name[MAX_NAME];
    char description[MAX_DESC];
    char severity[16];
    int mitigation_count;
    char mitigations[5][MAX_NAME];
} threat_t;

int analyze_spoofing(const component_t *component, threat_t *threats, int *threat_count) {
    if (component->component_type == ELEMENT_TYPE_PROCESS &&
        !component->authenticates_users) {

        threat_t *threat = &threats[*threat_count];
        time_t now = time(NULL);

        snprintf(threat->threat_id, sizeof(threat->threat_id), "THREAT-%ld", now);
        strncpy(threat->component_id, component->component_id, sizeof(threat->component_id) - 1);
        threat->category = STRIDE_SPOOFING;
        strncpy(threat->threat_name, "Identity Spoofing", sizeof(threat->threat_name) - 1);
        strncpy(threat->description,
                "Attacker impersonates legitimate user/service",
                sizeof(threat->description) - 1);
        strncpy(threat->severity, "high", sizeof(threat->severity) - 1);

        threat->mitigation_count = 3;
        strncpy(threat->mitigations[0], "Implement MFA", sizeof(threat->mitigations[0]) - 1);
        strncpy(threat->mitigations[1], "Use mutual TLS", sizeof(threat->mitigations[1]) - 1);
        strncpy(threat->mitigations[2], "Token-based auth", sizeof(threat->mitigations[2]) - 1);

        (*threat_count)++;
    }

    return 0;
}

int analyze_tampering(const component_t *component, threat_t *threats, int *threat_count) {
    if (component->component_type == ELEMENT_TYPE_DATA_STORE &&
        !component->access_controlled) {

        threat_t *threat = &threats[*threat_count];
        time_t now = time(NULL);

        snprintf(threat->threat_id, sizeof(threat->threat_id), "THREAT-%ld", now);
        strncpy(threat->component_id, component->component_id, sizeof(threat->component_id) - 1);
        threat->category = STRIDE_TAMPERING;
        strncpy(threat->threat_name, "Data Tampering", sizeof(threat->threat_name) - 1);
        strncpy(threat->description,
                "Unauthorized modification of stored data",
                sizeof(threat->description) - 1);
        strncpy(threat->severity, "critical", sizeof(threat->severity) - 1);

        threat->mitigation_count = 3;
        strncpy(threat->mitigations[0], "Implement ACLs", sizeof(threat->mitigations[0]) - 1);
        strncpy(threat->mitigations[1], "Database triggers", sizeof(threat->mitigations[1]) - 1);
        strncpy(threat->mitigations[2], "Digital signatures", sizeof(threat->mitigations[2]) - 1);

        (*threat_count)++;
    }

    return 0;
}

int analyze_information_disclosure(const component_t *component, threat_t *threats, int *threat_count) {
    if (component->component_type == ELEMENT_TYPE_DATA_STORE &&
        !component->encrypted_at_rest &&
        (strcmp(component->data_classification, "confidential") == 0 ||
         strcmp(component->data_classification, "restricted") == 0)) {

        threat_t *threat = &threats[*threat_count];
        time_t now = time(NULL);

        snprintf(threat->threat_id, sizeof(threat->threat_id), "THREAT-%ld", now);
        strncpy(threat->component_id, component->component_id, sizeof(threat->component_id) - 1);
        threat->category = STRIDE_INFORMATION_DISCLOSURE;
        strncpy(threat->threat_name, "Data Exposure", sizeof(threat->threat_name) - 1);
        strncpy(threat->description,
                "Sensitive data exposed through unauthorized access",
                sizeof(threat->description) - 1);
        strncpy(threat->severity, "critical", sizeof(threat->severity) - 1);

        threat->mitigation_count = 3;
        strncpy(threat->mitigations[0], "Encrypt at rest (AES-256)", sizeof(threat->mitigations[0]) - 1);
        strncpy(threat->mitigations[1], "Data loss prevention", sizeof(threat->mitigations[1]) - 1);
        strncpy(threat->mitigations[2], "Least privilege", sizeof(threat->mitigations[2]) - 1);

        (*threat_count)++;
    }

    return 0;
}

int perform_stride_analysis(const component_t *component, threat_t *threats, int *threat_count) {
    analyze_spoofing(component, threats, threat_count);
    analyze_tampering(component, threats, threat_count);
    analyze_information_disclosure(component, threats, threat_count);

    syslog(LOG_INFO, "STRIDE analysis completed: component_id=%s, threats_found=%d",
           component->component_id, *threat_count);

    return 0;
}
```

---

## Attack Tree Analysis

```c
#define MAX_CHILDREN 10

typedef struct attack_node {
    char node_id[64];
    char attack_goal[MAX_NAME];
    char description[MAX_DESC];
    char attack_type[8];  // "AND" or "OR"
    double probability;
    double cost;
    struct attack_node *children[MAX_CHILDREN];
    int child_count;
} attack_node_t;

attack_node_t* create_attack_node(
    const char *attack_goal,
    const char *description,
    const char *attack_type,
    double probability,
    double cost) {

    attack_node_t *node = malloc(sizeof(attack_node_t));
    time_t now = time(NULL);

    snprintf(node->node_id, sizeof(node->node_id), "NODE-%ld", now);
    strncpy(node->attack_goal, attack_goal, sizeof(node->attack_goal) - 1);
    strncpy(node->description, description, sizeof(node->description) - 1);
    strncpy(node->attack_type, attack_type, sizeof(node->attack_type) - 1);
    node->probability = probability;
    node->cost = cost;
    node->child_count = 0;

    return node;
}

int add_child_node(attack_node_t *parent, attack_node_t *child) {
    if (parent->child_count >= MAX_CHILDREN) {
        return -1;
    }

    parent->children[parent->child_count] = child;
    parent->child_count++;

    return 0;
}

attack_node_t* build_attack_tree() {
    // Root goal: Compromise system
    attack_node_t *root = create_attack_node(
        "Compromise System",
        "Attacker gains unauthorized access",
        "OR",
        0.0,
        0.0
    );

    // Attack path 1: Exploit application vulnerability
    attack_node_t *exploit_app = create_attack_node(
        "Exploit Application Vulnerability",
        "Find and exploit weakness",
        "AND",
        0.3,
        5000.0
    );

    add_child_node(root, exploit_app);

    // Attack path 2: Social engineering
    attack_node_t *social_eng = create_attack_node(
        "Social Engineering",
        "Manipulate users",
        "OR",
        0.4,
        2000.0
    );

    add_child_node(root, social_eng);

    syslog(LOG_INFO, "Attack tree built: root_goal=%s", root->attack_goal);

    return root;
}

double calculate_attack_probability(attack_node_t *node) {
    if (node->child_count == 0) {
        return node->probability;
    }

    if (strcmp(node->attack_type, "AND") == 0) {
        // All children must succeed
        double prob = 1.0;
        for (int i = 0; i < node->child_count; i++) {
            prob *= calculate_attack_probability(node->children[i]);
        }
        return prob;
    } else {
        // OR: At least one child must succeed
        double failure_prob = 1.0;
        for (int i = 0; i < node->child_count; i++) {
            failure_prob *= (1.0 - calculate_attack_probability(node->children[i]));
        }
        return 1.0 - failure_prob;
    }
}
```

---

## Success Criteria

- [ ] Data flow diagrams created
- [ ] Trust boundaries identified
- [ ] STRIDE analysis performed
- [ ] Attack trees created
- [ ] Mitigations mapped to threats
- [ ] Annual review schedule

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
