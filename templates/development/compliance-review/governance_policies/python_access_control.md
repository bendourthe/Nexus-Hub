---
template_id: compliance_governance_access_control_python
template_name: Access Control - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/python_security_policies.md
  - compliance_frameworks/python_soc2_compliance.md
related_templates:
  - compliance_frameworks/python_iso27001_implementation.md
  - ai_agent_governance/python_agent_security.md
tools:
  - flask-security (authentication)
  - pyjwt (JWT tokens)
  - python-jose (JWT/JWE)
  - casbin (authorization)
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - python
---

# Access Control - Python

**🔒 Pillar 3: Security (Least Privilege)**

Implement role-based access control (RBAC) and least privilege access

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is Access Control?

**Access Control** ensures only authorized users can access resources. It implements the principle of least privilege: users get minimum permissions needed for their role.

**Two Components**:
- **Authentication** - Who are you? (Identity verification)
- **Authorization** - What can you do? (Permission checking)

### Framework Requirements

**ISO 27001 Control 5.15**: Access control
- Access control policy
- User access management
- Access rights review

**SOC 2 CC6.1**: Logical access controls
- Unique user identification
- Authentication mechanisms
- Authorization

**SOC 2 CC6.2**: Authentication and identification
- Multi-factor authentication for privileged access
- Password requirements

---

## Access Control Models

### Role-Based Access Control (RBAC)

**Concept**: Permissions assigned to roles, users assigned to roles

**Example**:
- Role: "Developer" → Permissions: [read_code, write_code, deploy_dev]
- User: Alice → Roles: ["Developer"]
- Result: Alice can read_code, write_code, deploy_dev

### Attribute-Based Access Control (ABAC)

**Concept**: Access decisions based on attributes (user, resource, environment)

**Example**:
- Rule: "Allow if user.department == resource.owner_department AND time.hour >= 9 AND time.hour <= 17"

### Zero Trust Architecture

**Principle**: Never trust, always verify

**Requirements**:
- Verify explicitly (authenticate + authorize every request)
- Use least privilege
- Assume breach (monitor everything)

---

## Implementation Roadmap

### Phase 1: Authentication (Week 1)

**Deliverables**:
1. User authentication system
2. Multi-factor authentication (MFA)
3. Session management
4. Password policy enforcement

**Code**: See [Authentication](#authentication-implementation)

### Phase 2: Authorization (Week 2)

**Deliverables**:
1. RBAC implementation
2. Role definitions
3. Permission model
4. Authorization middleware

**Code**: See [RBAC Implementation](#rbac-implementation)

### Phase 3: Privileged Access Management (Week 3)

**Deliverables**:
1. Privileged account management
2. Just-in-time (JIT) access
3. Session recording
4. Access reviews

**Code**: See [Privileged Access](#privileged-access-management)

### Phase 4: Access Governance (Week 4)

**Deliverables**:
1. User provisioning/deprovisioning
2. Access certification
3. Access audit logs
4. Compliance reporting

**Code**: See [Access Governance](#access-governance-implementation)

---

## Authentication Implementation

### Multi-Factor Authentication

**SOC 2 CC6.2**: MFA for privileged access

**Implementation**:

```python
# Multi-factor authentication
import pyotp
import qrcode
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MFAManager:
    """
    Multi-factor authentication manager.

    Security: Least Privilege
    Compliance: SOC 2 CC6.2, ISO 27001 Control 8.5
    """

    def enroll_mfa(self, user_id: str, user_email: str) -> Dict:
        """
        Enroll user in MFA.

        Generates TOTP secret and QR code for authenticator app.
        """
        # Generate secret
        secret = pyotp.random_base32()

        # Store secret (encrypted)
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "mfa_secret": self._encrypt_secret(secret),
                "mfa_enabled": True,
                "mfa_enrolled_date": datetime.utcnow()
            }}
        )

        # Generate QR code for authenticator app
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="YourCompany"
        )

        # Generate QR code
        qr = qrcode.make(provisioning_uri)
        qr_filename = f"mfa_qr_{user_id}.png"
        qr.save(qr_filename)

        logger.info("MFA enrolled", extra={
            "event": "mfa_enrollment",
            "user_id": user_id
        })

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_file": qr_filename
        }

    def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """
        Verify MFA token.

        Time-based one-time password (TOTP) verification.
        """
        user = db.users.find_one({"user_id": user_id})

        if not user["mfa_enabled"]:
            return True  # MFA not enabled

        secret = self._decrypt_secret(user["mfa_secret"])
        totp = pyotp.TOTP(secret)

        # Verify with 1-minute window (allows clock drift)
        is_valid = totp.verify(token, valid_window=1)

        logger.info("MFA verification", extra={
            "event": "mfa_verification",
            "user_id": user_id,
            "success": is_valid
        })

        return is_valid

    def generate_backup_codes(self, user_id: str, count: int = 10) -> list:
        """
        Generate backup codes for account recovery.

        In case user loses MFA device.
        """
        import secrets

        backup_codes = [secrets.token_hex(4).upper() for _ in range(count)]

        # Store hashed backup codes
        hashed_codes = [self._hash_code(code) for code in backup_codes]

        db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "mfa_backup_codes": hashed_codes,
                "backup_codes_generated_date": datetime.utcnow()
            }}
        )

        logger.warning("Backup codes generated", extra={
            "event": "backup_codes_generated",
            "user_id": user_id,
            "count": count
        })

        return backup_codes

class AuthenticationManager:
    """
    User authentication manager.

    Security: Least Privilege
    Compliance: SOC 2 CC6.1, ISO 27001 Control 8.5
    """

    # Password policy
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_COMPLEXITY = True
    PASSWORD_HISTORY = 10
    PASSWORD_MAX_AGE_DAYS = 90
    ACCOUNT_LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION_MINUTES = 30

    def authenticate(self, username: str, password: str, mfa_token: Optional[str] = None) -> Dict:
        """
        Authenticate user.

        Returns session token if successful.
        """
        user = db.users.find_one({"username": username})

        if not user:
            self._record_failed_login(username, "user_not_found")
            raise AuthenticationError("Invalid credentials")

        # Check account locked
        if self._is_account_locked(user["user_id"]):
            raise AuthenticationError("Account locked due to failed login attempts")

        # Verify password
        if not self._verify_password(password, user["password_hash"]):
            self._record_failed_login(user["user_id"], "invalid_password")
            raise AuthenticationError("Invalid credentials")

        # Check MFA
        if user["mfa_enabled"]:
            if not mfa_token:
                return {"status": "mfa_required", "user_id": user["user_id"]}

            if not MFAManager().verify_mfa_token(user["user_id"], mfa_token):
                self._record_failed_login(user["user_id"], "invalid_mfa")
                raise AuthenticationError("Invalid MFA token")

        # Check password expiration
        if self._is_password_expired(user):
            return {"status": "password_expired", "user_id": user["user_id"]}

        # Success - create session
        session_token = self._create_session(user["user_id"])

        logger.info("Authentication successful", extra={
            "event": "authentication_success",
            "user_id": user["user_id"],
            "mfa_used": user["mfa_enabled"]
        })

        return {
            "status": "authenticated",
            "session_token": session_token,
            "user_id": user["user_id"]
        }

    def _create_session(self, user_id: str) -> str:
        """
        Create authenticated session.

        Returns JWT token.
        """
        import jwt
        from datetime import datetime, timedelta

        # Session expires in 8 hours
        expiration = datetime.utcnow() + timedelta(hours=8)

        payload = {
            "user_id": user_id,
            "exp": expiration,
            "iat": datetime.utcnow()
        }

        token = jwt.encode(payload, get_secret_key(), algorithm="HS256")

        # Store session
        db.sessions.insert_one({
            "session_id": generate_uuid(),
            "user_id": user_id,
            "token": token,
            "created_date": datetime.utcnow(),
            "expires_date": expiration,
            "ip_address": get_request_ip(),
            "user_agent": get_request_user_agent()
        })

        return token

    def _is_account_locked(self, user_id: str) -> bool:
        """Check if account locked due to failed attempts."""
        failed_attempts = db.failed_login_attempts.find({
            "user_id": user_id,
            "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)}
        }).count()

        return failed_attempts >= self.ACCOUNT_LOCKOUT_THRESHOLD
```

---

## RBAC Implementation

### Role-Based Access Control

**ISO 27001 Control 5.15**: RBAC for access management

**Implementation**:

```python
# Role-Based Access Control (RBAC)
from enum import Enum
from typing import List, Set

class Permission(Enum):
    """System permissions."""
    # Data permissions
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"

    # Configuration permissions
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"

    # User management
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    DELETE_USERS = "delete_users"

    # Admin permissions
    ADMIN_ALL = "admin_all"

class Role(Enum):
    """User roles."""
    USER = "user"
    DEVELOPER = "developer"
    ADMIN = "admin"
    AUDITOR = "auditor"

class RBACManager:
    """
    Role-Based Access Control manager.

    Security: Least Privilege
    Compliance: ISO 27001 Control 5.15, SOC 2 CC6.1
    """

    # Role permission matrix
    ROLE_PERMISSIONS = {
        Role.USER: {
            Permission.READ_DATA
        },
        Role.DEVELOPER: {
            Permission.READ_DATA,
            Permission.WRITE_DATA,
            Permission.READ_CONFIG
        },
        Role.ADMIN: {
            Permission.READ_DATA,
            Permission.WRITE_DATA,
            Permission.DELETE_DATA,
            Permission.READ_CONFIG,
            Permission.WRITE_CONFIG,
            Permission.READ_USERS,
            Permission.WRITE_USERS,
            Permission.DELETE_USERS,
            Permission.ADMIN_ALL
        },
        Role.AUDITOR: {
            Permission.READ_DATA,
            Permission.READ_CONFIG,
            Permission.READ_USERS
        }
    }

    def assign_role(self, user_id: str, role: Role, assigned_by: str) -> Dict:
        """
        Assign role to user.

        Least Privilege: Only assign necessary roles.
        """
        # Check if assigner has permission
        if not self.has_permission(assigned_by, Permission.WRITE_USERS):
            raise PermissionError("Insufficient permissions to assign roles")

        # Get user's current roles
        user = db.users.find_one({"user_id": user_id})
        current_roles = user.get("roles", [])

        # Add new role
        if role.value not in current_roles:
            current_roles.append(role.value)

            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"roles": current_roles}}
            )

            logger.warning("Role assigned", extra={
                "event": "role_assignment",
                "user_id": user_id,
                "role": role.value,
                "assigned_by": assigned_by
            })

        return {"user_id": user_id, "roles": current_roles}

    def revoke_role(self, user_id: str, role: Role, revoked_by: str) -> Dict:
        """
        Revoke role from user.
        """
        if not self.has_permission(revoked_by, Permission.WRITE_USERS):
            raise PermissionError("Insufficient permissions to revoke roles")

        user = db.users.find_one({"user_id": user_id})
        current_roles = user.get("roles", [])

        if role.value in current_roles:
            current_roles.remove(role.value)

            db.users.update_one(
                {"user_id": user_id},
                {"$set": {"roles": current_roles}}
            )

            logger.warning("Role revoked", extra={
                "event": "role_revocation",
                "user_id": user_id,
                "role": role.value,
                "revoked_by": revoked_by
            })

        return {"user_id": user_id, "roles": current_roles}

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has permission.

        Core authorization check used throughout application.
        """
        user = db.users.find_one({"user_id": user_id})
        user_roles = [Role(r) for r in user.get("roles", [])]

        # Aggregate permissions from all roles
        user_permissions: Set[Permission] = set()
        for role in user_roles:
            user_permissions.update(self.ROLE_PERMISSIONS.get(role, set()))

        has_access = permission in user_permissions

        logger.info("Permission check", extra={
            "user_id": user_id,
            "permission": permission.value,
            "granted": has_access
        })

        return has_access

    def require_permission(self, permission: Permission):
        """
        Decorator to enforce permission on functions.

        Usage:
        @RBACManager().require_permission(Permission.WRITE_DATA)
        def delete_record(record_id):
            ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                user_id = get_current_user_id()
                if not self.has_permission(user_id, permission):
                    raise PermissionError(f"Permission required: {permission.value}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

---

## Privileged Access Management

### Just-In-Time Access

**ISO 27001 Control 8.2**: Privileged access management

**Implementation**:

```python
# Privileged Access Management (PAM)
class PrivilegedAccessManager:
    """
    Just-in-time privileged access.

    Security: Least Privilege
    Compliance: ISO 27001 Control 8.2, SOC 2 CC6.1
    """

    def request_elevated_access(
        self,
        user_id: str,
        target_role: Role,
        justification: str,
        duration_hours: int = 4
    ) -> str:
        """
        Request temporary elevated access (JIT).

        Pattern: Just-in-time access (access granted only when needed)
        """
        if duration_hours > 8:
            raise ValueError("Maximum elevation period is 8 hours")

        request_id = generate_uuid()
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        # Store request
        db.access_requests.insert_one({
            "request_id": request_id,
            "user_id": user_id,
            "target_role": target_role.value,
            "justification": justification,
            "requested_date": datetime.utcnow(),
            "expires_at": expires_at,
            "status": "pending_approval",
            "approver": None
        })

        # Auto-approve for developers, require approval for admin
        if target_role == Role.DEVELOPER:
            self._auto_approve_request(request_id)
        else:
            self._notify_approvers(request_id)

        logger.warning("Elevated access requested", extra={
            "event": "elevated_access_request",
            "request_id": request_id,
            "user_id": user_id,
            "target_role": target_role.value
        })

        return request_id

    def approve_access_request(self, request_id: str, approver_id: str):
        """
        Approve access request.

        Temporarily grants elevated role.
        """
        request = db.access_requests.find_one({"request_id": request_id})

        # Grant temporary role
        db.users.update_one(
            {"user_id": request["user_id"]},
            {"$push": {"roles": request["target_role"]}}
        )

        # Update request status
        db.access_requests.update_one(
            {"request_id": request_id},
            {"$set": {
                "status": "approved",
                "approver": approver_id,
                "approved_date": datetime.utcnow()
            }}
        )

        # Schedule auto-revocation
        self._schedule_revocation(request_id, request["expires_at"])

        logger.warning("Elevated access granted", extra={
            "event": "elevated_access_granted",
            "request_id": request_id,
            "user_id": request["user_id"],
            "approver": approver_id
        })

    def revoke_elevated_access(self, request_id: str):
        """
        Revoke temporary elevated access.

        Called automatically when access expires.
        """
        request = db.access_requests.find_one({"request_id": request_id})

        # Remove temporary role
        db.users.update_one(
            {"user_id": request["user_id"]},
            {"$pull": {"roles": request["target_role"]}}
        )

        db.access_requests.update_one(
            {"request_id": request_id},
            {"$set": {"status": "revoked"}}
        )

        logger.warning("Elevated access revoked", extra={
            "event": "elevated_access_revoked",
            "request_id": request_id,
            "user_id": request["user_id"]
        })
```

---

## Access Governance Implementation

### Access Certification

**ISO 27001 Control 5.18**: Access reviews

**Implementation**:

```python
# Access governance and certification
class AccessGovernance:
    """
    Access governance and periodic reviews.

    Security: Least Privilege
    Compliance: ISO 27001 Control 5.18, SOC 2 CC6.1
    """

    def initiate_access_review(self, review_scope: str = "all") -> str:
        """
        Initiate periodic access review.

        ISO 27001 Control 5.18: Review user access rights at regular intervals
        Frequency: Quarterly for all users, monthly for privileged users
        """
        review_id = generate_uuid()

        # Get users in scope
        if review_scope == "privileged":
            users = list(db.users.find({"roles": {"$in": [Role.ADMIN.value]}}))
        else:
            users = list(db.users.find({"status": "active"}))

        review = {
            "review_id": review_id,
            "review_scope": review_scope,
            "initiated_date": datetime.utcnow(),
            "due_date": datetime.utcnow() + timedelta(days=14),
            "users_in_scope": len(users),
            "users_reviewed": 0,
            "status": "in_progress"
        }

        db.access_reviews.insert_one(review)

        # Notify managers to certify access
        for user in users:
            self._notify_manager_for_certification(user)

        logger.warning("Access review initiated", extra={
            "event": "access_review_initiated",
            "review_id": review_id,
            "scope": review_scope,
            "users_count": len(users)
        })

        return review_id

    def certify_user_access(
        self,
        review_id: str,
        user_id: str,
        certifier_id: str,
        certification: str,
        comments: str = None
    ):
        """
        Certify user's access as appropriate or inappropriate.

        Certification options: "approve", "revoke", "modify"
        """
        if certification not in ["approve", "revoke", "modify"]:
            raise ValueError("Invalid certification")

        certification_record = {
            "review_id": review_id,
            "user_id": user_id,
            "certifier_id": certifier_id,
            "certification": certification,
            "comments": comments,
            "certified_date": datetime.utcnow()
        }

        db.access_certifications.insert_one(certification_record)

        # If revoke, remove access
        if certification == "revoke":
            self._revoke_user_access(user_id, certifier_id, "access_review")

        # Update review progress
        db.access_reviews.update_one(
            {"review_id": review_id},
            {"$inc": {"users_reviewed": 1}}
        )

        logger.info("User access certified", extra={
            "event": "access_certified",
            "review_id": review_id,
            "user_id": user_id,
            "certification": certification
        })

    def provision_user(
        self,
        username: str,
        email: str,
        roles: List[Role],
        manager_id: str
    ) -> str:
        """
        Provision new user access.

        Onboarding workflow with manager approval.
        """
        user_id = generate_uuid()

        user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": [r.value for r in roles],
            "manager_id": manager_id,
            "status": "active",
            "provisioned_date": datetime.utcnow(),
            "mfa_enabled": False,
            "password_changed_date": datetime.utcnow()
        }

        db.users.insert_one(user)

        logger.warning("User provisioned", extra={
            "event": "user_provisioned",
            "user_id": user_id,
            "username": username,
            "roles": [r.value for r in roles]
        })

        return user_id

    def deprovision_user(self, user_id: str, deprovisioner_id: str, reason: str):
        """
        Deprovision user access.

        Offboarding workflow: Revoke all access within 24 hours.
        """
        # Revoke all roles
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "roles": [],
                "status": "deprovisioned",
                "deprovisioned_date": datetime.utcnow(),
                "deprovisioned_by": deprovisioner_id,
                "deprovision_reason": reason
            }}
        )

        # Terminate all active sessions
        db.sessions.update_many(
            {"user_id": user_id},
            {"$set": {"terminated": True}}
        )

        logger.warning("User deprovisioned", extra={
            "event": "user_deprovisioned",
            "user_id": user_id,
            "deprovisioner": deprovisioner_id,
            "reason": reason
        })
```

---

## Success Criteria

### Authentication Complete

- [ ] User authentication system operational
- [ ] Multi-factor authentication enabled for admins
- [ ] Password policy enforced
- [ ] Session management implemented
- [ ] Account lockout mechanism working

### Authorization Complete

- [ ] RBAC implemented with defined roles
- [ ] Permission checks enforced throughout application
- [ ] Authorization middleware configured
- [ ] Role assignments documented

### Privileged Access Management Complete

- [ ] Just-in-time access implemented
- [ ] Elevated access requires approval
- [ ] Automatic revocation on expiry
- [ ] Privileged session logging

### Access Governance Complete

- [ ] Quarterly access reviews scheduled
- [ ] User provisioning workflow operational
- [ ] Deprovisioning within 24 hours
- [ ] Access certification process documented

---

## Common Pitfalls

### ❌ Shared Accounts

**Problem**: Multiple users sharing credentials.

**Solution**: Unique accounts per user for accountability.

### ❌ Permanent Privileged Access

**Problem**: Users have admin rights permanently.

**Solution**: Just-in-time access, automatic revocation.

### ❌ No Access Reviews

**Problem**: Access rights never reviewed, privilege creep.

**Solution**: Quarterly access certification.

### ❌ Weak MFA

**Problem**: SMS-based MFA vulnerable to SIM swapping.

**Solution**: TOTP authenticator apps or hardware tokens.

---

## Resources

### Authentication/Authorization Frameworks

- [Flask-Security](https://flask-security-too.readthedocs.io/)
- [Django Authentication](https://docs.djangoproject.com/en/stable/topics/auth/)
- [Authlib](https://authlib.org/)

### Access Control Tools

- **Casbin** - Authorization library
- **Open Policy Agent** - Policy-based access control
- **Keycloak** - Identity and access management

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete access control implementation for Python
- Multi-factor authentication (TOTP)
- Role-based access control (RBAC)
- Just-in-time privileged access
- Access governance and certification
- User provisioning/deprovisioning
- Session management

**Framework Coverage**:
- ISO 27001 Controls 5.15, 5.18, 8.2, 8.5
- SOC 2 CC6.1, CC6.2
- Least Privilege principle

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
