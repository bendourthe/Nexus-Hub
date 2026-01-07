---
template_id: compliance_governance_pci_dss_csharp
template_name: PCI-DSS v4.0 Compliance - C#
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
  - governance_policies/csharp_access_control.md
tools:
  - ASP.NET Core (web framework)
  - Bouncy Castle (.NET cryptography)
tags:
  - pci-dss
  - payment-security
  - cardholder-data
  - csharp
  - aspnet-core
---

# PCI-DSS v4.0 Compliance - C#

**Payment Card Industry Data Security Standard for ASP.NET Core applications**

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### PCI-DSS v4.0 Requirements

**12 Core Requirements** for protecting payment card data in .NET applications.

---

## Requirement 3: Protect Stored Account Data

```csharp
using System;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.PCI
{
    /// <summary>
    /// Card Data Protection Manager for PCI-DSS compliance.
    ///
    /// PCI-DSS Requirement 3: Protect stored account data
    /// PCI-DSS Requirement 3.3: Mask PAN when displayed
    /// PCI-DSS Requirement 3.4: Render PAN unreadable
    /// </summary>
    public class CardDataProtectionManager
    {
        private readonly ILogger<CardDataProtectionManager> _logger;
        private readonly byte[] _masterKey;

        public CardDataProtectionManager(ILogger<CardDataProtectionManager> logger, byte[] masterKey)
        {
            _logger = logger;
            _masterKey = masterKey;

            if (masterKey.Length != 32)
            {
                throw new ArgumentException("Master key must be 256 bits (32 bytes)");
            }
        }

        /// <summary>
        /// Tokenize Primary Account Number (PAN) instead of storing.
        ///
        /// PCI-DSS Requirement 3.2.1: Do not store sensitive authentication data
        /// </summary>
        public string TokenizePAN(string pan)
        {
            if (!ValidatePAN(pan))
            {
                throw new ArgumentException("Invalid PAN format");
            }

            // Generate cryptographically secure token
            var token = $"TKN{Guid.NewGuid():N}"[..19].ToUpper();

            // Store token-to-PAN mapping in secure vault (HSM/external tokenization service)
            StoreTokenMapping(token, pan);

            _logger.LogInformation("PAN tokenized: TokenPrefix={TokenPrefix}, Timestamp={Timestamp}",
                token[..6], DateTime.UtcNow);

            return token;
        }

        /// <summary>
        /// Mask PAN for display.
        ///
        /// PCI-DSS Requirement 3.3: Mask PAN when displayed
        /// Only first 6 and last 4 digits shown
        /// </summary>
        public string MaskPAN(string pan)
        {
            if (pan.Length < 13)
            {
                throw new ArgumentException("PAN too short to mask");
            }

            // Show first 6 (BIN) and last 4 digits
            var masked = pan[..6] + new string('*', pan.Length - 10) + pan[^4..];

            _logger.LogInformation("PAN masked for display: MaskedPAN={MaskedPAN}, Timestamp={Timestamp}",
                masked, DateTime.UtcNow);

            return masked;
        }

        /// <summary>
        /// Encrypt PAN with AES-256-GCM.
        ///
        /// PCI-DSS Requirement 3.4.1: Use strong cryptography
        /// PCI-DSS Requirement 3.5.1: Key strength minimum 256-bit
        /// </summary>
        public EncryptedData EncryptPAN(string pan)
        {
            if (!ValidatePAN(pan))
            {
                throw new ArgumentException("Invalid PAN format");
            }

            using var aesGcm = new AesGcm(_masterKey);

            // Generate random nonce
            var nonce = new byte[AesGcm.NonceByteSizes.MaxSize];
            RandomNumberGenerator.Fill(nonce);

            // Encrypt PAN
            var plaintext = Encoding.UTF8.GetBytes(pan);
            var ciphertext = new byte[plaintext.Length];
            var tag = new byte[AesGcm.TagByteSizes.MaxSize];

            aesGcm.Encrypt(nonce, plaintext, ciphertext, tag);

            _logger.LogInformation("PAN encrypted: Algorithm=AES-256-GCM, Timestamp={Timestamp}",
                DateTime.UtcNow);

            return new EncryptedData
            {
                Ciphertext = Convert.ToBase64String(ciphertext),
                Nonce = Convert.ToBase64String(nonce),
                Tag = Convert.ToBase64String(tag),
                Algorithm = "AES-256-GCM"
            };
        }

        /// <summary>
        /// Decrypt PAN.
        /// </summary>
        public string DecryptPAN(EncryptedData encryptedData)
        {
            using var aesGcm = new AesGcm(_masterKey);

            var ciphertext = Convert.FromBase64String(encryptedData.Ciphertext);
            var nonce = Convert.FromBase64String(encryptedData.Nonce);
            var tag = Convert.FromBase64String(encryptedData.Tag);

            var plaintext = new byte[ciphertext.Length];

            try
            {
                aesGcm.Decrypt(nonce, ciphertext, tag, plaintext);

                _logger.LogInformation("PAN decrypted: Timestamp={Timestamp}", DateTime.UtcNow);

                return Encoding.UTF8.GetString(plaintext);
            }
            catch (CryptographicException ex)
            {
                _logger.LogError("PAN decryption failed: Error={Error}", ex.Message);
                throw;
            }
        }

        /// <summary>
        /// Create one-way hash of PAN for searching.
        ///
        /// PCI-DSS Requirement 3.4.1: Render PAN unreadable
        /// </summary>
        public string HashPANForSearch(string pan)
        {
            using var sha256 = SHA256.Create();
            var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(pan));

            _logger.LogInformation("PAN hashed: Algorithm=SHA-256, Timestamp={Timestamp}",
                DateTime.UtcNow);

            return Convert.ToBase64String(hash);
        }

        /// <summary>
        /// Validate PAN using Luhn algorithm.
        /// </summary>
        private bool ValidatePAN(string pan)
        {
            // Remove spaces and hyphens
            pan = Regex.Replace(pan, @"[\s-]", "");

            // Check length (13-19 digits)
            if (pan.Length < 13 || pan.Length > 19)
            {
                return false;
            }

            // Check all numeric
            if (!pan.All(char.IsDigit))
            {
                return false;
            }

            // Luhn algorithm
            int sum = 0;
            bool alternate = false;

            for (int i = pan.Length - 1; i >= 0; i--)
            {
                int digit = pan[i] - '0';

                if (alternate)
                {
                    digit *= 2;
                    if (digit > 9)
                    {
                        digit -= 9;
                    }
                }

                sum += digit;
                alternate = !alternate;
            }

            return (sum % 10 == 0);
        }

        private void StoreTokenMapping(string token, string pan)
        {
            // This would typically interface with a secure token vault
            // For demonstration purposes only
        }
    }

    public class EncryptedData
    {
        public string Ciphertext { get; set; }
        public string Nonce { get; set; }
        public string Tag { get; set; }
        public string Algorithm { get; set; }
    }
}
```

---

## Requirement 8: Multi-Factor Authentication

```csharp
using OtpNet;
using QRCoder;
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.PCI
{
    /// <summary>
    /// PCI-DSS Authentication Manager.
    ///
    /// PCI-DSS Requirement 8: Identify users and authenticate access
    /// PCI-DSS Requirement 8.3.6: Multi-factor authentication (MFA)
    /// </summary>
    public class PCIAuthenticationManager
    {
        private readonly ILogger<PCIAuthenticationManager> _logger;

        private const int PasswordMinLength = 12;
        private const int PasswordMaxAgeDays = 90;
        private const int LockoutThreshold = 6; // PCI-DSS 8.3.4
        private const int LockoutDurationMinutes = 30;

        public PCIAuthenticationManager(ILogger<PCIAuthenticationManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Generate MFA secret for user.
        ///
        /// PCI-DSS Requirement 8.3.6: MFA for admin access to CDE
        /// </summary>
        public MFAEnrollmentResponse GenerateMFASecret(string userId, string userEmail)
        {
            var secret = KeyGeneration.GenerateRandomKey(20);
            var base32Secret = Base32Encoding.ToString(secret);

            // Generate QR code
            var issuer = "PCI-DSS Application";
            var qrCodeUri = $"otpauth://totp/{issuer}:{userEmail}?secret={base32Secret}&issuer={issuer}";

            using var qrGenerator = new QRCodeGenerator();
            var qrCodeData = qrGenerator.CreateQrCode(qrCodeUri, QRCodeGenerator.ECCLevel.Q);
            using var qrCode = new PngByteQRCode(qrCodeData);
            var qrCodeBytes = qrCode.GetGraphic(20);
            var qrCodeDataUri = $"data:image/png;base64,{Convert.ToBase64String(qrCodeBytes)}";

            _logger.LogInformation("MFA secret generated: UserId={UserId}, Timestamp={Timestamp}",
                userId, DateTime.UtcNow);

            return new MFAEnrollmentResponse
            {
                Secret = base32Secret,
                QrCodeDataUri = qrCodeDataUri
            };
        }

        /// <summary>
        /// Verify MFA token.
        /// </summary>
        public bool VerifyMFAToken(string secret, string token)
        {
            var totp = new Totp(Base32Encoding.ToBytes(secret));
            var valid = totp.VerifyTotp(token, out _, new VerificationWindow(1, 1));

            _logger.LogInformation("MFA token verified: Valid={Valid}, Timestamp={Timestamp}",
                valid, DateTime.UtcNow);

            return valid;
        }

        /// <summary>
        /// Validate password complexity.
        ///
        /// PCI-DSS Requirement 8.3.6: Password complexity
        /// - Minimum 12 characters
        /// - Numeric and alphabetic characters
        /// </summary>
        public ValidationResult ValidatePasswordComplexity(string password)
        {
            var violations = new List<string>();

            if (password.Length < PasswordMinLength)
            {
                violations.Add($"Password must be at least {PasswordMinLength} characters");
            }

            if (!password.Any(char.IsDigit))
            {
                violations.Add("Password must contain at least one number");
            }

            if (!password.Any(char.IsLetter))
            {
                violations.Add("Password must contain at least one letter");
            }

            if (!password.Any(char.IsUpper))
            {
                violations.Add("Password must contain at least one uppercase letter");
            }

            if (!password.Any(char.IsLower))
            {
                violations.Add("Password must contain at least one lowercase letter");
            }

            var isValid = violations.Count == 0;

            if (!isValid)
            {
                _logger.LogWarning("Password complexity validation failed: Violations={Violations}",
                    string.Join(", ", violations));
            }

            return new ValidationResult(isValid, violations);
        }

        /// <summary>
        /// Check if password has expired.
        ///
        /// PCI-DSS Requirement 8.3.9: Password change every 90 days
        /// </summary>
        public bool CheckPasswordExpiry(string userId, DateTime lastChanged)
        {
            var ageDays = (DateTime.UtcNow - lastChanged).Days;
            var expired = ageDays >= PasswordMaxAgeDays;

            if (expired)
            {
                _logger.LogWarning("Password expired: UserId={UserId}, AgeDays={AgeDays}, MaxAgeDays={MaxAgeDays}",
                    userId, ageDays, PasswordMaxAgeDays);
            }

            return expired;
        }
    }

    public class MFAEnrollmentResponse
    {
        public string Secret { get; set; }
        public string QrCodeDataUri { get; set; }
    }

    public class ValidationResult
    {
        public bool IsValid { get; }
        public List<string> Violations { get; }

        public ValidationResult(bool isValid, List<string> violations)
        {
            IsValid = isValid;
            Violations = violations;
        }
    }
}
```

---

## Requirement 10: Audit Logging

```csharp
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;

namespace ComplianceGovernance.PCI
{
    /// <summary>
    /// PCI-DSS Audit Logger.
    ///
    /// PCI-DSS Requirement 10: Log and monitor all access
    /// PCI-DSS Requirement 10.2: Implement audit trails
    /// </summary>
    public class PCIAuditLogger
    {
        private readonly ILogger<PCIAuditLogger> _logger;

        public enum EventType
        {
            UserAccessCDE,
            PrivilegedAction,
            AccessCardholderData,
            SystemChange,
            AuthenticationFailed,
            AuthenticationSuccess
        }

        public PCIAuditLogger(ILogger<PCIAuditLogger> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Log access to Cardholder Data Environment.
        ///
        /// PCI-DSS Requirement 10.2.1: User access to CHD
        /// PCI-DSS Requirement 10.3: Record audit trail entries
        /// </summary>
        public void LogCDEAccess(string userId, string action, string resource,
                                 bool success, string ipAddress)
        {
            var auditEntry = new Dictionary<string, object>
            {
                ["event_type"] = EventType.UserAccessCDE,
                ["timestamp"] = DateTime.UtcNow,
                ["user_id"] = userId,
                ["action"] = action,
                ["resource"] = resource,
                ["success"] = success,
                ["ip_address"] = ipAddress,
                ["event_id"] = Guid.NewGuid()
            };

            _logger.LogWarning("CDE access: {@AuditEntry}", auditEntry);

            // Store in tamper-proof audit log
            StoreAuditEntry(auditEntry);
        }

        /// <summary>
        /// Log actions by privileged users.
        ///
        /// PCI-DSS Requirement 10.2.2: Actions by privileged users
        /// </summary>
        public void LogPrivilegedAction(string userId, string action,
                                        string targetSystem, string justification)
        {
            var auditEntry = new Dictionary<string, object>
            {
                ["event_type"] = EventType.PrivilegedAction,
                ["timestamp"] = DateTime.UtcNow,
                ["user_id"] = userId,
                ["action"] = action,
                ["target_system"] = targetSystem,
                ["justification"] = justification,
                ["event_id"] = Guid.NewGuid()
            };

            _logger.LogWarning("Privileged action: {@AuditEntry}", auditEntry);
            StoreAuditEntry(auditEntry);
        }

        /// <summary>
        /// Store audit entry in tamper-proof log.
        ///
        /// PCI-DSS Requirement 10.5.3: Protect audit trails
        /// Note: In production, use WORM storage or external SIEM
        /// </summary>
        private void StoreAuditEntry(Dictionary<string, object> entry)
        {
            // Store in centralized logging system
            // Use write-once-read-many (WORM) storage
            // Sign entries with cryptographic hash
        }
    }
}
```

---

## Success Criteria

- [ ] PAN never stored in clear text
- [ ] PAN masked when displayed (first 6, last 4 only)
- [ ] AES-256-GCM encryption for stored PAN
- [ ] TLS 1.2+ for data transmission
- [ ] MFA enforced for CDE access
- [ ] Password complexity enforced (12+ chars)
- [ ] Passwords expire after 90 days
- [ ] Account lockout after 6 failed attempts
- [ ] All CDE access logged with audit trail
- [ ] Logs tamper-proof and retained 1 year minimum

---

[← Back to Compliance Frameworks](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
