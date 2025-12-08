---
template_id: compliance_governance_iso27001_csharp
template_name: ISO 27001 Implementation - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 8-10
prerequisites:
  - compliance_frameworks/csharp_soc2_compliance.md
related_templates:
  - risk_management/csharp_risk_assessment.md
tools:
  - ASP.NET Core Identity (authentication)
  - Serilog (logging)
tags:
  - iso27001
  - isms
  - information-security
  - csharp
  - aspnet-core
---

# ISO 27001:2022 Implementation - C#

**Information Security Management System for ASP.NET Core applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### ISO 27001:2022 Structure

**4 Themes**: Organizational (37), People (8), Physical (14), Technological (34)
**Total**: 93 controls

---

## Control 5.15: Access Control

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.ISO27001
{
    /// <summary>
    /// Privileged Access Manager with Just-In-Time (JIT) access.
    ///
    /// ISO 27001 Control 5.15: Access control
    /// ISO 27001 Control 5.16: Identity management
    /// </summary>
    public class PrivilegedAccessManager
    {
        private readonly ILogger<PrivilegedAccessManager> _logger;
        private const int MaxElevationHours = 8;

        public enum PrivilegeLevel
        {
            Standard,
            Elevated,
            Admin,
            SuperAdmin
        }

        public PrivilegedAccessManager(ILogger<PrivilegedAccessManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Request temporary privilege elevation.
        /// </summary>
        public async Task<string> RequestPrivilegeElevation(
            string userId,
            PrivilegeLevel requestedLevel,
            string justification,
            int durationHours = 4)
        {
            if (durationHours > MaxElevationHours)
            {
                throw new ArgumentException($"Maximum elevation period is {MaxElevationHours} hours");
            }

            var requestId = Guid.NewGuid().ToString();
            var expiresAt = DateTime.UtcNow.AddHours(durationHours);

            // Store request in database
            await StorePrivilegeRequest(requestId, userId, requestedLevel, justification, expiresAt);

            _logger.LogWarning("Privilege elevation requested: RequestId={RequestId}, UserId={UserId}, " +
                             "Level={Level}, Duration={Duration}h, Justification={Justification}",
                requestId, userId, requestedLevel, durationHours, justification);

            return requestId;
        }

        /// <summary>
        /// Approve privilege elevation request.
        /// </summary>
        public async Task<ApprovalResult> ApproveElevation(string requestId, string approverId)
        {
            // Retrieve request
            var request = await GetPrivilegeRequest(requestId);

            if (request == null)
            {
                throw new InvalidOperationException("Request not found");
            }

            // Grant temporary privileges
            await GrantTemporaryPrivileges(request.UserId, request.RequestedLevel, request.ExpiresAt);

            _logger.LogWarning("Privilege elevation approved: RequestId={RequestId}, UserId={UserId}, " +
                             "ApproverId={ApproverId}, ExpiresAt={ExpiresAt}",
                requestId, request.UserId, approverId, request.ExpiresAt);

            return new ApprovalResult
            {
                Approved = true,
                ExpiresAt = request.ExpiresAt,
                Message = "Privilege elevation approved"
            };
        }

        /// <summary>
        /// Automatically revoke expired privileges.
        /// </summary>
        public async Task RevokeExpiredPrivileges()
        {
            var expiredUsers = await GetUsersWithExpiredPrivileges();

            foreach (var user in expiredUsers)
            {
                await RevokePrivileges(user.UserId);

                _logger.LogInformation("Expired privileges revoked: UserId={UserId}, " +
                                     "PreviousLevel={PreviousLevel}",
                    user.UserId, user.TemporaryPrivilege);
            }
        }

        private async Task StorePrivilegeRequest(string requestId, string userId,
            PrivilegeLevel level, string justification, DateTime expiresAt)
        {
            // Implementation: Store in database
            await Task.CompletedTask;
        }

        private async Task<PrivilegeRequest> GetPrivilegeRequest(string requestId)
        {
            // Implementation: Retrieve from database
            await Task.CompletedTask;
            return new PrivilegeRequest();
        }

        private async Task GrantTemporaryPrivileges(string userId, PrivilegeLevel level, DateTime expiresAt)
        {
            // Implementation: Update user privileges
            await Task.CompletedTask;
        }

        private async Task<List<UserPrivilege>> GetUsersWithExpiredPrivileges()
        {
            // Implementation: Query expired privileges
            await Task.CompletedTask;
            return new List<UserPrivilege>();
        }

        private async Task RevokePrivileges(string userId)
        {
            // Implementation: Remove temporary privileges
            await Task.CompletedTask;
        }

        public class ApprovalResult
        {
            public bool Approved { get; set; }
            public DateTime ExpiresAt { get; set; }
            public string Message { get; set; }
        }

        private class PrivilegeRequest
        {
            public string UserId { get; set; }
            public PrivilegeLevel RequestedLevel { get; set; }
            public DateTime ExpiresAt { get; set; }
        }

        private class UserPrivilege
        {
            public string UserId { get; set; }
            public PrivilegeLevel TemporaryPrivilege { get; set; }
        }
    }
}
```

---

## Control 5.17: Authentication Information

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Identity;

namespace ComplianceGovernance.ISO27001
{
    /// <summary>
    /// Secure authentication manager.
    ///
    /// ISO 27001 Control 5.17: Authentication information
    /// ISO 27001 Control 5.18: Access rights
    /// </summary>
    public class SecureAuthenticationManager
    {
        private readonly IPasswordHasher<object> _passwordHasher;
        private readonly ILogger<SecureAuthenticationManager> _logger;

        private const int PasswordMinLength = 12;
        private const int PasswordHistorySize = 5;

        public SecureAuthenticationManager(
            IPasswordHasher<object> passwordHasher,
            ILogger<SecureAuthenticationManager> logger)
        {
            _passwordHasher = passwordHasher;
            _logger = logger;
        }

        /// <summary>
        /// Validate password strength.
        ///
        /// ISO 27001 Control 5.17: Password policy enforcement
        /// </summary>
        public ValidationResult ValidatePasswordStrength(string password, UserContext user)
        {
            var violations = new List<string>();

            // Minimum length
            if (password.Length < PasswordMinLength)
            {
                violations.Add($"Password must be at least {PasswordMinLength} characters");
            }

            // Complexity requirements
            if (!Regex.IsMatch(password, @"[A-Z]"))
            {
                violations.Add("Password must contain at least one uppercase letter");
            }

            if (!Regex.IsMatch(password, @"[a-z]"))
            {
                violations.Add("Password must contain at least one lowercase letter");
            }

            if (!Regex.IsMatch(password, @"[0-9]"))
            {
                violations.Add("Password must contain at least one number");
            }

            if (!Regex.IsMatch(password, @"[!@#$%^&*(),.?""':{}|<>]"))
            {
                violations.Add("Password must contain at least one special character");
            }

            // Check against common passwords
            if (IsCommonPassword(password))
            {
                violations.Add("Password is too common");
            }

            // Check password history
            if (user.PasswordHistory != null)
            {
                foreach (var oldHash in user.PasswordHistory)
                {
                    var result = _passwordHasher.VerifyHashedPassword(null, oldHash, password);
                    if (result == PasswordVerificationResult.Success)
                    {
                        violations.Add($"Cannot reuse previous {PasswordHistorySize} passwords");
                        break;
                    }
                }
            }

            var compliant = violations.Count == 0;

            if (!compliant)
            {
                _logger.LogWarning("Password policy violation: UserId={UserId}, Violations={Violations}",
                    user.UserId, string.Join(", ", violations));
            }

            return new ValidationResult { Compliant = compliant, Violations = violations };
        }

        private bool IsCommonPassword(string password)
        {
            var commonPasswords = new[]
            {
                "password", "123456", "12345678", "qwerty", "abc123",
                "password123", "admin", "letmein", "welcome", "1234567890"
            };

            return commonPasswords.Contains(password.ToLower());
        }

        public class ValidationResult
        {
            public bool Compliant { get; set; }
            public List<string> Violations { get; set; }
        }

        public class UserContext
        {
            public string UserId { get; set; }
            public List<string> PasswordHistory { get; set; }
        }
    }
}
```

---

## Control 8.16: Monitoring Activities

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.ISO27001
{
    /// <summary>
    /// Security monitoring system.
    ///
    /// ISO 27001 Control 8.16: Monitoring activities
    /// ISO 27001 Control 8.15: Logging
    /// </summary>
    public class SecurityMonitor
    {
        private readonly ILogger<SecurityMonitor> _logger;

        private const int FailedLoginsThreshold = 5;
        private const int UnusualAccessTimeStart = 2; // 2 AM
        private const int UnusualAccessTimeEnd = 5;   // 5 AM

        public SecurityMonitor(ILogger<SecurityMonitor> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Monitor authentication attempts for anomalies.
        /// </summary>
        public async Task<AnomalyResult> MonitorAuthenticationPatterns(
            string userId,
            int timeWindowMinutes = 60)
        {
            var since = DateTime.UtcNow.AddMinutes(-timeWindowMinutes);
            var authLogs = await GetAuthenticationLogs(userId, since);

            var anomalies = new List<Anomaly>();

            // Check for excessive failed logins
            var failedLogins = authLogs.Count(log => !log.Success);
            if (failedLogins >= FailedLoginsThreshold)
            {
                anomalies.Add(new Anomaly
                {
                    Type = "excessive_failed_logins",
                    Count = failedLogins,
                    Threshold = FailedLoginsThreshold,
                    Severity = "high"
                });
            }

            // Check for unusual access times
            var nightAccess = authLogs.Count(log =>
            {
                var hour = log.Timestamp.Hour;
                return hour >= UnusualAccessTimeStart && hour <= UnusualAccessTimeEnd;
            });

            if (nightAccess > 3)
            {
                anomalies.Add(new Anomaly
                {
                    Type = "unusual_access_time",
                    Count = nightAccess,
                    Severity = "medium"
                });
            }

            // Check for rapid successive logins from different IPs
            var uniqueIPs = authLogs.Select(log => log.IpAddress).Distinct().Count();
            if (uniqueIPs > 5)
            {
                anomalies.Add(new Anomaly
                {
                    Type = "multiple_ip_addresses",
                    Count = uniqueIPs,
                    Severity = "high"
                });
            }

            if (anomalies.Any())
            {
                _logger.LogWarning("Security anomalies detected: UserId={UserId}, AnomalyCount={Count}",
                    userId, anomalies.Count);

                await CreateSecurityIncident(userId, anomalies);
            }

            return new AnomalyResult
            {
                AnomaliesDetected = anomalies.Any(),
                Anomalies = anomalies
            };
        }

        private async Task<List<AuthLog>> GetAuthenticationLogs(string userId, DateTime since)
        {
            // Implementation: Query authentication logs
            await Task.CompletedTask;
            return new List<AuthLog>();
        }

        private async Task CreateSecurityIncident(string userId, List<Anomaly> anomalies)
        {
            var incidentId = Guid.NewGuid().ToString();

            _logger.LogError("Security incident created: IncidentId={IncidentId}, UserId={UserId}",
                incidentId, userId);

            await Task.CompletedTask;
        }

        public class AnomalyResult
        {
            public bool AnomaliesDetected { get; set; }
            public List<Anomaly> Anomalies { get; set; }
        }

        public class Anomaly
        {
            public string Type { get; set; }
            public int Count { get; set; }
            public int? Threshold { get; set; }
            public string Severity { get; set; }
        }

        private class AuthLog
        {
            public DateTime Timestamp { get; set; }
            public bool Success { get; set; }
            public string IpAddress { get; set; }
        }
    }
}
```

---

## Success Criteria

- [ ] Privileged access requires justification and approval
- [ ] Temporary privileges auto-revoked after expiration
- [ ] Password policy enforced (12+ chars, complexity, history)
- [ ] Configuration changes tracked and audited
- [ ] Security monitoring detects anomalies
- [ ] Authentication patterns analyzed for threats

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
