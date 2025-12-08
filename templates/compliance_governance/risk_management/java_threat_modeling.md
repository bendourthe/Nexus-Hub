---
template_id: compliance_governance_threat_modeling_java
template_name: Threat Modeling - Java
version: 1.0.0
last_updated: 2025-12-05
language: java
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/java_risk_assessment.md
  - compliance_frameworks/java_nist_ai_rmf.md
related_templates:
  - compliance_frameworks/java_soc2_compliance.md
tools:
  - spring-boot (framework)
  - logback (logging)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - java
---

# Threat Modeling - Java

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Systematic threat modeling using STRIDE, PASTA, and attack tree analysis

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is Threat Modeling?

**Threat Modeling** is a structured approach to identify, enumerate, and prioritize potential threats to a system. It's a proactive security practice performed during design and architecture phases.

**Goal**: "What could go wrong?" → "How do we prevent it?"

### Threat Modeling Methodologies

**STRIDE** (Microsoft)
- **S**poofing identity
- **T**ampering with data
- **R**epudiation
- **I**nformation disclosure
- **D**enial of service
- **E**levation of privilege

**PASTA** (Process for Attack Simulation and Threat Analysis)
- 7-stage, risk-centric methodology
- Business objectives → Technical vulnerabilities

**Attack Trees**
- Visual representation of attack paths
- Root = attacker goal, leaves = attack steps

### When to Threat Model

- **Design phase** - Before building (most cost-effective)
- **Major changes** - New features, architecture changes
- **Post-incident** - After security incidents
- **Regular reviews** - Annual threat model review

---

## System Decomposition Implementation

```java
package com.company.compliance.threatmodeling;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class SystemDecomposition {
    private static final Logger logger = LoggerFactory.getLogger(SystemDecomposition.class);

    private final String systemName;
    private final List<Map<String, Object>> components;
    private final List<Map<String, Object>> dataFlows;

    public enum ElementType {
        EXTERNAL_ENTITY,  // External users/systems
        PROCESS,          // Application components
        DATA_STORE,       // Databases, files
        DATA_FLOW         // Communication between elements
    }

    public enum TrustBoundary {
        INTERNET,           // Untrusted external
        DMZ,                // Semi-trusted perimeter
        INTERNAL_NETWORK,   // Trusted internal
        DATABASE_TIER,      // Highly trusted data layer
        AI_MODEL_LAYER      // AI/ML model execution
    }

    public SystemDecomposition(String systemName) {
        this.systemName = systemName;
        this.components = new ArrayList<>();
        this.dataFlows = new ArrayList<>();
    }

    /**
     * Add external entity (users, external systems).
     *
     * External entities are outside system control = high risk.
     */
    public String addExternalEntity(
            String name,
            String description,
            String trustLevel) {

        String entityId = UUID.randomUUID().toString();

        var component = new HashMap<String, Object>();
        component.put("component_id", entityId);
        component.put("component_type", ElementType.EXTERNAL_ENTITY);
        component.put("name", name);
        component.put("description", description);
        component.put("trust_level", trustLevel);
        component.put("trust_boundary", TrustBoundary.INTERNET);

        components.add(component);

        logger.info("External entity added: entity_id={}, name={}", entityId, name);

        return entityId;
    }

    /**
     * Add process (application component).
     *
     * Processes are where data is transformed = attack targets.
     */
    public String addProcess(
            String name,
            String description,
            TrustBoundary trustBoundary,
            String runsAs,
            List<String> technologies) {

        String processId = UUID.randomUUID().toString();

        var component = new HashMap<String, Object>();
        component.put("component_id", processId);
        component.put("component_type", ElementType.PROCESS);
        component.put("name", name);
        component.put("description", description);
        component.put("trust_boundary", trustBoundary);
        component.put("runs_as", runsAs);  // Service account, root, etc.
        component.put("technologies", technologies);

        // Security properties
        component.put("authenticates_users", false);
        component.put("validates_input", false);
        component.put("logs_activity", false);
        component.put("encrypts_data", false);

        components.add(component);

        logger.info("Process added: process_id={}, name={}, trust_boundary={}",
            processId, name, trustBoundary);

        return processId;
    }

    /**
     * Add data store (database, file system, cache).
     *
     * Data stores are high-value targets for attackers.
     */
    public String addDataStore(
            String name,
            String description,
            String dataClassification,
            TrustBoundary trustBoundary,
            String storageType) {

        String datastoreId = UUID.randomUUID().toString();

        var component = new HashMap<String, Object>();
        component.put("component_id", datastoreId);
        component.put("component_type", ElementType.DATA_STORE);
        component.put("name", name);
        component.put("description", description);
        component.put("data_classification", dataClassification);
        component.put("trust_boundary", trustBoundary);
        component.put("storage_type", storageType);

        // Security properties
        component.put("encrypted_at_rest", false);
        component.put("access_controlled", false);
        component.put("backed_up", false);
        component.put("audit_logged", false);

        components.add(component);

        logger.info("Data store added: datastore_id={}, name={}, classification={}",
            datastoreId, name, dataClassification);

        return datastoreId;
    }

    /**
     * Add data flow between components.
     *
     * Flows crossing trust boundaries are high-risk.
     */
    public String addDataFlow(
            String name,
            String sourceId,
            String destinationId,
            String dataDescription,
            String protocol,
            boolean crossesTrustBoundary) {

        String flowId = UUID.randomUUID().toString();

        var dataFlow = new HashMap<String, Object>();
        dataFlow.put("flow_id", flowId);
        dataFlow.put("name", name);
        dataFlow.put("source_id", sourceId);
        dataFlow.put("destination_id", destinationId);
        dataFlow.put("data_description", dataDescription);
        dataFlow.put("protocol", protocol);
        dataFlow.put("crosses_trust_boundary", crossesTrustBoundary);

        // Security properties
        dataFlow.put("encrypted_in_transit", false);
        dataFlow.put("authenticated", false);
        dataFlow.put("authorized", false);

        dataFlows.add(dataFlow);

        logger.info("Data flow added: flow_id={}, name={}, crosses_boundary={}",
            flowId, name, crossesTrustBoundary);

        return flowId;
    }

    public List<Map<String, Object>> getComponents() {
        return components;
    }

    public List<Map<String, Object>> getDataFlows() {
        return dataFlows;
    }
}
```

---

## STRIDE Analysis Implementation

```java
package com.company.compliance.threatmodeling;

@Service
public class STRIDEAnalysis {
    private static final Logger logger = LoggerFactory.getLogger(STRIDEAnalysis.class);

    public enum STRIDECategory {
        SPOOFING,               // Pretending to be something/someone else
        TAMPERING,              // Modifying data or code
        REPUDIATION,            // Denying actions without proof
        INFORMATION_DISCLOSURE, // Exposing information
        DENIAL_OF_SERVICE,      // Degrading or denying service
        ELEVATION_OF_PRIVILEGE  // Gaining unauthorized access
    }

    /**
     * Perform STRIDE analysis on component.
     *
     * Risk Management: Defense in Depth
     * Methodology: Microsoft SDL
     */
    public List<Map<String, Object>> performSTRIDEAnalysis(
            Map<String, Object> component) {

        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");
        String componentId = (String) component.get("component_id");
        String componentName = (String) component.get("name");

        // Analyze each STRIDE category
        threats.addAll(analyzeSpoofing(component));
        threats.addAll(analyzeTampering(component));
        threats.addAll(analyzeRepudiation(component));
        threats.addAll(analyzeInformationDisclosure(component));
        threats.addAll(analyzeDenialOfService(component));
        threats.addAll(analyzeElevationOfPrivilege(component));

        logger.info("STRIDE analysis completed: component_id={}, component_name={}, threats_found={}",
            componentId, componentName, threats.size());

        return threats;
    }

    private List<Map<String, Object>> analyzeSpoofing(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");

        // Spoofing applies to: Processes, External Entities
        if (componentType == SystemDecomposition.ElementType.PROCESS ||
            componentType == SystemDecomposition.ElementType.EXTERNAL_ENTITY) {

            boolean authenticatesUsers = (boolean) component.getOrDefault("authenticates_users", false);

            if (!authenticatesUsers) {
                threats.add(Map.of(
                    "threat_id", UUID.randomUUID().toString(),
                    "component_id", component.get("component_id"),
                    "stride_category", STRIDECategory.SPOOFING,
                    "threat_name", "Identity Spoofing",
                    "description", "Attacker impersonates legitimate user/service",
                    "severity", "high",
                    "mitigations", Arrays.asList(
                        "Implement multi-factor authentication (MFA)",
                        "Use mutual TLS for service-to-service auth",
                        "Token-based authentication (JWT with signature verification)"
                    )
                ));
            }
        }

        return threats;
    }

    private List<Map<String, Object>> analyzeTampering(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");

        // Tampering applies to: Processes, Data Stores, Data Flows
        if (componentType == SystemDecomposition.ElementType.DATA_STORE) {
            boolean accessControlled = (boolean) component.getOrDefault("access_controlled", false);

            if (!accessControlled) {
                threats.add(Map.of(
                    "threat_id", UUID.randomUUID().toString(),
                    "component_id", component.get("component_id"),
                    "stride_category", STRIDECategory.TAMPERING,
                    "threat_name", "Data Tampering",
                    "description", "Unauthorized modification of stored data",
                    "severity", "critical",
                    "mitigations", Arrays.asList(
                        "Implement access control lists (ACLs)",
                        "Use database triggers for integrity checks",
                        "Digital signatures for critical data",
                        "Immutable audit logs"
                    )
                ));
            }
        }

        return threats;
    }

    private List<Map<String, Object>> analyzeRepudiation(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");

        // Repudiation applies to: Processes
        if (componentType == SystemDecomposition.ElementType.PROCESS) {
            boolean logsActivity = (boolean) component.getOrDefault("logs_activity", false);

            if (!logsActivity) {
                threats.add(Map.of(
                    "threat_id", UUID.randomUUID().toString(),
                    "component_id", component.get("component_id"),
                    "stride_category", STRIDECategory.REPUDIATION,
                    "threat_name", "Action Repudiation",
                    "description", "User denies performing action without proof",
                    "severity", "medium",
                    "mitigations", Arrays.asList(
                        "Comprehensive audit logging",
                        "Tamper-proof log storage (WORM, blockchain)",
                        "Digital signatures for transactions",
                        "Non-repudiation mechanisms"
                    )
                ));
            }
        }

        return threats;
    }

    private List<Map<String, Object>> analyzeInformationDisclosure(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");

        // Information Disclosure applies to: Data Stores, Processes
        if (componentType == SystemDecomposition.ElementType.DATA_STORE) {
            boolean encryptedAtRest = (boolean) component.getOrDefault("encrypted_at_rest", false);
            String dataClassification = (String) component.getOrDefault("data_classification", "unknown");

            if (!encryptedAtRest && ("confidential".equals(dataClassification) ||
                                     "restricted".equals(dataClassification))) {
                threats.add(Map.of(
                    "threat_id", UUID.randomUUID().toString(),
                    "component_id", component.get("component_id"),
                    "stride_category", STRIDECategory.INFORMATION_DISCLOSURE,
                    "threat_name", "Data Exposure",
                    "description", "Sensitive data exposed through unauthorized access",
                    "severity", "critical",
                    "mitigations", Arrays.asList(
                        "Encrypt data at rest (AES-256)",
                        "Implement data loss prevention (DLP)",
                        "Least privilege access control",
                        "Data masking/redaction"
                    )
                ));
            }
        }

        return threats;
    }

    private List<Map<String, Object>> analyzeDenialOfService(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        // DoS applies to: Processes, Data Stores
        threats.add(Map.of(
            "threat_id", UUID.randomUUID().toString(),
            "component_id", component.get("component_id"),
            "stride_category", STRIDECategory.DENIAL_OF_SERVICE,
            "threat_name", "Resource Exhaustion",
            "description", "Attacker overwhelms system resources",
            "severity", "high",
            "mitigations", Arrays.asList(
                "Rate limiting and throttling",
                "Resource quotas and circuit breakers",
                "Auto-scaling infrastructure",
                "DDoS protection (Cloudflare, AWS Shield)"
            )
        ));

        return threats;
    }

    private List<Map<String, Object>> analyzeElevationOfPrivilege(Map<String, Object> component) {
        List<Map<String, Object>> threats = new ArrayList<>();

        var componentType = (SystemDecomposition.ElementType) component.get("component_type");

        // Elevation of Privilege applies to: Processes
        if (componentType == SystemDecomposition.ElementType.PROCESS) {
            String runsAs = (String) component.getOrDefault("runs_as", "unknown");

            if ("root".equals(runsAs) || "administrator".equals(runsAs)) {
                threats.add(Map.of(
                    "threat_id", UUID.randomUUID().toString(),
                    "component_id", component.get("component_id"),
                    "stride_category", STRIDECategory.ELEVATION_OF_PRIVILEGE,
                    "threat_name", "Privilege Escalation",
                    "description", "Attacker gains elevated privileges",
                    "severity", "critical",
                    "mitigations", Arrays.asList(
                        "Run with least privilege (dedicated service account)",
                        "Implement role-based access control (RBAC)",
                        "Input validation to prevent injection attacks",
                        "Separate admin functions from user functions"
                    )
                ));
            }
        }

        return threats;
    }
}
```

---

## Attack Tree Analysis Implementation

```java
package com.company.compliance.threatmodeling;

@Service
public class AttackTreeAnalysis {
    private static final Logger logger = LoggerFactory.getLogger(AttackTreeAnalysis.class);

    public static class AttackNode {
        private String nodeId;
        private String attackGoal;
        private String description;
        private String attackType;  // "AND" or "OR"
        private double probability;
        private double cost;
        private List<AttackNode> children;

        public AttackNode(String attackGoal, String description, String attackType) {
            this.nodeId = UUID.randomUUID().toString();
            this.attackGoal = attackGoal;
            this.description = description;
            this.attackType = attackType;
            this.children = new ArrayList<>();
            this.probability = 0.0;
            this.cost = 0.0;
        }

        public void addChild(AttackNode child) {
            children.add(child);
        }

        // Getters and setters
        public String getNodeId() { return nodeId; }
        public String getAttackGoal() { return attackGoal; }
        public List<AttackNode> getChildren() { return children; }
        public double getProbability() { return probability; }
        public void setProbability(double probability) { this.probability = probability; }
        public double getCost() { return cost; }
        public void setCost(double cost) { this.cost = cost; }
    }

    /**
     * Build attack tree for system compromise.
     *
     * Attack trees help visualize attack paths and prioritize defenses.
     */
    public AttackNode buildAttackTree() {
        // Root goal: Compromise system
        AttackNode root = new AttackNode(
            "Compromise System",
            "Attacker gains unauthorized access to system",
            "OR"
        );

        // Attack path 1: Exploit application vulnerability
        AttackNode exploitApp = new AttackNode(
            "Exploit Application Vulnerability",
            "Find and exploit application weakness",
            "AND"
        );
        exploitApp.setProbability(0.3);
        exploitApp.setCost(5000.0);  // Cost to attacker

        AttackNode findVuln = new AttackNode(
            "Find Vulnerability",
            "Discover exploitable weakness",
            "OR"
        );
        findVuln.setProbability(0.6);
        findVuln.setCost(1000.0);

        AttackNode exploitVuln = new AttackNode(
            "Exploit Vulnerability",
            "Successfully exploit discovered weakness",
            "OR"
        );
        exploitVuln.setProbability(0.5);
        exploitVuln.setCost(4000.0);

        exploitApp.addChild(findVuln);
        exploitApp.addChild(exploitVuln);
        root.addChild(exploitApp);

        // Attack path 2: Social engineering
        AttackNode socialEng = new AttackNode(
            "Social Engineering",
            "Manipulate users to gain access",
            "OR"
        );
        socialEng.setProbability(0.4);
        socialEng.setCost(2000.0);

        AttackNode phishing = new AttackNode(
            "Phishing Attack",
            "Send malicious emails to steal credentials",
            "AND"
        );
        phishing.setProbability(0.5);
        phishing.setCost(500.0);

        socialEng.addChild(phishing);
        root.addChild(socialEng);

        // Attack path 3: Insider threat
        AttackNode insider = new AttackNode(
            "Insider Threat",
            "Malicious or compromised insider",
            "OR"
        );
        insider.setProbability(0.2);
        insider.setCost(10000.0);

        root.addChild(insider);

        logger.info("Attack tree built: root_goal={}, total_paths={}",
            root.getAttackGoal(), countAttackPaths(root));

        return root;
    }

    private int countAttackPaths(AttackNode node) {
        if (node.getChildren().isEmpty()) {
            return 1;
        }
        return node.getChildren().stream()
            .mapToInt(this::countAttackPaths)
            .sum();
    }

    /**
     * Calculate attack probability through tree.
     *
     * AND nodes: probability = product of children
     * OR nodes: probability = 1 - product of (1 - child_prob)
     */
    public double calculateAttackProbability(AttackNode node) {
        if (node.getChildren().isEmpty()) {
            return node.getProbability();
        }

        if ("AND".equals(node.attackType)) {
            // AND: All children must succeed
            return node.getChildren().stream()
                .mapToDouble(this::calculateAttackProbability)
                .reduce(1.0, (a, b) -> a * b);
        } else {
            // OR: At least one child must succeed
            double failureProb = node.getChildren().stream()
                .mapToDouble(child -> 1.0 - calculateAttackProbability(child))
                .reduce(1.0, (a, b) -> a * b);
            return 1.0 - failureProb;
        }
    }
}
```

---

## Success Criteria

### System Decomposition Complete

- [ ] Data flow diagrams created for all components
- [ ] Trust boundaries identified and documented
- [ ] Entry/exit points mapped
- [ ] System components cataloged with security properties

### Threat Identification Complete

- [ ] STRIDE analysis performed on all components
- [ ] Threat catalog populated
- [ ] AI-specific threats analyzed
- [ ] Attack surface documented

### Threat Prioritization Complete

- [ ] DREAD scores calculated for all threats
- [ ] Attack trees created for critical assets
- [ ] Threats prioritized by risk
- [ ] Risk ratings assigned

### Mitigation Strategy Complete

- [ ] Security controls mapped to threats
- [ ] Defense-in-depth architecture documented
- [ ] Threat model documentation complete
- [ ] Annual review schedule established

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
