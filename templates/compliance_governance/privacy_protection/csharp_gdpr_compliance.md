---
template_id: compliance_governance_gdpr_csharp
template_name: GDPR Compliance - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/csharp_iso27001_implementation.md
tools:
  - ASP.NET Core (web framework)
  - Entity Framework Core (data access)
tags:
  - gdpr
  - privacy
  - data-protection
  - csharp
---

# GDPR Compliance - C#

**General Data Protection Regulation for ASP.NET Core applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### GDPR Key Rights

1. **Right to Access** (Art. 15)
2. **Right to Rectification** (Art. 16)
3. **Right to Erasure** (Art. 17)
4. **Right to Data Portability** (Art. 20)
5. **Right to Object** (Art. 21)

---

## Right to Access (Art. 15)

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.GDPR
{
    /// <summary>
    /// GDPR Data Subject Access Request handler.
    ///
    /// GDPR Article 15: Right of access by the data subject
    /// </summary>
    public class DataSubjectAccessHandler
    {
        private readonly ILogger<DataSubjectAccessHandler> _logger;

        public DataSubjectAccessHandler(ILogger<DataSubjectAccessHandler> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Process data subject access request.
        /// Must respond within 30 days.
        /// </summary>
        public async Task<DataSubjectReport> ProcessAccessRequest(string dataSubjectId)
        {
            var requestId = Guid.NewGuid().ToString();
            var deadline = DateTime.UtcNow.AddDays(30);

            var personalData = await CollectPersonalData(dataSubjectId);
            var processingPurposes = await GetProcessingPurposes(dataSubjectId);
            var recipients = await GetDataRecipients(dataSubjectId);
            var retentionPeriod = await GetRetentionPeriod(dataSubjectId);

            var report = new DataSubjectReport
            {
                RequestId = requestId,
                DataSubjectId = dataSubjectId,
                RequestDate = DateTime.UtcNow,
                ResponseDeadline = deadline,
                PersonalData = personalData,
                ProcessingPurposes = processingPurposes,
                Recipients = recipients,
                RetentionPeriod = retentionPeriod,
                RightToLodgeComplaint = "You have the right to lodge a complaint with a supervisory authority"
            };

            _logger.LogInformation("GDPR access request processed: RequestId={RequestId}, DataSubjectId={DataSubjectId}",
                requestId, dataSubjectId);

            return report;
        }

        private async Task<Dictionary<string, object>> CollectPersonalData(string dataSubjectId)
        {
            // Collect all personal data across systems
            await Task.CompletedTask;
            return new Dictionary<string, object>
            {
                ["profile"] = new { Name = "User", Email = "user@example.com" },
                ["transactions"] = new List<object>(),
                ["preferences"] = new { Language = "en", Theme = "dark" }
            };
        }

        private async Task<List<string>> GetProcessingPurposes(string dataSubjectId)
        {
            await Task.CompletedTask;
            return new List<string>
            {
                "Providing services",
                "Improving user experience",
                "Marketing (with consent)"
            };
        }

        private async Task<List<string>> GetDataRecipients(string dataSubjectId)
        {
            await Task.CompletedTask;
            return new List<string>
            {
                "Cloud service providers (AWS, Azure)",
                "Payment processors (Stripe)",
                "Analytics providers (with anonymization)"
            };
        }

        private async Task<string> GetRetentionPeriod(string dataSubjectId)
        {
            await Task.CompletedTask;
            return "Active accounts: Indefinite while account active. " +
                   "Inactive accounts: 2 years after last activity. " +
                   "Transaction data: 7 years (legal requirement).";
        }

        public class DataSubjectReport
        {
            public string RequestId { get; set; }
            public string DataSubjectId { get; set; }
            public DateTime RequestDate { get; set; }
            public DateTime ResponseDeadline { get; set; }
            public Dictionary<string, object> PersonalData { get; set; }
            public List<string> ProcessingPurposes { get; set; }
            public List<string> Recipients { get; set; }
            public string RetentionPeriod { get; set; }
            public string RightToLodgeComplaint { get; set; }
        }
    }
}
```

---

## Right to Erasure (Art. 17)

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ComplianceGovernance.GDPR
{
    /// <summary>
    /// GDPR Right to Erasure handler.
    ///
    /// GDPR Article 17: Right to erasure ('right to be forgotten')
    /// </summary>
    public class DataErasureHandler
    {
        private readonly ILogger<DataErasureHandler> _logger;

        public DataErasureHandler(ILogger<DataErasureHandler> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Process erasure request.
        /// Must respond within 30 days.
        /// </summary>
        public async Task<ErasureResult> ProcessErasureRequest(
            string dataSubjectId,
            string justification)
        {
            var requestId = Guid.NewGuid().ToString();

            // Check for erasure exceptions (Art. 17(3))
            var exceptions = await CheckErasureExceptions(dataSubjectId);

            if (exceptions.Count > 0)
            {
                _logger.LogWarning("Erasure request denied: RequestId={RequestId}, Exceptions={Exceptions}",
                    requestId, string.Join(", ", exceptions));

                return new ErasureResult
                {
                    Status = "Denied",
                    Reason = "Legal obligations require data retention",
                    Exceptions = exceptions
                };
            }

            // Perform erasure
            await ErasePersonalData(dataSubjectId, requestId);

            _logger.LogWarning("Personal data erased: RequestId={RequestId}, DataSubjectId={DataSubjectId}",
                requestId, dataSubjectId);

            return new ErasureResult
            {
                Status = "Completed",
                RequestId = requestId,
                ErasureDate = DateTime.UtcNow
            };
        }

        private async Task<List<string>> CheckErasureExceptions(string dataSubjectId)
        {
            var exceptions = new List<string>();

            // Art. 17(3)(b): Compliance with legal obligation
            var hasLegalObligation = await HasLegalRetentionObligation(dataSubjectId);
            if (hasLegalObligation)
            {
                exceptions.Add("Legal retention obligation (7 years for financial records)");
            }

            // Art. 17(3)(e): Legal claims
            var hasPendingClaims = await HasPendingLegalClaims(dataSubjectId);
            if (hasPendingClaims)
            {
                exceptions.Add("Pending legal claims");
            }

            return exceptions;
        }

        private async Task<bool> HasLegalRetentionObligation(string dataSubjectId)
        {
            // Check if financial/tax records exist
            await Task.CompletedTask;
            return false;
        }

        private async Task<bool> HasPendingLegalClaims(string dataSubjectId)
        {
            await Task.CompletedTask;
            return false;
        }

        private async Task ErasePersonalData(string dataSubjectId, string requestId)
        {
            // Erase from all systems
            await Task.CompletedTask;

            // Log erasure in tamper-proof audit log
            _logger.LogWarning("Data erasure executed: DataSubjectId={DataSubjectId}, RequestId={RequestId}",
                dataSubjectId, requestId);
        }

        public class ErasureResult
        {
            public string Status { get; set; }
            public string RequestId { get; set; }
            public string Reason { get; set; }
            public List<string> Exceptions { get; set; }
            public DateTime? ErasureDate { get; set; }
        }
    }
}
```

---

## Consent Management

```csharp
namespace ComplianceGovernance.GDPR
{
    /// <summary>
    /// GDPR Consent Management.
    ///
    /// GDPR Article 7: Conditions for consent
    /// </summary>
    public class ConsentManager
    {
        private readonly ILogger<ConsentManager> _logger;

        public ConsentManager(ILogger<ConsentManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Record consent.
        /// GDPR requires: freely given, specific, informed, unambiguous.
        /// </summary>
        public async Task<string> RecordConsent(
            string dataSubjectId,
            string purpose,
            bool consentGiven,
            string consentText)
        {
            var consentId = Guid.NewGuid().ToString();

            var consent = new
            {
                ConsentId = consentId,
                DataSubjectId = dataSubjectId,
                Purpose = purpose,
                ConsentGiven = consentGiven,
                ConsentText = consentText,
                Timestamp = DateTime.UtcNow,
                Withdrawable = true
            };

            _logger.LogInformation("Consent recorded: ConsentId={ConsentId}, Purpose={Purpose}, Given={Given}",
                consentId, purpose, consentGiven);

            await Task.CompletedTask;
            return consentId;
        }

        /// <summary>
        /// Withdraw consent.
        /// GDPR Article 7(3): Right to withdraw consent.
        /// </summary>
        public async Task WithdrawConsent(string dataSubjectId, string consentId)
        {
            _logger.LogWarning("Consent withdrawn: DataSubjectId={DataSubjectId}, ConsentId={ConsentId}",
                dataSubjectId, consentId);

            await Task.CompletedTask;
        }
    }
}
```

---

## Success Criteria

- [ ] Data subject access requests processed within 30 days
- [ ] Right to erasure honored with exception handling
- [ ] Consent management implemented (freely given, specific, informed)
- [ ] Consent withdrawal mechanism operational
- [ ] Data portability exports in machine-readable format
- [ ] Breach notification within 72 hours

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
