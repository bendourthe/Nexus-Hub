---
template_id: compliance_governance_access_control_csharp
template_name: Access Control - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: governance_policies
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - governance_policies/csharp_security_policies.md
  - compliance_frameworks/csharp_soc2_compliance.md
related_templates:
  - compliance_frameworks/csharp_iso27001_implementation.md
tools:
  - ASP.NET Identity
  - JWT Bearer Authentication
tags:
  - access-control
  - rbac
  - least-privilege
  - authentication
  - authorization
  - csharp
---

# Access Control - C#

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

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Identity;
using Microsoft.Extensions.Logging;

namespace Organization.Security
{
    public class AuthenticationResult
    {
        public string SessionToken { get; set; }
        public string UserId { get; set; }
        public DateTime ExpiresAt { get; set; }
        public bool MfaRequired { get; set; }
    }

    public class AuthenticationService
    {
        private readonly ILogger<AuthenticationService> _logger;
        private readonly IPasswordHasher<string> _passwordHasher;

        // Password policy
        private const int PasswordMinLength = 12;
        private const int PasswordMaxAgeDays = 90;
        private const int AccountLockoutThreshold = 5;
        private const int LockoutDurationMinutes = 30;

        public AuthenticationService(ILogger<AuthenticationService> logger)
        {
            _logger = logger;
            _passwordHasher = new PasswordHasher<string>();
        }

        public async Task<AuthenticationResult> Authenticate(
            string username,
            string password,
            string mfaToken = null)
        {
            // var user = await _userRepository.GetByUsernameAsync(username);

            // Simulated user retrieval
            var user = new Dictionary<string, object>
            {
                ["user_id"] = Guid.NewGuid().ToString(),
                ["username"] = username,
                ["password_hash"] = _passwordHasher.HashPassword(username, "demo_password"),
                ["mfa_enabled"] = true,
                ["failed_login_attempts"] = 0,
                ["account_locked_until"] = (DateTime?)null
            };

            // Check account locked
            if (IsAccountLocked(user))
            {
                _logger.LogWarning(
                    "Authentication failed: account locked - user_id={UserId}, username={Username}",
                    user["user_id"], username);
                throw new SecurityException("Account locked due to failed login attempts");
            }

            // Verify password
            var passwordHash = user["password_hash"] as string;
            var verificationResult = _passwordHasher.VerifyHashedPassword(
                username, passwordHash, password);

            if (verificationResult == PasswordVerificationResult.Failed)
            {
                await RecordFailedLogin(user["user_id"].ToString(), "invalid_password");
                throw new SecurityException("Invalid credentials");
            }

            // Check MFA if enabled
            var mfaEnabled = (bool)user["mfa_enabled"];
            if (mfaEnabled && string.IsNullOrEmpty(mfaToken))
            {
                return new AuthenticationResult
                {
                    UserId = user["user_id"].ToString(),
                    MfaRequired = true
                };
            }

            if (mfaEnabled && !VerifyMFAToken(user["user_id"].ToString(), mfaToken))
            {
                await RecordFailedLogin(user["user_id"].ToString(), "invalid_mfa");
                throw new SecurityException("Invalid MFA token");
            }

            // Create session
            var sessionToken = GenerateSessionToken();
            var expiresAt = DateTime.UtcNow.AddHours(8);

            // Reset failed login attempts
            // await _userRepository.ResetFailedAttemptsAsync(user["user_id"].ToString());

            _logger.LogInformation(
                "Authentication successful: user_id={UserId}, username={Username}",
                user["user_id"], username);

            return new AuthenticationResult
            {
                SessionToken = sessionToken,
                UserId = user["user_id"].ToString(),
                ExpiresAt = expiresAt,
                MfaRequired = false
            };
        }

        private bool IsAccountLocked(Dictionary<string, object> user)
        {
            var failedAttempts = (int)user["failed_login_attempts"];
            if (failedAttempts >= AccountLockoutThreshold)
            {
                var lockedUntil = user["account_locked_until"] as DateTime?;
                if (lockedUntil.HasValue && DateTime.UtcNow < lockedUntil.Value)
                {
                    return true;
                }
            }
            return false;
        }

        private async Task RecordFailedLogin(string userId, string reason)
        {
            // await _userRepository.IncrementFailedAttemptsAsync(userId);

            _logger.LogWarning("Failed login attempt: user_id={UserId}, reason={Reason}",
                userId, reason);

            // Check if should lock account
            // if (attempts >= AccountLockoutThreshold)
            // {
            //     await _userRepository.LockAccountAsync(userId, LockoutDurationMinutes);
            // }

            await Task.CompletedTask;
        }

        private bool VerifyMFAToken(string userId, string token)
        {
            // TOTP verification logic
            // Use OtpNet or similar library
            return true; // Simplified
        }

        private string GenerateSessionToken()
        {
            return Guid.NewGuid().ToString();
        }

        public bool ValidatePassword(string password)
        {
            if (password.Length < PasswordMinLength)
            {
                return false;
            }

            // Check complexity: uppercase, lowercase, digit, special char
            var hasUpper = password.Any(char.IsUpper);
            var hasLower = password.Any(char.IsLower);
            var hasDigit = password.Any(char.IsDigit);
            var hasSpecial = password.Any(ch => !char.IsLetterOrDigit(ch));

            return hasUpper && hasLower && hasDigit && hasSpecial;
        }
    }
}
```

---

## RBAC Implementation

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.Security
{
    public class Role
    {
        public string RoleId { get; set; }
        public string RoleName { get; set; }
        public string Description { get; set; }
        public List<string> Permissions { get; set; }
        public DateTime CreatedDate { get; set; }
    }

    public class RBACService
    {
        private readonly ILogger<RBACService> _logger;

        public RBACService(ILogger<RBACService> logger)
        {
            _logger = logger;
        }

        public async Task<string> CreateRole(
            string roleName,
            string description,
            List<string> permissions)
        {
            var roleId = Guid.NewGuid().ToString();

            var role = new Role
            {
                RoleId = roleId,
                RoleName = roleName,
                Description = description,
                Permissions = permissions,
                CreatedDate = DateTime.UtcNow
            };

            // await _roleRepository.InsertAsync(role);

            _logger.LogInformation(
                "Role created: role_id={RoleId}, role_name={RoleName}, permissions={Permissions}",
                roleId, roleName, string.Join(", ", permissions));

            return roleId;
        }

        public async Task AssignRoleToUser(string userId, string roleId)
        {
            // await _userRoleRepository.InsertAsync(userId, roleId);

            _logger.LogInformation("Role assigned: user_id={UserId}, role_id={RoleId}",
                userId, roleId);

            await Task.CompletedTask;
        }

        public async Task<List<string>> GetUserRoles(string userId)
        {
            // return await _userRoleRepository.FindByUserIdAsync(userId);

            // Simulated
            var roles = new List<string> { "developer", "security_reviewer" };

            await Task.CompletedTask;
            return roles;
        }

        public async Task<List<string>> GetUserPermissions(string userId)
        {
            var roles = await GetUserRoles(userId);
            var allPermissions = new HashSet<string>();

            foreach (var roleId in roles)
            {
                // var role = await _roleRepository.GetByIdAsync(roleId);
                // allPermissions.UnionWith(role.Permissions);

                // Simulated permissions
                if (roleId == "developer")
                {
                    allPermissions.UnionWith(new[]
                    {
                        "code:read", "code:write", "deploy:dev", "logs:read"
                    });
                }
                else if (roleId == "security_reviewer")
                {
                    allPermissions.UnionWith(new[]
                    {
                        "audit_logs:read", "security_reports:read", "vulnerabilities:read"
                    });
                }
            }

            _logger.LogInformation(
                "Permissions retrieved: user_id={UserId}, permission_count={Count}",
                userId, allPermissions.Count);

            return allPermissions.ToList();
        }

        public async Task<bool> HasPermission(string userId, string permission)
        {
            var permissions = await GetUserPermissions(userId);
            var hasPermission = permissions.Contains(permission);

            _logger.LogInformation(
                "Permission check: user_id={UserId}, permission={Permission}, granted={Granted}",
                userId, permission, hasPermission);

            return hasPermission;
        }

        public async Task<object> CheckAccess(
            string userId,
            string resource,
            string action)
        {
            var requiredPermission = $"{resource}:{action}";
            var granted = await HasPermission(userId, requiredPermission);

            if (!granted)
            {
                _logger.LogWarning(
                    "Access denied: user_id={UserId}, resource={Resource}, action={Action}",
                    userId, resource, action);
            }
            else
            {
                _logger.LogInformation(
                    "Access granted: user_id={UserId}, resource={Resource}, action={Action}",
                    userId, resource, action);
            }

            return new
            {
                UserId = userId,
                Resource = resource,
                Action = action,
                Granted = granted,
                Timestamp = DateTime.UtcNow
            };
        }
    }
}
```

---

## Privileged Access Management

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.Security
{
    public class PrivilegedAccessRequest
    {
        public string RequestId { get; set; }
        public string UserId { get; set; }
        public string PrivilegedRole { get; set; }
        public string Justification { get; set; }
        public int DurationHours { get; set; }
        public DateTime RequestedAt { get; set; }
        public string Status { get; set; } // pending, approved, denied, expired
        public string ApprovedBy { get; set; }
        public DateTime? ApprovedAt { get; set; }
        public DateTime? ExpiresAt { get; set; }
    }

    public class PrivilegedAccessService
    {
        private readonly ILogger<PrivilegedAccessService> _logger;

        public PrivilegedAccessService(ILogger<PrivilegedAccessService> logger)
        {
            _logger = logger;
        }

        public async Task<string> RequestPrivilegedAccess(
            string userId,
            string privilegedRole,
            string justification,
            int durationHours)
        {
            var requestId = Guid.NewGuid().ToString();

            var request = new PrivilegedAccessRequest
            {
                RequestId = requestId,
                UserId = userId,
                PrivilegedRole = privilegedRole,
                Justification = justification,
                DurationHours = durationHours,
                RequestedAt = DateTime.UtcNow,
                Status = "pending"
            };

            // await _privilegedAccessRepository.InsertAsync(request);

            // Notify approvers
            await NotifyApprovers(requestId, privilegedRole);

            _logger.LogInformation(
                "Privileged access requested: request_id={RequestId}, user_id={UserId}, role={Role}",
                requestId, userId, privilegedRole);

            return requestId;
        }

        public async Task<object> ApprovePrivilegedAccess(
            string requestId,
            string approverId)
        {
            // var request = await _privilegedAccessRepository.GetByIdAsync(requestId);

            var request = new PrivilegedAccessRequest
            {
                RequestId = requestId,
                UserId = "user123",
                PrivilegedRole = "production_admin",
                DurationHours = 8,
                Status = "pending"
            };

            if (request.Status != "pending")
            {
                throw new InvalidOperationException("Request already processed");
            }

            request.Status = "approved";
            request.ApprovedBy = approverId;
            request.ApprovedAt = DateTime.UtcNow;
            request.ExpiresAt = DateTime.UtcNow.AddHours(request.DurationHours);

            // await _privilegedAccessRepository.UpdateAsync(request);

            // Grant temporary role
            await GrantTemporaryRole(request.UserId, request.PrivilegedRole, request.DurationHours);

            _logger.LogInformation(
                "Privileged access approved: request_id={RequestId}, approver_id={ApproverId}",
                requestId, approverId);

            return new
            {
                RequestId = requestId,
                Status = "approved",
                ExpiresAt = request.ExpiresAt
            };
        }

        private async Task GrantTemporaryRole(string userId, string role, int durationHours)
        {
            var expiresAt = DateTime.UtcNow.AddHours(durationHours);

            // await _temporaryRoleRepository.InsertAsync(userId, role, expiresAt);

            _logger.LogInformation(
                "Temporary role granted: user_id={UserId}, role={Role}, expires_at={ExpiresAt}",
                userId, role, expiresAt);

            await Task.CompletedTask;
        }

        private async Task NotifyApprovers(string requestId, string privilegedRole)
        {
            _logger.LogInformation(
                "Notifying approvers: request_id={RequestId}, role={Role}",
                requestId, privilegedRole);
            // Email/notification logic
            await Task.CompletedTask;
        }

        public async Task RevokeExpiredAccess()
        {
            // var expiredRoles = await _temporaryRoleRepository.FindExpiredAsync();

            // foreach (var role in expiredRoles)
            // {
            //     await _temporaryRoleRepository.DeleteAsync(role);
            //     _logger.LogInformation(
            //         "Expired role revoked: user_id={UserId}, role={Role}",
            //         role.UserId, role.Role);
            // }

            _logger.LogInformation("Expired access revocation completed");

            await Task.CompletedTask;
        }
    }
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
