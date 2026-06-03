# The Five Orchestration Patterns

This reference catalogs the five named patterns for shaping a multi-agent orchestration once you have chosen a primitive (subagents, agent teams, or a Dynamic Workflow) in the parent skill `agent-orchestration-primitives`. The primitive answers "what kind of coordination?"; the pattern answers "what is the control-flow shape?". Most real orchestrations are one of these five, or a composition of two.

Read this file when you need to pick a shape. Each section gives the shape, when it fits, when it does not, and a concrete worked example.

## Selection at a Glance

| Pattern | Control-flow shape | Pick it when | Avoid it when |
|---|---|---|---|
| Prompt chaining | A -> B -> C, each step's output feeds the next | The task decomposes into fixed, ordered stages where each depends on the prior. | Stages are independent (use parallelization) or the order is data-dependent (use routing). |
| Routing | Classify, then dispatch to the right handler | Inputs fall into distinct classes that want different handling or different model tiers. | There is only one kind of input, or every input needs every handler. |
| Parallelization | Fan out N independent units, then aggregate | The work is embarrassingly parallel (sectioning) or you want multiple independent votes on one question. | Units depend on each other, or the work is writing code (see the parent skill's Step 6). |
| Orchestrator-worker | A coordinator decomposes, dispatches, and reconciles | The subtasks are not known up front and must be discovered, then delegated and integrated. | The decomposition is fixed and known (use prompt chaining or parallelization directly). |
| Evaluator-optimizer | Generate, critique, regenerate, loop | Output quality improves measurably under critique and you can state a clear acceptance bar. | There is no objective acceptance signal, or one pass is already good enough. |

## 1. Prompt Chaining

**Shape.** A fixed sequence of steps where the output of each step is the input to the next: extract -> transform -> format, or research -> outline -> draft.

**When it fits.** The decomposition is known and strictly ordered, and each step is simpler (and more reliably correct) than the whole. Chaining also lets you insert a programmatic gate between steps (validate the extracted JSON before transforming it).

**When it does not.** If the steps are independent, chaining serializes work that could run in parallel. If the next step depends on *which* class the input falls into, you need routing first.

**Worked example.** Generating release notes: step 1 (a subagent) reads `git diff main..HEAD` and returns a structured change list; step 2 groups changes by component; step 3 formats the grouped list into the CHANGELOG entry. Each step is a clean, verifiable transform; a malformed step-1 output is caught before step 2 runs.

## 2. Routing

**Shape.** A cheap classifier inspects the input and dispatches it to one of several specialized handlers (often with different model tiers): easy inputs to a fast/cheap model, hard inputs to a capable model.

**When it fits.** Inputs are heterogeneous and different classes genuinely want different handling or different cost tiers. Routing is the dominant cost-control pattern: it sends only the hard fraction to the expensive model.

**When it does not.** If every input is the same kind, routing adds a useless hop. If every input needs every handler, you want parallelization (sectioning), not routing.

**Worked example.** A support-triage flow: a small model classifies an incoming request as "FAQ", "bug report", or "billing", then routes FAQ to a template responder, bug report to a capable model with repo context, and billing to a human-escalation path. The capable model only ever sees the requests that need it.

## 3. Parallelization

**Shape.** Two distinct sub-shapes:

- **Sectioning**: split the work into independent slices and run them concurrently (audit each route, summarize each module), then aggregate.
- **Voting**: run the *same* question through several agents independently and aggregate by majority or by union of findings.

**When it fits.** Sectioning fits embarrassingly-parallel, read-only, large-surface work -- the canonical "audit every endpoint under `src/routes/` for missing auth and report findings without changing code". Voting fits when a single pass is unreliable and independent opinions raise confidence (security findings, edge-case discovery).

**When it does not.** When the slices depend on each other, parallel execution produces incoherent partial state. Never use parallelization to write production code (parallel writers make incompatible assumptions -- see the parent skill's Step 6).

**Worked example (sectioning).** A Dynamic Workflow fans out one subagent per file under `src/routes/`, each checking for a missing authentication guard and returning a finding or "clean". The script collects all findings off-context and returns a single deduplicated report. Calibrate on one folder before running the full tree (scope-first token discipline).

**Worked example (voting).** Three subagents independently hunt for race conditions in the same module; the union of their findings is triaged. Independent context per agent reduces correlated blind spots.

## 4. Orchestrator-Worker

**Shape.** A coordinator agent dynamically decomposes a task whose subtasks are *not known in advance*, dispatches each to a worker, and reconciles the results. The dominant pattern for real coding work. Unlike prompt chaining (fixed steps), the orchestrator decides the subtasks at runtime based on what it finds.

**When it fits.** The task requires discovery before decomposition: "refactor the data layer" cannot be split until an agent has mapped what the data layer contains. The orchestrator explores, plans the split, delegates disjoint scopes, and integrates.

**When it does not.** If the decomposition is fully known up front, the orchestrator overhead is wasted -- use prompt chaining or direct parallelization.

**Worked example.** Coordinating a feature: the orchestrator (the main agent) maps the task graph, dispatches a backend worker (write scope `src/api/`), a frontend worker (`src/components/`), and a test worker (`tests/`), each with an explicit contract, then reconciles their outputs and runs the integrated test suite. This is exactly the [[multi-agent-coordinator]] flow.

## 5. Evaluator-Optimizer

**Shape.** A generate-then-critique loop: a generator produces a candidate, an evaluator critiques it against an explicit bar, and the generator regenerates using the critique -- iterating until the bar is met or a max-iteration cap is hit.

**When it fits.** Output quality demonstrably improves under critique and you can state a falsifiable acceptance bar ("all tests pass", "no high-severity findings remain", "matches the style guide checklist"). This is the engine behind adversarial convergence in Dynamic Workflows.

**When it does not.** If there is no objective acceptance signal, the loop spins without converging. If one pass is already good enough, the loop is pure cost. Always cap the iteration count.

**Worked example.** A code-fix loop: the generator proposes a patch, the evaluator (an [[adversarial-verifier]]-style agent) runs the test suite and reports the first failing test, the generator revises, and the loop repeats up to three times. The acceptance bar -- "the full suite passes, with output pasted" -- is concrete, so the evaluator cannot declare victory without verifying (the parent skill's failure mode 2).

## Composing Patterns

Real orchestrations chain these shapes. A common composition: **route** an incoming task by complexity, **parallelize** the discovery phase across independent areas, hand the findings to an **orchestrator-worker** decomposition, and wrap the risky workers in an **evaluator-optimizer** loop for verification. Compose deliberately -- each added shape adds token cost and failure surface, so add one only when a measured problem (parent skill, Step 2) demands it.

---

## Source

Patterns synthesized from public, widely-published agent-orchestration guidance on prompt chaining, routing, parallelization (sectioning and voting), the orchestrator-worker pattern, and the evaluator-optimizer loop. Re-authored as a Nexus-Hub decision reference; no external text is reproduced.
