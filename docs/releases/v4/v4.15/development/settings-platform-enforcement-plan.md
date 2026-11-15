# Settings Platform Enforcement

This local delivery plan corrects the shared effort mapping, compact Settings panel and status hover, and verifies the installed editor integrations before delivering an updated extension. It is bounded to the user's Settings request and does not authorize repository publication, release or unrelated plan changes.

## Baseline

The starting source is `6b4509b7a` plus nine existing working-tree edits. Those edits are preserved. The installed editors are Visual Studio Code, Cursor and Antigravity. Native settings, remembered session state, extension configuration and hook invocation are separate boundaries and must be checked independently.

## Phase 1 Implementation

1. [x] Verify installed vendor schemas and current official contracts; implement portable native effort mappings, readback equivalence and supported override reconciliation.
2. [x] Remove the redundant effort label, tighten spacing and replace the malformed status hover with compact native Markdown.
3. [x] Connect supported editor configuration and hook adapters, exercise valid and malformed inputs through actual consumers, and record explicit unsupported or unverified surfaces.

## Phase 2 Delivery

1. [x] Run affected tests, browser interaction and installed-host checks, package and install into every locally available compatible editor, then verify the installed files and effective settings.

The two phase boundaries are local commits. The [delivery evidence](settings-platform-enforcement-evidence.md) records the checks and the native effort integrations that remain open; these marks do not claim universal vendor enforcement or a repository release.

## Acceptance

- One global effort selection maps into supported native vocabularies without writing invalid values.
- Readback compares native mapped values, so an equivalent value does not produce an override warning.
- User-owned conflicting defaults are reconciled where a supported writable control exists. Organization policies are preserved; unsupported native controls are never described as enforced.
- The panel contains no duplicate selected effort label and the hover contains no simulated HTML controls.
- Guardrail verification distinguishes registered enforcement from a saved preference; each requested platform has a recorded observed outcome or a named limitation.
- Installation preserves unrelated settings and existing changes; native client/session behavior is not inferred from file copying alone.

## Ownership

The coordinator owns editor adapters, integration, documentation, packaging and delivery. Independent workers own the Python settings engine and the panel/status UI; a read-only worker audits installed platforms. All workers preserve the existing current files and use independent edit-guard stores.

## Validation

Use focused engine and extension tests during changes. Final validation includes actual CLI persistence/readback/reset, hook execution, rendered browser geometry and interaction, and real editor-host activation. Record native reasoning-request coverage separately from configuration persistence. No billable model request is authorized solely for testing.

## CI Impact

No pipeline changes or remote CI are needed for this local extension delivery. Existing affected test selections cover the changed modules. Publication and repository release remain outside this plan.
