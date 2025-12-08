---
template_id: compliance_governance_iso27001_python
template_name: ISO 27001:2022 Implementation - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - code_review/security_review/python_security_review.md
  - AI Skills: dependency-security-audit, licensing-compliance-check
related_templates:
  - compliance_frameworks/python_soc2_compliance.md
  - risk_management/python_risk_assessment.md
  - governance_policies/python_security_policies.md
  - incident_response/python_incident_response_plan.md
tools:
  - bandit (security scanner)
  - safety (dependency vulnerability scanner)
  - cryptography (encryption library)
  - python-jose (JWT handling)
  - pytest (testing framework)
tags:
  - iso27001
  - iso-27001-2022
  - compliance
  - information-security
  - isms
  - python
---

# ISO 27001:2022 Implementation - Python

**Establish comprehensive Information Security Management System (ISMS) with 114 controls**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is ISO 27001:2022?

ISO/IEC 27001:2022 is the international standard for establishing, implementing, maintaining, and continually improving an **Information Security Management System (ISMS)**. It provides a systematic approach to managing sensitive company information.

**Latest Version**: ISO 27001:2022 (published October 2022, organizations must transition by October 2025)

**Key Changes in 2022**:
- Restructured from 14 to 4 control themes
- 114 controls (vs. 114 in 2013, but reorganized)
- New controls: Threat intelligence (5.7), Cloud security (5.23), Web filtering (8.23)
- Removed: Business continuity duplications

### Why Python Applications Need ISO 27001

- **Global Recognition**: Accepted worldwide, required by many enterprises
- **Systematic Approach**: ISMS provides comprehensive security framework
- **Competitive Advantage**: Certification demonstrates security maturity
- **Regulatory Compliance**: Supports GDPR, NIS2, and other regulations
- **Risk Management**: Structured approach to identifying and treating risks

### The ISMS (Information Security Management System)

ISO 27001 is about the **management system**, not just technical controls:

1. **Context**: Understand the organization, stakeholders, scope
2. **Leadership**: Top management commitment, policies, roles
3. **Planning**: Risk assessment, risk treatment, objectives
4. **Support**: Resources, competence, awareness, communication, documentation
5. **Operation**: Implement risk treatment, controls
6. **Performance Evaluation**: Monitor, measure, audit, review
7. **Improvement**: Nonconformities, corrective actions, continual improvement

---

## Control Structure (2022 Version)

### The 4 Control Themes (93 Controls + 11 Attribute-Based)

#### Theme 1: Organizational Controls (37 controls)

**Focus**: Policies, procedures, organizational structures

Key controls:
- 5.1: Policies for information security
- 5.7: **Threat intelligence** (NEW in 2022)
- 5.10: Acceptable use of information
- 5.15: Access control
- 5.23: **Information security for use of cloud services** (NEW)
- 5.33: Protection of records
- 5.34: Privacy and protection of PII

#### Theme 2: People Controls (8 controls)

**Focus**: Human resources security

Key controls:
- 6.1: Screening (background checks)
- 6.2: Terms and conditions of employment
- 6.3: Information security awareness, education, training
- 6.4: Disciplinary process
- 6.8: Information security event reporting

#### Theme 3: Physical Controls (14 controls)

**Focus**: Physical and environmental security

Key controls:
- 7.1: Physical security perimeters
- 7.2: Physical entry
- 7.4: Physical security monitoring
- 7.7: Clear desk and clear screen
- 7.13: Equipment maintenance

#### Theme 4: Technological Controls (34 controls)

**Focus**: Technical security controls (most relevant for Python applications)

Key controls:
- 8.1: User endpoint devices
- 8.2: Privileged access rights
- 8.3: Information access restriction
- 8.5: Secure authentication
- 8.9: Configuration management
- 8.10: Information deletion
- 8.16: Monitoring activities
- 8.23: **Web filtering** (NEW in 2022)
- 8.24: Use of cryptography
- 8.28: Secure coding
- 8.32: Change management

---

## Implementation Roadmap

### Phase 1: Gap Analysis (Weeks 1-2)

1. **Run Security Assessments**:
   ```bash
   # Security review
   Use: security_review/python_security_review.md

   # Dependency audit
   Use: dependency-security-audit skill

   # License compliance
   Use: licensing-compliance-check skill
   ```

2. **Document Current State**:
   - What security controls exist?
   - What policies are documented?
   - What risks have been identified?
   - What evidence is available?

3. **Identify Gaps**:
   - Compare against 114 controls
   - Prioritize by risk
   - Create implementation plan

### Phase 2: ISMS Design (Weeks 3-4)

4. **Define ISMS Scope**:
   - What systems/data are included?
   - What organizational units?
   - What locations?
   - Exclusions (with justification)?

5. **Information Security Policy**:
   - Executive commitment
   - Security objectives
   - Compliance obligations
   - Use [governance_policies](../governance_policies/python_security_policies.md)

6. **Risk Assessment Methodology**:
   - Risk identification criteria
   - Risk analysis approach (likelihood × impact)
   - Risk evaluation criteria (risk appetite)
   - Use [risk_management](../risk_management/python_risk_assessment.md)

### Phase 3: Implementation (Weeks 5-12)

7. **Implement Controls** (follow code examples below)
8. **Document Procedures**
9. **Train Personnel**
10. **Collect Evidence**

### Phase 4: Audit & Certification (Weeks 13-16)

11. **Internal Audit**
12. **Management Review**
13. **Stage 1 Audit** (documentation review by certification body)
14. **Stage 2 Audit** (on-site assessment)
15. **Certification** (3-year cycle, annual surveillance audits)

---

## Code-Level Implementation (Technological Controls)

### Control 8.2: Privileged Access Rights

**Requirement**: Restrict and control privileged access rights.

**Implementation**:

```python
# Privileged access management with just-in-time elevation
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PrivilegeLevel(Enum):
    STANDARD = "standard"
    ELEVATED = "elevated"
    ADMIN = "admin"

class PrivilegedAccessManager:
    """
    Manage privileged access with just-in-time elevation.

    ISO 27001 Control: 8.2 (Privileged access rights)

    Requirements:
    - Separate privileged accounts from standard
    - Time-limited elevated access
    - Approval workflow
    - Comprehensive logging
    """

    def request_privilege_elevation(
        self,
        user_id: str,
        requested_level: PrivilegeLevel,
        justification: str,
        duration_hours: int = 4
    ) -> dict:
        """
        Request temporary privilege elevation.

        Args:
            user_id: User requesting elevation
            requested_level: Privilege level requested
            justification: Business justification
            duration_hours: How long access needed (max 8 hours)

        Returns:
            Elevation request details
        """
        if duration_hours > 8:
            raise ValueError("Maximum elevation period is 8 hours")

        request_id = generate_uuid()
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        # Create elevation request
        db.privilege_requests.insert_one({
            "request_id": request_id,
            "user_id": user_id,
            "current_level": self._get_current_privilege(user_id),
            "requested_level": requested_level.value,
            "justification": justification,
            "requested_date": datetime.utcnow(),
            "expires_at": expires_at,
            "status": "pending_approval",
            "approver": None
        })

        # Auto-approve for elevated (require approval for admin)
        if requested_level == PrivilegeLevel.ELEVATED:
            self._auto_approve(request_id)
        else:
            # Admin requires manager approval
            self._notify_approver(user_id, request_id)

        logger.info("Privilege elevation requested", extra={
            "event": "privilege_elevation_request",
            "request_id": request_id,
            "user_id": user_id,
            "requested_level": requested_level.value,
            "duration_hours": duration_hours
        })

        return {
            "request_id": request_id,
            "status": "pending_approval" if requested_level == PrivilegeLevel.ADMIN else "approved",
            "expires_at": expires_at
        }

    def grant_privilege_elevation(self, request_id: str, approver_id: str):
        """
        Grant privilege elevation after approval.

        All actions logged for ISO 27001 audit trail.
        """
        request = db.privilege_requests.find_one({"request_id": request_id})

        if not request:
            raise ValueError("Request not found")

        if request["status"] != "pending_approval":
            raise ValueError("Request not in pending state")

        # Grant temporary privileges
        db.privilege_grants.insert_one({
            "request_id": request_id,
            "user_id": request["user_id"],
            "privilege_level": request["requested_level"],
            "granted_by": approver_id,
            "granted_date": datetime.utcnow(),
            "expires_at": request["expires_at"],
            "active": True
        })

        # Update request status
        db.privilege_requests.update_one(
            {"request_id": request_id},
            {"$set": {
                "status": "approved",
                "approver": approver_id,
                "approved_date": datetime.utcnow()
            }}
        )

        logger.warning("Privilege elevation granted", extra={
            "event": "privilege_elevation_granted",
            "request_id": request_id,
            "user_id": request["user_id"],
            "privilege_level": request["requested_level"],
            "approver": approver_id
        })

    def check_privileges(self, user_id: str, required_level: PrivilegeLevel) -> bool:
        """
        Check if user currently has required privileges.

        Checks for active, non-expired privilege grants.
        """
        current_grant = db.privilege_grants.find_one({
            "user_id": user_id,
            "active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not current_grant:
            has_access = False
        else:
            granted_level = PrivilegeLevel(current_grant["privilege_level"])
            has_access = self._privilege_hierarchy(granted_level, required_level)

        logger.info("Privilege check", extra={
            "event": "privilege_check",
            "user_id": user_id,
            "required_level": required_level.value,
            "has_access": has_access
        })

        return has_access

    def revoke_privileges(self, user_id: str, reason: str):
        """
        Immediately revoke all elevated privileges.

        Used for security incidents or employee termination.
        """
        db.privilege_grants.update_many(
            {"user_id": user_id, "active": True},
            {"$set": {
                "active": False,
                "revoked_date": datetime.utcnow(),
                "revoked_reason": reason
            }}
        )

        logger.warning("Privileges revoked", extra={
            "event": "privilege_revocation",
            "user_id": user_id,
            "reason": reason
        })

    def _privilege_hierarchy(self, granted: PrivilegeLevel, required: PrivilegeLevel) -> bool:
        """Check if granted level meets or exceeds required level."""
        hierarchy = {
            PrivilegeLevel.ADMIN: 3,
            PrivilegeLevel.ELEVATED: 2,
            PrivilegeLevel.STANDARD: 1
        }
        return hierarchy[granted] >= hierarchy[required]
```

### Control 8.5: Secure Authentication

**Requirement**: Implement secure authentication mechanisms.

**Implementation**:

```python
# Multi-factor authentication for ISO 27001
import pyotp
import hashlib
from datetime import datetime, timedelta

class ISO27001Authentication:
    """
    Secure authentication implementing ISO 27001:2022 Control 8.5.

    Requirements:
    - Strong password policy
    - Multi-factor authentication
    - Account lockout
    - Session management
    - Authentication logging
    """

    # Password policy (Control 8.5)
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_COMPLEXITY = True  # Uppercase, lowercase, number, special char
    PASSWORD_HISTORY = 10  # Cannot reuse last 10 passwords
    PASSWORD_MAX_AGE_DAYS = 90
    ACCOUNT_LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION_MINUTES = 30

    def authenticate_user(self, username: str, password: str, mfa_token: str = None) -> dict:
        """
        Authenticate user with password and optional MFA.

        ISO 27001 Control 8.5: Secure authentication
        """
        user = db.users.find_one({"username": username})

        if not user:
            # Same error message to prevent username enumeration
            logger.warning("Authentication failed", extra={
                "event": "authentication_failed",
                "username": username,
                "reason": "invalid_credentials",
                "ip_address": get_request_ip()
            })
            raise AuthenticationError("Invalid credentials")

        # Check if account locked
        if self._is_account_locked(user["user_id"]):
            logger.warning("Authentication failed - account locked", extra={
                "event": "authentication_failed",
                "user_id": user["user_id"],
                "reason": "account_locked"
            })
            raise AuthenticationError("Account locked due to multiple failed attempts")

        # Verify password
        if not self._verify_password(password, user["password_hash"]):
            self._record_failed_attempt(user["user_id"])
            logger.warning("Authentication failed - invalid password", extra={
                "event": "authentication_failed",
                "user_id": user["user_id"],
                "reason": "invalid_password"
            })
            raise AuthenticationError("Invalid credentials")

        # Check if MFA required
        if user["mfa_enabled"]:
            if not mfa_token:
                logger.info("MFA required", extra={
                    "event": "mfa_required",
                    "user_id": user["user_id"]
                })
                return {"status": "mfa_required", "user_id": user["user_id"]}

            if not self._verify_mfa(user["mfa_secret"], mfa_token):
                logger.warning("Authentication failed - invalid MFA", extra={
                    "event": "authentication_failed",
                    "user_id": user["user_id"],
                    "reason": "invalid_mfa"
                })
                raise AuthenticationError("Invalid MFA token")

        # Check password expiration
        if self._is_password_expired(user):
            logger.info("Password expired", extra={
                "event": "password_expired",
                "user_id": user["user_id"]
            })
            return {"status": "password_expired", "user_id": user["user_id"]}

        # Authentication successful
        session_token = self._create_session(user["user_id"])

        # Clear failed attempts
        self._clear_failed_attempts(user["user_id"])

        logger.info("Authentication successful", extra={
            "event": "authentication_success",
            "user_id": user["user_id"],
            "mfa_used": user["mfa_enabled"],
            "ip_address": get_request_ip()
        })

        return {
            "status": "authenticated",
            "user_id": user["user_id"],
            "session_token": session_token
        }

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password using secure hashing (bcrypt/argon2)."""
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        try:
            ph.verify(password_hash, password)
            return True
        except:
            return False

    def _is_account_locked(self, user_id: str) -> bool:
        """Check if account locked due to failed attempts."""
        failed_attempts = db.failed_auth_attempts.find({
            "user_id": user_id,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)}
        }).count()

        return failed_attempts >= self.ACCOUNT_LOCKOUT_THRESHOLD

    def _is_password_expired(self, user: dict) -> bool:
        """Check if password has expired (Control 8.5)."""
        password_age = datetime.utcnow() - user["password_changed_date"]
        return password_age.days > self.PASSWORD_MAX_AGE_DAYS

    def enforce_password_policy(self, password: str, user_id: str = None) -> bool:
        """
        Enforce password complexity requirements.

        ISO 27001 Control 8.5: Strong passwords required
        """
        import re

        # Length check
        if len(password) < self.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.PASSWORD_MIN_LENGTH} characters")

        # Complexity check
        if self.PASSWORD_COMPLEXITY:
            if not re.search(r"[A-Z]", password):
                raise ValueError("Password must contain uppercase letter")
            if not re.search(r"[a-z]", password):
                raise ValueError("Password must contain lowercase letter")
            if not re.search(r"\d", password):
                raise ValueError("Password must contain number")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                raise ValueError("Password must contain special character")

        # Password history check (prevent reuse)
        if user_id and self._is_password_reused(user_id, password):
            raise ValueError(f"Cannot reuse last {self.PASSWORD_HISTORY} passwords")

        return True
```

### Control 8.9: Configuration Management

**Requirement**: Manage configurations securely throughout lifecycle.

**Implementation**:

```python
# Configuration management for ISO 27001
import json
from typing import Dict, Any

class ConfigurationManager:
    """
    Secure configuration management.

    ISO 27001 Control 8.9: Configuration management

    Requirements:
    - Configuration baseline documented
    - Changes tracked and authorized
    - Configurations versioned
    - Secrets never in plaintext
    """

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config_version = self._load_config_version()

    def get_config(self, key: str, secret: bool = False) -> Any:
        """
        Retrieve configuration value.

        Secrets fetched from vault, never from config files.
        """
        if secret:
            # Fetch from secrets vault (AWS Secrets Manager, HashiCorp Vault)
            value = self._fetch_from_vault(key)
        else:
            # Non-secret configs can be in config files
            value = self._fetch_from_config_file(key)

        logger.info("Configuration accessed", extra={
            "event": "config_access",
            "key": key,
            "is_secret": secret,
            "environment": self.environment
        })

        return value

    def update_config(self, key: str, value: Any, change_ticket: str):
        """
        Update configuration with change control.

        ISO 27001 Control 8.32: Change management required
        """
        # Verify change ticket approved
        if not self._is_change_approved(change_ticket):
            raise PermissionError("Configuration change requires approved change ticket")

        # Backup current config
        self._backup_current_config()

        # Update configuration
        current_config = self._load_config()
        old_value = current_config.get(key)
        current_config[key] = value

        # Save new configuration
        new_version = self._increment_version()
        self._save_config(current_config, new_version)

        # Audit log
        logger.warning("Configuration changed", extra={
            "event": "config_change",
            "key": key,
            "old_value": str(old_value)[:50],  # Truncate for security
            "new_value": str(value)[:50],
            "change_ticket": change_ticket,
            "changed_by": get_current_user(),
            "config_version": new_version
        })

        return {"version": new_version, "change_ticket": change_ticket}

    def _fetch_from_vault(self, secret_name: str) -> str:
        """
        Fetch secret from vault (never stored in code/config).

        Example: AWS Secrets Manager
        """
        import boto3

        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)

        return response['SecretString']

    def _is_change_approved(self, change_ticket: str) -> bool:
        """Verify change ticket approved before allowing config change."""
        ticket = db.change_tickets.find_one({"ticket_id": change_ticket})

        if not ticket:
            return False

        return ticket["status"] == "approved" and ticket["approver"] is not None
```

### Control 8.16: Monitoring Activities

**Requirement**: Monitor system activities and log security events.

**Implementation**:

```python
# Security monitoring for ISO 27001
from pythonjsonlogger import jsonlogger
import logging

class ISO27001SecurityMonitoring:
    """
    Security event monitoring and logging.

    ISO 27001 Control 8.16: Monitoring activities

    Requirements:
    - Log all security-relevant events
    - Protect log integrity
    - Regular log review
    - Retain logs per retention policy (typically 1 year minimum)
    """

    def __init__(self):
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Configure structured JSON logging for ISO 27001."""
        logger = logging.getLogger("iso27001_audit")
        logger.setLevel(logging.INFO)

        # Use JSON formatter for structured logs
        handler = logging.FileHandler("iso27001_audit.log")
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(event_type)s %(user_id)s %(ip_address)s %(resource)s %(action)s %(result)s %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Also send to SIEM (Splunk, ELK, etc.)
        siem_handler = self._setup_siem_handler()
        logger.addHandler(siem_handler)

        return logger

    def log_access_attempt(self, user_id: str, resource: str, action: str, granted: bool):
        """Log all access attempts (Control 8.16)."""
        self.logger.info("Access attempt", extra={
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "access_control",
            "user_id": user_id,
            "ip_address": get_request_ip(),
            "resource": resource,
            "action": action,
            "result": "granted" if granted else "denied"
        })

    def log_configuration_change(self, changed_by: str, component: str, change_details: dict):
        """Log configuration changes (Control 8.9, 8.16)."""
        self.logger.warning("Configuration change", extra={
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "config_change",
            "user_id": changed_by,
            "component": component,
            "change_details": json.dumps(change_details),
            "result": "success"
        })

    def log_security_event(self, event_type: str, severity: str, description: str):
        """Log security events (Control 8.16)."""
        log_method = {
            "low": self.logger.info,
            "medium": self.logger.warning,
            "high": self.logger.error,
            "critical": self.logger.critical
        }.get(severity.lower(), self.logger.info)

        log_method(f"Security event: {description}", extra={
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "description": description
        })

    def detect_anomalies(self):
        """
        Detect anomalous activities requiring investigation.

        Examples:
        - Failed login attempts (>5 in 15 minutes)
        - Privilege escalation
        - Unusual data access patterns
        - Configuration changes outside change window
        """
        # Check for brute force attacks
        failed_logins = db.audit_logs.aggregate([
            {"$match": {
                "event_type": "authentication",
                "result": "denied",
                "timestamp": {"$gte": fifteen_minutes_ago()}
            }},
            {"$group": {
                "_id": "$user_id",
                "attempts": {"$sum": 1}
            }},
            {"$match": {"attempts": {"$gte": 5}}}
        ])

        for user in failed_logins:
            self.log_security_event(
                event_type="brute_force_detected",
                severity="high",
                description=f"User {user['_id']}: {user['attempts']} failed login attempts"
            )
            # Trigger incident response
            self._create_security_incident(
                incident_type="brute_force_attack",
                user_id=user["_id"]
            )
```

### Control 8.24: Use of Cryptography

**Requirement**: Cryptography used appropriately and effectively.

**Implementation**:

```python
# Cryptography for ISO 27001
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os

class ISO27001Cryptography:
    """
    Cryptographic controls for ISO 27001.

    ISO 27001 Control 8.24: Use of cryptography

    Requirements:
    - Strong encryption algorithms (AES-256, RSA-2048+)
    - Key management (generation, storage, rotation, destruction)
    - Encryption for data at rest and in transit
    - Digital signatures where appropriate
    """

    # Cryptographic standards (Control 8.24)
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    KEY_SIZE = 256  # bits
    HASH_ALGORITHM = "SHA-256"

    def encrypt_sensitive_data(self, plaintext: bytes, data_classification: str) -> dict:
        """
        Encrypt sensitive data at rest.

        Control 8.24: Strong encryption for confidential data
        """
        # Generate key from master key (stored in HSM/vault)
        master_key = self._get_master_key()
        data_key = self._derive_key(master_key)

        # AES-256-GCM encryption
        cipher = Cipher(
            algorithms.AES(data_key),
            modes.GCM(os.urandom(12)),  # 96-bit nonce
            backend=default_backend()
        )

        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Compute integrity tag
        tag = encryptor.tag

        logger.info("Data encrypted", extra={
            "event": "data_encryption",
            "algorithm": self.ENCRYPTION_ALGORITHM,
            "data_classification": data_classification,
            "key_id": self._get_key_id(master_key)
        })

        return {
            "ciphertext": ciphertext,
            "nonce": cipher.mode.initialization_vector,
            "tag": tag,
            "algorithm": self.ENCRYPTION_ALGORITHM,
            "key_id": self._get_key_id(master_key)
        }

    def _get_master_key(self) -> bytes:
        """
        Retrieve master encryption key from secure storage.

        NEVER store encryption keys in:
        - Application code
        - Configuration files
        - Environment variables (on production)

        ALWAYS store keys in:
        - Hardware Security Module (HSM)
        - Key Management Service (AWS KMS, Azure Key Vault)
        - HashiCorp Vault
        """
        import boto3

        kms = boto3.client('kms')
        response = kms.generate_data_key(
            KeyId='alias/master-key',
            KeySpec='AES_256'
        )

        return response['Plaintext']
```

---

## Required Documentation (ISMS)

### 1. Statement of Applicability (SoA)

**Purpose**: Document which controls apply and justifications for exclusions.

**Template**:
```markdown
# Statement of Applicability - ISO 27001:2022

## ISMS Scope
- **Systems**: Production web application, database, API
- **Locations**: AWS us-east-1, employee home offices
- **Organizational Units**: Engineering, Security, Support

## Control Applicability

| Control | Theme | Title | Applicable? | Implementation Status | Justification |
|---------|-------|-------|-------------|----------------------|---------------|
| 5.1 | Organizational | Policies for information security | Yes | Implemented | Information Security Policy v2.0 |
| 5.7 | Organizational | Threat intelligence | Yes | Implemented | Vulnerability scanning, threat feeds |
| 5.15 | Organizational | Access control | Yes | Implemented | RBAC, MFA enforced |
| 8.2 | Technological | Privileged access rights | Yes | Implemented | Just-in-time elevation |
| 8.5 | Technological | Secure authentication | Yes | Implemented | MFA, strong passwords |
| 8.24 | Technological | Use of cryptography | Yes | Implemented | AES-256, TLS 1.2+ |
| 7.1 | Physical | Physical security perimeters | No | N/A | Cloud-only, no physical datacenter |
```

### 2. Risk Assessment Report

**Required by Clause 6.1.2**: Conduct risk assessment.

**Template**:
```markdown
# Information Security Risk Assessment

## Risk Assessment Methodology
- **Likelihood**: Rare (1), Unlikely (2), Possible (3), Likely (4), Almost Certain (5)
- **Impact**: Insignificant (1), Minor (2), Moderate (3), Major (4), Severe (5)
- **Risk Score**: Likelihood × Impact
- **Risk Appetite**: Accept risks ≤ 6, Treat risks > 6

## Identified Risks

| ID | Asset | Threat | Vulnerability | Likelihood | Impact | Risk Score | Treatment |
|----|-------|--------|---------------|------------|--------|------------|-----------|
| R001 | Database | Unauthorized access | Weak passwords | 4 | 5 | 20 | Treat (implement MFA) |
| R002 | API | Data breach | No encryption | 3 | 5 | 15 | Treat (implement TLS 1.3) |
| R003 | Backups | Data loss | No backups | 2 | 5 | 10 | Treat (automated backups) |
```

### 3. Risk Treatment Plan

**Required by Clause 6.1.3**: Define risk treatment.

**Template**:
```markdown
# Risk Treatment Plan

| Risk ID | Treatment Option | Controls Implemented | Owner | Due Date | Status |
|---------|------------------|---------------------|--------|----------|--------|
| R001 | Reduce | 8.5 (MFA), 8.2 (Privileged access) | Security Team | 2025-02-01 | In Progress |
| R002 | Reduce | 8.24 (Cryptography - TLS 1.3) | Engineering | 2025-01-15 | Complete |
| R003 | Reduce | 8.13 (Information backup) | Operations | 2025-01-20 | Complete |
```

---

## Integration with Other Frameworks

### ISO 27001 + SOC 2

Many organizations pursue both certifications:

| ISO 27001 Control | SOC 2 Control | Overlap |
|-------------------|---------------|---------|
| 5.15 (Access control) | CC6.1 (Logical access) | High |
| 8.5 (Authentication) | CC6.2 (Authentication) | High |
| 8.16 (Monitoring) | CC7.2 (System monitoring) | High |
| 8.32 (Change management) | CC8.1 (Authorize changes) | High |

Use same implementations and evidence for both!

### ISO 27001 + GDPR

ISO 27001 supports GDPR compliance:

| ISO 27001 Control | GDPR Requirement |
|-------------------|------------------|
| 5.34 (Privacy and PII) | Article 5 (Data protection principles) |
| 8.24 (Cryptography) | Article 32 (Security of processing) |
| 6.8 (Event reporting) | Article 33 (Breach notification) |
| 5.10 (Acceptable use) | Article 5(1)(b) (Purpose limitation) |

---

## Success Criteria

### Implementation Complete

- [ ] All 114 controls assessed for applicability
- [ ] Statement of Applicability (SoA) completed
- [ ] Risk assessment conducted
- [ ] Risk treatment plan documented
- [ ] Applicable controls implemented with Python code
- [ ] ISMS policies and procedures documented

### Evidence Collected

- [ ] Information Security Policy (executive-approved)
- [ ] Risk assessment and treatment documentation
- [ ] SoA with control implementation evidence
- [ ] Internal audit reports
- [ ] Management review minutes
- [ ] Access control matrices
- [ ] Configuration baselines
- [ ] Incident response records

### Certification Ready

- [ ] Internal audit completed (no major nonconformities)
- [ ] Management review conducted
- [ ] Corrective actions closed
- [ ] Stage 1 audit scheduled with certification body
- [ ] Stage 2 audit scheduled
- [ ] Surveillance audit schedule planned (annual)

---

## Common Pitfalls

### ❌ Treating as Checklist

**Problem**: Implementing controls without understanding risk context.

**Solution**: Start with risk assessment. Implement controls based on risks, not just checklist.

### ❌ Documentation Overload

**Problem**: Creating excessive documentation that isn't maintained.

**Solution**: Document what's necessary and useful. Link to existing docs where possible.

### ❌ Ignoring Context Clauses

**Problem**: Focusing only on Annex A controls, ignoring Clauses 4-10.

**Solution**: ISMS is about the management system. Context, leadership, planning, support, operation, evaluation, improvement are equally important.

### ❌ One-Time Project Mentality

**Problem**: Treating certification as endpoint rather than starting point.

**Solution**: Continual improvement. Regular audits (internal annual, external surveillance annual, recertification every 3 years).

---

## Resources

### Official Standards

- [ISO 27001:2022](https://www.iso.org/standard/27001) - Information Security Management
- [ISO 27002:2022](https://www.iso.org/standard/75652.html) - Information security controls (implementation guidance)
- [ISO 27005:2022](https://www.iso.org/standard/80585.html) - Information security risk management

### Implementation Guides

- [ISO 27001 and AI](https://www.itgovernance.co.uk/blog/how-to-address-ai-security-risks-with-iso-27001)
- [Transition Guide to 2022](https://www.iso.org/news/ref2833.html)

### Tools

- **ISMS Software**: ISMS.online, Secureframe, Vanta, Drata
- **Risk Assessment**: RiskLens, ServiceNow GRC
- **Internal Audit**: AuditBoard, LogicManager

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete ISO 27001:2022 implementation for Python
- All 4 control themes covered
- Focus on Technological Controls (Theme 4 - most relevant for Python)
- Privileged access management (Control 8.2)
- Secure authentication (Control 8.5)
- Configuration management (Control 8.9)
- Security monitoring (Control 8.16)
- Cryptography (Control 8.24)
- ISMS documentation templates (SoA, Risk Assessment, Risk Treatment Plan)
- Integration with SOC 2 and GDPR

**Framework Coverage**:
- 114 controls across 4 themes
- Focus on Organizational and Technological controls
- Code examples for key technological controls

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
