# GPT-6.1 Sol against the gpt-6-astra profile

One row per recorded gpt-6-astra claim, read from the pages saved on 2026-10-01.

| gpt-6-astra claim | For GPT-6.1 Sol | Evidence |
|---|---|---|
| Start at low instead of none or minimal; none unsupported | same | stated for GPT-6.1 Sol by name |
| configuration_update for effort changes between responses | same | migration checklist covering gpt-6.1-sol |
| Tool calling requires the Responses API | same | stated for GPT-6.1 Sol by name |
| Async tools via async: true and the original call_id | not stated for Sol | the What's new section names the GPT-6 family only |
| Remove temperature, top_p, and top_logprobs | same | migration checklist covering gpt-6.1-sol |
| Fast mode has no latency SLA and is unavailable with EU residency | not stated for Sol | the page names GPT-6 Astra, GPT-6 Sol, and GPT-6 Luna, not GPT-6.1 Sol |
| Replace prompt_cache_retention with prompt_cache_options.ttl 30m | same | migration checklist covering gpt-6.1-sol |
| Treat action-phrased prompts as instructions to act | not stated for Sol | Astra-observed behavior; vendor says to evaluate per model |
| User instructions take precedence over skill guidelines | not stated for Sol | Astra-observed behavior; vendor says to evaluate per model |
| Do not write tests for reversible, low-impact changes | not stated for Sol | Astra-observed behavior; vendor says to evaluate per model |
| Parallelize by delegating to another agent | same prompt, not adopted | family prompt; overridden by agent-orchestration-primitives |
| Release date and most-capable positioning | different | Sol is positioned as near-Astra at lower cost; no release date on these pages |
