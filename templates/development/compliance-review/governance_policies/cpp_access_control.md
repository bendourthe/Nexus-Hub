---
template_id: compliance_governance_access_control_cpp
template_name: Access Control - C++
version: 1.0.0
last_updated: 2025-12-05
language: cpp
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/cpp_security_policies.md
  - compliance_frameworks/cpp_soc2_compliance.md
related_templates:
  - compliance_frameworks/cpp_iso27001_implementation.md
tools:
  - spdlog (logging)
  - bcrypt (password hashing)
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - cpp
---

# Access Control - C++

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

```cpp
#include <string>
#include <memory>
#include <chrono>
#include <sstream>
#include <regex>
#include <spdlog/spdlog.h>

constexpr int PASSWORD_MIN_LENGTH = 12;
constexpr int PASSWORD_MAX_AGE_DAYS = 90;
constexpr int ACCOUNT_LOCKOUT_THRESHOLD = 5;
constexpr int LOCKOUT_DURATION_MINUTES = 30;

struct AuthenticationResult {
    std::string sessionToken;
    std::string userId;
    std::chrono::system_clock::time_point expiresAt;
    bool mfaRequired;
};

struct User {
    std::string userId;
    std::string username;
    std::string passwordHash;
    bool mfaEnabled;
    int failedLoginAttempts;
    std::chrono::system_clock::time_point accountLockedUntil;
};

class AuthenticationService {
private:
    std::shared_ptr<spdlog::logger> logger;

    bool isAccountLocked(const User& user) const {
        if (user.failedLoginAttempts >= ACCOUNT_LOCKOUT_THRESHOLD) {
            auto now = std::chrono::system_clock::now();
            if (user.accountLockedUntil > now) {
                return true;
            }
        }
        return false;
    }

    void recordFailedLogin(const std::string& userId, const std::string& reason) {
        logger->warn("Failed login attempt: user_id={}, reason={}", userId, reason);

        // In production: increment failed_login_attempts in database
        // and potentially lock account if threshold reached
    }

    bool verifyPassword(const std::string& password, const std::string& passwordHash) const {
        // In production: use bcrypt or similar
        return true; // Simplified
    }

    bool verifyMFAToken(const std::string& userId, const std::string& token) const {
        // TOTP verification logic
        return true; // Simplified
    }

    std::string generateSessionToken() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "SESSION-" << timestamp;
        return ss.str();
    }

public:
    AuthenticationService(std::shared_ptr<spdlog::logger> logger)
        : logger(logger) {}

    AuthenticationResult authenticate(
        const std::string& username,
        const std::string& password,
        const std::string& mfaToken = "") {

        // Retrieve user (simulated)
        User user;
        user.userId = "USER-" + std::to_string(
            std::chrono::system_clock::now().time_since_epoch().count()
        );
        user.username = username;
        user.passwordHash = "$2b$12$hashed_password";
        user.mfaEnabled = true;
        user.failedLoginAttempts = 0;
        user.accountLockedUntil = std::chrono::system_clock::time_point::min();

        // Check account locked
        if (isAccountLocked(user)) {
            logger->warn("Authentication failed: account locked - user_id={}, username={}",
                        user.userId, username);
            throw std::runtime_error("Account locked due to failed login attempts");
        }

        // Verify password
        if (!verifyPassword(password, user.passwordHash)) {
            recordFailedLogin(user.userId, "invalid_password");
            throw std::runtime_error("Invalid credentials");
        }

        // Check MFA if enabled
        if (user.mfaEnabled && mfaToken.empty()) {
            AuthenticationResult result;
            result.userId = user.userId;
            result.mfaRequired = true;
            return result;
        }

        if (user.mfaEnabled && !verifyMFAToken(user.userId, mfaToken)) {
            recordFailedLogin(user.userId, "invalid_mfa");
            throw std::runtime_error("Invalid MFA token");
        }

        // Create session
        AuthenticationResult result;
        result.sessionToken = generateSessionToken();
        result.userId = user.userId;
        result.expiresAt = std::chrono::system_clock::now() + std::chrono::hours(8);
        result.mfaRequired = false;

        logger->info("Authentication successful: user_id={}, username={}",
                    user.userId, username);

        return result;
    }

    bool validatePassword(const std::string& password) const {
        if (password.length() < PASSWORD_MIN_LENGTH) {
            return false;
        }

        // Check complexity using regex
        std::regex hasUpper("[A-Z]");
        std::regex hasLower("[a-z]");
        std::regex hasDigit("[0-9]");
        std::regex hasSpecial("[^A-Za-z0-9]");

        return std::regex_search(password, hasUpper) &&
               std::regex_search(password, hasLower) &&
               std::regex_search(password, hasDigit) &&
               std::regex_search(password, hasSpecial);
    }
};
```

---

## RBAC Implementation

```cpp
#include <string>
#include <vector>
#include <set>
#include <memory>
#include <map>
#include <spdlog/spdlog.h>

struct Role {
    std::string roleId;
    std::string roleName;
    std::string description;
    std::vector<std::string> permissions;
    std::chrono::system_clock::time_point createdDate;
};

class RBACService {
private:
    std::shared_ptr<spdlog::logger> logger;

    std::string generateRoleId() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "ROLE-" << timestamp;
        return ss.str();
    }

public:
    RBACService(std::shared_ptr<spdlog::logger> logger)
        : logger(logger) {}

    std::string createRole(
        const std::string& roleName,
        const std::string& description,
        const std::vector<std::string>& permissions) {

        std::string roleId = generateRoleId();

        Role role;
        role.roleId = roleId;
        role.roleName = roleName;
        role.description = description;
        role.permissions = permissions;
        role.createdDate = std::chrono::system_clock::now();

        // Save to repository

        logger->info("Role created: role_id={}, role_name={}, permission_count={}",
                    roleId, roleName, permissions.size());

        return roleId;
    }

    void assignRoleToUser(const std::string& userId, const std::string& roleId) {
        // Insert into user_roles table

        logger->info("Role assigned: user_id={}, role_id={}", userId, roleId);
    }

    std::vector<std::string> getUserRoles(const std::string& userId) {
        // Query user_roles table

        // Simulated
        return {"developer", "security_reviewer"};
    }

    std::vector<std::string> getUserPermissions(const std::string& userId) {
        auto roles = getUserRoles(userId);
        std::set<std::string> permissionSet;

        for (const auto& roleId : roles) {
            // Retrieve role and add permissions
            // Role role = roleRepository.getById(roleId);
            // permissionSet.insert(role.permissions.begin(), role.permissions.end());

            // Simulated permissions
            if (roleId == "developer") {
                permissionSet.insert("code:read");
                permissionSet.insert("code:write");
                permissionSet.insert("deploy:dev");
                permissionSet.insert("logs:read");
            } else if (roleId == "security_reviewer") {
                permissionSet.insert("audit_logs:read");
                permissionSet.insert("security_reports:read");
                permissionSet.insert("vulnerabilities:read");
            }
        }

        std::vector<std::string> permissions(permissionSet.begin(), permissionSet.end());

        logger->info("Permissions retrieved: user_id={}, permission_count={}",
                    userId, permissions.size());

        return permissions;
    }

    bool hasPermission(const std::string& userId, const std::string& permission) {
        auto permissions = getUserPermissions(userId);
        bool hasPermission = std::find(permissions.begin(), permissions.end(), permission)
                           != permissions.end();

        logger->info("Permission check: user_id={}, permission={}, granted={}",
                    userId, permission, hasPermission);

        return hasPermission;
    }

    std::map<std::string, std::string> checkAccess(
        const std::string& userId,
        const std::string& resource,
        const std::string& action) {

        std::string requiredPermission = resource + ":" + action;
        bool granted = hasPermission(userId, requiredPermission);

        if (!granted) {
            logger->warn("Access denied: user_id={}, resource={}, action={}",
                        userId, resource, action);
        } else {
            logger->info("Access granted: user_id={}, resource={}, action={}",
                        userId, resource, action);
        }

        std::map<std::string, std::string> result;
        result["user_id"] = userId;
        result["resource"] = resource;
        result["action"] = action;
        result["granted"] = granted ? "true" : "false";
        return result;
    }
};
```

---

## Privileged Access Management

```cpp
#include <string>
#include <memory>
#include <chrono>
#include <spdlog/spdlog.h>

struct PrivilegedAccessRequest {
    std::string requestId;
    std::string userId;
    std::string privilegedRole;
    std::string justification;
    int durationHours;
    std::chrono::system_clock::time_point requestedAt;
    std::string status; // pending, approved, denied, expired
    std::string approvedBy;
    std::chrono::system_clock::time_point approvedAt;
    std::chrono::system_clock::time_point expiresAt;
};

class PrivilegedAccessService {
private:
    std::shared_ptr<spdlog::logger> logger;

    std::string generateRequestId() const {
        auto now = std::chrono::system_clock::now();
        auto timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()
        ).count();

        std::stringstream ss;
        ss << "PRIVREQ-" << timestamp;
        return ss.str();
    }

    void notifyApprovers(const std::string& requestId, const std::string& privilegedRole) {
        logger->info("Notifying approvers: request_id={}, role={}",
                    requestId, privilegedRole);
        // Email/notification logic
    }

    void grantTemporaryRole(
        const std::string& userId,
        const std::string& role,
        int durationHours) {

        auto expiresAt = std::chrono::system_clock::now() +
                        std::chrono::hours(durationHours);

        // Insert into temporary_roles table

        logger->info("Temporary role granted: user_id={}, role={}, expires_at={}",
                    userId, role,
                    std::chrono::system_clock::to_time_t(expiresAt));
    }

public:
    PrivilegedAccessService(std::shared_ptr<spdlog::logger> logger)
        : logger(logger) {}

    std::string requestPrivilegedAccess(
        const std::string& userId,
        const std::string& privilegedRole,
        const std::string& justification,
        int durationHours) {

        std::string requestId = generateRequestId();

        PrivilegedAccessRequest request;
        request.requestId = requestId;
        request.userId = userId;
        request.privilegedRole = privilegedRole;
        request.justification = justification;
        request.durationHours = durationHours;
        request.requestedAt = std::chrono::system_clock::now();
        request.status = "pending";

        // Save to repository

        notifyApprovers(requestId, privilegedRole);

        logger->info("Privileged access requested: request_id={}, user_id={}, role={}",
                    requestId, userId, privilegedRole);

        return requestId;
    }

    std::map<std::string, std::string> approvePrivilegedAccess(
        const std::string& requestId,
        const std::string& approverId) {

        // Retrieve request (simulated)
        PrivilegedAccessRequest request;
        request.requestId = requestId;
        request.userId = "user123";
        request.privilegedRole = "production_admin";
        request.durationHours = 8;
        request.status = "pending";

        if (request.status != "pending") {
            throw std::runtime_error("Request already processed");
        }

        request.status = "approved";
        request.approvedBy = approverId;
        request.approvedAt = std::chrono::system_clock::now();
        request.expiresAt = std::chrono::system_clock::now() +
                           std::chrono::hours(request.durationHours);

        // Update repository

        grantTemporaryRole(request.userId, request.privilegedRole, request.durationHours);

        logger->info("Privileged access approved: request_id={}, approver_id={}",
                    requestId, approverId);

        std::map<std::string, std::string> result;
        result["request_id"] = requestId;
        result["status"] = "approved";
        return result;
    }

    void revokeExpiredAccess() {
        // Query for expired temporary roles and revoke them

        logger->info("Expired access revocation completed");
    }
};
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
