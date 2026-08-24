---
name: ai-agent-governance
description: Implement the 4 Pillars Framework for AI agent governance (Lifecycle, Risk, Security, Observability). Use when deploying autonomous AI agents, implementing agent guardrails, establishing agent security controls, or auditing AI agent behavior.
summary_l0: "Implement AI agent governance with lifecycle, risk, security, and observability pillars"
overview_l1: "This skill implements comprehensive governance for autonomous AI agents using the 4 Pillars Framework covering Lifecycle Management, Risk Management, Security, and Observability. Use it when deploying autonomous AI agents to production, implementing agent guardrails and safety controls, establishing security for agentic AI systems, tracking and auditing agent behavior, managing AI agent risks, or complying with AI regulations (NIST AI RMF, ISO 42001). Key capabilities include agent lifecycle management (registration, versioning, decommission), risk assessment and mitigation for autonomous agents, security controls (input validation, output filtering, privilege management), observability instrumentation (structured logging, trace propagation, cost tracking), and regulatory compliance mapping. The expected output is a governance framework with policies, controls, monitoring dashboards, and audit trails for AI agent operations. Trigger phrases: AI agent governance, agent guardrails, agent security, agentic AI, autonomous agent, agent observability, 4 pillars, agent lifecycle."
---

# AI Agent Governance - 4 Pillars Framework

Implement comprehensive governance for autonomous AI agents using the 4 Pillars Framework: Lifecycle Management, Risk Management, Security, and Observability.

## When to Use This Skill

Use this skill when you need to:

- Deploy autonomous AI agents to production
- Implement agent guardrails and safety controls
- Establish security for agentic AI systems
- Track and audit agent behavior
- Manage AI agent risks
- Comply with AI regulations (NIST AI RMF, ISO 42001)

**Trigger phrases**: "AI agent governance", "agent guardrails", "agent security", "agentic AI", "autonomous agent", "agent observability", "4 pillars", "agent lifecycle"

## What This Skill Does

### Why AI Agents Need Special Governance

Traditional software governance is insufficient for AI agents because:

| Traditional Software | AI Agents |
|---------------------|-----------|
| Deterministic | Non-deterministic |
| Predictable | Autonomous |
| Limited scope | Broad capabilities |
| Explicit programming | Emergent behaviors |
| Fixed logic | Learning and evolving |

80% of organizations have encountered risky behaviors from AI agents, including improper data exposure and unauthorized system access.

### The 4 Pillars Framework

| Pillar | Principle | Key Question |
|--------|-----------|--------------|
| Lifecycle | Separation of Duties | Can you safely promote changes through environments with rollback? |
| Risk | Defense in Depth | Do you have multiple layers of protection? |
| Security | Least Privilege | Are data sources accessible only to authorized agents? |
| Observability | Audit Everything | Can you trace every tool call, data access, and decision? |

## Instructions

### Step 1: Pillar 1 - Lifecycle Management (Separation of Duties)

Full walkthrough: [step-1-pillar-1-lifecycle-management-separation-of-duties.md](references/step-1-pillar-1-lifecycle-management-separation-of-duties.md) (load this step when you reach it).

### Step 2: Pillar 2 - Risk Management (Defense in Depth)

Full walkthrough: [step-2-pillar-2-risk-management-defense-in-depth.md](references/step-2-pillar-2-risk-management-defense-in-depth.md) (load this step when you reach it).

### Step 3: Pillar 3 - Security (Least Privilege)

Full walkthrough: [step-3-pillar-3-security-least-privilege.md](references/step-3-pillar-3-security-least-privilege.md) (load this step when you reach it).

### Step 4: Pillar 4 - Observability (Audit Everything)

Full walkthrough: [step-4-pillar-4-observability-audit-everything.md](references/step-4-pillar-4-observability-audit-everything.md) (load this step when you reach it).

### Step 5: Complete Agent Governance Implementation

Full walkthrough: [step-5-complete-agent-governance-implementation.md](references/step-5-complete-agent-governance-implementation.md) (load this step when you reach it).

## Implementation Checklist

Detailed guidance lives in [implementation-checklist.md](references/implementation-checklist.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Our existing app governance already covers the agent" | Deterministic-software governance has no model for non-deterministic, autonomous behavior; an agent with a tool allowlist gap can take unauthorized actions that a code review of static logic would never surface. |
| "We added input guardrails, so prompt injection is handled" | Input filtering alone is a single layer; the Defense-in-Depth pillar requires output guardrails and tool-use guardrails too, because an injection that slips the input filter still needs the output and tool layers to block exfiltration. |
| "We log the agent's responses, so we have observability" | Logging the final response is not tracing the decision; without per-tool-call spans and logged reasoning you cannot answer 'why did the agent do that', which is exactly what an audit or incident review demands. |
| "Agents run in a trusted environment, so least privilege is overkill" | The 80% of orgs that hit risky agent behavior mostly granted broad credentials; a long-lived admin-scoped key on a non-deterministic agent is one prompt injection away from data exposure. |

## Verification

- [ ] Every agent configuration is versioned with a recorded creator, changelog, and rollback path
- [ ] Input, output, and tool-use guardrails are all active and tested against adversarial inputs
- [ ] Agent credentials are role-scoped, time-limited, and rotated on a schedule (no shared admin keys)
- [ ] OpenTelemetry traces capture every LLM call and tool invocation with decision logging
- [ ] A rollback has been exercised end-to-end and documented, not just configured
- [ ] The control-to-framework mapping (SOC 2, ISO 42001, NIST AI RMF) is documented and current

## Compliance Framework Mapping

Detailed guidance lives in [compliance-framework-mapping.md](references/compliance-framework-mapping.md) (load on demand).

## Related Skills

- [[nist-ai-rmf]] -- NIST AI Risk Management Framework this governance maps to
- [[iso42001-ai-governance]] -- ISO 42001 AI Management System the lifecycle pillar satisfies
- [[soc2-compliance]] -- SOC 2 controls the security and observability pillars feed
- [[security-review]] -- security vulnerability review for the agent's surrounding code
- [[ai-agent-development]] -- builds the agents this skill wraps with governance
- [[ai-billing-safeguards]] -- enforces the spending caps the cost-tracking observability complements
- [[agent-execution-isolation]] -- OS sandbox, credential brokering, and egress-proxy triage this pillar must ask before treating least-privilege as complete

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates compliance_governance/ai_agent_governance/


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
