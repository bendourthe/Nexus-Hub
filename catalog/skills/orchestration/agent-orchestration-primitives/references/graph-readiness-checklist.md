# Graph Readiness Checklist

The escalation gate in `SKILL.md` Step 4 is passed only when this checklist is complete. It exists so a graph is entered on written evidence a reader can fail, rather than on the sense that a problem looks big enough to deserve one.

## Six signals that a graph can help

One line each. These are reasons to LOOK at a graph, not permission to build one.

- **Independent verification needs different context or permissions from the producer.** A verifier that shares the producer's context and authority is not independent.
- **The work is genuinely parallel with low dependencies.** Parallel-looking work with hidden ordering is sequential work with a merge problem.
- **Context isolation improves quality.** Separate contexts stop one node's accumulated noise from degrading another's judgement.
- **Permissions should differ by role.** A node that only reads should not carry write authority just because a sibling needs it.
- **Failure containment matters.** One node's failure should not require repeating the successful work around it.
- **The finish line changes by phase.** When "done" means something different at each stage, one exit condition cannot express it.

## The eight-item checklist

Every item must be TRUE before fan-out begins. A single false item sends the design back down a rung.

- [ ] A single loop has a **measured** failure mode that the graph fixes. Not a predicted one.
- [ ] Each node has a distinct responsibility, context boundary, permission boundary, or parallel work package. A node that shares all four with its neighbour is not a node.
- [ ] Inputs and outputs between nodes use explicit contracts or schemas, so a handoff can be validated rather than hoped about.
- [ ] The fan-out count is bounded AND the merge strategy is defined before fan-out starts, not discovered when the results arrive.
- [ ] Independent verification occurs BEFORE any high-cost or high-risk downstream work, so an unverified premise cannot be multiplied.
- [ ] Graph state can be checkpointed, resumed, and inspected. A graph nobody can inspect mid-run cannot be debugged when it stalls.
- [ ] Node failures can be retried or isolated without repeating successful side effects. Retrying a node that already sent an email is not a retry.
- [ ] Human authority sits at specific NAMED gates, each asking one concrete answerable question, rather than as a general expectation of oversight.

## The economics

A single-agent run costs several times a chat exchange, and a multi-agent system costs many times more again. Fan-out is therefore deliberate: it is a decision with a price, taken because the checklist above is complete, not because the work felt large. When the checklist is incomplete, the cheaper rung is not a compromise -- it is the option that has actually been justified.
