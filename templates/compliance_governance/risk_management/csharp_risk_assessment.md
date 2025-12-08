---
template_id: compliance_governance_risk_assessment_csharp
template_name: Risk Assessment - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/csharp_soc2_compliance.md
  - compliance_frameworks/csharp_iso27001_implementation.md
related_templates:
  - risk_management/csharp_threat_modeling.md
  - compliance_frameworks/csharp_nist_ai_rmf.md
tools:
  - ASP.NET Core (framework)
  - Entity Framework Core (data access)
tags:
  - risk-assessment
  - risk-management
  - defense-in-depth
  - compliance
  - csharp
---

# Risk Assessment - C#

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

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.Risk
{
    /// <summary>
    /// Asset inventory and classification.
    ///
    /// ISO 27001 Control 5.9: Inventory of information and assets
    /// Risk Management: Defense in Depth
    /// </summary>
    public class AssetInventory
    {
        private readonly ILogger<AssetInventory> _logger;

        public AssetInventory(ILogger<AssetInventory> logger)
        {
            _logger = logger;
        }

        public enum AssetType
        {
            Data,            // Databases, files, datasets
            Application,     // Software systems
            Infrastructure,  // Servers, networks
            Device,          // Endpoints, mobile devices
            People,          // Personnel with access
            AIModel,         // ML models
            API              // API endpoints
        }

        public enum Confidentiality
        {
            Public = 1,
            Internal = 2,
            Confidential = 3,
            Restricted = 4
        }

        public enum Criticality
        {
            Low = 1,
            Medium = 2,
            High = 3,
            Critical = 4
        }

        /// <summary>
        /// Register information asset in inventory.
        ///
        /// CIA Triad assessment:
        /// - Confidentiality: How sensitive?
        /// - Integrity: How accurate must it be?
        /// - Availability: How available must it be?
        /// </summary>
        public async Task<string> RegisterAsset(
            string assetName,
            AssetType assetType,
            string description,
            string owner,
            Confidentiality confidentiality,
            Criticality integrityRequirement,
            Criticality availabilityRequirement,
            List<string> dependencies = null)
        {
            var assetId = Guid.NewGuid().ToString();

            // Calculate overall criticality (max of CIA)
            var overallCriticality = new[] {
                (int)confidentiality,
                (int)integrityRequirement,
                (int)availabilityRequirement
            }.Max();

            var assetRecord = new
            {
                AssetId = assetId,
                AssetName = assetName,
                AssetType = assetType.ToString(),
                Description = description,
                Owner = owner,

                // CIA Triad classification
                Confidentiality = (int)confidentiality,
                IntegrityRequirement = (int)integrityRequirement,
                AvailabilityRequirement = (int)availabilityRequirement,
                OverallCriticality = overallCriticality,

                // Dependencies
                Dependencies = dependencies ?? new List<string>(),

                // Metadata
                RegisteredDate = DateTime.UtcNow,
                LastReviewed = DateTime.UtcNow,
                Status = "active"
            };

            // Store in database (Entity Framework, Dapper, etc.)
            // await _context.Assets.AddAsync(assetRecord);
            // await _context.SaveChangesAsync();

            _logger.LogInformation(
                "Asset registered: AssetId={AssetId}, AssetName={AssetName}, Criticality={Criticality}",
                assetId, assetName, overallCriticality);

            return assetId;
        }

        /// <summary>
        /// Calculate asset value for risk assessment.
        ///
        /// Value based on:
        /// - Replacement cost
        /// - Business impact if lost
        /// - Regulatory fines if breached
        /// - Reputation damage
        /// </summary>
        public async Task<double> CalculateAssetValue(string assetId)
        {
            // Retrieve asset from database
            // var asset = await _context.Assets.FindAsync(assetId);

            // Base value from criticality
            var criticalityValues = new Dictionary<int, double>
            {
                { 1, 10000 },     // Low
                { 2, 50000 },     // Medium
                { 3, 250000 },    // High
                { 4, 1000000 }    // Critical
            };

            int overallCriticality = 3; // Retrieved from database
            double baseValue = criticalityValues.GetValueOrDefault(overallCriticality, 50000);

            // Multiply by data volume (if applicable)
            // if (asset.AssetType == AssetType.Data)
            // {
            //     int recordCount = asset.RecordCount;
            //     baseValue *= (recordCount / 1000.0);
            // }

            // Multiply by number of dependencies (cascade effects)
            int dependencyCount = 2; // Retrieved from database
            double dependencyMultiplier = 1 + (dependencyCount * 0.2);
            double assetValue = baseValue * dependencyMultiplier;

            _logger.LogInformation(
                "Asset value calculated: AssetId={AssetId}, AssetValue={AssetValue}, Criticality={Criticality}",
                assetId, assetValue, overallCriticality);

            return assetValue;
        }
    }
}
```

---

## Threat Identification Implementation

```csharp
namespace ComplianceGovernance.Risk
{
    /// <summary>
    /// Threat identification and cataloging.
    ///
    /// NIST AI RMF MAP 4.1: Threats identified
    /// Frameworks: STRIDE, MITRE ATT&CK
    /// </summary>
    public class ThreatCatalog
    {
        private readonly ILogger<ThreatCatalog> _logger;

        public ThreatCatalog(ILogger<ThreatCatalog> logger)
        {
            _logger = logger;
        }

        public enum ThreatCategory
        {
            Spoofing,
            Tampering,
            Repudiation,
            InformationDisclosure,
            DenialOfService,
            ElevationOfPrivilege
        }

        public enum ThreatSource
        {
            ExternalAttacker,
            InsiderMalicious,
            InsiderAccidental,
            NaturalDisaster,
            TechnicalFailure,
            AISystem  // AI-specific threats
        }

        /// <summary>
        /// Identify threats applicable to asset.
        ///
        /// Returns list of potential threats based on asset type.
        /// </summary>
        public async Task<List<object>> IdentifyThreats(string assetId)
        {
            // Retrieve asset from database
            // var asset = await _context.Assets.FindAsync(assetId);

            // Threat database (simplified for example)
            var threats = new List<object>
            {
                new
                {
                    ThreatName = "Unauthorized Data Access",
                    ThreatCategory = ThreatCategory.InformationDisclosure,
                    ThreatSource = ThreatSource.ExternalAttacker,
                    Description = "Attacker gains unauthorized access to sensitive data",
                    AttackVectors = new[] { "SQL injection", "Broken authentication", "API exploitation" }
                },
                new
                {
                    ThreatName = "Data Exfiltration",
                    ThreatCategory = ThreatCategory.InformationDisclosure,
                    ThreatSource = ThreatSource.InsiderMalicious,
                    Description = "Insider copies sensitive data to external location",
                    AttackVectors = new[] { "USB drives", "Cloud storage", "Email" }
                },
                new
                {
                    ThreatName = "Ransomware",
                    ThreatCategory = ThreatCategory.DenialOfService,
                    ThreatSource = ThreatSource.ExternalAttacker,
                    Description = "Malware encrypts data, demands ransom",
                    AttackVectors = new[] { "Phishing", "Drive-by download", "RDP exploitation" }
                },
                new
                {
                    ThreatName = "Model Poisoning",
                    ThreatCategory = ThreatCategory.Tampering,
                    ThreatSource = ThreatSource.ExternalAttacker,
                    Description = "Attacker manipulates training data to corrupt model",
                    AttackVectors = new[] { "Data injection", "Label flipping", "Backdoor insertion" }
                },
                new
                {
                    ThreatName = "Prompt Injection",
                    ThreatCategory = ThreatCategory.ElevationOfPrivilege,
                    ThreatSource = ThreatSource.ExternalAttacker,
                    Description = "Malicious prompts manipulate LLM behavior",
                    AttackVectors = new[] { "Direct injection", "Indirect injection via data" }
                }
            };

            // Store threat-asset mappings
            var identifiedThreats = new List<object>();

            foreach (var threat in threats)
            {
                var threatId = Guid.NewGuid().ToString();

                var threatRecord = new
                {
                    ThreatId = threatId,
                    AssetId = assetId,
                    Threat = threat,
                    IdentifiedDate = DateTime.UtcNow
                };

                // Store in database
                // await _context.Threats.AddAsync(threatRecord);

                identifiedThreats.Add(threatRecord);
            }

            // await _context.SaveChangesAsync();

            _logger.LogInformation(
                "Threats identified: AssetId={AssetId}, ThreatsCount={ThreatsCount}",
                assetId, identifiedThreats.Count);

            return identifiedThreats;
        }
    }

    /// <summary>
    /// Vulnerability scanning integration.
    ///
    /// Integration with vulnerability scanners (Nessus, Qualys, etc.)
    /// </summary>
    public class VulnerabilityScanner
    {
        private readonly ILogger<VulnerabilityScanner> _logger;

        public VulnerabilityScanner(ILogger<VulnerabilityScanner> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Scan asset for vulnerabilities.
        ///
        /// Returns CVEs and severity scores (CVSS).
        /// </summary>
        public async Task<List<object>> ScanVulnerabilities(string assetId)
        {
            // Retrieve asset from database
            // var asset = await _context.Assets.FindAsync(assetId);

            // Simulate vulnerability scan results
            // In production: integrate with Nessus, Qualys, OpenVAS, etc.
            var vulnerabilities = new List<object>
            {
                new
                {
                    VulnerabilityId = "CVE-2024-12345",
                    Severity = "high",
                    CvssScore = 8.5,
                    Description = "SQL injection vulnerability",
                    Remediation = "Apply security patch 2024-01"
                }
            };

            // Store vulnerabilities
            foreach (var vuln in vulnerabilities)
            {
                var vulnRecord = new
                {
                    Vulnerability = vuln,
                    AssetId = assetId,
                    ScanDate = DateTime.UtcNow
                };

                // Store in database
                // await _context.Vulnerabilities.AddAsync(vulnRecord);
            }

            // await _context.SaveChangesAsync();

            _logger.LogInformation(
                "Vulnerability scan completed: AssetId={AssetId}, VulnerabilitiesFound={VulnerabilitiesFound}",
                assetId, vulnerabilities.Count);

            return vulnerabilities;
        }
    }
}
```

---

## Risk Analysis Implementation

```csharp
namespace ComplianceGovernance.Risk
{
    /// <summary>
    /// Risk analysis and scoring.
    ///
    /// ISO 27001 Clause 6.1.2(d): Analyze information security risks
    /// Formula: Risk = Likelihood × Impact
    /// </summary>
    public class RiskAnalysis
    {
        private readonly ILogger<RiskAnalysis> _logger;

        public RiskAnalysis(ILogger<RiskAnalysis> logger)
        {
            _logger = logger;
        }

        public enum Likelihood
        {
            Rare = 1,             // <5% annual probability
            Unlikely = 2,         // 5-25%
            Possible = 3,         // 25-50%
            Likely = 4,           // 50-75%
            AlmostCertain = 5     // >75%
        }

        public enum Impact
        {
            Insignificant = 1,  // <$10K loss
            Minor = 2,          // $10K-$100K
            Moderate = 3,       // $100K-$500K
            Major = 4,          // $500K-$1M
            Severe = 5          // >$1M
        }

        public enum RiskLevel
        {
            Low,        // Risk score 1-6
            Medium,     // Risk score 7-12
            High,       // Risk score 13-18
            Critical    // Risk score 19-25
        }

        /// <summary>
        /// Assess likelihood of threat occurring.
        ///
        /// Factors:
        /// - Threat source capability
        /// - Threat source motivation
        /// - Vulnerability severity
        /// - Existing controls effectiveness
        /// </summary>
        public async Task<Likelihood> AssessLikelihood(
            string threatId,
            string assetId,
            List<string> existingControls)
        {
            // Retrieve threat and asset
            // var threat = await _context.Threats.FindAsync(threatId);
            // var asset = await _context.Assets.FindAsync(assetId);
            // var vulnerabilities = await _context.Vulnerabilities
            //     .Where(v => v.AssetId == assetId).ToListAsync();

            // Base likelihood from threat source
            var sourceLikelihood = new Dictionary<string, int>
            {
                { "ExternalAttacker", 4 },      // Likely
                { "InsiderMalicious", 2 },      // Unlikely
                { "InsiderAccidental", 3 },     // Possible
                { "NaturalDisaster", 1 },       // Rare
                { "TechnicalFailure", 3 },      // Possible
                { "AISystem", 3 }               // Possible
            };

            string threatSource = "ExternalAttacker"; // From database
            int baseLikelihood = sourceLikelihood.GetValueOrDefault(threatSource, 3);

            // Adjust for vulnerabilities (increase likelihood)
            int highSeverityVulns = 1; // Count from database
            if (highSeverityVulns > 0)
            {
                baseLikelihood = Math.Min(baseLikelihood + 1, 5);
            }

            // Adjust for existing controls (decrease likelihood)
            double controlReduction = Math.Min(existingControls.Count * 0.5, 2.0);
            int finalLikelihood = Math.Max((int)(baseLikelihood - controlReduction), 1);

            var likelihood = (Likelihood)finalLikelihood;

            _logger.LogInformation(
                "Likelihood assessed: ThreatId={ThreatId}, AssetId={AssetId}, Likelihood={Likelihood}",
                threatId, assetId, likelihood);

            return likelihood;
        }

        /// <summary>
        /// Assess impact if threat materializes.
        ///
        /// Factors:
        /// - Asset value
        /// - Asset criticality
        /// - Regulatory fines
        /// - Reputation damage
        /// </summary>
        public async Task<Impact> AssessImpact(string threatId, string assetId)
        {
            // Retrieve threat and asset
            // var threat = await _context.Threats.FindAsync(threatId);
            // var asset = await _context.Assets.FindAsync(assetId);

            // Asset value
            var assetInventory = new AssetInventory(_logger);
            double assetValue = await assetInventory.CalculateAssetValue(assetId);

            // Base impact from threat category
            var categoryImpact = new Dictionary<string, int>
            {
                { "InformationDisclosure", 4 },      // Major (GDPR fines)
                { "DenialOfService", 3 },            // Moderate (downtime)
                { "Tampering", 4 },                  // Major (data integrity)
                { "ElevationOfPrivilege", 5 },       // Severe (full compromise)
                { "Spoofing", 3 },                   // Moderate
                { "Repudiation", 2 }                 // Minor
            };

            string threatCategory = "InformationDisclosure"; // From database
            int baseImpact = categoryImpact.GetValueOrDefault(threatCategory, 3);

            // Adjust for asset criticality
            int assetCriticality = 4; // From database
            if (assetCriticality == 4)  // Critical
            {
                baseImpact = Math.Min(baseImpact + 1, 5);
            }

            // Financial impact mapping
            Impact financialImpact;
            if (assetValue > 1000000)
                financialImpact = Impact.Severe;
            else if (assetValue > 500000)
                financialImpact = Impact.Major;
            else if (assetValue > 100000)
                financialImpact = Impact.Moderate;
            else if (assetValue > 10000)
                financialImpact = Impact.Minor;
            else
                financialImpact = Impact.Insignificant;

            // Take maximum of category and financial impact
            int finalImpactValue = Math.Max(baseImpact, (int)financialImpact);
            var finalImpact = (Impact)finalImpactValue;

            _logger.LogInformation(
                "Impact assessed: ThreatId={ThreatId}, AssetId={AssetId}, Impact={Impact}, AssetValue={AssetValue}",
                threatId, assetId, finalImpact, assetValue);

            return finalImpact;
        }

        /// <summary>
        /// Calculate risk score.
        ///
        /// Risk = Likelihood × Impact
        /// </summary>
        public async Task<object> CalculateRisk(
            string threatId,
            string assetId,
            List<string> existingControls = null)
        {
            existingControls ??= new List<string>();

            // Assess likelihood and impact
            var likelihood = await AssessLikelihood(threatId, assetId, existingControls);
            var impact = await AssessImpact(threatId, assetId);

            // Calculate risk score
            int riskScore = (int)likelihood * (int)impact;

            // Determine risk level
            RiskLevel riskLevel;
            if (riskScore >= 19)
                riskLevel = RiskLevel.Critical;
            else if (riskScore >= 13)
                riskLevel = RiskLevel.High;
            else if (riskScore >= 7)
                riskLevel = RiskLevel.Medium;
            else
                riskLevel = RiskLevel.Low;

            string riskId = Guid.NewGuid().ToString();

            var riskAnalysisResult = new
            {
                RiskId = riskId,
                ThreatId = threatId,
                AssetId = assetId,
                Likelihood = likelihood.ToString(),
                LikelihoodValue = (int)likelihood,
                Impact = impact.ToString(),
                ImpactValue = (int)impact,
                RiskScore = riskScore,
                RiskLevel = riskLevel.ToString(),
                ExistingControls = existingControls,
                AssessedDate = DateTime.UtcNow
            };

            // Store in risk register
            // await _context.RiskRegister.AddAsync(riskAnalysisResult);
            // await _context.SaveChangesAsync();

            _logger.LogWarning(
                "Risk calculated: RiskId={RiskId}, RiskLevel={RiskLevel}, RiskScore={RiskScore}",
                riskId, riskLevel, riskScore);

            return riskAnalysisResult;
        }
    }
}
```

---

## Risk Treatment Implementation

```csharp
namespace ComplianceGovernance.Risk
{
    /// <summary>
    /// Risk treatment planning.
    ///
    /// ISO 27001 Clause 6.1.3: Risk treatment
    /// Risk Management: Defense in Depth
    /// </summary>
    public class RiskTreatment
    {
        private readonly ILogger<RiskTreatment> _logger;

        public RiskTreatment(ILogger<RiskTreatment> logger)
        {
            _logger = logger;
        }

        public enum RiskTreatmentOption
        {
            Mitigate,   // Implement controls to reduce risk
            Accept,     // Accept risk within tolerance
            Transfer,   // Insurance, outsourcing
            Avoid       // Eliminate activity causing risk
        }

        // Risk appetite (configurable per organization)
        private static readonly Dictionary<string, string> RISK_APPETITE = new()
        {
            { "Low", "acceptable" },
            { "Medium", "review_required" },
            { "High", "must_mitigate" },
            { "Critical", "must_mitigate" }
        };

        /// <summary>
        /// Determine appropriate risk treatment.
        ///
        /// Decision based on risk level and risk appetite.
        /// </summary>
        public async Task<RiskTreatmentOption> DetermineTreatment(string riskId)
        {
            // Retrieve risk from database
            // var risk = await _context.RiskRegister.FindAsync(riskId);
            string riskLevel = "High"; // From database

            string appetiteDecision = RISK_APPETITE.GetValueOrDefault(riskLevel, "review_required");

            if (appetiteDecision == "acceptable")
                return RiskTreatmentOption.Accept;
            else if (appetiteDecision == "must_mitigate")
                return RiskTreatmentOption.Mitigate;
            else
                // Review required - default to mitigate
                return RiskTreatmentOption.Mitigate;
        }

        /// <summary>
        /// Create risk treatment plan.
        ///
        /// ISO 27001 Clause 6.1.3(e): Risk treatment plan required
        /// </summary>
        public async Task<string> CreateTreatmentPlan(
            string riskId,
            RiskTreatmentOption treatmentOption,
            List<string> proposedControls,
            string owner,
            DateTime targetCompletionDate)
        {
            // Retrieve risk from database
            // var risk = await _context.RiskRegister.FindAsync(riskId);

            string planId = Guid.NewGuid().ToString();

            var treatmentPlan = new
            {
                PlanId = planId,
                RiskId = riskId,
                TreatmentOption = treatmentOption.ToString(),
                ProposedControls = proposedControls,
                Owner = owner,
                TargetCompletionDate = targetCompletionDate,
                Status = "planned",
                CreatedDate = DateTime.UtcNow,

                // Residual risk (estimated after treatment)
                ResidualRiskLevel = EstimateResidualRisk(riskId, proposedControls)
            };

            // Store in database
            // await _context.RiskTreatmentPlans.AddAsync(treatmentPlan);
            // await _context.SaveChangesAsync();

            _logger.LogInformation(
                "Risk treatment plan created: PlanId={PlanId}, RiskId={RiskId}, Treatment={Treatment}",
                planId, riskId, treatmentOption);

            return planId;
        }

        /// <summary>
        /// Estimate residual risk after controls implemented.
        ///
        /// Assume each control reduces likelihood by 1 level.
        /// </summary>
        private string EstimateResidualRisk(string riskId, List<string> proposedControls)
        {
            // Retrieve risk from database
            // var risk = _context.RiskRegister.Find(riskId);

            int currentLikelihood = 4; // From database
            int likelihoodReduction = Math.Min(proposedControls.Count, currentLikelihood - 1);

            int residualLikelihood = currentLikelihood - likelihoodReduction;
            int residualImpact = 3; // From database (impact stays same)

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

        /// <summary>
        /// Accept residual risk (after controls implemented).
        ///
        /// ISO 27001 Clause 6.1.3(f): Obtain risk acceptance from risk owners
        /// </summary>
        public async Task AcceptResidualRisk(string planId, string approver, string justification)
        {
            // Retrieve plan from database
            // var plan = await _context.RiskTreatmentPlans.FindAsync(planId);

            var acceptance = new
            {
                PlanId = planId,
                RiskId = "risk-123", // From plan
                ResidualRiskLevel = "medium", // From plan
                Approver = approver,
                Justification = justification,
                AcceptedDate = DateTime.UtcNow
            };

            // Store in database
            // await _context.RiskAcceptances.AddAsync(acceptance);
            // await _context.SaveChangesAsync();

            _logger.LogWarning(
                "Residual risk accepted: PlanId={PlanId}, Approver={Approver}, ResidualRisk={ResidualRisk}",
                planId, approver, "medium");
        }
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
