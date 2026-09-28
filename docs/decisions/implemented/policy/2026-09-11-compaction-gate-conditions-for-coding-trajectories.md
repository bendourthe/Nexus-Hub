# Decision: Compaction gate conditions for coding trajectories

Status: implemented - CLOSED-UNIT requires an observable completed operation, and STUCK requires the same failure signature in three of four attempts without a new observation

## Problem

The adopted compaction rubric was written for math and search trajectories. Its CLOSED-UNIT and STUCK conditions did not transfer directly to coding work, where progress may appear as a tool result, test-state change, completed plan task, verification result, or commit. A coding definition must let an agent decide from quoted trajectory evidence without making commits mandatory or reducing stuckness to an arbitrary retry counter.

## Decision

CLOSED-UNIT is YES when the latest operation reached an observable boundary, its result is recorded, and no announced action remains in flight. A completed tool call, reported test run, completed task, commit, or verification result can satisfy it; an intent such as "Let me now check..." cannot.

STUCK is YES when the same failure signature appears in at least three of the last four attempts and no intervening attempt produces a new observation or changes test state. Each matching signature and the absence of new evidence must be quoted from the trajectory.

Evidence that would change this decision is a measured corpus of coding trajectories showing that these definitions either trigger compaction during live work or fail to identify repeated no-progress loops. Such evidence would justify changing the boundary or recurrence threshold.

## Alternatives considered

- **Define CLOSED-UNIT as a reported test run.** Rejected because research, documentation, configuration, and repository operations can finish observable units without tests.

- **Define CLOSED-UNIT as a phase commit.** Rejected because it suppresses safe compaction throughout long phases and couples a context decision to repository policy.

- **Define CLOSED-UNIT as a completed plan sub-task.** Rejected because not every task has a plan and one sub-task can contain several independently resumable boundaries.

- **Define CLOSED-UNIT as a recorded verification step.** Rejected as the sole definition because implementation and diagnosis can reach stable boundaries before final verification. It remains one qualifying example.

- **Define STUCK as repeated edits to the same file with no test-state change.** Rejected because the same no-progress loop can cross files, while productive refinement can edit one file repeatedly.

- **Define STUCK as the same failure signature recurring across attempts.** Adopted with an observation requirement and a threshold. Signature recurrence identifies the stable failure, while the absence of a new observation distinguishes repetition from productive diagnosis.

- **Define STUCK as a retry count without a new observation.** Rejected alone because different failures can occur across retries. Its no-new-observation requirement is retained as part of the adopted definition.

## Consequences

The rubric can be applied to coding, documentation, configuration, and repository work with the same evidence form. It does not require a plan or commit to exist. The three-of-four threshold is a policy judgment rather than a Nexus-Hub measurement, so future trajectory evidence may require retuning it.
