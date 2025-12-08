---
template_id: compliance_governance_threat_modeling_csharp
template_name: Threat Modeling - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/csharp_risk_assessment.md
  - compliance_frameworks/csharp_nist_ai_rmf.md
related_templates:
  - compliance_frameworks/csharp_soc2_compliance.md
tools:
  - ASP.NET Core (framework)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - csharp
---

# Threat Modeling - C#

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

## System Decomposition Implementation

```csharp
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.ThreatModeling
{
    public class SystemDecomposition
    {
        private readonly ILogger<SystemDecomposition> _logger;
        private readonly string _systemName;
        private readonly List<Component> _components;
        private readonly List<DataFlow> _dataFlows;

        public enum ElementType
        {
            ExternalEntity,
            Process,
            DataStore,
            DataFlow
        }

        public enum TrustBoundary
        {
            Internet,
            DMZ,
            InternalNetwork,
            DatabaseTier,
            AIModelLayer
        }

        public class Component
        {
            public string ComponentId { get; set; }
            public ElementType ComponentType { get; set; }
            public string Name { get; set; }
            public string Description { get; set; }
            public TrustBoundary TrustBoundary { get; set; }
            public Dictionary<string, object> SecurityProperties { get; set; }
        }

        public class DataFlow
        {
            public string FlowId { get; set; }
            public string Name { get; set; }
            public string SourceId { get; set; }
            public string DestinationId { get; set; }
            public string Protocol { get; set; }
            public bool CrossesTrustBoundary { get; set; }
        }

        public SystemDecomposition(string systemName, ILogger<SystemDecomposition> logger)
        {
            _systemName = systemName;
            _logger = logger;
            _components = new List<Component>();
            _dataFlows = new List<DataFlow>();
        }

        public string AddExternalEntity(string name, string description, string trustLevel)
        {
            var entityId = Guid.NewGuid().ToString();

            _components.Add(new Component
            {
                ComponentId = entityId,
                ComponentType = ElementType.ExternalEntity,
                Name = name,
                Description = description,
                TrustBoundary = TrustBoundary.Internet,
                SecurityProperties = new Dictionary<string, object>
                {
                    { "trust_level", trustLevel }
                }
            });

            _logger.LogInformation("External entity added: {EntityId}, {Name}", entityId, name);
            return entityId;
        }

        public string AddProcess(
            string name,
            string description,
            TrustBoundary trustBoundary,
            string runsAs,
            List<string> technologies)
        {
            var processId = Guid.NewGuid().ToString();

            _components.Add(new Component
            {
                ComponentId = processId,
                ComponentType = ElementType.Process,
                Name = name,
                Description = description,
                TrustBoundary = trustBoundary,
                SecurityProperties = new Dictionary<string, object>
                {
                    { "runs_as", runsAs },
                    { "technologies", technologies },
                    { "authenticates_users", false },
                    { "validates_input", false },
                    { "logs_activity", false }
                }
            });

            _logger.LogInformation("Process added: {ProcessId}, {Name}", processId, name);
            return processId;
        }

        public string AddDataStore(
            string name,
            string description,
            string dataClassification,
            TrustBoundary trustBoundary)
        {
            var datastoreId = Guid.NewGuid().ToString();

            _components.Add(new Component
            {
                ComponentId = datastoreId,
                ComponentType = ElementType.DataStore,
                Name = name,
                Description = description,
                TrustBoundary = trustBoundary,
                SecurityProperties = new Dictionary<string, object>
                {
                    { "data_classification", dataClassification },
                    { "encrypted_at_rest", false },
                    { "access_controlled", false }
                }
            });

            _logger.LogInformation("Data store added: {DatastoreId}, {Name}", datastoreId, name);
            return datastoreId;
        }
    }
}
```

---

## STRIDE Analysis Implementation

```csharp
namespace ComplianceGovernance.ThreatModeling
{
    public class STRIDEAnalysis
    {
        private readonly ILogger<STRIDEAnalysis> _logger;

        public enum STRIDECategory
        {
            Spoofing,
            Tampering,
            Repudiation,
            InformationDisclosure,
            DenialOfService,
            ElevationOfPrivilege
        }

        public class Threat
        {
            public string ThreatId { get; set; }
            public string ComponentId { get; set; }
            public STRIDECategory Category { get; set; }
            public string ThreatName { get; set; }
            public string Description { get; set; }
            public string Severity { get; set; }
            public List<string> Mitigations { get; set; }
        }

        public STRIDEAnalysis(ILogger<STRIDEAnalysis> logger)
        {
            _logger = logger;
        }

        public List<Threat> PerformSTRIDEAnalysis(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            threats.AddRange(AnalyzeSpoofing(component));
            threats.AddRange(AnalyzeTampering(component));
            threats.AddRange(AnalyzeRepudiation(component));
            threats.AddRange(AnalyzeInformationDisclosure(component));
            threats.AddRange(AnalyzeDenialOfService(component));
            threats.AddRange(AnalyzeElevationOfPrivilege(component));

            _logger.LogInformation(
                "STRIDE analysis completed: ComponentId={ComponentId}, ThreatsFound={Count}",
                component.ComponentId, threats.Count);

            return threats;
        }

        private List<Threat> AnalyzeSpoofing(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            if (component.ComponentType == SystemDecomposition.ElementType.Process)
            {
                var authenticates = (bool)component.SecurityProperties.GetValueOrDefault("authenticates_users", false);
                if (!authenticates)
                {
                    threats.Add(new Threat
                    {
                        ThreatId = Guid.NewGuid().ToString(),
                        ComponentId = component.ComponentId,
                        Category = STRIDECategory.Spoofing,
                        ThreatName = "Identity Spoofing",
                        Description = "Attacker impersonates legitimate user/service",
                        Severity = "high",
                        Mitigations = new List<string>
                        {
                            "Implement multi-factor authentication (MFA)",
                            "Use mutual TLS for service-to-service auth",
                            "Token-based authentication (JWT)"
                        }
                    });
                }
            }

            return threats;
        }

        private List<Threat> AnalyzeTampering(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            if (component.ComponentType == SystemDecomposition.ElementType.DataStore)
            {
                var accessControlled = (bool)component.SecurityProperties.GetValueOrDefault("access_controlled", false);
                if (!accessControlled)
                {
                    threats.Add(new Threat
                    {
                        ThreatId = Guid.NewGuid().ToString(),
                        ComponentId = component.ComponentId,
                        Category = STRIDECategory.Tampering,
                        ThreatName = "Data Tampering",
                        Description = "Unauthorized modification of stored data",
                        Severity = "critical",
                        Mitigations = new List<string>
                        {
                            "Implement access control lists (ACLs)",
                            "Database triggers for integrity checks",
                            "Digital signatures for critical data"
                        }
                    });
                }
            }

            return threats;
        }

        private List<Threat> AnalyzeRepudiation(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            if (component.ComponentType == SystemDecomposition.ElementType.Process)
            {
                var logsActivity = (bool)component.SecurityProperties.GetValueOrDefault("logs_activity", false);
                if (!logsActivity)
                {
                    threats.Add(new Threat
                    {
                        ThreatId = Guid.NewGuid().ToString(),
                        ComponentId = component.ComponentId,
                        Category = STRIDECategory.Repudiation,
                        ThreatName = "Action Repudiation",
                        Description = "User denies performing action without proof",
                        Severity = "medium",
                        Mitigations = new List<string>
                        {
                            "Comprehensive audit logging",
                            "Tamper-proof log storage",
                            "Digital signatures for transactions"
                        }
                    });
                }
            }

            return threats;
        }

        private List<Threat> AnalyzeInformationDisclosure(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            if (component.ComponentType == SystemDecomposition.ElementType.DataStore)
            {
                var encrypted = (bool)component.SecurityProperties.GetValueOrDefault("encrypted_at_rest", false);
                var classification = (string)component.SecurityProperties.GetValueOrDefault("data_classification", "unknown");

                if (!encrypted && (classification == "confidential" || classification == "restricted"))
                {
                    threats.Add(new Threat
                    {
                        ThreatId = Guid.NewGuid().ToString(),
                        ComponentId = component.ComponentId,
                        Category = STRIDECategory.InformationDisclosure,
                        ThreatName = "Data Exposure",
                        Description = "Sensitive data exposed through unauthorized access",
                        Severity = "critical",
                        Mitigations = new List<string>
                        {
                            "Encrypt data at rest (AES-256)",
                            "Data loss prevention (DLP)",
                            "Least privilege access control"
                        }
                    });
                }
            }

            return threats;
        }

        private List<Threat> AnalyzeDenialOfService(SystemDecomposition.Component component)
        {
            return new List<Threat>
            {
                new Threat
                {
                    ThreatId = Guid.NewGuid().ToString(),
                    ComponentId = component.ComponentId,
                    Category = STRIDECategory.DenialOfService,
                    ThreatName = "Resource Exhaustion",
                    Description = "Attacker overwhelms system resources",
                    Severity = "high",
                    Mitigations = new List<string>
                    {
                        "Rate limiting and throttling",
                        "Resource quotas and circuit breakers",
                        "Auto-scaling infrastructure"
                    }
                }
            };
        }

        private List<Threat> AnalyzeElevationOfPrivilege(SystemDecomposition.Component component)
        {
            var threats = new List<Threat>();

            if (component.ComponentType == SystemDecomposition.ElementType.Process)
            {
                var runsAs = (string)component.SecurityProperties.GetValueOrDefault("runs_as", "unknown");
                if (runsAs == "root" || runsAs == "administrator")
                {
                    threats.Add(new Threat
                    {
                        ThreatId = Guid.NewGuid().ToString(),
                        ComponentId = component.ComponentId,
                        Category = STRIDECategory.ElevationOfPrivilege,
                        ThreatName = "Privilege Escalation",
                        Description = "Attacker gains elevated privileges",
                        Severity = "critical",
                        Mitigations = new List<string>
                        {
                            "Run with least privilege",
                            "Role-based access control (RBAC)",
                            "Input validation to prevent injection"
                        }
                    });
                }
            }

            return threats;
        }
    }
}
```

---

## Attack Tree Analysis

```csharp
namespace ComplianceGovernance.ThreatModeling
{
    public class AttackTreeAnalysis
    {
        private readonly ILogger<AttackTreeAnalysis> _logger;

        public class AttackNode
        {
            public string NodeId { get; set; }
            public string AttackGoal { get; set; }
            public string Description { get; set; }
            public string AttackType { get; set; }  // "AND" or "OR"
            public double Probability { get; set; }
            public double Cost { get; set; }
            public List<AttackNode> Children { get; set; }

            public AttackNode(string attackGoal, string description, string attackType)
            {
                NodeId = Guid.NewGuid().ToString();
                AttackGoal = attackGoal;
                Description = description;
                AttackType = attackType;
                Children = new List<AttackNode>();
            }
        }

        public AttackTreeAnalysis(ILogger<AttackTreeAnalysis> logger)
        {
            _logger = logger;
        }

        public AttackNode BuildAttackTree()
        {
            var root = new AttackNode(
                "Compromise System",
                "Attacker gains unauthorized access",
                "OR");

            // Path 1: Exploit application vulnerability
            var exploitApp = new AttackNode(
                "Exploit Application Vulnerability",
                "Find and exploit weakness",
                "AND")
            {
                Probability = 0.3,
                Cost = 5000.0
            };

            var findVuln = new AttackNode(
                "Find Vulnerability",
                "Discover exploitable weakness",
                "OR")
            {
                Probability = 0.6,
                Cost = 1000.0
            };

            exploitApp.Children.Add(findVuln);
            root.Children.Add(exploitApp);

            // Path 2: Social engineering
            var socialEng = new AttackNode(
                "Social Engineering",
                "Manipulate users",
                "OR")
            {
                Probability = 0.4,
                Cost = 2000.0
            };

            root.Children.Add(socialEng);

            _logger.LogInformation("Attack tree built: {Goal}", root.AttackGoal);
            return root;
        }

        public double CalculateAttackProbability(AttackNode node)
        {
            if (node.Children.Count == 0)
                return node.Probability;

            if (node.AttackType == "AND")
            {
                // All children must succeed
                double prob = 1.0;
                foreach (var child in node.Children)
                    prob *= CalculateAttackProbability(child);
                return prob;
            }
            else
            {
                // At least one child must succeed
                double failureProb = 1.0;
                foreach (var child in node.Children)
                    failureProb *= (1.0 - CalculateAttackProbability(child));
                return 1.0 - failureProb;
            }
        }
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
