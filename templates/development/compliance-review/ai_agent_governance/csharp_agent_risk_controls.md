---
template_id: compliance_governance_agent_risk_controls_csharp
template_name: AI Agent Risk Controls - C#
version: 1.0.0
last_updated: 2025-12-05
language: csharp
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:
  - ai_agent_governance/csharp_agent_lifecycle.md
  - risk_management/csharp_risk_assessment.md
related_templates:
  - ai_agent_governance/csharp_agent_security.md
tools:
  - Polly (circuit breaker)
tags:
  - risk-management
  - defense-in-depth
  - four-pillars
  - csharp
---

# AI Agent Risk Controls - C#

**⚠️ Pillar 2: Risk Management (Defense in Depth)**

Implement risk controls for AI agent operations

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

**Defense in Depth**: Multiple layers of risk controls

**Risk Controls**:
- Rate limiting
- Circuit breakers
- Confidence thresholds
- Human-in-the-loop

---

## Implementation

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Organization.AI
{
    public enum RiskLevel
    {
        Low,
        Medium,
        High,
        Critical
    }

    public class AgentRiskControlsService
    {
        private readonly ILogger<AgentRiskControlsService> _logger;
        private const double ConfidenceThreshold = 0.7;
        private const int RateLimitPerMinute = 60;

        public AgentRiskControlsService(ILogger<AgentRiskControlsService> logger)
        {
            _logger = logger;
        }

        public bool CheckRateLimit(string agentId, string userId)
        {
            var requestCount = GetRequestCount(userId);

            if (requestCount >= RateLimitPerMinute)
            {
                _logger.LogWarning(
                    "Rate limit exceeded: agent_id={AgentId}, user_id={UserId}, count={Count}",
                    agentId, userId, requestCount);
                return false;
            }

            return true;
        }

        public Dictionary<string, object> EvaluateDecisionRisk(
            string agentId,
            Dictionary<string, object> decision,
            double confidence)
        {
            var riskLevel = RiskLevel.Low;
            var requiresHumanReview = false;
            var riskFactors = new List<string>();

            // Check confidence threshold
            if (confidence < ConfidenceThreshold)
            {
                riskLevel = RiskLevel.High;
                requiresHumanReview = true;
                riskFactors.Add("Low confidence score");
            }

            // Check financial impact
            if (decision.ContainsKey("financial_impact"))
            {
                var amount = Convert.ToDouble(decision["financial_impact"]);
                if (amount > 10000)
                {
                    riskLevel = RiskLevel.Critical;
                    requiresHumanReview = true;
                    riskFactors.Add("High financial impact");
                }
            }

            // Check sensitive data access
            if (decision.ContainsKey("accesses_pii") &&
                Convert.ToBoolean(decision["accesses_pii"]))
            {
                if (riskLevel < RiskLevel.Medium)
                {
                    riskLevel = RiskLevel.Medium;
                }
                riskFactors.Add("Accesses PII data");
            }

            var riskAssessment = new Dictionary<string, object>
            {
                { "agent_id", agentId },
                { "risk_level", riskLevel.ToString() },
                { "requires_human_review", requiresHumanReview },
                { "risk_factors", riskFactors },
                { "confidence", confidence }
            };

            if (requiresHumanReview)
            {
                _logger.LogWarning(
                    "Decision requires human review: agent_id={AgentId}, risk_level={RiskLevel}",
                    agentId, riskLevel);
            }

            return riskAssessment;
        }

        public void EnableCircuitBreaker(string agentId, string reason)
        {
            _logger.LogError(
                "Circuit breaker activated: agent_id={AgentId}, reason={Reason}",
                agentId, reason);

            var circuitBreaker = new Dictionary<string, object>
            {
                { "agent_id", agentId },
                { "status", "open" },
                { "reason", reason },
                { "activated_at", DateTime.UtcNow }
            };

            // await _circuitBreakerRepository.SaveAsync(circuitBreaker);
        }

        public async Task<bool> CheckCircuitBreakerAsync(string agentId)
        {
            // In production, query circuit breaker state from repository
            // Return false if circuit is open (agent disabled)
            return await Task.FromResult(true);
        }

        public Dictionary<string, object> ApplyConfidenceThreshold(
            string agentId,
            double confidence,
            Dictionary<string, object> decision)
        {
            if (confidence < ConfidenceThreshold)
            {
                _logger.LogWarning(
                    "Confidence below threshold: agent_id={AgentId}, confidence={Confidence}, threshold={Threshold}",
                    agentId, confidence, ConfidenceThreshold);

                return new Dictionary<string, object>
                {
                    { "approved", false },
                    { "reason", "Confidence below threshold" },
                    { "requires_review", true },
                    { "confidence", confidence }
                };
            }

            return new Dictionary<string, object>
            {
                { "approved", true },
                { "confidence", confidence }
            };
        }

        private int GetRequestCount(string userId)
        {
            // In production, query last minute request count from cache/database
            return 45; // Simulated
        }

        public async Task<bool> RequiresHumanApprovalAsync(
            string agentId,
            Dictionary<string, object> action)
        {
            var requiresApproval = false;

            // High-risk actions always require approval
            if (action.ContainsKey("action_type"))
            {
                var actionType = action["action_type"].ToString();
                var highRiskActions = new[] { "delete", "transfer_funds", "modify_permissions" };

                if (highRiskActions.Contains(actionType))
                {
                    requiresApproval = true;
                    _logger.LogWarning(
                        "High-risk action requires approval: agent_id={AgentId}, action_type={ActionType}",
                        agentId, actionType);
                }
            }

            return await Task.FromResult(requiresApproval);
        }
    }
}
```

---

## Success Criteria

- [ ] Rate limiting operational
- [ ] Confidence thresholds enforced
- [ ] Human-in-the-loop triggers functional
- [ ] Circuit breakers implemented

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
