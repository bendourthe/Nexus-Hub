# Edit Routing: where a finding is allowed to go

Research produces findings. This file is the contract for deciding, per finding, whether it may touch a shared catalog body or must stay in the per-model profile layer. The rules are implemented in `scripts/apply_prompting_edits.py` and every rule below has a test in `tests/skills/test_model_prompting_edit_routing.py`.

## The four routes

| Route | Meaning | Where it may write |
|---|---|---|
| `eligible` | Model-agnostic, targets an allowed surface, introduces no model identifier | The shared body named in the proposal, behind the full guard suite |
| `profile-only` | Model-specific, by declaration, by default, or by the hard rail | The profile layer, and nowhere else |
| `rejected` | Structurally unusable, or aimed at a surface this feature may not touch | Nowhere |

## Rule 1: ambiguity resolves to model-specific

A finding is eligible for a shared body ONLY when its `scope` is exactly `model-agnostic-candidate`. Every other value routes to `profile-only`: a missing scope, an empty string, an unrecognized value, even a differently-cased `MODEL-AGNOSTIC-CANDIDATE`.

The asymmetry is deliberate. A model-specific claim parked in the profile layer is merely unhelpful to models it does not describe. A model-specific claim written into a shared body is distributed verbatim to every platform, where it is wrong for every reader running something else. The costs are not symmetric, so the default is not neutral.

## Rule 2: only six surfaces are targetable

A model-agnostic finding may propose an edit to exactly these `target_kind` values:

- `skill-description` and `skill-trigger-phrase` (sharpening how a skill is found)
- `skill-rationalization` and `skill-verification` (sharpening how a skill is followed)
- `command-body` (clarifying a command's instructions)
- `base-template-line` (a genuinely platform-agnostic line in the lockstep templates)

Anything else is `rejected`. This feature exists to sharpen authoring, not to refactor the catalog: it may not touch installers, hooks, the `data/` registry files, READMEs, or CI configuration. A finding that seems to call for one of those is a suggestion for a human, not an auto-applied edit.

## Rule 3: the hard rail, and where it actually lives

**An edit may not INTRODUCE a model identifier into a shared body, whatever its declared scope.**

Detection compares the identifiers in the edit's `new` text against those already in its `old` text, so the rail blocks smuggling a new model name in while still allowing a line that already names a model to be reworded or to have the name removed. A blocked edit routes to `profile-only`, not `rejected`, because the underlying guidance is usually fine; it is the destination that was wrong.

### Why the rail is enforced here and not by the parity guard

The v3.15.5 plan asserted that `scripts/check_base_template_parity.py` makes this rail physical, on the theory that a model-named line in a shared `base-*.md` fails the build. **That is not true**, and it was verified empirically before this engine was written:

| Case | Parity guard result |
|---|---|
| The same model-named line added to ALL FIVE `base-*.md` inside an invariant section | PASSES |
| A model-named line added to ONE file, in a non-invariant section | PASSES |
| A genuinely divergent invariant section (the control) | Correctly FAILS |

The parity guard compares the five templates **to each other**. Lockstep is precisely what it checks, so an auto-apply engine dutifully applying the same model-named line five times satisfies it perfectly. The guard prevents drift between the templates; it says nothing about whether their shared content is model-specific.

`tests/skills/test_model_prompting_edit_routing.py::test_parity_guard_does_not_catch_a_model_named_line_in_lockstep` pins this reality, so if the parity guard ever gains content-level checks the test fails and this section gets revisited.

### The residual, stated plainly

This rail binds the auto-apply engine. It does not bind a human hand-editing a shared body, because a catalog-wide model-name gate would fail today on pre-existing legitimate mentions (`model-routing` documents tiers by name; `claude-api` names model ids) and triaging those is a separate decision. So the accurate claim is: **this feature cannot autonomously write model-specific content into a shared body**, not "model-specific content cannot exist in a shared body".

## Rule 4: structural completeness

A proposal is `rejected` when it has no `target`, no `old` anchor text, or when `new` equals `old`. Two further conditions surface at apply time rather than classification, because they depend on the file's current contents:

- the anchor is not present in the target file, or
- the anchor appears more than once, so the edit site is ambiguous.

Both quarantine the edit rather than guessing which occurrence was meant.

## The guard loop

Every `eligible` edit is applied and then guarded individually:

1. Snapshot the target file's current contents in memory.
2. Apply the edit (replace the single anchor occurrence).
3. Run the full guard suite: the skill-bundle audit, base-template parity, the profile schema gate, version sync, and the trigger-and-routing gate, plus ShellCheck when the edited file is a shell script.
4. If every guard passes, keep the edit. If any fails, restore the snapshot and record the edit in the quarantine list with the failing guard's name and output.

A quarantine is per-edit. The run continues with the next proposal, so one bad edit never costs the whole batch.

**Why a snapshot rather than `git checkout --`**: the plan specified `git checkout -- <file>` for the revert. That is wrong when two eligible edits target the same file, because `git checkout --` reverts to HEAD and would silently discard an earlier surviving edit along with the failing one. Restoring an in-memory snapshot reverts exactly the failed edit. `test_a_failing_second_edit_does_not_destroy_a_surviving_first_edit` guards this.

## Branch isolation

The engine creates or checks out `feat/tune-prompting-<stamp>` from the integration branch before touching a file, and asserts immediately afterwards that HEAD is that branch and that it is not `main`, `master`, or `develop`. The stamp is supplied by the caller and never generated internally, because a workflow runtime has no clock.

Edits are left uncommitted unless `--commit` is passed, and the run always ends by stating that the branch is for human merge. Nothing here merges, tags, or pushes.
