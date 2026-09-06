# Phase 1 verification

Status: local baseline and design contract complete. Model: current frontier session, max-effort recommendation retained; no automatic model change.

- `NEXUS_REQUIRE_RENDER=1 python -m pytest tests/guides -q`: 340 passed, 1 optional skip in 374.03s.
- `python tests/guides/tools/learning_experience_audit.py --out docs/releases/v4/v4.4/development/guide-learning-experience/baseline --performance`: 72 geometry cases, zero overflow/errors, 12 performance samples including warmups.
- Eight baseline screenshots were inspected during planning at this exact source hash. The review records spacing, wrapping, diagram visibility, and Training's premature success claim. No screenshot was modified to hide a defect.
- Baseline content and heights are recorded in baseline.md; seven lesson storyboards and the legacy-assertion migration policy are recorded in design-contract.md.

## Plan delta

Incomplete measurement assumption: baseline timing overlapped another browser suite in early samples. Retained transparently; clean final samples and diagnostic attribution are required. No runtime source changed in this phase. Human comprehension and final visual approval remain final-phase gates.

## Closeout

CI impact: the reusable audit tool is local evidence generation; existing guide-render remains the owning test job. No pipeline edits. Gitignore and living-doc architecture need no change. Known defects remain open for phases 2 and 6. The progress tracker and this release-scoped history record the phase. Planning artifacts, baseline evidence, and the audit tool form one local phase commit; no publication is authorized here.
