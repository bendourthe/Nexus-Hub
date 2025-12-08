---
template_id: compliance_governance_agent_observability_python
template_name: AI Agent Observability - Python
version: 1.0.0
last_updated: 2025-12-05
language: python
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - ai_agent_governance/README.md
  - compliance_frameworks/python_nist_ai_rmf.md
  - compliance_frameworks/python_soc2_compliance.md
related_templates:
  - ai_agent_governance/python_agent_lifecycle.md
  - ai_agent_governance/python_agent_security.md
  - compliance_frameworks/python_iso27001_implementation.md
tools:
  - opentelemetry (distributed tracing)
  - prometheus (metrics)
  - langsmith (LLM tracing)
  - arize (AI observability)
  - mlflow (experiment tracking)
tags:
  - observability
  - ai-agents
  - tracing
  - monitoring
  - audit-everything
  - four-pillars
  - python
---

# AI Agent Observability - Python

**Pillar 4: 🔍 Observability - Audit Everything**

Comprehensive observability for AI agents with distributed tracing, lineage tracking, and audit logging

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### What is AI Agent Observability?

**AI Agent Observability** is the ability to measure and understand the internal state of AI agents by examining their outputs. For autonomous AI agents, this means comprehensive tracking of:

- **Agent decisions** - What actions the agent took and why
- **Data lineage** - What data influenced each decision
- **Tool usage** - What external tools/APIs the agent called
- **Token consumption** - LLM API usage and costs
- **Errors and failures** - What went wrong and recovery attempts
- **Performance metrics** - Latency, throughput, success rates

### The 4 Pillars of AI Agent Governance

This template implements **Pillar 4: Observability (Audit Everything)**:

1. 🔄 **Lifecycle Management** (Separation of Duties) - Version control, CI/CD
2. ⚠️ **Risk Management** (Defense in Depth) - PII detection, guardrails
3. 🔒 **Security** (Least Privilege) - Authentication, secrets management
4. **🔍 Observability (Audit Everything)** ← **THIS TEMPLATE**

**Principle**: "Audit Everything" - Every agent action, decision, and data access must be logged, traceable, and auditable for compliance, debugging, and continuous improvement.

### Why AI Agents Need Enhanced Observability

Traditional application monitoring is insufficient for AI agents because:

- **Non-deterministic** - Same input can produce different outputs
- **Autonomous** - Agents make decisions without human intervention
- **Multi-step reasoning** - Complex chains of thought requiring step-by-step tracing
- **External dependencies** - Calls to LLMs, vector DBs, APIs must be tracked
- **Compliance requirements** - SOC 2 CC7.2, ISO 27001 Control 8.16, GDPR Article 30
- **Cost management** - Token usage can be expensive and unpredictable
- **Hallucination detection** - Need to trace reasoning to identify false outputs

---

## Observability Architecture

### The 3 Pillars of Observability

Classic observability consists of 3 pillars, extended for AI agents:

#### 1. Logs

**Traditional**: Application event logs
**AI Agents**: Structured agent decision logs with:
- Agent reasoning steps
- Tool invocation logs
- Token usage per LLM call
- PII detection results
- Guardrail triggers

#### 2. Metrics

**Traditional**: System performance metrics (CPU, memory, latency)
**AI Agents**: AI-specific metrics:
- Agent success/failure rates
- Average decision latency
- Token consumption rate
- Cost per agent invocation
- Hallucination detection rate
- Guardrail violation frequency

#### 3. Traces

**Traditional**: Distributed request tracing
**AI Agents**: End-to-end agent execution traces:
- User query → Agent reasoning → Tool calls → LLM interactions → Final response
- Data lineage (what data influenced the decision)
- Multi-agent collaboration traces

### OpenTelemetry for AI Agents

**OpenTelemetry (OTel)** is the CNCF standard for observability. For AI agents, we extend OTel with:

- **Custom spans**: Agent reasoning steps, LLM calls, tool executions
- **Semantic conventions**: AI-specific attributes (model name, token count, prompt)
- **Context propagation**: Trace context across async agent operations
- **Instrumentation**: Auto-instrument LangChain, LlamaIndex, OpenAI SDK

---

## Implementation Roadmap

### Phase 1: Distributed Tracing Setup (Week 1)

**Deliverables**:
1. OpenTelemetry instrumentation
2. Trace backend (Jaeger, Zipkin, or cloud provider)
3. Agent span creation for all operations
4. Context propagation

**Code**: See [Distributed Tracing](#distributed-tracing-implementation)

### Phase 2: Structured Logging (Week 2)

**Deliverables**:
1. JSON structured logging
2. Agent decision logging
3. Tool invocation logging
4. PII redaction in logs
5. Log aggregation (ELK, Splunk, Datadog)

**Code**: See [Structured Logging](#structured-logging-implementation)

### Phase 3: Metrics and Dashboards (Week 3)

**Deliverables**:
1. Prometheus metrics export
2. Grafana dashboards
3. Alert rules (cost, errors, latency)
4. Token usage tracking
5. Business metrics (agent success rate)

**Code**: See [Metrics Collection](#metrics-collection-implementation)

### Phase 4: Data Lineage and Provenance (Week 4)

**Deliverables**:
1. Data lineage tracking
2. Prompt versioning
3. Model version tracking
4. Reproducibility logs
5. Compliance audit trail

**Code**: See [Data Lineage](#data-lineage-implementation)

---

## Distributed Tracing Implementation

### OpenTelemetry Setup for AI Agents

**Standard**: OpenTelemetry (CNCF standard for observability)

**Implementation**:

```python
# OpenTelemetry setup for AI agents
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Status, StatusCode
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AIAgentTracing:
    """
    OpenTelemetry distributed tracing for AI agents.

    Observability Pillar: Audit Everything
    Compliance: SOC 2 CC7.2 (System monitoring), ISO 27001 Control 8.16

    Traces capture:
    - Agent execution flow
    - LLM API calls (model, tokens, cost)
    - Tool invocations
    - Decision reasoning
    - Errors and retries
    """

    def __init__(self, service_name: str = "ai-agent", environment: str = "production"):
        """Initialize OpenTelemetry tracing."""

        # Define service resource
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
            "service.type": "ai_agent"
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Configure span exporter (OTLP to backend)
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",  # Jaeger, Tempo, or cloud provider
            insecure=True
        )

        # Add batch processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

    def trace_agent_execution(
        self,
        agent_name: str,
        user_query: str,
        context: Dict[str, Any]
    ):
        """
        Create root span for agent execution.

        Captures end-to-end agent workflow.
        """
        with self.tracer.start_as_current_span(
            "agent.execute",
            kind=trace.SpanKind.SERVER,
            attributes={
                # Agent attributes
                "agent.name": agent_name,
                "agent.version": context.get("agent_version", "1.0.0"),
                "agent.type": context.get("agent_type", "autonomous"),

                # Query attributes
                "query.text": user_query[:200],  # Truncate long queries
                "query.length": len(user_query),
                "query.language": context.get("language", "en"),

                # User attributes
                "user.id": context.get("user_id"),
                "user.session_id": context.get("session_id"),

                # Execution context
                "environment": context.get("environment", "production")
            }
        ) as span:
            try:
                # Agent execution logic here
                result = self._execute_agent_logic(agent_name, user_query, context)

                # Record success
                span.set_attribute("agent.status", "success")
                span.set_attribute("response.length", len(str(result)))
                span.set_status(Status(StatusCode.OK))

                return result

            except Exception as e:
                # Record failure
                span.set_attribute("agent.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)

                logger.error("Agent execution failed", extra={
                    "agent_name": agent_name,
                    "error": str(e),
                    "trace_id": span.get_span_context().trace_id
                })

                raise

    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        parameters: Dict[str, Any]
    ) -> Dict:
        """
        Trace LLM API call.

        Captures model invocation with token usage and cost.
        """
        with self.tracer.start_as_current_span(
            "llm.call",
            kind=trace.SpanKind.CLIENT,
            attributes={
                # LLM attributes (OpenTelemetry semantic conventions for GenAI)
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.request.max_tokens": parameters.get("max_tokens", 1000),
                "gen_ai.request.temperature": parameters.get("temperature", 0.7),

                # Prompt attributes
                "gen_ai.prompt.length": len(prompt),
                "gen_ai.prompt.hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],

                # Cost tracking
                "gen_ai.request.top_p": parameters.get("top_p", 1.0)
            }
        ) as span:
            try:
                import openai

                # Call LLM
                start_time = time.time()
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    **parameters
                )
                latency = time.time() - start_time

                # Extract usage
                usage = response.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)

                # Calculate cost (example pricing for GPT-4)
                cost = self._calculate_llm_cost(model, prompt_tokens, completion_tokens)

                # Record token usage
                span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)
                span.set_attribute("gen_ai.usage.total_tokens", total_tokens)
                span.set_attribute("gen_ai.response.cost_usd", cost)
                span.set_attribute("gen_ai.response.latency_ms", latency * 1000)
                span.set_attribute("gen_ai.response.finish_reason", response.get("choices", [{}])[0].get("finish_reason"))

                span.set_status(Status(StatusCode.OK))

                logger.info("LLM call completed", extra={
                    "model": model,
                    "tokens": total_tokens,
                    "cost": cost,
                    "latency_ms": latency * 1000,
                    "trace_id": format(span.get_span_context().trace_id, '032x')
                })

                return {
                    "response": response.get("choices", [{}])[0].get("message", {}).get("content"),
                    "usage": usage,
                    "cost": cost,
                    "latency": latency
                }

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_tool_invocation(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Any:
        """
        Trace agent tool invocation.

        Captures tool calls (database queries, API requests, file operations).
        """
        with self.tracer.start_as_current_span(
            f"tool.{tool_name}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "tool.name": tool_name,
                "tool.input.size": len(str(tool_input)),
                "tool.input.keys": list(tool_input.keys())
            }
        ) as span:
            try:
                # Tool execution
                result = self._execute_tool(tool_name, tool_input)

                span.set_attribute("tool.status", "success")
                span.set_attribute("tool.output.size", len(str(result)))
                span.set_status(Status(StatusCode.OK))

                return result

            except Exception as e:
                span.set_attribute("tool.status", "error")
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def _calculate_llm_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate LLM API cost.

        Pricing (as of 2025, update regularly):
        - GPT-4: $0.03/1K prompt, $0.06/1K completion
        - GPT-4 Turbo: $0.01/1K prompt, $0.03/1K completion
        - GPT-3.5 Turbo: $0.0005/1K prompt, $0.0015/1K completion
        """
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015}
        }

        model_pricing = pricing.get(model, {"prompt": 0.01, "completion": 0.03})

        cost = (
            (prompt_tokens / 1000) * model_pricing["prompt"] +
            (completion_tokens / 1000) * model_pricing["completion"]
        )

        return round(cost, 6)
```

---

## Structured Logging Implementation

### Agent Decision Logging

**Standard**: JSON structured logging for machine parsing

**Implementation**:

```python
# Structured logging for AI agents
import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from pythonjsonlogger import jsonlogger

class AIAgentLogger:
    """
    Structured logging for AI agents.

    Observability Pillar: Audit Everything
    Compliance:
    - SOC 2 CC7.2 (System monitoring)
    - ISO 27001 Control 8.16 (Monitoring activities)
    - GDPR Article 30 (Records of processing activities)

    Logs capture:
    - Agent decisions and reasoning
    - Tool invocations
    - Data access (with PII redaction)
    - Security events
    - Cost tracking
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure JSON structured logger."""
        logger = logging.getLogger(f"ai_agent.{self.agent_name}")
        logger.setLevel(logging.INFO)

        # JSON formatter
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(agent_name)s %(event_type)s %(message)s',
            timestamp=True
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Also log to file for audit trail
        file_handler = logging.FileHandler(f"logs/agent_{self.agent_name}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def log_agent_decision(
        self,
        decision: str,
        reasoning: str,
        confidence: float,
        alternatives_considered: List[str],
        context: Dict[str, Any]
    ):
        """
        Log agent decision with reasoning.

        Critical for:
        - Debugging (why did agent do that?)
        - Auditing (what data influenced decision?)
        - Compliance (demonstrate accountability)
        """
        self.logger.info("Agent decision", extra={
            "event_type": "agent_decision",
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),

            # Decision details
            "decision": decision,
            "reasoning": reasoning[:500],  # Truncate long reasoning
            "confidence": confidence,
            "alternatives_considered": alternatives_considered,

            # Context
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
            "trace_id": context.get("trace_id"),

            # Governance
            "decision_id": generate_uuid(),
            "reviewable": True,  # Can be reviewed by humans
            "automated": True
        })

    def log_tool_invocation(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Log tool invocation.

        Tracks what external systems agent accessed.
        """
        # Redact PII from tool input/output
        redacted_input = self._redact_pii(tool_input)
        redacted_output = self._redact_pii(str(tool_output)[:200])

        self.logger.info("Tool invocation", extra={
            "event_type": "tool_invocation",
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),

            # Tool details
            "tool_name": tool_name,
            "tool_input": redacted_input,
            "tool_output": redacted_output,
            "success": success,
            "error": error,

            # Audit trail
            "invocation_id": generate_uuid()
        })

    def log_llm_interaction(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost: float,
        latency_ms: float
    ):
        """
        Log LLM API interaction.

        Tracks token usage and cost for budgeting.
        """
        # Hash prompt for deduplication
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        # Detect PII in prompt/response
        pii_in_prompt = self._detect_pii(prompt)
        pii_in_response = self._detect_pii(response)

        self.logger.info("LLM interaction", extra={
            "event_type": "llm_interaction",
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),

            # LLM details
            "model": model,
            "prompt_hash": prompt_hash,
            "prompt_length": len(prompt),
            "response_length": len(response),

            # Usage
            "tokens_used": tokens_used,
            "cost_usd": cost,
            "latency_ms": latency_ms,

            # Privacy
            "pii_in_prompt": pii_in_prompt,
            "pii_in_response": pii_in_response,

            # Audit
            "interaction_id": generate_uuid()
        })

        # Alert if PII detected
        if pii_in_prompt or pii_in_response:
            self.log_security_event(
                event_type="pii_in_llm",
                severity="high",
                description=f"PII detected in LLM interaction (model: {model})"
            )

    def log_guardrail_trigger(
        self,
        guardrail_name: str,
        trigger_reason: str,
        blocked_action: str,
        risk_score: float
    ):
        """
        Log guardrail trigger.

        Tracks when agent attempted risky action that was blocked.
        """
        self.logger.warning("Guardrail triggered", extra={
            "event_type": "guardrail_trigger",
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),

            # Guardrail details
            "guardrail_name": guardrail_name,
            "trigger_reason": trigger_reason,
            "blocked_action": blocked_action,
            "risk_score": risk_score,

            # Audit
            "trigger_id": generate_uuid()
        })

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        context: Dict[str, Any] = None
    ):
        """
        Log security event.

        High-priority logs for security incidents.
        """
        self.logger.warning("Security event", extra={
            "event_type": "security_event",
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),

            # Security details
            "security_event_type": event_type,
            "severity": severity,
            "description": description,
            "context": context or {},

            # Response
            "requires_investigation": severity in ["high", "critical"],
            "security_event_id": generate_uuid()
        })

    def _redact_pii(self, data: Any) -> Any:
        """Redact PII from logs."""
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        if not isinstance(data, str):
            data = str(data)

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        # Detect PII
        results = analyzer.analyze(text=data, language='en')

        # Anonymize
        anonymized = anonymizer.anonymize(text=data, analyzer_results=results)

        return anonymized.text

    def _detect_pii(self, text: str) -> bool:
        """Detect if text contains PII."""
        from presidio_analyzer import AnalyzerEngine

        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, language='en')

        return len(results) > 0
```

---

## Metrics Collection Implementation

### Prometheus Metrics for AI Agents

**Standard**: Prometheus metrics with Grafana dashboards

**Implementation**:

```python
# Prometheus metrics for AI agents
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client import start_http_server
from typing import Dict
import time

class AIAgentMetrics:
    """
    Prometheus metrics for AI agents.

    Observability Pillar: Audit Everything

    Metrics categories:
    - Operational metrics (latency, errors, throughput)
    - Business metrics (agent success rate, user satisfaction)
    - Cost metrics (token usage, LLM costs)
    - AI-specific metrics (hallucination rate, guardrail triggers)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

        # Operational Metrics
        self.agent_requests_total = Counter(
            'agent_requests_total',
            'Total number of agent requests',
            ['agent_name', 'status']
        )

        self.agent_request_duration = Histogram(
            'agent_request_duration_seconds',
            'Agent request latency',
            ['agent_name'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        self.agent_errors_total = Counter(
            'agent_errors_total',
            'Total number of agent errors',
            ['agent_name', 'error_type']
        )

        # LLM Metrics
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total LLM API requests',
            ['agent_name', 'model']
        )

        self.llm_tokens_total = Counter(
            'llm_tokens_total',
            'Total LLM tokens used',
            ['agent_name', 'model', 'token_type']  # prompt, completion
        )

        self.llm_cost_total = Counter(
            'llm_cost_usd_total',
            'Total LLM cost in USD',
            ['agent_name', 'model']
        )

        self.llm_latency = Histogram(
            'llm_latency_seconds',
            'LLM API latency',
            ['agent_name', 'model'],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
        )

        # AI-Specific Metrics
        self.hallucination_detected_total = Counter(
            'hallucination_detected_total',
            'Total hallucinations detected',
            ['agent_name']
        )

        self.guardrail_triggers_total = Counter(
            'guardrail_triggers_total',
            'Total guardrail triggers',
            ['agent_name', 'guardrail_name']
        )

        self.pii_detected_total = Counter(
            'pii_detected_total',
            'Total PII detections',
            ['agent_name', 'location']  # prompt, response, tool_input
        )

        # Business Metrics
        self.agent_success_rate = Gauge(
            'agent_success_rate',
            'Agent success rate (0-1)',
            ['agent_name']
        )

        self.user_satisfaction_score = Gauge(
            'user_satisfaction_score',
            'User satisfaction score (1-5)',
            ['agent_name']
        )

        # Tool Metrics
        self.tool_invocations_total = Counter(
            'tool_invocations_total',
            'Total tool invocations',
            ['agent_name', 'tool_name', 'status']
        )

    def record_agent_request(self, status: str, duration: float):
        """Record agent request."""
        self.agent_requests_total.labels(
            agent_name=self.agent_name,
            status=status
        ).inc()

        self.agent_request_duration.labels(
            agent_name=self.agent_name
        ).observe(duration)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency: float
    ):
        """Record LLM API call."""
        self.llm_requests_total.labels(
            agent_name=self.agent_name,
            model=model
        ).inc()

        self.llm_tokens_total.labels(
            agent_name=self.agent_name,
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)

        self.llm_tokens_total.labels(
            agent_name=self.agent_name,
            model=model,
            token_type="completion"
        ).inc(completion_tokens)

        self.llm_cost_total.labels(
            agent_name=self.agent_name,
            model=model
        ).inc(cost)

        self.llm_latency.labels(
            agent_name=self.agent_name,
            model=model
        ).observe(latency)

    def record_guardrail_trigger(self, guardrail_name: str):
        """Record guardrail trigger."""
        self.guardrail_triggers_total.labels(
            agent_name=self.agent_name,
            guardrail_name=guardrail_name
        ).inc()

    def record_hallucination(self):
        """Record hallucination detection."""
        self.hallucination_detected_total.labels(
            agent_name=self.agent_name
        ).inc()

    def record_pii_detection(self, location: str):
        """Record PII detection."""
        self.pii_detected_total.labels(
            agent_name=self.agent_name,
            location=location
        ).inc()

    def update_success_rate(self, success_rate: float):
        """Update agent success rate."""
        self.agent_success_rate.labels(
            agent_name=self.agent_name
        ).set(success_rate)

    def start_metrics_server(self, port: int = 8000):
        """Start Prometheus metrics HTTP server."""
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
```

---

## Data Lineage Implementation

### Data Provenance Tracking

**Purpose**: Track what data influenced each agent decision (GDPR Article 15, NIST AI RMF MAP 4.1)

**Implementation**:

```python
# Data lineage and provenance tracking
from typing import List, Dict, Any
from datetime import datetime
import networkx as nx

class DataLineageTracker:
    """
    Track data lineage for AI agent decisions.

    Observability Pillar: Audit Everything
    Compliance:
    - GDPR Article 15 (Right to explanation)
    - NIST AI RMF MAP 4.1 (Impacts assessed and documented)
    - SOC 2 CC7.2 (System monitoring)

    Lineage captures:
    - What data was used in decision
    - Where data came from (source)
    - What transformations applied
    - What models/prompts used
    - What outputs generated
    """

    def __init__(self):
        # Directed acyclic graph for lineage
        self.lineage_graph = nx.DiGraph()

    def record_data_source(
        self,
        source_id: str,
        source_type: str,
        source_location: str,
        data_classification: str,
        timestamp: datetime = None
    ) -> str:
        """
        Record data source.

        Examples: Database, API, file, user input
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        node_id = f"source_{source_id}"

        self.lineage_graph.add_node(
            node_id,
            node_type="data_source",
            source_type=source_type,
            location=source_location,
            classification=data_classification,
            timestamp=timestamp.isoformat()
        )

        logger.info("Data source recorded", extra={
            "event": "lineage_source",
            "source_id": source_id,
            "source_type": source_type
        })

        return node_id

    def record_transformation(
        self,
        transformation_id: str,
        transformation_type: str,
        input_nodes: List[str],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Record data transformation.

        Examples: Filtering, aggregation, anonymization, vectorization
        """
        node_id = f"transform_{transformation_id}"

        self.lineage_graph.add_node(
            node_id,
            node_type="transformation",
            transformation_type=transformation_type,
            parameters=parameters,
            timestamp=datetime.utcnow().isoformat()
        )

        # Add edges from inputs to transformation
        for input_node in input_nodes:
            self.lineage_graph.add_edge(input_node, node_id)

        return node_id

    def record_model_inference(
        self,
        inference_id: str,
        model_name: str,
        model_version: str,
        input_nodes: List[str],
        hyperparameters: Dict[str, Any]
    ) -> str:
        """
        Record model inference.

        Tracks what data influenced model prediction.
        """
        node_id = f"inference_{inference_id}"

        self.lineage_graph.add_node(
            node_id,
            node_type="model_inference",
            model_name=model_name,
            model_version=model_version,
            hyperparameters=hyperparameters,
            timestamp=datetime.utcnow().isoformat()
        )

        # Add edges from inputs
        for input_node in input_nodes:
            self.lineage_graph.add_edge(input_node, node_id)

        return node_id

    def record_agent_decision(
        self,
        decision_id: str,
        agent_name: str,
        decision: str,
        input_nodes: List[str],
        confidence: float
    ) -> str:
        """
        Record agent decision.

        Links decision to all data sources that influenced it.
        """
        node_id = f"decision_{decision_id}"

        self.lineage_graph.add_node(
            node_id,
            node_type="agent_decision",
            agent_name=agent_name,
            decision=decision,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat()
        )

        # Add edges from inputs
        for input_node in input_nodes:
            self.lineage_graph.add_edge(input_node, node_id)

        return node_id

    def get_decision_lineage(self, decision_id: str) -> Dict:
        """
        Get complete lineage for a decision.

        Returns all data sources, transformations, models that influenced decision.
        """
        decision_node = f"decision_{decision_id}"

        if decision_node not in self.lineage_graph:
            raise ValueError(f"Decision {decision_id} not found in lineage graph")

        # Get all ancestors (backward traversal)
        ancestors = nx.ancestors(self.lineage_graph, decision_node)

        lineage = {
            "decision_id": decision_id,
            "decision": self.lineage_graph.nodes[decision_node].get("decision"),
            "timestamp": self.lineage_graph.nodes[decision_node].get("timestamp"),

            # Data sources
            "data_sources": [
                self.lineage_graph.nodes[node]
                for node in ancestors
                if self.lineage_graph.nodes[node]["node_type"] == "data_source"
            ],

            # Transformations
            "transformations": [
                self.lineage_graph.nodes[node]
                for node in ancestors
                if self.lineage_graph.nodes[node]["node_type"] == "transformation"
            ],

            # Model inferences
            "model_inferences": [
                self.lineage_graph.nodes[node]
                for node in ancestors
                if self.lineage_graph.nodes[node]["node_type"] == "model_inference"
            ],

            # Full graph (for visualization)
            "lineage_graph": nx.node_link_data(
                self.lineage_graph.subgraph(ancestors | {decision_node})
            )
        }

        logger.info("Decision lineage retrieved", extra={
            "event": "lineage_retrieval",
            "decision_id": decision_id,
            "data_sources_count": len(lineage["data_sources"])
        })

        return lineage

    def export_lineage_report(self, decision_id: str, format: str = "json") -> str:
        """
        Export lineage report for compliance/audit.

        GDPR Article 15: Right to explanation
        """
        lineage = self.get_decision_lineage(decision_id)

        if format == "json":
            return json.dumps(lineage, indent=2)
        elif format == "graphviz":
            return self._export_graphviz(decision_id)
        else:
            raise ValueError(f"Unsupported format: {format}")
```

---

## Integration with Compliance Frameworks

### Observability Supports Multiple Frameworks

| Framework | Control | How Observability Helps |
|-----------|---------|-------------------------|
| **SOC 2** | CC7.2 (System monitoring) | Distributed tracing, metrics, alerts |
| **SOC 2** | CC7.3 (Evaluate and communicate processing) | Structured logging, dashboards |
| **ISO 27001** | Control 8.16 (Monitoring activities) | Comprehensive audit logs |
| **GDPR** | Article 15 (Right of access) | Data lineage for explaining decisions |
| **GDPR** | Article 30 (Records of processing) | Processing activity logs |
| **NIST AI RMF** | MEASURE 1.1 (Metrics defined) | AI-specific metrics (hallucination, bias) |
| **NIST AI RMF** | MANAGE 3.1 (Risk monitoring) | Continuous monitoring dashboards |

---

## Success Criteria

### Distributed Tracing Operational

- [ ] OpenTelemetry instrumented for all agent operations
- [ ] Trace backend configured (Jaeger/Zipkin/Tempo)
- [ ] End-to-end traces visible in UI
- [ ] Context propagation across async operations
- [ ] Trace retention policy defined (90 days minimum for compliance)

### Structured Logging Complete

- [ ] JSON logs for all agent decisions
- [ ] PII redacted in logs automatically
- [ ] Log aggregation configured (ELK/Splunk/Datadog)
- [ ] Log retention per compliance requirements (1-7 years)
- [ ] Security event logs monitored 24/7

### Metrics and Dashboards Live

- [ ] Prometheus metrics exported
- [ ] Grafana dashboards created (operational, business, cost)
- [ ] Alert rules configured (error rate, cost budget, latency SLA)
- [ ] Token usage tracked per user/agent
- [ ] Cost attribution per business unit

### Data Lineage Implemented

- [ ] Lineage tracked for all agent decisions
- [ ] Data provenance retrievable within 1 minute
- [ ] Lineage reports exportable (JSON, Graphviz)
- [ ] Model versions tracked
- [ ] Prompt versions tracked

---

## Common Pitfalls

### ❌ Logging Sensitive Data

**Problem**: Logging PII or secrets in plain text.

**Solution**: Automatic PII redaction using Presidio. Never log API keys, passwords, tokens.

### ❌ No Cost Attribution

**Problem**: LLM costs ballooning without tracking who/what caused it.

**Solution**: Tag all LLM calls with user_id, agent_name, business_unit for cost attribution.

### ❌ Ignoring Cardinality

**Problem**: High-cardinality labels (e.g., trace_id) in Prometheus metrics causing memory issues.

**Solution**: Use traces for high-cardinality data, metrics for low-cardinality aggregations.

### ❌ No Sampling

**Problem**: Tracing 100% of requests in high-traffic production.

**Solution**: Implement probabilistic sampling (e.g., 10% of requests) or intelligent sampling (100% errors, 1% successes).

---

## Resources

### OpenTelemetry

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/) - Official docs
- [OpenTelemetry Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) - GenAI tracing standards
- [OpenLLMetry](https://github.com/traceloop/openllmetry) - LLM observability with OTel

### AI Observability Platforms

- **LangSmith** - LangChain tracing and evaluation
- **Arize AI** - ML observability and monitoring
- **Weights & Biases** - Experiment tracking
- **Evidently AI** - ML monitoring and testing
- **WhyLabs** - Data and ML monitoring

### Tools

- **Presidio** - PII detection and anonymization
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization
- **Jaeger** - Distributed tracing backend

---

## Changelog

### Version 1.0.0 - 2025-12-05

**Added**:
- Complete observability implementation for AI agents (4 Pillars - Pillar 4)
- OpenTelemetry distributed tracing with AI-specific spans
- LLM call tracing (model, tokens, cost, latency)
- Tool invocation tracing
- Structured JSON logging with PII redaction
- Agent decision logging with reasoning
- Guardrail trigger logging
- Prometheus metrics (operational, business, cost, AI-specific)
- Token usage and cost tracking
- Hallucination detection metrics
- Data lineage tracking with directed acyclic graph
- Provenance for GDPR right to explanation
- Integration with SOC 2, ISO 27001, GDPR, NIST AI RMF

**Framework Coverage**:
- 4 Pillars: Observability (Audit Everything)
- 3 Pillars of Observability: Logs, Metrics, Traces
- OpenTelemetry semantic conventions for GenAI

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
