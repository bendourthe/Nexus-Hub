---
template_id: compliance_governance_risk_assessment_java
template_name: Risk Assessment - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/java_soc2_compliance.md
  - compliance_frameworks/java_iso27001_implementation.md
related_templates:
  - risk_management/java_threat_modeling.md
  - compliance_frameworks/java_nist_ai_rmf.md
tools:
  - spring-boot (framework)
  - logback (logging)
tags:
  - risk-assessment
  - risk-management
  - defense-in-depth
  - compliance
  - java
---

# Risk Assessment - Java

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

```java
package com.company.compliance.risk;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;

@Service
public class AssetInventory {
    private static final Logger logger = LoggerFactory.getLogger(AssetInventory.class);

    public enum AssetType {
        DATA,            // Databases, files, datasets
        APPLICATION,     // Software systems
        INFRASTRUCTURE,  // Servers, networks
        DEVICE,          // Endpoints, mobile devices
        PEOPLE,          // Personnel with access
        AI_MODEL,        // ML models
        API              // API endpoints
    }

    public enum Confidentiality {
        PUBLIC(1),
        INTERNAL(2),
        CONFIDENTIAL(3),
        RESTRICTED(4);

        private final int value;
        Confidentiality(int value) { this.value = value; }
        public int getValue() { return value; }
    }

    public enum Criticality {
        LOW(1),
        MEDIUM(2),
        HIGH(3),
        CRITICAL(4);

        private final int value;
        Criticality(int value) { this.value = value; }
        public int getValue() { return value; }
    }

    /**
     * Register information asset in inventory.
     *
     * ISO 27001 Control 5.9: Inventory of information and assets
     * CIA Triad assessment:
     * - Confidentiality: How sensitive?
     * - Integrity: How accurate must it be?
     * - Availability: How available must it be?
     */
    public String registerAsset(
            String assetName,
            AssetType assetType,
            String description,
            String owner,
            Confidentiality confidentiality,
            Criticality integrityRequirement,
            Criticality availabilityRequirement,
            List<String> dependencies) {

        String assetId = UUID.randomUUID().toString();

        // Calculate overall criticality (max of CIA)
        int overallCriticality = Math.max(
            Math.max(confidentiality.getValue(), integrityRequirement.getValue()),
            availabilityRequirement.getValue()
        );

        var assetRecord = new HashMap<String, Object>();
        assetRecord.put("asset_id", assetId);
        assetRecord.put("asset_name", assetName);
        assetRecord.put("asset_type", assetType.name());
        assetRecord.put("description", description);
        assetRecord.put("owner", owner);

        // CIA Triad classification
        assetRecord.put("confidentiality", confidentiality.getValue());
        assetRecord.put("integrity_requirement", integrityRequirement.getValue());
        assetRecord.put("availability_requirement", availabilityRequirement.getValue());
        assetRecord.put("overall_criticality", overallCriticality);

        // Dependencies
        assetRecord.put("dependencies", dependencies != null ? dependencies : new ArrayList<>());

        // Metadata
        assetRecord.put("registered_date", Instant.now());
        assetRecord.put("last_reviewed", Instant.now());
        assetRecord.put("status", "active");

        // Store in database (MongoDB, PostgreSQL, etc.)
        // db.assets.insertOne(assetRecord);

        logger.info("Asset registered: asset_id={}, asset_name={}, criticality={}",
            assetId, assetName, overallCriticality);

        return assetId;
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
    public double calculateAssetValue(String assetId) {
        // Retrieve asset from database
        // var asset = db.assets.findOne(assetId);

        // Base value from criticality
        Map<Integer, Double> criticalityValues = Map.of(
            1, 10000.0,    // Low
            2, 50000.0,    // Medium
            3, 250000.0,   // High
            4, 1000000.0   // Critical
        );

        int overallCriticality = 3; // Retrieved from database
        double baseValue = criticalityValues.getOrDefault(overallCriticality, 50000.0);

        // Multiply by data volume (if applicable)
        // if (asset.assetType == AssetType.DATA) {
        //     int recordCount = asset.recordCount;
        //     baseValue *= (recordCount / 1000.0);
        // }

        // Multiply by number of dependencies (cascade effects)
        int dependencyCount = 2; // Retrieved from database
        double dependencyMultiplier = 1 + (dependencyCount * 0.2);
        double assetValue = baseValue * dependencyMultiplier;

        logger.info("Asset value calculated: asset_id={}, asset_value={}, criticality={}",
            assetId, assetValue, overallCriticality);

        return assetValue;
    }
}
```

---

## Threat Identification Implementation

```java
package com.company.compliance.risk;

@Service
public class ThreatCatalog {
    private static final Logger logger = LoggerFactory.getLogger(ThreatCatalog.class);

    public enum ThreatCategory {
        SPOOFING,
        TAMPERING,
        REPUDIATION,
        INFORMATION_DISCLOSURE,
        DENIAL_OF_SERVICE,
        ELEVATION_OF_PRIVILEGE
    }

    public enum ThreatSource {
        EXTERNAL_ATTACKER,
        INSIDER_MALICIOUS,
        INSIDER_ACCIDENTAL,
        NATURAL_DISASTER,
        TECHNICAL_FAILURE,
        AI_SYSTEM  // AI-specific threats
    }

    /**
     * Identify threats applicable to asset.
     *
     * NIST AI RMF MAP 4.1: Threats identified
     * Returns list of potential threats based on asset type.
     */
    public List<Map<String, Object>> identifyThreats(String assetId) {
        // Retrieve asset from database
        // var asset = db.assets.findOne(assetId);

        // Get threats for asset type (simplified for example)
        List<Map<String, Object>> threats = new ArrayList<>();

        // Data asset threats
        threats.add(Map.of(
            "threat_name", "Unauthorized Data Access",
            "threat_category", ThreatCategory.INFORMATION_DISCLOSURE,
            "threat_source", ThreatSource.EXTERNAL_ATTACKER,
            "description", "Attacker gains unauthorized access to sensitive data",
            "attack_vectors", Arrays.asList("SQL injection", "Broken authentication", "API exploitation")
        ));

        threats.add(Map.of(
            "threat_name", "Data Exfiltration",
            "threat_category", ThreatCategory.INFORMATION_DISCLOSURE,
            "threat_source", ThreatSource.INSIDER_MALICIOUS,
            "description", "Insider copies sensitive data to external location",
            "attack_vectors", Arrays.asList("USB drives", "Cloud storage", "Email")
        ));

        threats.add(Map.of(
            "threat_name", "Ransomware",
            "threat_category", ThreatCategory.DENIAL_OF_SERVICE,
            "threat_source", ThreatSource.EXTERNAL_ATTACKER,
            "description", "Malware encrypts data, demands ransom",
            "attack_vectors", Arrays.asList("Phishing", "Drive-by download", "RDP exploitation")
        ));

        // AI Model threats
        threats.add(Map.of(
            "threat_name", "Model Poisoning",
            "threat_category", ThreatCategory.TAMPERING,
            "threat_source", ThreatSource.EXTERNAL_ATTACKER,
            "description", "Attacker manipulates training data to corrupt model",
            "attack_vectors", Arrays.asList("Data injection", "Label flipping", "Backdoor insertion")
        ));

        threats.add(Map.of(
            "threat_name", "Prompt Injection",
            "threat_category", ThreatCategory.ELEVATION_OF_PRIVILEGE,
            "threat_source", ThreatSource.EXTERNAL_ATTACKER,
            "description", "Malicious prompts manipulate LLM behavior",
            "attack_vectors", Arrays.asList("Direct injection", "Indirect injection via data")
        ));

        // Store threat-asset mappings
        List<Map<String, Object>> identifiedThreats = new ArrayList<>();

        for (var threat : threats) {
            String threatId = UUID.randomUUID().toString();

            var threatRecord = new HashMap<String, Object>();
            threatRecord.put("threat_id", threatId);
            threatRecord.put("asset_id", assetId);
            threatRecord.putAll(threat);
            threatRecord.put("identified_date", Instant.now());

            // Store in database
            // db.threats.insertOne(threatRecord);

            identifiedThreats.add(threatRecord);
        }

        logger.info("Threats identified: asset_id={}, threats_count={}",
            assetId, identifiedThreats.size());

        return identifiedThreats;
    }
}

@Service
public class VulnerabilityScanner {
    private static final Logger logger = LoggerFactory.getLogger(VulnerabilityScanner.class);

    /**
     * Scan asset for vulnerabilities.
     *
     * Returns CVEs and severity scores (CVSS).
     * Integration with vulnerability scanners (Nessus, Qualys, etc.)
     */
    public List<Map<String, Object>> scanVulnerabilities(String assetId) {
        // Retrieve asset from database
        // var asset = db.assets.findOne(assetId);

        // Simulate vulnerability scan results
        // In production: integrate with Nessus, Qualys, OpenVAS, etc.
        List<Map<String, Object>> vulnerabilities = Arrays.asList(
            Map.of(
                "vulnerability_id", "CVE-2024-12345",
                "severity", "high",
                "cvss_score", 8.5,
                "description", "SQL injection vulnerability",
                "remediation", "Apply security patch 2024-01"
            )
        );

        // Store vulnerabilities
        for (var vuln : vulnerabilities) {
            var vulnRecord = new HashMap<String, Object>();
            vulnRecord.putAll(vuln);
            vulnRecord.put("asset_id", assetId);
            vulnRecord.put("scan_date", Instant.now());

            // Store in database
            // db.vulnerabilities.insertOne(vulnRecord);
        }

        logger.info("Vulnerability scan completed: asset_id={}, vulnerabilities_found={}",
            assetId, vulnerabilities.size());

        return vulnerabilities;
    }
}
```

---

## Risk Analysis Implementation

```java
package com.company.compliance.risk;

@Service
public class RiskAnalysis {
    private static final Logger logger = LoggerFactory.getLogger(RiskAnalysis.class);

    public enum Likelihood {
        RARE(1),             // <5% annual probability
        UNLIKELY(2),         // 5-25%
        POSSIBLE(3),         // 25-50%
        LIKELY(4),           // 50-75%
        ALMOST_CERTAIN(5);   // >75%

        private final int value;
        Likelihood(int value) { this.value = value; }
        public int getValue() { return value; }
    }

    public enum Impact {
        INSIGNIFICANT(1),  // <$10K loss
        MINOR(2),          // $10K-$100K
        MODERATE(3),       // $100K-$500K
        MAJOR(4),          // $500K-$1M
        SEVERE(5);         // >$1M

        private final int value;
        Impact(int value) { this.value = value; }
        public int getValue() { return value; }
    }

    public enum RiskLevel {
        LOW,        // Risk score 1-6
        MEDIUM,     // Risk score 7-12
        HIGH,       // Risk score 13-18
        CRITICAL    // Risk score 19-25
    }

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
    public Likelihood assessLikelihood(
            String threatId,
            String assetId,
            List<String> existingControls) {

        // Retrieve threat and asset
        // var threat = db.threats.findOne(threatId);
        // var asset = db.assets.findOne(assetId);
        // var vulnerabilities = db.vulnerabilities.find(assetId);

        // Base likelihood from threat source
        Map<String, Integer> sourceLikelihood = Map.of(
            "EXTERNAL_ATTACKER", 4,      // Likely
            "INSIDER_MALICIOUS", 2,      // Unlikely
            "INSIDER_ACCIDENTAL", 3,     // Possible
            "NATURAL_DISASTER", 1,       // Rare
            "TECHNICAL_FAILURE", 3,      // Possible
            "AI_SYSTEM", 3               // Possible
        );

        String threatSource = "EXTERNAL_ATTACKER"; // From database
        int baseLikelihood = sourceLikelihood.getOrDefault(threatSource, 3);

        // Adjust for vulnerabilities (increase likelihood)
        int highSeverityVulns = 1; // Count from database
        if (highSeverityVulns > 0) {
            baseLikelihood = Math.min(baseLikelihood + 1, 5);
        }

        // Adjust for existing controls (decrease likelihood)
        double controlReduction = Math.min(existingControls.size() * 0.5, 2.0);
        int finalLikelihood = Math.max((int)(baseLikelihood - controlReduction), 1);

        Likelihood likelihood = Likelihood.values()[finalLikelihood - 1];

        logger.info("Likelihood assessed: threat_id={}, asset_id={}, likelihood={}",
            threatId, assetId, likelihood.name());

        return likelihood;
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
    public Impact assessImpact(String threatId, String assetId) {
        // Retrieve threat and asset
        // var threat = db.threats.findOne(threatId);
        // var asset = db.assets.findOne(assetId);

        // Asset value
        AssetInventory assetInventory = new AssetInventory();
        double assetValue = assetInventory.calculateAssetValue(assetId);

        // Base impact from threat category
        Map<String, Integer> categoryImpact = Map.of(
            "INFORMATION_DISCLOSURE", 4,      // Major (GDPR fines)
            "DENIAL_OF_SERVICE", 3,           // Moderate (downtime)
            "TAMPERING", 4,                   // Major (data integrity)
            "ELEVATION_OF_PRIVILEGE", 5,      // Severe (full compromise)
            "SPOOFING", 3,                    // Moderate
            "REPUDIATION", 2                  // Minor
        );

        String threatCategory = "INFORMATION_DISCLOSURE"; // From database
        int baseImpact = categoryImpact.getOrDefault(threatCategory, 3);

        // Adjust for asset criticality
        int assetCriticality = 4; // From database
        if (assetCriticality == 4) {  // Critical
            baseImpact = Math.min(baseImpact + 1, 5);
        }

        // Financial impact mapping
        Impact financialImpact;
        if (assetValue > 1000000) {
            financialImpact = Impact.SEVERE;
        } else if (assetValue > 500000) {
            financialImpact = Impact.MAJOR;
        } else if (assetValue > 100000) {
            financialImpact = Impact.MODERATE;
        } else if (assetValue > 10000) {
            financialImpact = Impact.MINOR;
        } else {
            financialImpact = Impact.INSIGNIFICANT;
        }

        // Take maximum of category and financial impact
        int finalImpactValue = Math.max(baseImpact, financialImpact.getValue());
        Impact finalImpact = Impact.values()[finalImpactValue - 1];

        logger.info("Impact assessed: threat_id={}, asset_id={}, impact={}, asset_value={}",
            threatId, assetId, finalImpact.name(), assetValue);

        return finalImpact;
    }

    /**
     * Calculate risk score.
     *
     * Risk = Likelihood × Impact
     */
    public Map<String, Object> calculateRisk(
            String threatId,
            String assetId,
            List<String> existingControls) {

        if (existingControls == null) {
            existingControls = new ArrayList<>();
        }

        // Assess likelihood and impact
        Likelihood likelihood = assessLikelihood(threatId, assetId, existingControls);
        Impact impact = assessImpact(threatId, assetId);

        // Calculate risk score
        int riskScore = likelihood.getValue() * impact.getValue();

        // Determine risk level
        RiskLevel riskLevel;
        if (riskScore >= 19) {
            riskLevel = RiskLevel.CRITICAL;
        } else if (riskScore >= 13) {
            riskLevel = RiskLevel.HIGH;
        } else if (riskScore >= 7) {
            riskLevel = RiskLevel.MEDIUM;
        } else {
            riskLevel = RiskLevel.LOW;
        }

        String riskId = UUID.randomUUID().toString();

        var riskAnalysis = new HashMap<String, Object>();
        riskAnalysis.put("risk_id", riskId);
        riskAnalysis.put("threat_id", threatId);
        riskAnalysis.put("asset_id", assetId);
        riskAnalysis.put("likelihood", likelihood.name());
        riskAnalysis.put("likelihood_value", likelihood.getValue());
        riskAnalysis.put("impact", impact.name());
        riskAnalysis.put("impact_value", impact.getValue());
        riskAnalysis.put("risk_score", riskScore);
        riskAnalysis.put("risk_level", riskLevel.name());
        riskAnalysis.put("existing_controls", existingControls);
        riskAnalysis.put("assessed_date", Instant.now());

        // Store in risk register
        // db.riskRegister.insertOne(riskAnalysis);

        logger.warn("Risk calculated: risk_id={}, risk_level={}, risk_score={}",
            riskId, riskLevel.name(), riskScore);

        return riskAnalysis;
    }
}
```

---

## Risk Treatment Implementation

```java
package com.company.compliance.risk;

@Service
public class RiskTreatment {
    private static final Logger logger = LoggerFactory.getLogger(RiskTreatment.class);

    public enum RiskTreatmentOption {
        MITIGATE,   // Implement controls to reduce risk
        ACCEPT,     // Accept risk within tolerance
        TRANSFER,   // Insurance, outsourcing
        AVOID       // Eliminate activity causing risk
    }

    // Risk appetite (configurable per organization)
    private static final Map<String, String> RISK_APPETITE = Map.of(
        "LOW", "acceptable",
        "MEDIUM", "review_required",
        "HIGH", "must_mitigate",
        "CRITICAL", "must_mitigate"
    );

    /**
     * Determine appropriate risk treatment.
     *
     * ISO 27001 Clause 6.1.3: Risk treatment
     * Decision based on risk level and risk appetite.
     */
    public RiskTreatmentOption determineTreatment(String riskId) {
        // Retrieve risk from database
        // var risk = db.riskRegister.findOne(riskId);
        String riskLevel = "HIGH"; // From database

        String appetiteDecision = RISK_APPETITE.getOrDefault(riskLevel, "review_required");

        if ("acceptable".equals(appetiteDecision)) {
            return RiskTreatmentOption.ACCEPT;
        } else if ("must_mitigate".equals(appetiteDecision)) {
            return RiskTreatmentOption.MITIGATE;
        } else {
            // Review required - default to mitigate
            return RiskTreatmentOption.MITIGATE;
        }
    }

    /**
     * Create risk treatment plan.
     *
     * ISO 27001 Clause 6.1.3(e): Risk treatment plan required
     */
    public String createTreatmentPlan(
            String riskId,
            RiskTreatmentOption treatmentOption,
            List<String> proposedControls,
            String owner,
            Instant targetCompletionDate) {

        // Retrieve risk from database
        // var risk = db.riskRegister.findOne(riskId);

        String planId = UUID.randomUUID().toString();

        var treatmentPlan = new HashMap<String, Object>();
        treatmentPlan.put("plan_id", planId);
        treatmentPlan.put("risk_id", riskId);
        treatmentPlan.put("treatment_option", treatmentOption.name());
        treatmentPlan.put("proposed_controls", proposedControls);
        treatmentPlan.put("owner", owner);
        treatmentPlan.put("target_completion_date", targetCompletionDate);
        treatmentPlan.put("status", "planned");
        treatmentPlan.put("created_date", Instant.now());

        // Residual risk (estimated after treatment)
        treatmentPlan.put("residual_risk_level", estimateResidualRisk(riskId, proposedControls));

        // Store in database
        // db.riskTreatmentPlans.insertOne(treatmentPlan);

        logger.info("Risk treatment plan created: plan_id={}, risk_id={}, treatment={}",
            planId, riskId, treatmentOption.name());

        return planId;
    }

    /**
     * Estimate residual risk after controls implemented.
     *
     * Assume each control reduces likelihood by 1 level.
     */
    private String estimateResidualRisk(String riskId, List<String> proposedControls) {
        // Retrieve risk from database
        // var risk = db.riskRegister.findOne(riskId);

        int currentLikelihood = 4; // From database
        int likelihoodReduction = Math.min(proposedControls.size(), currentLikelihood - 1);

        int residualLikelihood = currentLikelihood - likelihoodReduction;
        int residualImpact = 3; // From database (impact stays same)

        int residualScore = residualLikelihood * residualImpact;

        if (residualScore >= 19) {
            return "critical";
        } else if (residualScore >= 13) {
            return "high";
        } else if (residualScore >= 7) {
            return "medium";
        } else {
            return "low";
        }
    }

    /**
     * Accept residual risk (after controls implemented).
     *
     * ISO 27001 Clause 6.1.3(f): Obtain risk acceptance from risk owners
     */
    public void acceptResidualRisk(String planId, String approver, String justification) {
        // Retrieve plan from database
        // var plan = db.riskTreatmentPlans.findOne(planId);

        var acceptance = new HashMap<String, Object>();
        acceptance.put("plan_id", planId);
        acceptance.put("risk_id", "risk-123"); // From plan
        acceptance.put("residual_risk_level", "medium"); // From plan
        acceptance.put("approver", approver);
        acceptance.put("justification", justification);
        acceptance.put("accepted_date", Instant.now());

        // Store in database
        // db.riskAcceptances.insertOne(acceptance);

        logger.warn("Residual risk accepted: plan_id={}, approver={}, residual_risk={}",
            planId, approver, "medium");
    }
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
