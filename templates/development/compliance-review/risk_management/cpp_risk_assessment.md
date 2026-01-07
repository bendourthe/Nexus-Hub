---
template_id: compliance_governance_risk_assessment_cpp
template_name: Risk Assessment - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/cpp_soc2_compliance.md
  - compliance_frameworks/cpp_iso27001_implementation.md
related_templates:
  - risk_management/cpp_threat_modeling.md
  - compliance_frameworks/cpp_nist_ai_rmf.md
tools:
  - spdlog (logging)
tags:
  - risk-assessment
  - risk-management
  - defense-in-depth
  - compliance
  - cpp
  - modern-cpp
---

# Risk Assessment - C++

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

```cpp
#include <spdlog/spdlog.h>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <algorithm>

namespace risk {

enum class AssetType {
    Data,
    Application,
    Infrastructure,
    Device,
    People,
    AIModel,
    API
};

enum class Confidentiality {
    Public = 1,
    Internal = 2,
    Confidential = 3,
    Restricted = 4
};

enum class Criticality {
    Low = 1,
    Medium = 2,
    High = 3,
    Critical = 4
};

class AssetInventory {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct AssetRecord {
        std::string assetId;
        std::string assetName;
        AssetType assetType;
        std::string description;
        std::string owner;

        // CIA Triad classification
        Confidentiality confidentiality;
        Criticality integrityRequirement;
        Criticality availabilityRequirement;
        int overallCriticality;

        // Dependencies
        std::vector<std::string> dependencies;

        // Metadata
        std::chrono::system_clock::time_point registeredDate;
        std::chrono::system_clock::time_point lastReviewed;
        std::string status;
    };

    explicit AssetInventory(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /// Register information asset in inventory.
    ///
    /// ISO 27001 Control 5.9: Inventory of information and assets
    /// CIA Triad assessment:
    /// - Confidentiality: How sensitive?
    /// - Integrity: How accurate must it be?
    /// - Availability: How available must it be?
    std::string registerAsset(
        const std::string& assetName,
        AssetType assetType,
        const std::string& description,
        const std::string& owner,
        Confidentiality confidentiality,
        Criticality integrityRequirement,
        Criticality availabilityRequirement,
        const std::vector<std::string>& dependencies = {}) {

        auto now = std::chrono::system_clock::now();
        auto assetId = "ASSET-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        // Calculate overall criticality (max of CIA)
        int overallCriticality = std::max({
            static_cast<int>(confidentiality),
            static_cast<int>(integrityRequirement),
            static_cast<int>(availabilityRequirement)
        });

        AssetRecord record;
        record.assetId = assetId;
        record.assetName = assetName;
        record.assetType = assetType;
        record.description = description;
        record.owner = owner;
        record.confidentiality = confidentiality;
        record.integrityRequirement = integrityRequirement;
        record.availabilityRequirement = availabilityRequirement;
        record.overallCriticality = overallCriticality;
        record.dependencies = dependencies;
        record.registeredDate = now;
        record.lastReviewed = now;
        record.status = "active";

        // Store in database

        logger_->info("Asset registered: asset_id={}, asset_name={}, criticality={}",
                     assetId, assetName, overallCriticality);

        return assetId;
    }

    /// Calculate asset value for risk assessment.
    ///
    /// Value based on:
    /// - Replacement cost
    /// - Business impact if lost
    /// - Regulatory fines if breached
    /// - Reputation damage
    double calculateAssetValue(const std::string& assetId) {
        // Retrieve asset from database
        // auto asset = db.findAsset(assetId);

        // Base value from criticality
        static const std::map<int, double> criticalityValues = {
            {1, 10000.0},    // Low
            {2, 50000.0},    // Medium
            {3, 250000.0},   // High
            {4, 1000000.0}   // Critical
        };

        int overallCriticality = 3; // Retrieved from database
        double baseValue = criticalityValues.at(overallCriticality);

        // Multiply by data volume (if applicable)
        // if (asset.assetType == AssetType::Data) {
        //     int recordCount = asset.recordCount;
        //     baseValue *= (recordCount / 1000.0);
        // }

        // Multiply by number of dependencies (cascade effects)
        int dependencyCount = 2; // Retrieved from database
        double dependencyMultiplier = 1 + (dependencyCount * 0.2);
        double assetValue = baseValue * dependencyMultiplier;

        logger_->info("Asset value calculated: asset_id={}, asset_value={:.2f}, criticality={}",
                     assetId, assetValue, overallCriticality);

        return assetValue;
    }
};

} // namespace risk
```

---

## Threat Identification Implementation

```cpp
namespace risk {

enum class ThreatCategory {
    Spoofing,
    Tampering,
    Repudiation,
    InformationDisclosure,
    DenialOfService,
    ElevationOfPrivilege
};

enum class ThreatSource {
    ExternalAttacker,
    InsiderMalicious,
    InsiderAccidental,
    NaturalDisaster,
    TechnicalFailure,
    AISystem
};

class ThreatCatalog {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct ThreatRecord {
        std::string threatId;
        std::string assetId;
        std::string threatName;
        ThreatCategory threatCategory;
        ThreatSource threatSource;
        std::string description;
        std::vector<std::string> attackVectors;
        std::chrono::system_clock::time_point identifiedDate;
    };

    explicit ThreatCatalog(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /// Identify threats applicable to asset.
    ///
    /// NIST AI RMF MAP 4.1: Threats identified
    /// Returns list of potential threats based on asset type.
    std::vector<ThreatRecord> identifyThreats(const std::string& assetId) {
        // Retrieve asset from database
        // auto asset = db.findAsset(assetId);

        auto now = std::chrono::system_clock::now();
        std::vector<ThreatRecord> threats;

        // Threat 1: Unauthorized Data Access
        threats.push_back({
            "THREAT-" + std::to_string(now.time_since_epoch().count()) + "-0",
            assetId,
            "Unauthorized Data Access",
            ThreatCategory::InformationDisclosure,
            ThreatSource::ExternalAttacker,
            "Attacker gains unauthorized access to sensitive data",
            {"SQL injection", "Broken authentication", "API exploitation"},
            now
        });

        // Threat 2: Data Exfiltration
        threats.push_back({
            "THREAT-" + std::to_string(now.time_since_epoch().count()) + "-1",
            assetId,
            "Data Exfiltration",
            ThreatCategory::InformationDisclosure,
            ThreatSource::InsiderMalicious,
            "Insider copies sensitive data to external location",
            {"USB drives", "Cloud storage", "Email"},
            now
        });

        // Threat 3: Ransomware
        threats.push_back({
            "THREAT-" + std::to_string(now.time_since_epoch().count()) + "-2",
            assetId,
            "Ransomware",
            ThreatCategory::DenialOfService,
            ThreatSource::ExternalAttacker,
            "Malware encrypts data, demands ransom",
            {"Phishing", "Drive-by download", "RDP exploitation"},
            now
        });

        // Threat 4: Model Poisoning
        threats.push_back({
            "THREAT-" + std::to_string(now.time_since_epoch().count()) + "-3",
            assetId,
            "Model Poisoning",
            ThreatCategory::Tampering,
            ThreatSource::ExternalAttacker,
            "Attacker manipulates training data to corrupt model",
            {"Data injection", "Label flipping", "Backdoor insertion"},
            now
        });

        // Threat 5: Prompt Injection
        threats.push_back({
            "THREAT-" + std::to_string(now.time_since_epoch().count()) + "-4",
            assetId,
            "Prompt Injection",
            ThreatCategory::ElevationOfPrivilege,
            ThreatSource::ExternalAttacker,
            "Malicious prompts manipulate LLM behavior",
            {"Direct injection", "Indirect injection via data"},
            now
        });

        // Store threats in database

        logger_->info("Threats identified: asset_id={}, threats_count={}",
                     assetId, threats.size());

        return threats;
    }
};

class VulnerabilityScanner {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct VulnerabilityRecord {
        std::string vulnerabilityId;
        std::string severity;
        double cvssScore;
        std::string description;
        std::string remediation;
        std::string assetId;
        std::chrono::system_clock::time_point scanDate;
    };

    explicit VulnerabilityScanner(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /// Scan asset for vulnerabilities.
    ///
    /// Returns CVEs and severity scores (CVSS).
    /// Integration with vulnerability scanners (Nessus, Qualys, etc.)
    std::vector<VulnerabilityRecord> scanVulnerabilities(const std::string& assetId) {
        // Retrieve asset from database
        // auto asset = db.findAsset(assetId);

        // Simulate vulnerability scan results
        // In production: integrate with Nessus, Qualys, OpenVAS, etc.
        std::vector<VulnerabilityRecord> vulnerabilities = {
            {
                "CVE-2024-12345",
                "high",
                8.5,
                "SQL injection vulnerability",
                "Apply security patch 2024-01",
                assetId,
                std::chrono::system_clock::now()
            }
        };

        // Store vulnerabilities in database

        logger_->info("Vulnerability scan completed: asset_id={}, vulnerabilities_found={}",
                     assetId, vulnerabilities.size());

        return vulnerabilities;
    }
};

} // namespace risk
```

---

## Risk Analysis Implementation

```cpp
namespace risk {

enum class Likelihood {
    Rare = 1,             // <5% annual probability
    Unlikely = 2,         // 5-25%
    Possible = 3,         // 25-50%
    Likely = 4,           // 50-75%
    AlmostCertain = 5     // >75%
};

enum class Impact {
    Insignificant = 1,  // <$10K loss
    Minor = 2,          // $10K-$100K
    Moderate = 3,       // $100K-$500K
    Major = 4,          // $500K-$1M
    Severe = 5          // >$1M
};

enum class RiskLevel {
    Low,        // Risk score 1-6
    Medium,     // Risk score 7-12
    High,       // Risk score 13-18
    Critical    // Risk score 19-25
};

class RiskAnalysis {
private:
    std::shared_ptr<spdlog::logger> logger_;

public:
    struct RiskAnalysisResult {
        std::string riskId;
        std::string threatId;
        std::string assetId;
        Likelihood likelihood;
        Impact impact;
        int riskScore;
        RiskLevel riskLevel;
        std::vector<std::string> existingControls;
        std::chrono::system_clock::time_point assessedDate;
    };

    explicit RiskAnalysis(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /// Assess likelihood of threat occurring.
    ///
    /// ISO 27001 Clause 6.1.2(d): Analyze information security risks
    ///
    /// Factors:
    /// - Threat source capability
    /// - Threat source motivation
    /// - Vulnerability severity
    /// - Existing controls effectiveness
    Likelihood assessLikelihood(
        const ThreatCatalog::ThreatRecord& threat,
        const AssetInventory::AssetRecord& asset,
        const std::vector<std::string>& existingControls) {

        // Base likelihood from threat source
        static const std::map<ThreatSource, int> sourceLikelihood = {
            {ThreatSource::ExternalAttacker, 4},    // Likely
            {ThreatSource::InsiderMalicious, 2},    // Unlikely
            {ThreatSource::InsiderAccidental, 3},   // Possible
            {ThreatSource::NaturalDisaster, 1},     // Rare
            {ThreatSource::TechnicalFailure, 3},    // Possible
            {ThreatSource::AISystem, 3}             // Possible
        };

        int baseLikelihood = sourceLikelihood.at(threat.threatSource);

        // Adjust for vulnerabilities (increase likelihood)
        int highSeverityVulns = 1; // Count from database
        if (highSeverityVulns > 0) {
            baseLikelihood = std::min(baseLikelihood + 1, 5);
        }

        // Adjust for existing controls (decrease likelihood)
        double controlReduction = std::min(existingControls.size() * 0.5, 2.0);
        int finalLikelihood = std::max(static_cast<int>(baseLikelihood - controlReduction), 1);

        auto likelihood = static_cast<Likelihood>(finalLikelihood);

        logger_->info("Likelihood assessed: threat_id={}, asset_id={}, likelihood={}",
                     threat.threatId, asset.assetId, finalLikelihood);

        return likelihood;
    }

    /// Assess impact if threat materializes.
    ///
    /// Factors:
    /// - Asset value
    /// - Asset criticality
    /// - Regulatory fines
    /// - Reputation damage
    Impact assessImpact(
        const ThreatCatalog::ThreatRecord& threat,
        const AssetInventory::AssetRecord& asset) {

        // Asset value
        AssetInventory assetInventory(logger_);
        double assetValue = assetInventory.calculateAssetValue(asset.assetId);

        // Base impact from threat category
        static const std::map<ThreatCategory, int> categoryImpact = {
            {ThreatCategory::InformationDisclosure, 4},     // Major (GDPR fines)
            {ThreatCategory::DenialOfService, 3},           // Moderate (downtime)
            {ThreatCategory::Tampering, 4},                 // Major (data integrity)
            {ThreatCategory::ElevationOfPrivilege, 5},      // Severe (full compromise)
            {ThreatCategory::Spoofing, 3},                  // Moderate
            {ThreatCategory::Repudiation, 2}                // Minor
        };

        int baseImpact = categoryImpact.at(threat.threatCategory);

        // Adjust for asset criticality
        if (asset.overallCriticality == 4) {  // Critical
            baseImpact = std::min(baseImpact + 1, 5);
        }

        // Financial impact mapping
        Impact financialImpact;
        if (assetValue > 1000000)
            financialImpact = Impact::Severe;
        else if (assetValue > 500000)
            financialImpact = Impact::Major;
        else if (assetValue > 100000)
            financialImpact = Impact::Moderate;
        else if (assetValue > 10000)
            financialImpact = Impact::Minor;
        else
            financialImpact = Impact::Insignificant;

        // Take maximum of category and financial impact
        int finalImpactValue = std::max(baseImpact, static_cast<int>(financialImpact));
        auto finalImpact = static_cast<Impact>(finalImpactValue);

        logger_->info("Impact assessed: threat_id={}, asset_id={}, impact={}, asset_value={:.2f}",
                     threat.threatId, asset.assetId, finalImpactValue, assetValue);

        return finalImpact;
    }

    /// Calculate risk score.
    ///
    /// Risk = Likelihood × Impact
    RiskAnalysisResult calculateRisk(
        const ThreatCatalog::ThreatRecord& threat,
        const AssetInventory::AssetRecord& asset,
        const std::vector<std::string>& existingControls = {}) {

        auto likelihood = assessLikelihood(threat, asset, existingControls);
        auto impact = assessImpact(threat, asset);

        int riskScore = static_cast<int>(likelihood) * static_cast<int>(impact);

        RiskLevel riskLevel;
        if (riskScore >= 19)
            riskLevel = RiskLevel::Critical;
        else if (riskScore >= 13)
            riskLevel = RiskLevel::High;
        else if (riskScore >= 7)
            riskLevel = RiskLevel::Medium;
        else
            riskLevel = RiskLevel::Low;

        auto riskId = "RISK-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count());

        RiskAnalysisResult result{
            riskId,
            threat.threatId,
            asset.assetId,
            likelihood,
            impact,
            riskScore,
            riskLevel,
            existingControls,
            std::chrono::system_clock::now()
        };

        // Store in risk register

        logger_->warn("Risk calculated: risk_id={}, risk_level={}, risk_score={}",
                     riskId, static_cast<int>(riskLevel), riskScore);

        return result;
    }
};

} // namespace risk
```

---

## Risk Treatment Implementation

```cpp
namespace risk {

enum class TreatmentOption {
    Mitigate,   // Implement controls to reduce risk
    Accept,     // Accept risk within tolerance
    Transfer,   // Insurance, outsourcing
    Avoid       // Eliminate activity causing risk
};

class RiskTreatment {
private:
    std::shared_ptr<spdlog::logger> logger_;

    // Risk appetite (configurable per organization)
    static const std::map<RiskLevel, std::string> riskAppetite;

public:
    struct TreatmentPlan {
        std::string planId;
        std::string riskId;
        TreatmentOption treatmentOption;
        std::vector<std::string> proposedControls;
        std::string owner;
        std::chrono::system_clock::time_point targetCompletionDate;
        std::string status;
        std::chrono::system_clock::time_point createdDate;
        std::string residualRiskLevel;
    };

    explicit RiskTreatment(std::shared_ptr<spdlog::logger> logger)
        : logger_(std::move(logger)) {}

    /// Determine appropriate risk treatment.
    ///
    /// ISO 27001 Clause 6.1.3: Risk treatment
    /// Decision based on risk level and risk appetite.
    TreatmentOption determineTreatment(const RiskAnalysis::RiskAnalysisResult& risk) {
        std::string appetiteDecision = riskAppetite.at(risk.riskLevel);

        if (appetiteDecision == "acceptable")
            return TreatmentOption::Accept;
        else if (appetiteDecision == "must_mitigate")
            return TreatmentOption::Mitigate;
        else
            return TreatmentOption::Mitigate;  // Review required - default to mitigate
    }

    /// Create risk treatment plan.
    ///
    /// ISO 27001 Clause 6.1.3(e): Risk treatment plan required
    std::string createTreatmentPlan(
        const RiskAnalysis::RiskAnalysisResult& risk,
        TreatmentOption treatmentOption,
        const std::vector<std::string>& proposedControls,
        const std::string& owner,
        const std::chrono::system_clock::time_point& targetCompletionDate) {

        auto now = std::chrono::system_clock::now();
        auto planId = "PLAN-" + std::to_string(now.time_since_epoch().count());

        TreatmentPlan plan{
            planId,
            risk.riskId,
            treatmentOption,
            proposedControls,
            owner,
            targetCompletionDate,
            "planned",
            now,
            estimateResidualRisk(risk, proposedControls)
        };

        // Store in database

        logger_->info("Risk treatment plan created: plan_id={}, risk_id={}, treatment={}",
                     planId, risk.riskId, static_cast<int>(treatmentOption));

        return planId;
    }

private:
    /// Estimate residual risk after controls implemented.
    ///
    /// Assume each control reduces likelihood by 1 level.
    std::string estimateResidualRisk(
        const RiskAnalysis::RiskAnalysisResult& risk,
        const std::vector<std::string>& proposedControls) {

        int currentLikelihood = static_cast<int>(risk.likelihood);
        int likelihoodReduction = std::min(static_cast<int>(proposedControls.size()),
                                          currentLikelihood - 1);

        int residualLikelihood = currentLikelihood - likelihoodReduction;
        int residualImpact = static_cast<int>(risk.impact);

        int residualScore = residualLikelihood * residualImpact;

        if (residualScore >= 19)
            return "critical";
        else if (residualScore >= 13)
            return "high";
        else if (residualScore >= 7)
            return "medium";
        else
            return "low";
    }
};

const std::map<RiskLevel, std::string> RiskTreatment::riskAppetite = {
    {RiskLevel::Low, "acceptable"},
    {RiskLevel::Medium, "review_required"},
    {RiskLevel::High, "must_mitigate"},
    {RiskLevel::Critical, "must_mitigate"}
};

} // namespace risk
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
