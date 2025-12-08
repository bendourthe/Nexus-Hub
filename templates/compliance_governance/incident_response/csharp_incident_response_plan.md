---
template_id: compliance_governance_incident_response_csharp
template_name: Incident Response Plan - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: incident_response
phase_number: 5
difficulty: intermediate
estimated_time_hours: 4-6
prerequisites:
  - compliance_frameworks/csharp_soc2_compliance.md
  - compliance_frameworks/csharp_iso27001_implementation.md
related_templates:
  - incident_response/csharp_breach_protocols.md
  - privacy_protection/csharp_gdpr_compliance.md
tools:
  - PagerDuty (alerting)
  - JIRA (incident tracking)
tags:
  - incident-response
  - security-incidents
  - cyber-incidents
  - csharp
---

# Incident Response Plan - C#

**6-phase incident response lifecycle implementation**

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Incident Response Lifecycle

**NIST SP 800-61**: 6-phase incident response process

1. **Preparation** - Tools, training, procedures
2. **Detection and Analysis** - Identify incidents
3. **Containment** - Stop spread
4. **Eradication** - Remove threat
5. **Recovery** - Restore operations
6. **Post-Incident** - Lessons learned

### Framework Requirements

**ISO 27001 Control 5.26**: Response to information security incidents
**SOC 2 CC7.4**: Respond to security incidents

---

## Implementation

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.Security
{
    public enum IncidentSeverity
    {
        P1Critical,  // System down, data breach
        P2High,      // Significant impact
        P3Medium,    // Moderate impact
        P4Low        // Minor issue
    }

    public enum IncidentStatus
    {
        Detected,
        Investigating,
        Contained,
        Eradicated,
        Recovered,
        Closed
    }

    public class IncidentResponseService
    {
        private readonly ILogger<IncidentResponseService> _logger;
        // private readonly IIncidentRepository _incidentRepo;
        // private readonly IReviewRepository _reviewRepo;

        private static readonly Dictionary<IncidentSeverity, int> ResponseSla = new()
        {
            { IncidentSeverity.P1Critical, 15 },    // 15 minutes
            { IncidentSeverity.P2High, 60 },        // 1 hour
            { IncidentSeverity.P3Medium, 240 },     // 4 hours
            { IncidentSeverity.P4Low, 1440 }        // 24 hours
        };

        public IncidentResponseService(ILogger<IncidentResponseService> logger)
        {
            _logger = logger;
        }

        public async Task<string> CreateIncidentAsync(
            string title,
            string description,
            IncidentSeverity severity,
            string incidentType,
            string detectedBy)
        {
            var incidentId = Guid.NewGuid().ToString();
            var responseDeadline = DateTime.UtcNow.AddMinutes(ResponseSla[severity]);

            var incident = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "title", title },
                { "description", description },
                { "severity", severity.ToString() },
                { "incident_type", incidentType },
                { "detected_by", detectedBy },
                { "detected_date", DateTime.UtcNow },
                { "status", IncidentStatus.Detected.ToString() },
                { "response_deadline", responseDeadline },
                { "incident_commander", null },
                { "response_team", new List<string>() },
                { "contained_date", null },
                { "eradicated_date", null },
                { "recovered_date", null },
                { "closed_date", null },
                { "systems_affected", new List<string>() },
                { "data_affected", false },
                { "users_affected_count", 0 }
            };

            // await _incidentRepo.SaveAsync(incident);

            // Alert response team for critical/high severity
            if (severity == IncidentSeverity.P1Critical || severity == IncidentSeverity.P2High)
            {
                AlertResponseTeam(incidentId);
            }

            _logger.LogError("Security incident created: incident_id={IncidentId}, severity={Severity}",
                           incidentId, severity);

            return incidentId;
        }

        public async Task ContainIncidentAsync(string incidentId, List<string> containmentActions)
        {
            var updates = new Dictionary<string, object>
            {
                { "status", IncidentStatus.Contained.ToString() },
                { "contained_date", DateTime.UtcNow },
                { "containment_actions", containmentActions }
            };

            // await _incidentRepo.UpdateAsync(incidentId, updates);

            _logger.LogWarning("Incident contained: incident_id={IncidentId}, actions={Actions}",
                             incidentId, string.Join(", ", containmentActions));
        }

        public async Task EradicateThreatAsync(string incidentId, List<string> eradicationActions)
        {
            var updates = new Dictionary<string, object>
            {
                { "status", IncidentStatus.Eradicated.ToString() },
                { "eradicated_date", DateTime.UtcNow },
                { "eradication_actions", eradicationActions }
            };

            // await _incidentRepo.UpdateAsync(incidentId, updates);

            _logger.LogInformation("Threat eradicated: incident_id={IncidentId}", incidentId);
        }

        public async Task RecoverSystemsAsync(string incidentId, List<string> recoveryActions)
        {
            var updates = new Dictionary<string, object>
            {
                { "status", IncidentStatus.Recovered.ToString() },
                { "recovered_date", DateTime.UtcNow },
                { "recovery_actions", recoveryActions }
            };

            // await _incidentRepo.UpdateAsync(incidentId, updates);

            _logger.LogInformation("Systems recovered: incident_id={IncidentId}", incidentId);
        }

        public async Task CloseIncidentAsync(string incidentId, string rootCause, string lessonsLearned)
        {
            // var incident = await _incidentRepo.GetByIdAsync(incidentId);

            // Simulated incident for demonstration
            var incident = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "detected_date", DateTime.UtcNow.AddHours(-48) }
            };

            // Calculate metrics
            var detectedDate = (DateTime)incident["detected_date"];
            var totalDurationHours = (DateTime.UtcNow - detectedDate).TotalHours;

            var postMortem = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "root_cause", rootCause },
                { "lessons_learned", lessonsLearned },
                { "total_duration_hours", totalDurationHours },
                { "created_date", DateTime.UtcNow }
            };

            // await _postMortemRepo.SaveAsync(postMortem);

            var updates = new Dictionary<string, object>
            {
                { "status", IncidentStatus.Closed.ToString() },
                { "closed_date", DateTime.UtcNow },
                { "root_cause", rootCause }
            };

            // await _incidentRepo.UpdateAsync(incidentId, updates);

            _logger.LogInformation("Incident closed: incident_id={IncidentId}, duration_hours={DurationHours}",
                                 incidentId, totalDurationHours);
        }

        public async Task<Dictionary<string, object>> GenerateIncidentReportAsync(string incidentId)
        {
            // var incident = await _incidentRepo.GetByIdAsync(incidentId);
            // var postMortem = await _postMortemRepo.GetByIncidentIdAsync(incidentId);

            // Simulated data for demonstration
            var incident = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "title", "Database breach detected" },
                { "severity", IncidentSeverity.P1Critical.ToString() },
                { "detected_date", DateTime.UtcNow.AddHours(-48) },
                { "closed_date", DateTime.UtcNow },
                { "systems_affected", new List<string> { "database_server", "web_application" } },
                { "data_affected", true },
                { "users_affected_count", 5000 },
                { "containment_actions", new List<string> { "Revoked access", "Changed passwords" } },
                { "eradication_actions", new List<string> { "Removed malware", "Patched vulnerability" } },
                { "recovery_actions", new List<string> { "Restored from backup", "Verified integrity" } }
            };

            var postMortem = new Dictionary<string, object>
            {
                { "root_cause", "Unpatched SQL injection vulnerability" },
                { "lessons_learned", "Implement automated patching, enhance monitoring" }
            };

            var report = new Dictionary<string, object>
            {
                { "incident_id", incidentId },
                { "title", incident["title"] },
                { "severity", incident["severity"] },
                { "detection_date", incident["detected_date"] },
                { "closure_date", incident["closed_date"] },
                { "systems_affected", incident["systems_affected"] },
                { "data_affected", incident["data_affected"] },
                { "users_affected", incident["users_affected_count"] },
                { "containment_actions", incident["containment_actions"] },
                { "eradication_actions", incident["eradication_actions"] },
                { "recovery_actions", incident["recovery_actions"] },
                { "root_cause", postMortem["root_cause"] },
                { "lessons_learned", postMortem["lessons_learned"] }
            };

            return await Task.FromResult(report);
        }

        public async Task<Dictionary<string, object>> ConductPostIncidentReviewAsync(
            string incidentId,
            string rootCause,
            List<string> lessonsLearned,
            List<string> correctiveActions)
        {
            var review = new Dictionary<string, object>
            {
                { "review_id", Guid.NewGuid().ToString() },
                { "incident_id", incidentId },
                { "review_date", DateTime.UtcNow },
                { "root_cause", rootCause },
                { "lessons_learned", lessonsLearned },
                { "corrective_actions", correctiveActions }
            };

            // await _reviewRepo.SaveAsync(review);

            _logger.LogInformation("Post-incident review completed: incident_id={IncidentId}", incidentId);

            return await Task.FromResult(review);
        }

        private void AlertResponseTeam(string incidentId)
        {
            // In production: PagerDuty, email, SMS alerts
            _logger.LogError("ALERT: Critical incident created - incident_id={IncidentId}", incidentId);
        }

        private void SchedulePostIncidentReview(string incidentId)
        {
            // In production: create calendar event for post-incident review
            _logger.LogInformation("Post-incident review scheduled: incident_id={IncidentId}", incidentId);
        }
    }
}
```

---

## Success Criteria

- [ ] Incident response plan documented
- [ ] Response team identified and trained
- [ ] Incident detection mechanisms operational
- [ ] Escalation procedures defined
- [ ] Post-incident review process established

---

[← Back to Incident Response](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
