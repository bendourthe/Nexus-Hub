---
template_id: compliance_governance_access_control_c
template_name: Access Control - C
version: 1.0.0
last_updated: 2025-12-05
language: c
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/c_security_policies.md
  - compliance_frameworks/c_soc2_compliance.md
related_templates:
  - compliance_frameworks/c_iso27001_implementation.md
tools:
  - syslog (logging)
  - bcrypt (password hashing)
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - c
---

# Access Control - C

**🔒 Pillar 3: Security (Least Privilege)**

Implement role-based access control (RBAC) and least privilege access

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Access Control** ensures only authorized users can access resources.

**Framework Requirements**:
- **ISO 27001 Control 5.15**: Access control policy
- **SOC 2 CC6.1**: Logical access controls
- **SOC 2 CC6.2**: Multi-factor authentication

---

## Authentication Implementation

```c
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <syslog.h>

#define MAX_NAME 128
#define PASSWORD_MIN_LENGTH 12
#define ACCOUNT_LOCKOUT_THRESHOLD 5
#define LOCKOUT_DURATION_MINUTES 30

typedef struct {
    char session_token[64];
    char user_id[64];
    time_t expires_at;
    int mfa_required;
} authentication_result_t;

typedef struct {
    char user_id[64];
    char username[MAX_NAME];
    char password_hash[128];
    int mfa_enabled;
    int failed_login_attempts;
    time_t account_locked_until;
} user_t;

int is_account_locked(const user_t *user) {
    if (user->failed_login_attempts >= ACCOUNT_LOCKOUT_THRESHOLD) {
        time_t now = time(NULL);
        if (user->account_locked_until > now) {
            return 1;
        }
    }
    return 0;
}

void record_failed_login(const char *user_id, const char *reason) {
    syslog(LOG_WARNING, "Failed login attempt: user_id=%s, reason=%s", user_id, reason);

    // In production: increment failed_login_attempts in database
    // and potentially lock account if threshold reached
}

int verify_password(const char *password, const char *password_hash) {
    // In production: use bcrypt_checkpw or similar
    // For demonstration, simplified comparison
    return 1; // Simplified
}

int verify_mfa_token(const char *user_id, const char *token) {
    // TOTP verification logic
    // Use oath-toolkit or similar library
    return 1; // Simplified
}

void generate_session_token(char *token, size_t size) {
    time_t now = time(NULL);
    snprintf(token, size, "SESSION-%ld", now);
}

int authenticate(
    const char *username,
    const char *password,
    const char *mfa_token,
    authentication_result_t *result) {

    // Retrieve user (simulated)
    user_t user;
    snprintf(user.user_id, sizeof(user.user_id), "USER-%ld", time(NULL));
    strncpy(user.username, username, sizeof(user.username) - 1);
    strncpy(user.password_hash, "$2b$12$hashed_password", sizeof(user.password_hash) - 1);
    user.mfa_enabled = 1;
    user.failed_login_attempts = 0;
    user.account_locked_until = 0;

    // Check account locked
    if (is_account_locked(&user)) {
        syslog(LOG_WARNING, "Authentication failed: account locked - user_id=%s, username=%s",
               user.user_id, username);
        return -1;
    }

    // Verify password
    if (!verify_password(password, user.password_hash)) {
        record_failed_login(user.user_id, "invalid_password");
        return -1;
    }

    // Check MFA if enabled
    if (user.mfa_enabled && (!mfa_token || strlen(mfa_token) == 0)) {
        strncpy(result->user_id, user.user_id, sizeof(result->user_id) - 1);
        result->mfa_required = 1;
        return 0;
    }

    if (user.mfa_enabled && !verify_mfa_token(user.user_id, mfa_token)) {
        record_failed_login(user.user_id, "invalid_mfa");
        return -1;
    }

    // Create session
    generate_session_token(result->session_token, sizeof(result->session_token));
    strncpy(result->user_id, user.user_id, sizeof(result->user_id) - 1);
    result->expires_at = time(NULL) + (8 * 60 * 60); // 8 hours
    result->mfa_required = 0;

    syslog(LOG_INFO, "Authentication successful: user_id=%s, username=%s",
           user.user_id, username);

    return 0;
}

int validate_password(const char *password) {
    if (strlen(password) < PASSWORD_MIN_LENGTH) {
        return 0;
    }

    // Check complexity
    int has_upper = 0, has_lower = 0, has_digit = 0, has_special = 0;

    for (size_t i = 0; i < strlen(password); i++) {
        char ch = password[i];
        if (ch >= 'A' && ch <= 'Z') has_upper = 1;
        else if (ch >= 'a' && ch <= 'z') has_lower = 1;
        else if (ch >= '0' && ch <= '9') has_digit = 1;
        else has_special = 1;
    }

    return has_upper && has_lower && has_digit && has_special;
}
```

---

## RBAC Implementation

```c
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <syslog.h>

#define MAX_PERMISSIONS 50
#define MAX_ROLES 10

typedef struct {
    char role_id[64];
    char role_name[MAX_NAME];
    char description[256];
    char permissions[MAX_PERMISSIONS][64];
    int permission_count;
    time_t created_date;
} role_t;

typedef struct {
    char user_id[64];
    char role_ids[MAX_ROLES][64];
    int role_count;
} user_roles_t;

int create_role(
    const char *role_name,
    const char *description,
    const char *permissions[],
    int permission_count,
    role_t *role) {

    time_t now = time(NULL);
    snprintf(role->role_id, sizeof(role->role_id), "ROLE-%ld", now);
    strncpy(role->role_name, role_name, sizeof(role->role_name) - 1);
    strncpy(role->description, description, sizeof(role->description) - 1);

    role->permission_count = (permission_count < MAX_PERMISSIONS) ?
                             permission_count : MAX_PERMISSIONS;

    for (int i = 0; i < role->permission_count; i++) {
        strncpy(role->permissions[i], permissions[i],
                sizeof(role->permissions[i]) - 1);
    }

    role->created_date = now;

    syslog(LOG_INFO, "Role created: role_id=%s, role_name=%s, permission_count=%d",
           role->role_id, role_name, permission_count);

    return 0;
}

int assign_role_to_user(const char *user_id, const char *role_id) {
    // In production: insert into user_roles table

    syslog(LOG_INFO, "Role assigned: user_id=%s, role_id=%s", user_id, role_id);

    return 0;
}

int get_user_permissions(
    const char *user_id,
    char permissions[][64],
    int *permission_count) {

    // In production: query database for user roles and aggregate permissions

    // Simulated permissions
    strncpy(permissions[0], "code:read", 64);
    strncpy(permissions[1], "code:write", 64);
    strncpy(permissions[2], "deploy:dev", 64);
    strncpy(permissions[3], "logs:read", 64);
    *permission_count = 4;

    syslog(LOG_INFO, "Permissions retrieved: user_id=%s, permission_count=%d",
           user_id, *permission_count);

    return 0;
}

int has_permission(const char *user_id, const char *permission) {
    char permissions[MAX_PERMISSIONS][64];
    int permission_count = 0;

    get_user_permissions(user_id, permissions, &permission_count);

    for (int i = 0; i < permission_count; i++) {
        if (strcmp(permissions[i], permission) == 0) {
            syslog(LOG_INFO, "Permission check: user_id=%s, permission=%s, granted=1",
                   user_id, permission);
            return 1;
        }
    }

    syslog(LOG_INFO, "Permission check: user_id=%s, permission=%s, granted=0",
           user_id, permission);

    return 0;
}

typedef struct {
    char user_id[64];
    char resource[MAX_NAME];
    char action[64];
    int granted;
    time_t timestamp;
} access_check_result_t;

int check_access(
    const char *user_id,
    const char *resource,
    const char *action,
    access_check_result_t *result) {

    char required_permission[192];
    snprintf(required_permission, sizeof(required_permission), "%s:%s", resource, action);

    int granted = has_permission(user_id, required_permission);

    strncpy(result->user_id, user_id, sizeof(result->user_id) - 1);
    strncpy(result->resource, resource, sizeof(result->resource) - 1);
    strncpy(result->action, action, sizeof(result->action) - 1);
    result->granted = granted;
    result->timestamp = time(NULL);

    if (!granted) {
        syslog(LOG_WARNING, "Access denied: user_id=%s, resource=%s, action=%s",
               user_id, resource, action);
    } else {
        syslog(LOG_INFO, "Access granted: user_id=%s, resource=%s, action=%s",
               user_id, resource, action);
    }

    return 0;
}
```

---

## Privileged Access Management

```c
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <syslog.h>

typedef struct {
    char request_id[64];
    char user_id[64];
    char privileged_role[MAX_NAME];
    char justification[512];
    int duration_hours;
    time_t requested_at;
    char status[32]; // pending, approved, denied, expired
    char approved_by[64];
    time_t approved_at;
    time_t expires_at;
} privileged_access_request_t;

int request_privileged_access(
    const char *user_id,
    const char *privileged_role,
    const char *justification,
    int duration_hours,
    privileged_access_request_t *request) {

    time_t now = time(NULL);

    snprintf(request->request_id, sizeof(request->request_id), "PRIVREQ-%ld", now);
    strncpy(request->user_id, user_id, sizeof(request->user_id) - 1);
    strncpy(request->privileged_role, privileged_role, sizeof(request->privileged_role) - 1);
    strncpy(request->justification, justification, sizeof(request->justification) - 1);
    request->duration_hours = duration_hours;
    request->requested_at = now;
    strncpy(request->status, "pending", sizeof(request->status) - 1);

    // Notify approvers
    syslog(LOG_INFO, "Notifying approvers: request_id=%s, role=%s",
           request->request_id, privileged_role);

    syslog(LOG_INFO, "Privileged access requested: request_id=%s, user_id=%s, role=%s",
           request->request_id, user_id, privileged_role);

    return 0;
}

typedef struct {
    char request_id[64];
    char status[32];
    time_t expires_at;
} approval_result_t;

int approve_privileged_access(
    const char *request_id,
    const char *approver_id,
    approval_result_t *result) {

    // Retrieve request (simulated)
    privileged_access_request_t request;
    strncpy(request.request_id, request_id, sizeof(request.request_id) - 1);
    strncpy(request.user_id, "user123", sizeof(request.user_id) - 1);
    strncpy(request.privileged_role, "production_admin", sizeof(request.privileged_role) - 1);
    request.duration_hours = 8;
    strncpy(request.status, "pending", sizeof(request.status) - 1);

    if (strcmp(request.status, "pending") != 0) {
        syslog(LOG_ERR, "Request already processed: request_id=%s", request_id);
        return -1;
    }

    // Update request
    strncpy(request.status, "approved", sizeof(request.status) - 1);
    strncpy(request.approved_by, approver_id, sizeof(request.approved_by) - 1);
    request.approved_at = time(NULL);
    request.expires_at = time(NULL) + (request.duration_hours * 60 * 60);

    // Grant temporary role
    syslog(LOG_INFO, "Temporary role granted: user_id=%s, role=%s, expires_at=%ld",
           request.user_id, request.privileged_role, request.expires_at);

    syslog(LOG_INFO, "Privileged access approved: request_id=%s, approver_id=%s",
           request_id, approver_id);

    // Fill result
    strncpy(result->request_id, request_id, sizeof(result->request_id) - 1);
    strncpy(result->status, "approved", sizeof(result->status) - 1);
    result->expires_at = request.expires_at;

    return 0;
}

int revoke_expired_access() {
    // Query for expired temporary roles and revoke them

    syslog(LOG_INFO, "Expired access revocation completed");

    return 0;
}
```

---

## Success Criteria

- [ ] Authentication system implemented
- [ ] Multi-factor authentication operational
- [ ] RBAC model deployed
- [ ] Privileged access management functional
- [ ] Access reviews scheduled
- [ ] Audit logging comprehensive

---

[← Back to Governance Policies](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
