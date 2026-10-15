### Step 4: Pillar 4 - Observability (Audit Everything)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode
from prometheus_client import Counter, Histogram, Gauge
import hashlib
import json

class AgentObservability:
    """
    AI Agent Observability.

    Pillar 4: Audit Everything
    - Distributed tracing
    - Structured logging
    - Metrics collection
    - Data lineage
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._setup_tracing()
        self._setup_metrics()

    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing."""
        provider = TracerProvider()

        exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",
            insecure=True
        )

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(__name__)

    def _setup_metrics(self):
        """Initialize Prometheus metrics."""
        self.agent_requests = Counter(
            'agent_requests_total',
            'Total agent requests',
            ['agent_name', 'status']
        )

        self.agent_latency = Histogram(
            'agent_request_duration_seconds',
            'Agent request latency',
            ['agent_name'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        self.llm_tokens = Counter(
            'llm_tokens_total',
            'LLM tokens used',
            ['agent_name', 'model', 'token_type']
        )

        self.llm_cost = Counter(
            'llm_cost_usd_total',
            'LLM cost in USD',
            ['agent_name', 'model']
        )

        self.guardrail_triggers = Counter(
            'guardrail_triggers_total',
            'Guardrail triggers',
            ['agent_name', 'guardrail_name']
        )

    def trace_agent_execution(
        self,
        user_query: str,
        user_id: str,
        session_id: str
    ):
        """
        Create root span for agent execution.

        Traces capture end-to-end workflow:
        Query → Reasoning → Tool calls → Response
        """
        return self.tracer.start_as_current_span(
            "agent.execute",
            kind=trace.SpanKind.SERVER,
            attributes={
                "agent.name": self.agent_name,
                "query.text": user_query[:200],
                "query.length": len(user_query),
                "user.id": user_id,
                "session.id": session_id
            }
        )

    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        parameters: Dict
    ):
        """
        Trace LLM API call.

        Captures:
        - Model and parameters
        - Token usage and cost
        - Latency
        """
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        return self.tracer.start_as_current_span(
            "llm.call",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.request.max_tokens": parameters.get("max_tokens", 1000),
                "gen_ai.request.temperature": parameters.get("temperature", 0.7),
                "gen_ai.prompt.hash": prompt_hash,
                "gen_ai.prompt.length": len(prompt)
            }
        )

    def trace_tool_invocation(
        self,
        tool_name: str,
        tool_input: Dict
    ):
        """
        Trace tool invocation.

        Captures what external systems agent accessed.
        """
        return self.tracer.start_as_current_span(
            f"tool.{tool_name}",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "tool.name": tool_name,
                "tool.input.size": len(json.dumps(tool_input)),
                "tool.input.keys": list(tool_input.keys())
            }
        )

    def log_agent_decision(
        self,
        decision: str,
        reasoning: str,
        confidence: float,
        alternatives: List[str],
        context: Dict
    ):
        """
        Log agent decision with reasoning.

        Critical for:
        - Debugging (why did agent do that?)
        - Auditing (what influenced decision?)
        - Compliance (demonstrate accountability)
        """
        decision_log = {
            "event_type": "agent_decision",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": self.agent_name,

            # Decision details
            "decision": decision,
            "reasoning": reasoning[:500],
            "confidence": confidence,
            "alternatives_considered": alternatives,

            # Context
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
            "trace_id": context.get("trace_id"),

            # Governance
            "decision_id": str(uuid.uuid4()),
            "reviewable": True,
            "automated": True
        }

        logger.info("Agent decision", extra=decision_log)

    def record_llm_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency: float
    ):
        """Record LLM usage metrics."""
        self.llm_tokens.labels(
            agent_name=self.agent_name,
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)

        self.llm_tokens.labels(
            agent_name=self.agent_name,
            model=model,
            token_type="completion"
        ).inc(completion_tokens)

        self.llm_cost.labels(
            agent_name=self.agent_name,
            model=model
        ).inc(cost)

    def record_guardrail_trigger(
        self,
        guardrail_name: str,
        trigger_reason: str,
        blocked_action: str
    ):
        """Log guardrail trigger."""
        self.guardrail_triggers.labels(
            agent_name=self.agent_name,
            guardrail_name=guardrail_name
        ).inc()

        logger.warning("Guardrail triggered", extra={
            "event_type": "guardrail_trigger",
            "agent_name": self.agent_name,
            "guardrail_name": guardrail_name,
            "trigger_reason": trigger_reason,
            "blocked_action": blocked_action,
            "timestamp": datetime.utcnow().isoformat()
        })
```
