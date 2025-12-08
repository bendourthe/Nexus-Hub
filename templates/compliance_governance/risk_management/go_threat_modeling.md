---
template_id: compliance_governance_threat_modeling_go
template_name: Threat Modeling - Go
version: 1.0.0
last_updated: 2025-12-05
language: go
category: compliance_governance
phase: risk_management
phase_number: 2
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - risk_management/go_risk_assessment.md
  - compliance_frameworks/go_nist_ai_rmf.md
related_templates:
  - compliance_frameworks/go_soc2_compliance.md
tools:
  - logrus (logging)
tags:
  - threat-modeling
  - stride
  - attack-trees
  - defense-in-depth
  - go
---

# Threat Modeling - Go

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

```go
package threatmodeling

import (
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type ElementType string

const (
	ElementTypeExternalEntity ElementType = "external_entity"
	ElementTypeProcess        ElementType = "process"
	ElementTypeDataStore      ElementType = "data_store"
	ElementTypeDataFlow       ElementType = "data_flow"
)

type TrustBoundary string

const (
	TrustBoundaryInternet        TrustBoundary = "internet"
	TrustBoundaryDMZ             TrustBoundary = "dmz"
	TrustBoundaryInternalNetwork TrustBoundary = "internal"
	TrustBoundaryDatabaseTier    TrustBoundary = "database"
	TrustBoundaryAIModelLayer    TrustBoundary = "ai_model"
)

type Component struct {
	ComponentID        string
	ComponentType      ElementType
	Name               string
	Description        string
	TrustBoundary      TrustBoundary
	SecurityProperties map[string]interface{}
}

type DataFlow struct {
	FlowID               string
	Name                 string
	SourceID             string
	DestinationID        string
	Protocol             string
	CrossesTrustBoundary bool
}

type SystemDecomposition struct {
	systemName string
	components []Component
	dataFlows  []DataFlow
	logger     *logrus.Logger
}

func NewSystemDecomposition(systemName string, logger *logrus.Logger) *SystemDecomposition {
	return &SystemDecomposition{
		systemName: systemName,
		components: []Component{},
		dataFlows:  []DataFlow{},
		logger:     logger,
	}
}

func (sd *SystemDecomposition) AddExternalEntity(name, description, trustLevel string) string {
	entityID := uuid.New().String()

	component := Component{
		ComponentID:   entityID,
		ComponentType: ElementTypeExternalEntity,
		Name:          name,
		Description:   description,
		TrustBoundary: TrustBoundaryInternet,
		SecurityProperties: map[string]interface{}{
			"trust_level": trustLevel,
		},
	}

	sd.components = append(sd.components, component)

	sd.logger.WithFields(logrus.Fields{
		"entity_id": entityID,
		"name":      name,
		"timestamp": time.Now().UTC(),
	}).Info("External entity added")

	return entityID
}

func (sd *SystemDecomposition) AddProcess(
	name, description string,
	trustBoundary TrustBoundary,
	runsAs string,
	technologies []string,
) string {
	processID := uuid.New().String()

	component := Component{
		ComponentID:   processID,
		ComponentType: ElementTypeProcess,
		Name:          name,
		Description:   description,
		TrustBoundary: trustBoundary,
		SecurityProperties: map[string]interface{}{
			"runs_as":            runsAs,
			"technologies":       technologies,
			"authenticates_users": false,
			"validates_input":     false,
			"logs_activity":       false,
		},
	}

	sd.components = append(sd.components, component)

	sd.logger.WithFields(logrus.Fields{
		"process_id":     processID,
		"name":           name,
		"trust_boundary": trustBoundary,
		"timestamp":      time.Now().UTC(),
	}).Info("Process added")

	return processID
}

func (sd *SystemDecomposition) AddDataStore(
	name, description, dataClassification string,
	trustBoundary TrustBoundary,
) string {
	datastoreID := uuid.New().String()

	component := Component{
		ComponentID:   datastoreID,
		ComponentType: ElementTypeDataStore,
		Name:          name,
		Description:   description,
		TrustBoundary: trustBoundary,
		SecurityProperties: map[string]interface{}{
			"data_classification": dataClassification,
			"encrypted_at_rest":   false,
			"access_controlled":   false,
		},
	}

	sd.components = append(sd.components, component)

	sd.logger.WithFields(logrus.Fields{
		"datastore_id":   datastoreID,
		"name":           name,
		"classification": dataClassification,
		"timestamp":      time.Now().UTC(),
	}).Info("Data store added")

	return datastoreID
}
```

---

## STRIDE Analysis Implementation

```go
package threatmodeling

type STRIDECategory string

const (
	STRIDECategorySpoofing              STRIDECategory = "spoofing"
	STRIDECategoryTampering             STRIDECategory = "tampering"
	STRIDECategoryRepudiation           STRIDECategory = "repudiation"
	STRIDECategoryInformationDisclosure STRIDECategory = "information_disclosure"
	STRIDECategoryDenialOfService       STRIDECategory = "denial_of_service"
	STRIDECategoryElevationOfPrivilege  STRIDECategory = "elevation_of_privilege"
)

type Threat struct {
	ThreatID    string
	ComponentID string
	Category    STRIDECategory
	ThreatName  string
	Description string
	Severity    string
	Mitigations []string
}

type STRIDEAnalysis struct {
	logger *logrus.Logger
}

func NewSTRIDEAnalysis(logger *logrus.Logger) *STRIDEAnalysis {
	return &STRIDEAnalysis{logger: logger}
}

func (sa *STRIDEAnalysis) PerformSTRIDEAnalysis(component Component) []Threat {
	var threats []Threat

	threats = append(threats, sa.analyzeSpoofing(component)...)
	threats = append(threats, sa.analyzeTampering(component)...)
	threats = append(threats, sa.analyzeRepudiation(component)...)
	threats = append(threats, sa.analyzeInformationDisclosure(component)...)
	threats = append(threats, sa.analyzeDenialOfService(component)...)
	threats = append(threats, sa.analyzeElevationOfPrivilege(component)...)

	sa.logger.WithFields(logrus.Fields{
		"component_id":   component.ComponentID,
		"threats_found":  len(threats),
		"timestamp":      time.Now().UTC(),
	}).Info("STRIDE analysis completed")

	return threats
}

func (sa *STRIDEAnalysis) analyzeSpoofing(component Component) []Threat {
	var threats []Threat

	if component.ComponentType == ElementTypeProcess {
		authenticates := component.SecurityProperties["authenticates_users"].(bool)
		if !authenticates {
			threats = append(threats, Threat{
				ThreatID:    uuid.New().String(),
				ComponentID: component.ComponentID,
				Category:    STRIDECategorySpoofing,
				ThreatName:  "Identity Spoofing",
				Description: "Attacker impersonates legitimate user/service",
				Severity:    "high",
				Mitigations: []string{
					"Implement multi-factor authentication (MFA)",
					"Use mutual TLS for service-to-service auth",
					"Token-based authentication (JWT)",
				},
			})
		}
	}

	return threats
}

func (sa *STRIDEAnalysis) analyzeTampering(component Component) []Threat {
	var threats []Threat

	if component.ComponentType == ElementTypeDataStore {
		accessControlled := component.SecurityProperties["access_controlled"].(bool)
		if !accessControlled {
			threats = append(threats, Threat{
				ThreatID:    uuid.New().String(),
				ComponentID: component.ComponentID,
				Category:    STRIDECategoryTampering,
				ThreatName:  "Data Tampering",
				Description: "Unauthorized modification of stored data",
				Severity:    "critical",
				Mitigations: []string{
					"Implement access control lists (ACLs)",
					"Database triggers for integrity checks",
					"Digital signatures for critical data",
				},
			})
		}
	}

	return threats
}

func (sa *STRIDEAnalysis) analyzeRepudiation(component Component) []Threat {
	var threats []Threat

	if component.ComponentType == ElementTypeProcess {
		logsActivity := component.SecurityProperties["logs_activity"].(bool)
		if !logsActivity {
			threats = append(threats, Threat{
				ThreatID:    uuid.New().String(),
				ComponentID: component.ComponentID,
				Category:    STRIDECategoryRepudiation,
				ThreatName:  "Action Repudiation",
				Description: "User denies performing action without proof",
				Severity:    "medium",
				Mitigations: []string{
					"Comprehensive audit logging",
					"Tamper-proof log storage",
					"Digital signatures for transactions",
				},
			})
		}
	}

	return threats
}

func (sa *STRIDEAnalysis) analyzeInformationDisclosure(component Component) []Threat {
	var threats []Threat

	if component.ComponentType == ElementTypeDataStore {
		encrypted := component.SecurityProperties["encrypted_at_rest"].(bool)
		classification := component.SecurityProperties["data_classification"].(string)

		if !encrypted && (classification == "confidential" || classification == "restricted") {
			threats = append(threats, Threat{
				ThreatID:    uuid.New().String(),
				ComponentID: component.ComponentID,
				Category:    STRIDECategoryInformationDisclosure,
				ThreatName:  "Data Exposure",
				Description: "Sensitive data exposed through unauthorized access",
				Severity:    "critical",
				Mitigations: []string{
					"Encrypt data at rest (AES-256)",
					"Data loss prevention (DLP)",
					"Least privilege access control",
				},
			})
		}
	}

	return threats
}

func (sa *STRIDEAnalysis) analyzeDenialOfService(component Component) []Threat {
	return []Threat{
		{
			ThreatID:    uuid.New().String(),
			ComponentID: component.ComponentID,
			Category:    STRIDECategoryDenialOfService,
			ThreatName:  "Resource Exhaustion",
			Description: "Attacker overwhelms system resources",
			Severity:    "high",
			Mitigations: []string{
				"Rate limiting and throttling",
				"Resource quotas and circuit breakers",
				"Auto-scaling infrastructure",
			},
		},
	}
}

func (sa *STRIDEAnalysis) analyzeElevationOfPrivilege(component Component) []Threat {
	var threats []Threat

	if component.ComponentType == ElementTypeProcess {
		runsAs := component.SecurityProperties["runs_as"].(string)
		if runsAs == "root" || runsAs == "administrator" {
			threats = append(threats, Threat{
				ThreatID:    uuid.New().String(),
				ComponentID: component.ComponentID,
				Category:    STRIDECategoryElevationOfPrivilege,
				ThreatName:  "Privilege Escalation",
				Description: "Attacker gains elevated privileges",
				Severity:    "critical",
				Mitigations: []string{
					"Run with least privilege",
					"Role-based access control (RBAC)",
					"Input validation to prevent injection",
				},
			})
		}
	}

	return threats
}
```

---

## Attack Tree Analysis

```go
package threatmodeling

type AttackNode struct {
	NodeID      string
	AttackGoal  string
	Description string
	AttackType  string // "AND" or "OR"
	Probability float64
	Cost        float64
	Children    []*AttackNode
}

type AttackTreeAnalysis struct {
	logger *logrus.Logger
}

func NewAttackTreeAnalysis(logger *logrus.Logger) *AttackTreeAnalysis {
	return &AttackTreeAnalysis{logger: logger}
}

func (ata *AttackTreeAnalysis) BuildAttackTree() *AttackNode {
	root := &AttackNode{
		NodeID:      uuid.New().String(),
		AttackGoal:  "Compromise System",
		Description: "Attacker gains unauthorized access",
		AttackType:  "OR",
		Children:    []*AttackNode{},
	}

	// Path 1: Exploit application vulnerability
	exploitApp := &AttackNode{
		NodeID:      uuid.New().String(),
		AttackGoal:  "Exploit Application Vulnerability",
		Description: "Find and exploit weakness",
		AttackType:  "AND",
		Probability: 0.3,
		Cost:        5000.0,
		Children:    []*AttackNode{},
	}

	findVuln := &AttackNode{
		NodeID:      uuid.New().String(),
		AttackGoal:  "Find Vulnerability",
		Description: "Discover exploitable weakness",
		AttackType:  "OR",
		Probability: 0.6,
		Cost:        1000.0,
		Children:    []*AttackNode{},
	}

	exploitApp.Children = append(exploitApp.Children, findVuln)
	root.Children = append(root.Children, exploitApp)

	// Path 2: Social engineering
	socialEng := &AttackNode{
		NodeID:      uuid.New().String(),
		AttackGoal:  "Social Engineering",
		Description: "Manipulate users",
		AttackType:  "OR",
		Probability: 0.4,
		Cost:        2000.0,
		Children:    []*AttackNode{},
	}

	root.Children = append(root.Children, socialEng)

	ata.logger.WithFields(logrus.Fields{
		"root_goal": root.AttackGoal,
		"timestamp": time.Now().UTC(),
	}).Info("Attack tree built")

	return root
}

func (ata *AttackTreeAnalysis) CalculateAttackProbability(node *AttackNode) float64 {
	if len(node.Children) == 0 {
		return node.Probability
	}

	if node.AttackType == "AND" {
		// All children must succeed
		prob := 1.0
		for _, child := range node.Children {
			prob *= ata.CalculateAttackProbability(child)
		}
		return prob
	}

	// OR: At least one child must succeed
	failureProb := 1.0
	for _, child := range node.Children {
		failureProb *= (1.0 - ata.CalculateAttackProbability(child))
	}
	return 1.0 - failureProb
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
