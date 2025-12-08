---
template_id: compliance_governance_risk_assessment_c
template_name: Risk Assessment - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/c_soc2_compliance.md
  - compliance_frameworks/c_iso27001_implementation.md
related_templates:
  - risk_management/c_threat_modeling.md
  - compliance_frameworks/c_nist_ai_rmf.md
tools:
  - syslog (logging)
tags:
  - risk-assessment
  - risk-management
  - defense-in-depth
  - compliance
  - c
---

# Risk Assessment - C

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Conduct comprehensive risk assessments following ISO 27001, NIST AI RMF, and SOC 2 requirements

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Risk Formula**: `Risk = Likelihood × Impact`

### Framework Requirements

**ISO 27001 Clause 6.1.2**: Risk assessment required
- Identify risks to confidentiality, integrity, availability
- Assess likelihood and impact
- Determine risk levels

**SOC 2 CC9.1**: Risk assessment process
- Identify potential threats
- Evaluate severity of risks
- Update risk assessment periodically

**NIST AI RMF MAP Function**: Context and risk identification
- MAP 4.1: Risks and benefits assessed
- MAP 5.1: Impact assessments conducted

---

## Asset Management Implementation

```c
#include <stdio.h>
#include <string.h>
#include <syslog.h>
#include <time.h>

#define MAX_ASSET_NAME 128
#define MAX_DESCRIPTION 512
#define MAX_OWNER 64
#define MAX_DEPENDENCIES 10
#define MAX_ASSET_ID 64

typedef enum {
    ASSET_TYPE_DATA,
    ASSET_TYPE_APPLICATION,
    ASSET_TYPE_INFRASTRUCTURE,
    ASSET_TYPE_DEVICE,
    ASSET_TYPE_PEOPLE,
    ASSET_TYPE_AI_MODEL,
    ASSET_TYPE_API
} asset_type_t;

typedef enum {
    CONFIDENTIALITY_PUBLIC = 1,
    CONFIDENTIALITY_INTERNAL = 2,
    CONFIDENTIALITY_CONFIDENTIAL = 3,
    CONFIDENTIALITY_RESTRICTED = 4
} confidentiality_t;

typedef enum {
    CRITICALITY_LOW = 1,
    CRITICALITY_MEDIUM = 2,
    CRITICALITY_HIGH = 3,
    CRITICALITY_CRITICAL = 4
} criticality_t;

typedef struct {
    char asset_id[MAX_ASSET_ID];
    char asset_name[MAX_ASSET_NAME];
    asset_type_t asset_type;
    char description[MAX_DESCRIPTION];
    char owner[MAX_OWNER];

    // CIA Triad classification
    confidentiality_t confidentiality;
    criticality_t integrity_requirement;
    criticality_t availability_requirement;
    int overall_criticality;

    // Dependencies
    char dependencies[MAX_DEPENDENCIES][MAX_ASSET_NAME];
    int dependency_count;

    // Metadata
    time_t registered_date;
    time_t last_reviewed;
    char status[16];
} asset_record_t;

/**
 * Register information asset in inventory.
 *
 * ISO 27001 Control 5.9: Inventory of information and assets
 * CIA Triad assessment:
 * - Confidentiality: How sensitive?
 * - Integrity: How accurate must it be?
 * - Availability: How available must it be?
 */
int register_asset(
    const char *asset_name,
    asset_type_t asset_type,
    const char *description,
    const char *owner,
    confidentiality_t confidentiality,
    criticality_t integrity_requirement,
    criticality_t availability_requirement,
    const char dependencies[][MAX_ASSET_NAME],
    int dependency_count,
    asset_record_t *asset_record) {

    time_t now = time(NULL);

    // Generate asset ID
    snprintf(asset_record->asset_id, sizeof(asset_record->asset_id),
             "ASSET-%ld", now);

    strncpy(asset_record->asset_name, asset_name, sizeof(asset_record->asset_name) - 1);
    asset_record->asset_type = asset_type;
    strncpy(asset_record->description, description, sizeof(asset_record->description) - 1);
    strncpy(asset_record->owner, owner, sizeof(asset_record->owner) - 1);

    // CIA Triad classification
    asset_record->confidentiality = confidentiality;
    asset_record->integrity_requirement = integrity_requirement;
    asset_record->availability_requirement = availability_requirement;

    // Calculate overall criticality (max of CIA)
    int max_cia = confidentiality;
    if (integrity_requirement > max_cia) max_cia = integrity_requirement;
    if (availability_requirement > max_cia) max_cia = availability_requirement;
    asset_record->overall_criticality = max_cia;

    // Dependencies
    asset_record->dependency_count = dependency_count;
    for (int i = 0; i < dependency_count && i < MAX_DEPENDENCIES; i++) {
        strncpy(asset_record->dependencies[i], dependencies[i],
                sizeof(asset_record->dependencies[i]) - 1);
    }

    // Metadata
    asset_record->registered_date = now;
    asset_record->last_reviewed = now;
    strncpy(asset_record->status, "active", sizeof(asset_record->status) - 1);

    syslog(LOG_INFO,
           "Asset registered: asset_id=%s, asset_name=%s, criticality=%d",
           asset_record->asset_id, asset_name, asset_record->overall_criticality);

    return 0;
}

/**
 * Calculate asset value for risk assessment.
 *
 * Value based on:
 * - Replacement cost
 * - Business impact if lost
 * - Regulatory fines if breached
 * - Reputation damage
 */
double calculate_asset_value(const asset_record_t *asset_record) {
    // Base value from criticality
    double base_value;
    switch (asset_record->overall_criticality) {
        case 1: base_value = 10000.0; break;    // Low
        case 2: base_value = 50000.0; break;    // Medium
        case 3: base_value = 250000.0; break;   // High
        case 4: base_value = 1000000.0; break;  // Critical
        default: base_value = 50000.0;
    }

    // Multiply by data volume (if applicable)
    if (asset_record->asset_type == ASSET_TYPE_DATA) {
        // In production: factor in record count
        // base_value *= (record_count / 1000.0);
    }

    // Multiply by number of dependencies (cascade effects)
    double dependency_multiplier = 1 + (asset_record->dependency_count * 0.2);
    double asset_value = base_value * dependency_multiplier;

    syslog(LOG_INFO,
           "Asset value calculated: asset_id=%s, asset_value=%.2f, criticality=%d",
           asset_record->asset_id, asset_value, asset_record->overall_criticality);

    return asset_value;
}
```

---

## Threat Identification Implementation

```c
#define MAX_THREAT_NAME 128
#define MAX_THREAT_DESC 512
#define MAX_ATTACK_VECTORS 5
#define MAX_VECTOR_NAME 64
#define MAX_THREAT_ID 64

typedef enum {
    THREAT_CATEGORY_SPOOFING,
    THREAT_CATEGORY_TAMPERING,
    THREAT_CATEGORY_REPUDIATION,
    THREAT_CATEGORY_INFORMATION_DISCLOSURE,
    THREAT_CATEGORY_DENIAL_OF_SERVICE,
    THREAT_CATEGORY_ELEVATION_OF_PRIVILEGE
} threat_category_t;

typedef enum {
    THREAT_SOURCE_EXTERNAL_ATTACKER,
    THREAT_SOURCE_INSIDER_MALICIOUS,
    THREAT_SOURCE_INSIDER_ACCIDENTAL,
    THREAT_SOURCE_NATURAL_DISASTER,
    THREAT_SOURCE_TECHNICAL_FAILURE,
    THREAT_SOURCE_AI_SYSTEM
} threat_source_t;

typedef struct {
    char threat_id[MAX_THREAT_ID];
    char asset_id[MAX_ASSET_ID];
    char threat_name[MAX_THREAT_NAME];
    threat_category_t threat_category;
    threat_source_t threat_source;
    char description[MAX_THREAT_DESC];
    char attack_vectors[MAX_ATTACK_VECTORS][MAX_VECTOR_NAME];
    int attack_vector_count;
    time_t identified_date;
} threat_record_t;

/**
 * Identify threats applicable to asset.
 *
 * NIST AI RMF MAP 4.1: Threats identified
 * Returns list of potential threats based on asset type.
 */
int identify_threats(const char *asset_id, threat_record_t *threats, int max_threats) {
    int threat_count = 0;
    time_t now = time(NULL);

    // Threat 1: Unauthorized Data Access
    if (threat_count < max_threats) {
        snprintf(threats[threat_count].threat_id, MAX_THREAT_ID, "THREAT-%ld-%d", now, threat_count);
        strncpy(threats[threat_count].asset_id, asset_id, MAX_ASSET_ID - 1);
        strncpy(threats[threat_count].threat_name, "Unauthorized Data Access", MAX_THREAT_NAME - 1);
        threats[threat_count].threat_category = THREAT_CATEGORY_INFORMATION_DISCLOSURE;
        threats[threat_count].threat_source = THREAT_SOURCE_EXTERNAL_ATTACKER;
        strncpy(threats[threat_count].description,
                "Attacker gains unauthorized access to sensitive data", MAX_THREAT_DESC - 1);

        threats[threat_count].attack_vector_count = 3;
        strncpy(threats[threat_count].attack_vectors[0], "SQL injection", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[1], "Broken authentication", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[2], "API exploitation", MAX_VECTOR_NAME - 1);

        threats[threat_count].identified_date = now;
        threat_count++;
    }

    // Threat 2: Data Exfiltration
    if (threat_count < max_threats) {
        snprintf(threats[threat_count].threat_id, MAX_THREAT_ID, "THREAT-%ld-%d", now, threat_count);
        strncpy(threats[threat_count].asset_id, asset_id, MAX_ASSET_ID - 1);
        strncpy(threats[threat_count].threat_name, "Data Exfiltration", MAX_THREAT_NAME - 1);
        threats[threat_count].threat_category = THREAT_CATEGORY_INFORMATION_DISCLOSURE;
        threats[threat_count].threat_source = THREAT_SOURCE_INSIDER_MALICIOUS;
        strncpy(threats[threat_count].description,
                "Insider copies sensitive data to external location", MAX_THREAT_DESC - 1);

        threats[threat_count].attack_vector_count = 3;
        strncpy(threats[threat_count].attack_vectors[0], "USB drives", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[1], "Cloud storage", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[2], "Email", MAX_VECTOR_NAME - 1);

        threats[threat_count].identified_date = now;
        threat_count++;
    }

    // Threat 3: Ransomware
    if (threat_count < max_threats) {
        snprintf(threats[threat_count].threat_id, MAX_THREAT_ID, "THREAT-%ld-%d", now, threat_count);
        strncpy(threats[threat_count].asset_id, asset_id, MAX_ASSET_ID - 1);
        strncpy(threats[threat_count].threat_name, "Ransomware", MAX_THREAT_NAME - 1);
        threats[threat_count].threat_category = THREAT_CATEGORY_DENIAL_OF_SERVICE;
        threats[threat_count].threat_source = THREAT_SOURCE_EXTERNAL_ATTACKER;
        strncpy(threats[threat_count].description,
                "Malware encrypts data, demands ransom", MAX_THREAT_DESC - 1);

        threats[threat_count].attack_vector_count = 3;
        strncpy(threats[threat_count].attack_vectors[0], "Phishing", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[1], "Drive-by download", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[2], "RDP exploitation", MAX_VECTOR_NAME - 1);

        threats[threat_count].identified_date = now;
        threat_count++;
    }

    // Threat 4: Prompt Injection (AI-specific)
    if (threat_count < max_threats) {
        snprintf(threats[threat_count].threat_id, MAX_THREAT_ID, "THREAT-%ld-%d", now, threat_count);
        strncpy(threats[threat_count].asset_id, asset_id, MAX_ASSET_ID - 1);
        strncpy(threats[threat_count].threat_name, "Prompt Injection", MAX_THREAT_NAME - 1);
        threats[threat_count].threat_category = THREAT_CATEGORY_ELEVATION_OF_PRIVILEGE;
        threats[threat_count].threat_source = THREAT_SOURCE_EXTERNAL_ATTACKER;
        strncpy(threats[threat_count].description,
                "Malicious prompts manipulate LLM behavior", MAX_THREAT_DESC - 1);

        threats[threat_count].attack_vector_count = 2;
        strncpy(threats[threat_count].attack_vectors[0], "Direct injection", MAX_VECTOR_NAME - 1);
        strncpy(threats[threat_count].attack_vectors[1], "Indirect injection via data", MAX_VECTOR_NAME - 1);

        threats[threat_count].identified_date = now;
        threat_count++;
    }

    syslog(LOG_INFO, "Threats identified: asset_id=%s, threats_count=%d",
           asset_id, threat_count);

    return threat_count;
}
```

---

## Risk Analysis Implementation

```c
typedef enum {
    LIKELIHOOD_RARE = 1,             // <5% annual probability
    LIKELIHOOD_UNLIKELY = 2,         // 5-25%
    LIKELIHOOD_POSSIBLE = 3,         // 25-50%
    LIKELIHOOD_LIKELY = 4,           // 50-75%
    LIKELIHOOD_ALMOST_CERTAIN = 5    // >75%
} likelihood_t;

typedef enum {
    IMPACT_INSIGNIFICANT = 1,  // <$10K loss
    IMPACT_MINOR = 2,          // $10K-$100K
    IMPACT_MODERATE = 3,       // $100K-$500K
    IMPACT_MAJOR = 4,          // $500K-$1M
    IMPACT_SEVERE = 5          // >$1M
} impact_t;

typedef enum {
    RISK_LEVEL_LOW,        // Risk score 1-6
    RISK_LEVEL_MEDIUM,     // Risk score 7-12
    RISK_LEVEL_HIGH,       // Risk score 13-18
    RISK_LEVEL_CRITICAL    // Risk score 19-25
} risk_level_t;

typedef struct {
    char risk_id[MAX_ASSET_ID];
    char threat_id[MAX_THREAT_ID];
    char asset_id[MAX_ASSET_ID];
    likelihood_t likelihood;
    impact_t impact;
    int risk_score;
    risk_level_t risk_level;
    int existing_control_count;
    time_t assessed_date;
} risk_analysis_t;

/**
 * Assess likelihood of threat occurring.
 *
 * ISO 27001 Clause 6.1.2(d): Analyze information security risks
 *
 * Factors:
 * - Threat source capability
 * - Threat source motivation
 * - Vulnerability severity
 * - Existing controls effectiveness
 */
likelihood_t assess_likelihood(
    const threat_record_t *threat,
    const asset_record_t *asset,
    int existing_control_count) {

    // Base likelihood from threat source
    int base_likelihood;
    switch (threat->threat_source) {
        case THREAT_SOURCE_EXTERNAL_ATTACKER:   base_likelihood = 4; break; // Likely
        case THREAT_SOURCE_INSIDER_MALICIOUS:   base_likelihood = 2; break; // Unlikely
        case THREAT_SOURCE_INSIDER_ACCIDENTAL:  base_likelihood = 3; break; // Possible
        case THREAT_SOURCE_NATURAL_DISASTER:    base_likelihood = 1; break; // Rare
        case THREAT_SOURCE_TECHNICAL_FAILURE:   base_likelihood = 3; break; // Possible
        case THREAT_SOURCE_AI_SYSTEM:           base_likelihood = 3; break; // Possible
        default: base_likelihood = 3;
    }

    // Adjust for vulnerabilities (increase likelihood)
    int high_severity_vulns = 1; // From vulnerability scan
    if (high_severity_vulns > 0) {
        base_likelihood = (base_likelihood + 1 < 5) ? base_likelihood + 1 : 5;
    }

    // Adjust for existing controls (decrease likelihood)
    double control_reduction = (existing_control_count * 0.5 < 2.0) ?
                               existing_control_count * 0.5 : 2.0;
    int final_likelihood = (int)(base_likelihood - control_reduction);
    if (final_likelihood < 1) final_likelihood = 1;

    syslog(LOG_INFO, "Likelihood assessed: threat_id=%s, asset_id=%s, likelihood=%d",
           threat->threat_id, asset->asset_id, final_likelihood);

    return (likelihood_t)final_likelihood;
}

/**
 * Assess impact if threat materializes.
 *
 * Factors:
 * - Asset value
 * - Asset criticality
 * - Regulatory fines
 * - Reputation damage
 */
impact_t assess_impact(
    const threat_record_t *threat,
    const asset_record_t *asset) {

    // Asset value
    double asset_value = calculate_asset_value(asset);

    // Base impact from threat category
    int base_impact;
    switch (threat->threat_category) {
        case THREAT_CATEGORY_INFORMATION_DISCLOSURE:  base_impact = 4; break; // Major (GDPR fines)
        case THREAT_CATEGORY_DENIAL_OF_SERVICE:       base_impact = 3; break; // Moderate (downtime)
        case THREAT_CATEGORY_TAMPERING:               base_impact = 4; break; // Major (data integrity)
        case THREAT_CATEGORY_ELEVATION_OF_PRIVILEGE:  base_impact = 5; break; // Severe (full compromise)
        case THREAT_CATEGORY_SPOOFING:                base_impact = 3; break; // Moderate
        case THREAT_CATEGORY_REPUDIATION:             base_impact = 2; break; // Minor
        default: base_impact = 3;
    }

    // Adjust for asset criticality
    if (asset->overall_criticality == 4) {  // Critical
        base_impact = (base_impact + 1 < 5) ? base_impact + 1 : 5;
    }

    // Financial impact mapping
    impact_t financial_impact;
    if (asset_value > 1000000) {
        financial_impact = IMPACT_SEVERE;
    } else if (asset_value > 500000) {
        financial_impact = IMPACT_MAJOR;
    } else if (asset_value > 100000) {
        financial_impact = IMPACT_MODERATE;
    } else if (asset_value > 10000) {
        financial_impact = IMPACT_MINOR;
    } else {
        financial_impact = IMPACT_INSIGNIFICANT;
    }

    // Take maximum of category and financial impact
    int final_impact = (base_impact > financial_impact) ? base_impact : financial_impact;

    syslog(LOG_INFO,
           "Impact assessed: threat_id=%s, asset_id=%s, impact=%d, asset_value=%.2f",
           threat->threat_id, asset->asset_id, final_impact, asset_value);

    return (impact_t)final_impact;
}

/**
 * Calculate risk score.
 *
 * Risk = Likelihood × Impact
 */
int calculate_risk(
    const threat_record_t *threat,
    const asset_record_t *asset,
    int existing_control_count,
    risk_analysis_t *risk_analysis) {

    time_t now = time(NULL);

    // Generate risk ID
    snprintf(risk_analysis->risk_id, sizeof(risk_analysis->risk_id),
             "RISK-%ld", now);
    strncpy(risk_analysis->threat_id, threat->threat_id, MAX_THREAT_ID - 1);
    strncpy(risk_analysis->asset_id, asset->asset_id, MAX_ASSET_ID - 1);

    // Assess likelihood and impact
    risk_analysis->likelihood = assess_likelihood(threat, asset, existing_control_count);
    risk_analysis->impact = assess_impact(threat, asset);

    // Calculate risk score
    risk_analysis->risk_score = risk_analysis->likelihood * risk_analysis->impact;

    // Determine risk level
    if (risk_analysis->risk_score >= 19) {
        risk_analysis->risk_level = RISK_LEVEL_CRITICAL;
    } else if (risk_analysis->risk_score >= 13) {
        risk_analysis->risk_level = RISK_LEVEL_HIGH;
    } else if (risk_analysis->risk_score >= 7) {
        risk_analysis->risk_level = RISK_LEVEL_MEDIUM;
    } else {
        risk_analysis->risk_level = RISK_LEVEL_LOW;
    }

    risk_analysis->existing_control_count = existing_control_count;
    risk_analysis->assessed_date = now;

    syslog(LOG_ALERT,
           "Risk calculated: risk_id=%s, risk_level=%d, risk_score=%d",
           risk_analysis->risk_id, risk_analysis->risk_level, risk_analysis->risk_score);

    return 0;
}
```

---

## Risk Treatment Implementation

```c
typedef enum {
    TREATMENT_MITIGATE,   // Implement controls to reduce risk
    TREATMENT_ACCEPT,     // Accept risk within tolerance
    TREATMENT_TRANSFER,   // Insurance, outsourcing
    TREATMENT_AVOID       // Eliminate activity causing risk
} treatment_option_t;

typedef struct {
    char plan_id[MAX_ASSET_ID];
    char risk_id[MAX_ASSET_ID];
    treatment_option_t treatment_option;
    char owner[MAX_OWNER];
    time_t target_completion_date;
    char status[32];
    time_t created_date;
    char residual_risk_level[16];
} treatment_plan_t;

/**
 * Determine appropriate risk treatment.
 *
 * ISO 27001 Clause 6.1.3: Risk treatment
 * Decision based on risk level and risk appetite.
 */
treatment_option_t determine_treatment(const risk_analysis_t *risk_analysis) {
    // Risk appetite (configurable per organization)
    switch (risk_analysis->risk_level) {
        case RISK_LEVEL_LOW:
            return TREATMENT_ACCEPT;  // Acceptable
        case RISK_LEVEL_MEDIUM:
            return TREATMENT_MITIGATE;  // Review required - default to mitigate
        case RISK_LEVEL_HIGH:
        case RISK_LEVEL_CRITICAL:
            return TREATMENT_MITIGATE;  // Must mitigate
        default:
            return TREATMENT_MITIGATE;
    }
}

/**
 * Create risk treatment plan.
 *
 * ISO 27001 Clause 6.1.3(e): Risk treatment plan required
 */
int create_treatment_plan(
    const risk_analysis_t *risk_analysis,
    treatment_option_t treatment_option,
    int proposed_control_count,
    const char *owner,
    time_t target_completion_date,
    treatment_plan_t *treatment_plan) {

    time_t now = time(NULL);

    // Generate plan ID
    snprintf(treatment_plan->plan_id, sizeof(treatment_plan->plan_id),
             "PLAN-%ld", now);
    strncpy(treatment_plan->risk_id, risk_analysis->risk_id, MAX_ASSET_ID - 1);
    treatment_plan->treatment_option = treatment_option;
    strncpy(treatment_plan->owner, owner, MAX_OWNER - 1);
    treatment_plan->target_completion_date = target_completion_date;
    strncpy(treatment_plan->status, "planned", sizeof(treatment_plan->status) - 1);
    treatment_plan->created_date = now;

    // Estimate residual risk (simplified)
    int current_likelihood = risk_analysis->likelihood;
    int likelihood_reduction = (proposed_control_count < current_likelihood - 1) ?
                               proposed_control_count : current_likelihood - 1;
    int residual_likelihood = current_likelihood - likelihood_reduction;
    int residual_impact = risk_analysis->impact;
    int residual_score = residual_likelihood * residual_impact;

    if (residual_score >= 19) {
        strncpy(treatment_plan->residual_risk_level, "critical", 16);
    } else if (residual_score >= 13) {
        strncpy(treatment_plan->residual_risk_level, "high", 16);
    } else if (residual_score >= 7) {
        strncpy(treatment_plan->residual_risk_level, "medium", 16);
    } else {
        strncpy(treatment_plan->residual_risk_level, "low", 16);
    }

    syslog(LOG_INFO,
           "Risk treatment plan created: plan_id=%s, risk_id=%s, treatment=%d",
           treatment_plan->plan_id, treatment_plan->risk_id, treatment_option);

    return 0;
}

/**
 * Accept residual risk (after controls implemented).
 *
 * ISO 27001 Clause 6.1.3(f): Obtain risk acceptance from risk owners
 */
int accept_residual_risk(
    const treatment_plan_t *treatment_plan,
    const char *approver,
    const char *justification) {

    time_t now = time(NULL);

    syslog(LOG_ALERT,
           "Residual risk accepted: plan_id=%s, approver=%s, residual_risk=%s, timestamp=%ld",
           treatment_plan->plan_id, approver, treatment_plan->residual_risk_level, now);

    return 0;
}
```

---

## Success Criteria

### Asset Inventory Complete

- [ ] All information assets identified and cataloged
- [ ] Asset owners assigned
- [ ] CIA classification completed
- [ ] Asset dependencies mapped
- [ ] Asset values calculated

### Risk Assessment Complete

- [ ] Threats identified for all critical assets
- [ ] Vulnerabilities scanned and documented
- [ ] Risk analysis completed (likelihood × impact)
- [ ] Risk register populated and maintained
- [ ] Risk matrix generated

### Risk Treatment Planned

- [ ] Treatment decisions for all high/critical risks
- [ ] Risk treatment plans created
- [ ] Control implementations scheduled
- [ ] Residual risks accepted by risk owners
- [ ] Continuous monitoring established

### Compliance Evidence

- [ ] Risk assessment documentation (ISO 27001 6.1.2)
- [ ] Risk treatment plan (ISO 27001 6.1.3)
- [ ] Risk acceptance records
- [ ] Periodic risk review schedule (quarterly)
- [ ] Executive risk reports

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
