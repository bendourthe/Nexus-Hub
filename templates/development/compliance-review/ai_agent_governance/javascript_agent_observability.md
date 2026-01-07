---
template_id: compliance_governance_agent_observability_javascript
template_name: AI Agent Observability - JavaScript
version: 1.0.0
last_updated: 2025-12-05
language: javascript
category: compliance_governance
phase: ai_agent_governance
phase_number: 5
difficulty: advanced
estimated_time_hours: 6-8
prerequisites:
  - ai_agent_governance/README.md
  - compliance_frameworks/javascript_nist_ai_rmf.md
related_templates:
  - ai_agent_governance/javascript_agent_lifecycle.md
  - compliance_frameworks/javascript_soc2_compliance.md
tools:
  - @opentelemetry/sdk-node (tracing)
  - prom-client (metrics)
  - winston (logging)
tags:
  - ai-observability
  - audit-everything
  - four-pillars
  - opentelemetry
  - javascript
  - nodejs
---

# AI Agent Observability - JavaScript

**🔍 Pillar 4: Observability (Audit Everything)**

Implement comprehensive observability for AI agents with OpenTelemetry tracing

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)

---

## Overview

### Observability Principle

**Audit Everything**: Every AI agent action must be traceable, auditable, and explainable

### Key Capabilities

- **Distributed Tracing**: Track requests across microservices
- **LLM Call Tracking**: Monitor all AI model invocations
- **Data Lineage**: Track data flow through AI systems
- **Audit Logging**: Immutable audit trail

---

## Implementation

```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { BatchSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { trace, context } = require('@opentelemetry/api');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

// Configure OpenTelemetry
const jaegerExporter = new JaegerExporter({
  endpoint: process.env.JAEGER_ENDPOINT || 'http://localhost:14268/api/traces'
});

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'ai-agent-system',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0'
  }),
  spanProcessor: new BatchSpanProcessor(jaegerExporter)
});

sdk.start();

// Configure structured logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'ai-agent-audit.log' }),
    new winston.transports.File({
      filename: 'ai-agent-errors.log',
      level: 'error'
    })
  ]
});

class AIAgentObservability {
  constructor() {
    this.tracer = trace.getTracer('ai-agent-tracer', '1.0.0');
  }

  /**
   * Trace complete LLM request with all parameters.
   *
   * Pillar 4: Audit Everything
   * OpenTelemetry Semantic Conventions for GenAI
   */
  async traceLLMCall(agentId, model, prompt, parameters, userId) {
    const span = this.tracer.startSpan('llm.call', {
      attributes: {
        // GenAI semantic conventions
        'gen_ai.system': 'anthropic',
        'gen_ai.request.model': model,
        'gen_ai.request.temperature': parameters.temperature || 0.7,
        'gen_ai.request.max_tokens': parameters.max_tokens || 1024,
        'gen_ai.request.top_p': parameters.top_p || 1.0,

        // Custom attributes
        'ai.agent_id': agentId,
        'ai.user_id': userId,
        'ai.prompt_length': prompt.length
      }
    });

    const callId = uuidv4();

    try {
      // Log request
      logger.info('LLM call initiated', {
        event: 'llm_call_initiated',
        callId,
        agentId,
        model,
        userId,
        promptPreview: prompt.substring(0, 100),
        parameters,
        timestamp: new Date().toISOString(),
        traceId: span.spanContext().traceId,
        spanId: span.spanContext().spanId
      });

      // Make LLM call
      const startTime = Date.now();

      const Anthropic = require('@anthropic-ai/sdk');
      const anthropic = new Anthropic({
        apiKey: process.env.ANTHROPIC_API_KEY
      });

      const message = await anthropic.messages.create({
        model,
        max_tokens: parameters.max_tokens || 1024,
        temperature: parameters.temperature || 0.7,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      const latency = Date.now() - startTime;

      // Add response attributes to span
      span.setAttributes({
        'gen_ai.response.id': message.id,
        'gen_ai.usage.input_tokens': message.usage.input_tokens,
        'gen_ai.usage.output_tokens': message.usage.output_tokens,
        'gen_ai.response.finish_reason': message.stop_reason,
        'ai.latency_ms': latency
      });

      // Calculate cost
      const cost = this.calculateLLMCost(
        model,
        message.usage.input_tokens,
        message.usage.output_tokens
      );

      span.setAttribute('gen_ai.response.cost_usd', cost);

      // Log response
      logger.info('LLM call completed', {
        event: 'llm_call_completed',
        callId,
        agentId,
        model,
        userId,
        inputTokens: message.usage.input_tokens,
        outputTokens: message.usage.output_tokens,
        totalTokens: message.usage.input_tokens + message.usage.output_tokens,
        latencyMs: latency,
        costUsd: cost,
        finishReason: message.stop_reason,
        responsePreview: message.content[0].text.substring(0, 100),
        timestamp: new Date().toISOString(),
        traceId: span.spanContext().traceId
      });

      // Store in database for audit
      await this.storeLLMCall({
        callId,
        agentId,
        model,
        userId,
        prompt,
        response: message.content[0].text,
        usage: message.usage,
        latencyMs: latency,
        costUsd: cost,
        traceId: span.spanContext().traceId,
        timestamp: new Date()
      });

      span.setStatus({ code: 1 }); // OK
      span.end();

      return {
        callId,
        response: message.content[0].text,
        usage: message.usage,
        cost
      };

    } catch (error) {
      span.recordException(error);
      span.setStatus({
        code: 2, // ERROR
        message: error.message
      });
      span.end();

      logger.error('LLM call failed', {
        event: 'llm_call_failed',
        callId,
        agentId,
        error: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  /**
   * Calculate LLM API cost.
   */
  calculateLLMCost(model, inputTokens, outputTokens) {
    const pricing = {
      'claude-3-5-sonnet-20241022': {
        input: 0.003 / 1000,  // $3 per million tokens
        output: 0.015 / 1000  // $15 per million tokens
      },
      'claude-3-opus-20240229': {
        input: 0.015 / 1000,
        output: 0.075 / 1000
      }
    };

    const modelPricing = pricing[model] || pricing['claude-3-5-sonnet-20241022'];

    return (inputTokens * modelPricing.input) + (outputTokens * modelPricing.output);
  }

  /**
   * Store LLM call in database for audit trail.
   */
  async storeLLMCall(callData) {
    await db.collection('llm_calls').insertOne(callData);
  }

  /**
   * Trace complete agent execution workflow.
   *
   * Pillar 4: End-to-end traceability
   */
  async traceAgentExecution(agentId, userId, request) {
    const span = this.tracer.startSpan('agent.execution', {
      attributes: {
        'ai.agent_id': agentId,
        'ai.user_id': userId,
        'ai.request_type': request.type
      }
    });

    const executionId = uuidv4();

    logger.info('Agent execution started', {
      event: 'agent_execution_started',
      executionId,
      agentId,
      userId,
      request: request.type,
      timestamp: new Date().toISOString(),
      traceId: span.spanContext().traceId
    });

    try {
      // Set active context for child spans
      return await context.with(
        trace.setSpan(context.active(), span),
        async () => {
          // Child spans will automatically be linked
          const result = await this.executeAgentWorkflow(agentId, userId, request);

          span.setAttributes({
            'ai.execution_success': true,
            'ai.steps_completed': result.stepsCompleted
          });

          logger.info('Agent execution completed', {
            event: 'agent_execution_completed',
            executionId,
            agentId,
            stepsCompleted: result.stepsCompleted,
            timestamp: new Date().toISOString(),
            traceId: span.spanContext().traceId
          });

          span.setStatus({ code: 1 });
          span.end();

          return result;
        }
      );

    } catch (error) {
      span.recordException(error);
      span.setStatus({ code: 2, message: error.message });
      span.end();

      logger.error('Agent execution failed', {
        event: 'agent_execution_failed',
        executionId,
        agentId,
        error: error.message,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  /**
   * Execute agent workflow with sub-spans.
   */
  async executeAgentWorkflow(agentId, userId, request) {
    // Step 1: Input validation
    const validationSpan = this.tracer.startSpan('agent.validate_input');
    await this.validateInput(request);
    validationSpan.end();

    // Step 2: Context retrieval
    const contextSpan = this.tracer.startSpan('agent.retrieve_context');
    const context = await this.retrieveContext(userId);
    contextSpan.setAttribute('ai.context_size', context.length);
    contextSpan.end();

    // Step 3: LLM call (automatically traced by traceLLMCall)
    const response = await this.traceLLMCall(
      agentId,
      'claude-3-5-sonnet-20241022',
      `Context: ${context}\n\nUser request: ${request.query}`,
      { temperature: 0.7, max_tokens: 1024 },
      userId
    );

    // Step 4: Post-processing
    const processingSpan = this.tracer.startSpan('agent.post_process');
    const processedResult = await this.postProcess(response.response);
    processingSpan.end();

    return {
      stepsCompleted: 4,
      result: processedResult
    };
  }

  async validateInput(request) {
    // Validation logic
    return true;
  }

  async retrieveContext(userId) {
    // Context retrieval
    return 'User context data';
  }

  async postProcess(response) {
    // Post-processing
    return response;
  }

  /**
   * Track data lineage through AI system.
   *
   * Pillar 4: Data provenance tracking
   */
  async trackDataLineage(datasetId, transformations) {
    const lineageId = uuidv4();

    const lineageRecord = {
      lineageId,
      datasetId,
      createdAt: new Date(),
      transformations: []
    };

    for (const transformation of transformations) {
      const transformationId = uuidv4();

      lineageRecord.transformations.push({
        transformationId,
        type: transformation.type,
        timestamp: new Date(),
        inputSchema: transformation.inputSchema,
        outputSchema: transformation.outputSchema,
        parameters: transformation.parameters,
        performedBy: transformation.performedBy
      });

      logger.info('Data transformation tracked', {
        event: 'data_transformation',
        lineageId,
        transformationId,
        type: transformation.type,
        timestamp: new Date().toISOString()
      });
    }

    await db.collection('data_lineage').insertOne(lineageRecord);

    return lineageId;
  }

  /**
   * Generate audit report for compliance.
   *
   * Pillar 4: Compliance reporting
   */
  async generateAuditReport(agentId, startDate, endDate) {
    const llmCalls = await db.collection('llm_calls')
      .find({
        agentId,
        timestamp: { $gte: startDate, $lte: endDate }
      })
      .toArray();

    const totalCost = llmCalls.reduce((sum, call) => sum + call.costUsd, 0);
    const totalTokens = llmCalls.reduce(
      (sum, call) => sum + call.usage.input_tokens + call.usage.output_tokens,
      0
    );

    const report = {
      reportId: uuidv4(),
      agentId,
      period: { startDate, endDate },
      generatedAt: new Date(),

      // Usage statistics
      totalCalls: llmCalls.length,
      totalCostUsd: totalCost,
      totalTokens,
      averageLatencyMs: llmCalls.reduce((sum, c) => sum + c.latencyMs, 0) / llmCalls.length,

      // Model distribution
      modelDistribution: this.groupBy(llmCalls, 'model'),

      // User distribution
      uniqueUsers: [...new Set(llmCalls.map(c => c.userId))].length,

      // Sample calls
      sampleCalls: llmCalls.slice(0, 10).map(call => ({
        callId: call.callId,
        timestamp: call.timestamp,
        model: call.model,
        tokens: call.usage.input_tokens + call.usage.output_tokens,
        cost: call.costUsd
      }))
    };

    await db.collection('audit_reports').insertOne(report);

    logger.info('Audit report generated', {
      event: 'audit_report_generated',
      reportId: report.reportId,
      agentId,
      totalCalls: report.totalCalls,
      totalCost: report.totalCostUsd
    });

    return report;
  }

  groupBy(array, key) {
    return array.reduce((result, item) => {
      const groupKey = item[key];
      result[groupKey] = (result[groupKey] || 0) + 1;
      return result;
    }, {});
  }
}

module.exports = AIAgentObservability;
```

---

## Success Criteria

- [ ] All LLM calls traced with OpenTelemetry
- [ ] Distributed tracing operational across services
- [ ] Structured audit logs for all agent actions
- [ ] Data lineage tracked for AI training data
- [ ] Cost tracking per agent and user
- [ ] Audit reports generated on-demand
- [ ] Compliance monitoring automated

---

[← Back to AI Agent Governance](./README.md) | [← Back to Compliance & Governance](../README.md) | [← Back to Main](../../../README.md)
