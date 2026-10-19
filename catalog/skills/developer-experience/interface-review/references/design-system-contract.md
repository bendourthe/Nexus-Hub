# Design-system lint contract

This reference guides UI authors and reviewers when a project already has design tokens and a lint task. It covers repeatable CSS checks, domain ownership, actionable diagnostics, one adaptable configuration, and honest coverage limits. `interface-review` owns execution and coverage; domain owners retain their rules.

## Contract

A machine-checkable design-system contract turns the project's approved component and token decisions into repeatable checks with file locations, repair advice, and a failing exit code. It complements rendered judgment. A clean syntax check cannot establish readable hierarchy or brand fidelity.

| Violation class | Verdict | Policy owner and measurement boundary |
|---|---|---|
| Unchecked files, ignored diagnostics, or a successful exit despite violations | States | `interface-review` records the exact command, resolved file set, exclusions, exit code, and rejected-then-fixed example. Empty coverage is not a pass. |
| Raw colors or values outside approved color roles | Defers | `color-systems` owns role construction; `theme-tokens` / `brand-styling` apply supplied token JSON. Translate the project's approved values, not a new palette. The example checks only `color` and `background-color`. |
| Spacing outside the project's scale | Defers | `layout-and-spacing` chooses the scale and exceptions. The example checks only `gap`; other spacing properties need the project's existing rules. |
| Arbitrary type values or wrap rules | Defers | `web-typography` owns these decisions. The CSS example does not claim to check them. |
| Restyling a protected component or unsupported prop/variant | Defers | `ui-component-generation` owns the component contract. Use the project's framework-aware checker; CSS-only checks cannot infer props or ownership boundaries. |
| Accessibility requirements and their severity | Defers | `accessibility-engineering` owns the requirements. Run its checks separately; this reference adds no alternative thresholds or motion rules. |

A diagnostic must identify the location, violated project decision, permitted replacement, and owner for an exception. A bare rule ID gives an agent no repair target. Prefer replacing a literal with an already defined semantic token; do not invent a token just to make lint green. Route exceptions to the policy owner and document their bounded scope.

## Adaptable configuration

Checked with Stylelint 17.16.0 on 2026-10-16, using the built-in [declaration-property-value-allowed-list](https://stylelint.io/user-guide/rules/declaration-property-value-allowed-list/) rule and its [custom message option](https://stylelint.io/user-guide/configure/#message). This is a small CSS example, not a universal token policy. Copy the following JSON to `.stylelintrc.design-system.json` in the consuming project's root only after replacing its example values and file exclusions with the project's approved contract. Keep the project's existing linter version in its lockfile and test compatibility before upgrading it.

```json
{
  "ignoreFiles": ["src/styles/tokens.css"],
  "rules": {
    "declaration-property-value-allowed-list": [
      {
        "color": ["var(--color-fg)", "inherit", "currentColor"],
        "background-color": ["var(--color-bg)", "transparent"],
        "gap": ["0", "var(--space-2)", "var(--space-4)"]
      },
      {
        "message": "Replace %s value %s with its approved role or spacing token; see the project token map and the domain owner for exceptions."
      }
    ]
  }
}
```

The token-definition file is excluded because it legitimately contains raw values. Record that exclusion explicitly; validate token definitions with the project's existing source/schema checks. The example checks exact declaration values, not equivalent spellings, token existence, shorthand expansion, CSS-in-JS, component props, imported dependencies, or whether a declared token has the right rendered effect. Missing framework/parser coverage must be named, not inferred from a green CSS result.

## Existing lint integration

Prerequisites: run in the consuming project's root, with its installed Stylelint dependency, the adapted configuration above, CSS sources under `src/`, and the referenced tokens already defined. This repository supplies guidance; it does not add a new mandatory dependency or a CSS pipeline to every consumer.

```powershell
npm exec --no -- stylelint --config .stylelintrc.design-system.json "src/**/*.css" --max-warnings 0
```

Add that invocation to the project's existing lint task using its existing task runner. Preserve all other checks and propagate any nonzero exit to the caller. Record the actual covered files from that project's lint output and configuration; do not accept an empty glob or hide failures with a success fallback. No pipeline file is changed merely by adopting this reference.

For a proportional smoke, create a temporary in-scope CSS file containing `.probe { color: #123456; gap: 13px; }`. The command must fail and identify both declarations with repair advice. Replace it with `.probe { color: var(--color-fg); gap: var(--space-2); }`; expect exit 0. Remove only the owned temporary fixture and rerun the normal lint task. Keep the failing and passing outputs in the project evidence. These observations prove the configured properties only; rendered review remains with the domain owners.

## Unchanged wiring

- Not wired: `web-typography`, because this phase adds no type-scale or wrapping rule.
- Not wired: `interface-copy`, because source-string quality is outside CSS lint.
- Not wired: `accessibility-engineering`, because its existing checks and severity ownership remain separate.

## Decision

Rejected alternative: an original rule package has no active consuming call site and would add maintenance without a demonstrated need. Guidance plus one adaptable configuration is the approved ceiling. The durable [decision record](../../../../../docs/decisions/implemented/tooling/2026-10-16-design-system-lint-contract.md) records the owner and tradeoff. Do not add a theme catalog or duplicate the verifier taxonomy owned by `multi-agent-code-review`.
