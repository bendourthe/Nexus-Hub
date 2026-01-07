---
template_id: compliance_governance_security_policies_python
template_name: Security Policies - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/python_soc2_compliance.md
  - compliance_frameworks/python_iso27001_implementation.md
related_templates:
  - governance_policies/python_access_control.md
  - privacy_protection/python_gdpr_compliance.md
  - incident_response/python_incident_response_plan.md
tools:
  - opa (open policy agent)
  - policykit (policy enforcement)
tags:
  - security-policies
  - policy-as-code
  - least-privilege
  - governance
  - python
---

# Security Policies - Python

**🔒 Pillar 3: Security (Least Privilege)**

Implement organization-wide security policies with policy-as-code enforcement

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What are Security Policies?

**Security Policies** are formal statements defining how an organization protects its information assets. They establish the rules, practices, and procedures for security.

**Key Principle**: "Tone from the top" - Leadership commitment to security

### Policy vs. Standards vs. Procedures

- **Policy** - High-level statement (WHAT) - "Data must be encrypted"
- **Standard** - Specific requirements (HOW MUCH) - "AES-256 encryption required"
- **Procedure** - Step-by-step instructions (HOW) - "Use cryptography library..."

### Framework Requirements

**ISO 27001 Control 5.1**: Policies for information security
- Management direction and support
- Published and communicated
- Reviewed at planned intervals

**SOC 2 CC1.1**: Control environment
- Demonstrates commitment to integrity and ethical values
- Board oversight
- Establishes structure, authority, responsibility

---

## Core Security Policies

### 1. Information Security Policy (Master Policy)

**Purpose**: Overarching security policy establishing organization's commitment

**Key Elements**:
- Information security objectives
- Legal and regulatory compliance
- Security roles and responsibilities
- Risk management approach
- Consequences of policy violations

### 2. Acceptable Use Policy (AUP)

**Purpose**: Define appropriate use of organization resources

**Key Elements**:
- Permitted uses of systems and data
- Prohibited activities
- Personal use guidelines
- Monitoring and privacy expectations
- Consequences of misuse

### 3. Access Control Policy

**Purpose**: Control who can access what

**Key Elements**:
- User provisioning and deprovisioning
- Authentication requirements (MFA)
- Authorization model (RBAC)
- Privileged access management
- Access reviews

### 4. Data Classification and Handling Policy

**Purpose**: Classify and protect data based on sensitivity

**Key Elements**:
- Classification levels (Public, Internal, Confidential, Restricted)
- Handling requirements per classification
- Encryption requirements
- Data retention and disposal

### 5. Incident Response Policy

**Purpose**: Respond to security incidents

**Key Elements**:
- Incident definition and classification
- Reporting procedures
- Response team roles
- Investigation and remediation
- Post-incident review

---

## Implementation Roadmap

### Phase 1: Policy Development (Week 1-2)

**Deliverables**:
1. Draft policies based on frameworks
2. Stakeholder review (Legal, HR, Security)
3. Executive approval
4. Policy publication

**Code**: See [Policy Management](#policy-management-implementation)

### Phase 2: Policy Communication (Week 3)

**Deliverables**:
1. Employee training
2. Policy acknowledgment system
3. Policy portal
4. Communication campaign

**Code**: See [Policy Acknowledgment](#policy-acknowledgment-implementation)

### Phase 3: Policy Enforcement (Week 4)

**Deliverables**:
1. Policy-as-code implementation
2. Automated compliance checking
3. Violation detection and alerting
4. Enforcement workflows

**Code**: See [Policy-as-Code](#policy-as-code-implementation)

### Phase 4: Policy Maintenance (Ongoing)

**Deliverables**:
1. Annual policy review
2. Policy updates as needed
3. Continuous monitoring
4. Audit evidence collection

---

## Policy Management Implementation

### Policy Lifecycle Management

**ISO 27001 Control 5.1**: Policy lifecycle

**Implementation**:

```python
# Policy lifecycle management
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PolicyStatus(Enum):
    """Policy lifecycle status."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PolicyType(Enum):
    """Types of security policies."""
    MASTER_POLICY = "master_policy"
    ACCEPTABLE_USE = "acceptable_use"
    ACCESS_CONTROL = "access_control"
    DATA_CLASSIFICATION = "data_classification"
    INCIDENT_RESPONSE = "incident_response"
    CHANGE_MANAGEMENT = "change_management"
    VENDOR_MANAGEMENT = "vendor_management"
    AI_GOVERNANCE = "ai_governance"

class PolicyManagement:
    """
    Manage security policy lifecycle.

    Security: Least Privilege
    Compliance: ISO 27001 Control 5.1, SOC 2 CC1.1
    """

    def create_policy(
        self,
        policy_name: str,
        policy_type: PolicyType,
        content: str,
        owner: str,
        review_frequency_months: int = 12
    ) -> str:
        """
        Create new security policy.

        Policy lifecycle: Draft → Review → Approved → Published
        """
        policy_id = generate_uuid()

        policy = {
            "policy_id": policy_id,
            "policy_name": policy_name,
            "policy_type": policy_type.value,
            "version": "1.0",
            "content": content,
            "owner": owner,
            "status": PolicyStatus.DRAFT.value,
            "created_date": datetime.utcnow(),
            "review_frequency_months": review_frequency_months,
            "next_review_date": datetime.utcnow() + timedelta(days=365),

            # Approval tracking
            "approvers_required": ["legal", "security", "executive"],
            "approvals": [],
            "approval_date": None,

            # Publication tracking
            "published_date": None,
            "effective_date": None,

            # Acknowledgment tracking
            "acknowledgments_required": True,
            "acknowledgment_count": 0
        }

        db.policies.insert_one(policy)

        logger.info("Policy created", extra={
            "event": "policy_created",
            "policy_id": policy_id,
            "policy_name": policy_name,
            "status": PolicyStatus.DRAFT.value
        })

        return policy_id

    def submit_for_review(self, policy_id: str, reviewers: List[str]) -> Dict:
        """
        Submit policy for stakeholder review.

        Reviewers: Legal, HR, Security, Compliance
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        if policy["status"] != PolicyStatus.DRAFT.value:
            raise ValueError(f"Policy must be in DRAFT status, currently {policy['status']}")

        # Update status
        db.policies.update_one(
            {"policy_id": policy_id},
            {"$set": {
                "status": PolicyStatus.REVIEW.value,
                "reviewers": reviewers,
                "review_submitted_date": datetime.utcnow()
            }}
        )

        # Notify reviewers
        for reviewer in reviewers:
            self._notify_reviewer(policy_id, reviewer)

        logger.info("Policy submitted for review", extra={
            "event": "policy_review_submitted",
            "policy_id": policy_id,
            "reviewers": reviewers
        })

        return {"status": "review", "reviewers": reviewers}

    def approve_policy(self, policy_id: str, approver: str, comments: str = None) -> Dict:
        """
        Approve policy.

        Requires approvals from all required approvers before publishing.
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        if policy["status"] not in [PolicyStatus.REVIEW.value, PolicyStatus.APPROVED.value]:
            raise ValueError(f"Policy must be in REVIEW status")

        # Record approval
        approval = {
            "approver": approver,
            "approval_date": datetime.utcnow(),
            "comments": comments
        }

        db.policies.update_one(
            {"policy_id": policy_id},
            {"$push": {"approvals": approval}}
        )

        # Check if all approvals received
        updated_policy = db.policies.find_one({"policy_id": policy_id})
        approvers_received = [a["approver"] for a in updated_policy["approvals"]]
        all_approved = all(req in approvers_received for req in policy["approvers_required"])

        if all_approved:
            # Move to approved status
            db.policies.update_one(
                {"policy_id": policy_id},
                {"$set": {
                    "status": PolicyStatus.APPROVED.value,
                    "approval_date": datetime.utcnow()
                }}
            )

            logger.warning("Policy fully approved", extra={
                "event": "policy_approved",
                "policy_id": policy_id
            })

            return {"status": "approved", "ready_to_publish": True}
        else:
            pending = [req for req in policy["approvers_required"] if req not in approvers_received]
            return {"status": "pending_approvals", "pending_approvers": pending}

    def publish_policy(self, policy_id: str, effective_date: datetime = None) -> Dict:
        """
        Publish policy to organization.

        Makes policy active and enforceable.
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        if policy["status"] != PolicyStatus.APPROVED.value:
            raise ValueError("Policy must be APPROVED before publishing")

        if effective_date is None:
            effective_date = datetime.utcnow()

        # Publish policy
        db.policies.update_one(
            {"policy_id": policy_id},
            {"$set": {
                "status": PolicyStatus.PUBLISHED.value,
                "published_date": datetime.utcnow(),
                "effective_date": effective_date
            }}
        )

        # Notify all employees
        self._notify_all_employees(policy_id)

        # Reset acknowledgment count
        db.policies.update_one(
            {"policy_id": policy_id},
            {"$set": {"acknowledgment_count": 0}}
        )

        logger.warning("Policy published", extra={
            "event": "policy_published",
            "policy_id": policy_id,
            "effective_date": effective_date.isoformat()
        })

        return {
            "status": "published",
            "effective_date": effective_date.isoformat()
        }

    def review_policy(self, policy_id: str) -> Dict:
        """
        Periodic policy review (annual or as needed).

        ISO 27001 Control 5.1: Reviewed at planned intervals
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        review = {
            "review_id": generate_uuid(),
            "policy_id": policy_id,
            "review_date": datetime.utcnow(),
            "reviewer": get_current_user(),
            "changes_required": False,
            "review_notes": ""
        }

        # Check if policy needs updates
        if datetime.utcnow() >= policy["next_review_date"]:
            review["changes_required"] = True
            review["review_notes"] = "Scheduled annual review required"

        db.policy_reviews.insert_one(review)

        # Update next review date
        db.policies.update_one(
            {"policy_id": policy_id},
            {"$set": {
                "last_review_date": datetime.utcnow(),
                "next_review_date": datetime.utcnow() + timedelta(days=policy["review_frequency_months"] * 30)
            }}
        )

        logger.info("Policy reviewed", extra={
            "event": "policy_reviewed",
            "policy_id": policy_id,
            "changes_required": review["changes_required"]
        })

        return review
```

---

## Policy Acknowledgment Implementation

### Employee Policy Acknowledgment

**SOC 2 CC1.1**: Employees acknowledge policies

**Implementation**:

```python
# Policy acknowledgment tracking
class PolicyAcknowledgment:
    """
    Track employee policy acknowledgments.

    Security: Least Privilege
    Compliance: SOC 2 CC1.1, ISO 27001 Control 5.1
    """

    def require_acknowledgment(self, user_id: str, policy_id: str) -> bool:
        """
        Check if user must acknowledge policy.

        Returns True if acknowledgment required, False if already acknowledged.
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        if not policy["acknowledgments_required"]:
            return False

        # Check if user already acknowledged current version
        acknowledgment = db.policy_acknowledgments.find_one({
            "user_id": user_id,
            "policy_id": policy_id,
            "policy_version": policy["version"]
        })

        if acknowledgment:
            return False  # Already acknowledged

        logger.info("Policy acknowledgment required", extra={
            "user_id": user_id,
            "policy_id": policy_id
        })

        return True

    def record_acknowledgment(
        self,
        user_id: str,
        policy_id: str,
        signature: str,
        ip_address: str
    ) -> str:
        """
        Record policy acknowledgment.

        Burden of proof: Organization must demonstrate employees acknowledged.
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        acknowledgment = {
            "acknowledgment_id": generate_uuid(),
            "user_id": user_id,
            "policy_id": policy_id,
            "policy_version": policy["version"],
            "policy_name": policy["policy_name"],
            "acknowledged_date": datetime.utcnow(),
            "signature": signature,
            "ip_address": ip_address,
            "user_agent": get_request_user_agent()
        }

        db.policy_acknowledgments.insert_one(acknowledgment)

        # Increment acknowledgment count
        db.policies.update_one(
            {"policy_id": policy_id},
            {"$inc": {"acknowledgment_count": 1}}
        )

        logger.info("Policy acknowledged", extra={
            "event": "policy_acknowledged",
            "user_id": user_id,
            "policy_id": policy_id,
            "acknowledgment_id": acknowledgment["acknowledgment_id"]
        })

        return acknowledgment["acknowledgment_id"]

    def get_acknowledgment_status(self) -> Dict:
        """
        Get organization-wide acknowledgment status.

        For compliance reporting: "100% of employees acknowledged policies"
        """
        policies = list(db.policies.find({"status": PolicyStatus.PUBLISHED.value}))
        total_employees = db.users.count_documents({"status": "active"})

        status = {
            "total_employees": total_employees,
            "policies": []
        }

        for policy in policies:
            acknowledgment_rate = policy["acknowledgment_count"] / total_employees if total_employees > 0 else 0

            status["policies"].append({
                "policy_id": policy["policy_id"],
                "policy_name": policy["policy_name"],
                "acknowledgment_count": policy["acknowledgment_count"],
                "acknowledgment_rate": round(acknowledgment_rate * 100, 2),
                "compliant": acknowledgment_rate >= 0.95  # 95% threshold
            })

        return status

    def send_acknowledgment_reminder(self, policy_id: str):
        """
        Send reminder to employees who haven't acknowledged.

        Automated reminders increase compliance rate.
        """
        policy = db.policies.find_one({"policy_id": policy_id})

        # Get all active employees
        all_employees = list(db.users.find({"status": "active"}))

        # Find employees who haven't acknowledged
        for employee in all_employees:
            if self.require_acknowledgment(employee["user_id"], policy_id):
                self._send_reminder_email(employee, policy)

        logger.info("Acknowledgment reminders sent", extra={
            "policy_id": policy_id
        })
```

---

## Policy-as-Code Implementation

### Automated Policy Enforcement

**Purpose**: Enforce policies through code, not just documentation

**Implementation**:

```python
# Policy-as-code enforcement
class PolicyAsCode:
    """
    Enforce security policies through code.

    Security: Least Privilege
    Pattern: Policy-as-code (infrastructure-as-code for security)
    """

    def __init__(self):
        # In production: integrate with Open Policy Agent (OPA)
        self.policies = {}

    def register_policy(self, policy_name: str, policy_rules: Dict):
        """
        Register policy for automated enforcement.

        Example: Password policy, data retention policy, access control policy
        """
        self.policies[policy_name] = policy_rules

        logger.info("Policy registered for enforcement", extra={
            "policy_name": policy_name
        })

    def enforce_password_policy(self, password: str, user: Dict) -> Dict:
        """
        Enforce password policy.

        Policy requirements:
        - Minimum 12 characters
        - Complexity (uppercase, lowercase, number, special)
        - No password reuse (last 10)
        - 90-day expiration
        """
        password_policy = {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_number": True,
            "require_special": True,
            "password_history": 10,
            "max_age_days": 90
        }

        violations = []

        # Length check
        if len(password) < password_policy["min_length"]:
            violations.append(f"Password must be at least {password_policy['min_length']} characters")

        # Complexity checks
        import re
        if password_policy["require_uppercase"] and not re.search(r"[A-Z]", password):
            violations.append("Password must contain uppercase letter")
        if password_policy["require_lowercase"] and not re.search(r"[a-z]", password):
            violations.append("Password must contain lowercase letter")
        if password_policy["require_number"] and not re.search(r"\d", password):
            violations.append("Password must contain number")
        if password_policy["require_special"] and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            violations.append("Password must contain special character")

        # Password history check
        if self._is_password_reused(user["user_id"], password, password_policy["password_history"]):
            violations.append(f"Cannot reuse last {password_policy['password_history']} passwords")

        compliant = len(violations) == 0

        result = {
            "compliant": compliant,
            "violations": violations,
            "policy": "Password Policy v2.0"
        }

        if not compliant:
            logger.warning("Password policy violation", extra={
                "user_id": user["user_id"],
                "violations": violations
            })

        return result

    def enforce_data_retention_policy(self, data_type: str, data_age_days: int) -> bool:
        """
        Enforce data retention policy.

        Policy: Retain data only as long as necessary.
        """
        retention_policy = {
            "user_activity_logs": 90,      # 90 days
            "financial_records": 2555,     # 7 years
            "employment_records": 2190,    # 6 years
            "customer_data": 730,          # 2 years after last activity
            "audit_logs": 365              # 1 year
        }

        max_retention = retention_policy.get(data_type, 365)  # Default 1 year

        should_delete = data_age_days > max_retention

        if should_delete:
            logger.warning("Data retention policy requires deletion", extra={
                "data_type": data_type,
                "data_age_days": data_age_days,
                "max_retention_days": max_retention
            })

        return should_delete

    def enforce_access_control_policy(self, user: Dict, resource: str, action: str) -> bool:
        """
        Enforce access control policy (RBAC).

        Policy: Least privilege, role-based access control.
        """
        # Get user's role
        user_role = user.get("role", "user")

        # Access control matrix
        access_matrix = {
            "admin": {
                "database": ["read", "write", "delete"],
                "config": ["read", "write"],
                "users": ["read", "write", "delete"]
            },
            "developer": {
                "database": ["read"],
                "config": ["read"],
                "users": ["read"]
            },
            "user": {
                "database": ["read"],
                "config": [],
                "users": []
            }
        }

        allowed_actions = access_matrix.get(user_role, {}).get(resource, [])
        access_granted = action in allowed_actions

        logger.info("Access control policy enforced", extra={
            "user_id": user["user_id"],
            "role": user_role,
            "resource": resource,
            "action": action,
            "granted": access_granted
        })

        return access_granted

    def detect_policy_violations(self) -> List[Dict]:
        """
        Detect policy violations across organization.

        Continuous compliance monitoring.
        """
        violations = []

        # Check password expiration violations
        expired_passwords = db.users.find({
            "password_changed_date": {"$lt": ninety_days_ago()},
            "status": "active"
        })

        for user in expired_passwords:
            violations.append({
                "violation_type": "password_expired",
                "user_id": user["user_id"],
                "policy": "Password Policy",
                "description": "Password older than 90 days",
                "severity": "medium"
            })

        # Check data retention violations
        old_logs = db.activity_logs.find({
            "created_date": {"$lt": ninety_days_ago()}
        })

        if old_logs.count() > 0:
            violations.append({
                "violation_type": "data_retention",
                "policy": "Data Retention Policy",
                "description": f"{old_logs.count()} old activity logs should be deleted",
                "severity": "low"
            })

        # Check unacknowledged policies
        unacknowledged = PolicyAcknowledgment().get_acknowledgment_status()
        for policy_status in unacknowledged["policies"]:
            if not policy_status["compliant"]:
                violations.append({
                    "violation_type": "policy_not_acknowledged",
                    "policy": policy_status["policy_name"],
                    "description": f"Only {policy_status['acknowledgment_rate']}% acknowledged (need 95%)",
                    "severity": "high"
                })

        logger.warning("Policy violations detected", extra={
            "violations_count": len(violations)
        })

        return violations
```

---

## Policy Templates

### Information Security Policy Template

```markdown
# Information Security Policy

**Version**: 2.0
**Effective Date**: 2025-12-05
**Approved By**: CEO, CISO
**Review Cycle**: Annual

## 1. Purpose

This policy establishes [Organization]'s commitment to protecting information assets.

## 2. Scope

Applies to:
- All employees, contractors, third parties
- All information systems and data
- All locations (office, remote, cloud)

## 3. Information Security Objectives

- Protect confidentiality, integrity, availability of information
- Comply with legal, regulatory, contractual obligations
- Maintain customer trust
- Support business operations

## 4. Roles and Responsibilities

### CISO (Chief Information Security Officer)
- Oversees security program implementation
- Reports to executive leadership
- Approves security policies

### Security Team
- Implements security controls
- Monitors security events
- Responds to incidents

### All Employees
- Follow security policies
- Report security incidents
- Complete security training annually

## 5. Risk Management

- Risk assessments conducted annually
- Risks prioritized and treated
- Residual risks accepted by management

## 6. Access Control

- Least privilege principle enforced
- Multi-factor authentication required
- Access reviews conducted quarterly

## 7. Asset Management

Data classified as:
- **Public**: No harm if disclosed
- **Internal**: Moderate harm
- **Confidential**: Significant harm
- **Restricted**: Severe harm (PII, secrets)

## 8. Incident Response

- Report incidents to security@company.com
- Incident response plan maintained
- Post-incident reviews conducted

## 9. Compliance

Supports compliance with:
- SOC 2 Type II
- ISO 27001
- GDPR/CCPA

## 10. Policy Violations

May result in:
- Retraining
- Performance review
- Termination
- Legal action

## 11. Policy Review

Reviewed annually and updated as needed.

---

**I acknowledge that I have read, understood, and agree to comply with this policy.**

Employee Signature: _______________ Date: _______________
```

---

## Success Criteria

### Policy Development Complete

- [ ] All required policies documented
- [ ] Policies reviewed by stakeholders (Legal, HR, Security)
- [ ] Executive approval obtained
- [ ] Policies published to employee portal

### Policy Communication Complete

- [ ] All-hands announcement conducted
- [ ] Security training includes policy overview
- [ ] Policy acknowledgment system operational
- [ ] 95%+ of employees acknowledged policies

### Policy Enforcement Complete

- [ ] Policy-as-code implemented for key policies
- [ ] Automated compliance checking operational
- [ ] Violation detection and alerting configured
- [ ] Enforcement workflows documented

### Compliance Evidence

- [ ] Policy approval signatures collected
- [ ] Employee acknowledgment records maintained
- [ ] Policy version control established
- [ ] Annual review schedule defined

---

## Common Pitfalls

### ❌ Policy Shelf-ware

**Problem**: Policies documented but not enforced or communicated.

**Solution**: Active communication, training, technical enforcement, regular audits.

### ❌ Copy-Paste Policies

**Problem**: Generic policies that don't reflect actual practices.

**Solution**: Customize to your organization. Auditors will test alignment.

### ❌ No Technical Enforcement

**Problem**: Policies exist but not technically enforced (honor system).

**Solution**: Policy-as-code, automated controls, monitoring.

### ❌ Stale Policies

**Problem**: Policies never updated, become outdated.

**Solution**: Annual review minimum. Update when significant changes.

---

## Resources

### Policy Templates

- [SANS Security Policy Templates](https://www.sans.org/information-security-policy/)
- [ISO 27001 Policy Templates](https://www.iso27001security.com/)

### Policy-as-Code Tools

- **Open Policy Agent (OPA)** - Policy engine
- **HashiCorp Sentinel** - Policy-as-code framework
- **Cloud Custodian** - Cloud governance

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete security policy framework for Python
- Policy lifecycle management
- Policy acknowledgment tracking
- Policy-as-code enforcement
- Password policy enforcement
- Data retention policy enforcement
- Access control policy enforcement
- Violation detection
- Policy templates (Information Security, AUP, Access Control)

**Framework Coverage**:
- ISO 27001 Control 5.1 (Policies)
- SOC 2 CC1.1 (Control environment)
- Least Privilege principle

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
