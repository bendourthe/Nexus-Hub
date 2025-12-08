# Governance Policies

**Establish organization-wide security policies and access controls**

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)

---

## Overview

This sub-phase provides comprehensive templates for establishing, documenting, and maintaining organization-wide security policies and access control frameworks following the **Least Privilege** principle.

### Available Templates

1. **Security Policies** - Comprehensive security policy documentation, control frameworks
2. **Access Control** - RBAC implementation, least privilege, zero-trust architecture

### The Least Privilege Principle

**Definition**: Ensures agents and users receive only the minimum permissions required for their role. Implemented through encryption, authentication, and granular access controls.

**Best Practice**: Least privilege access with zero-trust security model (never trust, always verify).

**Key Techniques**:
- **Authentication**: OAuth 2.0, SSO (SAML, OIDC), multi-factor authentication, service principals, API keys
- **Secrets Management**: Key vaults, credential rotation, token management
- **Access Control**: Role-based access control (RBAC), group permissions, attribute-based access
- **Data Protection**: TLS/SSL, encryption at rest, key management, data masking, tokenization
- **Network Security**: Private networks, firewalls, endpoint security

**Checklist**: ✅ Are all your data sources accessible only to authorized agents and users?

---

## Quick Start

### Step 1: Assess Current Policy State

**Questions to Ask**:
- Do you have documented security policies?
- Are policies approved by leadership?
- Do employees acknowledge policies?
- Are policies reviewed regularly?
- Are policies enforced technically (not just documented)?

**Common Gap**: Policies exist but aren't enforced through code/configurations.

### Step 2: Choose Your Template

| Language | Security Policies | Access Control |
|----------|-------------------|----------------|
| **Python** | [View](./python_security_policies.md) | [View](./python_access_control.md) |
| **JavaScript** | [View](./javascript_security_policies.md) | [View](./javascript_access_control.md) |
| **Java** | [View](./java_security_policies.md) | [View](./java_access_control.md) |
| **C#** | [View](./csharp_security_policies.md) | [View](./csharp_access_control.md) |
| **Go** | [View](./go_security_policies.md) | [View](./go_access_control.md) |
| **C** | [View](./c_security_policies.md) | [View](./c_access_control.md) |
| **C++** | [View](./cpp_security_policies.md) | [View](./cpp_access_control.md) |

### Step 3: Follow Policy Development Lifecycle

1. **Draft**: Create policy based on frameworks (SOC 2, ISO 27001)
2. **Review**: Legal, HR, Security, Engineering review
3. **Approve**: Executive leadership sign-off
4. **Communicate**: All-hands announcement, training
5. **Acknowledge**: Employee policy acknowledgment
6. **Enforce**: Technical controls implementing policy
7. **Audit**: Regular compliance checks
8. **Update**: Annual review, update as needed

---

## Template Deep Dives

### Security Policies Templates

**Purpose**: Document organization-wide security standards and requirements.

**Included Policies**:
1. **Information Security Policy** (Master Policy)
   - Scope and objectives
   - Roles and responsibilities
   - Asset management
   - Acceptable use
   - Incident response
   - Compliance requirements

2. **Access Control Policy**
   - User provisioning/deprovisioning
   - Password requirements
   - MFA enforcement
   - Privileged access management
   - Access review procedures

3. **Data Classification and Handling Policy**
   - Classification levels (Public, Internal, Confidential, Restricted)
   - Handling requirements per classification
   - Encryption requirements
   - Data retention and disposal

4. **Acceptable Use Policy**
   - Permitted uses of company resources
   - Prohibited activities
   - Monitoring and privacy
   - Consequences of violations

5. **Change Management Policy**
   - Change approval workflows
   - Testing requirements
   - Rollback procedures
   - Emergency changes

6. **Vendor Management Policy**
   - Vendor risk assessment
   - Security requirements in contracts
   - Ongoing vendor monitoring
   - Data processing agreements

7. **Business Continuity and Disaster Recovery**
   - RTO/RPO definitions
   - Backup procedures
   - Failover processes
   - DR testing schedule

8. **AI/ML Governance Policy** (if applicable)
   - Model development lifecycle
   - Bias testing requirements
   - Explainability standards
   - Model monitoring and retraining

**Code Examples Include**:
- Policy-as-code enforcement (Open Policy Agent)
- Automated policy compliance checking
- Policy acknowledgment tracking systems
- Violation detection and alerting

**Time Investment**: 4-5 hours per language

**Use Cases**:
- SOC 2 CC1 (Control Environment)
- SOC 2 CC2 (Communication and Information)
- ISO 27001 Organizational Controls (37 controls)
- Compliance documentation for audits

### Access Control Templates

**Purpose**: Implement technical controls enforcing least privilege access.

**Implementation Patterns**:

1. **Role-Based Access Control (RBAC)**
   - Define organizational roles
   - Map permissions to roles
   - Assign users to roles
   - Enforce through code

2. **Attribute-Based Access Control (ABAC)**
   - Define attributes (user, resource, environment)
   - Policy rules based on attributes
   - Dynamic access decisions

3. **Zero-Trust Architecture**
   - Never trust, always verify
   - Verify explicitly (authenticate + authorize every request)
   - Use least privilege
   - Assume breach (monitor everything)

4. **Privileged Access Management (PAM)**
   - Separate privileged accounts
   - Just-in-time access elevation
   - Session recording
   - Access reviews

**Code Examples Include**:
- RBAC implementation (decorator patterns, middleware)
- JWT-based authentication
- API key management with rotation
- Service principal authentication
- Access control lists (ACLs)
- Permission inheritance hierarchies

**Time Investment**: 4-5 hours per language

**Use Cases**:
- SOC 2 CC6.1 (Logical access controls)
- SOC 2 CC6.2 (Authentication and identification)
- SOC 2 CC6.8 (Segregation of duties)
- ISO 27001 Control 5.15 (Access control)

---

## Policy Templates Included

### Information Security Policy Template

```markdown
# Information Security Policy

**Version**: 1.0
**Effective Date**: [Date]
**Approved By**: [CEO/CISO]
**Review Cycle**: Annual

## 1. Purpose

This policy establishes the organization's commitment to protecting information assets
from unauthorized access, disclosure, modification, or destruction.

## 2. Scope

This policy applies to:
- All employees, contractors, and third parties
- All information systems and data
- All locations (office, remote, cloud)

## 3. Roles and Responsibilities

### Chief Information Security Officer (CISO)
- Oversees implementation of security program
- Reports to executive leadership
- Approves security policies

### Security Team
- Implements security controls
- Monitors security events
- Responds to incidents

### System Owners
- Responsible for security of their systems
- Conduct access reviews
- Report security concerns

### All Users
- Follow security policies
- Report security incidents
- Complete security training

## 4. Asset Management

### Classification
- **Public**: No harm if disclosed
- **Internal**: Moderate harm if disclosed
- **Confidential**: Significant harm if disclosed
- **Restricted**: Severe harm if disclosed (PII, trade secrets)

### Handling Requirements
[See Data Classification Policy]

## 5. Access Control

- Least privilege principle enforced
- Multi-factor authentication required for:
  - Administrative access
  - Remote access
  - Access to confidential/restricted data
- Access reviews conducted quarterly
- Access revoked within 24 hours of termination

## 6. Acceptable Use

### Permitted Uses
- Business-related activities
- Incidental personal use (minimal)

### Prohibited Activities
- Unauthorized access attempts
- Installing unapproved software
- Sharing credentials
- Circumventing security controls
- Downloading illegal content

## 7. Security Awareness

- Annual security training required
- Phishing simulation program
- Incident reporting procedures communicated

## 8. Incident Response

- Report incidents to security@company.com
- Incident response plan maintained
- Post-incident reviews conducted

## 9. Compliance

This policy supports compliance with:
- SOC 2 Type II
- ISO 27001
- GDPR / CCPA (as applicable)
- PCI-DSS (if applicable)

## 10. Policy Violations

Violations may result in:
- Retraining
- Performance review
- Suspension
- Termination
- Legal action

## 11. Policy Review

This policy is reviewed annually and updated as needed.

---

**I acknowledge that I have read, understood, and agree to comply with this policy.**

Employee Signature: _______________ Date: _______________
```

### Access Control Policy Template

```markdown
# Access Control Policy

**Version**: 1.0
**Effective Date**: [Date]
**Approved By**: [CISO]
**Review Cycle**: Annual

## 1. Purpose

Ensure information systems and data are accessed only by authorized individuals.

## 2. User Provisioning

### New User Access
- Manager approval required
- Access request ticket created
- Least privilege principle applied
- Access granted within 1 business day

### Access Modification
- Manager approval for additional access
- Review existing access before granting new
- Document business justification

### User Deprovisioning
- Access revoked within 4 hours of termination notice
- Transfer of data/responsibilities documented
- Return of company assets verified

## 3. Authentication Requirements

### Password Policy
- Minimum 12 characters
- Complexity requirements: uppercase, lowercase, number, special character
- No password reuse (last 10 passwords)
- 90-day expiration
- Account lockout after 5 failed attempts

### Multi-Factor Authentication (MFA)
Required for:
- All administrative accounts
- Remote access (VPN)
- Access to systems containing confidential/restricted data
- Cloud services (email, file sharing, etc.)

MFA Methods:
- Authenticator app (preferred)
- Hardware token
- SMS (least preferred, security limitations)

## 4. Authorization (RBAC)

### Standard Roles

**User** (Standard Employee)
- Access to general systems (email, intranet, file shares)
- No administrative privileges
- Data access on need-to-know basis

**Developer**
- Access to development environments
- Read-only access to staging
- No production access (except approved deployments)
- Code review required for production changes

**Administrator** (System Admin)
- Full access to systems
- Elevated privileges
- Additional background check required
- All actions logged and audited

**Auditor** (Read-Only)
- Read-only access for compliance audits
- No modification capabilities
- Segregation of duties (cannot be admin)

### Custom Roles
- Defined based on business need
- Approved by Security team
- Documented with permissions matrix

## 5. Privileged Access Management

### Privileged Accounts
- Separate from standard accounts
- Named accounts (no shared "admin")
- Additional MFA requirements
- Session recording
- Just-in-time access (approve per session)

### Access Reviews
- Quarterly review of all access
- Focus on privileged accounts
- Certification by managers
- Automatic revocation if not certified

## 6. API Keys and Service Accounts

### API Key Management
- Generated through approved process
- Stored in secrets vault (never hardcoded)
- Rotated every 90 days
- Scoped to minimum required permissions
- Revoked immediately if compromised

### Service Principals
- Dedicated identities for applications
- No shared credentials
- Certificate-based authentication (preferred)
- Logged and monitored like user accounts

## 7. Enforcement

Technical controls enforce this policy:
- Identity management system
- MFA solution
- RBAC implementation in applications
- Secrets management platform
- Access logging and monitoring

## 8. Monitoring and Auditing

- All access attempts logged
- Failed authentication attempts monitored
- Privileged actions audited
- Anomalous activity alerts
- Quarterly access recertification

## 9. Policy Violations

Violations include:
- Sharing credentials
- Circumventing MFA
- Unauthorized access attempts
- Not reporting compromised credentials

Consequences: [See Information Security Policy]

---

**I acknowledge that I have read, understood, and agree to comply with this policy.**

Employee Signature: _______________ Date: _______________
```

---

## Code Implementation Examples

### Policy-as-Code (Open Policy Agent)

```python
# Example: Enforce access control policy using OPA
from opa_client.opa import OPA

class PolicyEnforcement:
    """Enforce policies using Open Policy Agent."""

    def __init__(self, opa_url="http://localhost:8181"):
        self.client = OPA(host=opa_url)

    def check_access(self, user, resource, action):
        """
        Check if user can perform action on resource.

        Policy evaluated by OPA based on RBAC rules.
        """
        input_data = {
            "user": {
                "id": user.id,
                "role": user.role,
                "attributes": user.attributes
            },
            "resource": {
                "id": resource.id,
                "classification": resource.classification
            },
            "action": action
        }

        result = self.client.check_permission(
            input_data=input_data,
            policy_name="access_control"
        )

        # Audit log
        logger.info("Access control check", extra={
            "user_id": user.id,
            "resource": resource.id,
            "action": action,
            "allowed": result["allow"],
            "policy_version": result.get("policy_version")
        })

        return result["allow"]
```

### Policy Acknowledgment Tracking

```python
# Track employee policy acknowledgments
from datetime import datetime

class PolicyAcknowledgment:
    """Track and enforce policy acknowledgments."""

    def require_acknowledgment(self, user, policy_name):
        """Check if user has acknowledged required policy."""
        acknowledgment = db.policy_acknowledgments.find_one({
            "user_id": user.id,
            "policy_name": policy_name,
            "policy_version": get_current_policy_version(policy_name)
        })

        if not acknowledgment:
            raise PolicyNotAcknowledged(
                f"User must acknowledge {policy_name} before proceeding"
            )

        # Check if acknowledgment is recent (annual requirement)
        if acknowledgment["acknowledged_date"] < one_year_ago():
            raise PolicyAcknowledgmentExpired(
                f"{policy_name} acknowledgment expired, re-acknowledgment required"
            )

        return True

    def record_acknowledgment(self, user, policy_name, signature):
        """Record policy acknowledgment with audit trail."""
        db.policy_acknowledgments.insert_one({
            "user_id": user.id,
            "policy_name": policy_name,
            "policy_version": get_current_policy_version(policy_name),
            "acknowledged_date": datetime.utcnow(),
            "signature": signature,
            "ip_address": get_request_ip()
        })

        logger.info("Policy acknowledged", extra={
            "user_id": user.id,
            "policy": policy_name,
            "timestamp": datetime.utcnow().isoformat()
        })
```

---

## Integration with Compliance Frameworks

### SOC 2 Integration

Governance policies directly support:
- **CC1.1-CC1.5**: Control environment (policies establish tone from top)
- **CC2.1-CC2.3**: Communication (policies communicate requirements)
- **CC6.1**: Logical access controls (access control policy)
- **CC6.2**: Authentication (MFA requirements)
- **CC6.8**: Segregation of duties (role definitions)

Policies serve as evidence of "tone from the top" and documented controls.

### ISO 27001 Integration

Maps to Organizational Controls:
- **Control 5.1**: Policies for information security
- **Control 5.2**: Information security roles and responsibilities
- **Control 5.15**: Access control
- **Control 5.16**: Identity management
- **Control 5.18**: Access rights

Policies form the foundation of your ISMS (Information Security Management System).

### GDPR/CCPA Integration

Privacy-related policies:
- Data classification (identifies personal data)
- Data retention and disposal
- Access control (protects personal data)
- Vendor management (data processing agreements)

---

## Success Criteria

### Policy Documentation Complete

- [ ] All required policies written
- [ ] Policies reviewed by legal, HR, security
- [ ] Executive leadership approval obtained
- [ ] Policies published to employee portal
- [ ] Policy acknowledgment system operational

### Policy Communication Complete

- [ ] All-hands announcement conducted
- [ ] Security training includes policy overview
- [ ] New hire onboarding includes policies
- [ ] Policy acknowledgments collected (100% of employees)
- [ ] Managers trained on enforcement

### Technical Enforcement Implemented

- [ ] Access controls enforce least privilege
- [ ] MFA required per policy
- [ ] Password requirements technically enforced
- [ ] Automated access reviews configured
- [ ] Policy violations trigger alerts

### Compliance Evidence Collected

- [ ] Policy approval signatures (leadership)
- [ ] Employee acknowledgment records
- [ ] Access control configuration screenshots
- [ ] Access review reports (quarterly)
- [ ] Policy training completion records

---

## Common Pitfalls

### ❌ Policy Shelf-ware

**Problem**: Policies documented but not enforced, not communicated, employees unaware.

**Solution**: Active communication, training, technical enforcement, regular audits.

### ❌ Copy-Paste Policies

**Problem**: Generic policies copied from templates without customization.

**Solution**: Customize to reflect actual practices. Auditors will test alignment.

### ❌ Policy Overload

**Problem**: Too many policies, too complex, employees overwhelmed.

**Solution**: Start with essential policies. Consolidate where possible. Keep language clear.

### ❌ No Technical Enforcement

**Problem**: Policies exist but not technically enforced (honor system).

**Solution**: Policy-as-code, automated controls, monitoring and alerting.

---

## Resources

### Policy Frameworks

- [SANS Security Policy Templates](https://www.sans.org/information-security-policy/) - Free policy templates
- [ISO 27001 Policy Templates](https://www.iso27001security.com/html/toolkit.html) - ISO-aligned policies
- [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) - Security control catalog

### Tools

- **Policy Management**: PolicyTech, LogicManager, Qualys Policy Compliance
- **Policy-as-Code**: Open Policy Agent (OPA), HashiCorp Sentinel
- **Access Control**: Okta, Azure AD, Auth0, AWS IAM
- **Secrets Management**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault

---

## Time Estimates

| Template | Research | Writing | Review | Total |
|----------|----------|---------|--------|-------|
| Security Policies | 1 hour | 2-3 hours | 1 hour | 4-5 hours |
| Access Control | 1 hour | 2-3 hours | 1 hour | 4-5 hours |

**Total per language**: 8-10 hours for both templates

---

[← Back to Compliance & Governance](../README.md) | [← Back to Main README](../../../README.md)
