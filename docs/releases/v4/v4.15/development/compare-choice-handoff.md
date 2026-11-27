# Comparison Choice Handoff

Summary: shared instruction changes make completed comparisons offer a clear planning choice. This evidence records the source scope, focused contract and projection checks, and the installed-host behavior that remains unverified. It is for review of the v4.15 maintenance change.

## Scope

The change is isolated on `fix/compare-choice-handoff`, based on `d70af08842456c94c90276584d7c330281f0c857`.

- `cross-project-comparison` owns the completed comparison's choice and selected action, including direct skill use.
- `/compare` delegates the complete handoff through installed skill discovery.
- `agent-communication` owns question presentation. The retained skill includes a minimal procedure when the common installed guide is unavailable and reports that coverage limit honestly.
- The worked example uses the same three choices: Create the plan (Recommended), Review recommendations, and Stop here.

An actually available question tool is used when the current host and mode support the ordinary choice. Otherwise, the same choices appear as a numbered text list. A preselected option, silence or elapsed time is not consent. Existing planning requests continue without another question, and comparisons without eligible adoption items do not offer an empty plan.

An explicit planning choice is a new user request for `/plan from-comparison` through the normal user-command route. Target confirmation, queue checks and the actual report path remain required. A separate commit or publication approval wait does not replace the planning handoff, while comparison security and target confirmation remain required. The choice grants no new implementation or publication authority. Signed approval capture and implementation progress reporting retain their existing owners.

No adapter, installer, platform template, registry or frozen plan was changed for this fix. The new handoff instructions use installed skill discovery and the common Nexus-Hub guide location rather than repository-relative paths that break after flattening.

## Verification

| Check | Result |
|---|---|
| Focused pre-change baseline | 174 passed; zero failures, errors or skips |
| Focused checks after the runtime-path correction | 174 passed; zero failures, errors or skips |
| Skill bundle validation | 340 skills scanned; zero errors, 66 warnings |
| Strict registry validation | Passed |
| Whitespace check | `git diff --check` passed |
| Documentation link and layout scan | Passed |

The focused checks cover `test_communication_contract_rule.py`, `test_communication_contract_rollout.py`, `test_catalog_adapters.py`, `test_cross_platform_flatten.py` and `test_antigravity_commands.py`. They exercise shared instruction requirements and command/skill projection into temporary output. Private temporary state was placed outside the real home-directory ancestry and pytest cache writes were disabled.

The focused command after the runtime-path correction completed in 37.515 seconds; its JUnit test duration was 35.974 seconds. The later publication-wait clarification passed lightweight skill bundle, registry and documentation checks. Private receipts and logs are retained for review. The bundle validator's 66 warnings were reported, not silently treated as a warning-free result or repaired outside this scope.

## Remaining Qualification

This is an instruction-only change. The focused tests do not prove that a model uses the expected question tool after an actual installed comparison. No post-change end-of-comparison flow, native question UI parity across clients, or text fallback in a real client was exercised here.

Installed delivery, actual client observations, commit and publication remain separate. No provider session, paid trial, installed-file replacement or native run-record mutation was performed for these checks. No full qualification profile was started for this instruction change.
