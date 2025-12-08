---
template_id: compliance_governance_ccpa_csharp
template_name: CCPA Compliance - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: privacy_protection
phase_number: 4
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - privacy_protection/README.md
related_templates:
  - compliance_frameworks/csharp_gdpr_compliance.md
tools:
  - ASP.NET Core (web framework)
  - Entity Framework Core (data access)
tags:
  - ccpa
  - privacy
  - california
  - csharp
---

# CCPA Compliance - C#

**California Consumer Privacy Act for ASP.NET Core applications**

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**5 Key Consumer Rights**: Right to Know, Right to Delete, Right to Opt-Out, Right to Non-Discrimination, Right to Correct

**Response Deadline**: 45 days

---

## Right to Know (CCPA §1798.100)

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace ComplianceGovernance.CCPA
{
    /// <summary>
    /// CCPA Right to Know handler.
    ///
    /// CCPA §1798.100: Right to know what personal information is collected
    /// </summary>
    public class CCPADataDisclosureService
    {
        private readonly ILogger<CCPADataDisclosureService> _logger;

        public CCPADataDisclosureService(ILogger<CCPADataDisclosureService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Process consumer's right to know request.
        /// Must respond within 45 days.
        /// </summary>
        public async Task<DisclosureResponse> ProcessRightToKnow(string consumerId)
        {
            var requestId = Guid.NewGuid().ToString();
            var deadline = DateTime.UtcNow.AddDays(45);

            var categoriesCollected = await GetCategoriesCollected(consumerId);
            var businessPurposes = await GetBusinessPurposes(consumerId);
            var thirdParties = await GetThirdParties(consumerId);
            var specificPieces = await GetSpecificPiecesOfPI(consumerId);

            var disclosure = new DisclosureResponse
            {
                RequestId = requestId,
                ConsumerId = consumerId,
                RequestDate = DateTime.UtcNow,
                ResponseDeadline = deadline,
                CategoriesCollected = categoriesCollected,
                BusinessPurposes = businessPurposes,
                ThirdParties = thirdParties,
                SpecificPieces = specificPieces,
                SaleDisclosure = "We do not sell personal information",
                SharingDisclosure = "We share data only with service providers under contract"
            };

            _logger.LogInformation(
                "CCPA right to know processed: RequestId={RequestId}, ConsumerId={ConsumerId}",
                requestId, consumerId);

            return disclosure;
        }

        private async Task<List<string>> GetCategoriesCollected(string consumerId)
        {
            await Task.CompletedTask;
            return new List<string>
            {
                "Identifiers (name, email, IP address)",
                "Commercial information (purchase history, browsing history)",
                "Internet or network activity (cookies, logs)",
                "Geolocation data (approximate location from IP)",
                "Inferences (preferences, characteristics)"
            };
        }

        private async Task<List<string>> GetBusinessPurposes(string consumerId)
        {
            await Task.CompletedTask;
            return new List<string>
            {
                "Providing and improving services",
                "Customer support and communication",
                "Security and fraud prevention",
                "Legal compliance",
                "Marketing (with explicit consent)"
            };
        }

        private async Task<List<string>> GetThirdParties(string consumerId)
        {
            await Task.CompletedTask;
            return new List<string>
            {
                "Service providers: AWS (hosting), Stripe (payments)",
                "Analytics providers: Google Analytics (with anonymization)",
                "Security providers: Cloudflare (DDoS protection)"
            };
        }

        private async Task<Dictionary<string, object>> GetSpecificPiecesOfPI(string consumerId)
        {
            await Task.CompletedTask;
            return new Dictionary<string, object>
            {
                ["profile"] = new { Name = "User", Email = "user@example.com" },
                ["account_created"] = "2023-01-15",
                ["last_login"] = "2025-12-05",
                ["orders"] = new List<object>()
            };
        }

        public class DisclosureResponse
        {
            public string RequestId { get; set; }
            public string ConsumerId { get; set; }
            public DateTime RequestDate { get; set; }
            public DateTime ResponseDeadline { get; set; }
            public List<string> CategoriesCollected { get; set; }
            public List<string> BusinessPurposes { get; set; }
            public List<string> ThirdParties { get; set; }
            public Dictionary<string, object> SpecificPieces { get; set; }
            public string SaleDisclosure { get; set; }
            public string SharingDisclosure { get; set; }
        }
    }
}
```

---

## Right to Delete (CCPA §1798.105)

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ComplianceGovernance.CCPA
{
    /// <summary>
    /// CCPA Right to Delete handler.
    ///
    /// CCPA §1798.105: Right to delete personal information
    /// </summary>
    public class CCPADeletionService
    {
        private readonly ILogger<CCPADeletionService> _logger;

        public CCPADeletionService(ILogger<CCPADeletionService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Process consumer's right to delete request.
        /// Must respond within 45 days.
        /// Check for exceptions under CCPA §1798.105(d).
        /// </summary>
        public async Task<DeletionResult> ProcessRightToDelete(
            string consumerId,
            string verificationMethod)
        {
            var requestId = Guid.NewGuid().ToString();

            // Verify consumer identity (2-factor verification for sensitive data)
            if (!await VerifyConsumerIdentity(consumerId, verificationMethod))
            {
                _logger.LogWarning(
                    "Deletion request verification failed: RequestId={RequestId}",
                    requestId);

                return new DeletionResult
                {
                    Status = "Verification Failed",
                    Reason = "Unable to verify consumer identity"
                };
            }

            // Check for deletion exceptions (§1798.105(d))
            var exceptions = await CheckDeletionExceptions(consumerId);

            if (exceptions.Count > 0)
            {
                _logger.LogWarning(
                    "Deletion denied: RequestId={RequestId}, Exceptions={Exceptions}",
                    requestId, string.Join(", ", exceptions));

                return new DeletionResult
                {
                    Status = "Denied",
                    Reason = "Legal obligations require data retention",
                    Exceptions = exceptions
                };
            }

            // Perform deletion
            await DeleteConsumerData(consumerId, requestId);

            _logger.LogWarning(
                "Consumer data deleted: RequestId={RequestId}, ConsumerId={ConsumerId}",
                requestId, consumerId);

            return new DeletionResult
            {
                Status = "Completed",
                RequestId = requestId,
                DeletionDate = DateTime.UtcNow
            };
        }

        private async Task<bool> VerifyConsumerIdentity(string consumerId, string method)
        {
            // Implement 2-factor verification for sensitive data
            await Task.CompletedTask;
            return true;
        }

        private async Task<List<string>> CheckDeletionExceptions(string consumerId)
        {
            var exceptions = new List<string>();

            // §1798.105(d)(1): Complete transaction
            var hasActiveOrders = await HasActiveOrders(consumerId);
            if (hasActiveOrders)
            {
                exceptions.Add("Active orders pending completion");
            }

            // §1798.105(d)(2): Security incidents, fraud, illegal activity
            var hasSecurityInvestigation = await HasOngoingSecurityInvestigation(consumerId);
            if (hasSecurityInvestigation)
            {
                exceptions.Add("Ongoing security incident investigation");
            }

            // §1798.105(d)(5): Internal uses (legal obligations)
            var hasTaxRecords = await HasRecentFinancialRecords(consumerId);
            if (hasTaxRecords)
            {
                exceptions.Add("Tax and accounting retention requirement (7 years)");
            }

            // §1798.105(d)(7): Comply with legal obligation
            var hasLegalHold = await HasLegalHold(consumerId);
            if (hasLegalHold)
            {
                exceptions.Add("Legal hold or pending litigation");
            }

            return exceptions;
        }

        private async Task<bool> HasActiveOrders(string consumerId)
        {
            await Task.CompletedTask;
            return false;
        }

        private async Task<bool> HasOngoingSecurityInvestigation(string consumerId)
        {
            await Task.CompletedTask;
            return false;
        }

        private async Task<bool> HasRecentFinancialRecords(string consumerId)
        {
            // Check for financial records within 7-year retention period
            await Task.CompletedTask;
            return false;
        }

        private async Task<bool> HasLegalHold(string consumerId)
        {
            await Task.CompletedTask;
            return false;
        }

        private async Task DeleteConsumerData(string consumerId, string requestId)
        {
            // Delete from all systems:
            // - User profile
            // - Preferences
            // - Analytics data
            // - Cookies and tracking data
            //
            // Pseudonymize transaction data (retain for legal compliance)

            await Task.CompletedTask;

            _logger.LogWarning(
                "Data deletion executed: ConsumerId={ConsumerId}, RequestId={RequestId}",
                consumerId, requestId);
        }

        public class DeletionResult
        {
            public string Status { get; set; }
            public string RequestId { get; set; }
            public string Reason { get; set; }
            public List<string> Exceptions { get; set; }
            public DateTime? DeletionDate { get; set; }
        }
    }
}
```

---

## Right to Opt-Out of Sale (CCPA §1798.120)

```csharp
namespace ComplianceGovernance.CCPA
{
    /// <summary>
    /// CCPA Right to Opt-Out handler.
    ///
    /// CCPA §1798.120: Right to opt-out of sale of personal information
    /// </summary>
    public class CCPAOptOutService
    {
        private readonly ILogger<CCPAOptOutService> _logger;

        public CCPAOptOutService(ILogger<CCPAOptOutService> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Process consumer opt-out of sale.
        /// Must honor immediately (no 45-day deadline).
        /// </summary>
        public async Task<OptOutResult> ProcessOptOut(string consumerId)
        {
            var optOutId = Guid.NewGuid().ToString();

            // Update consumer preferences
            await UpdateOptOutPreference(consumerId, true);

            // Notify third parties (if any data sharing for monetary consideration)
            await NotifyThirdParties(consumerId);

            _logger.LogInformation(
                "Consumer opted out of sale: OptOutId={OptOutId}, ConsumerId={ConsumerId}",
                optOutId, consumerId);

            return new OptOutResult
            {
                Status = "Completed",
                OptOutId = optOutId,
                OptOutDate = DateTime.UtcNow,
                Message = "Your opt-out preference has been recorded. " +
                         "We will not sell your personal information."
            };
        }

        /// <summary>
        /// Process consumer opt-in (after previous opt-out).
        /// Requires affirmative consent.
        /// </summary>
        public async Task<OptOutResult> ProcessOptIn(
            string consumerId,
            string affirmativeConsentText)
        {
            var optInId = Guid.NewGuid().ToString();

            // Record affirmative consent
            await RecordAffirmativeConsent(consumerId, affirmativeConsentText);

            // Update consumer preferences
            await UpdateOptOutPreference(consumerId, false);

            _logger.LogInformation(
                "Consumer opted in to sale: OptInId={OptInId}, ConsumerId={ConsumerId}",
                optInId, consumerId);

            return new OptOutResult
            {
                Status = "Completed",
                OptOutId = optInId,
                OptOutDate = DateTime.UtcNow,
                Message = "Your consent has been recorded."
            };
        }

        private async Task UpdateOptOutPreference(string consumerId, bool optedOut)
        {
            // Update database
            await Task.CompletedTask;
        }

        private async Task NotifyThirdParties(string consumerId)
        {
            // Notify any third parties about opt-out status
            await Task.CompletedTask;
        }

        private async Task RecordAffirmativeConsent(string consumerId, string consentText)
        {
            // Store consent with timestamp for audit
            await Task.CompletedTask;
        }

        public class OptOutResult
        {
            public string Status { get; set; }
            public string OptOutId { get; set; }
            public DateTime OptOutDate { get; set; }
            public string Message { get; set; }
        }
    }
}
```

---

## "Do Not Sell My Personal Information" Link

```csharp
using Microsoft.AspNetCore.Mvc;

namespace ComplianceGovernance.CCPA
{
    /// <summary>
    /// CCPA-required "Do Not Sell" page controller.
    ///
    /// CCPA §1798.135: Right to opt-out link on homepage
    /// </summary>
    [ApiController]
    [Route("api/ccpa")]
    public class CCPAController : ControllerBase
    {
        private readonly CCPAOptOutService _optOutService;
        private readonly ILogger<CCPAController> _logger;

        public CCPAController(
            CCPAOptOutService optOutService,
            ILogger<CCPAController> logger)
        {
            _optOutService = optOutService;
            _logger = logger;
        }

        /// <summary>
        /// POST /api/ccpa/do-not-sell
        /// Process "Do Not Sell My Personal Information" request
        /// </summary>
        [HttpPost("do-not-sell")]
        public async Task<IActionResult> DoNotSell([FromBody] DoNotSellRequest request)
        {
            if (string.IsNullOrEmpty(request.ConsumerId))
            {
                return BadRequest("Consumer ID is required");
            }

            var result = await _optOutService.ProcessOptOut(request.ConsumerId);

            return Ok(new
            {
                status = result.Status,
                message = result.Message,
                opt_out_date = result.OptOutDate
            });
        }

        public class DoNotSellRequest
        {
            public string ConsumerId { get; set; }
        }
    }
}
```

---

## Right to Non-Discrimination (CCPA §1798.125)

```csharp
namespace ComplianceGovernance.CCPA
{
    /// <summary>
    /// CCPA Right to Non-Discrimination enforcement.
    ///
    /// CCPA §1798.125: Cannot discriminate for exercising CCPA rights
    /// </summary>
    public class NonDiscriminationEnforcement
    {
        private readonly ILogger<NonDiscriminationEnforcement> _logger;

        public NonDiscriminationEnforcement(ILogger<NonDiscriminationEnforcement> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Ensure consumer receives same service level regardless of CCPA requests.
        /// Cannot deny goods/services, charge different prices, or provide
        /// different quality of service.
        /// </summary>
        public async Task<ServiceAccessResult> ValidateServiceAccess(
            string consumerId,
            string serviceType)
        {
            // Check if consumer has exercised CCPA rights
            var ccpaRequests = await GetCCPARequestHistory(consumerId);

            if (ccpaRequests.Count > 0)
            {
                _logger.LogInformation(
                    "Consumer with CCPA requests accessing service: " +
                    "ConsumerId={ConsumerId}, ServiceType={ServiceType}, " +
                    "RequestCount={RequestCount}",
                    consumerId, serviceType, ccpaRequests.Count);
            }

            // CRITICAL: Must provide same service regardless of CCPA activity
            return new ServiceAccessResult
            {
                AccessGranted = true,
                ServiceLevel = "Standard",
                Pricing = "Standard",
                Message = "Full access granted"
            };
        }

        private async Task<List<string>> GetCCPARequestHistory(string consumerId)
        {
            await Task.CompletedTask;
            return new List<string>();
        }

        public class ServiceAccessResult
        {
            public bool AccessGranted { get; set; }
            public string ServiceLevel { get; set; }
            public string Pricing { get; set; }
            public string Message { get; set; }
        }
    }
}
```

---

## Success Criteria

- [ ] Right to Know requests processed within 45 days
- [ ] Right to Delete honored with exception handling (§1798.105(d))
- [ ] "Do Not Sell" link prominently displayed on homepage
- [ ] Opt-out mechanism operational and immediate
- [ ] Non-discrimination enforced (same pricing, service level)
- [ ] 2-factor verification for sensitive data deletion
- [ ] Third-party notification system for opt-outs
- [ ] Audit logs for all CCPA requests

---

[← Back to Privacy Protection](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
