---
template_id: compliance_governance_breach_protocols_csharp
template_name: Breach Protocols - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - incident_response/csharp_incident_response_plan.md
  - privacy_protection/csharp_gdpr_compliance.md
related_templates:
  - compliance_frameworks/csharp_soc2_compliance.md
tools:
  - Forensics tools
tags:
  - data-breach
  - breach-notification
  - gdpr
  - ccpa
  - csharp
---

# Breach Protocols - C#

**Data breach notification and response protocols (GDPR 72-hour rule)**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Data Breach Notification Requirements

**GDPR Article 33**: Notify supervisory authority within 72 hours
**GDPR Article 34**: Notify individuals if high risk
**CCPA**: No specific timeline, but must notify "without unreasonable delay"
**State Laws**: Varies (CA requires notification without unreasonable delay)

---

## Implementation

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.Security
{
    public enum RiskLevel
    {
        Low,
        Medium,
        High,
        Critical
    }

    public class BreachNotificationService
    {
        private readonly ILogger<BreachNotificationService> _logger;
        private const int GdprNotificationDeadlineHours = 72;

        public BreachNotificationService(ILogger<BreachNotificationService> logger)
        {
            _logger = logger;
        }

        public async Task<Dictionary<string, object>> AssessBreachAsync(string incidentId)
        {
            // Retrieve incident (simulated)
            var incident = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "data_affected", true },
                { "detected_date", DateTime.UtcNow },
                { "users_affected_count", 5000 },
                { "ca_residents_affected", true }
            };

            bool isBreach = (bool)incident.GetValueOrDefault("data_affected", false);

            if (!isBreach)
            {
                return new Dictionary<string, object> { { "is_breach", false } };
            }

            var riskLevel = AssessRiskLevel(incident);
            var breachId = Guid.NewGuid().ToString();
            var gdprDeadline = DateTime.UtcNow.AddHours(GdprNotificationDeadlineHours);

            var breachAssessment = new Dictionary<string, object>
            {
                { "is_breach", true },
                { "breach_id", breachId },
                { "incident_id", incidentId },
                { "detected_date", incident["detected_date"] },
                { "risk_level", riskLevel.ToString() },
                { "notify_gdpr_authority",
                  riskLevel == RiskLevel.Medium ||
                  riskLevel == RiskLevel.High ||
                  riskLevel == RiskLevel.Critical },
                { "notify_individuals",
                  riskLevel == RiskLevel.High ||
                  riskLevel == RiskLevel.Critical },
                { "notify_ccpa", incident.GetValueOrDefault("ca_residents_affected", false) },
                { "gdpr_deadline", gdprDeadline }
            };

            _logger.LogError("Data breach assessed: breach_id={BreachId}, risk_level={RiskLevel}",
                           breachId, riskLevel);

            return await Task.FromResult(breachAssessment);
        }

        private RiskLevel AssessRiskLevel(Dictionary<string, object> incident)
        {
            int usersAffected = Convert.ToInt32(incident.GetValueOrDefault("users_affected_count", 0));

            if (usersAffected > 10000) return RiskLevel.Critical;
            if (usersAffected > 1000) return RiskLevel.High;
            if (usersAffected > 100) return RiskLevel.Medium;
            return RiskLevel.Low;
        }

        public async Task<string> NotifyGdprAuthorityAsync(string breachId)
        {
            var notificationId = Guid.NewGuid().ToString();

            var notification = new Dictionary<string, object>
            {
                { "notification_id", notificationId },
                { "breach_id", breachId },
                { "notification_type", "gdpr_authority" },
                { "notification_date", DateTime.UtcNow },
                { "nature_of_breach", "Unauthorized access to customer database" },
                { "dpo_contact", "dpo@company.com" },
                { "likely_consequences", "Risk of identity theft for affected individuals" },
                { "measures_taken", "Database access revoked, passwords reset, monitoring enhanced" }
            };

            SendToAuthority(notification);

            _logger.LogError("GDPR authority notified: notification_id={NotificationId}", notificationId);

            return await Task.FromResult(notificationId);
        }

        public async Task<int> NotifyIndividualsAsync(string breachId)
        {
            int affectedCount = 5000; // Simulated

            var notificationContent = @"
Subject: Important Security Notice

We are writing to inform you of a data security incident.

What Happened: Unauthorized access to customer database

What Information Was Involved: Names, email addresses, account numbers

What We Are Doing: Enhanced security measures, password resets, monitoring

What You Can Do: Update your password, enable 2FA, monitor accounts

Contact: security@company.com
";

            _logger.LogError("Individuals notified: breach_id={BreachId}, count={Count}",
                           breachId, affectedCount);

            return await Task.FromResult(affectedCount);
        }

        public async Task NotifyCcpaAsync(string breachId)
        {
            _logger.LogInformation("CCPA notification initiated: breach_id={BreachId}", breachId);
            // California-specific notification requirements
            await Task.CompletedTask;
        }

        private void SendToAuthority(Dictionary<string, object> notification)
        {
            _logger.LogInformation("Sending notification to GDPR supervisory authority");
        }

        public async Task<Dictionary<string, object>> GenerateBreachReportAsync(string breachId)
        {
            var report = new Dictionary<string, object>
            {
                { "report_id", Guid.NewGuid().ToString() },
                { "breach_id", breachId },
                { "generated_date", DateTime.UtcNow },
                { "executive_summary", "Summary of breach incident" },
                { "timeline", "Detailed timeline of events" },
                { "impact_analysis", "Analysis of affected systems and data" },
                { "response_actions", "Actions taken to contain and remediate" },
                { "lessons_learned", "Key takeaways and improvements" }
            };

            _logger.LogInformation("Breach report generated: breach_id={BreachId}", breachId);

            return await Task.FromResult(report);
        }
    }
}
```

---

## Success Criteria

- [ ] Breach detection mechanisms operational
- [ ] 72-hour notification workflow implemented
- [ ] Notification templates ready
- [ ] Authority contacts established
- [ ] Breach simulation conducted

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
