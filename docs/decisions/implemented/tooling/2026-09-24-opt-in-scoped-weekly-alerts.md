# Decision: Offer opt-in model-scoped weekly alerts

Status: implemented - A fourth threshold metric uses the account-reported scoped weekly limit without changing existing alert defaults.

## Problem

The Claude Usage Monitor renders an account-reported model-scoped weekly bar in the dashboard and status-bar hover. Its alerts and status-bar highlighting still evaluate only the current session and all-models weekly limits. A scoped limit can therefore approach capacity without an interrupting alert.

The original second-bar requirement kept the scoped figure out of the compact status-bar text. Adding it to the default `highest` threshold selection would change alerts for every existing user, including those who did not ask for the second bar to interrupt them. Preserving that default is the primary compatibility constraint.

Some accounts report no scoped weekly limit. Any scoped alert option must represent that absence directly, not substitute the session or all-models percentage and present an unrelated alert as a scoped one. The provider's scoped label is account data and must remain escaped in HTML surfaces.

## Decision

The monitor provides `weeklyScoped` as an explicit fourth `claudeUsage.thresholdMetric` value. When selected, the account-reported scoped percentage controls highlighting, refresh cadence, dashboard threshold suggestions, and warning-view thresholds. When the scoped metric is absent, those threshold paths have no selected percentage and raise no threshold alert. The status-bar text remains the current session and all-models weekly figures, and the default `highest` continues to ignore the scoped metric.

## Alternatives considered

**Add the scoped bar to `highest`.** This needs no new setting and would alert on the tightest reported limit. It changes existing users' alert policy under them and makes a bar intentionally omitted from status-bar text drive the status-bar color, so it is rejected.

**Keep scoped usage display-only.** This preserves every existing behavior and avoids settings-schema work. It also leaves a visible binding limit unable to warn, so it is retained as the default behavior but not as the only option.

**Add an opt-in scoped metric.** This changes only accounts whose operator selects the new value and gives the missing-data case an explicit no-alert outcome. It adds one setting choice and requires all threshold consumers to handle an unavailable metric; that cost is accepted.

## Consequences

- Existing users retain their current selection, status text, and alert policy unless they opt into the fourth value.
- Operators who select `weeklyScoped` get the account-provided percentage and label in threshold suggestions and warning presentation.
- An account with no scoped limit produces no threshold warning under that selection, even when another reported limit is high. The other bars remain visible in the dashboard and hover.
- Metric changes reset the in-memory alert bucket so a newly selected high scoped limit can warn once in that session.
