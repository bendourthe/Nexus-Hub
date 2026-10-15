---
name: multi-provider-ai
description: Configure and route LLM requests across multiple AI providers -- Anthropic direct, AWS Bedrock, Google Vertex AI, and OpenRouter. Covers provider selection criteria, environment variable patterns, unified client interfaces, fallback routing, and model ID conventions. Use when building LLM applications that need provider flexibility or enterprise cloud integration.
summary_l0: "Route LLM requests across Anthropic, Bedrock, Vertex AI, and OpenRouter providers"
overview_l1: "This skill provides patterns for building provider-agnostic LLM integrations that route requests across Anthropic, AWS Bedrock, Google Vertex AI, and OpenRouter without changing application code. Use it when choosing between AI providers, setting up credentials and environment variables, implementing a provider-agnostic client interface, designing fallback routing, comparing costs across providers, meeting enterprise cloud-native AI requirements, or avoiding vendor lock-in. Key capabilities include provider selection guides based on compliance, latency, cost, and features, credential and secret management patterns for each provider, unified TypeScript and Python client abstractions, failover routing strategies, cost comparison matrices, and model ID convention mapping. The expected output is a unified LLM client layer with automatic failover, per-provider credential management, and cost-aware routing. Trigger phrases: multi-provider Claude, AWS Bedrock Claude, Google Vertex Claude, OpenRouter setup, provider abstraction, fallback LLM, enterprise AI integration, Bedrock vs Anthropic."
---

# Multi-Provider AI Configuration

Design and implement provider-agnostic LLM integrations that can route requests across Anthropic, AWS Bedrock, Google Vertex AI, and OpenRouter without changing application code. Covers selection criteria, credential management, unified client patterns, cost comparison, and failover routing. Grounded in Shannon's multi-provider abstraction, which supports all four providers behind a single agent executor interface.

## When to Use This Skill

Use this skill for:

- Choosing between Anthropic direct, AWS Bedrock, Google Vertex AI, and OpenRouter
- Setting up credentials and environment variables for each provider
- Implementing a provider-agnostic client interface
- Designing fallback routing between providers
- Comparing costs across providers for production deployments
- Meeting enterprise requirements for cloud-native AI (Bedrock, Vertex)
- Avoiding vendor lock-in in long-running AI projects

**Trigger phrases**: "multi-provider Claude", "AWS Bedrock Claude", "Google Vertex Claude", "OpenRouter setup", "provider abstraction", "fallback LLM", "enterprise AI integration", "Bedrock vs Anthropic"

## What This Skill Does

Provides multi-provider LLM configuration patterns including:

- **Provider Selection Guide**: When to use each provider based on compliance, latency, cost, and feature requirements
- **Credential Patterns**: Environment variable setup and secret management for each provider
- **Unified Client Interface**: TypeScript and Python abstractions that hide provider differences
- **Model ID Reference**: Correct model identifiers for each provider (they differ significantly)
- **Cost Comparison**: Pricing structure differences and cost estimation
- **Failover Routing**: Graceful degradation when a provider is unavailable

## Instructions

### Step 1: Choose the Right Provider

| Criterion | Anthropic Direct | AWS Bedrock | Google Vertex AI | OpenRouter |
|-----------|-----------------|-------------|-----------------|------------|
| **Setup complexity** | Minimal (API key) | Medium (AWS IAM) | Medium (GCP IAM) | Minimal (API key) |
| **Latency** | Low | Low-Medium (regional) | Low-Medium (regional) | Low-Medium (routing overhead) |
| **Data residency** | Anthropic-managed | AWS region of choice | GCP region of choice | Anthropic-managed |
| **Compliance** | SOC 2 | SOC 2, HIPAA, GDPR, FedRAMP | SOC 2, HIPAA, GDPR | Anthropic's terms |
| **Enterprise billing** | Anthropic invoicing | AWS consolidated billing | GCP consolidated billing | OpenRouter invoicing |
| **Model availability** | All Claude models | Claude on Bedrock subset | Claude on Vertex subset | Many providers unified |
| **Rate limits** | Usage tier-based | Configurable quotas | Configurable quotas | Aggregated limits |
| **Fine-tuning** | No (yet) | No | No | No |
| **VPC/private link** | No | Yes (PrivateLink) | Yes (Private Service Connect) | No |
| **Best for** | Development, direct access | AWS-centric organizations | GCP-centric organizations | Multi-model comparison, prototyping |

**Decision guide**:
- Building a new project with no cloud preference → **Anthropic direct**
- Organization uses AWS, needs data residency or HIPAA → **AWS Bedrock**
- Organization uses GCP, needs Vertex AI ecosystem integration → **Google Vertex AI**
- Need to compare models across providers or use non-Anthropic models → **OpenRouter**

### Step 2: Set Up Provider Credentials

**Anthropic Direct**:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...

# Verify
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":1,"messages":[{"role":"user","content":"ping"}]}'
```

**AWS Bedrock**:

```bash
# Option A: Environment variables (development)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Option B: IAM role (production -- preferred for EC2/ECS/Lambda)
# Attach this IAM policy to your role:
# {
#   "Effect": "Allow",
#   "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
#   "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*"
# }

# Verify: list available Claude models in your region
aws bedrock list-foundation-models \
  --by-provider Anthropic \
  --query 'modelSummaries[].modelId' \
  --region us-east-1
```

**Google Vertex AI**:

```bash
# Option A: Application Default Credentials (development)
gcloud auth application-default login
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1  # or europe-west1, asia-northeast1

# Option B: Service account (production)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Required IAM role: roles/aiplatform.user
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:your-sa@your-project.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

**OpenRouter**:

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional: identify your app (improves rate limit allocation)
OPENROUTER_APP_NAME=your-app-name
OPENROUTER_SITE_URL=https://your-app.com
```

### Step 3: Model ID Reference

Model IDs differ significantly across providers. Always use the correct format for your provider.

| Model | Anthropic Direct | AWS Bedrock | Google Vertex AI | OpenRouter |
|-------|-----------------|-------------|-----------------|------------|
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | `anthropic.claude-haiku-4-5-20251001-v1:0` | `claude-haiku-4-5@20251001` | `anthropic/claude-haiku-4-5` |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | `anthropic.claude-sonnet-4-6-20251001-v1:0` | `claude-sonnet-4-6@20251001` | `anthropic/claude-sonnet-4-6` |
| Claude Opus 4.6 | `claude-opus-4-6` | `anthropic.claude-opus-4-6-20251001-v1:0` | `claude-opus-4-6@20251001` | `anthropic/claude-opus-4-6` |

> Always verify model availability in your region before deploying. Bedrock and Vertex AI model availability varies by region.

### Step 4: Implement a Unified Client (TypeScript)

```typescript
// src/ai/providers.ts

import Anthropic from "@anthropic-ai/sdk";

export type Provider = "anthropic" | "bedrock" | "vertex" | "openrouter";
export type ModelTier = "haiku" | "sonnet" | "opus";

const MODEL_IDS: Record<Provider, Record<ModelTier, string>> = {
  anthropic: {
    haiku: "claude-haiku-4-5-20251001",
    sonnet: "claude-sonnet-4-6",
    opus: "claude-opus-4-6",
  },
  bedrock: {
    haiku: "anthropic.claude-haiku-4-5-20251001-v1:0",
    sonnet: "anthropic.claude-sonnet-4-6-20251001-v1:0",
    opus: "anthropic.claude-opus-4-6-20251001-v1:0",
  },
  vertex: {
    haiku: "claude-haiku-4-5@20251001",
    sonnet: "claude-sonnet-4-6@20251001",
    opus: "claude-opus-4-6@20251001",
  },
  openrouter: {
    haiku: "anthropic/claude-haiku-4-5",
    sonnet: "anthropic/claude-sonnet-4-6",
    opus: "anthropic/claude-opus-4-6",
  },
};

export function resolveModelId(provider: Provider, tier: ModelTier): string {
  return MODEL_IDS[provider][tier];
}

export function createAnthropicClient(): Anthropic {
  const apiKey = process.env["ANTHROPIC_API_KEY"];
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY environment variable not set");
  return new Anthropic({ apiKey });
}

export function createOpenRouterClient(): Anthropic {
  const apiKey = process.env["OPENROUTER_API_KEY"];
  if (!apiKey) throw new Error("OPENROUTER_API_KEY environment variable not set");
  return new Anthropic({
    apiKey,
    baseURL: process.env["OPENROUTER_BASE_URL"] ?? "https://openrouter.ai/api/v1",
    defaultHeaders: {
      "HTTP-Referer": process.env["OPENROUTER_SITE_URL"] ?? "",
      "X-Title": process.env["OPENROUTER_APP_NAME"] ?? "",
    },
  });
}

// For Bedrock: use @anthropic-ai/bedrock-sdk
// import AnthropicBedrock from "@anthropic-ai/bedrock-sdk";
// export function createBedrockClient(): AnthropicBedrock {
//   return new AnthropicBedrock({
//     awsRegion: process.env["AWS_REGION"] ?? "us-east-1",
//     // Credentials from environment variables or IAM role (auto-detected)
//   });
// }

// For Vertex: use @anthropic-ai/vertex-sdk
// import AnthropicVertex from "@anthropic-ai/vertex-sdk";
// export function createVertexClient(): AnthropicVertex {
//   return new AnthropicVertex({
//     projectId: process.env["GOOGLE_CLOUD_PROJECT"],
//     region: process.env["GOOGLE_CLOUD_LOCATION"] ?? "us-central1",
//   });
// }

export function createClientForProvider(provider: Provider): Anthropic {
  switch (provider) {
    case "anthropic": return createAnthropicClient();
    case "openrouter": return createOpenRouterClient();
    case "bedrock":
      throw new Error("Install @anthropic-ai/bedrock-sdk and use createBedrockClient()");
    case "vertex":
      throw new Error("Install @anthropic-ai/vertex-sdk and use createVertexClient()");
    default: {
      const _: never = provider;
      throw new Error(`Unknown provider: ${_}`);
    }
  }
}
```

**Python equivalent** (using the unified `anthropic` library):

```python
import os
import anthropic

def create_client(provider: str = "anthropic") -> anthropic.Anthropic:
    """Create an Anthropic-compatible client for the specified provider."""
    if provider == "anthropic":
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    elif provider == "openrouter":
        return anthropic.Anthropic(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        )

    elif provider == "bedrock":
        import anthropic.lib.bedrock as bedrock
        return bedrock.AnthropicBedrock(
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        )

    elif provider == "vertex":
        import anthropic.lib.vertex as vertex
        return vertex.AnthropicVertex(
            project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            region=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

    raise ValueError(f"Unknown provider: {provider}")


MODEL_IDS = {
    "anthropic": {"haiku": "claude-haiku-4-5-20251001", "sonnet": "claude-sonnet-4-6", "opus": "claude-opus-4-6"},
    "bedrock": {"haiku": "anthropic.claude-haiku-4-5-20251001-v1:0", "sonnet": "anthropic.claude-sonnet-4-6-20251001-v1:0", "opus": "anthropic.claude-opus-4-6-20251001-v1:0"},
    "vertex": {"haiku": "claude-haiku-4-5@20251001", "sonnet": "claude-sonnet-4-6@20251001", "opus": "claude-opus-4-6@20251001"},
    "openrouter": {"haiku": "anthropic/claude-haiku-4-5", "sonnet": "anthropic/claude-sonnet-4-6", "opus": "anthropic/claude-opus-4-6"},
}
```

### Step 5: Implement Fallback Routing

Route requests to a fallback provider when the primary fails. Use this for resilience in production, not as a first-line cost optimization strategy.

```typescript
// src/ai/fallback-router.ts

import Anthropic from "@anthropic-ai/sdk";
import { createClientForProvider, resolveModelId, type Provider, type ModelTier } from "./providers.js";

export class FallbackRouter {
  private readonly providers: Provider[];
  private readonly tier: ModelTier;

  constructor(providers: Provider[], tier: ModelTier = "sonnet") {
    if (providers.length === 0) throw new Error("At least one provider required");
    this.providers = providers;
    this.tier = tier;
  }

  async invoke(
    params: Omit<Anthropic.MessageCreateParamsNonStreaming, "model">,
  ): Promise<{ response: Anthropic.Message; provider: Provider }> {
    let lastError: unknown;

    for (const provider of this.providers) {
      try {
        const client = createClientForProvider(provider);
        const model = resolveModelId(provider, this.tier);
        const response = await client.messages.create({ ...params, model });
        return { response, provider };
      } catch (error) {
        console.warn(`Provider ${provider} failed:`, error instanceof Error ? error.message : error);
        lastError = error;
      }
    }

    throw new Error(`All providers failed. Last error: ${lastError}`);
  }
}

// Usage:
// const router = new FallbackRouter(["anthropic", "openrouter"], "sonnet");
// const { response, provider } = await router.invoke({ max_tokens: 1024, messages: [...] });
```

### Step 6: Cost Comparison and Estimation

Pricing varies by provider and region. Always check the provider's pricing page for current rates. As of March 2026:

| Provider | Input (per M tokens) | Output (per M tokens) | Notes |
|----------|---------------------|----------------------|-------|
| Anthropic (Sonnet 4.6) | $3.00 | $15.00 | Direct API pricing |
| AWS Bedrock (Sonnet 4.6) | $3.00 + Bedrock markup | $15.00 + markup | Check Bedrock pricing page; markup varies by region |
| Google Vertex (Sonnet 4.6) | $3.00 + Vertex markup | $15.00 + markup | Check Vertex pricing page |
| OpenRouter (Sonnet 4.6) | $3.00 + routing fee | $15.00 + fee | Typically 0-10% routing overhead |

> Pricing is subject to change. Always verify on the provider's pricing page before production deployment.

```typescript
// Cost estimation utility
function estimateCostUsd(
  inputTokens: number,
  outputTokens: number,
  inputCostPerM: number = 3.0,
  outputCostPerM: number = 15.0,
): number {
  return (inputTokens / 1_000_000) * inputCostPerM + (outputTokens / 1_000_000) * outputCostPerM;
}
```

## Best Practices

- **Start with Anthropic direct**: The simplest path for development. Switch providers only when you have a concrete business requirement (compliance, billing consolidation, regional latency).
- **Pin model IDs explicitly**: Never use model aliases like `claude-sonnet-latest` in production -- they can change under you. Use the full versioned ID.
- **Use IAM roles in production**: For Bedrock and Vertex, use IAM roles attached to your compute, not long-lived access keys in environment variables.
- **Test in each provider before switching**: Model behavior can differ slightly across providers due to inference infrastructure differences. Test your prompts with the target provider before go-live.
- **Failover is for resilience, not cost arbitrage**: Routing to a cheaper provider when the primary is "busy" undermines predictable performance. Use fallback routing for genuine unavailability.
- **Document your provider choice**: Record the reasoning (compliance requirement, AWS consolidation, regional latency) in your CLAUDE.md or ADR. Future maintainers need to know why you chose a specific provider.

## Common Patterns

### Pattern 1: Environment-Driven Provider Selection

```typescript
const provider = (process.env["AI_PROVIDER"] ?? "anthropic") as Provider;
const tier = (process.env["MODEL_TIER"] ?? "sonnet") as ModelTier;
const client = createClientForProvider(provider);
const model = resolveModelId(provider, tier);
```

### Pattern 2: Region-Specific Bedrock Endpoint

Some Claude models on Bedrock are only available in specific regions. Check availability before selecting a region:

```typescript
// us-east-1 (N. Virginia): widest model availability
// us-west-2 (Oregon): good for West Coast latency
// eu-central-1 (Frankfurt): GDPR data residency
// ap-northeast-1 (Tokyo): APAC latency
const AWS_REGION = process.env["AWS_REGION"] ?? "us-east-1";
```

### Pattern 3: Provider Header Injection (OpenRouter)

OpenRouter uses HTTP headers to identify your app and allocate rate limits:

```typescript
const client = new Anthropic({
  apiKey: process.env["OPENROUTER_API_KEY"],
  baseURL: "https://openrouter.ai/api/v1",
  defaultHeaders: {
    "HTTP-Referer": "https://your-app.com",  // Required for some models
    "X-Title": "Your App Name",              // Displayed in OpenRouter dashboard
  },
});
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Using a model alias keeps me on the latest version" | An unpinned alias silently re-points to a new model whose tokenizer and pricing differ, so cost and output quality shift under you with no code change and no diff to review. |
| "All four providers expose the same model, region does not matter" | A model available in `us-east-1` Bedrock may be absent in the deploy region; the failure surfaces only at first production call in that region, not in dev. |
| "I do not need fallback routing, the primary provider is reliable" | Provider-wide outages and per-key rate limits happen; without a tested fallback path the whole agent fleet hard-fails instead of degrading to a secondary provider. |
| "A default branch in the provider switch is fine" | A non-exhaustive switch lets a new `Provider` value compile and silently hit the default, routing requests to the wrong backend; a `never` branch turns that into a compile error. |

## Verification

- [ ] Provider selection documented with rationale in CLAUDE.md or ADR
- [ ] Model IDs pinned to specific versioned identifiers (no aliases)
- [ ] Credentials use IAM roles (Bedrock/Vertex) or env vars (Anthropic/OpenRouter), not hardcoded values
- [ ] Model availability verified in target region before deployment
- [ ] Cost estimate calculated for expected token volume at production scale
- [ ] Fallback routing tested (simulate primary provider failure)
- [ ] `.env.example` documents all required environment variables for each provider
- [ ] TypeScript `Provider` type is exhaustive (`never` branch in switch)

## Related Skills

- [[claude-agent-sdk]] -- building autonomous agents on top of these providers
- [[ai-billing-safeguards]] -- spending cap enforcement for multi-provider agent systems
- [[temporal-orchestration]] -- workflow orchestration for multi-provider agent pipelines
- [[cross-model-orchestrator]] -- routing tasks across different models based on capability requirements
- [[model-routing]] -- task-time model + effort routing that reuses this skill's tier abstraction but enumerates the model set live instead of from a hardcoded matrix

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Reference Implementation**: Shannon (KeygraphHQ) -- supports Anthropic, AWS Bedrock, Google Vertex AI, and OpenRouter via unified provider abstraction
