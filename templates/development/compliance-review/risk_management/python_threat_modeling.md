---
template_id: compliance_governance_threat_modeling_python
template_name: Threat Modeling - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/python_risk_assessment.md
  - compliance_frameworks/python_nist_ai_rmf.md
related_templates:
  - ai_agent_governance/python_agent_risk_controls.md
  - compliance_frameworks/python_soc2_compliance.md
tools:
  - pytm (threat modeling library)
  - graphviz (diagram generation)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - python
---

# Threat Modeling - Python

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

## Implementation Roadmap

### Phase 1: System Decomposition (Week 1)

**Deliverables**:
1. Data flow diagrams (DFDs)
2. Trust boundaries identified
3. Entry/exit points mapped
4. System components cataloged

**Code**: See [System Decomposition](#system-decomposition-implementation)

### Phase 2: Threat Identification (Week 2)

**Deliverables**:
1. STRIDE analysis per component
2. Threat catalog
3. AI-specific threat analysis
4. Attack surface analysis

**Code**: See [STRIDE Analysis](#stride-analysis-implementation)

### Phase 3: Threat Prioritization (Week 3)

**Deliverables**:
1. DREAD scores
2. Attack trees
3. Prioritized threat list
4. Risk ratings

**Code**: See [Threat Prioritization](#threat-prioritization-implementation)

### Phase 4: Mitigation Strategy (Week 4)

**Deliverables**:
1. Security controls mapped to threats
2. Defense-in-depth architecture
3. Threat model documentation
4. Review schedule

**Code**: See [Mitigation Strategy](#mitigation-strategy-implementation)

---

## System Decomposition Implementation

### Data Flow Diagrams

**Purpose**: Visual representation of system architecture for threat identification

**Implementation**:

```python
# System decomposition and data flow diagram generation
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class ElementType(Enum):
    """DFD element types."""
    EXTERNAL_ENTITY = "external_entity"  # External users/systems
    PROCESS = "process"                  # Application components
    DATA_STORE = "data_store"            # Databases, files
    DATA_FLOW = "data_flow"              # Communication between elements

class TrustBoundary(Enum):
    """Trust boundaries in system."""
    INTERNET = "internet"                # Untrusted external
    DMZ = "dmz"                          # Semi-trusted perimeter
    INTERNAL_NETWORK = "internal"        # Trusted internal
    DATABASE_TIER = "database"           # Highly trusted data layer
    AI_MODEL_LAYER = "ai_model"          # AI/ML model execution

class SystemDecomposition:
    """
    Decompose system into components for threat modeling.

    Risk Management: Defense in Depth
    Methodology: Microsoft SDL threat modeling
    """

    def __init__(self, system_name: str):
        self.system_name = system_name
        self.components = []
        self.data_flows = []
        self.trust_boundaries = []

    def add_external_entity(
        self,
        name: str,
        description: str,
        trust_level: str = "untrusted"
    ) -> str:
        """
        Add external entity (users, external systems).

        External entities are outside system control = high risk.
        """
        entity_id = generate_uuid()

        component = {
            "component_id": entity_id,
            "component_type": ElementType.EXTERNAL_ENTITY.value,
            "name": name,
            "description": description,
            "trust_level": trust_level,
            "trust_boundary": TrustBoundary.INTERNET.value
        }

        self.components.append(component)

        logger.info("External entity added", extra={
            "entity_id": entity_id,
            "name": name
        })

        return entity_id

    def add_process(
        self,
        name: str,
        description: str,
        trust_boundary: TrustBoundary,
        runs_as: str,
        technologies: List[str]
    ) -> str:
        """
        Add process (application component).

        Processes are where data is transformed = attack targets.
        """
        process_id = generate_uuid()

        component = {
            "component_id": process_id,
            "component_type": ElementType.PROCESS.value,
            "name": name,
            "description": description,
            "trust_boundary": trust_boundary.value,
            "runs_as": runs_as,  # Service account, root, etc.
            "technologies": technologies,

            # Security properties
            "authenticates_users": False,
            "validates_input": False,
            "logs_activity": False,
            "encrypts_data": False
        }

        self.components.append(component)

        logger.info("Process added", extra={
            "process_id": process_id,
            "name": name,
            "trust_boundary": trust_boundary.value
        })

        return process_id

    def add_data_store(
        self,
        name: str,
        description: str,
        data_classification: str,
        trust_boundary: TrustBoundary,
        storage_type: str
    ) -> str:
        """
        Add data store (database, file system, cache).

        Data stores are high-value targets for attackers.
        """
        datastore_id = generate_uuid()

        component = {
            "component_id": datastore_id,
            "component_type": ElementType.DATA_STORE.value,
            "name": name,
            "description": description,
            "data_classification": data_classification,
            "trust_boundary": trust_boundary.value,
            "storage_type": storage_type,

            # Security properties
            "encrypted_at_rest": False,
            "access_controlled": False,
            "backed_up": False,
            "audit_logged": False
        }

        self.components.append(component)

        logger.info("Data store added", extra={
            "datastore_id": datastore_id,
            "name": name,
            "classification": data_classification
        })

        return datastore_id

    def add_data_flow(
        self,
        name: str,
        source_id: str,
        destination_id: str,
        data_description: str,
        protocol: str,
        crosses_trust_boundary: bool = False
    ) -> str:
        """
        Add data flow between components.

        Flows crossing trust boundaries are high-risk.
        """
        flow_id = generate_uuid()

        data_flow = {
            "flow_id": flow_id,
            "name": name,
            "source_id": source_id,
            "destination_id": destination_id,
            "data_description": data_description,
            "protocol": protocol,
            "crosses_trust_boundary": crosses_trust_boundary,

            # Security properties
            "encrypted_in_transit": False,
            "authenticated": False,
            "rate_limited": False
        }

        self.data_flows.append(data_flow)

        if crosses_trust_boundary:
            logger.warning("Data flow crosses trust boundary", extra={
                "flow_id": flow_id,
                "name": name,
                "requires_security_review": True
            })

        return flow_id

    def export_dfd(self, format: str = "json") -> str:
        """
        Export data flow diagram.

        Formats: JSON, Graphviz DOT
        """
        dfd = {
            "system_name": self.system_name,
            "components": self.components,
            "data_flows": self.data_flows,
            "trust_boundaries": [tb.value for tb in TrustBoundary],
            "generated_date": datetime.utcnow().isoformat()
        }

        if format == "json":
            return json.dumps(dfd, indent=2)
        elif format == "dot":
            return self._generate_graphviz(dfd)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_graphviz(self, dfd: Dict) -> str:
        """Generate Graphviz DOT format for visualization."""
        dot = "digraph ThreatModel {\n"
        dot += "  rankdir=LR;\n"
        dot += "  node [shape=box];\n\n"

        # Add nodes
        for component in dfd["components"]:
            comp_type = component["component_type"]
            comp_name = component["name"]
            comp_id = component["component_id"]

            # Different shapes for different types
            if comp_type == "external_entity":
                shape = "square"
            elif comp_type == "process":
                shape = "circle"
            elif comp_type == "data_store":
                shape = "cylinder"

            dot += f'  "{comp_id}" [label="{comp_name}", shape={shape}];\n'

        dot += "\n"

        # Add edges (data flows)
        for flow in dfd["data_flows"]:
            source = flow["source_id"]
            dest = flow["destination_id"]
            label = flow["name"]

            # Red edges for trust boundary crossings
            style = "color=red, style=bold" if flow["crosses_trust_boundary"] else ""

            dot += f'  "{source}" -> "{dest}" [label="{label}", {style}];\n'

        dot += "}\n"
        return dot
```

---

## STRIDE Analysis Implementation

### STRIDE Threat Identification

**Methodology**: Apply STRIDE to each component and data flow

**Implementation**:

```python
# STRIDE threat analysis
from typing import List, Dict

class STRIDECategory(Enum):
    """STRIDE threat categories."""
    SPOOFING = "spoofing"
    TAMPERING = "tampering"
    REPUDIATION = "repudiation"
    INFORMATION_DISCLOSURE = "information_disclosure"
    DENIAL_OF_SERVICE = "denial_of_service"
    ELEVATION_OF_PRIVILEGE = "elevation_of_privilege"

class STRIDEAnalysis:
    """
    STRIDE threat analysis for system components.

    Risk Management: Defense in Depth
    Methodology: Microsoft STRIDE
    """

    # STRIDE applies differently to different element types
    STRIDE_APPLICABILITY = {
        ElementType.EXTERNAL_ENTITY.value: [
            STRIDECategory.SPOOFING,
            STRIDECategory.REPUDIATION
        ],
        ElementType.PROCESS.value: [
            STRIDECategory.SPOOFING,
            STRIDECategory.TAMPERING,
            STRIDECategory.REPUDIATION,
            STRIDECategory.INFORMATION_DISCLOSURE,
            STRIDECategory.DENIAL_OF_SERVICE,
            STRIDECategory.ELEVATION_OF_PRIVILEGE
        ],
        ElementType.DATA_STORE.value: [
            STRIDECategory.TAMPERING,
            STRIDECategory.REPUDIATION,
            STRIDECategory.INFORMATION_DISCLOSURE,
            STRIDECategory.DENIAL_OF_SERVICE
        ],
        ElementType.DATA_FLOW.value: [
            STRIDECategory.TAMPERING,
            STRIDECategory.INFORMATION_DISCLOSURE,
            STRIDECategory.DENIAL_OF_SERVICE
        ]
    }

    def analyze_component(self, component: Dict) -> List[Dict]:
        """
        Perform STRIDE analysis on component.

        Returns list of potential threats.
        """
        component_type = component["component_type"]
        applicable_categories = self.STRIDE_APPLICABILITY.get(component_type, [])

        threats = []

        for category in applicable_categories:
            threat = self._generate_threat(component, category)
            if threat:
                threats.append(threat)

        logger.info("STRIDE analysis completed", extra={
            "component": component["name"],
            "threats_identified": len(threats)
        })

        return threats

    def _generate_threat(self, component: Dict, category: STRIDECategory) -> Optional[Dict]:
        """
        Generate threat for component and STRIDE category.

        Returns threat description and mitigation suggestions.
        """
        component_name = component["name"]
        component_type = component["component_type"]

        # Threat templates
        threat_templates = {
            STRIDECategory.SPOOFING: {
                "title": f"Spoofing attack on {component_name}",
                "description": f"Attacker impersonates legitimate user/system to access {component_name}",
                "examples": [
                    "Credential theft (phishing, keylogging)",
                    "Session hijacking",
                    "Man-in-the-middle attack"
                ],
                "mitigations": [
                    "Implement multi-factor authentication",
                    "Use strong authentication protocols (OAuth 2.0, SAML)",
                    "Certificate pinning for API clients"
                ]
            },

            STRIDECategory.TAMPERING: {
                "title": f"Data tampering in {component_name}",
                "description": f"Attacker modifies data in {component_name}",
                "examples": [
                    "SQL injection modifying database records",
                    "Man-in-the-middle modifying API requests",
                    "Direct database manipulation"
                ],
                "mitigations": [
                    "Input validation and sanitization",
                    "Use parameterized queries (prevent SQL injection)",
                    "Implement integrity checks (hashing, signatures)",
                    "Encrypt data in transit (TLS 1.3)"
                ]
            },

            STRIDECategory.REPUDIATION: {
                "title": f"Repudiation of actions in {component_name}",
                "description": f"User denies performing action in {component_name}",
                "examples": [
                    "User claims they didn't make transaction",
                    "Admin denies making configuration change"
                ],
                "mitigations": [
                    "Comprehensive audit logging",
                    "Digital signatures for critical actions",
                    "Non-repudiable authentication (certificates)"
                ]
            },

            STRIDECategory.INFORMATION_DISCLOSURE: {
                "title": f"Information disclosure from {component_name}",
                "description": f"Attacker gains unauthorized access to data in {component_name}",
                "examples": [
                    "SQL injection extracting database contents",
                    "Insecure API exposing sensitive data",
                    "Directory traversal accessing files",
                    "Error messages revealing system details"
                ],
                "mitigations": [
                    "Encryption at rest (AES-256)",
                    "Encryption in transit (TLS 1.3)",
                    "Access control (RBAC, least privilege)",
                    "Data classification and handling procedures",
                    "Redact sensitive data in logs"
                ]
            },

            STRIDECategory.DENIAL_OF_SERVICE: {
                "title": f"Denial of service against {component_name}",
                "description": f"Attacker makes {component_name} unavailable",
                "examples": [
                    "Resource exhaustion (CPU, memory, disk)",
                    "Network flooding (DDoS)",
                    "Application-layer DoS (algorithmic complexity)"
                ],
                "mitigations": [
                    "Rate limiting",
                    "Resource quotas and throttling",
                    "DDoS protection (CloudFlare, AWS Shield)",
                    "Input validation (prevent resource exhaustion)",
                    "Autoscaling and load balancing"
                ]
            },

            STRIDECategory.ELEVATION_OF_PRIVILEGE: {
                "title": f"Privilege escalation in {component_name}",
                "description": f"Attacker gains higher privileges in {component_name}",
                "examples": [
                    "Exploiting vulnerability to gain admin access",
                    "SQL injection to bypass authorization",
                    "Insecure direct object reference (IDOR)"
                ],
                "mitigations": [
                    "Principle of least privilege",
                    "Role-based access control (RBAC)",
                    "Regular security patching",
                    "Input validation and output encoding",
                    "Secure coding practices"
                ]
            }
        }

        template = threat_templates.get(category)

        if not template:
            return None

        threat = {
            "threat_id": generate_uuid(),
            "component_id": component["component_id"],
            "component_name": component_name,
            "stride_category": category.value,
            "title": template["title"],
            "description": template["description"],
            "examples": template["examples"],
            "mitigations": template["mitigations"],
            "identified_date": datetime.utcnow()
        }

        return threat

    def analyze_ai_specific_threats(self, component: Dict) -> List[Dict]:
        """
        Identify AI/ML-specific threats.

        Beyond STRIDE: AI system threats.
        """
        if "ai" not in component["name"].lower() and "model" not in component["name"].lower():
            return []

        ai_threats = [
            {
                "threat_id": generate_uuid(),
                "component_id": component["component_id"],
                "threat_category": "model_poisoning",
                "title": "Training data poisoning",
                "description": "Attacker injects malicious data into training set to corrupt model",
                "mitigations": [
                    "Validate training data provenance",
                    "Anomaly detection in training data",
                    "Robust training techniques"
                ]
            },
            {
                "threat_id": generate_uuid(),
                "component_id": component["component_id"],
                "threat_category": "adversarial_examples",
                "title": "Adversarial input attacks",
                "description": "Crafted inputs cause model misclassification",
                "mitigations": [
                    "Adversarial training",
                    "Input sanitization",
                    "Ensemble models"
                ]
            },
            {
                "threat_id": generate_uuid(),
                "component_id": component["component_id"],
                "threat_category": "model_extraction",
                "title": "Model stealing via API",
                "description": "Attacker recreates model through API queries",
                "mitigations": [
                    "Rate limiting on API",
                    "Query obfuscation",
                    "Watermarking models"
                ]
            },
            {
                "threat_id": generate_uuid(),
                "component_id": component["component_id"],
                "threat_category": "prompt_injection",
                "title": "Prompt injection (LLMs)",
                "description": "Malicious prompts manipulate LLM behavior",
                "mitigations": [
                    "Input validation and filtering",
                    "Prompt templates with parameterization",
                    "Output validation"
                ]
            }
        ]

        return ai_threats
```

---

## Threat Prioritization Implementation

### DREAD Scoring

**DREAD**: Damage, Reproducibility, Exploitability, Affected users, Discoverability

**Implementation**:

```python
# Threat prioritization with DREAD
class DREADScore:
    """
    DREAD scoring for threat prioritization.

    DREAD Components (1-10 scale):
    - Damage: How bad would an attack be?
    - Reproducibility: How easy to reproduce attack?
    - Exploitability: How easy to launch attack?
    - Affected users: How many users affected?
    - Discoverability: How easy to find vulnerability?
    """

    def calculate_dread_score(self, threat: Dict) -> Dict:
        """
        Calculate DREAD score for threat.

        Returns score breakdown and priority.
        """
        # Assess each DREAD component
        damage = self._assess_damage(threat)
        reproducibility = self._assess_reproducibility(threat)
        exploitability = self._assess_exploitability(threat)
        affected_users = self._assess_affected_users(threat)
        discoverability = self._assess_discoverability(threat)

        # Total DREAD score (average)
        total_score = (damage + reproducibility + exploitability +
                      affected_users + discoverability) / 5

        # Priority classification
        if total_score >= 8:
            priority = "critical"
        elif total_score >= 6:
            priority = "high"
        elif total_score >= 4:
            priority = "medium"
        else:
            priority = "low"

        dread_assessment = {
            "threat_id": threat["threat_id"],
            "damage": damage,
            "reproducibility": reproducibility,
            "exploitability": exploitability,
            "affected_users": affected_users,
            "discoverability": discoverability,
            "total_score": round(total_score, 2),
            "priority": priority,
            "assessed_date": datetime.utcnow()
        }

        logger.info("DREAD score calculated", extra={
            "threat_id": threat["threat_id"],
            "dread_score": total_score,
            "priority": priority
        })

        return dread_assessment

    def _assess_damage(self, threat: Dict) -> int:
        """
        Assess potential damage (1-10).

        10 = Complete system compromise, data breach
        5 = Individual account compromise
        1 = Minimal damage
        """
        category = threat.get("stride_category")

        damage_scores = {
            "information_disclosure": 9,  # Data breach = high damage
            "elevation_of_privilege": 10, # Full compromise
            "tampering": 8,               # Data integrity loss
            "denial_of_service": 6,       # Availability impact
            "spoofing": 7,                # Unauthorized access
            "repudiation": 3              # Lower impact
        }

        return damage_scores.get(category, 5)

    def _assess_reproducibility(self, threat: Dict) -> int:
        """
        Assess ease of reproducing attack (1-10).

        10 = Always reproducible
        5 = Requires specific conditions
        1 = Nearly impossible to reproduce
        """
        # Default to medium reproducibility
        return 7

    def _assess_exploitability(self, threat: Dict) -> int:
        """
        Assess ease of exploiting vulnerability (1-10).

        10 = Trivial (no tools needed)
        5 = Moderate skill required
        1 = Advanced skill, custom tools
        """
        category = threat.get("stride_category")

        # Information disclosure often easier to exploit
        if category == "information_disclosure":
            return 8
        elif category == "denial_of_service":
            return 7  # DDoS tools readily available
        else:
            return 5  # Moderate difficulty

    def _assess_affected_users(self, threat: Dict) -> int:
        """
        Assess number of affected users (1-10).

        10 = All users
        5 = Some users
        1 = Individual users
        """
        # If threat affects data store or core process = all users
        component = db.components.find_one({"component_id": threat["component_id"]})

        if component["component_type"] in ["data_store", "process"]:
            return 9  # Affects all users
        else:
            return 5  # Affects some users

    def _assess_discoverability(self, threat: Dict) -> int:
        """
        Assess ease of discovering vulnerability (1-10).

        10 = Obvious, visible in browser
        5 = Network traffic analysis required
        1 = Requires source code access
        """
        # Default to moderate discoverability
        return 6

class AttackTreeAnalysis:
    """
    Attack tree modeling for complex threats.

    Visualizes attacker paths to achieve goal.
    """

    def create_attack_tree(self, goal: str) -> Dict:
        """
        Create attack tree for attacker goal.

        Example goal: "Exfiltrate customer PII"
        """
        tree = {
            "goal": goal,
            "root_node": {
                "node_id": generate_uuid(),
                "description": goal,
                "type": "OR",  # OR = any child succeeds, AND = all children must succeed
                "children": []
            }
        }

        # Add attack paths
        # Path 1: SQL Injection
        sql_injection_path = {
            "node_id": generate_uuid(),
            "description": "SQL Injection Attack",
            "type": "AND",
            "children": [
                {
                    "node_id": generate_uuid(),
                    "description": "Find vulnerable parameter",
                    "cost": 2,  # Hours
                    "difficulty": "easy"
                },
                {
                    "node_id": generate_uuid(),
                    "description": "Craft SQL injection payload",
                    "cost": 1,
                    "difficulty": "easy"
                },
                {
                    "node_id": generate_uuid(),
                    "description": "Extract data",
                    "cost": 2,
                    "difficulty": "easy"
                }
            ]
        }

        # Path 2: Compromised Credentials
        credential_path = {
            "node_id": generate_uuid(),
            "description": "Compromised Admin Credentials",
            "type": "AND",
            "children": [
                {
                    "node_id": generate_uuid(),
                    "description": "Phishing admin user",
                    "cost": 4,
                    "difficulty": "medium"
                },
                {
                    "node_id": generate_uuid(),
                    "description": "Login with stolen credentials",
                    "cost": 0.5,
                    "difficulty": "easy"
                },
                {
                    "node_id": generate_uuid(),
                    "description": "Export database",
                    "cost": 1,
                    "difficulty": "easy"
                }
            ]
        }

        tree["root_node"]["children"] = [sql_injection_path, credential_path]

        return tree

    def calculate_attack_cost(self, tree: Dict) -> float:
        """
        Calculate minimum cost to achieve goal.

        For OR nodes: minimum of children
        For AND nodes: sum of children
        """
        def calculate_node_cost(node):
            if "cost" in node:
                return node["cost"]

            if not node.get("children"):
                return 0

            child_costs = [calculate_node_cost(child) for child in node["children"]]

            if node["type"] == "OR":
                return min(child_costs)
            else:  # AND
                return sum(child_costs)

        total_cost = calculate_node_cost(tree["root_node"])

        logger.info("Attack tree cost calculated", extra={
            "goal": tree["goal"],
            "minimum_cost_hours": total_cost
        })

        return total_cost
```

---

## Mitigation Strategy Implementation

### Security Control Mapping

**Purpose**: Map security controls to threats (Defense in Depth)

**Implementation**:

```python
# Security control mapping and defense in depth
class SecurityControl:
    """
    Security controls to mitigate threats.

    Defense in Depth: Multiple layers of security.
    """

    def __init__(self, control_id: str, name: str, category: str):
        self.control_id = control_id
        self.name = name
        self.category = category  # Preventive, Detective, Corrective

class MitigationStrategy:
    """
    Map security controls to threats.

    Risk Management: Defense in Depth
    """

    # Security control catalog
    CONTROL_CATALOG = {
        "authentication": SecurityControl(
            "AUTH-001",
            "Multi-factor authentication",
            "preventive"
        ),
        "encryption_transit": SecurityControl(
            "CRYPTO-001",
            "TLS 1.3 encryption in transit",
            "preventive"
        ),
        "encryption_rest": SecurityControl(
            "CRYPTO-002",
            "AES-256 encryption at rest",
            "preventive"
        ),
        "input_validation": SecurityControl(
            "INPUT-001",
            "Input validation and sanitization",
            "preventive"
        ),
        "audit_logging": SecurityControl(
            "LOG-001",
            "Comprehensive audit logging",
            "detective"
        ),
        "rate_limiting": SecurityControl(
            "NET-001",
            "API rate limiting",
            "preventive"
        ),
        "rbac": SecurityControl(
            "AC-001",
            "Role-based access control",
            "preventive"
        )
    }

    def map_controls_to_threat(self, threat: Dict) -> List[SecurityControl]:
        """
        Map security controls to mitigate threat.

        Returns recommended controls.
        """
        category = threat.get("stride_category")

        # Control mapping for each STRIDE category
        control_mapping = {
            "spoofing": ["authentication", "rbac"],
            "tampering": ["input_validation", "encryption_transit", "audit_logging"],
            "repudiation": ["audit_logging"],
            "information_disclosure": ["encryption_rest", "encryption_transit", "rbac"],
            "denial_of_service": ["rate_limiting"],
            "elevation_of_privilege": ["rbac", "input_validation", "audit_logging"]
        }

        control_ids = control_mapping.get(category, [])
        controls = [self.CONTROL_CATALOG[cid] for cid in control_ids]

        logger.info("Controls mapped to threat", extra={
            "threat_id": threat["threat_id"],
            "controls_count": len(controls)
        })

        return controls

    def generate_threat_model_report(self, system_name: str) -> Dict:
        """
        Generate comprehensive threat model report.

        For review and approval.
        """
        # Get all threats for system
        components = list(db.components.find({"system_name": system_name}))
        all_threats = []

        for component in components:
            threats = list(db.threats.find({"component_id": component["component_id"]}))
            all_threats.extend(threats)

        # Prioritize threats
        prioritized_threats = []
        for threat in all_threats:
            dread = DREADScore().calculate_dread_score(threat)
            threat["dread_score"] = dread
            prioritized_threats.append(threat)

        # Sort by priority
        prioritized_threats.sort(key=lambda x: x["dread_score"]["total_score"], reverse=True)

        report = {
            "system_name": system_name,
            "report_date": datetime.utcnow().isoformat(),
            "total_threats": len(all_threats),
            "critical_threats": sum(1 for t in prioritized_threats if t["dread_score"]["priority"] == "critical"),
            "high_threats": sum(1 for t in prioritized_threats if t["dread_score"]["priority"] == "high"),
            "threats": prioritized_threats[:20],  # Top 20
            "recommended_controls": self._aggregate_controls(prioritized_threats)
        }

        return report

    def _aggregate_controls(self, threats: List[Dict]) -> Dict:
        """
        Aggregate recommended controls across all threats.

        Identify most impactful controls.
        """
        control_frequency = {}

        for threat in threats:
            controls = self.map_controls_to_threat(threat)
            for control in controls:
                if control.control_id not in control_frequency:
                    control_frequency[control.control_id] = {
                        "control": control,
                        "threat_count": 0
                    }
                control_frequency[control.control_id]["threat_count"] += 1

        # Sort by frequency
        sorted_controls = sorted(
            control_frequency.values(),
            key=lambda x: x["threat_count"],
            reverse=True
        )

        return sorted_controls[:10]  # Top 10 most impactful
```

---

## Success Criteria

### System Decomposition Complete

- [ ] Data flow diagram created
- [ ] All components identified and documented
- [ ] Trust boundaries defined
- [ ] Data flows mapped
- [ ] Entry/exit points identified

### Threat Identification Complete

- [ ] STRIDE analysis performed on all components
- [ ] AI-specific threats identified
- [ ] Threat catalog populated
- [ ] Attack surface documented

### Threat Prioritization Complete

- [ ] DREAD scores calculated for all threats
- [ ] Threats prioritized (critical/high/medium/low)
- [ ] Attack trees created for critical threats
- [ ] Risk acceptance decisions made

### Mitigation Strategy Complete

- [ ] Security controls mapped to threats
- [ ] Defense-in-depth architecture defined
- [ ] Threat model report generated
- [ ] Stakeholder review conducted

---

## Common Pitfalls

### ❌ Threat Modeling Too Late

**Problem**: Performing threat modeling after system is built.

**Solution**: Threat model during design phase. Cheaper to fix design issues than code.

### ❌ One-Time Exercise

**Problem**: Creating threat model and never updating.

**Solution**: Update threat model when architecture changes. Annual review minimum.

### ❌ Too Generic

**Problem**: Generic threats that don't reflect actual system.

**Solution**: System-specific threats. Use actual component names, data flows.

### ❌ No Prioritization

**Problem**: Treating all threats equally.

**Solution**: Use DREAD or risk scoring to prioritize. Focus on critical/high first.

---

## Resources

### Threat Modeling Methodologies

- [Microsoft SDL Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling)
- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- [PASTA Methodology](https://versprite.com/tag/pasta-threat-modeling/)

### Tools

- **Microsoft Threat Modeling Tool** - Free DFD-based tool
- **OWASP Threat Dragon** - Open-source web-based
- **pytm** - Python threat modeling library
- **IriusRisk** - Commercial threat modeling platform

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete threat modeling implementation for Python
- System decomposition with DFD generation
- STRIDE analysis for all component types
- AI-specific threat identification
- DREAD scoring for prioritization
- Attack tree analysis
- Security control mapping
- Defense-in-depth architecture
- Threat model report generation

**Framework Coverage**:
- STRIDE methodology
- PASTA methodology
- Attack trees
- DREAD prioritization
- Microsoft SDL threat modeling

---

[← Back to Risk Management](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
