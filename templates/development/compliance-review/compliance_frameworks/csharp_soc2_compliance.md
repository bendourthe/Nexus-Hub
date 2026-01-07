---
template_id: compliance_governance_soc2_compliance_csharp
template_name: SOC 2 Type II Compliance - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: compliance_frameworks
phase_number: 1
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - compliance_frameworks/README.md
related_templates:
  - compliance_frameworks/csharp_iso27001_implementation.md
tools:
  - ASP.NET Core (web framework)
  - Serilog (logging)
  - IdentityServer (authentication)
tags:
  - soc2
  - trust-service-criteria
  - compliance
  - csharp
  - dotnet
---

# SOC 2 Type II Compliance - C#

**Implement Trust Service Criteria for ASP.NET Core applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Trust Service Criteria

1. **Security (CC)** - Common Criteria (required)
2. **Availability** - System uptime/performance
3. **Confidentiality** - Sensitive data protection
4. **Processing Integrity** - Accurate processing
5. **Privacy** - Personal information protection

---

## CC6.1: Logical Access Controls

```csharp
using System;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Logging;
using OtpNet;

namespace Company.Compliance.Security
{
    /// <summary>
    /// Multi-factor authentication manager.
    /// SOC 2 Control: CC6.1 - Multi-factor authentication
    /// </summary>
    public class MFAManager
    {
        private readonly ILogger<MFAManager> _logger;

        public MFAManager(ILogger<MFAManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Generate MFA secret for user enrollment.
        /// </summary>
        public EnrollmentResponse EnrollUser(string userId, string userEmail)
        {
            // Generate secret
            var secret = KeyGeneration.GenerateRandomKey(20);
            var base32Secret = Base32Encoding.ToString(secret);

            // Generate QR code URI
            var issuer = "YourApp";
            var qrCodeUri = $"otpauth://totp/{issuer}:{userEmail}?secret={base32Secret}&issuer={issuer}";

            // Store encrypted secret in database
            var encryptedSecret = EncryptSecret(base32Secret);

            _logger.LogInformation("MFA enrollment initiated: UserId={UserId}, Timestamp={Timestamp}",
                userId, DateTime.UtcNow);

            return new EnrollmentResponse
            {
                Secret = base32Secret,
                QrCodeUri = qrCodeUri,
                EncryptedSecret = encryptedSecret
            };
        }

        /// <summary>
        /// Verify MFA token during login.
        /// </summary>
        public VerificationResult VerifyToken(string userId, string token)
        {
            // Retrieve encrypted secret from database
            var encryptedSecret = GetUserMFASecret(userId);

            if (string.IsNullOrEmpty(encryptedSecret))
            {
                _logger.LogWarning("MFA verification failed: UserId={UserId}, Reason=MfaNotEnabled",
                    userId);
                return new VerificationResult { IsValid = false, Message = "MFA not enabled" };
            }

            var secret = DecryptSecret(encryptedSecret);
            var secretBytes = Base32Encoding.ToBytes(secret);

            var totp = new Totp(secretBytes);
            var isValid = totp.VerifyTotp(token, out long timeStepMatched, VerificationWindow.RfcSpecifiedNetworkDelay);

            _logger.LogInformation("MFA verification attempt: UserId={UserId}, Success={Success}, " +
                                  "Timestamp={Timestamp}",
                userId, isValid, DateTime.UtcNow);

            if (!isValid)
            {
                RecordFailedAttempt(userId);
            }

            return new VerificationResult
            {
                IsValid = isValid,
                Message = isValid ? "Verified" : "Invalid token"
            };
        }

        private string EncryptSecret(string secret)
        {
            // Implementation: AES-256-GCM encryption
            using var aes = Aes.Create();
            aes.KeySize = 256;
            aes.GenerateKey();
            aes.GenerateIV();

            using var encryptor = aes.CreateEncryptor();
            var secretBytes = Encoding.UTF8.GetBytes(secret);
            var encrypted = encryptor.TransformFinalBlock(secretBytes, 0, secretBytes.Length);

            return Convert.ToBase64String(encrypted);
        }

        private string DecryptSecret(string encryptedSecret)
        {
            // Implementation: AES-256-GCM decryption
            return encryptedSecret; // Simplified
        }

        private void RecordFailedAttempt(string userId)
        {
            // Check for brute force attack
            var recentAttempts = CountRecentFailedAttempts(userId, 15);

            if (recentAttempts >= 5)
            {
                _logger.LogWarning("Potential MFA brute force attack: UserId={UserId}, " +
                                  "AttemptCount={AttemptCount}",
                    userId, recentAttempts);
                LockAccount(userId, 30);
            }
        }

        private int CountRecentFailedAttempts(string userId, int minutes)
        {
            // Implementation: Query database
            return 0;
        }

        private void LockAccount(string userId, int minutes)
        {
            // Implementation: Lock account temporarily
            _logger.LogWarning("Account locked: UserId={UserId}, DurationMinutes={DurationMinutes}",
                userId, minutes);
        }

        private string GetUserMFASecret(string userId)
        {
            // Implementation: Retrieve from database
            return null;
        }

        public class EnrollmentResponse
        {
            public string Secret { get; set; }
            public string QrCodeUri { get; set; }
            public string EncryptedSecret { get; set; }
        }

        public class VerificationResult
        {
            public bool IsValid { get; set; }
            public string Message { get; set; }
        }
    }
}
```

## CC6.7: Encryption of Confidential Data

```csharp
using System;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Extensions.Logging;

namespace Company.Compliance.Security
{
    /// <summary>
    /// Data encryption manager for protecting confidential data.
    /// SOC 2 Control: CC6.7 - Data encryption at rest
    /// Standard: AES-256-GCM
    /// </summary>
    public class DataEncryptionManager
    {
        private readonly ILogger<DataEncryptionManager> _logger;

        public DataEncryptionManager(ILogger<DataEncryptionManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Encrypt sensitive data at rest.
        /// </summary>
        public EncryptedData EncryptData(string plaintext, Dictionary<string, string> context = null)
        {
            using var aes = new AesGcm(GenerateKey());

            var nonce = new byte[AesGcm.NonceByteSizes.MaxSize];
            RandomNumberGenerator.Fill(nonce);

            var plaintextBytes = Encoding.UTF8.GetBytes(plaintext);
            var ciphertext = new byte[plaintextBytes.Length];
            var tag = new byte[AesGcm.TagByteSizes.MaxSize];

            // Encrypt
            aes.Encrypt(nonce, plaintextBytes, ciphertext, tag);

            _logger.LogInformation("Data encrypted: Algorithm=AES-256-GCM, Context={Context}, " +
                                  "Timestamp={Timestamp}",
                context, DateTime.UtcNow);

            return new EncryptedData
            {
                Ciphertext = Convert.ToBase64String(ciphertext),
                Nonce = Convert.ToBase64String(nonce),
                Tag = Convert.ToBase64String(tag),
                Algorithm = "AES-256-GCM",
                Context = context
            };
        }

        /// <summary>
        /// Decrypt sensitive data.
        /// </summary>
        public string DecryptData(EncryptedData encryptedData)
        {
            using var aes = new AesGcm(RetrieveKey());

            var nonce = Convert.FromBase64String(encryptedData.Nonce);
            var ciphertext = Convert.FromBase64String(encryptedData.Ciphertext);
            var tag = Convert.FromBase64String(encryptedData.Tag);
            var plaintext = new byte[ciphertext.Length];

            // Decrypt
            aes.Decrypt(nonce, ciphertext, tag, plaintext);

            _logger.LogInformation("Data decrypted: Context={Context}, Timestamp={Timestamp}",
                encryptedData.Context, DateTime.UtcNow);

            return Encoding.UTF8.GetString(plaintext);
        }

        private byte[] GenerateKey()
        {
            var key = new byte[32]; // 256 bits
            RandomNumberGenerator.Fill(key);
            return key;
        }

        private byte[] RetrieveKey()
        {
            // Implementation: Retrieve from key management service
            return new byte[32];
        }

        public class EncryptedData
        {
            public string Ciphertext { get; set; }
            public string Nonce { get; set; }
            public string Tag { get; set; }
            public string Algorithm { get; set; }
            public Dictionary<string, string> Context { get; set; }
        }
    }
}
```

## CC7.2: System Monitoring

```csharp
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Prometheus;

namespace Company.Compliance.Monitoring
{
    /// <summary>
    /// Security event monitoring and alerting.
    /// SOC 2 Control: CC7.2 - Security event logging
    /// </summary>
    public class SecurityMonitoring
    {
        private readonly ILogger<SecurityMonitoring> _logger;
        private readonly Counter _securityEventsCounter;
        private readonly Counter _authenticationAttemptsCounter;

        public SecurityMonitoring(ILogger<SecurityMonitoring> logger)
        {
            _logger = logger;

            _securityEventsCounter = Metrics.CreateCounter(
                "security_events_total",
                "Total security events by type",
                new CounterConfiguration
                {
                    LabelNames = new[] { "event_type", "severity" }
                });

            _authenticationAttemptsCounter = Metrics.CreateCounter(
                "authentication_attempts_total",
                "Total authentication attempts",
                new CounterConfiguration
                {
                    LabelNames = new[] { "result" }
                });
        }

        /// <summary>
        /// Log security event with structured data.
        /// </summary>
        public void LogSecurityEvent(string eventType, string severity,
                                     Dictionary<string, object> details)
        {
            var eventData = new Dictionary<string, object>(details)
            {
                ["event"] = eventType,
                ["severity"] = severity,
                ["timestamp"] = DateTime.UtcNow
            };

            _logger.LogInformation("Security event: {@Event}", eventData);

            _securityEventsCounter.WithLabels(eventType, severity).Inc();

            if (severity == "critical")
            {
                SendSecurityAlert(eventData);
            }
        }

        /// <summary>
        /// Log authentication attempt.
        /// </summary>
        public void LogAuthenticationAttempt(string userId, string result,
                                            Dictionary<string, object> details)
        {
            var eventData = new Dictionary<string, object>(details)
            {
                ["event"] = "authentication_attempt",
                ["userId"] = userId,
                ["result"] = result,
                ["timestamp"] = DateTime.UtcNow
            };

            _logger.LogInformation("Authentication attempt: {@Event}", eventData);

            _authenticationAttemptsCounter.WithLabels(result).Inc();

            if (result == "failure")
            {
                CheckForBruteForce(userId);
            }
        }

        private void CheckForBruteForce(string userId)
        {
            // Implementation: Check failure rate
            var recentFailures = CountRecentFailures(userId, 15);

            if (recentFailures >= 5)
            {
                LogSecurityEvent("brute_force_detected", "critical",
                    new Dictionary<string, object>
                    {
                        ["userId"] = userId,
                        ["failureCount"] = recentFailures
                    });

                LockAccount(userId);
            }
        }

        private void SendSecurityAlert(Dictionary<string, object> eventData)
        {
            _logger.LogCritical("CRITICAL SECURITY ALERT: {@Event}", eventData);
            // Implementation: Integrate with PagerDuty, Slack, etc.
        }

        private int CountRecentFailures(string userId, int minutes)
        {
            // Implementation: Query database
            return 0;
        }

        private void LockAccount(string userId)
        {
            _logger.LogWarning("Account locked due to brute force: UserId={UserId}", userId);
        }
    }
}
```

---

## Success Criteria

- [ ] Multi-factor authentication enforced
- [ ] All sensitive data encrypted at rest (AES-256-GCM)
- [ ] HTTPS enforced with TLS 1.3
- [ ] Security events logged
- [ ] Failed authentication monitored
- [ ] Health monitoring operational

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
