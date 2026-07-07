# Comparison: Nexus-Hub vs pxpipe (optical / image-token context compression)

**Source**: [`teamchong/pxpipe`](https://github.com/teamchong/pxpipe) (npm `pxpipe-proxy` v0.8.0, MIT), plus the surrounding research and community debate on optical context compression
**Source type**: Git repository + web/topic deep research (hybrid)
**Comparison date**: 2026-07-06
**Nexus-Hub baseline**: v3.10.0 (259 skills, 16 commands, 25 hooks, 23 agents)
**Analysis target**: v3.11.0 adoption cycle
**Vendor claims treated as unverified**: pxpipe's headline figures ("up to 70% savings", "68% fewer input tokens", the SWE-bench and hex-recall tables) are all self-reported in the project's own `README.md` / `FINDINGS.md`. No independent third-party reproduction of the end-to-end savings was found. They are treated as vendor data throughout, not as measured fact.

---

## Executive Summary

**Verdict: do not integrate pxpipe or its imaging mechanism into Nexus-Hub. Adopt only the token-economics doctrine it surfaces, as skill-native text, and use it mainly to steer users away from the lossy hack toward the lossless techniques Nexus-Hub already ships.**

Three findings drive that verdict, and each is independently sufficient.

1. **The concept is real but the "no quality impact" premise is false for code.** Optical context compression (rendering text as an image so a vision model reads it back) is a genuine, freshly-validated 2025 research result (DeepSeek-OCR, Glyph). It works because it is lossy: it preserves gist and sacrifices exact characters. pxpipe's own tests show 12-character hex verbatim recall of about 87% on Fable 5 but **0% on Opus 4.5 and Opus 4.8**, and the misses are "silent confabulations, not errors" (the model returns a confident wrong value with no error signal). For a coding assistant, whose payloads are hashes, hex, base64, version pins, and near-identical identifiers, a silent single-character substitution is a wrong answer that passes human review and lint, not a degraded one. This is the exact failure the skeptics named, and the source repo concedes it.

2. **The token savings do not hold on the model this project runs on.** Anthropic bills images by 28x28-pixel patches (`ceil(w/28) * ceil(h/28)` visual tokens), with a high-resolution tier for Opus 4.8, Opus 4.7, Sonnet 5, and Fable 5 that roughly triples image cost. At any resolution where code stays legible, a page rendered as an image costs about 1.5x to 5x more tokens than the same text on Opus 4.8 (roughly 2,700 to 4,784 image tokens versus 750 to 1,050 text tokens). pxpipe reaches its 68% savings only by rendering text illegibly dense (about 92,000 characters per page) and by defaulting to Fable 5, whose vision encoder tolerates that density. On Opus, both the economics and the fidelity fail. The "70%" figure is measured on a purpose-built compressor or on Fable, then rhetorically transplanted onto "Claude Code" in general.

3. **It is the wrong architectural layer, and it inverts Nexus-Hub's posture.** pxpipe is a transport-layer reverse-proxy that sits in the critical path of every API call (`ANTHROPIC_BASE_URL=http://127.0.0.1:47821`) and lossily mutates requests before they reach Anthropic. Nexus-Hub is a content-layer catalog with a zero-outbound-by-default, no-runtime posture. An always-on proxy that rewrites the request stream is exactly the class of runtime component the MCP Registry Policy declines, and it was declined for the same reason in the v3.10.0 ruflo cycle (the MCP-server-as-daemon and standalone-loop-runtime precedents).

What **is** worth adopting is small and skill-native: a grounded subsection in `prompt-token-optimization` (cross-linked from `context-engineering`, `context-compression`, and `model-routing`) that explains image-token / optical compression honestly, the patch-billing math, the resolution trap, the silent-exact-string failure mode, and the rule that lossless prompt caching and context pruning are the correct default for the same static content. The primary deliverable of this exercise is the research below and the clear, reasoned decline, not new runtime capability.

---

# Part A: Deep Research on Optical Context Compression (the pxpipe topic)

This part answers the three questions posed: what the community says, the current research stage, and whether the technique reduces tokens without quality impact. Every quantitative claim carries a source.

## A.1 What pxpipe actually is and how it works

pxpipe is a local reverse-proxy written in TypeScript (Node >= 18, also runs on Cloudflare Workers), distributed as the npm package `pxpipe-proxy` (v0.8.0, MIT). The user starts it with `npx pxpipe-proxy` (it listens on `127.0.0.1:47821`) and points Claude Code at it with `ANTHROPIC_BASE_URL=http://127.0.0.1:47821`. It intercepts POSTs to `/v1/messages` (and the OpenAI-compatible paths), rewrites eligible parts of the request body into dense PNG image blocks, forwards the request upstream to `https://api.anthropic.com`, and tees the response to record token/usage metrics. A dashboard on the same port offers a kill switch and live model toggles. Source: repo `src/core/proxy.ts`, `src/core/transform.ts`, `README.md` ([github.com/teamchong/pxpipe](https://github.com/teamchong/pxpipe)).

The rewriting is selective, gated by a per-request profitability estimator that images a block only when `imageTokens + overhead < textTokens + overhead`:

- **Rendered to PNG (only when profitable)**: the static "system slab" (system prompt plus tool documentation, gate about 2,000 characters), large `tool_result` bodies (gate about 6,000 characters, capped at 10 images each), large `<system-reminder>` blocks, and older/closed conversation-history prefixes (only when the cost amortizes across turns).
- **Always kept as text**: the recent "live tail" of turns, all user messages, all model output, per-turn volatile blocks (`<env>`, `<context>`, `<git_status>`), caller `cache_control` markers, and, per the docs, byte-exact values (IDs, hashes, secrets).

The default model allowlist is `claude-fable-5, gpt-5.6`. Opus 4.7 / 4.8 and GPT-5.5 are opt-in only, "due to lower legibility". This selectivity is the whole safety model: pxpipe tries to image only gist-tolerant, static, bulky content and to keep everything correctness-critical as text.

Maturity signals: the repo is genuine engineering (vitest tests, `bench/`, `eval/`, GitHub Actions CI, Cloudflare `wrangler.toml`), but it is very young (a burst of about 34 commits over July 3 to 5, 2026) and pre-1.0. There are open correctness bugs, not just feature requests: Fable 5 refusing benign imaged content with `stop_reason=refusal, category=cyber` (issue #37), tool-doc imaging breaking native typed tools with a 400 error masked by silent model-fallback (#43), and OAuth/Pro users getting 401s through the proxy (#60). The two proposed exact-string safeguards (an "anchor sidecar" that passes high-entropy tokens as text beside the image, #55; and checksummed wordlist encoding of in-image strings, #38) are open and unimplemented. There is no runtime canary that verifies an imaged block was read correctly, so the documented failure mode (silent confabulation) is documented but not defended against in code.

## A.2 The research foundation and its maturity

The idea rests on a real and specific 2025 research line, not on folklore, but the viral framing overstates its maturity.

- **DeepSeek-OCR, "Contexts Optical Compression"** (arXiv [2510.18234](https://arxiv.org/abs/2510.18234), Oct 2025, MIT weights). A purpose-built vision encoder (SAM-base, a 16x convolutional token compressor, then CLIP-large) plus a small MoE decoder. Headline: within about 10x compression, decoding precision is about 97%; at nearly 20x, precision still approaches 60%. The Fox-benchmark curve is a cliff, not a slope: 98.5% at 6.7x, 96.5% at 10.5x, 85.9% at 15.1x, 59.1% at 19.7x. The authors explicitly call this "an initial investigation into the feasibility of compressing long contexts via optical 2D mapping", a proof of concept, and propose using it for memory decay (progressively downsampling older context).
- **Glyph, "Scaling Context Windows via Visual-Text Compression"** (arXiv [2510.17800](https://arxiv.org/abs/2510.17800), Oct 2025). The long-context-LLM application of the same idea. It reaches 3x to 4x token compression at accuracy comparable to a text baseline, and names OCR fidelity as the binding constraint: "UUID recognition remains particularly challenging" and "rare alphanumeric sequences frequently result in misordered or misclassified characters".
- **"Text or Pixels? It Takes Half"** (arXiv [2510.18279](https://arxiv.org/html/2510.18279v1)). Shows the effect with off-the-shelf VLMs (up to 58% fewer decoder tokens at about 99% accuracy on summarization). This is the closest analog to what pxpipe exploits.

On the viral claim that "AI labs quietly validated pixel-based reading years ago": it is half true. VLMs *reading* text from pixels is genuinely old and well established (Donut 2021, Pix2Struct 2022, Fuyu-8B 2023, GPT-4V and Gemini 2023). But those systems were about eliminating a separate OCR stage, not about token efficiency, and naive high-resolution document images often cost *more* vision tokens than the underlying text. The specific claim that pixels are a *token-efficient substitute for text context* is a 2025 result, not a years-old one. Andrej Karpathy's widely-shared take ([x.com/karpathy/status/1980397031542989305](https://x.com/karpathy/status/1980397031542989305)) endorsed the DeepSeek-OCR research thesis ("pixels may be better inputs than tokens"), explicitly as a springboard for speculation, not as an endorsement of pxpipe or of the efficiency claim as settled fact.

Maturity summary: production-grade only in the narrow OCR / document-extraction case (DeepSeek-OCR ships and is used that way). Research-preview for general long-context (Glyph is a research release; no mainstream lab ships "render your context as images" as a first-class long-context feature). Speculative as a general replacement for tokenized input. pxpipe is the one thing "shipping", and it is a third-party weekend-old proxy hack, not a lab product.

## A.3 The token economics: is the 70% real?

The savings claim is real for a purpose-built compressor and inverts to a loss for Claude's general API once legibility is priced in.

Anthropic's current documented billing is patch-based: an image costs `ceil(width/28) * ceil(height/28)` visual tokens (one visual token per 28x28-pixel patch), superseding the old `(w*h)/750` heuristic that still circulates (the two are close because 28^2 = 784, near 750). There are two tiers with a hard cap: standard models cap at 1,568 visual tokens (long edge 1,568 px); high-resolution models (Fable 5, Opus 4.8, Opus 4.7, Sonnet 5) cap at 4,784 tokens (long edge 2,576 px). Source: [Anthropic vision docs](https://platform.claude.com/docs/en/build-with-claude/vision).

Worked example, one page of code (about 50 lines, roughly 2,250 characters):

- **As text**: about 750 to 1,050 tokens (English is about 0.75 words per token; code is about 3.5 characters per token). Use `messages.count_tokens` for an exact figure; do not use `tiktoken`, which is OpenAI's tokenizer.
- **As a legible image (about 150 DPI, 1275x1650 px)**: on a standard-tier model it downscales and caps near 1,560 tokens; on Opus 4.8 (high-res tier) it is `ceil(1275/28) * ceil(1650/28) = 46 * 59 = 2,714` tokens; at a comfortable 200 DPI on Opus 4.8 it hits the 4,784 cap.

So at legible resolution the image costs about 1.5x to 5x more than the text, the opposite of a saving. An independent practitioner measurement agrees: the high-resolution tier introduced with Opus 4.7 roughly tripled image cost (the same screenshot went from about 1,242 tokens on Opus 4.6 to about 3,234 on Opus 4.7) ([claudecodecamp.com](https://www.claudecodecamp.com/p/images-cost-3x-more-tokens-in-claude-opus-4-7)).

How does pxpipe still measure 68% input savings, then? By operating at the opposite end of the dial. It renders text illegibly dense (about 92,000 characters per 1928x1928 page, roughly 3.1 characters per vision-token versus about 1 to 2 for a legible render) and defaults to Fable 5, whose encoder handles that density. The savings and the fidelity are the same dial turned in opposite directions: to get the 68% you must render at a density where exact strings are lost (0% hex recall on Opus), and to recover fidelity you must raise resolution until the savings evaporate. On a general VLM there is no operating point that is simultaneously cheap and byte-exact.

Two more economic caveats the community raised (A.5): lossless prompt caching competes for exactly the same static content pxpipe targets, and at least one independent user found that imaging reduced prompt tokens but raised completion tokens enough to be net more expensive and slower.

## A.4 The fidelity tradeoff: silent exact-string confabulation

This is the decisive risk for a coding context, and it is not a tunable accuracy knob, it is a categorical loss.

- **Confusable glyphs return**: 0/O, 1/l/I, rn/m, 7/J, and case ambiguity. base64 is "particularly problematic" because it mixes case and confusable glyphs; hex is challenging for the same reason ([monperrus.net](https://www.monperrus.net/martin/perfect-ocr-digital-data)).
- **Baseline error rates**: good printed-text OCR is 1% to 2% character error rate; average is 2% to 10%. At 97% precision (DeepSeek-OCR at 10x) a 2,000-character page still carries about 60 wrong characters ([CER/WER guide](https://towardsdatascience.com/evaluating-ocr-output-quality-with-character-error-rate-cer-and-word-error-rate-wer-853175297510/)).
- **The VLM-specific danger is fluency**: VLM OCR errors "remain fluent even when wrong, producing plausible substitutions", and fluent output "is not necessarily visually grounded" (arXiv [2509.17418](https://arxiv.org/pdf/2509.17418)). A traditional OCR engine that misreads a hash emits spottable garbage; a VLM emits a different but equally plausible-looking hash. pxpipe's own word for this is "silent confabulations, not errors".
- **Lost operations**: once the source is pixels, the model reconstructs tokens probabilistically. It cannot guarantee byte-identical verbatim reproduction, cannot do an exact character-level diff, and cannot do exact search against the original. Those operations require the literal token stream. For an agent that must "change only this line" or "find every call site of this symbol", that is a loss of core capability.

For a coding assistant the failure profile is close to worst case: the payloads are exactly the unforgiving high-entropy strings, the errors are self-camouflaging (a one-character substitution still parses and passes review), and the operations a coding agent depends on are removed. pxpipe's measured numbers make this concrete: Opus 4.5 and Opus 4.8 scored 0/15 on 12-character hex verbatim recall, and even semantic extraction on Opus was 4/15 to 6/15 ([FINDINGS.md](https://github.com/teamchong/pxpipe/blob/main/FINDINGS.md)).

## A.5 What the community actually concluded

The viral epicenter was a single Hacker News thread on July 3, 2026 ("60% Fable cost cut by converting code to images and having the model OCR it", 309 points, 99 comments, [news.ycombinator.com/item?id=48776464](https://news.ycombinator.com/item?id=48776464)). Repo traction grew fast over that weekend (snapshots from about 1,823 to about 4,000 stars). Reddit, Lobsters, and full X post text could not be independently verified (fetch access blocked), so the community read below rests on HN, the repo, and one rigorous independent blog.

- **Supporters** accept the mechanism as real physics: an image is priced by pixels, so dense content packs more characters per token. They cite DeepSeek-OCR as the grounding and point to genuine adjacent wins (one HN user offloaded tens of thousands of OCR characters to images successfully).
- **Skeptics** landed several durable points that went largely unrebutted. Kevin Riedl's independent analysis (verdict: "genius and absurd", "both") is the most rigorous: "anything you need back byte-exact must stay as text" ([wavect.io](https://wavect.io/blog/text-as-image-token-savings/)). HN voices called it "clearly a workaround for a pricing failure" that Anthropic will likely close, noted that lossless prompt caching competes for the same static content, and, most damagingly, one experimenter (`lpellis`) reported that completion tokens rose enough to make it net more expensive and slower for his workload. Mainstream coverage hedged: WinBuzzer's headline says pxpipe "*claims*" the savings and concludes the approach "needs exact-string failure rates alongside the savings range before image-rendered context can become a safe cost lever" ([winbuzzer.com](https://winbuzzer.com/2026/07/05/pxpipe-proxy-claims-fable-cost-cuts-through-code-images-xcxwbn/)).
- **No independent reproduction** of the end-to-end 70% figure was found. The only genuinely independent empirical datapoint (lpellis) contradicts the headline for that user.

Net community consensus: a narrow, opt-in cost lever for large, static, gist-only context on a strong vision model such as Fable 5, not a general-purpose "free 70%"; fundamentally lossy with silent exact-string failures; and probably a temporary pricing-arbitrage window.

## A.6 Bottom line: does it reduce tokens without impacting quality?

No, not in the general case, and specifically not for Nexus-Hub's user (working on Opus 4.8) or for code. The honest statement is:

- It reduces *input* tokens meaningfully only for large, static, gist-tolerant context, only on a vision encoder that tolerates dense rendering (Fable 5), and only while the pricing asymmetry persists. It can raise *completion* tokens enough to erase the win.
- On Opus 4.8 the token math inverts (images cost more at legible resolution) and fidelity collapses (0% exact-string recall).
- Quality is impacted by construction: the technique is lossy, and its failures are silent confabulations, which is the most dangerous error class for code. "Without any impact on quality" is not achievable at the compression ratios that make it worth doing.

The mechanism is a legitimate, well-grounded technique for the right narrow workload. It is not a safe, general token-savings lever for a correctness-first coding harness.

---

# Part B: Comparison and Integration Assessment (compare-project workflow)

## Step 1: Source Type and Scope

The source URL contains `github.com`, so it classifies as a Git repository. Because pxpipe is a single-purpose runtime tool rather than a broad harness, the 11-dimension comparison is applied but is deliberately thin: most dimensions reduce to "different category of artifact". The substantive analysis is the capability/security assessment in Steps 4 and 5, informed by the Part A research.

## Steps 2 and 3: Dimension Comparison and Difference Classification

Legend: `+` external-only (adoption candidate), `=` current-only (strength to preserve), `~` both with a different approach, `.` both equivalent.

| # | Dimension | pxpipe | Nexus-Hub | Bucket |
|---|-----------|--------|-----------|--------|
| 1 | **Project Identity** | Transport-layer cost proxy; MIT; TypeScript/npm; positions as a token-bill cutter for Claude Code / Fable | Content-layer template catalog; installer-distributed; positions as a skill harness / upstream catalog | `~` |
| 2 | **Technology Stack** | TypeScript, Node/Cloudflare Workers, `@napi-rs/canvas`, `gpt-tokenizer`, vitest/CI | Python + Bash/PowerShell installers, Markdown catalog, JSON registries; no compiled runtime | `~` |
| 3 | **Architecture layer** | Runtime reverse-proxy in the API critical path (`ANTHROPIC_BASE_URL`), lossily mutates requests | No runtime; ships instructions/skills/hooks; zero outbound by default | `~` |
| 4 | **Core capability** | Optical/image-token context compression (lossy) | Token *doctrine* via `prompt-token-optimization`, `context-compression`, `context-engineering`, plus the local lossless `nexus-context-compressor` engine | `~` |
| 5 | **Token-reduction approach** | Lossy image rendering of static context; savings model-specific (Fable) | Lossless: context hygiene, programmatic tool calling, prompt-caching guidance, output minimization | `~` |
| 6 | **Correctness posture** | Documented lossy; silent confabulation; safeguards proposed but unimplemented (#55, #38) | Correctness-first: binary Verification and Common Rationalizations in every skill; "no temporary fixes" | `=` |
| 7 | **Security / trust surface** | Adds an always-on proxy that sees and rewrites all traffic and re-injects credentials | Reverse-engineer-first, zero-outbound MCP Registry Policy; `secret-scan`, `git-guardrails` | `=` |
| 8 | **Maturity** | v0.8.0, one weekend old, open correctness bugs (#37, #43, #60) | Released v3.10.0; validation, parity guards, per-version docs | `=` |
| 9 | **Model coupling** | Tuned for Fable 5; degrades badly on Opus and GPT-5.5 | Model-agnostic content; `model-routing` skill picks the right tier per task | `~` |
| 10 | **Distribution** | `npx pxpipe-proxy`, single machine | One-line installer to 14+ AI assistants across Windows/macOS/Linux | `~` |
| 11 | **Governance / docs** | README + candid FINDINGS.md; no policy layer | `AGENTS.md`, MCP Registry Policy, reverse-engineering matrix, markdown style governance | `=` |

The table is mostly `~` and `=` because the two are different categories of artifact solving adjacent problems (token cost) from opposite layers. The interesting analysis is the per-capability classification below.

## Step 4: Adoption Candidates (value/effort)

| ID | pxpipe capability | Nexus-Hub equivalent (evidence) | Gap | Value | Effort | P-tier (pre-gate) |
|----|-------------------|----------------------------------|-----|-------|--------|-------------------|
| C1 | Token-economics doctrine: image-token patch billing, when imaging helps vs hurts, the resolution trap, lossless-first rule | `prompt-token-optimization`, `context-compression`, `context-engineering`, `guides/reference/RTK_CONTEXT_COMPRESSION.md` | Partial: no explicit treatment of optical/image-token compression or the patch-billing math | Med | Low | P2 |
| C2 | Silent-exact-string-confabulation warning (byte-exact must stay text; lossy proxies fail without an error signal) | Scattered: correctness doctrine implicit; `egress-redaction`, `prompt-injection-defense` cover adjacent trust-boundary risks | Partial: no named caution about lossy context transforms losing byte-exact fidelity silently | Med | Low | P2 |
| C3 | The imaging proxy runtime itself (lossy request mutation in the API critical path) | None (Nexus-Hub ships no runtime) | Non-adoptable runtime; architecturally and by policy out of scope | n/a | n/a | Drop |
| C4 | Model-specific applicability (technique works on Fable, not Opus) | `model-routing` skill (detect platform, pick model/effort) | Mostly covered; add a one-line note that some cost techniques are vision-encoder-specific | Low | Low | P3 |

## Step 5: Security and Reverse-Engineering Assessment (MANDATORY)

This gate runs every candidate through the `AGENTS.md` MCP Registry Policy decision tree. It overrides the raw P-tiers above.

### 5.1 Threat-model comparison

| Factor | pxpipe (runtime proxy) | Nexus-Hub (catalog) |
|--------|------------------------|---------------------|
| New runtime dependencies | An always-on local proxy on `127.0.0.1:47821` in the path of every API call | None at rest; installer is run-once, no daemon |
| Position relative to traffic | Sees, parses, and rewrites every request and response; re-injects `x-api-key` | Never touches API traffic |
| Request integrity | Deliberately mutates requests (lossy image substitution) | Never mutates requests |
| Failure mode introduced | Silent confabulation of exact strings; no runtime verification | None; skills carry binary Verification |
| Credentials handled | Proxies and re-injects the user's Anthropic/OpenAI credentials | Ships and requires no credential |
| Known correctness bugs inherited | #37 cyber-refusals on benign imaged data, #43 native-tool 400s, #60 OAuth 401s | n/a |

The threat-model delta is the whole story. Adopting pxpipe's runtime would place a lossy, credential-handling, request-mutating proxy in the critical path, inverting Nexus-Hub's zero-outbound, no-runtime, correctness-first posture. This is the same inversion the policy blocked for ruflo's daemon model in v3.10.0.

### 5.2 Per-item risk scorecard

| ID | Candidate | Risk tier | Why |
|----|-----------|-----------|-----|
| C1 | Token-economics doctrine (skill text) | None | Pure instruction text; reduces risk by grounding users in the real math |
| C2 | Silent-confabulation caution (skill text) | None | Pure instruction text; a defensive correctness warning |
| C4 | Model-specific note in `model-routing` | None | One-line doctrine addition |
| C3 | Imaging proxy runtime | High | Always-on proxy, credential handling, lossy request mutation, silent failure, inherited correctness bugs |

### 5.3 Reverse-engineering viability

| ID | Candidate | RE classification | Note |
|----|-----------|-------------------|------|
| C1 | Token-economics doctrine | `skill-native` | Achievable as skill text; enrich `prompt-token-optimization` with the patch-billing math and the resolution trap |
| C2 | Silent-confabulation caution | `skill-native` | A correctness/trust-boundary warning; fold into C1 and cross-link `egress-redaction` / `prompt-injection-defense` |
| C4 | Model-specific applicability | `skill-native` | One-line note in `model-routing` |
| C3 | Imaging proxy runtime | `drop-outright` | Technically local, but it is an always-on runtime that lossily mutates API traffic in the critical path. Non-adoptable per the MCP Registry Policy and the v3.10.0 ruflo runtime-decline precedent (MCP-server-as-daemon / standalone-loop-runtime). A correctness-first coding catalog must not ship or endorse a lossy context transform with silent failures. |

Note on why C3 is a drop rather than a tier-3 reverse-engineer build: the policy's tier 3 says to build a local internal equivalent when the external logic can run locally. pxpipe does run locally, but the *thing itself* (a lossy proxy in the request path) is the disqualifier, not its non-locality. Reverse-engineering it would faithfully reproduce a capability Nexus-Hub should not have. The correct reverse-engineering move is to extract the *doctrine* (C1, C2, C4) and decline the *mechanism* (C3).

### 5.4 Recommendation ordering (this IS the adoption plan)

1. **`skill-native` (the only adoptable bucket here)**
    - C1: token-economics / optical-compression doctrine in `prompt-token-optimization` (P2)
    - C2: silent-confabulation correctness caution, folded into C1 with security cross-links (P2)
    - C4: model-specific applicability note in `model-routing` (P3, optional)
2. **`re-full` / `re-partial`**: none.
3. **`vendor-intrinsic`**: none. There is no third-party data destination to justify a wrapper.
4. **`drop-outright` (moved to NOT-recommended, Step 7)**: C3, the imaging proxy runtime and its mechanism.

## Step 6: Sequenced Adoption Plan

Dependency-ordered, skill-native only. When chaining into `/plan from-comparison`, pass `reverse-engineer-first=true`.

1. **C1 + C2: enrich `prompt-token-optimization`** (P2, skill-native, no dependencies). Add an "optical / image-token compression" subsection that: explains the technique and its research grounding (DeepSeek-OCR, Glyph); states Anthropic's patch-based image billing and the high-resolution tier; gives the worked example showing images cost more than text at legible resolution on Opus-class models; names the silent-exact-string-confabulation failure and the "byte-exact content stays as text" rule; and directs users to the lossless defaults Nexus-Hub already ships (prompt caching, context pruning, the `nexus-context-compressor` engine). Cross-link `context-compression`, `context-engineering`, `model-routing`, `egress-redaction`, and `ai-billing-safeguards`. Registry: a body-only edit needs no `data/` change; if `summary_l0` / `overview_l1` change, update the three registry files and run `make validate`.
2. **C4: one-line note in `model-routing`** (P3, skill-native, optional). Record that some cost techniques are vision-encoder-specific and degrade on stronger reasoning models, so they are not a universal lever.
3. **Matrix row**: add a dated `drop-outright` row for the imaging-proxy runtime in `docs/policy/mcp-reverse-engineering-matrix.md`, citing the MCP Registry Policy and the v3.10.0 ruflo runtime-decline precedent, with generic descriptive language (no product name in distributed artifacts per the reverse-engineering attribution rule).

C1/C2 are a single edit and are the entire recommended cut. C4 and the matrix row are trivial follow-ons.

## Step 7: Risks, Conflicts, and NOT-Recommended

### Conflicts with existing conventions

- **C1/C2** is an additive skill-body edit. Low risk. If frontmatter changes, the three-file registry update and `make validate` are required (AGENTS.md rule 2). Follow `catalog/style-guides/markdown.md`.
- **Attribution**: per the reverse-engineering attribution rule, the distributed skill text should teach the technique and its risks generically and must not name the specific upstream repo or product. Attribution belongs only in the matrix row's rationale.

### NOT recommended for adoption (policy grounds cited by name)

- **C3, the pxpipe imaging proxy and its mechanism.** MCP Registry Policy: an always-on runtime component in the API critical path that lossily mutates requests, handles credentials, and fails silently. Declined on the same grounds as ruflo's MCP-server-as-daemon and standalone-loop-runtime models in v3.10.0. Independently declined on correctness grounds: a coding catalog whose ethos is binary verification and "no temporary fixes" must not ship or endorse a lossy context transform whose errors are silent confabulations. Independently declined on economics: the savings do not hold on Opus-class models and can be net-negative once completion tokens are counted.

### Nexus-Hub strengths to preserve (current-only, `=`)

- The correctness-first doctrine (binary Verification, Common Rationalizations) that makes a lossy silent-failure technique a non-starter here.
- The zero-outbound, no-runtime, reverse-engineer-first MCP Registry Policy that cleanly classifies a critical-path proxy as out of scope.
- The lossless token-reduction stack already shipped: `prompt-token-optimization`, `context-compression`, `context-engineering`, `context-optimization`, and the local `nexus-context-compressor` engine, plus `ai-billing-safeguards` and `/usage` for cost control.
- `model-routing` as the correct, lossless lever for cost: pick the cheapest capable model rather than lossily compress context for an expensive one.

---

## Verification Checklist

- [x] Source type correctly identified (Git repository + topic research) and scope stated
- [x] Deep research answers the three posed questions (community, research stage, tokens-vs-quality) with sources
- [x] Every quantitative claim cites a primary or clearly-labeled source; vendor-reported figures flagged as unverified
- [x] The apparent contradiction (pxpipe "68% savings" vs "images cost more") reconciled explicitly via the density/legibility dial and model specificity
- [x] Every gap claim cites a specific Nexus-Hub skill or file
- [x] Adoption items have concrete target locations
- [x] Step 5 complete: threat-model table, per-item risk scorecard, per-item RE classification present
- [x] Step 5.4 ordering used to sequence the plan (skill-native, then RE, then vendor, then drops)
- [x] MCP Registry Policy cited by name for the dropped runtime, with the v3.10.0 ruflo precedent
- [x] Reverse-engineering attribution rule noted (no upstream product name in distributed artifacts)

---

## Next Step

The recommended cut is small and low-risk: a single skill-native doctrine edit (C1 + C2) in `prompt-token-optimization`, an optional one-line note in `model-routing` (C4), and a `drop-outright` matrix row for the proxy runtime. This is ready to feed `/plan from-comparison` with `reverse-engineer-first=true`. The larger value of this exercise is the research in Part A and the reasoned decline of the mechanism itself: pxpipe is a clever, well-grounded technique for a narrow workload, but it is the wrong layer, the wrong risk profile, and the wrong economics for a correctness-first coding catalog running on Opus-class models.
