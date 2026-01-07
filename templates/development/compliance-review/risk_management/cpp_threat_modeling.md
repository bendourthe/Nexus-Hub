---
template_id: compliance_governance_threat_modeling_cpp
template_name: Threat Modeling - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/cpp_risk_assessment.md
  - compliance_frameworks/cpp_nist_ai_rmf.md
related_templates:
  - compliance_frameworks/cpp_soc2_compliance.md
tools:
  - spdlog (logging)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - cpp
---

# Threat Modeling - C++

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

```cpp
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <spdlog/spdlog.h>

enum class ElementType {
    ExternalEntity,
    Process,
    DataStore,
    DataFlow
};

enum class TrustBoundary {
    Internet,
    DMZ,
    InternalNetwork,
    DatabaseTier,
    AIModelLayer
};

struct Component {
    std::string componentId;
    ElementType componentType;
    std::string name;
    std::string description;
    TrustBoundary trustBoundary;
    std::map<std::string, std::string> securityProperties;
};

struct DataFlow {
    std::string flowId;
    std::string name;
    std::string sourceId;
    std::string destinationId;
    std::string protocol;
    bool crossesTrustBoundary;
};

class SystemDecomposition {
private:
    std::string systemName;
    std::vector<Component> components;
    std::vector<DataFlow> dataFlows;
    std::shared_ptr<spdlog::logger> logger;

    std::string generateUUID() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "COMP-" << timestamp;
        return ss.str();
    }

public:
    SystemDecomposition(const std::string& systemName,
                       std::shared_ptr<spdlog::logger> logger)
        : systemName(systemName), logger(logger) {}

    std::string addExternalEntity(
        const std::string& name,
        const std::string& description,
        const std::string& trustLevel) {

        std::string entityId = generateUUID();

        Component component;
        component.componentId = entityId;
        component.componentType = ElementType::ExternalEntity;
        component.name = name;
        component.description = description;
        component.trustBoundary = TrustBoundary::Internet;
        component.securityProperties["trust_level"] = trustLevel;

        components.push_back(std::move(component));

        logger->info("External entity added: id={}, name={}", entityId, name);

        return entityId;
    }

    std::string addProcess(
        const std::string& name,
        const std::string& description,
        TrustBoundary trustBoundary,
        const std::string& runsAs,
        const std::vector<std::string>& technologies) {

        std::string processId = generateUUID();

        Component component;
        component.componentId = processId;
        component.componentType = ElementType::Process;
        component.name = name;
        component.description = description;
        component.trustBoundary = trustBoundary;
        component.securityProperties["runs_as"] = runsAs;
        component.securityProperties["authenticates_users"] = "false";
        component.securityProperties["validates_input"] = "false";
        component.securityProperties["logs_activity"] = "false";

        // Store technologies as comma-separated string
        std::stringstream techStream;
        for (size_t i = 0; i < technologies.size(); ++i) {
            if (i > 0) techStream << ",";
            techStream << technologies[i];
        }
        component.securityProperties["technologies"] = techStream.str();

        components.push_back(std::move(component));

        logger->info("Process added: id={}, name={}, trust_boundary={}",
                    processId, name, static_cast<int>(trustBoundary));

        return processId;
    }

    std::string addDataStore(
        const std::string& name,
        const std::string& description,
        const std::string& dataClassification,
        TrustBoundary trustBoundary) {

        std::string datastoreId = generateUUID();

        Component component;
        component.componentId = datastoreId;
        component.componentType = ElementType::DataStore;
        component.name = name;
        component.description = description;
        component.trustBoundary = trustBoundary;
        component.securityProperties["data_classification"] = dataClassification;
        component.securityProperties["encrypted_at_rest"] = "false";
        component.securityProperties["access_controlled"] = "false";

        components.push_back(std::move(component));

        logger->info("Data store added: id={}, name={}, classification={}",
                    datastoreId, name, dataClassification);

        return datastoreId;
    }

    const std::vector<Component>& getComponents() const { return components; }
};
```

---

## STRIDE Analysis Implementation

```cpp
#include <string>
#include <vector>
#include <memory>
#include <map>

enum class STRIDECategory {
    Spoofing,
    Tampering,
    Repudiation,
    InformationDisclosure,
    DenialOfService,
    ElevationOfPrivilege
};

struct Threat {
    std::string threatId;
    std::string componentId;
    STRIDECategory category;
    std::string threatName;
    std::string description;
    std::string severity;
    std::vector<std::string> mitigations;
};

class STRIDEAnalysis {
private:
    std::shared_ptr<spdlog::logger> logger;

    std::string generateThreatID() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "THREAT-" << timestamp;
        return ss.str();
    }

    std::vector<Threat> analyzeSpoofing(const Component& component) {
        std::vector<Threat> threats;

        if (component.componentType == ElementType::Process) {
            auto authIt = component.securityProperties.find("authenticates_users");
            bool authenticates = (authIt != component.securityProperties.end() &&
                                authIt->second == "true");

            if (!authenticates) {
                Threat threat;
                threat.threatId = generateThreatID();
                threat.componentId = component.componentId;
                threat.category = STRIDECategory::Spoofing;
                threat.threatName = "Identity Spoofing";
                threat.description = "Attacker impersonates legitimate user/service";
                threat.severity = "high";
                threat.mitigations = {
                    "Implement multi-factor authentication (MFA)",
                    "Use mutual TLS for service-to-service auth",
                    "Token-based authentication (JWT)"
                };
                threats.push_back(std::move(threat));
            }
        }

        return threats;
    }

    std::vector<Threat> analyzeTampering(const Component& component) {
        std::vector<Threat> threats;

        if (component.componentType == ElementType::DataStore) {
            auto aclIt = component.securityProperties.find("access_controlled");
            bool accessControlled = (aclIt != component.securityProperties.end() &&
                                    aclIt->second == "true");

            if (!accessControlled) {
                Threat threat;
                threat.threatId = generateThreatID();
                threat.componentId = component.componentId;
                threat.category = STRIDECategory::Tampering;
                threat.threatName = "Data Tampering";
                threat.description = "Unauthorized modification of stored data";
                threat.severity = "critical";
                threat.mitigations = {
                    "Implement access control lists (ACLs)",
                    "Database triggers for integrity checks",
                    "Digital signatures for critical data"
                };
                threats.push_back(std::move(threat));
            }
        }

        return threats;
    }

    std::vector<Threat> analyzeRepudiation(const Component& component) {
        std::vector<Threat> threats;

        if (component.componentType == ElementType::Process) {
            auto logIt = component.securityProperties.find("logs_activity");
            bool logsActivity = (logIt != component.securityProperties.end() &&
                               logIt->second == "true");

            if (!logsActivity) {
                Threat threat;
                threat.threatId = generateThreatID();
                threat.componentId = component.componentId;
                threat.category = STRIDECategory::Repudiation;
                threat.threatName = "Action Repudiation";
                threat.description = "User denies performing action without proof";
                threat.severity = "medium";
                threat.mitigations = {
                    "Comprehensive audit logging",
                    "Tamper-proof log storage",
                    "Digital signatures for transactions"
                };
                threats.push_back(std::move(threat));
            }
        }

        return threats;
    }

    std::vector<Threat> analyzeInformationDisclosure(const Component& component) {
        std::vector<Threat> threats;

        if (component.componentType == ElementType::DataStore) {
            auto encIt = component.securityProperties.find("encrypted_at_rest");
            bool encrypted = (encIt != component.securityProperties.end() &&
                            encIt->second == "true");

            auto classIt = component.securityProperties.find("data_classification");
            std::string classification = (classIt != component.securityProperties.end()) ?
                                        classIt->second : "";

            if (!encrypted && (classification == "confidential" ||
                              classification == "restricted")) {
                Threat threat;
                threat.threatId = generateThreatID();
                threat.componentId = component.componentId;
                threat.category = STRIDECategory::InformationDisclosure;
                threat.threatName = "Data Exposure";
                threat.description = "Sensitive data exposed through unauthorized access";
                threat.severity = "critical";
                threat.mitigations = {
                    "Encrypt data at rest (AES-256)",
                    "Data loss prevention (DLP)",
                    "Least privilege access control"
                };
                threats.push_back(std::move(threat));
            }
        }

        return threats;
    }

    std::vector<Threat> analyzeDenialOfService(const Component& component) {
        Threat threat;
        threat.threatId = generateThreatID();
        threat.componentId = component.componentId;
        threat.category = STRIDECategory::DenialOfService;
        threat.threatName = "Resource Exhaustion";
        threat.description = "Attacker overwhelms system resources";
        threat.severity = "high";
        threat.mitigations = {
            "Rate limiting and throttling",
            "Resource quotas and circuit breakers",
            "Auto-scaling infrastructure"
        };

        return {threat};
    }

    std::vector<Threat> analyzeElevationOfPrivilege(const Component& component) {
        std::vector<Threat> threats;

        if (component.componentType == ElementType::Process) {
            auto runsAsIt = component.securityProperties.find("runs_as");
            std::string runsAs = (runsAsIt != component.securityProperties.end()) ?
                                runsAsIt->second : "";

            if (runsAs == "root" || runsAs == "administrator") {
                Threat threat;
                threat.threatId = generateThreatID();
                threat.componentId = component.componentId;
                threat.category = STRIDECategory::ElevationOfPrivilege;
                threat.threatName = "Privilege Escalation";
                threat.description = "Attacker gains elevated privileges";
                threat.severity = "critical";
                threat.mitigations = {
                    "Run with least privilege",
                    "Role-based access control (RBAC)",
                    "Input validation to prevent injection"
                };
                threats.push_back(std::move(threat));
            }
        }

        return threats;
    }

public:
    STRIDEAnalysis(std::shared_ptr<spdlog::logger> logger) : logger(logger) {}

    std::vector<Threat> performSTRIDEAnalysis(const Component& component) {
        std::vector<Threat> allThreats;

        auto spoofingThreats = analyzeSpoofing(component);
        allThreats.insert(allThreats.end(), spoofingThreats.begin(), spoofingThreats.end());

        auto tamperingThreats = analyzeTampering(component);
        allThreats.insert(allThreats.end(), tamperingThreats.begin(), tamperingThreats.end());

        auto repudiationThreats = analyzeRepudiation(component);
        allThreats.insert(allThreats.end(), repudiationThreats.begin(), repudiationThreats.end());

        auto disclosureThreats = analyzeInformationDisclosure(component);
        allThreats.insert(allThreats.end(), disclosureThreats.begin(), disclosureThreats.end());

        auto dosThreats = analyzeDenialOfService(component);
        allThreats.insert(allThreats.end(), dosThreats.begin(), dosThreats.end());

        auto privilegeThreats = analyzeElevationOfPrivilege(component);
        allThreats.insert(allThreats.end(), privilegeThreats.begin(), privilegeThreats.end());

        logger->info("STRIDE analysis completed: component_id={}, threats_found={}",
                    component.componentId, allThreats.size());

        return allThreats;
    }
};
```

---

## Attack Tree Analysis

```cpp
#include <string>
#include <vector>
#include <memory>
#include <algorithm>

struct AttackNode {
    std::string nodeId;
    std::string attackGoal;
    std::string description;
    std::string attackType;  // "AND" or "OR"
    double probability;
    double cost;
    std::vector<std::shared_ptr<AttackNode>> children;
};

class AttackTreeAnalysis {
private:
    std::shared_ptr<spdlog::logger> logger;

    std::string generateNodeID() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "NODE-" << timestamp;
        return ss.str();
    }

public:
    AttackTreeAnalysis(std::shared_ptr<spdlog::logger> logger) : logger(logger) {}

    std::shared_ptr<AttackNode> createAttackNode(
        const std::string& attackGoal,
        const std::string& description,
        const std::string& attackType,
        double probability,
        double cost) {

        auto node = std::make_shared<AttackNode>();
        node->nodeId = generateNodeID();
        node->attackGoal = attackGoal;
        node->description = description;
        node->attackType = attackType;
        node->probability = probability;
        node->cost = cost;

        return node;
    }

    std::shared_ptr<AttackNode> buildAttackTree() {
        // Root goal: Compromise system
        auto root = createAttackNode(
            "Compromise System",
            "Attacker gains unauthorized access",
            "OR",
            0.0,
            0.0
        );

        // Path 1: Exploit application vulnerability
        auto exploitApp = createAttackNode(
            "Exploit Application Vulnerability",
            "Find and exploit weakness",
            "AND",
            0.3,
            5000.0
        );

        auto findVuln = createAttackNode(
            "Find Vulnerability",
            "Discover exploitable weakness",
            "OR",
            0.6,
            1000.0
        );

        auto developExploit = createAttackNode(
            "Develop Exploit",
            "Create working exploit code",
            "OR",
            0.5,
            3000.0
        );

        exploitApp->children.push_back(findVuln);
        exploitApp->children.push_back(developExploit);
        root->children.push_back(exploitApp);

        // Path 2: Social engineering
        auto socialEng = createAttackNode(
            "Social Engineering",
            "Manipulate users",
            "OR",
            0.4,
            2000.0
        );

        auto phishing = createAttackNode(
            "Phishing Campaign",
            "Email-based credential theft",
            "OR",
            0.6,
            500.0
        );

        auto pretexting = createAttackNode(
            "Pretexting",
            "Impersonate trusted party",
            "OR",
            0.3,
            1000.0
        );

        socialEng->children.push_back(phishing);
        socialEng->children.push_back(pretexting);
        root->children.push_back(socialEng);

        // Path 3: Insider threat
        auto insiderThreat = createAttackNode(
            "Insider Threat",
            "Malicious or negligent insider",
            "OR",
            0.2,
            10000.0
        );

        root->children.push_back(insiderThreat);

        logger->info("Attack tree built: root_goal={}", root->attackGoal);

        return root;
    }

    double calculateAttackProbability(const std::shared_ptr<AttackNode>& node) {
        if (node->children.empty()) {
            return node->probability;
        }

        if (node->attackType == "AND") {
            // All children must succeed
            double prob = 1.0;
            for (const auto& child : node->children) {
                prob *= calculateAttackProbability(child);
            }
            return prob;
        } else {
            // OR: At least one child must succeed
            double failureProb = 1.0;
            for (const auto& child : node->children) {
                failureProb *= (1.0 - calculateAttackProbability(child));
            }
            return 1.0 - failureProb;
        }
    }

    double calculateAttackCost(const std::shared_ptr<AttackNode>& node) {
        if (node->children.empty()) {
            return node->cost;
        }

        if (node->attackType == "AND") {
            // Sum costs of all required paths
            double totalCost = 0.0;
            for (const auto& child : node->children) {
                totalCost += calculateAttackCost(child);
            }
            return totalCost;
        } else {
            // OR: Choose minimum cost path
            double minCost = std::numeric_limits<double>::max();
            for (const auto& child : node->children) {
                double childCost = calculateAttackCost(child);
                minCost = std::min(minCost, childCost);
            }
            return minCost;
        }
    }

    std::vector<std::string> identifyCriticalPaths(
        const std::shared_ptr<AttackNode>& node,
        double probabilityThreshold = 0.3) {

        std::vector<std::string> criticalPaths;

        std::function<void(const std::shared_ptr<AttackNode>&, std::string)> traverse;
        traverse = [&](const std::shared_ptr<AttackNode>& current, std::string path) {
            double prob = calculateAttackProbability(current);

            if (prob >= probabilityThreshold) {
                criticalPaths.push_back(path + " → " + current->attackGoal);
            }

            for (const auto& child : current->children) {
                traverse(child, path + " → " + current->attackGoal);
            }
        };

        traverse(node, "ROOT");

        return criticalPaths;
    }
};
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
